"""
Batch execution workflow for generating multiple assets.

This module provides functionality to execute multiple asset generation requests
in batch, with optional parallel execution and atlas texture combining.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.core.config import Settings, get_settings
from src.core.models import (
    AssetDefinition,
    AssetResult,
    AssetType,
    BatchDefinition,
    BatchResult,
    Dimensions,
    SpriteRequest,
)
from src.rendering.atlas_builder import AtlasBuilder
from src.state.executor import WorkflowExecutor
from src.utils.file_manager import derive_asset_name, organize_output_files
from PIL import Image

logger = logging.getLogger(__name__)


class BatchExecutor:
    """
    Execute batch generation workflows.
    
    Supports:
    - Multiple individual assets
    - Optional atlas combining
    - Progress tracking
    - Error handling per asset
    - Parallel execution
    """
    
    def __init__(
        self,
        settings: Settings | None = None,
        create_atlas: bool = False,
        atlas_name: str | None = None,
    ) -> None:
        """
        Initialize batch executor.
        
        Args:
            settings: Application settings (uses get_settings() if not provided)
            create_atlas: Whether to combine assets into atlas after generation
            atlas_name: Name for atlas (defaults to batch name)
        """
        self.settings = settings or get_settings()
        self.create_atlas = create_atlas
        self.atlas_name = atlas_name
        
        # Storage for batch requests
        self._requests: list[tuple[str, SpriteRequest, dict[str, Any]]] = []
        
        logger.info(f"BatchExecutor initialized (create_atlas={create_atlas})")
    
    async def add_request(
        self,
        description: str,
        dimensions: tuple[int, int] | None = None,
        style: str | None = None,
        asset_type: str | None = None,
        category: str | None = None,
        name: str | None = None,
    ) -> str:
        """
        Add a generation request to the batch.
        
        Args:
            description: Asset description
            dimensions: Optional dimensions as (width, height)
            style: Optional style name
            asset_type: Optional asset type
            category: Optional category for organization
            name: Optional explicit asset name
        
        Returns:
            Request ID for tracking
        """
        # Create SpriteRequest
        request = SpriteRequest(
            description=description,
            dimensions=Dimensions(width=dimensions[0], height=dimensions[1]) if dimensions else Dimensions(width=16, height=16),
            style=style if style else "stardew_valley",
            asset_type=AssetType(asset_type) if asset_type else AssetType.SPRITE,
        )
        
        # Store metadata
        metadata = {
            "category": category,
            "explicit_name": name,
        }
        
        # Generate request ID
        request_id = str(request.request_id)
        
        self._requests.append((request_id, request, metadata))
        
        logger.debug(f"Added request {request_id}: {description}")
        
        return request_id
    
    async def execute_batch(
        self,
        output_dir: Path,
        parallel_count: int = 1,
    ) -> BatchResult:
        """
        Execute all queued generation requests.
        
        Process:
        1. Generate each asset (manifest + PNG)
        2. Track success/failure per asset
        3. If create_atlas=True, combine into atlas
        4. Return comprehensive results
        
        Args:
            output_dir: Directory for output files
            parallel_count: Number of parallel generations (1-10)
        
        Returns:
            BatchResult with success/failure details
        
        Raises:
            ValueError: If no requests queued or invalid parameters
        """
        if not self._requests:
            raise ValueError("No requests queued for batch execution")
        
        if parallel_count < 1 or parallel_count > 10:
            raise ValueError("parallel_count must be between 1 and 10")
        
        logger.info(f"Starting batch execution: {len(self._requests)} requests, parallel={parallel_count}")
        
        start_time = datetime.utcnow()
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Execute requests (with parallelism if requested)
        if parallel_count == 1:
            asset_results = await self._execute_sequential(output_dir)
        else:
            asset_results = await self._execute_parallel(output_dir, parallel_count)
        
        # Count successes and failures
        successful = sum(1 for r in asset_results if r.success)
        failed = len(asset_results) - successful
        
        # Build atlas if requested and there are successful assets
        atlas_path = None
        atlas_metadata_path = None
        batch_errors = []
        
        if self.create_atlas and successful > 0:
            logger.info(f"Building atlas from {successful} successful assets")
            try:
                atlas_path, atlas_metadata_path = await self._build_atlas(
                    asset_results,
                    output_dir,
                )
            except Exception as e:
                error_msg = f"Atlas creation failed: {e}"
                logger.error(error_msg, exc_info=True)
                batch_errors.append(error_msg)
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Create batch result
        batch_result = BatchResult(
            batch_name=self.atlas_name or "batch",
            total_requests=len(self._requests),
            successful=successful,
            failed=failed,
            assets=asset_results,
            atlas_path=atlas_path,
            atlas_metadata_path=atlas_metadata_path,
            errors=batch_errors,
            execution_time=execution_time,
        )
        
        logger.info(
            f"Batch execution completed: {successful} successful, "
            f"{failed} failed, {execution_time:.2f}s"
        )
        
        return batch_result
    
    async def _execute_sequential(self, output_dir: Path) -> list[AssetResult]:
        """Execute requests sequentially."""
        results = []
        
        for i, (request_id, request, metadata) in enumerate(self._requests, 1):
            logger.info(f"Generating asset {i}/{len(self._requests)}: {request.description}")
            
            result = await self._generate_single_asset(
                request,
                metadata,
                output_dir,
            )
            results.append(result)
        
        return results
    
    async def _execute_parallel(
        self,
        output_dir: Path,
        parallel_count: int,
    ) -> list[AssetResult]:
        """Execute requests in parallel batches."""
        results = []
        
        # Create semaphore to limit concurrent executions
        semaphore = asyncio.Semaphore(parallel_count)
        
        async def generate_with_semaphore(
            request: SpriteRequest,
            metadata: dict[str, Any],
        ) -> AssetResult:
            async with semaphore:
                return await self._generate_single_asset(request, metadata, output_dir)
        
        # Create tasks for all requests
        tasks = [
            generate_with_semaphore(request, metadata)
            for _, request, metadata in self._requests
        ]
        
        # Execute all tasks and gather results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to failed results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                _, request, metadata = self._requests[i]
                asset_name = metadata.get("explicit_name") or derive_asset_name(request.description)
                processed_results.append(
                    AssetResult(
                        name=asset_name,
                        success=False,
                        error=f"Generation exception: {str(result)}",
                    )
                )
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _generate_single_asset(
        self,
        request: SpriteRequest,
        metadata: dict[str, Any],
        output_dir: Path,
    ) -> AssetResult:
        """
        Generate a single asset.
        
        Args:
            request: Sprite generation request
            metadata: Asset metadata including category and explicit name
            output_dir: Output directory
        
        Returns:
            AssetResult with generation outcome
        """
        gen_start = datetime.utcnow()
        
        # Derive asset name
        asset_name = metadata.get("explicit_name") or derive_asset_name(
            request.description,
            request.request_id,
        )
        
        # Organize output files
        category = metadata.get("category")
        file_paths = organize_output_files(asset_name, output_dir, category)
        
        try:
            # Create executor and generate
            executor = WorkflowExecutor()
            
            try:
                result = await executor.execute(request)
                
                # Check if generation was successful
                if result.status.value != "completed":
                    return AssetResult(
                        name=asset_name,
                        success=False,
                        error=result.error_message or "Generation failed",
                        generation_time=(datetime.utcnow() - gen_start).total_seconds(),
                    )
                
                # Get paths from rendering info if available
                manifest_path = None
                png_path = None
                
                if result.rendering_info:
                    manifest_path = result.rendering_info.get("manifest_path")
                    png_path = result.rendering_info.get("png_path")
                
                # If paths not in rendering info, they should be in expected locations
                if not manifest_path:
                    manifest_path = str(file_paths['manifest'])
                if not png_path:
                    png_path = str(file_paths['png'])
                
                generation_time = (datetime.utcnow() - gen_start).total_seconds()
                
                return AssetResult(
                    name=asset_name,
                    success=True,
                    manifest_path=Path(manifest_path) if manifest_path else None,
                    png_path=Path(png_path) if png_path else None,
                    generation_time=generation_time,
                    metadata={
                        "category": category,
                        "request_id": str(request.request_id),
                    },
                )
                
            finally:
                await executor.close()
        
        except Exception as e:
            logger.error(f"Failed to generate {asset_name}: {e}", exc_info=True)
            return AssetResult(
                name=asset_name,
                success=False,
                error=str(e),
                generation_time=(datetime.utcnow() - gen_start).total_seconds(),
            )
    
    async def _build_atlas(
        self,
        asset_results: list[AssetResult],
        output_dir: Path,
    ) -> tuple[Path, Path]:
        """
        Build texture atlas from successful assets.
        
        Args:
            asset_results: List of asset results
            output_dir: Output directory
        
        Returns:
            Tuple of (atlas PNG path, atlas metadata path)
        
        Raises:
            ValueError: If no successful assets to combine
        """
        # Filter successful assets with PNG paths
        successful_assets = [
            r for r in asset_results
            if r.success and r.png_path and r.png_path.exists()
        ]
        
        if not successful_assets:
            raise ValueError("No successful assets with PNG files to combine")
        
        logger.info(f"Building atlas from {len(successful_assets)} assets")
        
        # Create atlas builder
        builder = AtlasBuilder(
            padding=self.settings.rendering.render_scale * 2,
            power_of_two=True,
        )
        
        # Add all successful assets
        for asset_result in successful_assets:
            try:
                img = Image.open(asset_result.png_path)
                await builder.add_asset(
                    asset_result.name,
                    img,
                    metadata=asset_result.metadata,
                )
            except Exception as e:
                logger.warning(f"Failed to add {asset_result.name} to atlas: {e}")
                continue
        
        # Build atlas
        atlas_name = self.atlas_name or "batch_atlas"
        atlas_png_path = await builder.build_atlas(output_dir, atlas_name)
        atlas_metadata_path = output_dir / f"{atlas_name}.json"
        
        return atlas_png_path, atlas_metadata_path
    
    def clear(self) -> None:
        """Clear all queued requests."""
        self._requests.clear()
        logger.debug("Batch requests cleared")


async def execute_batch(
    batch_definition: BatchDefinition,
    settings: Settings | None = None,
) -> BatchResult:
    """
    Execute a batch definition.
    
    Convenience function that creates a BatchExecutor, adds all requests
    from the definition, and executes them.
    
    Args:
        batch_definition: Complete batch definition
        settings: Optional settings (uses get_settings() if not provided)
    
    Returns:
        BatchResult with execution outcome
    
    Example:
        >>> from pathlib import Path
        >>> batch_def = BatchDefinition(
        ...     batch_name="items",
        ...     output_dir=Path("output/items"),
        ...     create_atlas=True,
        ...     assets=[
        ...         AssetDefinition(description="wooden chest", name="chest_wood"),
        ...         AssetDefinition(description="stone chest", name="chest_stone"),
        ...     ]
        ... )
        >>> result = await execute_batch(batch_def)
    """
    logger.info(f"Executing batch: {batch_definition.batch_name}")
    
    # Create executor
    executor = BatchExecutor(
        settings=settings,
        create_atlas=batch_definition.create_atlas,
        atlas_name=batch_definition.atlas_name or batch_definition.batch_name,
    )
    
    # Add all asset requests
    for asset_def in batch_definition.assets:
        # Use asset-specific settings or batch defaults
        dimensions = asset_def.dimensions or batch_definition.default_dimensions
        style = asset_def.style or batch_definition.default_style
        asset_type = asset_def.asset_type or batch_definition.default_asset_type
        
        await executor.add_request(
            description=asset_def.description,
            dimensions=(dimensions.width, dimensions.height),
            style=style.value,
            asset_type=asset_type.value,
            category=asset_def.category,
            name=asset_def.name,
        )
    
    # Execute batch
    result = await executor.execute_batch(
        batch_definition.output_dir,
        parallel_count=batch_definition.parallel_count,
    )
    
    return result