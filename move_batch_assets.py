#!/usr/bin/env python3
"""
Move generated batch assets from output/<uuid>/ to Aris/phase-X-Y/ directories.
"""
import shutil
from pathlib import Path

# Mapping of asset names to their target directories
asset_mapping = {
    # Phase 8.2
    "shadow": "Aris/phase-8-2/character",
    "player": "Aris/phase-8-2/character",
    
    # Phase 8.3 - Tools
    "hoe": "Aris/phase-8-3/tools",
    "watering_can": "Aris/phase-8-3/tools",
    "axe": "Aris/phase-8-3/tools",
    "pickaxe": "Aris/phase-8-3/tools",
    "scythe": "Aris/phase-8-3/tools",
    "fishing_rod": "Aris/phase-8-3/tools",
    
    # Phase 8.3 - Weapons
    "sword": "Aris/phase-8-3/weapons",
    "bow": "Aris/phase-8-3/weapons",
    
    # Phase 8.3 - Effects
    "swing": "Aris/phase-8-3/effects",
    "slash": "Aris/phase-8-3/effects",
    
    # Phase 8.4 - Terrain
    "tree": "Aris/phase-8-4/terrain",
    "oak": "Aris/phase-8-4/terrain",
    "pine": "Aris/phase-8-4/terrain",
    "stump": "Aris/phase-8-4/terrain",
    
    # Phase 8.4 - Resources
    "rock": "Aris/phase-8-4/resources",
    "boulder": "Aris/phase-8-4/resources",
    "ore": "Aris/phase-8-4/resources",
    "iron": "Aris/phase-8-4/resources",
    "copper": "Aris/phase-8-4/resources",
    "gold": "Aris/phase-8-4/resources",
    
    # Phase 8.4 - Objects
    "fence": "Aris/phase-8-4/objects",
    "wooden": "Aris/phase-8-4/objects",
}

def get_target_dir(filename: str) -> str:
    """Determine target directory based on filename."""
    filename_lower = filename.lower()
    
    # Check each keyword in mapping
    for keyword, target_dir in asset_mapping.items():
        if keyword in filename_lower:
            return target_dir
    
    return None

def main():
    output_dir = Path("output")
    moved_count = 0
    
    # Find all PNG files in output/<uuid>/ directories
    for png_file in output_dir.glob("*/**.png"):
        # Skip zelda_review, mario_review, and other non-batch directories
        if any(skip in str(png_file) for skip in ["zelda_review", "mario_review", "test"]):
            continue
        
        filename = png_file.name
        target_dir = get_target_dir(filename)
        
        if target_dir:
            target_path = Path(target_dir)
            target_path.mkdir(parents=True, exist_ok=True)
            
            dest_file = target_path / filename
            
            print(f"Moving: {png_file}")
            print(f"    -> {dest_file}")
            
            shutil.copy2(png_file, dest_file)
            
            # Also copy the JSON manifest if it exists
            json_file = png_file.with_suffix('.json')
            if json_file.exists():
                dest_json = dest_file.with_suffix('.json')
                shutil.copy2(json_file, dest_json)
                print(f"    -> {dest_json} (manifest)")
            
            moved_count += 1
        else:
            print(f"Skipping (no mapping): {png_file}")
    
    print(f"\nMoved {moved_count} assets to Aris directories")

if __name__ == "__main__":
    main()
