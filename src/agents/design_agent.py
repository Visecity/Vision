"""
Design Agent for Vision pixel art generation system.

This agent analyzes sprite requests and creates detailed design specifications
that guide other agents in the generation pipeline.
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
    DESIGN_AGENT_SYSTEM,
    DESIGN_OUTPUT_SCHEMA,
    format_design_prompt,
)
from src.core.models import (
    AgentContext,
    AgentRole,
    ValidationResult,
)
from src.llm.client import LLMClient

logger = logging.getLogger(__name__)


class DesignAgent(BaseAgent[AgentContext, dict[str, Any]]):
    """
    Design Agent specialized in creating pixel art design specifications.

    This agent analyzes user requests and produces structured design blueprints
    that define shape language, composition, perspective, and technical constraints
    for pixel art creation in Stardew Valley style.

    Type Parameters:
        InputT: AgentContext - Processing context with sprite request
        OutputT: dict[str, Any] - Design specification as structured dictionary

    Attributes:
        llm_client: LLM client for AI-powered design analysis
        model_name: Claude model to use for design generation

    Example:
        >>> agent = DesignAgent(llm_client=client, model_name="claude-3-5-sonnet-20241022")
        >>> context = AgentContext(
        ...     request=sprite_request,
        ...     current_step="design",
        ...     previous_results={}
        ... )
        >>> design_spec = await agent.process(context)
        >>> print(design_spec["shape_language"]["primary_shape"])
    """

    def __init__(
        self,
        llm_client: LLMClient,
        model_name: str = "claude-3-5-sonnet-20241022",
    ) -> None:
        """
        Initialize the Design Agent.

        Args:
            llm_client: Configured LLM client for API calls
            model_name: Claude model identifier to use
        """
        # Define agent capabilities
        capabilities = [
            AgentCapability(
                name="design_analysis",
                description="Analyze sprite requests and create design specifications",
                required_inputs=["sprite_request"],
                provided_outputs=["design_specification"],
            ),
            AgentCapability(
                name="shape_language_definition",
                description="Define shape language and silhouette for sprites",
                required_inputs=["description", "asset_type", "dimensions"],
                provided_outputs=["shape_language", "silhouette"],
            ),
            AgentCapability(
                name="composition_design",
                description="Design composition and visual hierarchy",
                required_inputs=["sprite_request"],
                provided_outputs=["composition_spec"],
            ),
        ]

        # Create metadata
        metadata = AgentMetadata(
            name="Design Agent",
            role=AgentRole.DESIGN,
            description="Analyzes sprite requests and creates detailed design specifications",
            version="1.0.0",
            capabilities=capabilities,
        )

        super().__init__(metadata=metadata)

        self.llm_client = llm_client
        self.model_name = model_name

        logger.info(f"Initialized {self.name} with model {model_name}")

    async def process(self, context: AgentContext) -> dict[str, Any]:
        """
        Process sprite request and generate design specification.

        This method uses the LLM to analyze the user's request and create
        a structured design blueprint that other agents can follow.

        Args:
            context: Processing context containing sprite request and previous results

        Returns:
            dict[str, Any]: Design specification with shape, composition, perspective, etc.

        Raises:
            ProcessingError: If design generation fails
            ValidationError: If output validation fails
        """
        try:
            logger.info(f"Processing design for request: {context.request.request_id}")

            # Extract request details
            request = context.request
            dimensions_str = f"{request.dimensions.width}x{request.dimensions.height}"

            # Format the user prompt
            user_prompt = format_design_prompt(
                request_description=request.description,
                asset_type=request.asset_type.value,
                dimensions=dimensions_str,
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
                temperature=0.7,  # Moderate creativity for design
                system=DESIGN_AGENT_SYSTEM,
            )

            # Extract and parse response
            response_text = response.content[0].text  # type: ignore
            logger.debug(f"LLM response: {response_text[:200]}...")

            # Parse JSON from response
            design_spec = self._extract_json(response_text)

            # Add metadata
            design_spec["_metadata"] = {
                "agent": self.role.value,
                "model": self.model_name,
                "request_id": str(request.request_id),
                "asset_type": request.asset_type.value,
                "dimensions": dimensions_str,
            }

            logger.info("Design specification generated successfully")
            return design_spec

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            raise ProcessingError(
                agent_role=self.role,
                message=f"Invalid JSON in design response: {e}",
                context={"response_text": response_text[:500] if "response_text" in locals() else None},
            )
        except Exception as e:
            logger.error(f"Design processing failed: {e}")
            raise ProcessingError(
                agent_role=self.role,
                message=f"Design generation failed: {e}",
                context={"error_type": type(e).__name__},
            )

    def validate_input(self, context: AgentContext) -> ValidationResult:
        """
        Validate input context before processing.

        Checks that the sprite request contains all necessary information
        for design generation.

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

        # Validate description
        if not request.description or len(request.description.strip()) < 10:
            errors.append("Sprite description is too short (minimum 10 characters)")
        elif len(request.description) > 2000:
            warnings.append("Very long description may lead to unfocused designs")

        # Validate dimensions
        if request.dimensions.width < 8 or request.dimensions.height < 8:
            errors.append("Dimensions too small for meaningful design (minimum 8x8)")
        elif request.dimensions.width > 64 or request.dimensions.height > 64:
            warnings.append("Large dimensions may require complex design approach")

        # Check for Stardew Valley style compatibility
        if request.style.value != "stardew_valley":
            warnings.append(f"Design agent optimized for Stardew Valley style, may need adjustments for {request.style.value}")

        # Suggestions
        if request.dimensions.width != request.dimensions.height:
            suggestions.append("Non-square dimensions may require careful composition balance")

        if not request.reference_images:
            suggestions.append("Consider providing reference images for more accurate designs")

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def validate_output(self, output: dict[str, Any]) -> ValidationResult:
        """
        Validate design specification output.

        Ensures the generated design spec contains all required fields
        and follows the expected structure.

        Args:
            output: Design specification to validate

        Returns:
            ValidationResult: Validation outcome with errors/warnings
        """
        errors: list[str] = []
        warnings: list[str] = []
        suggestions: list[str] = []

        # Check required top-level keys
        required_keys = ["shape_language", "composition", "perspective", "technical_specs", "constraints"]
        for key in required_keys:
            if key not in output:
                errors.append(f"Missing required field: {key}")

        if errors:
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Validate shape_language
        shape = output.get("shape_language", {})
        if not shape.get("primary_shape"):
            errors.append("Missing primary_shape in shape_language")
        if not shape.get("silhouette_description"):
            errors.append("Missing silhouette_description in shape_language")
        if not shape.get("key_features") or len(shape.get("key_features", [])) == 0:
            warnings.append("No key_features defined in shape_language")

        # Validate composition
        comp = output.get("composition", {})
        if not comp.get("focal_point"):
            warnings.append("No focal_point defined in composition")
        if not comp.get("balance"):
            warnings.append("No balance strategy defined in composition")

        # Validate perspective
        persp = output.get("perspective", {})
        if not persp.get("view_angle"):
            errors.append("Missing view_angle in perspective")
        if persp.get("view_angle") and "3/4" not in str(persp.get("view_angle")):
            warnings.append("Perspective should typically be 3/4 for Stardew Valley style")

        # Validate technical_specs
        tech = output.get("technical_specs", {})
        if not tech.get("dimensions"):
            errors.append("Missing dimensions in technical_specs")
        if not tech.get("complexity_level"):
            warnings.append("No complexity_level specified")
        elif tech.get("complexity_level") not in ["simple", "medium", "complex"]:
            warnings.append(f"Unusual complexity_level: {tech.get('complexity_level')}")

        # Validate constraints
        const = output.get("constraints", {})
        if not const.get("must_have") or len(const.get("must_have", [])) == 0:
            warnings.append("No must_have constraints defined")
        if not const.get("should_avoid") or len(const.get("should_avoid", [])) == 0:
            suggestions.append("Consider adding should_avoid constraints for clarity")

        # Additional quality checks
        if "implementation_guidance" in output:
            guidance = output["implementation_guidance"]
            if not guidance.get("build_order"):
                suggestions.append("Consider adding build_order to implementation_guidance")

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
        return f"DesignAgent(model={self.model_name}, role={self.role.value})"