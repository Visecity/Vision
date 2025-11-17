# Vision Rendering Engine Guide

The Vision rendering engine provides comprehensive tools for creating, manipulating, and exporting pixel art assets. This guide covers all major rendering features and their usage.

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [PNG Export](#png-export)
3. [Sprite Sheets](#sprite-sheets)
4. [Drawing Primitives](#drawing-primitives)
5. [Advanced Techniques](#advanced-techniques)

## Core Concepts

### Colors and Palettes

```python
from src.rendering import Color, Palette

# Create colors
red = Color(255, 0, 0)
blue = Color.from_hex("#0000FF")

# Create a palette
palette = Palette.from_hex_list(
    "gameboy",
    ["#0f380f", "#306230", "#8bac0f", "#9bbc0f"]
)

# Find closest color in palette
closest = palette.find_closest(Color(100, 150, 50))
```

### Pixel Grids

```python
from src.rendering import PixelGrid, Color

# Create a 16x16 grid
grid = PixelGrid(16, 16, background=Color(0, 0, 0))

# Set individual pixels
grid.set_pixel(8, 8, Color(255, 255, 255))

# Get pixel data
pixel = grid.get_pixel(8, 8)

# Convert to numpy array
array = grid.to_numpy()
```

## PNG Export

### Basic Export

```python
from src.rendering import PixelGrid, quick_export, Color

grid = PixelGrid(16, 16)
# ... draw on grid ...

# Quick export
quick_export(grid, "sprite.png", scale=4)
```

### Advanced Export with PNGExporter

```python
from src.rendering import PNGExporter, Color

# Create exporter with 4x scaling
exporter = PNGExporter(
    scale=4,
    include_metadata=True
)

# Export with transparency
transparent_color = Color(255, 0, 255)  # Magenta = transparent
path = exporter.export(
    grid,
    "sprite.png",
    transparent_color=transparent_color,
    metadata={
        "sprite_type": "character",
        "generated_by": "Vision",
    }
)

# Export with border
bordered_path = exporter.export_with_border(
    grid,
    "sprite_bordered.png",
    border_size=1,
    border_color=Color(0, 0, 0),
    transparent_color=transparent_color,
)
```

### Batch Export

```python
from src.rendering import BatchExporter, PNGExporter

exporter = PNGExporter(scale=2)
batch = BatchExporter(exporter)

# Export animation frames
frames = [frame1, frame2, frame3, frame4]
paths = batch.export_sequence(
    frames,
    output_dir="output/walk_animation",
    name_prefix="walk",
    transparent_color=Color(255, 0, 255),
)

# Export named variations
variations = {
    "idle": idle_grid,
    "walk": walk_grid,
    "jump": jump_grid,
}
var_paths = batch.export_variations(
    variations,
    output_dir="output/character",
)
```

## Sprite Sheets

### Basic Sprite Sheet Packing

```python
from src.rendering import SpriteSheetPacker, PackingAlgorithm

# Create sprites
sprites = {
    "tree": tree_grid,
    "rock": rock_grid,
    "house": house_grid,
}

# Pack into sprite sheet using grid layout
packer = SpriteSheetPacker(
    algorithm=PackingAlgorithm.GRID,
    padding=2,
    power_of_two=True,
)

sheet = packer.pack(sprites, sort_by="area")

# Export sprite sheet
from src.rendering import PNGExporter
exporter = PNGExporter()
sheet_grid = sheet.to_grid()
exporter.export(sheet_grid, "sprites.png")

# Get metadata for game engine
metadata = sheet.get_metadata()
# metadata contains frame positions and dimensions
```

### Packing Algorithms

```python
from src.rendering import PackingAlgorithm

# ROW - Pack sprites in a single row
PackingAlgorithm.ROW

# COLUMN - Pack sprites in a single column
PackingAlgorithm.COLUMN

# GRID - Pack sprites in a uniform grid (best for same-size sprites)
PackingAlgorithm.GRID

# SHELF - Shelf-based bin packing (efficient for varied sizes)
PackingAlgorithm.SHELF

# MAXRECTS - MaxRects algorithm (most space-efficient)
PackingAlgorithm.MAXRECTS
```

### Animation Sheets

```python
from src.rendering import AnimationSheet

# Create animation
animation = AnimationSheet(
    name="walk_cycle",
    frames=[frame1, frame2, frame3, frame4],
    frame_duration=0.1,  # 100ms per frame
    loop=True,
)

# Convert to sprite sheet
sheet = animation.to_sprite_sheet()

# Get animation metadata
anim_metadata = animation.get_metadata()
```

### Texture Atlases

```python
from src.rendering import create_texture_atlas

# Combine multiple sprite sheets
sheets = {
    "characters": character_sheet,
    "environment": environment_sheet,
    "items": item_sheet,
}

# Create combined texture atlas
atlas_path, atlas_metadata = create_texture_atlas(
    sheets,
    "game_atlas.png",
)

# Save metadata as JSON
import json
with open("game_atlas.json", "w") as f:
    json.dump(atlas_metadata, f, indent=2)
```

## Drawing Primitives

### Basic Shapes

```python
from src.rendering import DrawingContext, Color

ctx = DrawingContext(grid)

# Draw line
ctx.draw_line(0, 0, 15, 15, Color(255, 0, 0))

# Draw rectangle
ctx.draw_rect(4, 4, 8, 8, Color(0, 255, 0), filled=True)

# Draw circle
ctx.draw_circle(8, 8, 6, Color(0, 0, 255), filled=False)

# Draw ellipse
ctx.draw_ellipse(8, 8, 6, 4, Color(255, 255, 0), filled=True)
```

### Flood Fill

```python
# Fill an area with color
ctx.flood_fill(
    x=8,
    y=8,
    fill_color=Color(255, 0, 0),
    target_color=Color(0, 0, 0),  # Replace black with red
)
```

### Pattern Fills

```python
# Create checkerboard pattern
def checkerboard(x, y):
    return Color(255, 255, 255) if (x + y) % 2 == 0 else Color(0, 0, 0)

ctx.draw_pattern(0, 0, 16, 16, checkerboard)

# Create gradient pattern
def gradient(x, y):
    intensity = int((x / 16) * 255)
    return Color(intensity, 0, 0)

ctx.draw_pattern(0, 0, 16, 16, gradient)
```

## Advanced Techniques

### Gradients

```python
from src.rendering import create_gradient, Color

# Horizontal gradient
gradient = create_gradient(
    32, 32,
    Color(255, 0, 0),  # Red
    Color(0, 0, 255),  # Blue
    direction="horizontal"
)

# Vertical gradient
gradient = create_gradient(
    32, 32,
    Color(255, 255, 0),
    Color(0, 255, 255),
    direction="vertical"
)

# Diagonal gradient
gradient = create_gradient(
    32, 32,
    Color(0, 0, 0),
    Color(255, 255, 255),
    direction="diagonal"
)
```

### Dithering

```python
from src.rendering import DitherPattern, Color

# Ordered dithering (Bayer pattern)
DitherPattern.ordered_dither(
    grid,
    Color(0, 0, 0),      # Dark color
    Color(255, 255, 255), # Light color
)

# Pattern dithering
colors = [Color(0, 0, 0), Color(128, 128, 128), Color(255, 255, 255)]
DitherPattern.pattern_dither(
    grid,
    colors,
    pattern="checkerboard"
)
```

### Outlines

```python
from src.rendering import OutlineGenerator, Color

# Add outline around sprite
outlined_grid = OutlineGenerator.add_outline(
    grid,
    outline_color=Color(0, 0, 0),
    transparent_color=Color(255, 0, 255),
    thickness=1,
)

# For thicker outlines
thick_outlined = OutlineGenerator.add_outline(
    grid,
    outline_color=Color(0, 0, 0),
    transparent_color=Color(255, 0, 255),
    thickness=2,
)
```

## Complete Example: Creating a Simple Sprite

```python
from src.rendering import (
    PixelGrid,
    Color,
    DrawingContext,
    OutlineGenerator,
    PNGExporter,
)

# Create 16x16 grid
grid = PixelGrid(16, 16, background=Color(255, 0, 255))

# Get drawing context
ctx = DrawingContext(grid)

# Draw a simple character
# Head
ctx.draw_circle(8, 6, 3, Color(255, 224, 189), filled=True)

# Eyes
ctx.draw_pixel(7, 5, Color(0, 0, 0))
ctx.draw_pixel(9, 5, Color(0, 0, 0))

# Body
ctx.draw_rect(6, 9, 5, 4, Color(100, 100, 200), filled=True)

# Arms
ctx.draw_line(5, 10, 4, 11, Color(255, 224, 189))
ctx.draw_line(11, 10, 12, 11, Color(255, 224, 189))

# Legs
ctx.draw_line(7, 13, 7, 15, Color(50, 50, 50))
ctx.draw_line(9, 13, 9, 15, Color(50, 50, 50))

# Add outline
outlined = OutlineGenerator.add_outline(
    grid,
    outline_color=Color(0, 0, 0),
    transparent_color=Color(255, 0, 255),
    thickness=1,
)

# Export with scaling
exporter = PNGExporter(scale=4)
exporter.export(
    outlined,
    "character.png",
    transparent_color=Color(255, 0, 255),
    metadata={"type": "character", "name": "hero"},
)
```

## Game Engine Integration

### Unity Integration

```python
# Export sprite sheet with metadata
sheet = packer.pack(sprites)
sheet_grid = sheet.to_grid()

# Export PNG
exporter.export(sheet_grid, "sprites.png")

# Export metadata as JSON (Unity can parse this)
import json
with open("sprites.json", "w") as f:
    json.dump(sheet.get_metadata(), f, indent=2)
```

### Godot Integration

```python
# Godot prefers texture atlases with .tres files
# Export as PNG first, then use metadata to generate .tres

atlas_path, metadata = create_texture_atlas(sheets, "atlas.png")

# metadata["frames"] contains all sprite positions
# Use this to generate Godot's AtlasTexture resources
```

### General Game Engine Format

The metadata format is compatible with most game engines:

```json
{
  "width": 1024,
  "height": 512,
  "padding": 2,
  "frame_count": 50,
  "frames": {
    "sprite_name": {
      "name": "sprite_name",
      "x": 0,
      "y": 0,
      "width": 16,
      "height": 16
    }
  }
}
```

## Performance Tips

1. **Use numpy operations when possible**: PixelGrid internally uses numpy arrays
2. **Batch exports**: Use BatchExporter for multiple sprites
3. **Choose appropriate packing algorithm**:
   - GRID: Fast but wastes space
   - SHELF: Good balance
   - MAXRECTS: Slowest but most efficient
4. **Set reasonable max dimensions**: Smaller texture atlases load faster
5. **Use power-of-two dimensions**: Better GPU performance in many engines

## Best Practices

1. **Always use transparency**: Set a dedicated transparent color (e.g., magenta #FF00FF)
2. **Add padding in sprite sheets**: Prevents texture bleeding (2-4 pixels recommended)
3. **Use consistent scaling**: Export all sprites with the same scale factor
4. **Embed metadata**: Include generation parameters in PNG metadata
5. **Organize by type**: Group similar sprites in the same sheet
6. **Test in target engine**: Always verify exported sprites work correctly

## Troubleshooting

### Sprites too small
```python
# Increase scale factor
exporter = PNGExporter(scale=8)  # 8x scaling
```

### Texture bleeding in sprite sheets
```python
# Increase padding
packer = SpriteSheetPacker(padding=4)
```

### Colors look wrong
```python
# Verify color palette
palette = Palette.from_hex_list("my_palette", ["#color1", "#color2"])
quantized = palette.quantize_colors([original_color])
```

### Sprites don't fit in sheet
```python
# Increase max dimensions or use better algorithm
packer = SpriteSheetPacker(
    algorithm=PackingAlgorithm.MAXRECTS,
    max_width=2048,
    max_height=2048,
)
```

## See Also

- [Core Models Documentation](../src/core/models.py)
- [Agent Integration Guide](AGENT_INTEGRATION.md)
- [CLI Usage Guide](CLI_USAGE.md)