"""
Animation Agent for Vision pixel art generation system.

This agent generates animation frames based on base sprite data and
animation configuration, ensuring smooth transitions and consistency.
"""

import json
import logging
from typing import Any

from src.agents.base import (
    AgentCapability,
    AgentMetadata,
    BaseAgent,
    ProcessingError,
    ValidationError,
)
from src.agents.prompts import (
    ANIMATION_AGENT_SYSTEM,
    ANIMATION_OUTPUT_SCHEMA,
    format_animation_prompt,
)
from src.core.models import (
    AgentContext,
    AgentRole,
    AnimationConfig,
    ValidationResult,
)
from src.llm.client import LLMClient

logger = logging.getLogger(__name__)


class AnimationAgent(BaseAgent[AgentContext, dict[str, Any]]):
    """
    Animation Agent specialized in generating animation frames for sprites.

    This agent takes base sprite data and animation configuration to create
    smooth animation sequences (walk cycles, idle animations, etc.) while
    maintaining sprite consistency across frames.

    Type Parameters:
        InputT: AgentContext - Processing context with sprite request, detail spec, and animation config
        OutputT: dict[str, Any] - Animation frame specifications and metadata

    Attributes:
        llm_client: LLM client for AI-powered animation generation
        model_name: Claude model to use for animation frame generation

    Example:
        >>> agent = AnimationAgent(llm_client=client, model_name="claude-3-5-sonnet-20241022")
        >>> context = AgentContext(
        ...     request=sprite_request,
        ...     current_step="animation",
        ...     previous_results={"detail": detail_spec}
        ... )
        >>> animation_spec = await agent.process(context)
        >>> print(animation_spec["frames"])
    """

    def __init__(
        self,
        llm_client: LLMClient,
        model_name: str = "claude-3-5-sonnet-20241022",
    ) -> None:
        """
        Initialize the Animation Agent.

        Args:
            llm_client: Configured LLM client for API calls
            model_name: Claude model identifier to use
        """
        # Define agent capabilities
        capabilities = [
            AgentCapability(
                name="frame_generation",
                description="Generate animation frames with smooth transitions",
                required_inputs=["base_sprite", "animation_config"],
                provided_outputs=["animation_frames", "frame_metadata"],
            ),
            AgentCapability(
                name="motion_design",
                description="Apply motion principles for natural animation",
                required_inputs=["animation_type", "frame_count"],
                provided_outputs=["motion_curves", "timing_data"],
            ),
            AgentCapability(
                name="consistency_maintenance",
                description="Ensure sprite consistency across animation frames",
                required_inputs=["base_sprite", "design_spec"],
                provided_outputs=["consistency_report", "validated_frames"],
            ),
        ]

        # Create metadata
        metadata = AgentMetadata(
            name="Animation Agent",
            role=AgentRole.ANIMATION,
            description="Generates animation frames with smooth transitions and sprite consistency",
            version="1.0.0",
            capabilities=capabilities,
        )

        super().__init__(metadata=metadata)

        self.llm_client = llm_client
        self.model_name = model_name

        logger.info(f"Initialized {self.name} with model {model_name}")

    async def process(self, context: AgentContext) -> dict[str, Any]:
        """
        Process base sprite and animation config to generate animation frames.

        This method uses the LLM to create frame specifications that maintain
        sprite consistency while providing smooth, natural motion.

        Args:
            context: Processing context containing sprite request, detail spec, and animation config

        Returns:
            dict[str, Any]: Animation frame specifications with timing and metadata

        Raises:
            ProcessingError: If animation generation fails
            ValidationError: If output validation fails
        """
        try:
            logger.info(f"Processing animation for request: {context.request.request_id}")

            # Check if animation is requested
            if not context.request.animation:
                logger.info("No animation requested, returning empty animation spec")
                return {
                    "frames": [],
                    "frame_count": 1,
                    "is_animated": False,
                    "message": "No animation configuration provided",
                    "_metadata": {
                        "agent": self.role.value,
                        "request_id": str(context.request.request_id),
                    },
                }

            # Extract required data from previous results
            detail_spec = context.previous_results.get("detail") or context.previous_results.get("detail_specification")

            if not detail_spec:
                raise ProcessingError(
                    agent_role=self.role,
                    message="Detail specification not found in previous results",
                    context={"available_keys": list(context.previous_results.keys())},
                )

            # Get animation configuration
            anim_config = context.request.animation

            # Format the user prompt
            user_prompt = format_animation_prompt(
                request_description=context.request.description,
                detail_spec=detail_spec,
                animation_config=anim_config,
                dimensions=f"{context.request.dimensions.width}x{context.request.dimensions.height}",
            )

            logger.debug(f"User prompt: {user_prompt[:200]}...")

            # Call LLM with system prompt
            response = await self.llm_client.create_message(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
                max_tokens=8192,  # Large for multiple frame specifications
                temperature=0.7,  # Creative but consistent
                system=ANIMATION_AGENT_SYSTEM,
            )

            # Extract and parse response
            response_text = response.content[0].text  # type: ignore
            logger.debug(f"LLM response: {response_text[:200]}...")

            # Parse JSON from response
            animation_spec = self._extract_json(response_text)

            # Add metadata
            animation_spec["_metadata"] = {
                "agent": self.role.value,
                "model": self.model_name,
                "request_id": str(context.request.request_id),
                "frame_count": anim_config.frame_count,
                "frame_duration": anim_config.frame_duration,
                "loop": anim_config.loop,
            }

            logger.info(f"Animation specification generated successfully with {len(animation_spec.get('frames', []))} frames")
            return animation_spec

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            raise ProcessingError(
                agent_role=self.role,
                message=f"Invalid JSON in animation response: {e}",
                context={"response_text": response_text[:500] if "response_text" in locals() else None},
            )
        except Exception as e:
            logger.error(f"Animation processing failed: {e}")
            raise ProcessingError(
                agent_role=self.role,
                message=f"Animation generation failed: {e}",
                context={"error_type": type(e).__name__},
            )

    def validate_input(self, context: AgentContext) -> ValidationResult:
        """
        Validate input context before processing.

        Checks that animation configuration and base sprite data are available.

        Args:
            context: Processing context to validate

        Returns:
            ValidationResult: Validation outcome with errors/warnings
        """
        errors: list[str] = []
        warnings: list[str] = []
        suggestions: list[str] = []

        # Check required fields
        if not context.request:
            errors.append("Missing sprite request in context")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Animation is optional - if not provided, validation still passes
        if not context.request.animation:
            logger.debug("No animation requested, skipping animation-specific validation")
            return ValidationResult(
                is_valid=True,
                errors=errors,
                warnings=["No animation configuration provided"],
                suggestions=["Consider adding AnimationConfig for animated sprites"],
            )

        anim_config = context.request.animation

        # Validate animation config
        if anim_config.frame_count < 2:
            errors.append("Animation requires at least 2 frames")
        elif anim_config.frame_count > 32:
            warnings.append(f"High frame count ({anim_config.frame_count}) may be complex to generate")

        if anim_config.frame_duration < 50:
            warnings.append("Very short frame duration may appear too fast")
        elif anim_config.frame_duration > 1000:
            warnings.append("Long frame duration may appear sluggish")

        # Check for detail specification
        detail_spec = context.previous_results.get("detail") or context.previous_results.get("detail_specification")
        if not detail_spec:
            errors.append("Detail specification not found in previous results - required for animation")
        elif not isinstance(detail_spec, dict):
            errors.append("Detail specification must be a dictionary")

        # Validate dimensions for animation
        request = context.request
        if request.asset_type.value == "character":
            if request.dimensions.height < 16:
                warnings.append("Character animations typically need at least 16 pixels height")
            if anim_config.frame_count < 4:
                suggestions.append("Character animations work best with at least 4 frames (walk cycle)")

        # Check style
        if request.style.value != "stardew_valley":
            warnings.append(f"Animation agent optimized for Stardew Valley style, may need adjustments for {request.style.value}")

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def validate_output(self, output: dict[str, Any]) -> ValidationResult:
        """
        Validate animation specification output.

        Ensures the animation frames contain all required data
        and are consistent with the configuration.

        Args:
            output: Animation specification to validate

        Returns:
            ValidationResult: Validation outcome with errors/warnings
        """
        errors: list[str] = []
        warnings: list[str] = []
        suggestions: list[str] = []

        # Check for non-animated output (valid case)
        if not output.get("is_animated", True):
            logger.debug("Output is for non-animated sprite")
            return ValidationResult(
                is_valid=True,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
            )

        # Check required top-level keys
        required_keys = ["frames", "frame_count", "timing"]
        for key in required_keys:
            if key not in output:
                errors.append(f"Missing required field: {key}")

        if errors:
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Validate frames
        frames = output.get("frames", [])
        frame_count = output.get("frame_count", 0)

        if not frames:
            errors.append("Animation specification has no frames")
        elif len(frames) != frame_count:
            errors.append(f"Frame count mismatch: declared {frame_count}, got {len(frames)} frames")

        if frame_count < 2:
            warnings.append("Animation should have at least 2 frames")

        # Validate each frame structure
        for i, frame in enumerate(frames):
            if not isinstance(frame, dict):
                errors.append(f"Frame {i} is not a dictionary")
                continue

            if "frame_number" not in frame:
                warnings.append(f"Frame {i} missing frame_number")
            if "changes" not in frame and "pixel_data" not in frame:
                warnings.append(f"Frame {i} missing both changes and pixel_data")

        # Validate timing
        timing = output.get("timing", {})
        if not timing.get("frame_duration"):
            warnings.append("No frame_duration specified in timing")
        if not timing.get("total_duration"):
            suggestions.append("Consider adding total_duration to timing")

        # Validate motion principles
        if "motion_principles" in output:
            motion = output["motion_principles"]
            if not motion:
                suggestions.append("Motion principles are empty, consider adding guidance")

        # Check for consistency notes
        if "consistency_notes" not in output:
            suggestions.append("Consider adding consistency_notes for frame-to-frame consistency")

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def _extract_json(self, text: str) -> dict[str, Any]:
        """
        Extract JSON from LLM response text.

        Handles both raw JSON and JSON wrapped in markdown code blocks.

        Args:
            text: Response text from LLM

        Returns:
            dict[str, Any]: Parsed JSON object

        Raises:
            json.JSONDecodeError: If JSON cannot be parsed
        """
        # Try to find JSON in markdown code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end != -1:
                text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                text = text[start:end].strip()

        # Remove any leading/trailing whitespace
        text = text.strip()

        # Parse JSON
        return json.loads(text)

    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"AnimationAgent(model={self.model_name}, role={self.role.value})"