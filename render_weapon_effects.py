#!/usr/bin/env python3
"""Render weapon effects manifest to PNG"""

import json
import re
from PIL import Image

def parse_pixel_grid_row(row_desc):
    """Parse a row description"""
    pixels = []
    
    # Split by sections if present
    sections = row_desc.split('|') if '|' in row_desc else [row_desc]
    
    for section in sections:
        # Extract pixel data from brackets
        bracket_match = re.search(r'\[([^\]]+)\]', section)
        if not bracket_match:
            continue
            
        pixel_data = bracket_match.group(1)
        
        # Parse patterns like "t×4", "#2d2d2d×2", etc.
        patterns = re.findall(r'([#\w]+)(?:×(\d+))?', pixel_data)
        
        for color, count in patterns:
            count = int(count) if count else 1
            pixels.extend([color] * count)
    
    return pixels

def render_manifest(manifest_path, output_path):
    """Render manifest with pixel_grid format to PNG"""
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Get dimensions and pixel data
    pixel_grid = manifest['pixel_grid']
    width = pixel_grid['width']
    height = pixel_grid['height']
    rows = pixel_grid['data']
    
    # Create image
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    pixels = img.load()
    
    # Process each row
    for y, row_desc in enumerate(rows):
        if 'transparent' in row_desc or y >= height:
            continue
            
        row_pixels = parse_pixel_grid_row(row_desc)
        
        for x, color_str in enumerate(row_pixels):
            if x >= width:
                break
                
            # Handle transparent
            if color_str == 't' or 'transparent' in color_str:
                continue
            
            # Parse hex color
            if color_str.startswith('#'):
                color_hex = color_str[1:]
                if len(color_hex) == 6:
                    r = int(color_hex[0:2], 16)
                    g = int(color_hex[2:4], 16)
                    b = int(color_hex[4:6], 16)
                    pixels[x, y] = (r, g, b, 255)
    
    # Save
    img.save(output_path, 'PNG')
    print(f"✓ Rendered {width}x{height} weapon effects to {output_path}")

if __name__ == '__main__':
    render_manifest(
        'output/3011e8cb-c58f-4aa6-8678-1a54758f738f/manifest.json',
        'Aris/phase-8-3/weapon_effects.png'
    )
