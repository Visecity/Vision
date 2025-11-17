"""
Orchestrator Agent for Vision pixel art generation system.

This agent coordinates all specialized agents in the proper sequence,
managing the complete workflow from design to final generation.
"""

import logging
from datetime import datetime
from typing import Any

from src.agents.base import (
    AgentCapability,
    AgentMetadata,
    BaseAgent,
    ProcessingError,
    ValidationError,
)
from src.core.models import (
    AgentContext,
    AgentMessage,
    AgentRole,
    ColorPalette,
    GenerationResult,
    GenerationStatus,
    MessageType,
    SpriteMetadata,
    SpriteRequest,
    ValidationResult,
)

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent[SpriteRequest, GenerationResult]):
    """
    Orchestrator Agent specialized in coordinating the complete generation workflow.

    This agent manages the execution sequence of all specialized agents
    (Design, Palette, Detail, Animation), handles inter-agent communication,
    aggregates results, and performs final quality checks.

    Type Parameters:
        InputT: SpriteRequest - User's sprite generation request
        OutputT: GenerationResult - Complete generation result with all metadata

    Attributes:
        workflow_steps: Ordered list of workflow steps to execute
        required_agents: Set of required agent roles for complete workflow

    Example:
        >>> agent = OrchestratorAgent()
        >>> context = AgentContext(
        ...     request=sprite_request,
        ...     current_step="orchestration",
        ...     previous_results={}
        ... )
        >>> result = await agent.process(sprite_request)
        >>> print(result.status)
    """

    def __init__(self) -> None:
        """
        Initialize the Orchestrator Agent.

        The orchestrator doesn't need an LLM client since it manages
        workflow logic rather than generating content.
        """
        # Define agent capabilities
        capabilities = [
            AgentCapability(
                name="workflow_coordination",
                description="Coordinate execution sequence of all specialized agents",
                required_inputs=["sprite_request"],
                provided_outputs=["generation_result", "workflow_log"],
            ),
            AgentCapability(
                name="agent_communication",
                description="Manage inter-agent message passing and context",
                required_inputs=["agent_outputs"],
                provided_outputs=["aggregated_results", "message_log"],
            ),
            AgentCapability(
                name="quality_validation",
                description="Perform final quality checks on generated assets",
                required_inputs=["all_agent_results"],
                provided_outputs=["validation_report", "quality_score"],
            ),
        ]

        # Create metadata
        metadata = AgentMetadata(
            name="Orchestrator Agent",
            role=AgentRole.ORCHESTRATOR,
            description="Coordinates all specialized agents and manages complete generation workflow",
            version="1.0.0",
            capabilities=capabilities,
        )

        super().__init__(metadata=metadata)

        # Define workflow steps (in execution order)
        self.workflow_steps = ["design", "palette", "detail", "animation"]
        self.required_agents = {AgentRole.DESIGN, AgentRole.PALETTE, AgentRole.DETAIL}
        # Animation is optional

        logger.info(f"Initialized {self.name}")

    async def process(self, request: SpriteRequest) -> GenerationResult:
        """
        Process sprite request and coordinate complete generation workflow.

        This method defines the workflow sequence and validates that all
        required steps are properly defined. In Phase 4 (LangGraph integration),
        this will orchestrate actual agent execution.

        Args:
            request: User's sprite generation request

        Returns:
            GenerationResult: Complete generation result with all metadata

        Raises:
            ProcessingError: If workflow coordination fails
            ValidationError: If validation fails
        """
        try:
            logger.info(f"Orchestrating generation for request: {request.request_id}")
            start_time = datetime.utcnow()

            # Initialize message log
            messages: list[AgentMessage] = []

            # Create initial orchestrator message
            init_message = self.create_message(
                to_agent=None,  # Broadcast
                message_type=MessageType.STATUS,
                content={
                    "status": "workflow_started",
                    "workflow_steps": self.workflow_steps,
                    "request_id": str(request.request_id),
                },
                context={"timestamp": datetime.utcnow().isoformat()},
            )
            messages.append(init_message)

            # Define workflow sequence
            workflow = self._define_workflow(request)

            # Validate workflow definition
            workflow_validation = self._validate_workflow(workflow, request)
            if not workflow_validation.is_valid:
                raise ValidationError(
                    validation_result=workflow_validation,
                    message="Workflow validation failed",
                )

            # Log workflow definition
            workflow_message = self.create_message(
                to_agent=None,
                message_type=MessageType.STATUS,
                content={
                    "status": "workflow_defined",
                    "steps": [step["agent"] for step in workflow["steps"]],
                    "total_steps": len(workflow["steps"]),
                },
            )
            messages.append(workflow_message)

            # NOTE: In Phase 4 with LangGraph, this is where we would:
            # 1. Execute each agent in sequence
            # 2. Pass results between agents via context
            # 3. Handle errors and retries
            # 4. Collect all agent outputs
            #
            # For now, we return a workflow definition result
            logger.info(f"Workflow defined with {len(workflow['steps'])} steps")

            # Create completion message
            completion_message = self.create_message(
                to_agent=None,
                message_type=MessageType.STATUS,
                content={
                    "status": "workflow_ready",
                    "message": "Workflow defined and validated successfully",
                    "next_phase": "LangGraph execution",
                },
            )
            messages.append(completion_message)

            # Create generation result
            result = GenerationResult(
                request_id=request.request_id,
                status=GenerationStatus.PENDING,
                metadata=None,  # Will be populated after actual execution in Phase 4
                manifest_json=workflow,  # Store workflow definition
                error_message=None,
                agent_messages=messages,
                warnings=workflow_validation.warnings,
                completed_at=datetime.utcnow(),
            )

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"Workflow orchestration completed in {duration:.2f}s")

            return result

        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            
            # Create error result
            error_message = self.create_message(
                to_agent=None,
                message_type=MessageType.ERROR,
                content={
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

            return GenerationResult(
                request_id=request.request_id,
                status=GenerationStatus.FAILED,
                metadata=None,
                manifest_json=None,
                error_message=f"Orchestration failed: {e}",
                agent_messages=[error_message],
                warnings=[],
                completed_at=datetime.utcnow(),
            )

    def validate_input(self, request: SpriteRequest) -> ValidationResult:
        """
        Validate sprite request before orchestration.

        Checks that the request contains all necessary information
        for the complete workflow.

        Args:
            request: Sprite request to validate

        Returns:
            ValidationResult: Validation outcome with errors/warnings
        """
        errors: list[str] = []
        warnings: list[str] = []
        suggestions: list[str] = []

        # Validate description
        if not request.description or len(request.description.strip()) < 10:
            errors.append("Sprite description is too short (minimum 10 characters)")
        elif len(request.description) > 2000:
            warnings.append("Very long description may slow down processing")

        # Validate dimensions
        if request.dimensions.width < 8 or request.dimensions.height < 8:
            errors.append("Dimensions too small for meaningful generation (minimum 8x8)")
        elif request.dimensions.width > 64 or request.dimensions.height > 64:
            warnings.append("Large dimensions will require more processing time")

        # Check animation configuration
        if request.animation:
            if request.animation.frame_count < 2:
                errors.append("Animation requires at least 2 frames")
            elif request.animation.frame_count > 32:
                warnings.append("High frame count may significantly increase generation time")
            
            if request.asset_type.value != "character" and request.animation.frame_count > 8:
                suggestions.append("Non-character animations typically use fewer frames (4-8)")

        # Check custom palette
        if request.palette:
            if len(request.palette.colors) < 3:
                warnings.append("Custom palette has very few colors, may limit detail options")
            elif len(request.palette.colors) > 52:
                warnings.append("Custom palette exceeds Stardew Valley limit of 52 colors")

        # Check reference images
        if request.reference_images and len(request.reference_images) > 5:
            warnings.append("Maximum 5 reference images supported")

        # Suggestions
        if not request.reference_images:
            suggestions.append("Consider providing reference images for more accurate results")

        if request.style.value != "stardew_valley":
            suggestions.append("System is optimized for Stardew Valley style")

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def validate_output(self, output: GenerationResult) -> ValidationResult:
        """
        Validate generation result output.

        Ensures the result contains all required data and is consistent
        with the generation status.

        Args:
            output: Generation result to validate

        Returns:
            ValidationResult: Validation outcome with errors/warnings
        """
        errors: list[str] = []
        warnings: list[str] = []
        suggestions: list[str] = []

        # Check status consistency
        if output.status == GenerationStatus.COMPLETED:
            if not output.metadata:
                errors.append("Completed status requires metadata")
            if not output.manifest_json:
                warnings.append("Completed result should include manifest JSON")
        elif output.status == GenerationStatus.FAILED:
            if not output.error_message:
                errors.append("Failed status requires error_message")
        elif output.status == GenerationStatus.PENDING:
            if output.metadata:
                warnings.append("Pending status should not have metadata yet")

        # Check agent messages
        if not output.agent_messages:
            warnings.append("No agent messages logged during generation")
        else:
            # Check for key workflow messages
            message_types = {msg.message_type for msg in output.agent_messages}
            if MessageType.ERROR in message_types and output.status == GenerationStatus.COMPLETED:
                warnings.append("Generation completed despite error messages")

        # Check warnings
        if output.warnings:
            logger.debug(f"Generation completed with {len(output.warnings)} warnings")

        # Validate metadata if present
        if output.metadata:
            if output.metadata.frame_count < 1:
                errors.append("Invalid frame count in metadata")
            if output.metadata.generation_time_seconds < 0:
                errors.append("Invalid generation time in metadata")

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def _define_workflow(self, request: SpriteRequest) -> dict[str, Any]:
        """
        Define the workflow sequence based on the request.

        Args:
            request: Sprite generation request

        Returns:
            dict: Workflow definition with steps and dependencies
        """
        steps = []

        # Step 1: Design Agent
        steps.append({
            "step_number": 1,
            "agent": AgentRole.DESIGN.value,
            "description": "Analyze request and create design specification",
            "inputs": ["sprite_request"],
            "outputs": ["design_specification"],
            "required": True,
        })

        # Step 2: Palette Agent
        steps.append({
            "step_number": 2,
            "agent": AgentRole.PALETTE.value,
            "description": "Generate harmonious color palette",
            "inputs": ["sprite_request", "design_specification"],
            "outputs": ["color_palette"],
            "required": True,
            "skip_if": request.palette is not None,  # Skip if custom palette provided
        })

        # Step 3: Detail Agent
        steps.append({
            "step_number": 3,
            "agent": AgentRole.DETAIL.value,
            "description": "Implement pixel-level details with shading",
            "inputs": ["sprite_request", "design_specification", "color_palette"],
            "outputs": ["pixel_grid", "shading_details"],
            "required": True,
        })

        # Step 4: Animation Agent (optional)
        if request.animation:
            steps.append({
                "step_number": 4,
                "agent": AgentRole.ANIMATION.value,
                "description": "Generate animation frames",
                "inputs": ["sprite_request", "detail_specification", "animation_config"],
                "outputs": ["animation_frames"],
                "required": False,
            })

        return {
            "workflow_version": "1.0.0",
            "request_id": str(request.request_id),
            "total_steps": len(steps),
            "steps": steps,
            "dependencies": self._build_dependency_graph(steps),
        }

    def _build_dependency_graph(self, steps: list[dict[str, Any]]) -> dict[str, list[str]]:
        """
        Build dependency graph showing which steps depend on which outputs.

        Args:
            steps: List of workflow steps

        Returns:
            dict: Dependency graph mapping step to required predecessors
        """
        dependencies = {}
        
        for step in steps:
            agent = step["agent"]
            required_inputs = step["inputs"]
            
            # Find which previous steps provide these inputs
            predecessors = []
            for prev_step in steps:
                if prev_step["step_number"] >= step["step_number"]:
                    break
                if any(output in required_inputs for output in prev_step["outputs"]):
                    predecessors.append(prev_step["agent"])
            
            dependencies[agent] = predecessors

        return dependencies

    def _validate_workflow(self, workflow: dict[str, Any], request: SpriteRequest) -> ValidationResult:
        """
        Validate that the workflow definition is complete and consistent.

        Args:
            workflow: Workflow definition to validate
            request: Original sprite request

        Returns:
            ValidationResult: Validation outcome
        """
        errors: list[str] = []
        warnings: list[str] = []
        suggestions: list[str] = []

        # Check required fields
        if not workflow.get("steps"):
            errors.append("Workflow has no steps defined")
            return ValidationResult(is_valid=False, errors=errors)

        steps = workflow["steps"]

        # Check minimum required steps
        required_agents = {AgentRole.DESIGN.value, AgentRole.PALETTE.value, AgentRole.DETAIL.value}
        defined_agents = {step["agent"] for step in steps if step.get("required", True)}
        
        missing_agents = required_agents - defined_agents
        if missing_agents:
            errors.append(f"Missing required agents in workflow: {', '.join(missing_agents)}")

        # Check step numbering
        step_numbers = [step["step_number"] for step in steps]
        if step_numbers != list(range(1, len(steps) + 1)):
            errors.append("Workflow steps are not properly numbered sequentially")

        # Validate dependencies
        dependencies = workflow.get("dependencies", {})
        for agent, deps in dependencies.items():
            for dep in deps:
                if not any(step["agent"] == dep for step in steps):
                    errors.append(f"Dependency {dep} for {agent} not found in workflow")

        # Check animation step if requested
        if request.animation:
            has_animation_step = any(
                step["agent"] == AgentRole.ANIMATION.value for step in steps
            )
            if not has_animation_step:
                warnings.append("Animation requested but no animation step in workflow")

        # Check for custom palette
        if request.palette:
            palette_step = next(
                (step for step in steps if step["agent"] == AgentRole.PALETTE.value),
                None
            )
            if palette_step and not palette_step.get("skip_if"):
                suggestions.append("Custom palette provided but palette step not marked for skipping")

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"OrchestratorAgent(role={self.role.value}, workflow_steps={len(self.workflow_steps)})"