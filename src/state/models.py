"""
State models for Vision workflow management.

This module defines Pydantic models for tracking workflow state,
including execution status, agent outputs, and checkpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.core.models import (
    AgentMessage,
    AnimationConfig,
    ColorPalette,
    GenerationStatus,
    SpriteRequest,
)


class WorkflowStep(str, Enum):
    """Steps in the sprite generation workflow."""

    DESIGN = "design"
    PALETTE = "palette"
    DETAIL = "detail"
    ANIMATION = "animation"
    COMPLETE = "complete"


class WorkflowState(BaseModel):
    """
    Complete state of a workflow execution.

    This model tracks the current state of a multi-agent workflow,
    including progress, intermediate results, and error information.
    """

    # Identifiers
    workflow_id: UUID = Field(
        default_factory=uuid4,
        description="Unique workflow instance identifier",
    )
    session_id: str = Field(
        description="User session identifier",
    )
    request: SpriteRequest = Field(
        description="Original sprite generation request",
    )

    # Progress tracking
    status: GenerationStatus = Field(
        default=GenerationStatus.PENDING,
        description="Overall workflow status",
    )
    current_step: WorkflowStep = Field(
        default=WorkflowStep.DESIGN,
        description="Current workflow step being executed",
    )
    completed_steps: list[WorkflowStep] = Field(
        default_factory=list,
        description="List of completed workflow steps",
    )

    # Agent outputs
    design_output: dict[str, Any] | None = Field(
        default=None,
        description="Output from design agent",
    )
    palette_output: ColorPalette | None = Field(
        default=None,
        description="Output from palette agent",
    )
    detail_output: dict[str, Any] | None = Field(
        default=None,
        description="Output from detail agent (pixel data, manifest)",
    )
    animation_output: list[dict[str, Any]] | None = Field(
        default=None,
        description="Output from animation agent (frame data)",
    )

    # Communication log
    messages: list[AgentMessage] = Field(
        default_factory=list,
        description="Log of all agent messages during workflow",
    )

    # Error handling
    error_message: str | None = Field(
        default=None,
        description="Error message if workflow failed",
    )
    retry_count: int = Field(
        default=0,
        ge=0,
        description="Number of retry attempts",
    )
    last_checkpoint: WorkflowStep | None = Field(
        default=None,
        description="Last successful checkpoint for recovery",
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Workflow creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Workflow completion timestamp",
    )

    def mark_step_complete(self, step: WorkflowStep) -> None:
        """Mark a workflow step as completed."""
        if step not in self.completed_steps:
            self.completed_steps.append(step)
        self.last_checkpoint = step
        self.updated_at = datetime.utcnow()

    def set_error(self, error: str) -> None:
        """Set error state for the workflow."""
        self.status = GenerationStatus.FAILED
        self.error_message = error
        self.updated_at = datetime.utcnow()

    def can_resume(self) -> bool:
        """Check if workflow can be resumed from checkpoint."""
        return (
            self.last_checkpoint is not None
            and self.status != GenerationStatus.COMPLETED
            and self.retry_count < 3
        )

    def get_next_step(self) -> WorkflowStep | None:
        """Determine the next workflow step to execute."""
        if self.status == GenerationStatus.COMPLETED:
            return None

        # If animation is requested and detail is complete
        if (
            self.request.animation is not None
            and WorkflowStep.DETAIL in self.completed_steps
            and WorkflowStep.ANIMATION not in self.completed_steps
        ):
            return WorkflowStep.ANIMATION

        # Standard flow
        if WorkflowStep.DESIGN not in self.completed_steps:
            return WorkflowStep.DESIGN
        if WorkflowStep.PALETTE not in self.completed_steps:
            return WorkflowStep.PALETTE
        if WorkflowStep.DETAIL not in self.completed_steps:
            return WorkflowStep.DETAIL

        # All steps complete
        return WorkflowStep.COMPLETE

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
                "session_id": "user-123-session-456",
                "status": "in_progress",
                "current_step": "palette",
                "completed_steps": ["design"],
            }
        }


class StateSnapshot(BaseModel):
    """
    Lightweight snapshot of workflow state for listing/querying.
    """

    workflow_id: UUID
    session_id: str
    status: GenerationStatus
    current_step: WorkflowStep
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_workflow_state(cls, state: WorkflowState) -> "StateSnapshot":
        """Create snapshot from full workflow state."""
        return cls(
            workflow_id=state.workflow_id,
            session_id=state.session_id,
            status=state.status,
            current_step=state.current_step,
            created_at=state.created_at,
            updated_at=state.updated_at,
        )