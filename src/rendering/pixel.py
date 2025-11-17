"""
Basic pixel utilities for Vision pixel art generation system.

This module provides fundamental pixel art utilities including color management,
palette operations, and basic grid operations. The full rendering engine will
be built in Phase 3.
"""

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class Color:
    """
    Immutable color representation with RGB values.

    Supports conversion between RGB tuples and hex strings, with
    validation to ensure values are within valid ranges.
    """

    r: int
    g: int
    b: int

    def __post_init__(self) -> None:
        """Validate RGB values are in valid range."""
        for value, name in [(self.r, "r"), (self.g, "g"), (self.b, "b")]:
            if not 0 <= value <= 255:
                raise ValueError(f"Color {name} value must be 0-255, got {value}")

    @property
    def rgb(self) -> tuple[int, int, int]:
        """Get RGB tuple."""
        return (self.r, self.g, self.b)

    @property
    def hex(self) -> str:
        """
        Convert to hex string format.

        Returns:
            str: Hex color string (e.g., '#FF5733')
        """
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"

    @classmethod
    def from_hex(cls, hex_string: str) -> "Color":
        """
        Create Color from hex string.

        Args:
            hex_string: Hex color string (e.g., '#FF5733' or 'FF5733')

        Returns:
            Color: Color instance

        Raises:
            ValueError: If hex string is invalid

        Example:
            >>> color = Color.from_hex('#FF5733')
            >>> color.rgb
            (255, 87, 51)
        """
        # Remove # if present
        hex_string = hex_string.lstrip("#")

        # Handle shorthand hex (e.g., 'FFF' -> 'FFFFFF')
        if len(hex_string) == 3:
            hex_string = "".join(c * 2 for c in hex_string)

        if len(hex_string) != 6:
            raise ValueError(f"Invalid hex color string: {hex_string}")

        try:
            r = int(hex_string[0:2], 16)
            g = int(hex_string[2:4], 16)
            b = int(hex_string[4:6], 16)
            return cls(r, g, b)
        except ValueError as e:
            raise ValueError(f"Invalid hex color string: {hex_string}") from e

    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> "Color":
        """
        Create Color from RGB values.

        Args:
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)

        Returns:
            Color: Color instance
        """
        return cls(r, g, b)

    def distance_to(self, other: "Color") -> float:
        """
        Calculate Euclidean distance to another color in RGB space.

        Args:
            other: Another color

        Returns:
            float: Distance between colors

        Example:
            >>> c1 = Color(255, 0, 0)
            >>> c2 = Color(0, 255, 0)
            >>> c1.distance_to(c2)
            360.62445840513925
        """
        return float(
            np.sqrt((self.r - other.r) ** 2 + (self.g - other.g) ** 2 + (self.b - other.b) ** 2)
        )

    def __repr__(self) -> str:
        """String representation."""
        return f"Color({self.r}, {self.g}, {self.b})"

    def __str__(self) -> str:
        """Human-readable string."""
        return self.hex


class Palette:
    """
    Color palette manager for pixel art.

    Manages a collection of colors with utilities for finding closest matches,
    color quantization, and palette validation.
    """

    def __init__(self, name: str, colors: list[Color]) -> None:
        """
        Initialize palette.

        Args:
            name: Palette name
            colors: List of colors in the palette

        Raises:
            ValueError: If palette has no colors or too many colors
        """
        if not colors:
            raise ValueError("Palette must have at least one color")
        if len(colors) > 256:
            raise ValueError("Palette cannot have more than 256 colors")

        self.name = name
        self._colors = colors
        self._color_set = set(colors)

    @property
    def colors(self) -> list[Color]:
        """Get list of colors in palette."""
        return self._colors.copy()

    @property
    def size(self) -> int:
        """Get number of colors in palette."""
        return len(self._colors)

    def contains(self, color: Color) -> bool:
        """
        Check if palette contains a color.

        Args:
            color: Color to check

        Returns:
            bool: True if color is in palette
        """
        return color in self._color_set

    def find_closest(self, color: Color) -> Color:
        """
        Find closest color in palette to given color.

        Uses Euclidean distance in RGB space.

        Args:
            color: Target color

        Returns:
            Color: Closest color from palette

        Example:
            >>> palette = Palette("basic", [Color(0, 0, 0), Color(255, 255, 255)])
            >>> palette.find_closest(Color(100, 100, 100))
            Color(0, 0, 0)
        """
        return min(self._colors, key=lambda c: color.distance_to(c))

    def quantize_colors(self, colors: list[Color]) -> list[Color]:
        """
        Quantize a list of colors to palette colors.

        Maps each color to its closest match in the palette.

        Args:
            colors: List of colors to quantize

        Returns:
            list[Color]: Quantized colors from palette
        """
        return [self.find_closest(color) for color in colors]

    def to_hex_list(self) -> list[str]:
        """
        Convert palette to list of hex strings.

        Returns:
            list[str]: List of hex color strings
        """
        return [color.hex for color in self._colors]

    @classmethod
    def from_hex_list(cls, name: str, hex_colors: list[str]) -> "Palette":
        """
        Create palette from list of hex strings.

        Args:
            name: Palette name
            hex_colors: List of hex color strings

        Returns:
            Palette: New palette instance

        Example:
            >>> palette = Palette.from_hex_list("web", ["#FF0000", "#00FF00", "#0000FF"])
            >>> palette.size
            3
        """
        colors = [Color.from_hex(hex_color) for hex_color in hex_colors]
        return cls(name, colors)

    def __repr__(self) -> str:
        """String representation."""
        return f"Palette(name={self.name!r}, size={self.size})"

    def __len__(self) -> int:
        """Get palette size."""
        return self.size


class Coordinate:
    """
    2D coordinate with validation.

    Immutable coordinate representation with bounds checking.
    """

    def __init__(self, x: int, y: int, width: int = 512, height: int = 512) -> None:
        """
        Initialize coordinate.

        Args:
            x: X coordinate
            y: Y coordinate
            width: Maximum width for validation
            height: Maximum height for validation

        Raises:
            ValueError: If coordinates are out of bounds
        """
        if x < 0 or x >= width:
            raise ValueError(f"X coordinate {x} out of bounds [0, {width})")
        if y < 0 or y >= height:
            raise ValueError(f"Y coordinate {y} out of bounds [0, {height})")

        self._x = x
        self._y = y
        self._width = width
        self._height = height

    @property
    def x(self) -> int:
        """Get X coordinate."""
        return self._x

    @property
    def y(self) -> int:
        """Get Y coordinate."""
        return self._y

    def __repr__(self) -> str:
        """String representation."""
        return f"Coordinate({self.x}, {self.y})"

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, Coordinate):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((self.x, self.y))


class PixelGrid:
    """
    Basic pixel grid for storing and manipulating pixel data.

    Represents a 2D grid of colors with utilities for getting/setting pixels
    and basic operations.
    """

    def __init__(self, width: int, height: int, background: Color | None = None) -> None:
        """
        Initialize pixel grid.

        Args:
            width: Grid width in pixels
            height: Grid height in pixels
            background: Optional background color (defaults to transparent black)

        Raises:
            ValueError: If dimensions are invalid
        """
        if width <= 0 or height <= 0:
            raise ValueError("Grid dimensions must be positive")
        if width > 512 or height > 512:
            raise ValueError("Grid dimensions cannot exceed 512x512")

        self.width = width
        self.height = height
        self._background = background or Color(0, 0, 0)

        # Initialize grid as numpy array for efficiency
        # Shape: (height, width, 3) for RGB values
        self._grid: NDArray[np.uint8] = np.zeros((height, width, 3), dtype=np.uint8)
        self._grid[:, :] = self._background.rgb

    def get_pixel(self, x: int, y: int) -> Color:
        """
        Get color at specified coordinate.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Color: Color at coordinate

        Raises:
            ValueError: If coordinates are out of bounds
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise ValueError(f"Coordinates ({x}, {y}) out of bounds")

        r, g, b = self._grid[y, x]
        return Color(int(r), int(g), int(b))

    def set_pixel(self, x: int, y: int, color: Color) -> None:
        """
        Set color at specified coordinate.

        Args:
            x: X coordinate
            y: Y coordinate
            color: Color to set

        Raises:
            ValueError: If coordinates are out of bounds
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise ValueError(f"Coordinates ({x}, {y}) out of bounds")

        self._grid[y, x] = color.rgb

    def fill(self, color: Color) -> None:
        """
        Fill entire grid with a color.

        Args:
            color: Color to fill with
        """
        self._grid[:, :] = color.rgb

    def clear(self) -> None:
        """Clear grid to background color."""
        self.fill(self._background)

    def to_numpy(self) -> NDArray[np.uint8]:
        """
        Get grid as numpy array.

        Returns:
            NDArray: RGB array with shape (height, width, 3)
        """
        return self._grid.copy()

    @classmethod
    def from_numpy(cls, array: NDArray[np.uint8]) -> "PixelGrid":
        """
        Create grid from numpy array.

        Args:
            array: RGB array with shape (height, width, 3)

        Returns:
            PixelGrid: New grid instance

        Raises:
            ValueError: If array has invalid shape
        """
        if array.ndim != 3 or array.shape[2] != 3:
            raise ValueError("Array must have shape (height, width, 3)")

        height, width = array.shape[0], array.shape[1]
        grid = cls(width, height)
        grid._grid = array.copy()
        return grid

    def __repr__(self) -> str:
        """String representation."""
        return f"PixelGrid(width={self.width}, height={self.height})"


# TODO: Phase 3 - Add advanced color operations (gradients, blending)
# TODO: Phase 3 - Add drawing primitives (lines, circles, rectangles)
# TODO: Phase 3 - Add flood fill and selection tools
# TODO: Phase 3 - Add dithering algorithms
# TODO: Phase 3 - Add sprite sheet utilities (packing, unpacking)
# TODO: Phase 4 - Add anti-aliasing options
# TODO: Phase 4 - Add layer support for compositing