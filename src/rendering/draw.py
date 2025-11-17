"""
Drawing primitives for Vision pixel art generation system.

This module provides utilities for drawing basic shapes, lines, and patterns
on PixelGrid objects using pixel-perfect algorithms suitable for pixel art.
"""

from typing import Callable

import numpy as np

from .pixel import Color, PixelGrid


class DrawingContext:
    """
    Context for drawing operations on a PixelGrid.
    
    Provides methods for drawing lines, circles, rectangles, and other shapes
    with pixel-perfect rendering suitable for pixel art.
    """
    
    def __init__(self, grid: PixelGrid) -> None:
        """
        Initialize drawing context.
        
        Args:
            grid: PixelGrid to draw on
        """
        self.grid = grid
    
    def draw_pixel(self, x: int, y: int, color: Color) -> None:
        """
        Draw a single pixel.
        
        Args:
            x: X coordinate
            y: Y coordinate
            color: Pixel color
        """
        if 0 <= x < self.grid.width and 0 <= y < self.grid.height:
            self.grid.set_pixel(x, y, color)
    
    def draw_line(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        color: Color,
    ) -> None:
        """
        Draw a line using Bresenham's algorithm.
        
        Args:
            x0: Start X coordinate
            y0: Start Y coordinate
            x1: End X coordinate
            y1: End Y coordinate
            color: Line color
            
        Example:
            >>> ctx = DrawingContext(PixelGrid(32, 32))
            >>> ctx.draw_line(0, 0, 31, 31, Color(255, 0, 0))
        """
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        x, y = x0, y0
        
        while True:
            self.draw_pixel(x, y, color)
            
            if x == x1 and y == y1:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
    
    def draw_rect(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: Color,
        filled: bool = False,
    ) -> None:
        """
        Draw a rectangle.
        
        Args:
            x: Top-left X coordinate
            y: Top-left Y coordinate
            width: Rectangle width
            height: Rectangle height
            color: Rectangle color
            filled: Whether to fill the rectangle
            
        Example:
            >>> ctx = DrawingContext(PixelGrid(32, 32))
            >>> ctx.draw_rect(8, 8, 16, 16, Color(0, 255, 0), filled=True)
        """
        if filled:
            # Fill rectangle
            for py in range(y, min(y + height, self.grid.height)):
                for px in range(x, min(x + width, self.grid.width)):
                    self.draw_pixel(px, py, color)
        else:
            # Draw outline
            # Top and bottom edges
            for px in range(x, min(x + width, self.grid.width)):
                self.draw_pixel(px, y, color)
                self.draw_pixel(px, y + height - 1, color)
            
            # Left and right edges
            for py in range(y, min(y + height, self.grid.height)):
                self.draw_pixel(x, py, color)
                self.draw_pixel(x + width - 1, py, color)
    
    def draw_circle(
        self,
        cx: int,
        cy: int,
        radius: int,
        color: Color,
        filled: bool = False,
    ) -> None:
        """
        Draw a circle using Bresenham's circle algorithm.
        
        Args:
            cx: Center X coordinate
            cy: Center Y coordinate
            radius: Circle radius
            color: Circle color
            filled: Whether to fill the circle
            
        Example:
            >>> ctx = DrawingContext(PixelGrid(32, 32))
            >>> ctx.draw_circle(16, 16, 8, Color(0, 0, 255), filled=True)
        """
        if radius <= 0:
            return
        
        if filled:
            # Filled circle
            for y in range(-radius, radius + 1):
                for x in range(-radius, radius + 1):
                    if x * x + y * y <= radius * radius:
                        self.draw_pixel(cx + x, cy + y, color)
        else:
            # Circle outline using midpoint algorithm
            x = radius
            y = 0
            err = 0
            
            while x >= y:
                self._plot_circle_points(cx, cy, x, y, color)
                
                if err <= 0:
                    y += 1
                    err += 2 * y + 1
                
                if err > 0:
                    x -= 1
                    err -= 2 * x + 1
    
    def _plot_circle_points(
        self,
        cx: int,
        cy: int,
        x: int,
        y: int,
        color: Color,
    ) -> None:
        """Plot 8 symmetric points of a circle."""
        self.draw_pixel(cx + x, cy + y, color)
        self.draw_pixel(cx - x, cy + y, color)
        self.draw_pixel(cx + x, cy - y, color)
        self.draw_pixel(cx - x, cy - y, color)
        self.draw_pixel(cx + y, cy + x, color)
        self.draw_pixel(cx - y, cy + x, color)
        self.draw_pixel(cx + y, cy - x, color)
        self.draw_pixel(cx - y, cy - x, color)
    
    def draw_ellipse(
        self,
        cx: int,
        cy: int,
        rx: int,
        ry: int,
        color: Color,
        filled: bool = False,
    ) -> None:
        """
        Draw an ellipse.
        
        Args:
            cx: Center X coordinate
            cy: Center Y coordinate
            rx: X radius
            ry: Y radius
            color: Ellipse color
            filled: Whether to fill the ellipse
        """
        if rx <= 0 or ry <= 0:
            return
        
        if filled:
            # Filled ellipse
            for y in range(-ry, ry + 1):
                for x in range(-rx, rx + 1):
                    if (x * x) / (rx * rx) + (y * y) / (ry * ry) <= 1:
                        self.draw_pixel(cx + x, cy + y, color)
        else:
            # Ellipse outline using midpoint algorithm
            # Region 1
            x = 0
            y = ry
            rx_sq = rx * rx
            ry_sq = ry * ry
            two_rx_sq = 2 * rx_sq
            two_ry_sq = 2 * ry_sq
            
            px = 0
            py = two_rx_sq * y
            
            # Plot initial points
            self._plot_ellipse_points(cx, cy, x, y, color)
            
            # Region 1
            p = int(ry_sq - (rx_sq * ry) + (0.25 * rx_sq))
            while px < py:
                x += 1
                px += two_ry_sq
                
                if p < 0:
                    p += ry_sq + px
                else:
                    y -= 1
                    py -= two_rx_sq
                    p += ry_sq + px - py
                
                self._plot_ellipse_points(cx, cy, x, y, color)
            
            # Region 2
            p = int(ry_sq * (x + 0.5) * (x + 0.5) + rx_sq * (y - 1) * (y - 1) - rx_sq * ry_sq)
            while y > 0:
                y -= 1
                py -= two_rx_sq
                
                if p > 0:
                    p += rx_sq - py
                else:
                    x += 1
                    px += two_ry_sq
                    p += rx_sq - py + px
                
                self._plot_ellipse_points(cx, cy, x, y, color)
    
    def _plot_ellipse_points(
        self,
        cx: int,
        cy: int,
        x: int,
        y: int,
        color: Color,
    ) -> None:
        """Plot 4 symmetric points of an ellipse."""
        self.draw_pixel(cx + x, cy + y, color)
        self.draw_pixel(cx - x, cy + y, color)
        self.draw_pixel(cx + x, cy - y, color)
        self.draw_pixel(cx - x, cy - y, color)
    
    def flood_fill(
        self,
        x: int,
        y: int,
        fill_color: Color,
        target_color: Color | None = None,
    ) -> None:
        """
        Flood fill an area with a color.
        
        Args:
            x: Starting X coordinate
            y: Starting Y coordinate
            fill_color: Color to fill with
            target_color: Color to replace (defaults to pixel at x, y)
            
        Example:
            >>> ctx = DrawingContext(PixelGrid(32, 32))
            >>> ctx.flood_fill(16, 16, Color(255, 0, 0))
        """
        if not (0 <= x < self.grid.width and 0 <= y < self.grid.height):
            return
        
        if target_color is None:
            target_color = self.grid.get_pixel(x, y)
        
        # Don't fill if target and fill colors are the same
        if target_color == fill_color:
            return
        
        # Stack-based flood fill to avoid recursion depth issues
        stack = [(x, y)]
        visited = set()
        
        while stack:
            px, py = stack.pop()
            
            if (px, py) in visited:
                continue
            
            if not (0 <= px < self.grid.width and 0 <= py < self.grid.height):
                continue
            
            current_color = self.grid.get_pixel(px, py)
            if current_color != target_color:
                continue
            
            # Fill this pixel
            self.grid.set_pixel(px, py, fill_color)
            visited.add((px, py))
            
            # Add neighbors to stack
            stack.extend([
                (px + 1, py),
                (px - 1, py),
                (px, py + 1),
                (px, py - 1),
            ])
    
    def draw_pattern(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        pattern_func: Callable[[int, int], Color],
    ) -> None:
        """
        Fill an area with a pattern generated by a function.
        
        Args:
            x: Top-left X coordinate
            y: Top-left Y coordinate
            width: Pattern width
            height: Pattern height
            pattern_func: Function that takes (x, y) and returns Color
            
        Example:
            >>> ctx = DrawingContext(PixelGrid(32, 32))
            >>> # Checkerboard pattern
            >>> def checker(x, y):
            ...     return Color(255, 255, 255) if (x + y) % 2 == 0 else Color(0, 0, 0)
            >>> ctx.draw_pattern(0, 0, 32, 32, checker)
        """
        for py in range(y, min(y + height, self.grid.height)):
            for px in range(x, min(x + width, self.grid.width)):
                color = pattern_func(px - x, py - y)
                self.draw_pixel(px, py, color)


class DitherPattern:
    """
    Dithering patterns for creating smooth gradients in pixel art.
    
    Provides various dithering algorithms for transitioning between colors
    with limited palettes.
    """
    
    @staticmethod
    def ordered_dither(
        grid: PixelGrid,
        color1: Color,
        color2: Color,
        threshold_map: list[list[int]] | None = None,
    ) -> None:
        """
        Apply ordered (Bayer) dithering to create gradient between two colors.
        
        Args:
            grid: PixelGrid to dither
            color1: First color
            color2: Second color
            threshold_map: Optional custom threshold map (uses 2x2 Bayer by default)
        """
        if threshold_map is None:
            # 2x2 Bayer matrix
            threshold_map = [
                [0, 2],
                [3, 1],
            ]
        
        map_height = len(threshold_map)
        map_width = len(threshold_map[0])
        max_threshold = map_height * map_width
        
        for y in range(grid.height):
            for x in range(grid.width):
                # Get threshold for this pixel
                threshold = threshold_map[y % map_height][x % map_width]
                
                # Calculate intensity (0.0 to 1.0)
                intensity = (x / grid.width + y / grid.height) / 2
                
                # Choose color based on intensity and threshold
                if intensity * max_threshold > threshold:
                    grid.set_pixel(x, y, color2)
                else:
                    grid.set_pixel(x, y, color1)
    
    @staticmethod
    def pattern_dither(
        grid: PixelGrid,
        colors: list[Color],
        pattern: str = "horizontal",
    ) -> None:
        """
        Apply pattern-based dithering.
        
        Args:
            grid: PixelGrid to dither
            colors: List of colors to use
            pattern: Pattern type ("horizontal", "vertical", "checkerboard")
        """
        if not colors:
            return
        
        for y in range(grid.height):
            for x in range(grid.width):
                if pattern == "horizontal":
                    color_idx = y % len(colors)
                elif pattern == "vertical":
                    color_idx = x % len(colors)
                elif pattern == "checkerboard":
                    color_idx = (x + y) % len(colors)
                else:
                    color_idx = 0
                
                grid.set_pixel(x, y, colors[color_idx])


class OutlineGenerator:
    """
    Generates outlines around sprites for pixel art.
    
    Useful for creating character/object outlines common in pixel art games.
    """
    
    @staticmethod
    def add_outline(
        grid: PixelGrid,
        outline_color: Color,
        transparent_color: Color | None = None,
        thickness: int = 1,
    ) -> PixelGrid:
        """
        Add an outline around non-transparent pixels.
        
        Args:
            grid: Source PixelGrid
            outline_color: Color for the outline
            transparent_color: Color to treat as transparent (None = use background)
            thickness: Outline thickness in pixels
            
        Returns:
            PixelGrid: New grid with outline added
            
        Example:
            >>> original = PixelGrid(16, 16)
            >>> outlined = OutlineGenerator.add_outline(
            ...     original,
            ...     Color(0, 0, 0),
            ...     thickness=1
            ... )
        """
        # Create new grid with padding for outline
        padding = thickness
        new_width = grid.width + (padding * 2)
        new_height = grid.height + (padding * 2)
        result = PixelGrid(new_width, new_height, background=transparent_color)
        
        # Copy original to center
        for y in range(grid.height):
            for x in range(grid.width):
                pixel = grid.get_pixel(x, y)
                if transparent_color is None or pixel != transparent_color:
                    result.set_pixel(x + padding, y + padding, pixel)
        
        # Add outline
        for y in range(grid.height):
            for x in range(grid.width):
                pixel = grid.get_pixel(x, y)
                
                # Check if this is a solid pixel
                if transparent_color is None or pixel != transparent_color:
                    # Check neighbors for transparent pixels
                    for dy in range(-thickness, thickness + 1):
                        for dx in range(-thickness, thickness + 1):
                            if dx == 0 and dy == 0:
                                continue
                            
                            nx = x + dx
                            ny = y + dy
                            
                            if 0 <= nx < grid.width and 0 <= ny < grid.height:
                                neighbor = grid.get_pixel(nx, ny)
                                if transparent_color is not None and neighbor == transparent_color:
                                    # This neighbor is transparent, add outline
                                    result.set_pixel(nx + padding, ny + padding, outline_color)
                            else:
                                # Edge of grid, add outline
                                if 0 <= nx + padding < new_width and 0 <= ny + padding < new_height:
                                    result.set_pixel(nx + padding, ny + padding, outline_color)
        
        return result


def create_gradient(
    width: int,
    height: int,
    color1: Color,
    color2: Color,
    direction: str = "horizontal",
) -> PixelGrid:
    """
    Create a gradient between two colors.
    
    Args:
        width: Grid width
        height: Grid height
        color1: Start color
        color2: End color
        direction: Gradient direction ("horizontal", "vertical", "diagonal")
        
    Returns:
        PixelGrid: Gradient grid
        
    Example:
        >>> gradient = create_gradient(32, 32, Color(255, 0, 0), Color(0, 0, 255))
    """
    grid = PixelGrid(width, height)
    
    for y in range(height):
        for x in range(width):
            # Calculate interpolation factor (0.0 to 1.0)
            if direction == "horizontal":
                t = x / (width - 1) if width > 1 else 0
            elif direction == "vertical":
                t = y / (height - 1) if height > 1 else 0
            elif direction == "diagonal":
                t = (x + y) / (width + height - 2) if width + height > 2 else 0
            else:
                t = 0
            
            # Interpolate RGB values
            r = int(color1.r + (color2.r - color1.r) * t)
            g = int(color1.g + (color2.g - color1.g) * t)
            b = int(color1.b + (color2.b - color1.b) * t)
            
            grid.set_pixel(x, y, Color(r, g, b))
    
    return grid