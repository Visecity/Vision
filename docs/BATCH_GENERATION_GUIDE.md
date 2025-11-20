# Vision Batch Generation Guide

**Version:** 2.0.0  
**Last Updated:** 2025-11-18  
**For:** Vision Pixel Art Generation System

---

## Table of Contents

1. [Introduction](#introduction)
2. [Batch File Format](#batch-file-format)
3. [Field Reference](#field-reference)
4. [Examples](#examples)
5. [Batch Execution](#batch-execution)
6. [Atlas Creation](#atlas-creation)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Introduction

Batch generation allows you to create multiple related pixel art assets in a single operation. This is ideal for creating collections of game items, character sets, tile sets, or any group of related assets.

### Benefits of Batch Generation

- **Efficiency**: Generate multiple assets concurrently (2-10 parallel workers)
- **Consistency**: Shared default settings ensure visual cohesion
- **Organization**: Automatic category-based file organization
- **Atlas Support**: Optionally combine assets into texture atlases
- **Error Recovery**: Continue generation even if individual assets fail

### When to Use Batch Generation

**Use batch generation when:**
- Creating collections (items, enemies, NPCs, tiles)
- Building themed asset sets (dungeon pack, forest pack)
- Generating variations (wooden/stone/iron versions)
- Need parallel processing for speed
- Want automatic atlas texture creation

**Use single generation when:**
- Creating one-off assets
- Iterating on specific designs
- Testing different parameters
- Need immediate feedback

---

## Batch File Format

Batch definitions can be written in YAML or JSON format. YAML is recommended for readability, while JSON is better for programmatic generation.

### Supported Formats

- **YAML**: `.yaml` or `.yml` extension
- **JSON**: `.json` extension

Format is auto-detected from file extension.

### Basic Structure

**YAML:**

```yaml
# Required fields
batch_name: "my_batch"
output_dir: "./output/batch"

# Optional fields
create_atlas: false
atlas_name: "my_atlas"
parallel_count: 2

# Default settings for all assets
default_style: "stardew_valley"
default_dimensions:
  width: 16
  height: 16
default_asset_type: "sprite"

# Asset definitions
assets:
  - description: "first asset"
    name: "asset_1"
  - description: "second asset"
    name: "asset_2"
```

**JSON:**

```json
{
  "batch_name": "my_batch",
  "output_dir": "./output/batch",
  "create_atlas": false,
  "parallel_count": 2,
  "default_style": "stardew_valley",
  "default_dimensions": {
    "width": 16,
    "height": 16
  },
  "assets": [
    {
      "description": "first asset",
      "name": "asset_1"
    },
    {
      "description": "second asset",
      "name": "asset_2"
    }
  ]
}
```

---

## Field Reference

### Top-Level Fields

#### `batch_name` (required)

- **Type**: string
- **Description**: Name for this batch of assets
- **Used for**: Metadata, logging, default atlas name
- **Example**: `"game_items"`, `"character_pack"`

#### `output_dir` (required)

- **Type**: string (path)
- **Description**: Directory where assets will be saved
- **Behavior**: Created if doesn't exist
- **Example**: `"./assets/items"`, `"/game/sprites/enemies"`

#### `create_atlas` (optional)

- **Type**: boolean
- **Default**: `false`
- **Description**: Automatically create texture atlas after generation
- **Example**: `true`, `false`

#### `atlas_name` (optional)

- **Type**: string
- **Default**: `{batch_name}_atlas`
- **Description**: Name for generated atlas (only if `create_atlas: true`)
- **Example**: `"items_atlas"`, `"characters_packed"`

#### `parallel_count` (optional)

- **Type**: integer
- **Default**: `2`
- **Range**: 1-10
- **Description**: Number of concurrent asset generations
- **Higher** = faster but more resources
- **Example**: `4`, `8`

### Default Settings

These apply to all assets unless overridden per-asset.

#### `default_style` (optional)

- **Type**: string
- **Default**: `"stardew_valley"`
- **Options**: `stardew_valley`, `retro_8bit`, `retro_16bit`, `pixel_art`, `custom`
- **Description**: Default art style for all assets
- **Example**: `"stardew_valley"`

#### `default_dimensions` (optional)

- **Type**: object with `width` and `height`
- **Default**: `{width: 16, height: 16}`
- **Description**: Default dimensions for all assets
- **Example**:
  ```yaml
  default_dimensions:
    width: 32
    height: 32
  ```

#### `default_asset_type` (optional)

- **Type**: string
- **Default**: `"sprite"`
- **Options**: `sprite`, `tile`, `icon`, `character`, `object`, `ui_element`
- **Description**: Default asset type classification
- **Example**: `"tile"`

### Asset Fields

Each asset in the `assets` array can have these fields:

#### `description` (required)

- **Type**: string
- **Description**: Natural language description of the asset
- **Be specific**: More detail = better results
- **Example**: `"wooden chest with metal hinges and lock"`

#### `name` (optional)

- **Type**: string
- **Default**: Derived from description
- **Description**: Asset filename (without extension)
- **Constraints**: Alphanumeric, underscores, hyphens only
- **Example**: `"chest_wood"`, `"potion_health"`

#### `dimensions` (optional)

- **Type**: array `[width, height]` or object `{width, height}`
- **Default**: Inherits from `default_dimensions`
- **Description**: Specific dimensions for this asset
- **Example**: `[16, 16]` or `{width: 16, height: 16}`

#### `style` (optional)

- **Type**: string
- **Default**: Inherits from `default_style`
- **Options**: See `default_style` options
- **Description**: Override style for this asset
- **Example**: `"retro_8bit"`

#### `asset_type` (optional)

- **Type**: string
- **Default**: Inherits from `default_asset_type`
- **Options**: See `default_asset_type` options
- **Description**: Override asset type for this asset
- **Example**: `"icon"`

#### `category` (optional)

- **Type**: string
- **Default**: None (asset in root of output_dir)
- **Description**: Subdirectory for organization
- **Example**: `"furniture"`, `"consumables"`, `"weapons/swords"`

#### `tags` (optional)

- **Type**: array of strings
- **Default**: Empty array
- **Description**: Tags for metadata and organization
- **Example**: `["furniture", "storage", "rare"]`

---

## Examples

### Example 1: Simple Item Collection

```yaml
batch_name: "basic_items"
output_dir: "./game/items"
parallel_count: 3

default_style: "stardew_valley"
default_dimensions:
  width: 16
  height: 16

assets:
  - description: "wooden chest"
    name: "chest_wood"
    tags: ["furniture", "storage"]
  
  - description: "stone chest"
    name: "chest_stone"
    tags: ["furniture", "storage"]
  
  - description: "gold chest with ornate decorations"
    name: "chest_gold"
    tags: ["furniture", "storage", "rare"]
```

**Result:**
```
game/items/
├── chest_wood.json
├── chest_wood.png
├── chest_stone.json
├── chest_stone.png
├── chest_gold.json
├── chest_gold.png
└── batch_metadata.json
```

### Example 2: Categorized Potions

```yaml
batch_name: "potions"
output_dir: "./assets"
create_atlas: true
atlas_name: "potions_atlas"
parallel_count: 2

default_dimensions:
  width: 12
  height: 16

assets:
  - description: "red health potion in glass bottle"
    name: "potion_health"
    category: "consumables"
    tags: ["potion", "healing"]
  
  - description: "blue mana potion in glass bottle"
    name: "potion_mana"
    category: "consumables"
    tags: ["potion", "magic"]
  
  - description: "green stamina potion in glass bottle"
    name: "potion_stamina"
    category: "consumables"
    tags: ["potion", "energy"]
  
  - description: "purple poison potion in glass bottle"
    name: "potion_poison"
    category: "consumables"
    tags: ["potion", "damage"]
```

**Result:**
```
assets/
├── consumables/
│   ├── potion_health.json
│   ├── potion_health.png
│   ├── potion_mana.json
│   ├── potion_mana.png
│   ├── potion_stamina.json
│   ├── potion_stamina.png
│   ├── potion_poison.json
│   └── potion_poison.png
├── potions_atlas.json
├── potions_atlas.png
└── batch_metadata.json
```

### Example 3: Mixed Dimensions and Styles

```yaml
batch_name: "ui_elements"
output_dir: "./game/ui"
parallel_count: 4

default_style: "pixel_art"
default_dimensions:
  width: 32
  height: 32

assets:
  # Square icons
  - description: "gold coin icon"
    name: "icon_coin"
    dimensions: [16, 16]
    category: "icons"
  
  - description: "heart health icon"
    name: "icon_heart"
    dimensions: [16, 16]
    category: "icons"
  
  # Rectangular buttons
  - description: "play button with arrow"
    name: "button_play"
    dimensions: [64, 32]
    category: "buttons"
  
  - description: "settings button with gear"
    name: "button_settings"
    dimensions: [64, 32]
    category: "buttons"
  
  # Large panels
  - description: "inventory panel background"
    name: "panel_inventory"
    dimensions: [128, 128]
    style: "retro_16bit"
    category: "panels"
```

### Example 4: Complete RPG Item Set

```yaml
batch_name: "rpg_items"
output_dir: "./game/assets/items"
create_atlas: true
atlas_name: "items_complete"
parallel_count: 4

default_style: "stardew_valley"
default_dimensions:
  width: 16
  height: 16
default_asset_type: "sprite"

assets:
  # Weapons
  - description: "wooden sword with brown grip"
    name: "sword_wood"
    category: "weapons"
    tags: ["weapon", "melee", "common"]
  
  - description: "iron sword with leather grip"
    name: "sword_iron"
    category: "weapons"
    tags: ["weapon", "melee", "uncommon"]
  
  - description: "steel sword with shiny blade"
    name: "sword_steel"
    category: "weapons"
    tags: ["weapon", "melee", "rare"]
  
  # Armor
  - description: "leather helmet"
    name: "helmet_leather"
    category: "armor"
    tags: ["armor", "head", "common"]
  
  - description: "iron helmet with visor"
    name: "helmet_iron"
    category: "armor"
    tags: ["armor", "head", "uncommon"]
  
  # Consumables
  - description: "red health potion"
    name: "potion_health_small"
    dimensions: [12, 16]
    category: "consumables"
    tags: ["potion", "healing", "common"]
  
  - description: "large red health potion"
    name: "potion_health_large"
    dimensions: [16, 20]
    category: "consumables"
    tags: ["potion", "healing", "uncommon"]
  
  # Currency
  - description: "copper coin"
    name: "coin_copper"
    dimensions: [8, 8]
    category: "currency"
  
  - description: "silver coin"
    name: "coin_silver"
    dimensions: [8, 8]
    category: "currency"
  
  - description: "gold coin with shine"
    name: "coin_gold"
    dimensions: [8, 8]
    category: "currency"
  
  # Tools
  - description: "wooden pickaxe for mining"
    name: "pickaxe_wood"
    category: "tools"
    tags: ["tool", "mining", "common"]
  
  - description: "iron pickaxe for mining"
    name: "pickaxe_iron"
    category: "tools"
    tags: ["tool", "mining", "uncommon"]
```

### Example 5: Tile Set Generation

```yaml
batch_name: "dungeon_tiles"
output_dir: "./game/tiles/dungeon"
create_atlas: true
atlas_name: "dungeon_tileset"
parallel_count: 6

default_style: "retro_16bit"
default_dimensions:
  width: 16
  height: 16
default_asset_type: "tile"

assets:
  # Floor tiles
  - description: "stone floor tile"
    name: "floor_stone"
    category: "floors"
  
  - description: "cracked stone floor tile"
    name: "floor_stone_cracked"
    category: "floors"
  
  - description: "mossy stone floor tile"
    name: "floor_stone_mossy"
    category: "floors"
  
  # Wall tiles
  - description: "stone wall tile"
    name: "wall_stone"
    category: "walls"
  
  - description: "stone wall with torch holder"
    name: "wall_stone_torch"
    category: "walls"
  
  # Decorations
  - description: "skull on ground"
    name: "deco_skull"
    category: "decorations"
  
  - description: "small rubble pile"
    name: "deco_rubble"
    category: "decorations"
  
  - description: "chains hanging from ceiling"
    name: "deco_chains"
    category: "decorations"
```

---

## Batch Execution

### Running a Batch

```bash
# Basic execution
vision generate-batch items.yaml

# With custom parallel count
vision generate-batch items.yaml --parallel 4

# Dry run (validate only)
vision generate-batch items.yaml --dry-run

# Stop on first error
vision generate-batch items.yaml --no-continue-on-error
```

### Parallel Processing

**How it works:**
- Assets are processed in parallel using multiple workers
- Each worker handles one asset at a time
- Progress is tracked and displayed
- Failed assets don't block others

**Worker Count Guidelines:**

| Batch Size | Recommended Workers | Rationale |
|------------|-------------------|-----------|
| 1-5 assets | 1-2 | Small overhead not worth it |
| 6-20 assets | 2-4 | Good balance |
| 21-50 assets | 4-6 | Significant speedup |
| 50+ assets | 6-10 | Maximum benefit |

**System Considerations:**
- Each worker uses ~200-500MB RAM
- Each worker makes concurrent API calls
- Monitor system resources
- Respect API rate limits

### Error Handling

**Continue on Error** (default):
```yaml
# In batch file (or use --continue-on-error)
continue_on_error: true
```
- Failed assets are logged
- Batch continues with remaining assets
- Summary shows successful/failed counts
- Exit code 0 if any succeed

**Stop on Error**:
```bash
# Via CLI flag
vision generate-batch items.yaml --no-continue-on-error
```
- Batch stops at first failure
- Partial results are saved
- Exit code 1 on any failure
- Useful for critical asset sets

### Progress Tracking

During execution, you'll see:
```
Generating assets... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 7/10 70% 00:45

Batch Generation Summary:
  Batch Name: game_items
  Total Assets: 10
  Successful: 7
  Failed: 3
  Execution Time: 45.2s

Asset Results:
  Asset          Status      Time    Details
  chest_wood     ✓ Success   4.2s    PNG: chest_wood.png
  chest_stone    ✓ Success   4.5s    PNG: chest_stone.png
  potion_health  ✗ Failed    2.1s    API timeout
  ...
```

---

## Atlas Creation

### Automatic Atlas Generation

When `create_atlas: true`, Vision automatically creates a texture atlas after all assets are generated.

**Configuration:**

```yaml
batch_name: "items"
create_atlas: true
atlas_name: "items_atlas"  # Optional, defaults to {batch_name}_atlas

# Atlas options (optional)
atlas_padding: 2           # Pixels between sprites
atlas_algorithm: "maxrects"  # Packing algorithm
atlas_power_of_two: true   # Use power-of-two dimensions
```

### Manual Atlas Creation

You can also create atlases manually after batch generation:

```bash
# Create atlas from batch output
vision create-atlas ./output/items ./atlases --name items_atlas

# With custom settings
vision create-atlas ./output/items ./atlases \
  --name items_packed \
  --algorithm MAXRECTS \
  --padding 4 \
  --max-size 2048x2048 \
  --power-of-two
```

### Atlas Metadata

Generated atlas JSON includes sprite coordinates:

```json
{
  "atlas_name": "items_atlas",
  "texture_size": [512, 256],
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
    "efficiency": 85.2
  }
}
```

---

## Best Practices

### Batch File Organization

**Keep batches focused:**
```
✓ Good: items_weapons.yaml (all weapons)
✓ Good: characters_npcs.yaml (all NPCs)
✗ Bad: game_assets.yaml (everything mixed)
```

**Use descriptive names:**
```yaml
# Good - clear and specific
batch_name: "dungeon_enemies"
batch_name: "forest_environment"

# Bad - vague
batch_name: "batch1"
batch_name: "assets"
```

### Description Quality

**Be specific and descriptive:**

```yaml
# Good descriptions
- description: "wooden chest with metal hinges and lock, slightly weathered"
- description: "red health potion in glass bottle with cork stopper"
- description: "iron sword with leather-wrapped grip and cross guard"

# Poor descriptions
- description: "chest"  # Too vague
- description: "potion"  # Not specific enough
- description: "sword"  # Missing details
```

### Default Settings Strategy

**Use defaults for consistency:**

```yaml
# Set common properties as defaults
default_style: "stardew_valley"
default_dimensions: {width: 16, height: 16}
default_asset_type: "sprite"

assets:
  # Override only when needed
  - description: "large boss sprite"
    dimensions: [32, 32]  # Override for this one asset
    
  - description: "small coin"
    dimensions: [8, 8]    # Override for small asset
    
  - description: "regular item"
    # Uses defaults (16x16)
```

### Category Organization

**Group related assets:**

```yaml
assets:
  # Weapons in weapons/ subdirectory
  - description: "wooden sword"
    category: "weapons"
  - description: "iron sword"
    category: "weapons"
  
  # Armor in armor/ subdirectory
  - description: "leather helmet"
    category: "armor"
  - description: "iron helmet"
    category: "armor"
```

### Parallel Count Optimization

**Start conservative, increase if needed:**

```yaml
# Small batch (< 10 assets)
parallel_count: 2

# Medium batch (10-30 assets)
parallel_count: 3-4

# Large batch (30-100 assets)
parallel_count: 4-6

# Very large batch (100+ assets)
parallel_count: 6-8
```

**Monitor performance:**
- Watch CPU usage
- Check API rate limits
- Monitor memory consumption
- Adjust based on results

### Atlas Planning

**When to create atlases:**
```yaml
# ✓ Create atlas for related items used together
batch_name: "ui_icons"
create_atlas: true  # All loaded as one texture

# ✓ Create atlas for tile sets
batch_name: "dungeon_tiles"
create_atlas: true  # Efficient for level rendering

# ✗ Don't create atlas for unrelated items
batch_name: "random_assets"
create_atlas: false  # Won't be used together
```

---

## Troubleshooting

### Validation Errors

**Invalid batch file:**
```
Error: Batch file validation failed:
  • Missing required field: batch_name
  • Missing required field: output_dir
  • Invalid field: parallel_count must be between 1 and 10
```

**Fix:** Ensure all required fields present and valid.

### Asset Generation Failures

**Individual asset failed:**
```
Asset Results:
  potion_health  ✗ Failed  2.1s  API timeout
```

**Causes:**
- API timeouts (network issues)
- Invalid descriptions (too vague/complex)
- API rate limits exceeded
- Insufficient API credits

**Solutions:**
1. Reduce `parallel_count` to decrease API load
2. Improve asset descriptions
3. Check API status and credits
4. Use `--continue-on-error` to skip failures

### Atlas Creation Issues

**Atlas packing failed:**
```
Error: Cannot fit all sprites in atlas (max size: 1024x1024)
```

**Solutions:**
1. Increase `max-size`: `--max-size 2048x2048`
2. Use better packing: `--algorithm MAXRECTS`
3. Reduce sprite count or dimensions
4. Split into multiple atlases

### Performance Issues

**Batch taking too long:**

**Causes:**
- Too many parallel workers (system overload)
- Large/complex assets
- Network latency
- API rate limiting

**Solutions:**
1. Reduce `parallel_count`
2. Split into smaller batches
3. Use simpler descriptions
4. Check network connection
5. Monitor API usage

### File Organization Problems

**Assets not in expected locations:**

**Check:**
1. `output_dir` setting in batch file
2. `category` fields on assets
3. File permissions for output directory
4. Disk space availability

---

## Related Documentation

- **[Workflow Guide](WORKFLOW_GUIDE.md)** - Complete workflow examples
- **[CLI Reference](CLI_REFERENCE.md)** - Command options and usage
- **[Migration Guide](MIGRATION_GUIDE.md)** - Upgrading from v1.x

---

**Example Batch Files:**

See [`examples/batch_examples/`](../examples/batch_examples/) for:
- [`items_batch.yaml`](../examples/batch_examples/items_batch.yaml) - Game items collection
- More example batch files for different use cases

**Need Help?**
- Review examples in `examples/batch_examples/`
- Check [Workflow Guide](WORKFLOW_GUIDE.md) for usage patterns
- See [CLI Reference](CLI_REFERENCE.md) for command details