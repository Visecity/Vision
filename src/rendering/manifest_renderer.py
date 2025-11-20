"""
Manifest-to-PNG rendering functionality for Vision.

This module provides utilities to convert Vision Manifest JSON files into
rendered PNG images, handling both single sprites and animation frames.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from src.rendering.draw import DrawingContext
from src.rendering.export import PNGExporter
from src.rendering.pixel import Color, PixelGrid

logger = logging.getLogger(__name__)


class ManifestParseError(Exception):
    """Raised when manifest JSON structure is invalid."""

    pass


class ManifestRenderer:
    """
    Renders Manifest JSON to PNG images.

    Converts Vision's Manifest JSON DSL into rendered pixel art images,
    supporting both single sprites and animation sprite sheets.
    """

    def __init__(
        self,
        scale: int = 1,
        include_metadata: bool = True,
    ) -> None:
        """
        Initialize manifest renderer.

        Args:
            scale: Integer scaling factor for output PNG
            include_metadata: Whether to embed metadata in PNG

        Raises:
            ValueError: If scale is invalid
        """
        if scale < 1 or scale > 16:
            raise ValueError("Scale must be between 1 and 16")

        self.scale = scale
        self.include_metadata = include_metadata

    async def render_manifest_async(
        self,
        manifest: dict[str, Any],
        output_path: Path | str,
        transparent_color: Color | None = None,
    ) -> Path:
        """
        Render manifest to PNG asynchronously.

        Args:
            manifest: Vision Manifest JSON
            output_path: Output file path (can be with or without .png extension)
            transparent_color: Optional color to treat as transparent

        Returns:
            Path: Absolute path to rendered PNG file

        Raises:
            ManifestParseError: If manifest structure is invalid
            IOError: If file cannot be written

        Example:
            >>> renderer = ManifestRenderer()
            >>> manifest = {"metadata": {...}, "layers": [...]}
            >>> path = await renderer.render_manifest_async(
            ...     manifest,
            ...     "output/sprite.png"
            ... )
        """
        # Run rendering in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.render_manifest_sync,
            manifest,
            output_path,
            transparent_color,
        )

    def render_manifest_sync(
        self,
        manifest: dict[str, Any],
        output_path: Path | str,
        transparent_color: Color | None = None,
    ) -> Path:
        """
        Render manifest to PNG synchronously.

        Args:
            manifest: Vision Manifest JSON
            output_path: Output file path
            transparent_color: Optional color to treat as transparent

        Returns:
            Path: Absolute path to rendered PNG file

        Raises:
            ManifestParseError: If manifest structure is invalid
        """
        output_path = Path(output_path)
        
        # Ensure .png extension
        if output_path.suffix.lower() != ".png":
            output_path = output_path.with_suffix(".png")

        # Validate manifest structure
        self._validate_manifest(manifest)

        # Render to PixelGrid
        grid = self._render_to_grid(manifest)

        # Export to PNG
        exporter = PNGExporter(
            scale=self.scale,
            include_metadata=self.include_metadata,
        )

        metadata = self._extract_metadata(manifest) if self.include_metadata else None

        return exporter.export(
            grid,
            output_path,
            transparent_color=transparent_color,
            metadata=metadata,
        )

    def _validate_manifest(self, manifest: dict[str, Any]) -> None:
        """
        Validate manifest structure.

        Args:
            manifest: Manifest dict to validate

        Raises:
            ManifestParseError: If manifest is invalid
        """
        if not isinstance(manifest, dict):
            raise ManifestParseError("Manifest must be a dictionary")

        # Check for required fields
        if "metadata" not in manifest:
            raise ManifestParseError("Manifest missing 'metadata' field")

        metadata = manifest["metadata"]
        if "canvas" not in metadata:
            raise ManifestParseError("Manifest metadata missing 'canvas' field")

        canvas = metadata["canvas"]
        if "width" not in canvas or "height" not in canvas:
            raise ManifestParseError("Canvas missing 'width' or 'height' field")

        # Must have either layers or frames
        if "layers" not in manifest and "frames" not in manifest:
            raise ManifestParseError(
                "Manifest must have either 'layers' or 'frames' field"
            )

    def _render_to_grid(self, manifest: dict[str, Any]) -> PixelGrid:
        """
        Render manifest to PixelGrid.

        Args:
            manifest: Validated manifest dict

        Returns:
            PixelGrid: Rendered pixel grid

        Raises:
            ManifestParseError: If rendering fails
        """
        # Get canvas dimensions
        canvas = manifest["metadata"]["canvas"]
        width = canvas["width"]
        height = canvas["height"]

        # Create grid with transparent background
        grid = PixelGrid(width, height, background=Color(0, 0, 0))

        # Determine manifest type and render
        if "layers" in manifest:
            self._render_layers(grid, manifest["layers"])
        elif "frames" in manifest:
            self._render_frames(grid, manifest["frames"])

        return grid

    def _render_layers(
        self,
        grid: PixelGrid,
        layers: list[dict[str, Any]],
    ) -> None:
        """
        Render layer-based manifest.

        Args:
            grid: PixelGrid to render into
            layers: List of layer dicts with elements

        Raises:
            ManifestParseError: If layer rendering fails
        """
        ctx = DrawingContext(grid)

        for layer in layers:
            if "elements" not in layer:
                logger.warning(f"Layer '{layer.get('name', 'unnamed')}' has no elements")
                continue

            elements = layer["elements"]
            for element in elements:
                try:
                    self._render_element(ctx, element)
                except Exception as e:
                    logger.error(f"Failed to render element: {e}")
                    # Continue with other elements

    def _render_frames(
        self,
        grid: PixelGrid,
        frames: list[dict[str, Any]],
    ) -> None:
        """
        Render frame-based manifest.

        Args:
            grid: PixelGrid to render into
            frames: List of frame dicts

        Raises:
            ManifestParseError: If frame rendering fails
        """
        ctx = DrawingContext(grid)

        for frame in frames:
            if "elements" not in frame:
                logger.warning(f"Frame '{frame.get('name', 'unnamed')}' has no elements")
                continue

            elements = frame["elements"]
            for element in elements:
                try:
                    self._render_element(ctx, element)
                except Exception as e:
                    logger.error(f"Failed to render element: {e}")
                    # Continue with other elements

    def _render_element(
        self,
        ctx: DrawingContext,
        element: dict[str, Any],
    ) -> None:
        """
        Render a single element (shape) to the drawing context.

        Args:
            ctx: DrawingContext to render into
            element: Element dict with type, position, and properties

        Raises:
            ManifestParseError: If element is invalid
        """
        element_type = element.get("type")
        if not element_type:
            raise ManifestParseError("Element missing 'type' field")

        if element_type == "rect":
            self._render_rect(ctx, element)
        elif element_type == "circle":
            self._render_circle(ctx, element)
        elif element_type == "line":
            self._render_line(ctx, element)
        elif element_type == "pixel":
            self._render_pixel(ctx, element)
        else:
            logger.warning(f"Unknown element type: {element_type}")

    def _render_rect(
        self,
        ctx: DrawingContext,
        element: dict[str, Any],
    ) -> None:
        """Render a rectangle element."""
        x = element.get("x", 0)
        y = element.get("y", 0)
        width = element.get("width", 1)
        height = element.get("height", 1)
        fill = element.get("fill")

        if fill:
            color = self._parse_color(fill)
            ctx.draw_rect(x, y, width, height, color, filled=True)

    def _render_circle(
        self,
        ctx: DrawingContext,
        element: dict[str, Any],
    ) -> None:
        """Render a circle element."""
        cx = element.get("cx", 0)
        cy = element.get("cy", 0)
        radius = element.get("radius", 1)
        fill = element.get("fill")
        filled = element.get("filled", True)

        if fill:
            color = self._parse_color(fill)
            ctx.draw_circle(cx, cy, radius, color, filled=filled)

    def _render_line(
        self,
        ctx: DrawingContext,
        element: dict[str, Any],
    ) -> None:
        """Render a line element."""
        x1 = element.get("x1", 0)
        y1 = element.get("y1", 0)
        x2 = element.get("x2", 0)
        y2 = element.get("y2", 0)
        stroke = element.get("stroke")

        if stroke:
            color = self._parse_color(stroke)
            ctx.draw_line(x1, y1, x2, y2, color)

    def _render_pixel(
        self,
        ctx: DrawingContext,
        element: dict[str, Any],
    ) -> None:
        """Render a single pixel element."""
        x = element.get("x", 0)
        y = element.get("y", 0)
        fill = element.get("fill")

        if fill:
            color = self._parse_color(fill)
            ctx.draw_pixel(x, y, color)

    def _parse_color(self, color_string: str) -> Color:
        """
        Parse color string to Color object.

        Args:
            color_string: Hex color string (e.g., "#FF0000")

        Returns:
            Color: Parsed color

        Raises:
            ManifestParseError: If color is invalid
        """
        try:
            return Color.from_hex(color_string)
        except ValueError as e:
            raise ManifestParseError(f"Invalid color '{color_string}': {e}") from e

    def _extract_metadata(self, manifest: dict[str, Any]) -> dict[str, str]:
        """
        Extract metadata for PNG embedding.

        Args:
            manifest: Manifest dict

        Returns:
            dict: Metadata key-value pairs
        """
        metadata: dict[str, str] = {}

        # Add basic manifest info
        if "version" in manifest:
            metadata["vision_manifest_version"] = str(manifest["version"])

        manifest_meta = manifest.get("metadata", {})
        if "name" in manifest_meta:
            metadata["asset_name"] = str(manifest_meta["name"])
        if "description" in manifest_meta:
            metadata["asset_description"] = str(manifest_meta["description"])

        # Add canvas dimensions
        canvas = manifest_meta.get("canvas", {})
        if "width" in canvas and "height" in canvas:
            metadata["canvas_size"] = f"{canvas['width']}x{canvas['height']}"

        return metadata


def render_animation_frames(
    manifest: dict[str, Any],
    output_dir: Path | str,
    name_prefix: str = "frame",
    scale: int = 1,
    transparent_color: Color | None = None,
) -> list[Path]:
    """
    Render animation frames as individual PNG files.

    Extracts individual frames from an animation manifest and renders
    each to a separate PNG file.

    Args:
        manifest: Vision Manifest JSON with layers or frames
        output_dir: Output directory for frame PNGs
        name_prefix: Prefix for frame filenames
        scale: Integer scaling factor
        transparent_color: Optional color to treat as transparent

    Returns:
        list[Path]: List of rendered frame paths

    Raises:
        ManifestParseError: If manifest is invalid
        IOError: If files cannot be written

    Example:
        >>> manifest = load_manifest("animation.json")
        >>> frames = render_animation_frames(
        ...     manifest,
        ...     "output/frames",
        ...     "walk"
        ... )
        >>> # Creates: walk_0000.png, walk_0001.png, etc.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    renderer = ManifestRenderer(scale=scale, include_metadata=False)
    frames: list[Path] = []

    # Determine frame source
    frame_list = manifest.get("layers") or manifest.get("frames", [])

    for i, frame_data in enumerate(frame_list):
        # Create single-frame manifest
        single_frame_manifest = {
            "version": manifest.get("version", "1.0"),
            "metadata": manifest["metadata"],
            "layers": [frame_data],
        }

        # Generate filename
        frame_filename = f"{name_prefix}_{i:04d}.png"
        frame_path = output_dir / frame_filename

        # Render frame
        rendered_path = renderer.render_manifest_sync(
            single_frame_manifest,
            frame_path,
            transparent_color=transparent_color,
        )

        frames.append(rendered_path)
        logger.info(f"Rendered frame {i}: {rendered_path}")

    return frames


# Convenience function for quick rendering
def quick_render(
    manifest: dict[str, Any],
    output_path: Path | str,
    scale: int = 1,
    transparent_color: Color | None = None,
) -> Path:
    """
    Quick render function for simple use cases.

    Args:
        manifest: Vision Manifest JSON
        output_path: Output PNG path
        scale: Integer scaling factor
        transparent_color: Optional color to treat as transparent

    Returns:
        Path: Absolute path to rendered PNG

    Example:
        >>> manifest = {"metadata": {...}, "layers": [...]}
        >>> quick_render(manifest, "sprite.png", scale=2)
        PosixPath('/path/to/sprite.png')
    """
    renderer = ManifestRenderer(scale=scale, include_metadata=False)
    return renderer.render_manifest_sync(manifest, output_path, transparent_color)