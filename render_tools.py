#!/usr/bin/env python3
"""Render tools manifest to PNG for Aris Phase 8.3"""

import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw

def render_manifest_to_png(manifest_path: str, output_path: str):
    """Render a manifest JSON to PNG image"""
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Get dimensions
    width = manifest['metadata']['dimensions']['width']
    height = manifest['metadata']['dimensions']['height']
    
    # Create image with transparency
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    pixels = image.load()
    
    # Render each pixel from manifest
    for pixel_data in manifest['pixels']:
        x = pixel_data['x']
        y = pixel_data['y']
        color = pixel_data['color']
        
        # Convert hex color to RGBA tuple
        if color.startswith('#'):
            color = color[1:]
        
        if len(color) == 6:  # RGB
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            a = 255
        elif len(color) == 8:  # RGBA
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            a = int(color[6:8], 16)
        else:
            continue
        
        pixels[x, y] = (r, g, b, a)
    
    # Save as PNG
    image.save(output_path, 'PNG')
    print(f"✓ Rendered {width}x{height} image to {output_path}")
    return image

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python render_tools.py <manifest_path> [output_path]")
        sys.exit(1)
    
    manifest_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else manifest_path.replace('.json', '.png')
    
    render_manifest_to_png(manifest_path, output_path)
