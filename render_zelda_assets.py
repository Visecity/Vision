#!/usr/bin/env python3
"""Render Zelda-style manifests to PNG files."""

import json
import os
from pathlib import Path
from src.rendering.pixel import PixelGrid, Color
from src.rendering.export import PNGExporter

def load_manifest(manifest_path: str) -> dict:
    """Load a manifest JSON file."""
    with open(manifest_path, 'r') as f:
        return json.load(f)

def render_manifest_to_grid(manifest: dict) -> PixelGrid:
    """Convert a manifest to a PixelGrid."""
    width = manifest['dimensions']['width']
    height = manifest['dimensions']['height']
    
    # Create grid with transparent background
    grid = PixelGrid(width, height, background=Color(255, 0, 255))  # Magenta = transparent
    
    # Draw each pixel from the manifest
    if 'pixels' in manifest:
        for pixel in manifest['pixels']:
            x = pixel['x']
            y = pixel['y']
            color = pixel['color']
            grid.set_pixel(x, y, Color(color['r'], color['g'], color['b']))
    
    return grid

def main():
    # Define the three generated assets
    assets = [
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
    
    # Create review directory
    review_dir = Path('output/zelda_review')
    review_dir.mkdir(exist_ok=True)
    
    # Create exporter with 4x scaling
    exporter = PNGExporter(scale=4, include_metadata=True)
    
    rendered_files = []
    
    for asset in assets:
        manifest_path = f"output/{asset['id']}/manifest.json"
        
        if not os.path.exists(manifest_path):
            print(f"⚠️  Manifest not found: {manifest_path}")
            continue
        
        print(f"Rendering {asset['description']}...")
        
        # Load manifest
        manifest = load_manifest(manifest_path)
        
        # Convert to grid
        grid = render_manifest_to_grid(manifest)
        
        # Export to PNG
        output_path = review_dir / f"{asset['name']}.png"
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
        
        rendered_files.append(str(output_path))
        print(f"✓ Rendered to: {output_path}")
    
    # Create summary file
    summary_path = review_dir / 'REVIEW_SUMMARY.txt'
    with open(summary_path, 'w') as f:
        f.write("Zelda-Style Asset Review\n")
        f.write("=" * 50 + "\n\n")
        f.write("Generated Assets:\n\n")
        for i, asset in enumerate(assets, 1):
            f.write(f"{i}. {asset['description']}\n")
            f.write(f"   File: {asset['name']}.png\n")
            f.write(f"   Request ID: {asset['id']}\n\n")
        f.write("\nAll assets have been rendered at 4x scale.\n")
        f.write("Transparent color: Magenta (#FF00FF)\n")
    
    print(f"\n✓ All assets rendered to: {review_dir}")
    print(f"✓ Summary created: {summary_path}")
    print(f"\nRendered files:")
    for f in rendered_files:
        print(f"  - {f}")

if __name__ == '__main__':
    main()
