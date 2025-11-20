#!/usr/bin/env python3
"""Render Mario and Zelda-style manifests to PNG files."""

import json
import os
from pathlib import Path
from src.rendering.pixel import PixelGrid, Color
from src.rendering.export import PNGExporter

def load_manifest(manifest_path: str) -> dict:
    """Load a manifest JSON file."""
    with open(manifest_path, 'r') as f:
        return json.load(f)

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

def render_manifest_to_grid(manifest: dict) -> PixelGrid:
    """Convert a manifest to a PixelGrid."""
    pixel_grid_data = manifest['pixel_grid']
    width = pixel_grid_data['width']
    height = pixel_grid_data['height']
    data = pixel_grid_data['data']
    
    # Create grid with transparent background
    grid = PixelGrid(width, height, background=Color(255, 0, 255))  # Magenta = transparent
    
    # Draw each pixel from the 2D data array
    for y, row in enumerate(data):
        for x, pixel_value in enumerate(row):
            if pixel_value != 'T':  # 'T' means transparent
                try:
                    color = hex_to_color(pixel_value)
                    grid.set_pixel(x, y, color)
                except (ValueError, IndexError) as e:
                    print(f"Warning: Invalid color at ({x}, {y}): {pixel_value}, error: {e}")
    
    return grid

def main():
    # Define Mario assets (from agent-log.md)
    mario_assets = [
        {
            'id': '007ae9b5-779a-4eb7-af57-d455edbfaa54',
            'name': 'mario_sword',
            'description': 'Mario Sword'
        },
        {
            'id': '3449d39e-a229-4bd8-b85b-1e9c75b7fcf1',
            'name': 'mario_shield',
            'description': 'Mario Shield'
        },
        {
            'id': '66582a57-1f88-4f46-998c-8df6d193ba6a',
            'name': 'mario_health_potion',
            'description': 'Mario Health Potion (Mushroom)'
        },
        {
            'id': '0dc5ac2a-13af-48a7-b11d-d96472542274',
            'name': 'mario_player_sprite',
            'description': 'Mario Player Sprite'
        },
        {
            'id': 'ee6fb394-801a-4eb9-a25b-e508ce483ae3',
            'name': 'mario_soda',
            'description': 'Mario Soda'
        },
        {
            'id': '2db3ac53-f832-4677-b9d0-d39a8c4ed78d',
            'name': 'mario_grass_tile',
            'description': 'Mario Grass Tile'
        },
        {
            'id': 'bc074dec-0a0c-486a-a593-b5a02f34d972',
            'name': 'mario_water_tile',
            'description': 'Mario Water Tile (Animated)'
        }
    ]
    
    # Define Zelda assets
    zelda_assets = [
        {
            'id': '18657548-b98e-4ca2-bdba-a08bd0c0be98',
            'name': 'zelda_sword_master_sword',
            'description': 'Master Sword'
        },
        {
            'id': 'b69723fd-7143-40fe-ac5c-eb7c7a9c4e7b',
            'name': 'zelda_shield_hyrulian',
            'description': 'Hyrulian Shield'
        },
        {
            'id': 'a13edcc9-4f79-4894-a07f-60dbb6a28cbc',
            'name': 'zelda_health_potion_fairy_bottle',
            'description': 'Fairy Bottle Health Potion'
        }
    ]
    
    # Create review directories
    mario_dir = Path('output/mario_review')
    zelda_dir = Path('output/zelda_review')
    mario_dir.mkdir(exist_ok=True)
    zelda_dir.mkdir(exist_ok=True)
    
    # Create exporter with 4x scaling
    exporter = PNGExporter(scale=4, include_metadata=True)
    
    mario_rendered = []
    zelda_rendered = []
    
    # Render Mario assets
    print("=" * 60)
    print("RENDERING MARIO-STYLE ASSETS")
    print("=" * 60)
    for asset in mario_assets:
        manifest_path = f"output/{asset['id']}/manifest.json"
        
        if not os.path.exists(manifest_path):
            print(f"⚠️  Manifest not found: {manifest_path}")
            continue
        
        print(f"Rendering {asset['description']}...")
        
        try:
            # Load manifest
            manifest = load_manifest(manifest_path)
            
            # Convert to grid
            grid = render_manifest_to_grid(manifest)
            
            # Export to PNG
            output_path = mario_dir / f"{asset['name']}.png"
            exporter.export(
                grid,
                str(output_path),
                transparent_color=Color(255, 0, 255),
                metadata={
                    'name': asset['description'],
                    'request_id': asset['id'],
                    'generated_by': 'Vision',
                    'style': 'mario'
                }
            )
            
            mario_rendered.append(str(output_path))
            print(f"✓ Rendered to: {output_path}")
        except Exception as e:
            print(f"✗ Error rendering {asset['description']}: {e}")
    
    # Render Zelda assets
    print("\n" + "=" * 60)
    print("RENDERING ZELDA-STYLE ASSETS")
    print("=" * 60)
    for asset in zelda_assets:
        manifest_path = f"output/{asset['id']}/manifest.json"
        
        if not os.path.exists(manifest_path):
            print(f"⚠️  Manifest not found: {manifest_path}")
            continue
        
        print(f"Rendering {asset['description']}...")
        
        try:
            # Load manifest
            manifest = load_manifest(manifest_path)
            
            # Convert to grid
            grid = render_manifest_to_grid(manifest)
            
            # Export to PNG
            output_path = zelda_dir / f"{asset['name']}.png"
            exporter.export(
                grid,
                str(output_path),
                transparent_color=Color(255, 0, 255),
                metadata={
                    'name': asset['description'],
                    'request_id': asset['id'],
                    'generated_by': 'Vision',
                    'style': 'zelda'
                }
            )
            
            zelda_rendered.append(str(output_path))
            print(f"✓ Rendered to: {output_path}")
        except Exception as e:
            print(f"✗ Error rendering {asset['description']}: {e}")
    
    # Create Mario summary file
    mario_summary = mario_dir / 'REVIEW_SUMMARY.txt'
    with open(mario_summary, 'w') as f:
        f.write("Mario-Style Asset Review\n")
        f.write("=" * 50 + "\n\n")
        f.write("Generated Assets:\n\n")
        for i, asset in enumerate(mario_assets, 1):
            f.write(f"{i}. {asset['description']}\n")
            f.write(f"   File: {asset['name']}.png\n")
            f.write(f"   Request ID: {asset['id']}\n\n")
        f.write("\nAll assets have been rendered at 4x scale.\n")
        f.write("Transparent color: Magenta (#FF00FF)\n")
        f.write(f"\nStyle: Mario Bros - bright colors, bold outlines, cheerful\n")
    
    # Create Zelda summary file
    zelda_summary = zelda_dir / 'REVIEW_SUMMARY.txt'
    with open(zelda_summary, 'w') as f:
        f.write("Zelda-Style Asset Review\n")
        f.write("=" * 50 + "\n\n")
        f.write("Generated Assets:\n\n")
        for i, asset in enumerate(zelda_assets, 1):
            f.write(f"{i}. {asset['description']}\n")
            f.write(f"   File: {asset['name']}.png\n")
            f.write(f"   Request ID: {asset['id']}\n\n")
        f.write("\nAll assets have been rendered at 4x scale.\n")
        f.write("Transparent color: Magenta (#FF00FF)\n")
        f.write(f"\nStyle: Legend of Zelda - medieval fantasy, rich colors\n")
    
    print("\n" + "=" * 60)
    print("RENDERING COMPLETE")
    print("=" * 60)
    print(f"\n✓ Mario assets rendered to: {mario_dir}")
    print(f"  - {len(mario_rendered)} files")
    print(f"✓ Zelda assets rendered to: {zelda_dir}")
    print(f"  - {len(zelda_rendered)} files")
    print(f"\n✓ Summary files created")
    print(f"  - {mario_summary}")
    print(f"  - {zelda_summary}")

if __name__ == '__main__':
    main()
