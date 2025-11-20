"""
Core data models for Vision pixel art generation system.

This module defines Pydantic models for all data structures used throughout
the system, ensuring type safety and validation at every step.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class AssetType(str, Enum):
    """Types of pixel art assets that can be generated."""

    SPRITE = "sprite"
    TILE = "tile"
    ICON = "icon"
    CHARACTER = "character"
    OBJECT = "object"
    UI_ELEMENT = "ui_element"


class AssetStyle(str, Enum):
    """Art styles for generated assets."""

    STARDEW_VALLEY = "stardew_valley"
    RETRO_8BIT = "retro_8bit"
    RETRO_16BIT = "retro_16bit"
    PIXEL_ART = "pixel_art"
    CUSTOM = "custom"


class AgentRole(str, Enum):
    """Roles for different agents in the system."""

    ORCHESTRATOR = "orchestrator"
    DESIGN = "design"
    PALETTE = "palette"
    DETAIL = "detail"
    ANIMATION = "animation"
    VALIDATOR = "validator"


class MessageType(str, Enum):
    """Types of messages exchanged between agents."""

    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    STATUS = "status"


class GenerationStatus(str, Enum):
    """Status of asset generation process."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Dimensions(BaseModel):
    """Pixel dimensions for an asset."""

    width: int = Field(gt=0, le=512, description="Width in pixels")
    height: int = Field(gt=0, le=512, description="Height in pixels")

    @model_validator(mode="after")
    def validate_dimensions(self) -> "Dimensions":
        """Validate dimension constraints."""
        if self.width * self.height > 262144:  # 512x512 max
            raise ValueError("Total pixel count cannot exceed 262,144 (512x512)")
        return self


class ColorPalette(BaseModel):
    """Color palette definition."""

    name: str = Field(description="Palette name")
    colors: list[str] = Field(
        min_length=1,
        max_length=256,
        description="List of hex color codes",
    )
    description: str | None = Field(
        default=None,
        description="Optional palette description",
    )

    @field_validator("colors")
    @classmethod
    def validate_hex_colors(cls, v: list[str]) -> list[str]:
        """Validate that all colors are valid hex codes."""
        for color in v:
            if not color.startswith("#") or len(color) not in (4, 7):
                raise ValueError(f"Invalid hex color: {color}")
        return v


class AnimationConfig(BaseModel):
    """Configuration for animated sprites."""

    frame_count: int = Field(ge=2, le=64, description="Number of animation frames")
    frame_duration: int = Field(
        ge=50,
        le=5000,
        description="Duration of each frame in milliseconds",
    )
    loop: bool = Field(default=True, description="Whether animation should loop")


class SpriteRequest(BaseModel):
    """User input for sprite generation request."""

    request_id: UUID = Field(default_factory=uuid4, description="Unique request identifier")
    description: str = Field(
        min_length=10,
        max_length=2000,
        description="Natural language description of the sprite",
    )
    asset_type: AssetType = Field(description="Type of asset to generate")
    style: AssetStyle = Field(
        default=AssetStyle.STARDEW_VALLEY,
        description="Art style to apply",
    )
    dimensions: Dimensions = Field(
        default=Dimensions(width=16, height=16),
        description="Target dimensions",
    )
    palette: ColorPalette | None = Field(
        default=None,
        description="Optional custom color palette",
    )
    animation: AnimationConfig | None = Field(
        default=None,
        description="Optional animation configuration",
    )
    reference_images: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Optional reference image URLs or paths",
    )
    tags: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="Tags for categorization",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Request creation timestamp",
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate and normalize tags."""
        return [tag.lower().strip() for tag in v if tag.strip()]


class SpriteMetadata(BaseModel):
    """Metadata for a generated sprite asset."""

    asset_id: UUID = Field(default_factory=uuid4, description="Unique asset identifier")
    request_id: UUID = Field(description="Original request identifier")
    asset_type: AssetType = Field(description="Type of asset")
    style: AssetStyle = Field(description="Applied art style")
    dimensions: Dimensions = Field(description="Actual dimensions")
    palette_used: ColorPalette = Field(description="Color palette used in generation")
    file_path: str = Field(description="Path to generated asset file")
    thumbnail_path: str | None = Field(
        default=None,
        description="Path to thumbnail image",
    )
    frame_count: int = Field(default=1, ge=1, description="Number of frames (1 for static)")
    tags: list[str] = Field(default_factory=list, description="Asset tags")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Generation timestamp",
    )
    generation_time_seconds: float = Field(
        ge=0,
        description="Time taken to generate",
    )

    model_config = {"json_schema_extra": {"example": {"asset_id": "123e4567-e89b-12d3-a456-426614174000"}}}


class AgentMessage(BaseModel):
    """Message structure for inter-agent communication."""

    message_id: UUID = Field(default_factory=uuid4, description="Unique message identifier")
    from_agent: AgentRole = Field(description="Sending agent role")
    to_agent: AgentRole | None = Field(
        default=None,
        description="Recipient agent role (None for broadcast)",
    )
    message_type: MessageType = Field(description="Type of message")
    content: dict[str, Any] = Field(
        default_factory=dict,
        description="Message payload",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context data",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Message timestamp",
    )
    parent_message_id: UUID | None = Field(
        default=None,
        description="ID of message this is responding to",
    )


class GenerationResult(BaseModel):
    """Complete result of asset generation process."""

    request_id: UUID = Field(description="Original request identifier")
    status: GenerationStatus = Field(description="Final generation status")
    metadata: SpriteMetadata | None = Field(
        default=None,
        description="Asset metadata (if successful)",
    )
    manifest_json: dict[str, Any] | None = Field(
        default=None,
        description="Manifest JSON DSL (if applicable)",
    )
    error_message: str | None = Field(
        default=None,
        description="Error message (if failed)",
    )
    agent_messages: list[AgentMessage] = Field(
        default_factory=list,
        description="Log of agent communications",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-critical warnings",
    )
    completed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Completion timestamp",
    )
    rendering_info: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Rendering information including: "
            "'png_path' (str), 'auto_rendered' (bool), "
            "'render_error' (str), 'sprite_sheet' (bool), "
            "'frame_count' (int), 'render_time_seconds' (float)"
        ),
    )

    @model_validator(mode="after")
    def validate_result_consistency(self) -> "GenerationResult":
        """Validate that result fields are consistent with status."""
        if self.status == GenerationStatus.COMPLETED and self.metadata is None:
            raise ValueError("Completed status requires metadata")
        if self.status == GenerationStatus.FAILED and self.error_message is None:
            raise ValueError("Failed status requires error_message")
        return self


class AgentContext(BaseModel):
    """Context information passed to agents during processing."""

    request: SpriteRequest = Field(description="Original user request")
    current_step: str = Field(description="Current processing step")
    previous_results: dict[str, Any] = Field(
        default_factory=dict,
        description="Results from previous agents",
    )
    constraints: dict[str, Any] = Field(
        default_factory=dict,
        description="Processing constraints",
    )
    retry_count: int = Field(default=0, ge=0, description="Number of retries attempted")


class ValidationResult(BaseModel):
    """Result of validation operations."""

    is_valid: bool = Field(description="Whether validation passed")
    errors: list[str] = Field(
        default_factory=list,
        description="Validation errors",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Validation warnings",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Improvement suggestions",
    )


class AssetResult(BaseModel):
    """Result from single asset generation in a batch."""
    
    name: str = Field(description="Asset name/identifier")
    success: bool = Field(description="Whether generation succeeded")
    manifest_path: Path | None = Field(
        default=None,
        description="Path to manifest JSON file (if successful)",
    )
    png_path: Path | None = Field(
        default=None,
        description="Path to rendered PNG file (if successful)",
    )
    error: str | None = Field(
        default=None,
        description="Error message (if failed)",
    )
    generation_time: float = Field(
        default=0.0,
        ge=0,
        description="Time taken to generate in seconds",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional asset metadata",
    )


class BatchResult(BaseModel):
    """Results from batch execution."""
    
    batch_name: str = Field(description="Name of the batch")
    total_requests: int = Field(ge=0, description="Total number of asset requests")
    successful: int = Field(ge=0, description="Number of successful generations")
    failed: int = Field(ge=0, description="Number of failed generations")
    assets: list[AssetResult] = Field(
        default_factory=list,
        description="List of individual asset results",
    )
    atlas_path: Path | None = Field(
        default=None,
        description="Path to combined atlas PNG (if created)",
    )
    atlas_metadata_path: Path | None = Field(
        default=None,
        description="Path to atlas metadata JSON (if created)",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="List of batch-level errors",
    )
    execution_time: float = Field(
        default=0.0,
        ge=0,
        description="Total batch execution time in seconds",
    )
    completed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Batch completion timestamp",
    )
    
    @model_validator(mode="after")
    def validate_counts(self) -> "BatchResult":
        """Validate that counts are consistent."""
        if self.successful + self.failed != self.total_requests:
            raise ValueError(
                f"successful ({self.successful}) + failed ({self.failed}) "
                f"must equal total_requests ({self.total_requests})"
            )
        return self


class AssetDefinition(BaseModel):
    """Definition for a single asset in a batch."""
    
    description: str = Field(
        min_length=10,
        max_length=2000,
        description="Asset description",
    )
    name: str | None = Field(
        default=None,
        description="Optional explicit asset name",
    )
    dimensions: Dimensions | None = Field(
        default=None,
        description="Optional dimensions (uses batch default if not specified)",
    )
    style: AssetStyle | None = Field(
        default=None,
        description="Optional style (uses batch default if not specified)",
    )
    asset_type: AssetType | None = Field(
        default=None,
        description="Optional asset type (uses batch default if not specified)",
    )
    category: str | None = Field(
        default=None,
        description="Optional category for organization",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Optional tags",
    )
    animation: AnimationConfig | None = Field(
        default=None,
        description="Optional animation configuration",
    )


class BatchDefinition(BaseModel):
    """Complete batch definition for multiple assets."""
    
    batch_name: str = Field(description="Name for this batch")
    output_dir: Path = Field(description="Output directory for assets")
    create_atlas: bool = Field(
        default=False,
        description="Whether to combine assets into atlas",
    )
    atlas_name: str | None = Field(
        default=None,
        description="Name for atlas (defaults to batch_name)",
    )
    
    # Default settings for all assets
    default_style: AssetStyle = Field(
        default=AssetStyle.STARDEW_VALLEY,
        description="Default style for all assets",
    )
    default_dimensions: Dimensions = Field(
        default=Dimensions(width=16, height=16),
        description="Default dimensions for all assets",
    )
    default_asset_type: AssetType = Field(
        default=AssetType.SPRITE,
        description="Default asset type",
    )
    
    # Asset definitions
    assets: list[AssetDefinition] = Field(
        min_length=1,
        description="List of assets to generate",
    )
    
    # Batch execution settings
    parallel_count: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Number of parallel generations",
    )


# TODO: Phase 3 - Add models for LangGraph state management
# TODO: Phase 3 - Add models for agent-specific outputs (design specs, palette selections)
# TODO: Phase 3 - Add models for animation frame data
# TODO: Phase 4 - Add models for version control and asset history