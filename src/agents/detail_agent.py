"""
Detail Agent for Vision pixel art generation system.

This agent implements design specifications at the pixel level, applying
color palettes with proper shading, highlights, and texture details.
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
    DETAIL_AGENT_SYSTEM,
    DETAIL_OUTPUT_SCHEMA,
    format_detail_prompt,
)
from src.core.models import (
    AgentContext,
    AgentRole,
    ColorPalette,
    ValidationResult,
)
from src.llm.client import LLMClient

logger = logging.getLogger(__name__)


class DetailAgent(BaseAgent[AgentContext, dict[str, Any]]):
    """
    Detail Agent specialized in pixel-level sprite implementation.

    This agent takes design specifications and color palettes and creates
    the actual pixel-by-pixel implementation with proper shading, highlights,
    and texture details optimized for Stardew Valley style.

    Type Parameters:
        InputT: AgentContext - Processing context with sprite request, design, and palette
        OutputT: dict[str, Any] - Pixel grid data with shading and final specifications

    Attributes:
        llm_client: LLM client for AI-powered detail generation
        model_name: Claude model to use for detail implementation

    Example:
        >>> agent = DetailAgent(llm_client=client, model_name="claude-3-5-sonnet-20241022")
        >>> context = AgentContext(
        ...     request=sprite_request,
        ...     current_step="detail",
        ...     previous_results={"design": design_spec, "palette": color_palette}
        ... )
        >>> detail_spec = await agent.process(context)
        >>> print(detail_spec["pixel_grid"])
    """

    def __init__(
        self,
        llm_client: LLMClient,
        model_name: str = "claude-3-5-sonnet-20241022",
    ) -> None:
        """
        Initialize the Detail Agent.

        Args:
            llm_client: Configured LLM client for API calls
            model_name: Claude model identifier to use
        """
        # Define agent capabilities
        capabilities = [
            AgentCapability(
                name="pixel_implementation",
                description="Implement design specifications at pixel level",
                required_inputs=["design_specification", "color_palette", "sprite_request"],
                provided_outputs=["pixel_grid", "shading_map"],
            ),
            AgentCapability(
                name="shading_application",
                description="Apply proper shading and highlights using palette colors",
                required_inputs=["color_palette", "design_spec"],
                provided_outputs=["shaded_sprite", "highlight_map"],
            ),
            AgentCapability(
                name="texture_detail",
                description="Add texture and fine details within pixel constraints",
                required_inputs=["design_spec", "dimensions"],
                provided_outputs=["detailed_sprite", "texture_notes"],
            ),
        ]

        # Create metadata
        metadata = AgentMetadata(
            name="Detail Agent",
            role=AgentRole.DETAIL,
            description="Implements design specifications at pixel level with shading and details",
            version="1.0.0",
            capabilities=capabilities,
        )

        super().__init__(metadata=metadata)

        self.llm_client = llm_client
        self.model_name = model_name

        logger.info(f"Initialized {self.name} with model {model_name}")

    async def process(self, context: AgentContext) -> dict[str, Any]:
        """
        Process design and palette to generate pixel-level implementation.

        This method uses the LLM to create detailed pixel placement,
        shading, and texture specifications based on the design blueprint
        and selected color palette.

        Args:
            context: Processing context containing sprite request, design, and palette

        Returns:
            dict[str, Any]: Pixel grid data with shading details and final specifications

        Raises:
            ProcessingError: If detail generation fails
            ValidationError: If output validation fails
        """
        try:
            logger.info(f"Processing details for request: {context.request.request_id}")

            # Extract required data from previous results
            design_spec = context.previous_results.get("design") or context.previous_results.get("design_specification")
            palette_data = context.previous_results.get("palette") or context.previous_results.get("color_palette")

            if not design_spec:
                raise ProcessingError(
                    agent_role=self.role,
                    message="Design specification not found in previous results",
                    context={"available_keys": list(context.previous_results.keys())},
                )

            if not palette_data:
                raise ProcessingError(
                    agent_role=self.role,
                    message="Color palette not found in previous results",
                    context={"available_keys": list(context.previous_results.keys())},
                )

            # Convert palette if it's a ColorPalette object
            if isinstance(palette_data, ColorPalette):
                palette_colors = palette_data.colors
            else:
                palette_colors = palette_data.get("colors", [])

            # Format the user prompt
            user_prompt = format_detail_prompt(
                request_description=context.request.description,
                design_spec=design_spec,
                palette_colors=palette_colors,
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
                max_tokens=8192,  # Larger for detailed pixel grids
                temperature=0.6,  # Moderate creativity but more precision
                system=DETAIL_AGENT_SYSTEM,
            )

            # Extract and parse response
            response_text = response.content[0].text  # type: ignore
            logger.debug(f"LLM response: {response_text[:200]}...")

            # Parse JSON from response
            detail_spec = self._extract_json(response_text)

            # Add metadata
            detail_spec["_metadata"] = {
                "agent": self.role.value,
                "model": self.model_name,
                "request_id": str(context.request.request_id),
                "dimensions": f"{context.request.dimensions.width}x{context.request.dimensions.height}",
                "palette_size": len(palette_colors),
            }

            logger.info("Detail specification generated successfully")
            return detail_spec

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            raise ProcessingError(
                agent_role=self.role,
                message=f"Invalid JSON in detail response: {e}",
                context={"response_text": response_text[:500] if "response_text" in locals() else None},
            )
        except Exception as e:
            logger.error(f"Detail processing failed: {e}")
            raise ProcessingError(
                agent_role=self.role,
                message=f"Detail generation failed: {e}",
                context={"error_type": type(e).__name__},
            )

    def validate_input(self, context: AgentContext) -> ValidationResult:
        """
        Validate input context before processing.

        Checks that design specification and color palette are available
        from previous steps.

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

        # Check for design specification
        design_spec = context.previous_results.get("design") or context.previous_results.get("design_specification")
        if not design_spec:
            errors.append("Design specification not found in previous results")
        elif not isinstance(design_spec, dict):
            errors.append("Design specification must be a dictionary")
        else:
            # Validate design spec has required fields
            required_keys = ["shape_language", "composition", "technical_specs"]
            missing_keys = [key for key in required_keys if key not in design_spec]
            if missing_keys:
                warnings.append(f"Design spec missing recommended fields: {', '.join(missing_keys)}")

        # Check for color palette
        palette_data = context.previous_results.get("palette") or context.previous_results.get("color_palette")
        if not palette_data:
            errors.append("Color palette not found in previous results")
        else:
            # Extract colors from palette
            if isinstance(palette_data, ColorPalette):
                palette_colors = palette_data.colors
            else:
                palette_colors = palette_data.get("colors", [])

            if not palette_colors:
                errors.append("Color palette has no colors")
            elif len(palette_colors) < 3:
                warnings.append(f"Palette has only {len(palette_colors)} colors, may limit detail options")

        # Validate dimensions
        request = context.request
        dim_product = request.dimensions.width * request.dimensions.height
        if dim_product < 64:  # e.g., 8x8
            warnings.append("Very small dimensions may limit detail implementation")
        elif dim_product > 1024:  # e.g., 32x32
            suggestions.append("Large dimensions allow for rich detail and texture")

        # Check style
        if request.style.value != "stardew_valley":
            warnings.append(f"Detail agent optimized for Stardew Valley style, may need adjustments for {request.style.value}")

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def validate_output(self, output: dict[str, Any]) -> ValidationResult:
        """
        Validate detail specification output.

        Ensures the pixel implementation contains all required data
        and follows the expected structure.

        Args:
            output: Detail specification to validate

        Returns:
            ValidationResult: Validation outcome with errors/warnings
        """
        errors: list[str] = []
        warnings: list[str] = []
        suggestions: list[str] = []

        # Check required top-level keys
        required_keys = ["pixel_grid", "shading_details", "final_specs"]
        for key in required_keys:
            if key not in output:
                errors.append(f"Missing required field: {key}")

        if errors:
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Validate pixel_grid
        pixel_grid = output.get("pixel_grid", {})
        if not pixel_grid.get("data"):
            errors.append("Missing pixel_grid.data")
        else:
            grid_data = pixel_grid["data"]
            if isinstance(grid_data, list):
                # Check dimensions if provided
                if "width" in pixel_grid and "height" in pixel_grid:
                    expected_size = pixel_grid["width"] * pixel_grid["height"]
                    if len(grid_data) != expected_size:
                        errors.append(f"Pixel grid size mismatch: expected {expected_size}, got {len(grid_data)}")

        # Validate shading_details
        shading = output.get("shading_details", {})
        if not shading.get("light_source"):
            warnings.append("No light_source specified in shading_details")
        if not shading.get("shading_technique"):
            warnings.append("No shading_technique specified")

        # Validate final_specs
        final = output.get("final_specs", {})
        if not final.get("colors_used"):
            warnings.append("No colors_used list in final_specs")
        elif isinstance(final["colors_used"], list):
            # Validate colors are hex format
            for color in final["colors_used"]:
                if not isinstance(color, str) or not color.startswith("#"):
                    errors.append(f"Invalid color format in colors_used: {color}")
        
        if not final.get("readability_score"):
            suggestions.append("Consider adding readability_score to final_specs")

        # Check for implementation notes
        if "implementation_notes" in output:
            notes = output["implementation_notes"]
            if not notes:
                suggestions.append("Implementation notes are empty, consider adding guidance")

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
        return f"DetailAgent(model={self.model_name}, role={self.role.value})"