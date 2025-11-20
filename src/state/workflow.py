"""
LangGraph workflow definition for Vision sprite generation.

This module defines the state graph that coordinates multiple agents
in the sprite generation pipeline, managing state transitions and
conditional routing.

Includes parallel execution support for animation frames to improve performance.
Optimized for minimal context passing to reduce token usage.
"""

import logging
import time
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, StateGraph

from src.agents.animation_agent import AnimationAgent
from src.agents.design_agent import DesignAgent
from src.agents.detail_agent import DetailAgent
from src.agents.palette_agent import PaletteAgent
from src.core.models import (
    AgentContext,
    AgentMessage,
    ColorPalette,
    SpriteRequest,
)
from src.llm.client import LLMClient
from src.state.models import WorkflowState, WorkflowStep

logger = logging.getLogger(__name__)

# Maximum number of parallel animation frame nodes to create
MAX_PARALLEL_FRAMES = 8


def merge_animation_frames(left: dict, right: dict) -> dict:
    """
    Merge animation frame dictionaries for parallel execution.
    
    This reducer is used by LangGraph to combine concurrent writes
    to the animation_frames field from multiple parallel nodes.
    
    Args:
        left: Existing animation frames dict
        right: New animation frames dict to merge
    
    Returns:
        Merged dict with all frame data
    """
    return {**left, **right}


def merge_timing_dict(left: dict[str, float], right: dict[str, float]) -> dict[str, float]:
    """Merge timing dictionaries for parallel execution.
    
    Args:
        left: Existing timing data
        right: New timing data to merge
        
    Returns:
        Combined timing dictionary with all entries
    """
    return {**left, **right}

# Agent dependency mapping for optimal context passing
# This defines exactly what each agent needs from previous results
AGENT_DEPENDENCIES = {
    "design": [],  # No dependencies - uses request only
    "palette": ["design"],  # Needs design output
    "detail": ["design", "palette"],  # Needs both design and palette
    "animation": ["design", "palette", "detail"],  # Needs all previous outputs
    "animation_frame": ["design", "palette", "detail"],  # Frame generation needs all context
}


def build_minimal_context(
    state: "AgentState",
    current_step: str,
    additional_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build minimal previous_results context for an agent.
    
    This function implements selective context passing to reduce token usage
    by only including fields that the agent actually needs.
    
    Args:
        state: Current workflow state
        current_step: Name of the agent step
        additional_fields: Optional additional fields to include (e.g., frame_index)
    
    Returns:
        dict: Minimal previous_results containing only required fields
    """
    previous_results: dict[str, Any] = {}
    
    # Get dependencies for this step
    dependencies = AGENT_DEPENDENCIES.get(current_step, [])
    
    # Build context with only required fields
    for dep in dependencies:
        if dep in state:
            previous_results[dep] = state[dep]
            logger.debug(f"Including '{dep}' in context for '{current_step}' (~{_estimate_size(state[dep])} chars)")
        else:
            logger.warning(f"Required dependency '{dep}' not found in state for '{current_step}'")
    
    # Add any additional fields (e.g., frame_index for animation frames)
    if additional_fields:
        previous_results.update(additional_fields)
        for key, value in additional_fields.items():
            logger.debug(f"Including additional field '{key}' in context for '{current_step}'")
    
    # Log context summary
    total_size = sum(_estimate_size(v) for v in previous_results.values())
    logger.info(
        f"Context for '{current_step}': {len(previous_results)} field(s), "
        f"~{total_size} chars, keys={list(previous_results.keys())}"
    )
    
    return previous_results


def _estimate_size(obj: Any) -> int:
    """
    Estimate the size of an object in characters for logging.
    
    Args:
        obj: Object to estimate size of
    
    Returns:
        int: Estimated size in characters
    """
    try:
        if isinstance(obj, str):
            return len(obj)
        elif isinstance(obj, (dict, list)):
            import json
            return len(json.dumps(obj, default=str))
        elif isinstance(obj, ColorPalette):
            return len(str(obj.colors))
        else:
            return len(str(obj))
    except Exception:
        return 0


def validate_context_dependencies(
    state: "AgentState",
    current_step: str,
) -> tuple[bool, list[str]]:
    """
    Validate that all required dependencies are present in state.
    
    Args:
        state: Current workflow state
        current_step: Name of the agent step
    
    Returns:
        tuple: (is_valid, list of missing dependencies)
    """
    dependencies = AGENT_DEPENDENCIES.get(current_step, [])
    missing = [dep for dep in dependencies if dep not in state]
    
    if missing:
        logger.error(f"Missing dependencies for '{current_step}': {missing}")
        return False, missing
    
    return True, []


class AgentState(TypedDict, total=False):
    """
    State structure for LangGraph workflow.

    This TypedDict defines the shape of state passed between nodes
    in the workflow graph.
    """

    request: SpriteRequest
    design: dict[str, Any]
    palette: ColorPalette
    detail: dict[str, Any]  # Fixed: Changed from 'details' to 'detail' to match AGENT_DEPENDENCIES
    animation: list[dict[str, Any]] | None
    animation_frames: Annotated[dict[int, dict[str, Any]], merge_animation_frames]  # Parallel frame storage with merge reducer
    messages: list[AgentMessage]
    error: str | None
    retry_count: int
    timing: Annotated[dict[str, float], merge_timing_dict]  # Performance timing data (supports concurrent writes)


async def design_node(state: AgentState, llm_client: LLMClient) -> AgentState:
    """
    Design agent node - creates design specifications.

    Args:
        state: Current workflow state
        llm_client: LLM client for agent initialization

    Returns:
        Updated state with design specification
    """
    try:
        logger.info("Executing design node")

        # Create design agent
        agent = DesignAgent(llm_client=llm_client)

        # Build minimal context (design has no dependencies)
        previous_results = build_minimal_context(state, "design")

        # Create agent context
        context = AgentContext(
            request=state["request"],
            current_step="design",
            previous_results=previous_results,
            retry_count=state.get("retry_count", 0),
        )

        # Execute agent
        design_spec = await agent.process(context)

        # Update state
        state["design"] = design_spec
        state["messages"] = state.get("messages", []) + agent.get_processing_history()

        logger.info("Design node completed successfully")
        return state

    except Exception as e:
        logger.error(f"Design node failed: {e}")
        state["error"] = f"Design generation failed: {str(e)}"
        return state


async def palette_node(state: AgentState, llm_client: LLMClient) -> AgentState:
    """
    Palette agent node - selects color palettes.

    Args:
        state: Current workflow state
        llm_client: LLM client for agent initialization

    Returns:
        Updated state with color palette
    """
    try:
        logger.info("Executing palette node")

        # Check for errors from previous steps
        if state.get("error"):
            logger.warning("Skipping palette node due to previous error")
            return state

        # Validate dependencies
        is_valid, missing = validate_context_dependencies(state, "palette")
        if not is_valid:
            state["error"] = f"Palette node missing dependencies: {missing}"
            return state

        # Create palette agent
        agent = PaletteAgent(llm_client=llm_client)

        # Build minimal context (palette needs design only)
        previous_results = build_minimal_context(state, "palette")

        # Create agent context
        context = AgentContext(
            request=state["request"],
            current_step="palette",
            previous_results=previous_results,
            retry_count=state.get("retry_count", 0),
        )

        # Execute agent
        palette = await agent.process(context)

        # Update state
        state["palette"] = palette
        state["messages"] = state.get("messages", []) + agent.get_processing_history()

        logger.info("Palette node completed successfully")
        return state

    except Exception as e:
        logger.error(f"Palette node failed: {e}")
        state["error"] = f"Palette generation failed: {str(e)}"
        return state


async def detail_node(state: AgentState, llm_client: LLMClient) -> AgentState:
    """
    Detail agent node - implements pixel-level details.
    
    Automatically selects RLE encoding for larger sprites to stay within
    API token limits.

    Args:
        state: Current workflow state
        llm_client: LLM client for agent initialization

    Returns:
        Updated state with pixel implementation
    """
    try:
        logger.info("Executing detail node")

        # Check for errors from previous steps
        if state.get("error"):
            logger.warning("Skipping detail node due to previous error")
            return state

        # Validate dependencies
        is_valid, missing = validate_context_dependencies(state, "detail")
        if not is_valid:
            state["error"] = f"Detail node missing dependencies: {missing}"
            return state

        # Create detail agent
        agent = DetailAgent(llm_client=llm_client)

        # Build minimal context (detail needs design and palette)
        previous_results = build_minimal_context(state, "detail")

        # Create agent context with RLE preference
        request = state["request"]
        context = AgentContext(
            request=request,
            current_step="detail",
            previous_results=previous_results,
            retry_count=state.get("retry_count", 0),
        )

        # Execute agent (it will choose RLE automatically if needed)
        detail_spec = await agent.process(context)

        # Update state (Fixed: Changed 'details' to 'detail' for consistency with AGENT_DEPENDENCIES)
        state["detail"] = detail_spec
        state["messages"] = state.get("messages", []) + agent.get_processing_history()

        logger.info("Detail node completed successfully")
        return state

    except Exception as e:
        logger.error(f"Detail node failed: {e}")
        state["error"] = f"Detail generation failed: {str(e)}"
        return state


async def animation_node(state: AgentState, llm_client: LLMClient) -> AgentState:
    """
    Animation agent node - generates animation frames (legacy sequential mode).

    This node generates all frames sequentially in a single LLM call.
    Use this when parallel execution is not beneficial (e.g., < 4 frames).

    Args:
        state: Current workflow state
        llm_client: LLM client for agent initialization

    Returns:
        Updated state with animation frames
    """
    try:
        start_time = time.time()
        logger.info("Executing animation node (sequential mode)")

        # Check for errors from previous steps
        if state.get("error"):
            logger.warning("Skipping animation node due to previous error")
            return state

        # Validate dependencies
        is_valid, missing = validate_context_dependencies(state, "animation")
        if not is_valid:
            state["error"] = f"Animation node missing dependencies: {missing}"
            return state

        # Create animation agent
        agent = AnimationAgent(llm_client=llm_client)

        # Build minimal context (animation needs design, palette, and detail)
        previous_results = build_minimal_context(state, "animation")

        # Create agent context
        context = AgentContext(
            request=state["request"],
            current_step="animation",
            previous_results=previous_results,
            retry_count=state.get("retry_count", 0),
        )

        # Execute agent
        animation_spec = await agent.process(context)

        # Update state
        frames = animation_spec.get("frames", [])
        if frames:
            state["animation"] = frames if isinstance(frames, list) else [frames]
        else:
            state["animation"] = None

        state["messages"] = state.get("messages", []) + agent.get_processing_history()

        # Record timing
        elapsed = time.time() - start_time
        timing = state.get("timing", {})
        timing["animation_sequential"] = elapsed
        state["timing"] = timing

        logger.info(f"Animation node completed successfully in {elapsed:.2f}s")
        return state

    except Exception as e:
        logger.error(f"Animation node failed: {e}")
        state["error"] = f"Animation generation failed: {str(e)}"
        return state


def create_animation_frame_node(frame_index: int, llm_client: LLMClient):
    """
    Factory function to create a parallel animation frame generation node.

    Each node generates a single animation frame independently, allowing
    multiple frames to be generated in parallel.

    Args:
        frame_index: The frame number to generate (0-based)
        llm_client: LLM client for agent initialization

    Returns:
        Async function that generates the specified frame
    """
    async def animation_frame_node(state: AgentState) -> AgentState:
        """Generate a single animation frame in parallel."""
        try:
            # Check if this frame should be generated
            request = state.get("request")
            if not request or not request.animation:
                logger.debug(f"Frame {frame_index}: No animation config, skipping")
                return state
            
            if frame_index >= request.animation.frame_count:
                logger.debug(f"Frame {frame_index}: Beyond frame_count ({request.animation.frame_count}), skipping")
                return state

            start_time = time.time()
            logger.info(f"Executing animation frame {frame_index} node")

            # Check for errors from previous steps
            if state.get("error"):
                logger.warning(f"Skipping frame {frame_index} due to previous error")
                return state

            # Create animation agent
            agent = AnimationAgent(llm_client=llm_client)

            # Build minimal context for frame generation
            additional_fields = {
                "frame_index": frame_index,
                "total_frames": request.animation.frame_count,
            }
            previous_results = build_minimal_context(
                state,
                "animation_frame",
                additional_fields=additional_fields
            )

            # Create context for single frame generation
            context = AgentContext(
                request=state["request"],
                current_step=f"animation_frame_{frame_index}",
                previous_results=previous_results,
                retry_count=state.get("retry_count", 0),
            )

            # Generate single frame
            frame_spec = await agent.process(context)

            # Store frame in parallel storage
            animation_frames = state.get("animation_frames", {})
            animation_frames[frame_index] = frame_spec

            # Record timing
            elapsed = time.time() - start_time
            timing = state.get("timing", {})
            timing[f"animation_frame_{frame_index}"] = elapsed

            logger.info(f"Frame {frame_index} completed in {elapsed:.2f}s")
            
            # Fixed: Return only updated fields to avoid concurrent state update errors
            # Do NOT include 'request' or other shared fields
            return {"animation_frames": animation_frames, "timing": timing}

        except Exception as e:
            logger.error(f"Animation frame {frame_index} generation failed: {e}")
            # Don't set global error - allow other frames to complete
            logger.warning(f"Frame {frame_index} failed but continuing with other frames")
            # Fixed: Return empty dict to avoid concurrent state update errors
            return {}

    return animation_frame_node


async def aggregate_animation_frames(state: AgentState) -> AgentState:
    """
    Aggregate parallel animation frame results into final animation output.

    This node combines all individually generated frames into a cohesive
    animation sequence, ensuring proper ordering and consistency.

    Args:
        state: Current workflow state with animation_frames populated

    Returns:
        Updated state with aggregated animation output
    """
    try:
        start_time = time.time()
        logger.info("Aggregating parallel animation frames")

        # Check for errors
        if state.get("error"):
            logger.warning("Skipping aggregation due to previous error")
            return state

        # Get frame count
        request = state.get("request")
        if not request or not request.animation:
            logger.warning("No animation config found during aggregation")
            return state

        frame_count = request.animation.frame_count

        # Collect frames in order
        animation_frames = state.get("animation_frames", {})
        frames = []
        missing_frames = []

        for i in range(frame_count):
            if i in animation_frames:
                frame_data = animation_frames[i]
                # Extract frames from the frame_spec
                if isinstance(frame_data, dict):
                    if "frames" in frame_data:
                        frames.extend(frame_data["frames"] if isinstance(frame_data["frames"], list) else [frame_data["frames"]])
                    else:
                        frames.append(frame_data)
            else:
                missing_frames.append(i)
                logger.warning(f"Frame {i} missing from parallel generation")

        if missing_frames:
            logger.warning(f"Missing frames: {missing_frames}. Animation may be incomplete.")

        # Create aggregated animation spec
        aggregated = {
            "frames": frames,
            "frame_count": len(frames),
            "timing": {
                "frame_duration": request.animation.frame_duration,
                "total_duration": len(frames) * request.animation.frame_duration,
                "loop": request.animation.loop,
            },
            "is_animated": len(frames) > 1,
            "parallel_execution": True,
            "missing_frames": missing_frames,
            "_metadata": {
                "agent": "animation",
                "request_id": str(request.request_id),
                "generation_mode": "parallel",
                "frames_generated": len(frames),
                "frames_requested": frame_count,
            },
        }

        state["animation"] = frames if frames else None

        # Record timing
        elapsed = time.time() - start_time
        timing = state.get("timing", {})
        timing["animation_aggregation"] = elapsed
        state["timing"] = timing

        # Calculate total parallel time
        parallel_times = [v for k, v in timing.items() if k.startswith("animation_frame_")]
        if parallel_times:
            max_parallel_time = max(parallel_times)
            timing["animation_parallel_max"] = max_parallel_time
            timing["animation_parallel_total"] = sum(parallel_times)
            logger.info(
                f"Parallel execution: {len(parallel_times)} frames in {max_parallel_time:.2f}s "
                f"(sequential would be ~{sum(parallel_times):.2f}s, "
                f"speedup: {sum(parallel_times)/max_parallel_time:.1f}x)"
            )

        logger.info(f"Animation aggregation completed in {elapsed:.2f}s, {len(frames)} frames")
        return state

    except Exception as e:
        logger.error(f"Animation aggregation failed: {e}")
        state["error"] = f"Animation aggregation failed: {str(e)}"
        return state


def should_animate(state: AgentState) -> str:
    """
    Conditional edge function to determine animation execution mode.

    Routes to:
    - END: No animation needed
    - "animation": Sequential animation generation (< 4 frames)
    - "parallel_animation": Parallel frame generation (>= 4 frames)

    Args:
        state: Current workflow state

    Returns:
        Target node name or END
    """
    # Check if there's an error - skip animation if so
    if state.get("error"):
        logger.warning("Skipping animation due to error in previous steps")
        return END

    # Check if animation is requested
    request = state.get("request")
    if not request or not request.animation:
        logger.info("No animation requested, completing workflow")
        return END

    frame_count = request.animation.frame_count

    if frame_count < 2:
        logger.info("Single frame requested, no animation needed")
        return END

    # Use parallel execution for 4+ frames (significant speedup potential)
    if frame_count >= 4:
        logger.info(f"Routing to parallel animation generation ({frame_count} frames)")
        return "parallel_animation"
    else:
        logger.info(f"Routing to sequential animation generation ({frame_count} frames)")
        return "animation"


def create_workflow_graph(llm_client: LLMClient, enable_parallel: bool = True) -> StateGraph:
    """
    Create and compile the LangGraph workflow for sprite generation.

    This function sets up the complete workflow graph with all agent nodes
    and conditional routing logic. Supports both sequential and parallel
    execution modes for animation generation.

    Args:
        llm_client: LLM client to pass to agent nodes
        enable_parallel: Enable parallel frame generation for animations (default: True)

    Returns:
        Compiled StateGraph ready for execution

    Workflow Modes:
        - Sequential (< 4 frames): Design → Palette → Detail → Animation → END
        - Parallel (>= 4 frames): Design → Palette → Detail → [Frame0, Frame1, ...] → Aggregate → END

    Example:
        >>> from src.llm.client import LLMClient
        >>> from src.core.config import get_settings
        >>>
        >>> settings = get_settings()
        >>> llm_client = LLMClient(api_key=settings.anthropic_api_key)
        >>> workflow = create_workflow_graph(llm_client, enable_parallel=True)
        >>>
        >>> # Execute workflow
        >>> initial_state = {
        ...     "request": sprite_request,
        ...     "messages": [],
        ...     "retry_count": 0,
        ...     "timing": {},
        ... }
        >>> result = await workflow.ainvoke(initial_state)
    """
    start_time = time.time()
    logger.info(f"Creating workflow graph (parallel_mode={'enabled' if enable_parallel else 'disabled'})")

    # Create state graph
    workflow = StateGraph(AgentState)

    # Add core agent nodes
    async def _design_node(state: AgentState) -> AgentState:
        node_start = time.time()
        result = await design_node(state, llm_client)
        timing = result.get("timing", {})
        timing["design"] = time.time() - node_start
        result["timing"] = timing
        return result

    async def _palette_node(state: AgentState) -> AgentState:
        node_start = time.time()
        result = await palette_node(state, llm_client)
        timing = result.get("timing", {})
        timing["palette"] = time.time() - node_start
        result["timing"] = timing
        return result

    async def _detail_node(state: AgentState) -> AgentState:
        node_start = time.time()
        result = await detail_node(state, llm_client)
        timing = result.get("timing", {})
        timing["detail"] = time.time() - node_start
        result["timing"] = timing
        return result

    async def _animation_node(state: AgentState) -> AgentState:
        return await animation_node(state, llm_client)

    workflow.add_node("design", _design_node)
    workflow.add_node("palette", _palette_node)
    workflow.add_node("detail", _detail_node)
    workflow.add_node("animation", _animation_node)

    # Add parallel animation support
    if enable_parallel:
        # Create a router node that dynamically spawns parallel frame nodes
        async def _parallel_animation_router(state: AgentState) -> AgentState:
            """Route to dynamically created parallel animation frame nodes."""
            logger.info("Entering parallel animation router")
            
            # Initialize animation_frames dict and timing
            state["animation_frames"] = {}
            timing = state.get("timing", {})
            timing["parallel_animation_start"] = time.time()
            state["timing"] = timing
            
            return state

        workflow.add_node("parallel_animation", _parallel_animation_router)

        # Create parallel frame nodes (up to MAX_PARALLEL_FRAMES)
        # These will be used dynamically based on frame_count
        for i in range(MAX_PARALLEL_FRAMES):
            frame_node = create_animation_frame_node(i, llm_client)
            workflow.add_node(f"animation_frame_{i}", frame_node)

        # Add aggregation node
        workflow.add_node("aggregate_animation", aggregate_animation_frames)

        # Connect parallel_animation router to ALL frame nodes
        # LangGraph will execute them in parallel, each checks if it should run
        for i in range(MAX_PARALLEL_FRAMES):
            workflow.add_edge("parallel_animation", f"animation_frame_{i}")
            workflow.add_edge(f"animation_frame_{i}", "aggregate_animation")

        # Aggregation leads to END
        workflow.add_edge("aggregate_animation", END)

    # Define workflow structure
    workflow.set_entry_point("design")
    workflow.add_edge("design", "palette")
    workflow.add_edge("palette", "detail")

    # Conditional edge: route to appropriate animation mode or END
    if enable_parallel:
        workflow.add_conditional_edges(
            "detail",
            should_animate,
            {
                "animation": "animation",
                "parallel_animation": "parallel_animation",
                END: END,
            },
        )
        # Sequential animation still leads to END
        workflow.add_edge("animation", END)
    else:
        # Original sequential-only behavior
        workflow.add_conditional_edges(
            "detail",
            lambda state: "animation" if (
                state.get("request") and
                state.get("request").animation and
                state.get("request").animation.frame_count > 1
            ) else END,
            {
                "animation": "animation",
                END: END,
            },
        )
        workflow.add_edge("animation", END)

    # Compile the graph
    compiled_workflow = workflow.compile()
    
    elapsed = time.time() - start_time
    logger.info(f"Workflow graph compiled successfully in {elapsed:.3f}s")
    logger.info(f"Graph nodes: {len(workflow.nodes)}, Parallel mode: {enable_parallel}")

    return compiled_workflow


def workflow_state_to_agent_state(state: WorkflowState) -> AgentState:
    """
    Convert WorkflowState to AgentState for graph execution.

    Args:
        state: Workflow state from state manager

    Returns:
        AgentState compatible with LangGraph execution
    """
    agent_state: AgentState = {
        "request": state.request,
        "messages": state.messages,
        "retry_count": state.retry_count,
    }

    # Add optional fields if present
    if state.design_output:
        agent_state["design"] = state.design_output
    if state.palette_output:
        agent_state["palette"] = state.palette_output
    if state.detail_output:
        agent_state["detail"] = state.detail_output  # Fixed: Changed 'details' to 'detail'
    if state.animation_output:
        agent_state["animation"] = state.animation_output
    if state.error_message:
        agent_state["error"] = state.error_message

    return agent_state


def agent_state_to_workflow_state(
    agent_state: AgentState,
    workflow_state: WorkflowState,
) -> WorkflowState:
    """
    Update WorkflowState from AgentState after graph execution.

    Args:
        agent_state: State returned from graph execution
        workflow_state: Original workflow state to update

    Returns:
        Updated workflow state
    """
    # Update outputs
    if "design" in agent_state:
        workflow_state.design_output = agent_state["design"]
        workflow_state.mark_step_complete(WorkflowStep.DESIGN)

    if "palette" in agent_state:
        workflow_state.palette_output = agent_state["palette"]
        workflow_state.mark_step_complete(WorkflowStep.PALETTE)

    if "detail" in agent_state:
        workflow_state.detail_output = agent_state["detail"]
        workflow_state.mark_step_complete(WorkflowStep.DETAIL)

    if "animation" in agent_state and agent_state["animation"]:
        workflow_state.animation_output = agent_state["animation"]
        workflow_state.mark_step_complete(WorkflowStep.ANIMATION)

    # Update messages
    if "messages" in agent_state:
        workflow_state.messages = agent_state["messages"]

    # Update error state
    if "error" in agent_state and agent_state["error"]:
        workflow_state.set_error(agent_state["error"])

    # Update retry count
    if "retry_count" in agent_state:
        workflow_state.retry_count = agent_state["retry_count"]

    return workflow_state