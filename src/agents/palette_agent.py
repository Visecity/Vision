"""
Palette Agent for Vision pixel art generation system.

This agent selects harmonious color palettes based on design specifications,
ensuring readability and style consistency for Stardew Valley pixel art.
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
    PALETTE_AGENT_SYSTEM,
    PALETTE_OUTPUT_SCHEMA,
    format_palette_prompt,
)
from src.core.models import (
    AgentContext,
    AgentRole,
    ColorPalette,
    ValidationResult,
)
from src.llm.client import LLMClient

logger = logging.getLogger(__name__)


class PaletteAgent(BaseAgent[AgentContext, ColorPalette]):
    """
    Palette Agent specialized in selecting color palettes for pixel art.

    This agent analyzes design specifications and user requests to create
    harmonious, readable color palettes optimized for Stardew Valley style
    pixel art. It considers color theory, contrast, and readability at small
    resolutions.

    Type Parameters:
        InputT: AgentContext - Processing context with sprite request and design spec
        OutputT: ColorPalette - Color palette with semantic labels

    Attributes:
        llm_client: LLM client for AI-powered palette generation
        model_name: Claude model to use for palette selection

    Example:
        >>> agent = PaletteAgent(llm_client=client, model_name="claude-3-5-sonnet-20241022")
        >>> context = AgentContext(
        ...     request=sprite_request,
        ...     current_step="palette",
        ...     previous_results={"design": design_spec}
        ... )
        >>> palette = await agent.process(context)
        >>> print(palette.colors)
    """

    def __init__(
        self,
        llm_client: LLMClient,
        model_name: str = "claude-3-5-sonnet-20241022",
        max_colors: int = 52,
    ) -> None:
        """
        Initialize the Palette Agent.

        Args:
            llm_client: Configured LLM client for API calls
            model_name: Claude model identifier to use
            max_colors: Maximum number of colors in palette (Stardew Valley limit)
        """
        # Define agent capabilities
        capabilities = [
            AgentCapability(
                name="palette_generation",
                description="Generate harmonious color palettes for pixel art",
                required_inputs=["sprite_request", "design_specification"],
                provided_outputs=["color_palette"],
            ),
            AgentCapability(
                name="color_theory_application",
                description="Apply color theory principles for readability and harmony",
                required_inputs=["design_spec", "asset_type"],
                provided_outputs=["color_relationships", "usage_guidelines"],
            ),
            AgentCapability(
                name="stardew_palette_matching",
                description="Match colors to Stardew Valley style constraints",
                required_inputs=["sprite_request"],
                provided_outputs=["style_aligned_palette"],
            ),
        ]

        # Create metadata
        metadata = AgentMetadata(
            name="Palette Agent",
            role=AgentRole.PALETTE,
            description="Selects harmonious color palettes for pixel art generation",
            version="1.0.0",
            capabilities=capabilities,
        )

        super().__init__(metadata=metadata)

        self.llm_client = llm_client
        self.model_name = model_name
        self.max_colors = max_colors

        logger.info(f"Initialized {self.name} with model {model_name}, max_colors={max_colors}")

    async def process(self, context: AgentContext) -> ColorPalette:
        """
        Process design specification and generate color palette.

        This method uses the LLM to analyze the design spec and create
        a harmonious color palette with semantic role labels.

        Args:
            context: Processing context containing sprite request and design spec

        Returns:
            ColorPalette: Color palette with hex codes and semantic labels

        Raises:
            ProcessingError: If palette generation fails
            ValidationError: If output validation fails
        """
        try:
            logger.info(f"Processing palette for request: {context.request.request_id}")

            # Check if we have design specification from previous step
            if "design" not in context.previous_results and "design_specification" not in context.previous_results:
                logger.warning("No design specification found, proceeding with request only")
                design_spec = {}
            else:
                design_spec = context.previous_results.get("design") or context.previous_results.get("design_specification", {})

            # Check if user provided custom palette
            if context.request.palette:
                logger.info("Using user-provided custom palette")
                return context.request.palette

            # Format the user prompt
            user_prompt = format_palette_prompt(
                request_description=context.request.description,
                design_spec=design_spec,
                asset_type=context.request.asset_type.value,
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
                max_tokens=4096,
                temperature=0.8,  # Higher creativity for color exploration
                system=PALETTE_AGENT_SYSTEM,
            )

            # Extract and parse response
            response_text = response.content[0].text  # type: ignore
            logger.debug(f"LLM response: {response_text[:200]}...")

            # Parse JSON from response
            palette_data = self._extract_json(response_text)

            # Convert to ColorPalette model
            color_palette = self._convert_to_color_palette(palette_data, context)

            logger.info(f"Color palette generated successfully with {len(color_palette.colors)} colors")
            return color_palette

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            raise ProcessingError(
                agent_role=self.role,
                message=f"Invalid JSON in palette response: {e}",
                context={"response_text": response_text[:500] if "response_text" in locals() else None},
            )
        except Exception as e:
            logger.error(f"Palette processing failed: {e}")
            raise ProcessingError(
                agent_role=self.role,
                message=f"Palette generation failed: {e}",
                context={"error_type": type(e).__name__},
            )

    def validate_input(self, context: AgentContext) -> ValidationResult:
        """
        Validate input context before processing.

        Checks that the sprite request is valid and design specification
        is available if needed.

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

        request = context.request

        # Check if user provided custom palette
        if request.palette:
            # Validate custom palette
            if len(request.palette.colors) > self.max_colors:
                warnings.append(f"Custom palette has {len(request.palette.colors)} colors, exceeding recommended maximum of {self.max_colors}")
            if len(request.palette.colors) < 3:
                warnings.append("Custom palette has very few colors, may limit detail options")
        else:
            # Check for design specification
            if "design" not in context.previous_results and "design_specification" not in context.previous_results:
                warnings.append("No design specification available, palette generation will be based on request only")
            else:
                design_spec = context.previous_results.get("design") or context.previous_results.get("design_specification", {})
                if not design_spec:
                    warnings.append("Empty design specification, palette generation may be less optimal")

        # Validate dimensions for palette complexity
        dim_product = request.dimensions.width * request.dimensions.height
        if dim_product < 100:  # e.g., 10x10
            suggestions.append("Small dimensions may benefit from limited palette (3-5 colors)")
        elif dim_product > 1024:  # e.g., 32x32
            suggestions.append("Large dimensions allow for more color variety (8-12 colors)")

        # Check style
        if request.style.value != "stardew_valley":
            warnings.append(f"Palette agent optimized for Stardew Valley style, colors may need adjustment for {request.style.value}")

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def validate_output(self, output: ColorPalette) -> ValidationResult:
        """
        Validate color palette output.

        Ensures the palette meets all requirements including color count,
        hex format, and distinctness.

        Args:
            output: Color palette to validate

        Returns:
            ValidationResult: Validation outcome with errors/warnings
        """
        errors: list[str] = []
        warnings: list[str] = []
        suggestions: list[str] = []

        # Check color count
        color_count = len(output.colors)
        if color_count < 3:
            errors.append(f"Palette has too few colors ({color_count}), minimum is 3")
        elif color_count > self.max_colors:
            warnings.append(f"Palette has {color_count} colors, exceeding Stardew Valley limit of {self.max_colors}")
        elif color_count < 4:
            suggestions.append("Consider adding more colors for better shading options")
        elif color_count > 12:
            suggestions.append("Large palettes may be difficult to use effectively at small resolutions")

        # Validate hex format
        for color in output.colors:
            if not color.startswith("#"):
                errors.append(f"Invalid hex color format: {color}")
            elif len(color) not in (4, 7):  # #RGB or #RRGGBB
                errors.append(f"Invalid hex color length: {color}")

        # Check for duplicate colors
        if len(output.colors) != len(set(output.colors)):
            warnings.append("Palette contains duplicate colors")

        # Check color distinctness (simplified check)
        if color_count > 1:
            distinct_check = self._check_color_distinctness(output.colors)
            if not distinct_check["sufficient_contrast"]:
                warnings.append("Some colors may be too similar, reducing readability")
                suggestions.append("Ensure at least 20% brightness difference between adjacent shades")

        # Validate palette name
        if not output.name or len(output.name.strip()) < 3:
            warnings.append("Palette name is too short or missing")

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

    def _convert_to_color_palette(
        self,
        palette_data: dict[str, Any],
        context: AgentContext,
    ) -> ColorPalette:
        """
        Convert palette JSON to ColorPalette model.

        Extracts hex colors from the structured palette data and creates
        a ColorPalette instance with proper metadata.

        Args:
            palette_data: Parsed palette JSON from LLM
            context: Processing context for metadata

        Returns:
            ColorPalette: Validated color palette model
        """
        # Extract hex colors
        colors: list[str] = []
        color_entries = palette_data.get("colors", [])

        for entry in color_entries:
            if isinstance(entry, dict) and "hex" in entry:
                colors.append(entry["hex"])
            elif isinstance(entry, str):
                colors.append(entry)

        # Create description from metadata
        description_parts = [palette_data.get("name", "Generated Palette")]
        
        if "color_theory" in palette_data:
            theory = palette_data["color_theory"]
            scheme = theory.get("scheme", "")
            temp = theory.get("temperature", "")
            if scheme:
                description_parts.append(f"{scheme} scheme")
            if temp:
                description_parts.append(f"{temp} temperature")

        description = " | ".join(description_parts)

        # Create ColorPalette
        return ColorPalette(
            name=palette_data.get("name", f"Palette for {context.request.asset_type.value}"),
            colors=colors,
            description=description,
        )

    def _check_color_distinctness(self, colors: list[str]) -> dict[str, Any]:
        """
        Check if colors in palette are sufficiently distinct.

        Performs a simplified contrast check by comparing hex values.

        Args:
            colors: List of hex color codes

        Returns:
            dict: Analysis results with contrast information
        """
        # Simplified check: convert hex to RGB and check brightness differences
        def hex_to_brightness(hex_color: str) -> float:
            """Calculate perceived brightness from hex color."""
            hex_color = hex_color.lstrip("#")
            if len(hex_color) == 3:
                hex_color = "".join([c * 2 for c in hex_color])
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            # Perceived brightness formula
            return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0

        brightnesses = [hex_to_brightness(c) for c in colors]
        
        # Check minimum brightness difference
        min_diff = 1.0
        for i in range(len(brightnesses)):
            for j in range(i + 1, len(brightnesses)):
                diff = abs(brightnesses[i] - brightnesses[j])
                min_diff = min(min_diff, diff)

        sufficient_contrast = min_diff >= 0.15  # At least 15% brightness difference

        return {
            "sufficient_contrast": sufficient_contrast,
            "minimum_difference": min_diff,
            "recommendation": "good" if sufficient_contrast else "increase contrast",
        }

    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"PaletteAgent(model={self.model_name}, max_colors={self.max_colors}, role={self.role.value})"