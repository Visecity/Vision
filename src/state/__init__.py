"""
State management package for Vision pixel art generation.

This package provides workflow state management, persistence, and orchestration
capabilities for the multi-agent sprite generation pipeline.

Key Components:
    - WorkflowState: Pydantic model for workflow state tracking
    - StateManager: Redis-backed state persistence
    - WorkflowExecutor: Complete workflow orchestration
    - LangGraph workflow: Agent coordination graph

Example Usage:
    >>> from src.state import WorkflowExecutor, WorkflowState
    >>> from src.core.models import SpriteRequest, AssetType, Dimensions
    >>> 
    >>> # Create a sprite request
    >>> request = SpriteRequest(
    ...     description="A small oak tree",
    ...     asset_type=AssetType.SPRITE,
    ...     dimensions=Dimensions(width=16, height=16)
    ... )
    >>> 
    >>> # Execute workflow
    >>> async with WorkflowExecutor() as executor:
    ...     result = await executor.execute(request, session_id="user-123")
    ...     print(f"Status: {result.status}")
    ...     print(f"Generated: {result.metadata.file_path if result.metadata else 'N/A'}")
"""

from src.state.executor import WorkflowExecutor
from src.state.manager import StateManager
from src.state.models import StateSnapshot, WorkflowState, WorkflowStep
from src.state.workflow import (
    AgentState,
    agent_state_to_workflow_state,
    create_workflow_graph,
    workflow_state_to_agent_state,
)

__all__ = [
    # Core state models
    "WorkflowState",
    "WorkflowStep",
    "StateSnapshot",
    # State management
    "StateManager",
    # Workflow execution
    "WorkflowExecutor",
    # Workflow graph utilities
    "AgentState",
    "create_workflow_graph",
    "workflow_state_to_agent_state",
    "agent_state_to_workflow_state",
]