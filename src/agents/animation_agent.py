"""
Animation Agent for Vision pixel art generation system.

This agent generates animation frames based on base sprite data and
animation configuration, ensuring smooth transitions and consistency.

Supports delta encoding for efficient multi-frame animations (70-80% compression).
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
from src.agents.detail_schemas import (
    AnimationAgentOutputDelta,
)
from src.agents.prompts import (
    ANIMATION_AGENT_SYSTEM,
    ANIMATION_OUTPUT_SCHEMA,
    format_animation_prompt,
)
from src.rendering.delta_encoder import (
    decode_delta_animation,
    analyze_animation_deltas,
    calculate_delta_compression_ratio,
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
    
    Supports delta encoding for animations with ≥2 frames, achieving 70-80%
    compression for typical animations where frames share many common pixels.

    Type Parameters:
        InputT: AgentContext - Processing context with sprite request, detail spec, and animation config
        OutputT: dict[str, Any] - Animation frame specifications and metadata

    Attributes:
        llm_client: LLM client for AI-powered animation generation
        model_name: Claude model to use for animation frame generation

    Example:
        >>> agent = AnimationAgent(llm_client=client, model_name="claude-sonnet-4-5")
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
        model_name: str = "claude-sonnet-4-5",
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
                name="delta_encoding",
                description="Compress animations using delta encoding (70-80% reduction)",
                required_inputs=["animation_frames"],
                provided_outputs=["delta_compressed_animation"],
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
            description="Generates animation frames with smooth transitions, sprite consistency, and delta encoding compression",
            version="2.0.0",  # Updated for delta encoding support
            capabilities=capabilities,
        )

        super().__init__(metadata=metadata)

        self.llm_client = llm_client
        self.model_name = model_name

        logger.info(f"Initialized {self.name} with model {model_name} (delta encoding enabled)")

    async def process(self, context: AgentContext) -> dict[str, Any]:
        """
        Process base sprite and animation config to generate animation frames.

        This method uses the LLM to create frame specifications that maintain
        sprite consistency while providing smooth, natural motion. Automatically
        uses delta encoding for animations with 2+ frames.

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
            
            # Determine if delta encoding should be used
            frame_count = anim_config.frame_count
            use_delta = frame_count >= 2  # Always use delta for 2+ frames
            
            # Format the user prompt
            user_prompt = format_animation_prompt(
                request_description=context.request.description,
                detail_spec=detail_spec,
                animation_config=anim_config,
                dimensions=f"{context.request.dimensions.width}x{context.request.dimensions.height}",
            )

            logger.debug(f"User prompt: {user_prompt[:200]}...")
            
            # Select appropriate system prompt and output format
            if use_delta:
                logger.info(
                    f"Using delta encoding for {frame_count}-frame animation "
                    f"({context.request.dimensions.width}x{context.request.dimensions.height})"
                )
                output_format = AnimationAgentOutputDelta
                system_prompt = self._get_delta_system_prompt()
            else:
                logger.info("Using standard animation format (single frame)")
                output_format = None  # Use standard JSON parsing
                system_prompt = ANIMATION_AGENT_SYSTEM

            # Call LLM with system prompt
            if use_delta:
                response = await self.llm_client.create_message(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "user",
                            "content": user_prompt,
                        }
                    ],
                    max_tokens=8192,
                    temperature=0.7,
                    system=system_prompt,
                    response_format=output_format,
                )
            else:
                response = await self.llm_client.create_message(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "user",
                            "content": user_prompt,
                        }
                    ],
                    max_tokens=8192,
                    temperature=0.7,
                    system=system_prompt,
                )

            # Extract and parse response
            response_text = response.content[0].text  # type: ignore
            logger.debug(f"LLM response: {response_text[:200]}...")

            # Parse response based on format
            if use_delta:
                # Parse structured delta output
                try:
                    parsed_output = output_format.model_validate_json(response_text)
                except Exception as parse_error:
                    logger.error(f"Failed to parse delta animation output: {parse_error}")
                    raise ProcessingError(
                        agent_role=self.role,
                        message=f"Failed to parse delta animation output: {parse_error}",
                        context={"response_text": response_text[:500]},
                    )
                
                # Convert Pydantic model to dict
                animation_spec = parsed_output.model_dump()
                
                # Decode delta animation to standard frames
                animation_data = animation_spec.get("animation", {})
                if animation_data.get("encoding") == "delta":
                    logger.info("Decoding delta-encoded animation to standard frames")
                    
                    try:
                        # Decode frames
                        frames = decode_delta_animation(
                            animation_data["width"],
                            animation_data["height"],
                            animation_data["keyframe"],
                            animation_data["deltas"]
                        )
                        
                        # Calculate compression metrics
                        deltas = animation_data["deltas"]
                        total_changes = sum(
                            len(delta.get("changes", [])) 
                            for delta in deltas 
                            if not delta.get("is_keyframe", False)
                        )
                        keyframe_count = 1 + sum(
                            1 for delta in deltas 
                            if delta.get("is_keyframe", False)
                        )
                        
                        compression_metrics = calculate_delta_compression_ratio(
                            frame_count=animation_data["frame_count"],
                            width=animation_data["width"],
                            height=animation_data["height"],
                            total_changes=total_changes,
                            keyframe_count=keyframe_count
                        )
                        
                        # Replace with decoded frames
                        animation_spec["frames"] = frames
                        animation_spec["frame_count"] = len(frames)
                        animation_spec["is_animated"] = True
                        
                        # Add delta metadata
                        animation_spec["_delta_metadata"] = {
                            "was_delta_encoded": True,
                            "keyframe_count": keyframe_count,
                            "total_changes": total_changes,
                            "compression_percent": compression_metrics["compression_percent"],
                            "avg_changes_per_frame": compression_metrics["avg_changes_per_frame"],
                        }
                        
                        logger.info(
                            f"Delta decoding successful: {len(frames)} frames decoded "
                            f"({compression_metrics['compression_percent']}% compression, "
                            f"{compression_metrics['avg_changes_per_frame']} avg changes/frame)"
                        )
                        
                    except Exception as decode_error:
                        logger.error(f"Delta decoding failed: {decode_error}")
                        raise ProcessingError(
                            agent_role=self.role,
                            message=f"Failed to decode delta animation: {decode_error}",
                            context={
                                "frame_count": animation_data.get("frame_count"),
                                "delta_count": len(animation_data.get("deltas", []))
                            },
                        )
            else:
                # Parse standard JSON
                animation_spec = self._extract_json(response_text)

            # Add metadata
            animation_spec["_metadata"] = {
                "agent": self.role.value,
                "model": self.model_name,
                "request_id": str(context.request.request_id),
                "frame_count": anim_config.frame_count,
                "frame_duration": anim_config.frame_duration,
                "loop": anim_config.loop,
                "encoding_used": "delta" if use_delta else "standard",
            }

            logger.info(
                f"Animation generated successfully: {len(animation_spec.get('frames', []))} frames"
            )
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
        required_keys = ["frames", "frame_count"]
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

        # Check for delta metadata if delta was used
        if "_delta_metadata" in output:
            delta_meta = output["_delta_metadata"]
            if delta_meta.get("compression_percent", 0) < 30:
                warnings.append(
                    f"Low delta compression ({delta_meta['compression_percent']}%) - "
                    f"frames may have too many differences"
                )

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def _get_delta_system_prompt(self) -> str:
        """
        Get the system prompt for delta-encoded animation output.
        
        Returns:
            str: System prompt that instructs the LLM to use delta encoding
        """
        return """You are an animation generation agent using DELTA ENCODING for maximum compression efficiency.

CRITICAL OUTPUT FORMAT - DELTA ENCODING:
Instead of storing complete frames, store only pixel DIFFERENCES (deltas) between frames.

Delta Encoding Structure:
1. Keyframe: Store first frame completely as 2D grid of hex colors
2. Deltas: For each subsequent frame, store only changed pixels

Format:
{
  "animation": {
    "width": 16,
    "height": 16,
    "frame_count": 4,
    "encoding": "delta",
    "keyframe": [["#FF0000", ...], ...],  // Full first frame
    "deltas": [
      {
        "frame_index": 1,
        "is_keyframe": false,
        "changes": [
          {"x": 5, "y": 3, "color": "#00FF00"},
          {"x": 6, "y": 3, "color": "#00FF00"}
        ]
      },
      ...
    ]
  },
  "animation_specs": {
    "motion_type": "walk_cycle",
    "fps": 12
  }
}

Delta Change Format:
- x: X coordinate (0-based)
- y: Y coordinate (0-based)  
- color: New hex color (#RRGGBB) or "transparent"

IMPORTANT Rules:
1. Keyframe must be complete 2D grid (width × height)
2. Changes list only pixels that differ from previous frame
3. If >50% pixels change, set is_keyframe=true and include full frame_data
4. frame_index starts at 1 (frame 0 is the keyframe)
5. Changes flow sequentially - each frame builds on previous

Benefits of Delta Encoding:
- 70-80% compression for typical animations
- Perfect for walk cycles, idle animations (small changes per frame)
- Lossless - can perfectly reconstruct all frames
- Ideal when consecutive frames share many pixels

Animation Guidelines:
- Smooth transitions between frames
- Maintain sprite consistency
- Apply motion principles (squash/stretch, anticipation)
- Ensure readability at small size

You will receive base sprite data and animation configuration. Generate smooth animation using delta encoding for maximum efficiency."""

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
        return f"AnimationAgent(model={self.model_name}, role={self.role.value}, delta_encoding=True)"