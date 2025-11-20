#!/usr/bin/env python3
"""Render Phase 8.2 player sprite and shadow from manifest files."""

import json
from pathlib import Path
from src.rendering.pixel import PixelGrid, Color
from src.rendering.export import PNGExporter

def parse_opacity_color(color_code: str, hex_mapping: dict) -> tuple[int, int, int, int]:
    """Parse color code to RGBA tuple."""
    color_str = hex_mapping[color_code]
    
    # Handle transparent
    if "transparent" in color_str:
        return (0, 0, 0, 0)
    
    # Split by / to get the hex part if format is "rgba(...)/hex"
    if "/" in color_str:
        parts = color_str.split("/")
        # Use the hex part (after /)
        hex_color = parts[1].lstrip("#")
    elif color_str.startswith("rgba"):
        # Parse rgba(0,0,0,0.25) format
        rgba_str = color_str.replace("rgba(", "").replace(")", "")
        rgba = rgba_str.split(",")
        r = int(rgba[0])
        g = int(rgba[1])
        b = int(rgba[2])
        a = int(float(rgba[3]) * 255)
        return (r, g, b, a)
    else:
        # Pure hex format
        hex_color = color_str.lstrip("#")
    
    # Parse hex color with alpha
    if len(hex_color) == 8:  # RRGGBBAA
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        a = int(hex_color[6:8], 16)
        return (r, g, b, a)
    elif len(hex_color) == 6:  # RRGGBB (opaque)
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b, 255)
    
    return (0, 0, 0, 0)

def render_shadow_manifest(manifest_path: Path) -> Path:
    """Render shadow manifest to PNG."""
    print(f"\n📄 Rendering shadow: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Get dimensions
    width = manifest['pixel_grid']['width']
    height = manifest['pixel_grid']['height']
    data = manifest['pixel_grid']['data']
    hex_mapping = manifest['pixel_grid']['hex_mapping']
    
    print(f"  Dimensions: {width}×{height}")
    
    # Create RGBA image array
    import numpy as np
    rgba_array = np.zeros((height, width, 4), dtype=np.uint8)
    
    # Fill pixel data
    for y, row in enumerate(data):
        for x, code in enumerate(row):
            r, g, b, a = parse_opacity_color(code, hex_mapping)
            rgba_array[y, x] = [r, g, b, a]
    
    # Create grid from array
    from PIL import Image
    image = Image.fromarray(rgba_array, mode='RGBA')
    
    # Save PNG
    output_path = manifest_path.parent / f"{manifest_path.stem}.png"
    image.save(output_path, "PNG")
    
    print(f"  ✓ Saved: {output_path}")
    print(f"  File size: {output_path.stat().st_size} bytes")
    
    return output_path

def render_player_sprite_manifest(manifest_path: Path) -> Path:
    """Render conceptual player sprite manifest to PNG."""
    print(f"\n📄 Rendering player sprite: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Get dimensions
    width = manifest['pixel_grid']['width']
    height = manifest['pixel_grid']['height']
    
    print(f"  Dimensions: {width}×{height}")
    print(f"  Note: This is a conceptual manifest (descriptive, not pixel-perfect)")
    
    # Parse colors from final_specs
    color_map = {}
    for color_desc in manifest['final_specs']['colors_used']:
        parts = color_desc.split(" ")
        hex_color = parts[0]
        color_map[hex_color] = hex_color
    
    # Create a placeholder visualization
    # Since this manifest is conceptual/descriptive, we'll create a simple representation
    import numpy as np
    from PIL import Image
    
    # Create blank transparent image
    rgba_array = np.zeros((height, width, 4), dtype=np.uint8)
    
    # Add note that this is conceptual
    print("  ⚠️  This manifest contains descriptive pixel maps, not exact coordinates")
    print("  Creating placeholder representation...")
    
    # For now, create a grid pattern to show dimensions
    for y in range(height):
        for x in range(width):
            if x % 16 == 0 or y == 0 or y == height-1:
                rgba_array[y, x] = [100, 100, 100, 255]  # Gray grid lines
    
    image = Image.fromarray(rgba_array, mode='RGBA')
    
    # Save PNG
    output_path = manifest_path.parent / f"{manifest_path.stem}_placeholder.png"
    image.save(output_path, "PNG")
    
    print(f"  ✓ Saved placeholder: {output_path}")
    print(f"  File size: {output_path.stat().st_size} bytes")
    print(f"  ℹ️  Full rendering requires interpreting the descriptive pixel_map")
    
    return output_path

def main():
    """Render both Phase 8.2 assets."""
    print("=" * 60)
    print("Vision Phase 8.2 Asset Renderer")
    print("=" * 60)
    
    # Asset 1: Player Sprite
    player_manifest = Path("output/ec6c0626-8a1d-40b9-98ef-48d2e8db9f56/manifest.json")
    if player_manifest.exists():
        try:
            player_png = render_player_sprite_manifest(player_manifest)
        except Exception as e:
            print(f"  ✗ Error rendering player sprite: {e}")
    else:
        print(f"  ✗ Player manifest not found: {player_manifest}")
    
    # Asset 2: Shadow
    shadow_manifest = Path("output/75ec9846-1f53-496c-95a8-e9ba846db40c/manifest.json")
    if shadow_manifest.exists():
        try:
            shadow_png = render_shadow_manifest(shadow_manifest)
        except Exception as e:
            print(f"  ✗ Error rendering shadow: {e}")
    else:
        print(f"  ✗ Shadow manifest not found: {shadow_manifest}")
    
    print("\n" + "=" * 60)
    print("✓ Rendering complete")
    print("=" * 60)

if __name__ == '__main__':
    main()