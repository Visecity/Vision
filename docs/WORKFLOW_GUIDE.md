# Vision Workflow Guide

**Version:** 2.0.0  
**Last Updated:** 2025-11-18  
**For:** Vision Pixel Art Generation System

---

## Table of Contents

1. [Introduction](#introduction)
2. [What Changed](#what-changed)
3. [Quick Start](#quick-start)
4. [End-to-End Workflow](#end-to-end-workflow)
5. [File Organization](#file-organization)
6. [Configuration](#configuration)
7. [Best Practices](#best-practices)

---

## Introduction

Vision 2.0 introduces a completely streamlined workflow for pixel art generation. The system now provides end-to-end automation from text description to rendered PNG assets, with powerful batch processing and atlas generation capabilities.

### Overview of Workflow Improvements

**What's New:**
- **Automatic Rendering**: Generate both `.json` manifest and `.png` image in one command
- **Batch Generation**: Create multiple related assets from YAML/JSON definition files
- **Atlas Creation**: Combine individual assets into texture atlases for game engines
- **Consistent Naming**: Matching filenames for `.json` and `.png` outputs
- **Category Organization**: Organize assets by category (items, characters, etc.)
- **Manual Rendering**: Re-render existing manifests with custom settings

### Benefits

- **90% fewer manual steps**: From 3-4 steps to a single command
- **100% naming consistency**: No more mismatched JSON/PNG filenames
- **Parallel batch processing**: Generate multiple assets concurrently (2-10 workers)
- **Game engine ready**: Atlas textures with coordinate metadata
- **Flexible workflow**: Choose automatic or manual rendering as needed

---

## What Changed

### Previous Workflow (v1.x)

```bash
# Step 1: Generate manifest
vision generate "wooden chest" > chest.json

# Step 2: Create custom render script
# ... write Python code ...

# Step 3: Manually run renderer
python render_chest.py

# Step 4: Manage output files yourself
# ... manual file organization ...
```

**Pain Points:**
- Manual rendering scripts required
- Inconsistent file naming
- No batch support
- Manual file organization

### New Workflow (v2.0)

```bash
# Single command for complete workflow
vision generate "wooden chest" --dimensions 16x16

# Output:
# ✓ chest.json (manifest)
# ✓ chest.png (rendered image)
# ✓ metadata.json (generation info)
```

**Improvements:**
- Automatic rendering integrated
- Consistent naming guaranteed
- Batch generation built-in
- Atlas creation supported
- Category-based organization

---

## Quick Start

### Single Asset Generation

```bash
# Simple generation with auto-rendering
vision generate "wooden chest" --dimensions 16x16
```

**Output:**
```
output/
└── abc123-def4-5678-9012-345678901234/
    ├── wooden_chest.json
    ├── wooden_chest.png
    └── metadata.json
```

### With Custom Naming and Organization

```bash
vision generate "health potion" \
  --name potion_health \
  --category items \
  --dimensions 16x16
```

**Output:**
```
output/
└── abc123-def4-5678-9012-345678901234/
    └── items/
        ├── potion_health.json
        ├── potion_health.png
        └── metadata.json
```

### Batch Generation from File

```bash
# Create batch definition
cat > items.yaml << 'EOF'
batch_name: "game_items"
output_dir: "./assets/items"
create_atlas: true
parallel_count: 2

assets:
  - description: "wooden chest"
    dimensions: [16, 16]
    category: "containers"
  - description: "gold coin"
    dimensions: [8, 8]
    category: "currency"
EOF

# Generate batch
vision generate-batch items.yaml
```

**Output:**
```
assets/items/
├── wooden_chest.json
├── wooden_chest.png
├── gold_coin.json
├── gold_coin.png
├── items_atlas.json
├── items_atlas.png
└── metadata.json
```

---

## End-to-End Workflow

### Workflow 1: Single Asset Generation

**Goal**: Create a single pixel art asset

**Steps:**

1. **Generate with automatic rendering**
   ```bash
   vision generate "oak tree" --dimensions 16x16 --style stardew_valley
   ```

2. **Check output**
   ```bash
   ls output/*/
   # oak_tree.json
   # oak_tree.png
   # metadata.json
   ```

3. **View result**
   ```bash
   open output/*/oak_tree.png  # macOS
   xdg-open output/*/oak_tree.png  # Linux
   ```

**Automatic Process:**
- Multi-agent workflow generates manifest JSON
- [`ManifestRenderer`](../src/rendering/manifest_renderer.py) automatically converts to PNG
- Both files saved with matching names
- Metadata links files together

---

### Workflow 2: Batch Generation

**Goal**: Generate multiple related assets efficiently

**Steps:**

1. **Create batch definition** (`game_items.yaml`)
   ```yaml
   batch_name: "game_items"
   output_dir: "./output/items"
   create_atlas: false  # Just individual assets
   parallel_count: 3    # Use 3 parallel workers

   default_style: "stardew_valley"
   default_dimensions:
     width: 16
     height: 16

   assets:
     - description: "wooden chest with metal hinges"
       name: "chest_wood"
       category: "furniture"
     
     - description: "health potion in glass bottle"
       name: "potion_health"
       dimensions: [12, 16]
       category: "consumables"
     
     - description: "gold coin with shine"
       name: "coin_gold"
       dimensions: [8, 8]
       category: "currency"
   ```

2. **Validate batch file** (optional)
   ```bash
   vision generate-batch game_items.yaml --dry-run
   ```

3. **Generate all assets**
   ```bash
   vision generate-batch game_items.yaml --parallel 3
   ```

4. **Check output**
   ```bash
   ls output/items/
   # furniture/chest_wood.json
   # furniture/chest_wood.png
   # consumables/potion_health.json
   # consumables/potion_health.png
   # currency/coin_gold.json
   # currency/coin_gold.png
   ```

**Parallel Processing:**
- Multiple assets generated concurrently
- Default 2 workers, configurable 1-10
- Significant speedup for large batches
- Progress tracking and error recovery

---

### Workflow 3: Atlas Texture Creation

**Goal**: Combine multiple assets into a single texture atlas

**Steps:**

1. **Generate individual assets** (or use existing)
   ```bash
   vision generate-batch items.yaml --no-atlas
   ```

2. **Create texture atlas**
   ```bash
   vision create-atlas ./output/items ./output --name items_atlas
   ```

3. **Review atlas metadata**
   ```bash
   cat output/items_atlas.json
   ```

**Atlas Output:**
```json
{
  "atlas_name": "items_atlas",
  "texture_size": [256, 128],
  "packing_algorithm": "maxrects",
  "sprites": {
    "chest_wood": {
      "x": 0,
      "y": 0,
      "width": 16,
      "height": 16,
      "source_file": "furniture/chest_wood.png"
    },
    "potion_health": {
      "x": 16,
      "y": 0,
      "width": 12,
      "height": 16,
      "source_file": "consumables/potion_health.png"
    }
  },
  "metadata": {
    "generated_at": "2025-11-18T16:00:00Z",
    "total_sprites": 10,
    "padding": 2,
    "power_of_two": true,
    "efficiency": 87.5
  }
}
```

**Use in Game Engine:**
- Load `items_atlas.png` as single texture
- Use coordinate data from JSON for sprite positioning
- Reduces draw calls and improves performance

---

### Workflow 4: Manual Re-rendering

**Goal**: Render existing manifest with custom settings

**Steps:**

1. **Generate manifest only**
   ```bash
   vision generate "player sprite" --no-render --dimensions 32x32
   ```

2. **Manually render later with custom scale**
   ```bash
   vision render output/*/player_sprite.json --scale 4
   ```

3. **Result**: `player_sprite.png` at 128x128 pixels (32×4)

**Use Cases:**
- Generate different scaled versions
- Change transparent color
- Export animation frames individually
- Test rendering without regenerating manifest

---

## File Organization

### Default Directory Structure

```
output/
├── {request_id_1}/              # Individual generation
│   ├── asset_name.json
│   ├── asset_name.png
│   └── metadata.json
│
├── {request_id_2}/              # With category
│   └── category/
│       ├── asset_name.json
│       ├── asset_name.png
│       └── metadata.json
│
└── batch_{batch_name}/          # Batch generation
    ├── batch_metadata.json
    ├── category1/
    │   ├── asset1.json
    │   └── asset1.png
    ├── category2/
    │   ├── asset2.json
    │   └── asset2.png
    ├── atlas_name.json          # If atlas created
    └── atlas_name.png
```

### Naming Conventions

**Asset Names:**
- Derived from description: `"wooden chest"` → `wooden_chest`
- Explicit via `--name`: `--name chest_wood` → `chest_wood`
- Collision handling: `chest_wood_001`, `chest_wood_002`, etc.
- Maximum length: 50 characters
- Characters: `a-z`, `0-9`, `_`, `-` (lowercase, underscores, hyphens only)

**File Extensions:**
- `.json` - Manifest JSON (Vision's pixel art DSL)
- `.png` - Rendered PNG image
- Both files always have matching base names

**Category Organization:**
- Optional category subdirectories
- Specified via `--category` or in batch file
- Examples: `items`, `characters`, `furniture`, `consumables`, `weapons`
- No limit on depth: `items/potions`, `characters/npcs/merchants`

### Output Metadata

**metadata.json Structure:**
```json
{
  "request_id": "abc123-def4-5678-9012-345678901234",
  "asset_name": "chest_wood",
  "files": {
    "manifest": "furniture/chest_wood.json",
    "render": "furniture/chest_wood.png",
    "frames_dir": null
  },
  "generation": {
    "description": "wooden chest with metal hinges",
    "dimensions": "16x16",
    "style": "stardew_valley",
    "generated_at": "2025-11-18T16:00:00Z",
    "generation_time_seconds": 12.5
  },
  "rendering": {
    "rendered": true,
    "render_time_seconds": 0.3,
    "scale": 1,
    "transparent_color": "#FF00FF"
  }
}
```

---

## Configuration

### Rendering Configuration

**Location:** [`src/core/config.py`](../src/core/config.py)

**Settings:**
```python
class RenderingConfig:
    auto_render: bool = True          # Auto-render after generation
    render_scale: int = 1              # PNG scale factor (1-16)
    transparent_color: str = "#FF00FF" # Magenta transparency
    include_metadata: bool = True      # Embed metadata in PNG
    failure_strategy: str = "warn"     # "warn" or "fail"
```

**Override via CLI:**
```bash
# Skip rendering
vision generate "tree" --no-render

# Custom scale
vision generate "sprite" --render-scale 4

# Via environment variables
export RENDER_SCALE=2
export TRANSPARENT_COLOR="#FF00FF"
```

### When to Use `--no-render`

**Use `--no-render` when:**
- Testing manifest generation only
- Rendering will be done later with custom settings
- Generating many assets and will batch-render
- Debugging manifest JSON output
- Using external rendering tools

**Example:**
```bash
# Generate 10 manifests quickly
for i in {1..10}; do
  vision generate "item $i" --no-render
done

# Batch render all later
for json in output/*/*.json; do
  vision render "$json" --scale 2
done
```

### Scale Factors and Transparency

**Scale Factor Guidelines:**
```bash
# Original size (for game use)
--render-scale 1

# Double size (for editors)
--render-scale 2

# Quadruple (for preview/showcase)
--render-scale 4

# Maximum detail (for print/hi-res)
--render-scale 16
```

**Transparent Color:**
- Default: `#FF00FF` (magenta)
- Common alternatives: `#000000` (black), `#FFFFFF` (white)
- PNG uses alpha channel (not color-keyed)
- Transparent color is reference only

### Atlas Packing Algorithms

**Available Algorithms:**

1. **MAXRECTS** (recommended, default)
   - Best packing efficiency (~85-95%)
   - Good for varied sprite sizes
   - Slightly slower but worth it

2. **SHELF**
   - Good for uniform heights
   - Fast packing
   - Efficiency ~70-85%

3. **ROW**
   - Simple left-to-right packing
   - Fast, predictable
   - Lower efficiency ~60-75%

**Example Usage:**
```bash
# Use MaxRects (best efficiency)
vision create-atlas ./sprites ./output --algorithm MAXRECTS

# Use Shelf (faster, good for tiles)
vision create-atlas ./tiles ./output --algorithm SHELF --power-of-two
```

---

## Best Practices

### When to Use Single vs Batch Generation

**Use Single Generation (`vision generate`) when:**
- Creating one-off assets
- Iterating on a specific design
- Testing different parameters
- Quick prototyping
- Asset needs immediate review

**Use Batch Generation (`vision generate-batch`) when:**
- Creating asset collections (items, enemies, tiles)
- Building consistent themed sets
- Generating game level assets
- Need parallel processing for speed
- Want atlas texture output

### Choosing Packing Algorithms

**MaxRects:**
- Best for: Mixed sprite sizes, maximum efficiency
- Ideal for: Item collections, UI elements, varied assets
- Performance: Moderate (worth the wait)

**Shelf:**
- Best for: Uniform heights, tileset-like sprites
- Ideal for: Character animations, tile sets
- Performance: Fast

**Row:**
- Best for: Simple sequential layout, debugging
- Ideal for: Testing, small batches
- Performance: Fastest

### Organizing Game Assets

**Recommended Structure:**
```
game_assets/
├── characters/
│   ├── players/
│   ├── npcs/
│   └── enemies/
├── items/
│   ├── consumables/
│   ├── equipment/
│   └── currency/
├── environment/
│   ├── tiles/
│   ├── props/
│   └── background/
└── ui/
    ├── icons/
    ├── buttons/
    └── panels/
```

**Batch Files:**
```yaml
# characters_players.yaml
batch_name: "characters_players"
output_dir: "./game_assets/characters/players"
create_atlas: true
atlas_name: "players_atlas"

# items_consumables.yaml
batch_name: "items_consumables"
output_dir: "./game_assets/items/consumables"
create_atlas: true
atlas_name: "consumables_atlas"
```

### Performance Considerations

**Parallel Processing:**
- Use 2-4 workers for normal batches
- Use 6-10 workers for large batches (100+ assets)
- Monitor system resources (CPU, memory)
- Balance speed vs system load

**Batch Size Guidelines:**
- Small: 1-10 assets (sequential OK)
- Medium: 10-50 assets (use parallel: 2-4)
- Large: 50-200 assets (use parallel: 4-8)
- Very large: 200+ assets (split into multiple batches)

**Caching Benefits:**
- Vision caches LLM responses
- Identical descriptions reuse cached results
- ~40% faster on cache hits
- ~30-40% cost reduction
- Cache TTL: 1 hour (default)

### Common Workflows

**Iterative Asset Development:**
```bash
# 1. Generate initial version
vision generate "sword sprite" --name sword_v1

# 2. Review and adjust description
vision generate "iron sword with leather grip" --name sword_v2

# 3. Generate variations
vision generate "iron sword, shiny steel blade" --name sword_shiny
vision generate "iron sword, battle-worn" --name sword_worn

# 4. Choose best, create scaled versions
vision render output/*/sword_shiny.json --scale 2
vision render output/*/sword_shiny.json --scale 4
```

**Building Item Collections:**
```bash
# 1. Create batch file with all items
cat > rpg_items.yaml << 'EOF'
batch_name: "rpg_items"
output_dir: "./game/items"
create_atlas: true
parallel_count: 4

assets:
  - description: "health potion"
    category: "potions"
  - description: "mana potion"
    category: "potions"
  - description: "iron sword"
    category: "weapons"
  # ... more items ...
EOF

# 2. Generate all items
vision generate-batch rpg_items.yaml

# 3. Atlas is automatically created
# game/items/rpg_items_atlas.png
# game/items/rpg_items_atlas.json
```

**Creating Animation Sets:**
```bash
# 1. Generate animation frames
vision generate "player walking animation" \
  --animate --frames 8 \
  --dimensions 32x32 \
  --name player_walk

# Output: player_walk.json (all frames in spritesheet)
#         player_walk.png (horizontal strip)

# 2. Can export individual frames if needed
vision render output/*/player_walk.json --export-frames
```

---

## Related Documentation

- **[CLI Reference](CLI_REFERENCE.md)** - Complete command reference
- **[Batch Generation Guide](BATCH_GENERATION_GUIDE.md)** - Batch operation details
- **[Migration Guide](MIGRATION_GUIDE.md)** - Upgrading from v1.x
- **[Technical Specification](../WORKFLOW_IMPROVEMENTS_DESIGN.md)** - Implementation details

---

**Need Help?**
- Check [`examples/batch_examples/`](../examples/batch_examples/) for sample batch files
- Review [`QUICKSTART.md`](../QUICKSTART.md) for setup guide
- See [`README.md`](../README.md) for project overview