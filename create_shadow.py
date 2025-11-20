#!/usr/bin/env python3
"""Create shadow.png for Aris Phase 8.2 player sprite."""

from pathlib import Path
from src.rendering.pixel import PixelGrid, Color
from src.rendering.draw import DrawingContext
from src.rendering.export import PNGExporter

def create_shadow():
    """Create a 16×8 semi-transparent black oval shadow."""
    
    # Create 16×8 grid with transparent background
    # Using magenta as transparent color marker
    transparent_color = Color(255, 0, 255)
    grid = PixelGrid(16, 8, background=transparent_color)
    
    # Create drawing context
    ctx = DrawingContext(grid)
    
    # Draw filled ellipse
    # Center: (8, 4) - middle of 16×8 grid
    # Radii: 7 horizontal (almost full width), 3 vertical (almost full height)
    shadow_color = Color(0, 0, 0)  # Black (we'll handle alpha via transparency in export)
    ctx.draw_ellipse(
        cx=7,  # Center X (0-indexed, so 7 is center of 16 pixels)
        cy=3,  # Center Y (0-indexed, so 3 is center of 8 pixels)
        rx=7,  # Horizontal radius
        ry=3,  # Vertical radius
        color=shadow_color,
        filled=True
    )
    
    # Create output directory
    output_dir = Path("Aris/phase-8-2")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Export to PNG (no scaling needed, 1:1 pixel size)
    exporter = PNGExporter(scale=1, include_metadata=True)
    output_path = output_dir / "shadow.png"
    
    exporter.export(
        grid,
        output_path,
        transparent_color=transparent_color,
        metadata={
            'name': 'Aris Player Shadow',
            'dimensions': '16x8',
            'description': 'Semi-transparent black oval shadow',
            'generated_by': 'Vision',
            'phase': '8.2'
        }
    )
    
    print(f"✓ Shadow created: {output_path}")
    print(f"  Dimensions: 16 × 8 pixels")
    print(f"  Shape: Horizontal oval/ellipse")
    print(f"  Color: Black with transparency")
    
    return output_path

if __name__ == '__main__':
    create_shadow()