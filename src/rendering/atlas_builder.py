"""
Atlas texture builder for combining multiple assets into texture atlases.

This module provides functionality to combine multiple individual pixel art assets
into single texture atlases with metadata for game engine integration.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image

from .pixel import PixelGrid, Color
from .spritesheet import SpriteSheetPacker, PackingAlgorithm, SpriteSheet
from .export import PNGExporter

logger = logging.getLogger(__name__)


class AtlasBuilder:
    """
    Build texture atlases from multiple individual assets.
    
    Uses existing SpriteSheetPacker for layout and generates metadata JSON
    with sprite coordinates for game engine integration.
    
    Attributes:
        padding: Padding between sprites in pixels
        max_size: Maximum atlas dimensions (width, height)
        power_of_two: Force atlas dimensions to powers of two
        packing_algorithm: Algorithm to use for packing sprites
    """
    
    def __init__(
        self,
        padding: int = 2,
        max_size: tuple[int, int] = (1024, 1024),
        power_of_two: bool = True,
        packing_algorithm: PackingAlgorithm = PackingAlgorithm.MAXRECTS,
    ) -> None:
        """
        Initialize atlas builder with packing constraints.
        
        Args:
            padding: Padding between sprites in pixels
            max_size: Maximum atlas dimensions (width, height)
            power_of_two: Force atlas dimensions to powers of two
            packing_algorithm: Algorithm for packing sprites
        
        Raises:
            ValueError: If parameters are invalid
        """
        if padding < 0:
            raise ValueError("Padding must be non-negative")
        if max_size[0] <= 0 or max_size[1] <= 0:
            raise ValueError("Max size dimensions must be positive")
        if max_size[0] > 4096 or max_size[1] > 4096:
            raise ValueError("Max size cannot exceed 4096x4096")
        
        self.padding = padding
        self.max_size = max_size
        self.power_of_two = power_of_two
        self.packing_algorithm = packing_algorithm
        
        # Storage for assets to be packed
        self._assets: dict[str, PixelGrid] = {}
        self._metadata_map: dict[str, dict[str, Any]] = {}
        
        # Packer instance
        self._packer = SpriteSheetPacker(
            algorithm=packing_algorithm,
            padding=padding,
            max_width=max_size[0],
            max_height=max_size[1],
            power_of_two=power_of_two,
        )
        
        logger.debug(
            f"AtlasBuilder initialized: padding={padding}, "
            f"max_size={max_size}, power_of_two={power_of_two}, "
            f"algorithm={packing_algorithm.value}"
        )
    
    async def add_asset(
        self,
        name: str,
        image: Image.Image,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Add an asset to be included in the atlas.
        
        Args:
            name: Asset identifier (must be unique)
            image: PIL Image containing the asset
            metadata: Optional metadata to associate with this asset
        
        Raises:
            ValueError: If asset name already exists or image is invalid
        """
        if name in self._assets:
            raise ValueError(f"Asset with name '{name}' already exists")
        
        if image.mode not in ('RGB', 'RGBA'):
            raise ValueError(f"Image mode must be RGB or RGBA, got {image.mode}")
        
        # Convert PIL Image to PixelGrid
        try:
            grid = PixelGrid.from_pil(image)
        except Exception as e:
            raise ValueError(f"Failed to convert image to PixelGrid: {e}")
        
        # Store asset and metadata
        self._assets[name] = grid
        self._metadata_map[name] = metadata or {}
        
        logger.debug(f"Added asset '{name}': {grid.width}x{grid.height}")
    
    async def add_asset_from_file(
        self,
        name: str,
        file_path: Path,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Add an asset from a PNG file.
        
        Args:
            name: Asset identifier (must be unique)
            file_path: Path to PNG file
            metadata: Optional metadata to associate with this asset
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a valid image
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            image = Image.open(file_path)
            await self.add_asset(name, image, metadata)
        except Exception as e:
            raise ValueError(f"Failed to load image from {file_path}: {e}")
    
    async def build_atlas(
        self,
        output_path: Path,
        atlas_name: str,
    ) -> Path:
        """
        Build and save the texture atlas.
        
        Creates:
        - {atlas_name}.png - Combined texture atlas image
        - {atlas_name}.json - Metadata with sprite coordinates
        
        Args:
            output_path: Directory to save atlas files
            atlas_name: Base name for atlas files
        
        Returns:
            Path to the atlas PNG file
        
        Raises:
            ValueError: If no assets have been added or packing fails
        """
        if not self._assets:
            raise ValueError("No assets to pack into atlas")
        
        logger.info(f"Building atlas '{atlas_name}' with {len(self._assets)} assets")
        
        # Pack sprites using SpriteSheetPacker
        try:
            sprite_sheet = self._packer.pack(self._assets, sort_by="area")
        except Exception as e:
            raise ValueError(f"Failed to pack sprites: {e}")
        
        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Export atlas PNG
        atlas_png_path = output_path / f"{atlas_name}.png"
        atlas_grid = sprite_sheet.to_grid()
        
        exporter = PNGExporter(scale=1, include_metadata=True)
        exporter.export(atlas_grid, atlas_png_path)
        
        logger.info(f"Atlas PNG saved: {atlas_png_path}")
        
        # Generate and save metadata JSON
        metadata_path = output_path / f"{atlas_name}.json"
        metadata = self._generate_metadata(sprite_sheet, atlas_name)
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Atlas metadata saved: {metadata_path}")
        
        return atlas_png_path
    
    def _generate_metadata(
        self,
        sprite_sheet: SpriteSheet,
        atlas_name: str,
    ) -> dict[str, Any]:
        """
        Generate atlas metadata in standard format.
        
        Args:
            sprite_sheet: Packed sprite sheet
            atlas_name: Name of the atlas
        
        Returns:
            Metadata dictionary with sprite coordinates
        """
        sprites_metadata = {}
        
        for frame in sprite_sheet.frames:
            sprite_info = {
                "x": frame.x,
                "y": frame.y,
                "width": frame.width,
                "height": frame.height,
            }
            
            # Add custom metadata if available
            if frame.name in self._metadata_map:
                sprite_info["metadata"] = self._metadata_map[frame.name]
            
            sprites_metadata[frame.name] = sprite_info
        
        return {
            "atlas_name": atlas_name,
            "texture_size": [sprite_sheet.width, sprite_sheet.height],
            "sprites": sprites_metadata,
            "metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "total_sprites": len(sprite_sheet.frames),
                "padding": sprite_sheet.padding,
                "power_of_two": self.power_of_two,
                "packing_algorithm": self.packing_algorithm.value,
            }
        }
    
    def get_metadata(self) -> dict[str, Any]:
        """
        Get current atlas metadata without building.
        
        Returns:
            Dictionary with metadata (sprites not yet positioned)
        
        Raises:
            ValueError: If no assets have been added
        """
        if not self._assets:
            raise ValueError("No assets added to atlas")
        
        # Create temporary packed sheet to get positions
        try:
            sprite_sheet = self._packer.pack(self._assets, sort_by="area")
            return self._generate_metadata(sprite_sheet, "preview")
        except Exception as e:
            raise ValueError(f"Failed to generate metadata: {e}")
    
    def clear(self) -> None:
        """Clear all added assets and reset the builder."""
        self._assets.clear()
        self._metadata_map.clear()
        logger.debug("Atlas builder cleared")
    
    @property
    def asset_count(self) -> int:
        """Get the number of assets currently added."""
        return len(self._assets)
    
    @property
    def asset_names(self) -> list[str]:
        """Get list of asset names currently added."""
        return list(self._assets.keys())


async def build_atlas_from_directory(
    input_dir: Path,
    output_dir: Path,
    atlas_name: str,
    pattern: str = "*.png",
    **kwargs: Any,
) -> tuple[Path, dict[str, Any]]:
    """
    Build an atlas from all PNG files in a directory.
    
    Convenience function that scans a directory for PNG files and
    builds an atlas from them.
    
    Args:
        input_dir: Directory containing PNG files
        output_dir: Directory to save atlas files
        atlas_name: Name for the atlas
        pattern: Glob pattern for finding files (default: "*.png")
        **kwargs: Additional arguments passed to AtlasBuilder
    
    Returns:
        Tuple of (atlas PNG path, metadata dict)
    
    Raises:
        FileNotFoundError: If input directory doesn't exist
        ValueError: If no matching files found
    
    Example:
        >>> path, metadata = await build_atlas_from_directory(
        ...     Path("assets/items"),
        ...     Path("output"),
        ...     "items_atlas"
        ... )
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    # Find all matching files
    png_files = list(input_dir.glob(pattern))
    if not png_files:
        raise ValueError(f"No files matching '{pattern}' found in {input_dir}")
    
    logger.info(f"Found {len(png_files)} files matching '{pattern}'")
    
    # Create atlas builder
    builder = AtlasBuilder(**kwargs)
    
    # Add all files
    for png_file in png_files:
        asset_name = png_file.stem
        try:
            await builder.add_asset_from_file(asset_name, png_file)
        except Exception as e:
            logger.warning(f"Skipping {png_file}: {e}")
            continue
    
    if builder.asset_count == 0:
        raise ValueError("No valid assets could be loaded")
    
    # Build atlas
    atlas_path = await builder.build_atlas(output_dir, atlas_name)
    metadata = builder.get_metadata()
    
    return atlas_path, metadata