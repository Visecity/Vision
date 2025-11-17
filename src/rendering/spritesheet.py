"""
Sprite sheet and texture atlas generation for Vision pixel art system.

This module provides utilities for packing multiple sprites into sprite sheets
and texture atlases, with support for various packing algorithms and metadata
generation for game engines.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from .pixel import Color, PixelGrid
from .export import PNGExporter


class PackingAlgorithm(Enum):
    """Sprite sheet packing algorithms."""
    
    ROW = "row"  # Pack sprites in rows
    COLUMN = "column"  # Pack sprites in columns
    GRID = "grid"  # Pack sprites in a grid
    SHELF = "shelf"  # Shelf packing (bin packing)
    MAXRECTS = "maxrects"  # MaxRects algorithm (efficient)


@dataclass
class SpriteFrame:
    """
    Represents a single sprite frame in a sprite sheet.
    
    Attributes:
        name: Frame identifier
        grid: PixelGrid containing the sprite data
        x: X position in sprite sheet
        y: Y position in sprite sheet
        width: Frame width
        height: Frame height
    """
    
    name: str
    grid: PixelGrid
    x: int = 0
    y: int = 0
    
    @property
    def width(self) -> int:
        """Get frame width."""
        return self.grid.width
    
    @property
    def height(self) -> int:
        """Get frame height."""
        return self.grid.height
    
    def to_dict(self) -> dict[str, int | str]:
        """
        Convert to dictionary format for metadata.
        
        Returns:
            dict: Frame metadata
        """
        return {
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }


@dataclass
class SpriteSheet:
    """
    Represents a complete sprite sheet with frames and metadata.
    
    Attributes:
        width: Sheet width in pixels
        height: Sheet height in pixels
        frames: List of sprite frames
        padding: Padding between sprites in pixels
        background: Background color
    """
    
    width: int
    height: int
    frames: list[SpriteFrame]
    padding: int = 0
    background: Color = Color(0, 0, 0)
    
    def to_grid(self) -> PixelGrid:
        """
        Render sprite sheet to a PixelGrid.
        
        Returns:
            PixelGrid: Complete sprite sheet
        """
        sheet = PixelGrid(self.width, self.height, background=self.background)
        sheet_array = sheet.to_numpy()
        
        for frame in self.frames:
            frame_array = frame.grid.to_numpy()
            sheet_array[
                frame.y:frame.y + frame.height,
                frame.x:frame.x + frame.width,
                :
            ] = frame_array
        
        return PixelGrid.from_numpy(sheet_array)
    
    def get_metadata(self) -> dict:
        """
        Get sprite sheet metadata in JSON-compatible format.
        
        Returns:
            dict: Complete sprite sheet metadata
        """
        return {
            "width": self.width,
            "height": self.height,
            "padding": self.padding,
            "frame_count": len(self.frames),
            "frames": {frame.name: frame.to_dict() for frame in self.frames},
        }


class SpriteSheetPacker:
    """
    Packs multiple sprites into a sprite sheet using various algorithms.
    
    Supports different packing strategies optimized for different use cases:
    - ROW/COLUMN: Simple linear packing
    - GRID: Fixed grid layout
    - SHELF: Efficient shelf-based packing
    - MAXRECTS: Advanced MaxRects algorithm for optimal space usage
    """
    
    def __init__(
        self,
        algorithm: PackingAlgorithm = PackingAlgorithm.GRID,
        padding: int = 0,
        max_width: int = 1024,
        max_height: int = 1024,
        power_of_two: bool = False,
        background: Color = Color(0, 0, 0),
    ) -> None:
        """
        Initialize sprite sheet packer.
        
        Args:
            algorithm: Packing algorithm to use
            padding: Padding between sprites in pixels
            max_width: Maximum sheet width
            max_height: Maximum sheet height
            power_of_two: Force sheet dimensions to be powers of two
            background: Background color for empty space
            
        Raises:
            ValueError: If parameters are invalid
        """
        if padding < 0:
            raise ValueError("Padding must be non-negative")
        if max_width <= 0 or max_height <= 0:
            raise ValueError("Max dimensions must be positive")
        if max_width > 4096 or max_height > 4096:
            raise ValueError("Max dimensions cannot exceed 4096")
        
        self.algorithm = algorithm
        self.padding = padding
        self.max_width = max_width
        self.max_height = max_height
        self.power_of_two = power_of_two
        self.background = background
    
    def pack(
        self,
        sprites: dict[str, PixelGrid],
        sort_by: Literal["width", "height", "area", "name"] = "area",
    ) -> SpriteSheet:
        """
        Pack sprites into a sprite sheet.
        
        Args:
            sprites: Dict mapping sprite names to PixelGrid objects
            sort_by: How to sort sprites before packing
            
        Returns:
            SpriteSheet: Packed sprite sheet
            
        Raises:
            ValueError: If sprites don't fit in max dimensions
            
        Example:
            >>> packer = SpriteSheetPacker()
            >>> sprites = {
            ...     "player": PixelGrid(16, 16),
            ...     "enemy": PixelGrid(24, 24),
            ... }
            >>> sheet = packer.pack(sprites)
        """
        if not sprites:
            raise ValueError("No sprites to pack")
        
        # Convert to SpriteFrame objects
        frames = [
            SpriteFrame(name=name, grid=grid)
            for name, grid in sprites.items()
        ]
        
        # Sort sprites
        frames = self._sort_frames(frames, sort_by)
        
        # Pack using selected algorithm
        if self.algorithm == PackingAlgorithm.ROW:
            packed_frames, width, height = self._pack_row(frames)
        elif self.algorithm == PackingAlgorithm.COLUMN:
            packed_frames, width, height = self._pack_column(frames)
        elif self.algorithm == PackingAlgorithm.GRID:
            packed_frames, width, height = self._pack_grid(frames)
        elif self.algorithm == PackingAlgorithm.SHELF:
            packed_frames, width, height = self._pack_shelf(frames)
        else:  # MAXRECTS
            packed_frames, width, height = self._pack_maxrects(frames)
        
        # Adjust dimensions to power of two if needed
        if self.power_of_two:
            width = self._next_power_of_two(width)
            height = self._next_power_of_two(height)
        
        return SpriteSheet(
            width=width,
            height=height,
            frames=packed_frames,
            padding=self.padding,
            background=self.background,
        )
    
    def _sort_frames(
        self,
        frames: list[SpriteFrame],
        sort_by: Literal["width", "height", "area", "name"],
    ) -> list[SpriteFrame]:
        """Sort frames by specified criteria."""
        if sort_by == "width":
            return sorted(frames, key=lambda f: f.width, reverse=True)
        elif sort_by == "height":
            return sorted(frames, key=lambda f: f.height, reverse=True)
        elif sort_by == "area":
            return sorted(frames, key=lambda f: f.width * f.height, reverse=True)
        else:  # name
            return sorted(frames, key=lambda f: f.name)
    
    def _pack_row(self, frames: list[SpriteFrame]) -> tuple[list[SpriteFrame], int, int]:
        """Pack sprites in a single row."""
        x = 0
        max_height = 0
        
        for frame in frames:
            frame.x = x
            frame.y = 0
            x += frame.width + self.padding
            max_height = max(max_height, frame.height)
        
        total_width = x - self.padding if frames else 0
        
        if total_width > self.max_width:
            raise ValueError(f"Sprites don't fit in row (width: {total_width} > {self.max_width})")
        
        return frames, total_width, max_height
    
    def _pack_column(self, frames: list[SpriteFrame]) -> tuple[list[SpriteFrame], int, int]:
        """Pack sprites in a single column."""
        y = 0
        max_width = 0
        
        for frame in frames:
            frame.x = 0
            frame.y = y
            y += frame.height + self.padding
            max_width = max(max_width, frame.width)
        
        total_height = y - self.padding if frames else 0
        
        if total_height > self.max_height:
            raise ValueError(f"Sprites don't fit in column (height: {total_height} > {self.max_height})")
        
        return frames, max_width, total_height
    
    def _pack_grid(self, frames: list[SpriteFrame]) -> tuple[list[SpriteFrame], int, int]:
        """Pack sprites in a grid layout."""
        if not frames:
            return frames, 0, 0
        
        # Calculate grid dimensions
        num_sprites = len(frames)
        cols = int(np.ceil(np.sqrt(num_sprites)))
        rows = int(np.ceil(num_sprites / cols))
        
        # Find max dimensions for uniform grid
        max_sprite_width = max(f.width for f in frames)
        max_sprite_height = max(f.height for f in frames)
        
        # Calculate cell size with padding
        cell_width = max_sprite_width + self.padding
        cell_height = max_sprite_height + self.padding
        
        # Position frames in grid
        for i, frame in enumerate(frames):
            col = i % cols
            row = i // cols
            frame.x = col * cell_width
            frame.y = row * cell_height
        
        total_width = cols * cell_width - self.padding
        total_height = rows * cell_height - self.padding
        
        if total_width > self.max_width or total_height > self.max_height:
            raise ValueError("Sprites don't fit in grid with max dimensions")
        
        return frames, total_width, total_height
    
    def _pack_shelf(self, frames: list[SpriteFrame]) -> tuple[list[SpriteFrame], int, int]:
        """Pack sprites using shelf algorithm (rows of varying heights)."""
        shelves: list[dict] = []  # List of shelves with current x, y, height
        max_width = 0
        total_height = 0
        
        for frame in frames:
            # Try to fit in existing shelves
            placed = False
            for shelf in shelves:
                if (shelf["x"] + frame.width <= self.max_width and
                    frame.height <= shelf["height"]):
                    # Fits in this shelf
                    frame.x = shelf["x"]
                    frame.y = shelf["y"]
                    shelf["x"] += frame.width + self.padding
                    max_width = max(max_width, shelf["x"] - self.padding)
                    placed = True
                    break
            
            if not placed:
                # Create new shelf
                new_y = total_height
                frame.x = 0
                frame.y = new_y
                
                new_shelf = {
                    "x": frame.width + self.padding,
                    "y": new_y,
                    "height": frame.height,
                }
                shelves.append(new_shelf)
                
                total_height += frame.height + self.padding
                max_width = max(max_width, frame.width)
        
        total_height = total_height - self.padding if shelves else 0
        
        if total_height > self.max_height:
            raise ValueError("Sprites don't fit using shelf packing")
        
        return frames, max_width, total_height
    
    def _pack_maxrects(self, frames: list[SpriteFrame]) -> tuple[list[SpriteFrame], int, int]:
        """Pack sprites using MaxRects algorithm for optimal space usage."""
        # Simplified MaxRects implementation
        # Start with one big rectangle
        free_rects = [{"x": 0, "y": 0, "width": self.max_width, "height": self.max_height}]
        max_x = 0
        max_y = 0
        
        for frame in frames:
            # Find best rect for this frame
            best_rect = None
            best_score = float("inf")
            
            for rect in free_rects:
                if frame.width <= rect["width"] and frame.height <= rect["height"]:
                    # Score based on leftover area (smaller is better)
                    leftover = (rect["width"] - frame.width) * (rect["height"] - frame.height)
                    if leftover < best_score:
                        best_score = leftover
                        best_rect = rect
            
            if best_rect is None:
                raise ValueError("Sprites don't fit using MaxRects packing")
            
            # Place frame in best rect
            frame.x = best_rect["x"]
            frame.y = best_rect["y"]
            max_x = max(max_x, frame.x + frame.width)
            max_y = max(max_y, frame.y + frame.height)
            
            # Split remaining space into new free rects
            new_rects = []
            
            # Right remainder
            if best_rect["width"] > frame.width:
                new_rects.append({
                    "x": best_rect["x"] + frame.width + self.padding,
                    "y": best_rect["y"],
                    "width": best_rect["width"] - frame.width - self.padding,
                    "height": frame.height,
                })
            
            # Bottom remainder
            if best_rect["height"] > frame.height:
                new_rects.append({
                    "x": best_rect["x"],
                    "y": best_rect["y"] + frame.height + self.padding,
                    "width": best_rect["width"],
                    "height": best_rect["height"] - frame.height - self.padding,
                })
            
            # Remove used rect and add new ones
            free_rects.remove(best_rect)
            free_rects.extend(new_rects)
        
        return frames, max_x, max_y
    
    @staticmethod
    def _next_power_of_two(n: int) -> int:
        """Round up to next power of two."""
        return 2 ** int(np.ceil(np.log2(n)))


class AnimationSheet:
    """
    Specialized sprite sheet for animation frames.
    
    Provides utilities for creating and exporting animation sprite sheets
    with metadata suitable for game engines.
    """
    
    def __init__(
        self,
        name: str,
        frames: list[PixelGrid],
        frame_duration: float = 0.1,
        loop: bool = True,
    ) -> None:
        """
        Initialize animation sheet.
        
        Args:
            name: Animation name
            frames: List of animation frames
            frame_duration: Duration of each frame in seconds
            loop: Whether animation should loop
        """
        if not frames:
            raise ValueError("Animation must have at least one frame")
        
        self.name = name
        self.frames = frames
        self.frame_duration = frame_duration
        self.loop = loop
    
    def to_sprite_sheet(
        self,
        packer: SpriteSheetPacker | None = None,
    ) -> SpriteSheet:
        """
        Convert animation to sprite sheet.
        
        Args:
            packer: Optional custom packer (defaults to ROW packing)
            
        Returns:
            SpriteSheet: Animation sprite sheet
        """
        if packer is None:
            packer = SpriteSheetPacker(algorithm=PackingAlgorithm.ROW)
        
        # Create sprites dict with frame numbers
        sprites = {
            f"{self.name}_{i:04d}": frame
            for i, frame in enumerate(self.frames)
        }
        
        return packer.pack(sprites, sort_by="name")
    
    def get_metadata(self) -> dict:
        """
        Get animation metadata.
        
        Returns:
            dict: Animation metadata
        """
        return {
            "name": self.name,
            "frame_count": len(self.frames),
            "frame_duration": self.frame_duration,
            "loop": self.loop,
            "total_duration": len(self.frames) * self.frame_duration,
        }


def create_texture_atlas(
    sprite_sheets: dict[str, SpriteSheet],
    output_path: Path | str,
    exporter: PNGExporter | None = None,
) -> tuple[Path, dict]:
    """
    Create a texture atlas from multiple sprite sheets.
    
    Combines multiple sprite sheets into a single texture with complete metadata.
    
    Args:
        sprite_sheets: Dict mapping atlas names to SpriteSheet objects
        output_path: Output PNG path
        exporter: Optional custom exporter
        
    Returns:
        tuple: (Path to PNG, combined metadata dict)
        
    Example:
        >>> sheets = {
        ...     "player": player_sheet,
        ...     "enemies": enemy_sheet,
        ... }
        >>> path, metadata = create_texture_atlas(sheets, "atlas.png")
    """
    if not sprite_sheets:
        raise ValueError("No sprite sheets to combine")
    
    if exporter is None:
        exporter = PNGExporter()
    
    # Pack all sheets into one
    all_sprites = {}
    for sheet_name, sheet in sprite_sheets.items():
        for frame in sheet.frames:
            sprite_name = f"{sheet_name}_{frame.name}"
            all_sprites[sprite_name] = frame.grid
    
    # Use MaxRects for optimal atlas packing
    packer = SpriteSheetPacker(algorithm=PackingAlgorithm.MAXRECTS)
    atlas_sheet = packer.pack(all_sprites)
    
    # Export atlas
    atlas_grid = atlas_sheet.to_grid()
    atlas_path = exporter.export(atlas_grid, output_path)
    
    # Combine metadata
    atlas_metadata = {
        "atlas_width": atlas_sheet.width,
        "atlas_height": atlas_sheet.height,
        "sprite_sheets": {
            name: sheet.get_metadata()
            for name, sheet in sprite_sheets.items()
        },
        "frames": atlas_sheet.get_metadata()["frames"],
    }
    
    return atlas_path, atlas_metadata