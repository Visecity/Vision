#!/usr/bin/env python3
"""
Script to re-render existing manifests with the fixed converter.
This fixes the black square issue caused by "#T" transparent pixels.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.rendering.manifest_renderer import ManifestRenderer


def re_render_manifest(manifest_path: Path) -> bool:
    """Re-render a manifest JSON file to PNG."""
    try:
        # Load manifest
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Determine output PNG path (same directory, same name)
        png_path = manifest_path.with_suffix('.png')
        
        # Render
        renderer = ManifestRenderer(scale=1, include_metadata=True)
        result_path = renderer.render_manifest_sync(manifest, png_path)
        
        print(f"✓ Re-rendered: {png_path.name}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to render {manifest_path.name}: {e}")
        return False


def main():
    """Find and re-render all manifests in Aris directories."""
    base_dir = Path("Aris")
    
    if not base_dir.exists():
        print("Error: Aris directory not found")
        return 1
    
    # Find all JSON manifests
    manifests = list(base_dir.rglob("*.json"))
    
    if not manifests:
        print("No manifests found to re-render")
        return 0
    
    print(f"Found {len(manifests)} manifests to re-render\n")
    
    success_count = 0
    fail_count = 0
    
    for manifest_path in sorted(manifests):
        if re_render_manifest(manifest_path):
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\n{'='*50}")
    print(f"Re-rendering complete!")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"{'='*50}")
    
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())