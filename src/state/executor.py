"""
Workflow executor for Vision sprite generation.

This module provides the WorkflowExecutor class that orchestrates
complete sprite generation workflows, managing state, agents, and results.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable
from uuid import UUID

from redis import Redis
from redis.exceptions import RedisError

from src.core.config import get_settings
from src.core.models import (
    GenerationResult,
    GenerationStatus,
    SpriteMetadata,
    SpriteRequest,
)
from src.llm.client import LLMClient
from src.state.manager import StateManager
from src.state.models import WorkflowState, WorkflowStep
from src.state.workflow import (
    agent_state_to_workflow_state,
    create_workflow_graph,
    workflow_state_to_agent_state,
)

logger = logging.getLogger(__name__)

# Type alias for progress callback
ProgressCallback = Callable[[str, float, dict[str, Any]], None]


class WorkflowExecutor:
    """
    Executes complete sprite generation workflows.

    This class coordinates the multi-agent workflow, manages state persistence,
    handles error recovery, and provides progress monitoring capabilities.

    Attributes:
        llm_client: LLM client for agent execution
        state_manager: State manager for persistence
        settings: Application settings
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        state_manager: StateManager | None = None,
    ) -> None:
        """
        Initialize workflow executor.

        Args:
            llm_client: Optional LLM client. If not provided, creates one from settings.
            state_manager: Optional state manager. If not provided, creates one.
        """
        self.settings = get_settings()

        # Initialize LLM client with Redis caching
        if llm_client is None:
            # Initialize Redis client for caching if enabled
            redis_client = None
            if self.settings.performance.enable_caching:
                try:
                    redis_client = Redis(
                        host=self.settings.redis.host,
                        port=self.settings.redis.port,
                        password=self.settings.redis.password if self.settings.redis.password else None,
                        db=self.settings.redis.db,
                        decode_responses=True,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                    )
                    # Test connection
                    redis_client.ping()
                    logger.info(f"Redis cache enabled: {self.settings.redis.host}:{self.settings.redis.port}")
                except (RedisError, Exception) as e:
                    logger.warning(f"Redis connection failed, caching disabled: {e}")
                    redis_client = None

            self.llm_client = LLMClient(settings=self.settings, redis_client=redis_client)
        else:
            self.llm_client = llm_client

        # Initialize state manager
        self.state_manager = state_manager or StateManager()

        # Create workflow graph
        self.workflow = create_workflow_graph(self.llm_client)

        logger.info("WorkflowExecutor initialized")

    async def execute(
        self,
        request: SpriteRequest,
        session_id: str = "default",
        progress_callback: ProgressCallback | None = None,
    ) -> GenerationResult:
        """
        Execute a complete sprite generation workflow.

        This is the main entry point for workflow execution. It handles
        state initialization, workflow execution, error recovery, and
        result generation.

        Args:
            request: Sprite generation request
            session_id: Session identifier for state management
            progress_callback: Optional callback for progress updates

        Returns:
            GenerationResult with complete generation outcome

        Example:
            >>> executor = WorkflowExecutor()
            >>> request = SpriteRequest(
            ...     description="A small tree sprite",
            ...     asset_type=AssetType.SPRITE,
            ...     dimensions=Dimensions(width=16, height=16)
            ... )
            >>> result = await executor.execute(request, session_id="user-123")
            >>> print(result.status)
        """
        start_time = datetime.utcnow()

        try:
            logger.info(f"Starting workflow execution for request {request.request_id}")

            # Initialize workflow state
            workflow_state = WorkflowState(
                session_id=session_id,
                request=request,
                status=GenerationStatus.IN_PROGRESS,
                current_step=WorkflowStep.DESIGN,
            )

            # Save initial state
            await self.state_manager.save_state(workflow_state)

            # Send progress update
            if progress_callback:
                progress_callback("initialized", 0.0, {"workflow_id": str(workflow_state.workflow_id)})

            # Execute workflow
            final_state = await self._execute_workflow(
                workflow_state,
                progress_callback,
            )

            # Generate result
            result = await self._generate_result(final_state, start_time)

            logger.info(f"Workflow execution completed with status: {result.status}")
            return result

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)

            # Create error result
            return GenerationResult(
                request_id=request.request_id,
                status=GenerationStatus.FAILED,
                error_message=f"Workflow execution failed: {str(e)}",
                agent_messages=[],
                completed_at=datetime.utcnow(),
            )

    async def execute_async(
        self,
        request: SpriteRequest,
        session_id: str = "default",
    ) -> UUID:
        """
        Start workflow execution asynchronously and return workflow ID.

        This method starts the workflow in the background and immediately
        returns the workflow ID. Use get_status() to check progress.

        Args:
            request: Sprite generation request
            session_id: Session identifier for state management

        Returns:
            UUID of the workflow for status tracking

        Example:
            >>> executor = WorkflowExecutor()
            >>> workflow_id = await executor.execute_async(request, "user-123")
            >>> # Later, check status
            >>> status = await executor.get_status(workflow_id)
        """
        # Initialize workflow state
        workflow_state = WorkflowState(
            session_id=session_id,
            request=request,
            status=GenerationStatus.IN_PROGRESS,
            current_step=WorkflowStep.DESIGN,
        )

        # Save initial state
        await self.state_manager.save_state(workflow_state)

        # Start workflow in background
        asyncio.create_task(self._execute_workflow_background(workflow_state))

        logger.info(f"Started async workflow {workflow_state.workflow_id}")
        return workflow_state.workflow_id

    async def get_status(self, workflow_id: UUID) -> dict[str, Any]:
        """
        Get current status of a workflow execution.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Dictionary with workflow status information

        Example:
            >>> status = await executor.get_status(workflow_id)
            >>> print(status["status"])
            >>> print(status["current_step"])
            >>> print(status["progress_percentage"])
        """
        # Load workflow state
        state = await self.state_manager.load_state(workflow_id)

        if state is None:
            return {
                "workflow_id": str(workflow_id),
                "status": "not_found",
                "error": "Workflow not found",
            }

        # Calculate progress
        total_steps = 3  # design, palette, detail (animation is optional)
        if state.request.animation:
            total_steps = 4

        completed_count = len(state.completed_steps)
        progress = (completed_count / total_steps) * 100

        return {
            "workflow_id": str(state.workflow_id),
            "status": state.status.value,
            "current_step": state.current_step.value,
            "completed_steps": [step.value for step in state.completed_steps],
            "progress_percentage": progress,
            "error": state.error_message,
            "retry_count": state.retry_count,
            "created_at": state.created_at.isoformat(),
            "updated_at": state.updated_at.isoformat(),
        }

    async def resume_workflow(
        self,
        workflow_id: UUID,
        progress_callback: ProgressCallback | None = None,
    ) -> GenerationResult:
        """
        Resume a failed or interrupted workflow from last checkpoint.

        Args:
            workflow_id: Workflow identifier to resume
            progress_callback: Optional callback for progress updates

        Returns:
            GenerationResult with generation outcome

        Raises:
            ValueError: If workflow cannot be resumed
        """
        # Load workflow state
        state = await self.state_manager.load_state(workflow_id)

        if state is None:
            raise ValueError(f"Workflow {workflow_id} not found")

        if not state.can_resume():
            raise ValueError(
                f"Workflow {workflow_id} cannot be resumed (status: {state.status}, retries: {state.retry_count})"
            )

        logger.info(f"Resuming workflow {workflow_id} from checkpoint {state.last_checkpoint}")

        # Increment retry count
        state.retry_count += 1
        state.status = GenerationStatus.IN_PROGRESS
        state.error_message = None
        await self.state_manager.save_state(state)

        # Execute from current point
        start_time = datetime.utcnow()
        final_state = await self._execute_workflow(state, progress_callback)

        return await self._generate_result(final_state, start_time)

    async def _execute_workflow(
        self,
        workflow_state: WorkflowState,
        progress_callback: ProgressCallback | None = None,
    ) -> WorkflowState:
        """
        Execute the workflow graph and update state.

        Args:
            workflow_state: Initial workflow state
            progress_callback: Optional callback for progress updates

        Returns:
            Final workflow state after execution
        """
        try:
            # Convert to agent state for graph execution
            agent_state = workflow_state_to_agent_state(workflow_state)

            # Execute workflow graph
            logger.info("Invoking workflow graph")
            result_state = await self.workflow.ainvoke(agent_state)

            # Update workflow state from result
            workflow_state = agent_state_to_workflow_state(result_state, workflow_state)

            # Set final status
            if workflow_state.error_message:
                workflow_state.status = GenerationStatus.FAILED
            else:
                workflow_state.status = GenerationStatus.COMPLETED
                workflow_state.completed_at = datetime.utcnow()

            # Save final state
            await self.state_manager.save_state(workflow_state)

            # Send completion callback
            if progress_callback:
                progress_callback(
                    "completed" if not workflow_state.error_message else "failed",
                    100.0 if not workflow_state.error_message else 0.0,
                    {"workflow_id": str(workflow_state.workflow_id)},
                )

            return workflow_state

        except Exception as e:
            logger.error(f"Workflow execution error: {e}", exc_info=True)

            # Update state with error
            workflow_state.set_error(str(e))
            await self.state_manager.save_state(workflow_state)

            # Send error callback
            if progress_callback:
                progress_callback(
                    "error",
                    0.0,
                    {"error": str(e), "workflow_id": str(workflow_state.workflow_id)},
                )

            return workflow_state

    async def _execute_workflow_background(self, workflow_state: WorkflowState) -> None:
        """
        Execute workflow in background (for async execution).

        Args:
            workflow_state: Initial workflow state
        """
        try:
            await self._execute_workflow(workflow_state, None)
        except Exception as e:
            logger.error(f"Background workflow execution failed: {e}", exc_info=True)

    async def _generate_result(
        self,
        workflow_state: WorkflowState,
        start_time: datetime,
    ) -> GenerationResult:
        """
        Generate final GenerationResult from workflow state.

        Args:
            workflow_state: Final workflow state
            start_time: Workflow start timestamp

        Returns:
            GenerationResult with complete outcome
        """
        generation_time = (datetime.utcnow() - start_time).total_seconds()

        # Create metadata if successful
        metadata = None
        manifest_json = None
        warnings = []
        rendering_info: dict[str, Any] = {}

        if workflow_state.status == GenerationStatus.COMPLETED and workflow_state.detail_output:
            # Extract colors used
            colors_used = workflow_state.detail_output.get("final_specs", {}).get("colors_used", [])

            # Create palette from used colors
            from src.core.models import ColorPalette

            if workflow_state.palette_output:
                palette_used = workflow_state.palette_output
            else:
                palette_used = ColorPalette(
                    name="Generated Palette",
                    colors=colors_used if colors_used else ["#000000"],
                )

            # Determine frame count
            frame_count = 1
            if workflow_state.animation_output:
                frame_count = len(workflow_state.animation_output)

            # Create manifest JSON from detail output
            detail_output = workflow_state.detail_output
            
            # Convert DetailAgent output to Manifest JSON DSL format
            manifest_json = None
            if detail_output:
                try:
                    from src.rendering.manifest_converter import convert_detail_to_manifest
                    
                    asset_name = self._derive_asset_name(
                        workflow_state.request.description,
                        workflow_state.request.request_id,
                    )
                    
                    manifest_json = convert_detail_to_manifest(
                        detail_spec=detail_output,
                        asset_name=asset_name,
                        asset_description=workflow_state.request.description,
                    )
                    
                    logger.info(f"Converted DetailAgent output to Manifest JSON: {asset_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to convert DetailAgent output to Manifest: {e}")
                    warnings.append(f"Manifest conversion failed: {str(e)}")
                    manifest_json = None

            # Automatic rendering if enabled
            if self.settings.rendering.auto_render and manifest_json:
                render_start = datetime.utcnow()
                try:
                    from pathlib import Path
                    from src.rendering.manifest_renderer import ManifestRenderer
                    from src.rendering.pixel import Color
                    from src.agents.base import RenderingError

                    # Derive asset name from description
                    asset_name = self._derive_asset_name(
                        workflow_state.request.description,
                        workflow_state.request.request_id,
                    )

                    # Determine output path
                    output_dir = Path(self.settings.output.output_dir) / str(workflow_state.request.request_id)
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    manifest_path = output_dir / f"{asset_name}.json"
                    png_path = output_dir / f"{asset_name}.png"

                    # Save manifest JSON first
                    import json
                    with open(manifest_path, 'w') as f:
                        json.dump(manifest_json, f, indent=2)
                    
                    logger.info(f"Saved manifest to {manifest_path}")

                    # Parse transparent color
                    transparent_color = None
                    if self.settings.rendering.transparent_color:
                        try:
                            transparent_color = Color.from_hex(
                                self.settings.rendering.transparent_color
                            )
                        except Exception as e:
                            logger.warning(f"Invalid transparent color, using None: {e}")

                    # Render manifest to PNG
                    renderer = ManifestRenderer(
                        scale=self.settings.rendering.render_scale,
                        include_metadata=self.settings.rendering.include_metadata,
                    )

                    rendered_path = await renderer.render_manifest_async(
                        manifest_json,
                        png_path,
                        transparent_color=transparent_color,
                    )

                    render_time = (datetime.utcnow() - render_start).total_seconds()
                    logger.info(f"Rendered PNG to {rendered_path} in {render_time:.2f}s")

                    # Update rendering info
                    rendering_info = {
                        "png_path": str(rendered_path),
                        "manifest_path": str(manifest_path),
                        "auto_rendered": True,
                        "render_time_seconds": render_time,
                        "sprite_sheet": frame_count > 1,
                        "frame_count": frame_count,
                    }

                    # Export individual frames if requested and is animation
                    if (self.settings.rendering.export_individual_frames
                        and frame_count > 1):
                        try:
                            from src.rendering.manifest_renderer import render_animation_frames
                            
                            frames_dir = output_dir / "frames"
                            frame_paths = render_animation_frames(
                                manifest_json,
                                frames_dir,
                                name_prefix=asset_name,
                                scale=self.settings.rendering.render_scale,
                                transparent_color=transparent_color,
                            )
                            rendering_info["individual_frames"] = [str(p) for p in frame_paths]
                            logger.info(f"Exported {len(frame_paths)} individual frames")
                        except Exception as e:
                            logger.warning(f"Failed to export individual frames: {e}")
                            warnings.append(f"Individual frame export failed: {str(e)}")

                except RenderingError as e:
                    error_msg = f"Rendering failed: {str(e)}"
                    logger.error(error_msg)
                    rendering_info = {
                        "auto_rendered": False,
                        "render_error": str(e),
                    }
                    
                    if self.settings.rendering.fail_on_render_error:
                        # Fail the entire generation
                        return GenerationResult(
                            request_id=workflow_state.request.request_id,
                            status=GenerationStatus.FAILED,
                            error_message=error_msg,
                            agent_messages=workflow_state.messages,
                            warnings=warnings,
                            completed_at=datetime.utcnow(),
                            rendering_info=rendering_info,
                        )
                    else:
                        # Continue with warning
                        warnings.append(error_msg)

                except Exception as e:
                    error_msg = f"Unexpected rendering error: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    rendering_info = {
                        "auto_rendered": False,
                        "render_error": str(e),
                    }
                    
                    if self.settings.rendering.fail_on_render_error:
                        return GenerationResult(
                            request_id=workflow_state.request.request_id,
                            status=GenerationStatus.FAILED,
                            error_message=error_msg,
                            agent_messages=workflow_state.messages,
                            warnings=warnings,
                            completed_at=datetime.utcnow(),
                            rendering_info=rendering_info,
                        )
                    else:
                        warnings.append(error_msg)

            # Create metadata
            file_path = rendering_info.get("png_path", "")
            metadata = SpriteMetadata(
                request_id=workflow_state.request.request_id,
                asset_type=workflow_state.request.asset_type,
                style=workflow_state.request.style,
                dimensions=workflow_state.request.dimensions,
                palette_used=palette_used,
                file_path=file_path,
                frame_count=frame_count,
                tags=workflow_state.request.tags,
                generation_time_seconds=generation_time,
            )

        # Create result
        return GenerationResult(
            request_id=workflow_state.request.request_id,
            status=workflow_state.status,
            metadata=metadata,
            manifest_json=manifest_json,
            error_message=workflow_state.error_message,
            agent_messages=workflow_state.messages,
            warnings=warnings,
            completed_at=datetime.utcnow(),
            rendering_info=rendering_info,
        )

    def _derive_asset_name(self, description: str, request_id: UUID) -> str:
        """
        Derive asset filename from description.

        Args:
            description: User description
            request_id: Request UUID for fallback

        Returns:
            str: Safe filename base (without extension)
        """
        import re
        
        # Take first 3-5 significant words
        words = description.lower().split()
        significant_words = [w for w in words if len(w) > 2][:5]
        
        if not significant_words:
            return f"asset_{str(request_id)[:8]}"
        
        base_name = "_".join(significant_words)
        # Remove special chars except _ and -
        base_name = re.sub(r'[^a-z0-9_-]', '', base_name)
        
        return base_name[:50] if base_name else f"asset_{str(request_id)[:8]}"

    async def cleanup(self, workflow_id: UUID) -> bool:
        """
        Clean up workflow state and resources.

        Args:
            workflow_id: Workflow identifier to clean up

        Returns:
            True if cleanup successful
        """
        try:
            await self.state_manager.delete_state(workflow_id)
            logger.info(f"Cleaned up workflow {workflow_id}")
            return True
        except Exception as e:
            logger.error(f"Cleanup failed for workflow {workflow_id}: {e}")
            return False

    async def close(self) -> None:
        """Close executor and release resources."""
        await self.state_manager.close()
        logger.info("WorkflowExecutor closed")

    async def __aenter__(self) -> "WorkflowExecutor":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()