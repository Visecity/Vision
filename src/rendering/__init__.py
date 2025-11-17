"""
Vision rendering module.

This module provides all rendering functionality for the Vision pixel art
generation system, including:

- Pixel art primitives (Color, Palette, PixelGrid)
- PNG export with transparency and metadata
- Sprite sheet and texture atlas generation
- Drawing primitives (lines, shapes, patterns)
- Dithering and outline generation
"""

from .draw import (
    DrawingContext,
    DitherPattern,
    OutlineGenerator,
    create_gradient,
)
from .export import (
    BatchExporter,
    PNGExporter,
    quick_export,
)
from .pixel import (
    Color,
    Coordinate,
    Palette,
    PixelGrid,
)
from .spritesheet import (
    AnimationSheet,
    PackingAlgorithm,
    SpriteFrame,
    SpriteSheet,
    SpriteSheetPacker,
    create_texture_atlas,
)

__all__ = [
    # Pixel primitives
    "Color",
    "Coordinate",
    "Palette",
    "PixelGrid",
    # Export
    "PNGExporter",
    "BatchExporter",
    "quick_export",
    # Sprite sheets
    "SpriteFrame",
    "SpriteSheet",
    "SpriteSheetPacker",
    "AnimationSheet",
    "PackingAlgorithm",
    "create_texture_atlas",
    # Drawing
    "DrawingContext",
    "DitherPattern",
    "OutlineGenerator",
    "create_gradient",
]