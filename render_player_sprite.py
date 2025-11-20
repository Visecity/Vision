#!/usr/bin/env python3
"""Render Aris Phase 8.2 player sprite from JSON manifest."""

import json
from pathlib import Path
from src.rendering.pixel import PixelGrid, Color
from src.rendering.draw import DrawingContext
from src.rendering.export import PNGExporter

def hex_to_color(hex_str: str) -> Color:
    """Convert hex string to Color object."""
    hex_str = hex_str.lstrip('#')
    
    # Handle 3-digit hex codes (expand to 6 digits)
    if len(hex_str) == 3:
        hex_str = ''.join([c*2 for c in hex_str])
    
    # Ensure we have a 6-digit hex code
    if len(hex_str) != 6:
        raise ValueError(f"Invalid hex color: {hex_str}")
    
    return Color(
        int(hex_str[0:2], 16),
        int(hex_str[2:4], 16),
        int(hex_str[4:6], 16)
    )

def render_layer_based_manifest(manifest: dict) -> PixelGrid:
    """Convert a layer-based manifest to a PixelGrid."""
    # Get canvas dimensions from metadata
    canvas = manifest['metadata']['canvas']
    width = canvas['width']
    height = canvas['height']
    
    # Create grid with transparent background
    transparent_color = Color(255, 0, 255)  # Magenta = transparent
    grid = PixelGrid(width, height, background=transparent_color)
    
    # Create drawing context
    ctx = DrawingContext(grid)
    
    # Render each layer
    for layer in manifest['layers']:
        for element in layer['elements']:
            if element['type'] == 'rect':
                x = element['x']
                y = element['y']
                w = element['width']
                h = element['height']
                fill_color = hex_to_color(element['fill'])
                
                # Draw filled rectangle
                ctx.draw_rect(x, y, w, h, fill_color, filled=True)
    
    return grid

def render_player_sprite():
    """Render the player sprite from JSON manifest."""
    
    # Load manifest
    manifest_path = Path("Aris/phase-8-2/player_animated_32.json")
    
    if not manifest_path.exists():
        print(f"✗ Manifest not found: {manifest_path}")
        return None
    
    print(f"Loading manifest from: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Convert to grid
    print("Rendering layers...")
    grid = render_layer_based_manifest(manifest)
    
    # Export to PNG
    output_path = Path("Aris/phase-8-2/player_animated_32.png")
    
    # Use scale=1 for 1:1 pixel rendering
    exporter = PNGExporter(scale=1, include_metadata=True)
    
    transparent_color = Color(255, 0, 255)  # Magenta
    
    exporter.export(
        grid,
        output_path,
        transparent_color=transparent_color,
        metadata={
            'name': 'Aris Player Sprite',
            'dimensions': f"{grid.width}x{grid.height}",
            'description': '16x32 animated player character (2x4 frames)',
            'generated_by': 'Vision',
            'phase': '8.2'
        }
    )
    
    print(f"✓ Player sprite rendered: {output_path}")
    print(f"  Dimensions: {grid.width} × {grid.height} pixels")
    print(f"  Layout: 2 columns × 4 rows")
    print(f"  Frame Size: 16 × 32 per frame")
    
    return output_path

if __name__ == '__main__':
    render_player_sprite()