# Vision Examples

This directory contains example scripts demonstrating the Vision pixel art generation system's capabilities.

## Sample Assets Demo

### Running the Demo

```bash
python3 examples/create_sample_assets.py
```

This generates a complete set of game-ready pixel art assets:

### Generated Assets

#### 🌍 Terrain Tiles (5 tiles)
- **Grass** - Lush green grass with texture details
- **Dirt** - Brown earth with subtle variation
- **Stone** - Gray stone with crack patterns
- **Water** - Blue water with wave effects
- **Sand** - Yellow sand with granular texture

All terrain tiles are 16x16 pixels, scaled 4x for visibility (64x64 output).

#### 🎯 UI Icons (5 icons)
- **Health** - Red heart icon for player health
- **Mana** - Blue crystal/gem for magic energy
- **Coin** - Gold coin for currency
- **Inventory** - Brown bag/chest for items
- **Settings** - Gray gear for game settings

All UI icons are 16x16 pixels, scaled 4x (64x64 output).

#### ⚔️ Items (5 items)
- **Sword** - Silver blade with brown handle
- **Potion** - Glass bottle with red liquid
- **Key** - Golden key for unlocking
- **Chest** - Wooden treasure chest
- **Gem** - Purple gemstone

All items are 16x16 pixels, scaled 4x (64x64 output).

#### 🏃 Player Animations (5 animations, 4 frames each)
1. **Idle** - Breathing/standing animation
2. **Walk** - Walking cycle with alternating legs
3. **Jump** - Jump arc with raised arms
4. **Attack** - Sword swing attack
5. **Hurt** - Damage flash with knockback

Each animation has 4 frames, 16x16 pixels each, scaled 4x (64x64 output).

### Output Structure

```
examples/output/
├── terrain/           # Individual terrain tiles
│   ├── grass.png
│   ├── dirt.png
│   ├── stone.png
│   ├── water.png
│   └── sand.png
├── ui/               # Individual UI icons
│   ├── health.png
│   ├── mana.png
│   ├── coin.png
│   ├── inventory.png
│   └── settings.png
├── items/            # Individual items
│   ├── sword.png
│   ├── potion.png
│   ├── key.png
│   ├── chest.png
│   └── gem.png
├── player/           # Animation frames by type
│   ├── idle/
│   │   ├── idle_00.png
│   │   ├── idle_01.png
│   │   ├── idle_02.png
│   │   └── idle_03.png
│   ├── walk/
│   ├── jump/
│   ├── attack/
│   └── hurt/
└── sprite_sheets/    # Packed sprite sheets
    ├── terrain_sheet.png
    ├── ui_sheet.png
    ├── items_sheet.png
    ├── player_idle_sheet.png
    ├── player_walk_sheet.png
    ├── player_jump_sheet.png
    ├── player_attack_sheet.png
    ├── player_hurt_sheet.png
    ├── master_atlas.png
    └── master_atlas.json
```

### Sprite Sheets

The demo automatically packs sprites into optimized sprite sheets:

- **Individual sheets**: One per category (terrain, ui, items)
- **Animation sheets**: One per animation type (horizontal strip)
- **Master atlas**: Combined texture atlas with metadata JSON

### Using the Assets

#### In Your Game Engine

1. **Unity**: Import PNGs, use master_atlas.json to create AtlasTexture
2. **Godot**: Import PNGs, create AtlasTexture resources from metadata
3. **Pygame**: Load PNGs, use metadata for sprite rect positioning
4. **HTML5/Canvas**: Load images, use JSON for sprite coordinates

#### Metadata Format

The `master_atlas.json` contains sprite positions:

```json
{
  "atlas_width": 240,
  "atlas_height": 16,
  "frames": {
    "terrain_grass": {
      "name": "terrain_grass",
      "x": 0,
      "y": 0,
      "width": 16,
      "height": 16
    }
  }
}
```

### Rendering Features Demonstrated

This example showcases:

✅ **Drawing Primitives**
- Lines (Bresenham's algorithm)
- Rectangles (filled and outlined)
- Circles (midpoint algorithm)
- Pixel-by-pixel control

✅ **Color Management**
- Stardew Valley-inspired palette
- Transparency (magenta as transparent color)
- Color quantization

✅ **PNG Export**
- Integer scaling (4x)
- Transparency support
- Metadata embedding
- Batch export

✅ **Sprite Sheet Packing**
- Grid algorithm for uniform sprites
- Row algorithm for animation strips
- MaxRects algorithm for atlas
- Automatic padding
- Metadata generation

✅ **Animation**
- Frame sequencing
- Animation sheets
- Consistent sprite sizing

## Creating Your Own Assets

### Basic Example

```python
from src.rendering import PixelGrid, DrawingContext, Color, PNGExporter

# Create 16x16 grid
grid = PixelGrid(16, 16, background=Color(255, 0, 255))

# Draw a simple tree
ctx = DrawingContext(grid)
ctx.draw_rect(7, 10, 2, 4, Color(120, 80, 60), filled=True)  # Trunk
ctx.draw_circle(8, 6, 4, Color(56, 183, 100), filled=True)   # Leaves

# Export with 4x scaling
exporter = PNGExporter(scale=4)
exporter.export(grid, "my_tree.png", transparent_color=Color(255, 0, 255))
```

### Animation Example

```python
from src.rendering import AnimationSheet

frames = []
for i in range(4):
    grid = PixelGrid(16, 16)
    # Draw frame i...
    frames.append(grid)

animation = AnimationSheet("walk", frames, frame_duration=0.1, loop=True)
sheet = animation.to_sprite_sheet()
```

## Style Guide

The sample assets follow Stardew Valley-inspired pixel art principles:

1. **Limited Palette**: 17 carefully chosen colors
2. **Readable at Small Size**: Clear silhouettes at 16x16
3. **Consistent Style**: Unified art direction across all assets
4. **Functional Design**: Immediately recognizable icons
5. **Clean Outlines**: Dark outlines for visual clarity

## Next Steps

1. **Modify the script**: Change colors, sizes, or add new assets
2. **Experiment with algorithms**: Try different sprite sheet packing methods
3. **Add effects**: Use dithering, gradients, or outlines
4. **Create animations**: Add more frames or animation types
5. **Integrate with AI**: Use the Vision workflow to generate assets automatically

## AI-Powered Generation (Coming Soon)

While this demo creates assets manually, the Vision system's full power comes from AI-powered generation:

```bash
# Generate assets using AI agents (requires API key and Redis)
vision generate "fantasy RPG grass tile" --style stardew
vision generate "sword and shield icon" --size 16x16
```

See the main README for setting up the full AI workflow.