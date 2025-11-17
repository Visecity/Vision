"""
PNG export functionality for Vision pixel art generation system.

This module provides utilities for exporting PixelGrid objects to PNG files
with support for transparency, scaling, and metadata embedding.
"""

from pathlib import Path
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from PIL import Image, PngImagePlugin

from .pixel import Color, PixelGrid


class PNGExporter:
    """
    Exports PixelGrid objects to PNG files.
    
    Supports transparency, integer scaling (for pixel-perfect upscaling),
    and metadata embedding for tracking generation parameters.
    """
    
    def __init__(
        self,
        scale: int = 1,
        include_metadata: bool = True,
    ) -> None:
        """
        Initialize PNG exporter.
        
        Args:
            scale: Integer scaling factor (1 = original size, 2 = 2x size, etc.)
            include_metadata: Whether to embed generation metadata in PNG
            
        Raises:
            ValueError: If scale is invalid
        """
        if scale < 1:
            raise ValueError("Scale must be at least 1")
        if scale > 16:
            raise ValueError("Scale cannot exceed 16 (too large)")
            
        self.scale = scale
        self.include_metadata = include_metadata
    
    def export(
        self,
        grid: PixelGrid,
        output_path: Path | str,
        transparent_color: Color | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Path:
        """
        Export PixelGrid to PNG file.
        
        Args:
            grid: PixelGrid to export
            output_path: Output file path
            transparent_color: Optional color to treat as transparent
            metadata: Optional metadata dict to embed in PNG
            
        Returns:
            Path: Absolute path to exported file
            
        Example:
            >>> grid = PixelGrid(16, 16)
            >>> exporter = PNGExporter(scale=2)
            >>> exporter.export(grid, "sprite.png")
            PosixPath('/path/to/sprite.png')
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get pixel data as numpy array
        rgb_array = grid.to_numpy()
        
        # Add alpha channel if transparent color specified
        if transparent_color is not None:
            rgba_array = self._add_alpha_channel(rgb_array, transparent_color)
            image = Image.fromarray(rgba_array, mode="RGBA")
        else:
            image = Image.fromarray(rgb_array, mode="RGB")
        
        # Apply scaling if needed (nearest neighbor for pixel-perfect)
        if self.scale > 1:
            new_size = (grid.width * self.scale, grid.height * self.scale)
            image = image.resize(new_size, Image.NEAREST)
        
        # Prepare PNG metadata
        png_info = None
        if self.include_metadata and metadata:
            png_info = PngImagePlugin.PngInfo()
            for key, value in metadata.items():
                png_info.add_text(key, str(value))
        
        # Save PNG
        image.save(output_path, "PNG", pnginfo=png_info)
        
        return output_path.absolute()
    
    def export_with_border(
        self,
        grid: PixelGrid,
        output_path: Path | str,
        border_size: int = 1,
        border_color: Color = Color(0, 0, 0),
        transparent_color: Color | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Path:
        """
        Export PixelGrid with a colored border.
        
        Useful for sprites that need clear boundaries or for debugging.
        
        Args:
            grid: PixelGrid to export
            output_path: Output file path
            border_size: Border width in pixels
            border_color: Color of the border
            transparent_color: Optional color to treat as transparent
            metadata: Optional metadata dict to embed in PNG
            
        Returns:
            Path: Absolute path to exported file
        """
        # Create new grid with border
        new_width = grid.width + (border_size * 2)
        new_height = grid.height + (border_size * 2)
        bordered_grid = PixelGrid(new_width, new_height, background=border_color)
        
        # Copy original grid to center
        original_array = grid.to_numpy()
        bordered_array = bordered_grid.to_numpy()
        bordered_array[
            border_size:border_size + grid.height,
            border_size:border_size + grid.width,
            :
        ] = original_array
        
        # Create new grid from modified array
        final_grid = PixelGrid.from_numpy(bordered_array)
        
        # Export with border
        return self.export(final_grid, output_path, transparent_color, metadata)
    
    @staticmethod
    def _add_alpha_channel(
        rgb_array: NDArray[np.uint8],
        transparent_color: Color,
    ) -> NDArray[np.uint8]:
        """
        Add alpha channel to RGB array, making specified color transparent.
        
        Args:
            rgb_array: RGB array with shape (height, width, 3)
            transparent_color: Color to make transparent
            
        Returns:
            NDArray: RGBA array with shape (height, width, 4)
        """
        height, width = rgb_array.shape[0], rgb_array.shape[1]
        rgba_array = np.zeros((height, width, 4), dtype=np.uint8)
        
        # Copy RGB channels
        rgba_array[:, :, :3] = rgb_array
        
        # Set alpha channel (255 = opaque, 0 = transparent)
        # Create mask where color matches transparent_color
        mask = np.all(rgb_array == transparent_color.rgb, axis=2)
        rgba_array[:, :, 3] = np.where(mask, 0, 255)
        
        return rgba_array


class BatchExporter:
    """
    Batch export multiple grids to PNG files.
    
    Useful for exporting animation frames, sprite variations,
    or multiple assets in one operation.
    """
    
    def __init__(self, exporter: PNGExporter) -> None:
        """
        Initialize batch exporter.
        
        Args:
            exporter: PNGExporter instance to use for all exports
        """
        self.exporter = exporter
    
    def export_sequence(
        self,
        grids: list[PixelGrid],
        output_dir: Path | str,
        name_prefix: str = "frame",
        name_suffix: str = "",
        start_index: int = 0,
        transparent_color: Color | None = None,
        metadata: dict[str, str] | None = None,
    ) -> list[Path]:
        """
        Export sequence of grids with numbered filenames.
        
        Args:
            grids: List of PixelGrid objects to export
            output_dir: Output directory
            name_prefix: Filename prefix (default: "frame")
            name_suffix: Filename suffix (default: "")
            start_index: Starting index for numbering (default: 0)
            transparent_color: Optional color to treat as transparent
            metadata: Optional metadata dict to embed in all PNGs
            
        Returns:
            list[Path]: List of exported file paths
            
        Example:
            >>> grids = [PixelGrid(16, 16) for _ in range(4)]
            >>> batch = BatchExporter(PNGExporter())
            >>> batch.export_sequence(grids, "output", "walk")
            [PosixPath('output/walk_0000.png'), ...]
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        paths: list[Path] = []
        
        for i, grid in enumerate(grids):
            # Create zero-padded filename
            index = start_index + i
            padding = max(4, len(str(len(grids) + start_index)))
            filename = f"{name_prefix}_{index:0{padding}d}{name_suffix}.png"
            filepath = output_dir / filename
            
            # Add frame number to metadata
            frame_metadata = metadata.copy() if metadata else {}
            frame_metadata["frame_number"] = str(index)
            
            # Export
            exported_path = self.exporter.export(
                grid,
                filepath,
                transparent_color=transparent_color,
                metadata=frame_metadata,
            )
            paths.append(exported_path)
        
        return paths
    
    def export_variations(
        self,
        grids: dict[str, PixelGrid],
        output_dir: Path | str,
        transparent_color: Color | None = None,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Path]:
        """
        Export named variations of a sprite.
        
        Args:
            grids: Dict mapping variation names to PixelGrid objects
            output_dir: Output directory
            transparent_color: Optional color to treat as transparent
            metadata: Optional metadata dict to embed in all PNGs
            
        Returns:
            dict[str, Path]: Dict mapping variation names to file paths
            
        Example:
            >>> grids = {
            ...     "idle": PixelGrid(16, 16),
            ...     "walk": PixelGrid(16, 16),
            ...     "jump": PixelGrid(16, 16),
            ... }
            >>> batch = BatchExporter(PNGExporter())
            >>> batch.export_variations(grids, "output")
            {'idle': PosixPath('output/idle.png'), ...}
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        paths: dict[str, Path] = {}
        
        for name, grid in grids.items():
            filepath = output_dir / f"{name}.png"
            
            # Add variation name to metadata
            var_metadata = metadata.copy() if metadata else {}
            var_metadata["variation"] = name
            
            # Export
            exported_path = self.exporter.export(
                grid,
                filepath,
                transparent_color=transparent_color,
                metadata=var_metadata,
            )
            paths[name] = exported_path
        
        return paths


def quick_export(
    grid: PixelGrid,
    output_path: Path | str,
    scale: int = 1,
    transparent_color: Color | None = None,
) -> Path:
    """
    Quick export function for simple use cases.
    
    Args:
        grid: PixelGrid to export
        output_path: Output file path
        scale: Integer scaling factor
        transparent_color: Optional color to treat as transparent
        
    Returns:
        Path: Absolute path to exported file
        
    Example:
        >>> grid = PixelGrid(16, 16)
        >>> quick_export(grid, "sprite.png", scale=2)
        PosixPath('/path/to/sprite.png')
    """
    exporter = PNGExporter(scale=scale, include_metadata=False)
    return exporter.export(grid, output_path, transparent_color=transparent_color)