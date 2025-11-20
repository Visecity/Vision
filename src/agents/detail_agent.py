"""
Detail Agent for Vision pixel art generation system.

This agent implements design specifications at the pixel level, applying
color palettes with proper shading, highlights, and texture details.

Supports multiple encoding formats:
- Standard grid: For small sprites (<256 pixels)
- RLE: For larger sprites (>256 pixels)
- Palette indexing + RLE: For sprites with ≤16 colors (best compression)
"""

import json
import logging
import time
from typing import Any
from datetime import datetime

from src.agents.base import (
    AgentCapability,
    AgentMetadata,
    BaseAgent,
    ProcessingError,
    ValidationError,
)
from src.agents.detail_schemas import (
    DetailAgentOutput,
    DetailAgentOutputRLE,
    DetailAgentOutputPaletteIndexed,
)
from src.agents.prompts import (
    DETAIL_AGENT_SYSTEM,
    DETAIL_OUTPUT_SCHEMA,
    format_detail_prompt,
)
from src.rendering.rle_decoder import decode_rle_to_grid, calculate_compression_ratio
from src.rendering.palette_encoder import (
    decode_palette_indexed,
    calculate_palette_compression_ratio,
)
from src.rendering.complexity_analyzer import (
    estimate_complexity_from_design,
    recommend_encoding_strategy,
    get_compression_estimate,
)
from src.rendering.metadata_schema import (
    SpriteMetadata,
    ComplexityMetrics,
    EncodingDecision,
    PerformanceMetrics,
)
from src.rendering.metadata_collector import MetadataCollector
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
        # Start timing for performance metrics
        process_start_time = time.perf_counter()
        
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

            # Determine optimal encoding strategy using complexity analysis
            dimensions = context.request.dimensions
            pixel_count = dimensions.width * dimensions.height
            is_animated = context.request.animation is not None
            palette_size = len(palette_colors)
            
            # Estimate sprite complexity from design specification
            logger.info("Analyzing sprite complexity from design specification")
            analysis_start_time = time.perf_counter()
            complexity_metrics = estimate_complexity_from_design(design_spec)
            analysis_time_ms = (time.perf_counter() - analysis_start_time) * 1000
            
            # Get encoding recommendation based on complexity
            recommended_encoding = recommend_encoding_strategy(
                complexity=complexity_metrics,
                pixel_count=pixel_count,
                palette_size=palette_size
            )
            
            # Get compression estimates for the recommended encoding
            compression_estimate = get_compression_estimate(
                complexity=complexity_metrics,
                pixel_count=pixel_count,
                encoding=recommended_encoding
            )
            
            logger.info(
                f"Complexity analysis complete: "
                f"entropy={complexity_metrics['entropy']:.3f}, "
                f"repetition={complexity_metrics['repetition_score']:.3f}, "
                f"structure={complexity_metrics['structure_score']:.3f}, "
                f"rle_ratio={complexity_metrics['estimated_rle_ratio']:.3f}"
            )
            logger.info(
                f"Recommended encoding: {recommended_encoding} "
                f"(estimated compression: {compression_estimate['compression_ratio']:.3f}, "
                f"tokens: {compression_estimate['token_estimate']})"
            )
            
            # Map recommended encoding to implementation flags
            use_palette_indexing = recommended_encoding == "palette_indexed_rle"
            use_rle = recommended_encoding == "rle"
            
            if use_palette_indexing:
                logger.info(
                    f"Using palette indexing for {dimensions.width}x{dimensions.height} sprite "
                    f"with {palette_size} colors"
                )
                output_format = DetailAgentOutputPaletteIndexed
                system_prompt = self._get_palette_indexed_system_prompt()
            elif use_rle:
                logger.info(
                    f"Using RLE encoding for {dimensions.width}x{dimensions.height} "
                    f"({'animated' if is_animated else 'static'}) sprite"
                )
                output_format = DetailAgentOutputRLE
                system_prompt = self._get_rle_system_prompt()
            else:
                logger.info(
                    f"Using standard grid format for {dimensions.width}x{dimensions.height} sprite"
                )
                output_format = DetailAgentOutput
                system_prompt = DETAIL_AGENT_SYSTEM

            # Call LLM with structured output
            response = await self.llm_client.create_message(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
                max_tokens=8192,
                temperature=0.6,
                system=system_prompt,
                response_format=output_format,
            )

            # Extract structured response
            response_text = response.content[0].text  # type: ignore
            logger.debug(f"LLM response: {response_text[:200]}...")

            # Parse structured output
            try:
                parsed_output = output_format.model_validate_json(response_text)
            except Exception as parse_error:
                logger.error(f"Failed to parse structured output: {parse_error}")
                raise ProcessingError(
                    agent_role=self.role,
                    message=f"Failed to parse structured output: {parse_error}",
                    context={"response_text": response_text[:500]},
                )

            # Convert Pydantic model to dict
            detail_spec = parsed_output.model_dump()
            
            # Decode compressed formats to standard grid
            if use_palette_indexing:
                pixel_grid = detail_spec.get("pixel_grid", {})
                if pixel_grid.get("encoding") == "palette_indexed_rle":
                    logger.info("Decoding palette-indexed RLE to standard grid format")
                    
                    try:
                        # Decode palette-indexed data with auto-correction
                        palette = pixel_grid.get("palette", [])
                        rle_segments = pixel_grid.get("data", [])
                        
                        decoded_grid = decode_palette_indexed(
                            pixel_grid["width"],
                            pixel_grid["height"],
                            palette,
                            rle_segments,
                            auto_correct=True,
                            tolerance=0.05
                        )
                        
                        # Calculate compression metrics
                        compression_metrics = calculate_palette_compression_ratio(
                            len(palette),
                            len(rle_segments),
                            pixel_grid["width"],
                            pixel_grid["height"]
                        )
                        
                        # Replace with decoded grid
                        detail_spec["pixel_grid"]["data"] = decoded_grid
                        detail_spec["pixel_grid"]["encoding"] = "grid"
                        detail_spec["pixel_grid"]["format"] = "row-major array of hex colors"
                        
                        # Add palette indexing metadata
                        detail_spec["pixel_grid"]["_palette_indexed_metadata"] = {
                            "was_palette_indexed": True,
                            "palette_size": len(palette),
                            "segment_count": len(rle_segments),
                            "compression_vs_grid_percent": compression_metrics["vs_grid_percent"],
                            "compression_vs_rle_percent": compression_metrics["vs_standard_rle_percent"],
                            "estimated_tokens": compression_metrics["estimated_tokens"],
                            "actual_compression_ratio": compression_metrics["compression_ratio"],
                        }
                        
                        logger.info(
                            f"Palette indexing successful: {len(palette)} colors, "
                            f"{len(rle_segments)} segments -> {pixel_grid['width']}x{pixel_grid['height']} grid "
                            f"(compression vs grid: {compression_metrics['vs_grid_percent']:.1f}%, "
                            f"vs RLE: {compression_metrics['vs_standard_rle_percent']:.1f}%)"
                        )
                        
                    except Exception as decode_error:
                        logger.error(f"Palette indexing decoding failed: {decode_error}")
                        raise ProcessingError(
                            agent_role=self.role,
                            message=f"Failed to decode palette-indexed data: {decode_error}",
                            context={
                                "palette_size": len(pixel_grid.get("palette", [])),
                                "segment_count": len(pixel_grid.get("data", []))
                            },
                        )
            
            elif use_rle:
                pixel_grid = detail_spec.get("pixel_grid", {})
                if pixel_grid.get("encoding") == "rle":
                    logger.info("Decoding RLE to standard grid format")
                    
                    try:
                        # Decode RLE data with auto-correction
                        decoded_grid = decode_rle_to_grid(
                            pixel_grid["width"],
                            pixel_grid["height"],
                            pixel_grid.get("data", []),
                            auto_correct=True,
                            tolerance=0.05
                        )
                        
                        # Calculate compression ratio
                        compression = calculate_compression_ratio(
                            pixel_grid["width"],
                            pixel_grid["height"],
                            len(pixel_grid.get("data", []))
                        )
                        
                        # Replace with decoded grid
                        detail_spec["pixel_grid"]["data"] = decoded_grid
                        detail_spec["pixel_grid"]["encoding"] = "grid"
                        detail_spec["pixel_grid"]["format"] = "row-major array of hex colors"
                        
                        # Add RLE metadata
                        detail_spec["pixel_grid"]["_rle_metadata"] = {
                            "was_rle": True,
                            "segment_count": len(pixel_grid.get("data", [])),
                            "actual_compression_ratio": compression,
                            "compression_percent": round((1 - compression) * 100, 1),
                        }
                        
                        logger.info(
                            f"RLE decoding successful: {len(pixel_grid.get('data', []))} segments -> "
                            f"{pixel_grid['width']}x{pixel_grid['height']} grid "
                            f"({(1-compression)*100:.1f}% compression)"
                        )
                        
                    except Exception as decode_error:
                        logger.error(f"RLE decoding failed: {decode_error}")
                        raise ProcessingError(
                            agent_role=self.role,
                            message=f"Failed to decode RLE data: {decode_error}",
                            context={
                                "segment_count": len(pixel_grid.get("data", []))
                            },
                        )

            # Build complete metadata using new schema
            sprite_metadata = self._build_sprite_metadata(
                context=context,
                complexity_metrics=complexity_metrics,
                recommended_encoding=recommended_encoding,
                compression_estimate=compression_estimate,
                analysis_time_ms=analysis_time_ms,
                palette_colors=palette_colors,
                use_palette_indexing=use_palette_indexing,
                use_rle=use_rle,
                detail_spec=detail_spec,
            )
            
            # Add metadata to result (backward compatibility)
            detail_spec["_metadata"] = sprite_metadata
            
            # Collect metadata for monitoring (non-blocking)
            try:
                collector = MetadataCollector()
                collector.collect(sprite_metadata)
            except Exception as e:
                logger.warning(f"Failed to collect metadata: {e}")

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

    def _get_rle_system_prompt(self) -> str:
        """
        Get the system prompt for RLE output.
        
        Returns:
            str: System prompt that instructs the LLM to use RLE encoding
        """
        return """You are a pixel art implementation agent using RLE (Run-Length Encoding) for efficient output.

CRITICAL OUTPUT FORMAT - RLE:
Instead of listing every pixel individually, group consecutive pixels of the same color.

RLE Format: {"color": "#RRGGBB", "count": N}

Example for 4×4 red-green pattern (RRRR GGGG RRRR GGGG):
[
  {"color": "#FF0000", "count": 4},
  {"color": "#00FF00", "count": 4},
  {"color": "#FF0000", "count": 4},
  {"color": "#00FF00", "count": 4}
]

Total pixels: 4+4+4+4 = 16 (matches 4×4)

IMPORTANT Rules:
1. Colors must be 6-character hex: #RRGGBB (or "transparent")
2. Total pixel count must equal width times height
3. Each segment must have count ≥ 1
4. Segments flow left-to-right, top-to-bottom (row-major order)

You will receive design specifications and color palettes. Implement the pixel art using RLE encoding for maximum efficiency."""

    def _get_palette_indexed_system_prompt(self) -> str:
        """
        Get the system prompt for palette-indexed output.
        
        Returns:
            str: System prompt that instructs the LLM to use palette indexing + RLE
        """
        return """You are a pixel art implementation agent using PALETTE INDEXING + RLE for maximum compression efficiency.

CRITICAL OUTPUT FORMAT - PALETTE INDEXING:
Instead of repeating hex codes for every pixel, define a color palette once and reference colors by index.

Palette Indexing Format:
1. Define palette: list of hex colors used in sprite (max 16 colors recommended)
2. Use indices 0-14 for palette colors, index 255 for transparent
3. Encode pixel runs using {"idx": N, "count": M}
4. Segments flow left-to-right, top-to-bottom (row-major order)

Format Structure:
{
  "palette": ["#FF0000", "#00FF00", "#0000FF"],
  "data": [
    {"idx": 0, "count": 50},
    {"idx": 1, "count": 30},
    {"idx": 255, "count": 20}
  ]
}

Example for 4×4 sprite with 3 colors:
Red-Green pattern (RR GG / RR BB / GG BB / RR GG)

Palette: ["#FF0000", "#00FF00", "#0000FF"]

RLE with indices:
[
  {"idx": 0, "count": 2},
  {"idx": 1, "count": 2},
  {"idx": 0, "count": 2},
  {"idx": 2, "count": 2},
  {"idx": 1, "count": 2},
  {"idx": 2, "count": 2},
  {"idx": 0, "count": 2},
  {"idx": 1, "count": 2}
]
Total: 2+2+2+2+2+2+2+2 = 16 (matches 4×4)

Benefits of Palette Indexing:
- 60-75% smaller than standard RLE (for sprites with 16 or fewer colors)
- 85-90% smaller than standard grid format
- Perfect for pixel art which typically uses 4-16 colors
- Maintains perfect color accuracy

IMPORTANT Rules:
1. Palette must contain ALL colors used (except transparent)
2. Maximum 255 colors in palette, index 255 reserved for transparent
3. Each color in palette must be 6-character hex: #RRGGBB
4. Indices must reference valid palette positions
5. Total pixel count must equal width times height

You will receive design specifications and a color palette. Implement the pixel art using palette indexing for maximum efficiency."""

    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"DetailAgent(model={self.model_name}, role={self.role.value})"
    def _build_sprite_metadata(
        self,
        context: AgentContext,
        complexity_metrics: dict[str, Any],
        recommended_encoding: str,
        compression_estimate: dict[str, Any],
        analysis_time_ms: float,
        palette_colors: list[str],
        use_palette_indexing: bool,
        use_rle: bool,
        detail_spec: dict[str, Any],
    ) -> SpriteMetadata:
        """
        Build complete SpriteMetadata for monitoring.
        
        Args:
            context: Processing context
            complexity_metrics: Complexity analysis results
            recommended_encoding: Recommended encoding strategy
            compression_estimate: Compression estimates
            analysis_time_ms: Time spent on analysis
            palette_colors: List of palette colors
            use_palette_indexing: Whether palette indexing was used
            use_rle: Whether RLE was used
            detail_spec: Generated detail specification
            
        Returns:
            Complete SpriteMetadata object
        """
        # Extract actual compression data if available
        actual_compression = None
        if use_palette_indexing and "_palette_indexed_metadata" in detail_spec.get("pixel_grid", {}):
            palette_meta = detail_spec["pixel_grid"]["_palette_indexed_metadata"]
            actual_compression = palette_meta.get("actual_compression_ratio")
        elif use_rle and "_rle_metadata" in detail_spec.get("pixel_grid", {}):
            rle_meta = detail_spec["pixel_grid"]["_rle_metadata"]
            actual_compression = rle_meta.get("actual_compression_ratio")
        
        # Calculate prediction accuracy if actual data available
        prediction_accuracy = None
        if actual_compression is not None:
            estimated = compression_estimate["compression_ratio"]
            prediction_error = abs(estimated - actual_compression) / actual_compression if actual_compression > 0 else 0
            prediction_accuracy = prediction_error * 100
            
            logger.info(
                f"Compression prediction accuracy: "
                f"estimated={estimated:.3f}, actual={actual_compression:.3f}, "
                f"error={prediction_accuracy:.1f}%"
            )
        
        # Build encoding decision
        selected_encoding = "palette_indexed_rle" if use_palette_indexing else ("rle" if use_rle else "standard")
        
        # Generate decision reason
        reasons = [self._get_decision_reason(
            recommended_encoding,
            complexity_metrics,
            context.request.dimensions.width * context.request.dimensions.height,
            len(palette_colors)
        )]
        
        encoding_decision: EncodingDecision = {
            "recommended_encoding": recommended_encoding,
            "selected_encoding": selected_encoding,
            "reasons": reasons,
            "estimated_compression": compression_estimate["compression_ratio"],
            "actual_compression": actual_compression,
        }
        
        # Build performance metrics
        performance_metrics: PerformanceMetrics = {
            "analysis_time_ms": analysis_time_ms,
            "prediction_accuracy_percent": prediction_accuracy,
        }
        
        # Build complete metadata
        metadata: SpriteMetadata = {
            "request_id": str(context.request.request_id),
            "agent": self.role.value,
            "model": self.model_name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "dimensions": f"{context.request.dimensions.width}x{context.request.dimensions.height}",
            "pixel_count": context.request.dimensions.width * context.request.dimensions.height,
            "palette_size": len(palette_colors),
            "asset_type": context.request.asset_type.value,
            "is_animated": context.request.animation is not None,
            "complexity_metrics": complexity_metrics,
            "encoding_decision": encoding_decision,
            "performance_metrics": performance_metrics,
            "meets_performance_target": analysis_time_ms < 10.0,
            "meets_accuracy_target": prediction_accuracy < 15.0 if prediction_accuracy is not None else None,
        }
        
        return metadata
    
    def _get_decision_reason(
        self,
        encoding: str,
        complexity: dict[str, Any],
        pixel_count: int,
        palette_size: int
    ) -> str:
        """
        Generate human-readable decision explanation.
        
        Args:
            encoding: Selected encoding strategy
            complexity: Complexity metrics
            pixel_count: Number of pixels
            palette_size: Number of colors
            
        Returns:
            Human-readable explanation of encoding choice
        """
        if encoding == "palette_indexed_rle":
            return (
                f"Palette indexing selected: {palette_size} colors (≤16 threshold), "
                f"{pixel_count} pixels (>128 threshold). "
                f"Expected {(1-complexity['estimated_rle_ratio'])*100:.0f}% compression."
            )
        elif encoding == "rle":
            return (
                f"RLE selected: {pixel_count} pixels (>256 threshold) OR "
                f"high repetition (ratio={complexity['estimated_rle_ratio']:.2f} < 0.4). "
                f"Expected {(1-complexity['estimated_rle_ratio'])*100:.0f}% compression."
            )
        else:
            return (
                f"Standard grid selected: {pixel_count} pixels (≤256) with "
                f"moderate complexity (entropy={complexity['entropy']:.2f}). "
                f"RLE overhead not justified."
            )
