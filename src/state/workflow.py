"""
LangGraph workflow definition for Vision sprite generation.

This module defines the state graph that coordinates multiple agents
in the sprite generation pipeline, managing state transitions and
conditional routing.
"""

import logging
from typing import Any, TypedDict

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


class AgentState(TypedDict, total=False):
    """
    State structure for LangGraph workflow.

    This TypedDict defines the shape of state passed between nodes
    in the workflow graph.
    """

    request: SpriteRequest
    design: dict[str, Any]
    palette: ColorPalette
    details: dict[str, Any]
    animation: list[dict[str, Any]] | None
    messages: list[AgentMessage]
    error: str | None
    retry_count: int


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

        # Create agent context
        context = AgentContext(
            request=state["request"],
            current_step="design",
            previous_results={},
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

        # Create palette agent
        agent = PaletteAgent(llm_client=llm_client)

        # Create agent context with design from previous step
        context = AgentContext(
            request=state["request"],
            current_step="palette",
            previous_results={"design": state.get("design")},
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

        # Create detail agent
        agent = DetailAgent(llm_client=llm_client)

        # Create agent context with design and palette from previous steps
        context = AgentContext(
            request=state["request"],
            current_step="detail",
            previous_results={
                "design": state.get("design"),
                "palette": state.get("palette"),
            },
            retry_count=state.get("retry_count", 0),
        )

        # Execute agent
        detail_spec = await agent.process(context)

        # Update state
        state["details"] = detail_spec
        state["messages"] = state.get("messages", []) + agent.get_processing_history()

        logger.info("Detail node completed successfully")
        return state

    except Exception as e:
        logger.error(f"Detail node failed: {e}")
        state["error"] = f"Detail generation failed: {str(e)}"
        return state


async def animation_node(state: AgentState, llm_client: LLMClient) -> AgentState:
    """
    Animation agent node - generates animation frames.

    Args:
        state: Current workflow state
        llm_client: LLM client for agent initialization

    Returns:
        Updated state with animation frames
    """
    try:
        logger.info("Executing animation node")

        # Check for errors from previous steps
        if state.get("error"):
            logger.warning("Skipping animation node due to previous error")
            return state

        # Create animation agent
        agent = AnimationAgent(llm_client=llm_client)

        # Create agent context with all previous results
        context = AgentContext(
            request=state["request"],
            current_step="animation",
            previous_results={
                "design": state.get("design"),
                "palette": state.get("palette"),
                "detail": state.get("details"),
            },
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

        logger.info("Animation node completed successfully")
        return state

    except Exception as e:
        logger.error(f"Animation node failed: {e}")
        state["error"] = f"Animation generation failed: {str(e)}"
        return state


def should_animate(state: AgentState) -> str:
    """
    Conditional edge function to determine if animation should be generated.

    Args:
        state: Current workflow state

    Returns:
        "animation" if animation is requested, END otherwise
    """
    # Check if there's an error - skip animation if so
    if state.get("error"):
        logger.warning("Skipping animation due to error in previous steps")
        return END

    # Check if animation is requested
    request = state.get("request")
    if request and request.animation and request.animation.frame_count > 1:
        logger.info("Animation requested, routing to animation node")
        return "animation"

    logger.info("No animation requested, completing workflow")
    return END


def create_workflow_graph(llm_client: LLMClient) -> StateGraph:
    """
    Create and compile the LangGraph workflow for sprite generation.

    This function sets up the complete workflow graph with all agent nodes
    and conditional routing logic.

    Args:
        llm_client: LLM client to pass to agent nodes

    Returns:
        Compiled StateGraph ready for execution

    Example:
        >>> from src.llm.client import LLMClient
        >>> from src.core.config import get_settings
        >>> 
        >>> settings = get_settings()
        >>> llm_client = LLMClient(api_key=settings.anthropic_api_key)
        >>> workflow = create_workflow_graph(llm_client)
        >>> 
        >>> # Execute workflow
        >>> initial_state = {
        ...     "request": sprite_request,
        ...     "messages": [],
        ...     "retry_count": 0,
        ... }
        >>> result = await workflow.ainvoke(initial_state)
    """
    logger.info("Creating workflow graph")

    # Create state graph
    workflow = StateGraph(AgentState)

    # Add nodes - wrap each agent node with llm_client
    async def _design_node(state: AgentState) -> AgentState:
        return await design_node(state, llm_client)

    async def _palette_node(state: AgentState) -> AgentState:
        return await palette_node(state, llm_client)

    async def _detail_node(state: AgentState) -> AgentState:
        return await detail_node(state, llm_client)

    async def _animation_node(state: AgentState) -> AgentState:
        return await animation_node(state, llm_client)

    workflow.add_node("design", _design_node)
    workflow.add_node("palette", _palette_node)
    workflow.add_node("detail", _detail_node)
    workflow.add_node("animation", _animation_node)

    # Define workflow edges
    workflow.set_entry_point("design")
    workflow.add_edge("design", "palette")
    workflow.add_edge("palette", "detail")

    # Conditional edge: animate only if requested
    workflow.add_conditional_edges(
        "detail",
        should_animate,
        {
            "animation": "animation",
            END: END,
        },
    )

    # Animation always leads to end
    workflow.add_edge("animation", END)

    # Compile the graph
    compiled_workflow = workflow.compile()
    logger.info("Workflow graph compiled successfully")

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
        agent_state["details"] = state.detail_output
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

    if "details" in agent_state:
        workflow_state.detail_output = agent_state["details"]
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