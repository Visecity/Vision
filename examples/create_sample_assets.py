"""
Sample asset generation script for Vision pixel art system.

This script demonstrates the rendering engine by creating:
- 5 terrain tiles
- 5 UI icon elements
- 5 items
- 5 animated player sprites (with 4 frames each)

All assets are created manually to showcase the drawing primitives,
then exported as PNGs and packed into sprite sheets.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rendering import (
    Color,
    PixelGrid,
    DrawingContext,
    PNGExporter,
    SpriteSheetPacker,
    PackingAlgorithm,
    AnimationSheet,
    create_texture_atlas,
    Palette,
    OutlineGenerator,
)


# Define a Stardew Valley-inspired palette
PALETTE = Palette.from_hex_list(
    "stardew",
    [
        "#000000",  # Black
        "#1a1c2c",  # Dark blue
        "#5d275d",  # Purple
        "#b13e53",  # Red
        "#ef7d57",  # Orange
        "#ffcd75",  # Yellow
        "#a7f070",  # Light green
        "#38b764",  # Green
        "#257179",  # Teal
        "#29366f",  # Blue
        "#3b5dc9",  # Light blue
        "#41a6f6",  # Sky blue
        "#73eff7",  # Cyan
        "#f4f4f4",  # White
        "#94b0c2",  # Gray
        "#566c86",  # Dark gray
        "#333c57",  # Darker gray
    ]
)

# Common colors
BLACK = Color(0, 0, 0)
WHITE = Color(255, 255, 255)
TRANSPARENT = Color(255, 0, 255)  # Magenta for transparency

# Stardew-inspired colors
GRASS_GREEN = Color(167, 240, 112)
DARK_GREEN = Color(56, 183, 100)
DIRT_BROWN = Color(181, 62, 83)
STONE_GRAY = Color(148, 176, 194)
WATER_BLUE = Color(65, 166, 246)
SAND_YELLOW = Color(255, 205, 117)


def create_terrain_tiles() -> dict[str, PixelGrid]:
    """Create 5 terrain tiles: grass, dirt, stone, water, sand."""
    tiles = {}
    
    # 1. Grass tile
    grass = PixelGrid(16, 16, background=TRANSPARENT)
    ctx = DrawingContext(grass)
    ctx.draw_rect(0, 0, 16, 16, GRASS_GREEN, filled=True)
    # Add grass details
    for x in [2, 6, 10, 14]:
        for y in [3, 7, 11]:
            ctx.draw_pixel(x, y, DARK_GREEN)
            ctx.draw_pixel(x, y + 1, DARK_GREEN)
    tiles["grass"] = grass
    
    # 2. Dirt tile
    dirt = PixelGrid(16, 16, background=TRANSPARENT)
    ctx = DrawingContext(dirt)
    ctx.draw_rect(0, 0, 16, 16, DIRT_BROWN, filled=True)
    # Add dirt texture
    dirt_dark = Color(150, 50, 65)
    for x in [1, 5, 9, 13]:
        for y in [2, 6, 10, 14]:
            ctx.draw_pixel(x, y, dirt_dark)
    tiles["dirt"] = dirt
    
    # 3. Stone tile
    stone = PixelGrid(16, 16, background=TRANSPARENT)
    ctx = DrawingContext(stone)
    ctx.draw_rect(0, 0, 16, 16, STONE_GRAY, filled=True)
    # Add stone cracks
    stone_dark = Color(100, 120, 140)
    ctx.draw_line(2, 3, 6, 3, stone_dark)
    ctx.draw_line(10, 8, 14, 8, stone_dark)
    ctx.draw_line(4, 12, 8, 12, stone_dark)
    tiles["stone"] = stone
    
    # 4. Water tile (animated look with simple pattern)
    water = PixelGrid(16, 16, background=TRANSPARENT)
    ctx = DrawingContext(water)
    ctx.draw_rect(0, 0, 16, 16, WATER_BLUE, filled=True)
    # Add wave pattern
    water_light = Color(115, 239, 247)
    for x in range(0, 16, 4):
        ctx.draw_line(x, 4, x + 2, 4, water_light)
        ctx.draw_line(x + 2, 10, x + 4, 10, water_light)
    tiles["water"] = water
    
    # 5. Sand tile
    sand = PixelGrid(16, 16, background=TRANSPARENT)
    ctx = DrawingContext(sand)
    ctx.draw_rect(0, 0, 16, 16, SAND_YELLOW, filled=True)
    # Add sand texture
    sand_light = Color(255, 220, 140)
    for x in [3, 7, 11]:
        for y in [2, 8, 14]:
            ctx.draw_pixel(x, y, sand_light)
            ctx.draw_pixel(x + 1, y, sand_light)
    tiles["sand"] = sand
    
    return tiles


def create_ui_icons() -> dict[str, PixelGrid]:
    """Create 5 UI icons: health, mana, coin, inventory, settings."""
    icons = {}
    
    # 1. Health (heart)
    health = PixelGrid(16, 16, background=TRANSPARENT)
    ctx = DrawingContext(health)
    heart_red = Color(181, 62, 83)
    heart_dark = Color(120, 40, 60)
    # Draw heart shape
    ctx.draw_circle(5, 6, 2, heart_red, filled=True)
    ctx.draw_circle(9, 6, 2, heart_red, filled=True)
    ctx.draw_pixel(7, 8, heart_red)
    ctx.draw_line(5, 8, 9, 8, heart_red)
    ctx.draw_line(4, 9, 10, 9, heart_red)
    ctx.draw_line(5, 10, 9, 10, heart_red)
    ctx.draw_line(6, 11, 8, 11, heart_red)
    ctx.draw_pixel(7, 12, heart_red)
    # Add highlight
    ctx.draw_pixel(6, 6, Color(239, 125, 87))
    icons["health"] = health
    
    # 2. Mana (crystal/gem)
    mana = PixelGrid(16, 16, background=TRANSPARENT)
    ctx = DrawingContext(mana)
    mana_blue = Color(65, 166, 246)
    mana_light = Color(115, 239, 247)
    # Diamond shape
    ctx.draw_line(7, 4, 7, 4, mana_light)
    ctx.draw_line(6, 5, 8, 5, mana_blue)
    ctx.draw_line(5, 6, 9, 6, mana_blue)
    ctx.draw_line(5, 7, 9, 7, mana_blue)
    ctx.draw_line(5, 8, 9, 8, mana_blue)
    ctx.draw_line(6, 9, 8, 9, mana_blue)
    ctx.draw_line(6, 10, 8, 10, mana_blue)
    ctx.draw_line(7, 11, 7, 11, mana_blue)
    # Highlight
    ctx.draw_pixel(7, 5, mana_light)
    icons["mana"] = mana
    
    # 3. Coin
    coin = PixelGrid(16, 16, background=TRANSPARENT)
    ctx = DrawingContext(coin)
    coin_yellow = Color(255, 205, 117)
    coin_dark = Color(220, 160, 80)
    # Circle
    ctx.draw_circle(7, 7, 4, coin_yellow, filled=True)
    # Details
    ctx.draw_circle(7, 7, 4, coin_dark, filled=False)
    ctx.draw_circle(7, 7, 2, coin_dark, filled=False)
    icons["coin"] = coin
    
    # 4. Inventory (chest/bag)
    inventory = PixelGrid(16, 16, background=TRANSPARENT)
    ctx = DrawingContext(inventory)
    bag_brown = Color(150, 100, 70)
    bag_dark = Color(100, 60, 40)
    # Bag shape
    ctx.draw_rect(4, 5, 8, 7, bag_brown, filled=True)
    ctx.draw_rect(4, 5, 8, 7, bag_dark, filled=False)
    # Handle
    ctx.draw_line(6, 3, 6, 5, bag_dark)
    ctx.draw_line(9, 3, 9, 5, bag_dark)
    ctx.draw_line(6, 3, 9, 3, bag_dark)
    icons["inventory"] = inventory
    
    # 5. Settings (gear)
    settings = PixelGrid(16, 16, background=TRANSPARENT)
    ctx = DrawingContext(settings)
    gear_gray = Color(148, 176, 194)
    gear_dark = Color(80, 100, 120)
    # Center circle
    ctx.draw_circle(7, 7, 2, gear_gray, filled=True)
    # Gear teeth (simple)
    for angle in [0, 90, 180, 270]:
        if angle == 0:
            ctx.draw_rect(10, 6, 2, 3, gear_gray, filled=True)
        elif angle == 90:
            ctx.draw_rect(6, 10, 3, 2, gear_gray, filled=True)
        elif angle == 180:
            ctx.draw_rect(3, 6, 2, 3, gear_gray, filled=True)
        else:  # 270
            ctx.draw_rect(6, 3, 3, 2, gear_gray, filled=True)
    # Center hole
    ctx.draw_pixel(7, 7, gear_dark)
    icons["settings"] = settings
    
    return icons


def create_items() -> dict[str, PixelGrid]:
    """Create 5 items: sword, potion, key, chest, gem."""
    items = {}
    
    # 1. Sword
    sword = PixelGrid(16, 16, background=TRANSPARENT)
    ctx = DrawingContext(sword)
    blade_gray = Color(180, 180, 200)
    handle_brown = Color(120, 80, 60)
    gold = Color(255, 200, 80)
    # Blade
    ctx.draw_line(8, 2, 8, 10, blade_gray)
    ctx.draw_line(7, 3, 7, 9, blade_gray)
    ctx.draw_line(9, 3, 9, 9, blade_gray)
    ctx.draw_pixel(8, 1, blade_gray)
    # Guard
    ctx.draw_line(6, 10, 10, 10, gold)
    # Handle
    ctx.draw_line(8, 11, 8, 13, handle_brown)
    # Pommel
    ctx.draw_circle(8, 14, 1, gold, filled=True)
    items["sword"] = sword
    
    # 2. Potion
    potion = PixelGrid(16, 16, background=TRANSPARENT)
    ctx = DrawingContext(potion)
    glass = Color(180, 200, 220)
    liquid_red = Color(200, 60, 80)
    # Bottle
    ctx.draw_line(7, 4, 7, 12, glass)
    ctx.draw_line(9, 4, 9, 12, glass)
    ctx.draw_line(7, 12, 9, 12, glass)
    # Cork
    ctx.draw_rect(7, 2, 3, 2, Color(140, 100, 70), filled=True)
    # Liquid
    ctx.draw_rect(7, 8, 3, 4, liquid_red, filled=True)
    items["potion"] = potion
    
    # 3. Key
    key = PixelGrid(16, 16, background=TRANSPARENT)
    ctx = DrawingContext(key)
    key_gold = Color(255, 200, 80)
    # Head (circle)
    ctx.draw_circle(5, 6, 2, key_gold, filled=True)
    ctx.draw_pixel(5, 6, Color(200, 150, 60))  # Hole
    # Shaft
    ctx.draw_line(7, 6, 12, 6, key_gold)
    # Teeth
    ctx.draw_pixel(10, 7, key_gold)
    ctx.draw_pixel(11, 7, key_gold)
    ctx.draw_pixel(12, 7, key_gold)
    items["key"] = key
    
    # 4. Chest
    chest = PixelGrid(16, 16, background=TRANSPARENT)
    ctx = DrawingContext(chest)
    wood_brown = Color(140, 90, 60)
    wood_dark = Color(90, 60, 40)
    gold = Color(255, 200, 80)
    # Chest body
    ctx.draw_rect(3, 6, 10, 7, wood_brown, filled=True)
    ctx.draw_rect(3, 6, 10, 7, wood_dark, filled=False)
    # Lid
    ctx.draw_rect(3, 4, 10, 3, wood_brown, filled=True)
    ctx.draw_rect(3, 4, 10, 3, wood_dark, filled=False)
    # Lock
    ctx.draw_rect(7, 9, 2, 2, gold, filled=True)
    items["chest"] = chest
    
    # 5. Gem
    gem = PixelGrid(16, 16, background=TRANSPARENT)
    ctx = DrawingContext(gem)
    gem_purple = Color(147, 62, 146)
    gem_light = Color(200, 100, 200)
    # Diamond shape
    ctx.draw_pixel(7, 3, gem_light)
    ctx.draw_line(6, 4, 8, 4, gem_purple)
    ctx.draw_line(5, 5, 9, 5, gem_purple)
    ctx.draw_line(5, 6, 9, 6, gem_purple)
    ctx.draw_line(5, 7, 9, 7, gem_purple)
    ctx.draw_line(5, 8, 9, 8, gem_purple)
    ctx.draw_line(6, 9, 8, 9, gem_purple)
    ctx.draw_line(6, 10, 8, 10, gem_purple)
    ctx.draw_line(7, 11, 7, 11, gem_purple)
    # Highlights
    ctx.draw_pixel(6, 5, gem_light)
    ctx.draw_pixel(7, 5, gem_light)
    items["gem"] = gem
    
    return items


def create_player_animations() -> dict[str, list[PixelGrid]]:
    """Create 5 animated player sprites with 4 frames each."""
    animations = {}
    
    # Player colors
    skin = Color(255, 224, 189)
    hair = Color(120, 80, 60)
    shirt = Color(100, 150, 200)
    pants = Color(60, 80, 120)
    
    # 1. Idle animation (4 frames - subtle breathing)
    idle_frames = []
    for frame in range(4):
        grid = PixelGrid(16, 16, background=TRANSPARENT)
        ctx = DrawingContext(grid)
        y_offset = 0 if frame % 2 == 0 else 1
        
        # Head
        ctx.draw_rect(6, 3 + y_offset, 4, 4, skin, filled=True)
        # Hair
        ctx.draw_rect(6, 3 + y_offset, 4, 2, hair, filled=True)
        # Eyes
        ctx.draw_pixel(7, 5 + y_offset, BLACK)
        ctx.draw_pixel(8, 5 + y_offset, BLACK)
        # Body
        ctx.draw_rect(5, 7 + y_offset, 6, 4, shirt, filled=True)
        # Arms
        ctx.draw_line(4, 8 + y_offset, 4, 10 + y_offset, skin)
        ctx.draw_line(11, 8 + y_offset, 11, 10 + y_offset, skin)
        # Legs
        ctx.draw_rect(6, 11 + y_offset, 2, 3, pants, filled=True)
        ctx.draw_rect(8, 11 + y_offset, 2, 3, pants, filled=True)
        
        idle_frames.append(grid)
    animations["idle"] = idle_frames
    
    # 2. Walk animation (4 frames)
    walk_frames = []
    for frame in range(4):
        grid = PixelGrid(16, 16, background=TRANSPARENT)
        ctx = DrawingContext(grid)
        
        # Head
        ctx.draw_rect(6, 3, 4, 4, skin, filled=True)
        ctx.draw_rect(6, 3, 4, 2, hair, filled=True)
        ctx.draw_pixel(7, 5, BLACK)
        ctx.draw_pixel(8, 5, BLACK)
        # Body
        ctx.draw_rect(5, 7, 6, 4, shirt, filled=True)
        
        # Arms and legs alternate
        if frame in [0, 2]:
            # Right arm forward, left arm back
            ctx.draw_line(4, 8, 3, 10, skin)
            ctx.draw_line(11, 8, 12, 10, skin)
            # Right leg forward, left leg back
            ctx.draw_rect(7, 11, 2, 3, pants, filled=True)
            ctx.draw_rect(6, 12, 2, 2, pants, filled=True)
        else:
            # Left arm forward, right arm back
            ctx.draw_line(4, 8, 3, 10, skin)
            ctx.draw_line(11, 8, 12, 10, skin)
            # Left leg forward, right leg back
            ctx.draw_rect(6, 11, 2, 3, pants, filled=True)
            ctx.draw_rect(8, 12, 2, 2, pants, filled=True)
        
        walk_frames.append(grid)
    animations["walk"] = walk_frames
    
    # 3. Jump animation (4 frames)
    jump_frames = []
    for frame in range(4):
        grid = PixelGrid(16, 16, background=TRANSPARENT)
        ctx = DrawingContext(grid)
        y_pos = max(0, 6 - frame * 2) if frame < 2 else (frame - 2) * 2
        
        # Head
        ctx.draw_rect(6, y_pos, 4, 4, skin, filled=True)
        ctx.draw_rect(6, y_pos, 4, 2, hair, filled=True)
        ctx.draw_pixel(7, y_pos + 2, BLACK)
        ctx.draw_pixel(8, y_pos + 2, BLACK)
        # Body
        ctx.draw_rect(5, y_pos + 4, 6, 4, shirt, filled=True)
        # Arms (raised)
        ctx.draw_line(4, y_pos + 4, 3, y_pos + 3, skin)
        ctx.draw_line(11, y_pos + 4, 12, y_pos + 3, skin)
        # Legs (together)
        ctx.draw_rect(6, y_pos + 8, 4, 3, pants, filled=True)
        
        jump_frames.append(grid)
    animations["jump"] = jump_frames
    
    # 4. Attack animation (4 frames - sword swing)
    attack_frames = []
    for frame in range(4):
        grid = PixelGrid(16, 16, background=TRANSPARENT)
        ctx = DrawingContext(grid)
        
        # Head
        ctx.draw_rect(6, 3, 4, 4, skin, filled=True)
        ctx.draw_rect(6, 3, 4, 2, hair, filled=True)
        ctx.draw_pixel(7, 5, BLACK)
        ctx.draw_pixel(8, 5, BLACK)
        # Body
        ctx.draw_rect(5, 7, 6, 4, shirt, filled=True)
        # Legs
        ctx.draw_rect(6, 11, 2, 3, pants, filled=True)
        ctx.draw_rect(8, 11, 2, 3, pants, filled=True)
        
        # Sword swing
        sword_color = Color(200, 200, 220)
        if frame == 0:
            # Sword raised
            ctx.draw_line(11, 4, 11, 7, sword_color)
        elif frame == 1:
            # Sword mid-swing
            ctx.draw_line(10, 5, 13, 5, sword_color)
        elif frame == 2:
            # Sword down
            ctx.draw_line(12, 6, 12, 10, sword_color)
        else:
            # Sword recovery
            ctx.draw_line(11, 6, 11, 9, sword_color)
        
        # Arm
        ctx.draw_line(11, 8, 11, 10, skin)
        
        attack_frames.append(grid)
    animations["attack"] = attack_frames
    
    # 5. Hurt animation (4 frames - flash and knockback)
    hurt_frames = []
    for frame in range(4):
        grid = PixelGrid(16, 16, background=TRANSPARENT)
        ctx = DrawingContext(grid)
        
        # Flash effect (every other frame)
        if frame % 2 == 0:
            flash_color = Color(255, 100, 100)
        else:
            flash_color = skin
        
        x_offset = -frame if frame < 2 else -(3 - frame)
        
        # Head
        ctx.draw_rect(6 + x_offset, 3, 4, 4, flash_color, filled=True)
        ctx.draw_rect(6 + x_offset, 3, 4, 2, hair, filled=True)
        if frame % 2 == 0:
            ctx.draw_pixel(7 + x_offset, 5, BLACK)
            ctx.draw_pixel(8 + x_offset, 5, BLACK)
        # Body
        ctx.draw_rect(5 + x_offset, 7, 6, 4, shirt, filled=True)
        # Arms
        ctx.draw_line(4 + x_offset, 8, 4 + x_offset, 10, flash_color)
        ctx.draw_line(11 + x_offset, 8, 11 + x_offset, 10, flash_color)
        # Legs
        ctx.draw_rect(6 + x_offset, 11, 2, 3, pants, filled=True)
        ctx.draw_rect(8 + x_offset, 11, 2, 3, pants, filled=True)
        
        hurt_frames.append(grid)
    animations["hurt"] = hurt_frames
    
    return animations


def main():
    """Generate all sample assets."""
    print("🎨 Vision Pixel Art Generation - Sample Assets")
    print("=" * 50)
    
    # Create output directories
    output_dir = Path("examples/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    terrain_dir = output_dir / "terrain"
    ui_dir = output_dir / "ui"
    items_dir = output_dir / "items"
    player_dir = output_dir / "player"
    sheets_dir = output_dir / "sprite_sheets"
    
    for d in [terrain_dir, ui_dir, items_dir, player_dir, sheets_dir]:
        d.mkdir(exist_ok=True)
    
    # Create exporter with 4x scaling
    exporter = PNGExporter(scale=4, include_metadata=True)
    
    # 1. Create terrain tiles
    print("\n📦 Creating terrain tiles...")
    terrain_tiles = create_terrain_tiles()
    for name, grid in terrain_tiles.items():
        path = exporter.export(
            grid,
            terrain_dir / f"{name}.png",
            transparent_color=TRANSPARENT,
            metadata={"type": "terrain", "name": name},
        )
        print(f"  ✓ Created {name}.png")
    
    # 2. Create UI icons
    print("\n🎯 Creating UI icons...")
    ui_icons = create_ui_icons()
    for name, grid in ui_icons.items():
        path = exporter.export(
            grid,
            ui_dir / f"{name}.png",
            transparent_color=TRANSPARENT,
            metadata={"type": "ui_icon", "name": name},
        )
        print(f"  ✓ Created {name}.png")
    
    # 3. Create items
    print("\n⚔️  Creating items...")
    items = create_items()
    for name, grid in items.items():
        path = exporter.export(
            grid,
            items_dir / f"{name}.png",
            transparent_color=TRANSPARENT,
            metadata={"type": "item", "name": name},
        )
        print(f"  ✓ Created {name}.png")
    
    # 4. Create player animations
    print("\n🏃 Creating player animations...")
    animations = create_player_animations()
    for anim_name, frames in animations.items():
        anim_dir = player_dir / anim_name
        anim_dir.mkdir(exist_ok=True)
        
        for i, frame in enumerate(frames):
            path = exporter.export(
                frame,
                anim_dir / f"{anim_name}_{i:02d}.png",
                transparent_color=TRANSPARENT,
                metadata={"type": "animation", "name": anim_name, "frame": i},
            )
        print(f"  ✓ Created {anim_name} animation (4 frames)")
    
    # 5. Create sprite sheets
    print("\n📋 Creating sprite sheets...")
    
    # Terrain sprite sheet
    packer = SpriteSheetPacker(
        algorithm=PackingAlgorithm.GRID,
        padding=2,
        power_of_two=False,
    )
    terrain_sheet = packer.pack(terrain_tiles)
    terrain_grid = terrain_sheet.to_grid()
    exporter.export(terrain_grid, sheets_dir / "terrain_sheet.png", transparent_color=TRANSPARENT)
    print(f"  ✓ Created terrain_sheet.png ({terrain_sheet.width}x{terrain_sheet.height})")
    
    # UI icons sprite sheet
    ui_sheet = packer.pack(ui_icons)
    ui_grid = ui_sheet.to_grid()
    exporter.export(ui_grid, sheets_dir / "ui_sheet.png", transparent_color=TRANSPARENT)
    print(f"  ✓ Created ui_sheet.png ({ui_sheet.width}x{ui_sheet.height})")
    
    # Items sprite sheet
    items_sheet = packer.pack(items)
    items_grid = items_sheet.to_grid()
    exporter.export(items_grid, sheets_dir / "items_sheet.png", transparent_color=TRANSPARENT)
    print(f"  ✓ Created items_sheet.png ({items_sheet.width}x{items_sheet.height})")
    
    # Player animation sheets
    for anim_name, frames in animations.items():
        anim_sprites = {f"{anim_name}_{i:02d}": frame for i, frame in enumerate(frames)}
        anim_packer = SpriteSheetPacker(algorithm=PackingAlgorithm.ROW, padding=1)
        anim_sheet = anim_packer.pack(anim_sprites, sort_by="name")
        anim_grid = anim_sheet.to_grid()
        exporter.export(
            anim_grid,
            sheets_dir / f"player_{anim_name}_sheet.png",
            transparent_color=TRANSPARENT,
        )
        print(f"  ✓ Created player_{anim_name}_sheet.png ({anim_sheet.width}x{anim_sheet.height})")
    
    # 6. Create master texture atlas
    print("\n🗺️  Creating master texture atlas...")
    all_sheets = {
        "terrain": terrain_sheet,
        "ui": ui_sheet,
        "items": items_sheet,
    }
    
    atlas_path, atlas_metadata = create_texture_atlas(
        all_sheets,
        sheets_dir / "master_atlas.png",
        exporter=exporter,
    )
    
    # Save metadata
    import json
    with open(sheets_dir / "master_atlas.json", "w") as f:
        json.dump(atlas_metadata, f, indent=2)
    
    print(f"  ✓ Created master_atlas.png ({atlas_metadata['atlas_width']}x{atlas_metadata['atlas_height']})")
    print(f"  ✓ Created master_atlas.json")
    
    print("\n✅ All assets created successfully!")
    print(f"\n📁 Output directory: {output_dir.absolute()}")
    print("\nAsset Summary:")
    print(f"  • Terrain tiles: {len(terrain_tiles)}")
    print(f"  • UI icons: {len(ui_icons)}")
    print(f"  • Items: {len(items)}")
    print(f"  • Player animations: {len(animations)} ({sum(len(f) for f in animations.values())} frames total)")
    print(f"  • Sprite sheets: {3 + len(animations) + 1} (including master atlas)")


if __name__ == "__main__":
    main()