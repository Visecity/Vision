"""
Pydantic schemas for DetailAgent structured outputs.

These schemas define the exact structure that DetailAgent must return,
enforced by Anthropic's Structured Outputs API.

Includes both standard grid format and RLE (Run-Length Encoding) format
for efficient storage of larger sprites.
"""

from pydantic import BaseModel, Field
from typing import Literal


class PixelGrid(BaseModel):
    """Pixel grid data structure (standard format)."""
    
    width: int = Field(description="Grid width in pixels")
    height: int = Field(description="Grid height in pixels")
    data: list[list[str]] = Field(
        description="2D array of hex colors (format: #RRGGBB) or 'transparent'. Each inner list is a row of pixels."
    )
    format: str = Field(
        default="row-major array of hex colors",
        description="Description of data format"
    )


class RLESegment(BaseModel):
    """A run of consecutive pixels with the same color (RLE format)."""
    
    color: str = Field(
        ...,
        description="6-character hex color code (e.g., '#FF5733') or 'transparent'",
        pattern="^(#[0-9A-Fa-f]{6}|transparent)$"
    )
    count: int = Field(
        ...,
        description="Number of consecutive pixels with this color",
        ge=1,
        le=4096  # Max for 64×64 grid
    )


class PixelGridRLE(BaseModel):
    """Pixel grid using run-length encoding for efficient storage."""
    
    width: int = Field(
        ...,
        description="Grid width in pixels",
        ge=1,
        le=128
    )
    height: int = Field(
        ...,
        description="Grid height in pixels",
        ge=1,
        le=128
    )
    encoding: Literal["rle"] = Field(
        default="rle",
        description="Encoding type - must be 'rle'"
    )
    data: list[RLESegment] = Field(
        ...,
        description="RLE-encoded pixel data, row by row from top-left to bottom-right"
    )


class PaletteIndexSegment(BaseModel):
    """RLE segment using palette indices instead of hex codes (palette indexing format)."""
    
    idx: int = Field(
        ...,
        description="Index into color palette (0-254 for palette colors, 255 for transparent)",
        ge=0,
        le=255
    )
    count: int = Field(
        ...,
        description="Number of consecutive pixels with this palette color",
        ge=1,
        le=4096
    )


class PixelGridPaletteIndexed(BaseModel):
    """Pixel grid using palette indexing + RLE for maximum efficiency.
    
    This format is ideal for sprites with limited color counts (≤16 colors),
    which is typical for pixel art. Instead of repeating hex codes, colors
    are defined once in a palette and referenced by index.
    """
    
    width: int = Field(
        ...,
        description="Grid width in pixels",
        ge=1,
        le=128
    )
    height: int = Field(
        ...,
        description="Grid height in pixels",
        ge=1,
        le=128
    )
    encoding: Literal["palette_indexed_rle"] = Field(
        default="palette_indexed_rle",
        description="Encoding type - must be 'palette_indexed_rle'"
    )
    palette: list[str] = Field(
        ...,
        description="Color palette (max 255 colors). Each color is a 6-character hex code (#RRGGBB). Index 255 is reserved for 'transparent'.",
        max_length=255
    )
    data: list[PaletteIndexSegment] = Field(
        ...,
        description="RLE-encoded pixel data using palette indices, row by row from top-left to bottom-right"
    )


class ShadingDetails(BaseModel):
    """Shading and lighting details."""
    
    light_source: str = Field(description="Direction of light source (e.g., 'top-left', 'overhead')")
    shading_technique: str = Field(description="Technique used for shading (e.g., 'dithering', 'gradient', 'cel-shading')")
    contrast_level: str = Field(
        default="medium",
        description="Level of contrast used (low, medium, high)"
    )


class FinalSpecs(BaseModel):
    """Final specifications and metadata."""
    
    colors_used: list[str] = Field(
        description="List of all hex colors used (format: #RRGGBB only, no 8-char hex with alpha)"
    )
    total_pixels: int = Field(description="Total number of non-transparent pixels")
    readability_score: str = Field(
        default="high",
        description="Readability at small size (low, medium, high)"
    )


class DetailAgentOutput(BaseModel):
    """Complete DetailAgent output structure."""
    
    pixel_grid: PixelGrid = Field(description="The pixel-by-pixel implementation")
    shading_details: ShadingDetails = Field(description="Shading and lighting information")
    final_specs: FinalSpecs = Field(description="Final specifications and metadata")
    implementation_notes: str | None = Field(
        default=None,
        description="Optional notes about implementation choices"
    )


class DetailAgentOutputRLE(BaseModel):
    """Complete DetailAgent output structure with RLE compression."""
    
    pixel_grid: PixelGridRLE = Field(description="The pixel-by-pixel implementation using RLE")
    shading_details: ShadingDetails = Field(description="Shading and lighting information")
    final_specs: FinalSpecs = Field(description="Final specifications and metadata")
    implementation_notes: str | None = Field(
        default=None,
        description="Optional notes about implementation choices"
    )


class DetailAgentOutputPaletteIndexed(BaseModel):
    """Complete DetailAgent output structure with palette indexing + RLE compression.
    
    This format achieves 60-75% better compression than standard RLE for sprites
    with limited color counts (≤16 colors), which is typical for pixel art.
    """
    
    pixel_grid: PixelGridPaletteIndexed = Field(description="The pixel-by-pixel implementation using palette indexing")
    shading_details: ShadingDetails = Field(description="Shading and lighting information")
    final_specs: FinalSpecs = Field(description="Final specifications and metadata")
    implementation_notes: str | None = Field(
        default=None,
        description="Optional notes about implementation choices"
    )


# ============================================================================
# Animation Delta Encoding Schemas
# ============================================================================


class PixelChange(BaseModel):
    """A single pixel change in a delta frame (delta encoding format)."""
    
    x: int = Field(
        ...,
        description="X coordinate of changed pixel",
        ge=0,
        le=127
    )
    y: int = Field(
        ...,
        description="Y coordinate of changed pixel",
        ge=0,
        le=127
    )
    color: str = Field(
        ...,
        description="New color value (6-character hex code or 'transparent')",
        pattern="^(#[0-9A-Fa-f]{6}|transparent)$"
    )


class FrameDelta(BaseModel):
    """Delta changes for a single animation frame.
    
    Represents the difference between a frame and its reference (usually previous frame).
    Can also represent a keyframe with complete frame data.
    """
    
    frame_index: int = Field(
        ...,
        description="Frame number in animation sequence (0-based)",
        ge=0
    )
    is_keyframe: bool = Field(
        default=False,
        description="True if this delta contains a complete frame (keyframe)"
    )
    changes: list[PixelChange] = Field(
        default_factory=list,
        description="List of pixel changes from reference frame (empty for keyframes)"
    )
    frame_data: list[list[str]] | None = Field(
        default=None,
        description="Complete frame data (only for keyframes)"
    )


class AnimationDelta(BaseModel):
    """Complete animation using delta encoding.
    
    Stores first frame completely (keyframe) and subsequent frames as deltas
    (pixel differences). This achieves 70-80% compression for typical animations
    where frames share many common pixels.
    """
    
    width: int = Field(
        ...,
        description="Frame width in pixels",
        ge=1,
        le=128
    )
    height: int = Field(
        ...,
        description="Frame height in pixels",
        ge=1,
        le=128
    )
    frame_count: int = Field(
        ...,
        description="Total number of frames in animation",
        ge=2,
        le=64
    )
    encoding: Literal["delta"] = Field(
        default="delta",
        description="Encoding type - must be 'delta'"
    )
    keyframe: list[list[str]] = Field(
        ...,
        description="First frame stored completely (reference for deltas)"
    )
    deltas: list[FrameDelta] = Field(
        ...,
        description="Frame-by-frame deltas starting from frame 1"
    )


class AnimationAgentOutputDelta(BaseModel):
    """Complete AnimationAgent output with delta encoding.
    
    This format is highly efficient for animations where consecutive frames
    have minimal changes, achieving 70-80% compression over storing all frames.
    """
    
    animation: AnimationDelta = Field(description="Delta-encoded animation sequence")
    animation_specs: dict = Field(
        default_factory=dict,
        description="Animation specifications (timing, loop settings, etc.)"
    )
    implementation_notes: str | None = Field(
        default=None,
        description="Optional notes about animation implementation"
    )