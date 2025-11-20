# Vision CLI Reference

**Version:** 2.0.0  
**Last Updated:** 2025-11-18  
**For:** Vision Pixel Art Generation System

---

## Table of Contents

1. [Overview](#overview)
2. [vision generate](#vision-generate)
3. [vision generate-batch](#vision-generate-batch)
4. [vision create-atlas](#vision-create-atlas)
5. [vision render](#vision-render)
6. [Other Commands](#other-commands)
7. [Global Options](#global-options)
8. [Exit Codes](#exit-codes)

---

## Overview

Vision provides a comprehensive CLI for pixel art generation, batch processing, and asset management. All commands follow consistent patterns and provide rich terminal output.

### Command Structure

```bash
vision [COMMAND] [ARGUMENTS] [OPTIONS]
```

### Getting Help

```bash
# Show all available commands
vision --help

# Show help for specific command
vision generate --help
vision generate-batch --help
vision create-atlas --help
vision render --help
```

---

## vision generate

Generate a single pixel art asset with automatic rendering.

### Synopsis

```bash
vision generate DESCRIPTION [OPTIONS]
```

### Arguments

**`DESCRIPTION`** (required)
- Text description of the asset to generate
- Natural language, be descriptive
- Example: `"wooden chest with metal hinges"`

### Options

#### Asset Configuration

**`--dimensions WxH`**, **`-d WxH`**
- Asset dimensions in pixels
- Format: `WIDTHxHEIGHT` (e.g., `16x16`, `32x32`)
- Default: `16x16`
- Examples: `16x16`, `32x32`, `64x64`, `128x64`

**`--style STYLE`**, **`-s STYLE`**
- Art style for generation
- Default: `stardew_valley`
- Available styles:
  - `stardew_valley` - Stardew Valley inspired pixel art
  - `retro_8bit` - Classic 8-bit game style
  - `retro_16bit` - 16-bit era console style
  - `pixel_art` - General pixel art style
  - `custom` - Custom style (requires additional parameters)

**`--type TYPE`**, **`-t TYPE`**
- Asset type classification
- Default: `sprite`
- Available types:
  - `sprite` - General game sprite
  - `tile` - Tile for tilesets
  - `icon` - UI icon or small graphic
  - `character` - Character sprite
  - `object` - Environmental object
  - `ui_element` - UI component

#### Animation Options

**`--animate`**, **`-a`**
- Generate animation frames
- Creates sprite sheet with multiple frames
- Default: `false`

**`--frames COUNT`**, **`-f COUNT`**
- Number of animation frames
- Only used with `--animate`
- Default: `4`
- Range: 2-32 frames

**`--frame-duration MS`**
- Duration of each frame in milliseconds
- Only used with `--animate`
- Default: `200` ms
- Range: 50-1000 ms

#### Naming and Organization

**`--name NAME`**
- Custom asset name (without extension)
- Default: Derived from description
- Must be valid filename (alphanumeric, underscores, hyphens)
- Max length: 50 characters
- Example: `chest_wood`, `potion_health_large`

**`--category CATEGORY`**
- Category for file organization
- Creates subdirectory for asset
- Examples: `items`, `characters`, `furniture`, `weapons`
- Can use paths: `items/consumables`, `characters/npcs`

**`--output-dir DIR`**, **`-o DIR`**
- Output directory for generated files
- Default: `./output/{request_id}/`
- Directory created if doesn't exist

#### Rendering Options

**`--no-render`**
- Skip automatic PNG rendering
- Only generates manifest JSON
- Useful for batch operations or manual rendering
- Default: Rendering enabled

**`--render-scale SCALE`**
- PNG scaling factor
- Range: 1-16
- Default: `1` (original size)
- Example: `--render-scale 4` creates 4x larger PNG

#### Other Options

**`--session-id ID`**
- Session ID for grouping related generations
- Default: Auto-generated
- Useful for tracking related assets

**`--interactive`**, **`-i`**
- Interactive mode with prompts
- Asks for parameters step-by-step
- Good for beginners or exploratory use

**`--json`**
- Output results as JSON
- Useful for scripting and automation
- Suppresses pretty-printed output

**`--verbose`**, **`-v`**
- Enable verbose output
- Shows detailed progress and debug information
- Includes error traces

### Examples

#### Basic Usage

```bash
# Simple sprite generation
vision generate "oak tree"

# With specific dimensions
vision generate "wooden chest" --dimensions 16x16

# Different art style
vision generate "space ship" --style retro_8bit --dimensions 32x32
```

#### Custom Naming and Organization

```bash
# Custom name
vision generate "health potion" --name potion_health

# With category
vision generate "iron sword" --category weapons

# Both name and category
vision generate "gold coin" --name coin_gold --category currency
```

#### Animation Generation

```bash
# Simple 4-frame animation
vision generate "player walking" --animate --dimensions 32x32

# Custom frame count
vision generate "fire effect" --animate --frames 8 --dimensions 16x16

# With frame duration
vision generate "water ripple" --animate --frames 6 --frame-duration 150
```

#### Rendering Options

```bash
# Generate JSON only (no PNG)
vision generate "background tile" --no-render

# Generate with 4x scaling
vision generate "player sprite" --render-scale 4 --dimensions 32x32

# JSON only, render manually later
vision generate "complex animation" --no-render --animate --frames 16
vision render output/*/complex_animation.json --scale 2
```

#### Interactive Mode

```bash
# Launch interactive wizard
vision generate --interactive

# Prompts will ask for:
# - Description
# - Dimensions
# - Style
# - Animation (yes/no)
# - Frame count (if animated)
```

### Output

**Files Created:**

```
output/{request_id}/
├── {asset_name}.json      # Manifest JSON
├── {asset_name}.png       # Rendered PNG (unless --no-render)
└── metadata.json          # Generation metadata
```

**With Category:**

```
output/{request_id}/{category}/
├── {asset_name}.json
├── {asset_name}.png
└── metadata.json
```

### Exit Codes

- `0` - Success
- `1` - General error (invalid arguments, generation failed)
- `130` - User cancelled (Ctrl+C)

---

## vision generate-batch

Generate multiple assets from a batch definition file.

### Synopsis

```bash
vision generate-batch BATCH_FILE [OPTIONS]
```

### Arguments

**`BATCH_FILE`** (required)
- Path to batch definition file
- Supports YAML (`.yaml`, `.yml`) and JSON (`.json`)
- Must exist and be readable
- See [Batch Generation Guide](BATCH_GENERATION_GUIDE.md) for file format

### Options

**`--parallel COUNT`**, **`-p COUNT`**
- Number of concurrent generations
- Range: 1-10
- Default: `2`
- Overrides `parallel_count` in batch file
- Higher values = faster but more resource intensive

**`--dry-run`**
- Validate batch file without generating
- Checks file format and asset definitions
- Useful for testing batch files
- No API calls made

**`--continue-on-error`** / **`--no-continue-on-error`**
- Continue batch if individual assets fail
- Default: `true` (continue on error)
- Use `--no-continue-on-error` to stop at first error

**`--verbose`**, **`-v`**
- Enable verbose output
- Shows detailed progress for each asset
- Includes error traces

### Batch File Format

**YAML Example:**

```yaml
batch_name: "game_items"
output_dir: "./assets/items"
create_atlas: true
atlas_name: "items_atlas"
parallel_count: 2

# Default settings for all assets
default_style: "stardew_valley"
default_dimensions:
  width: 16
  height: 16
default_asset_type: "sprite"

# Asset definitions
assets:
  - description: "wooden chest with metal hinges"
    name: "chest_wood"
    category: "containers"
    tags: ["furniture", "storage"]
  
  - description: "health potion in glass bottle"
    name: "potion_health"
    dimensions: [12, 16]
    category: "consumables"
    tags: ["potion", "healing"]
  
  - description: "gold coin with shine"
    name: "coin_gold"
    dimensions: [8, 8]
    category: "currency"
```

**JSON Example:**

```json
{
  "batch_name": "game_items",
  "output_dir": "./assets/items",
  "create_atlas": true,
  "parallel_count": 2,
  "default_style": "stardew_valley",
  "default_dimensions": {
    "width": 16,
    "height": 16
  },
  "assets": [
    {
      "description": "wooden chest",
      "name": "chest_wood",
      "category": "containers"
    },
    {
      "description": "health potion",
      "name": "potion_health",
      "category": "consumables"
    }
  ]
}
```

### Examples

#### Basic Batch Generation

```bash
# Generate from YAML file
vision generate-batch items.yaml

# Generate from JSON file
vision generate-batch assets.json
```

#### With Custom Parallel Count

```bash
# Use 4 parallel workers
vision generate-batch large_batch.yaml --parallel 4

# Sequential generation (1 worker)
vision generate-batch small_batch.yaml --parallel 1
```

#### Validation and Dry Run

```bash
# Validate batch file without generating
vision generate-batch items.yaml --dry-run

# Check for errors before running expensive batch
vision generate-batch complex_batch.yaml --dry-run
```

#### Error Handling

```bash
# Stop at first error
vision generate-batch items.yaml --no-continue-on-error

# Continue despite errors (default)
vision generate-batch items.yaml --continue-on-error

# Verbose output for debugging
vision generate-batch items.yaml --verbose
```

### Output

**Batch Output Structure:**

```
{output_dir}/
├── batch_metadata.json      # Batch execution info
├── {category1}/
│   ├── asset1.json
│   ├── asset1.png
│   ├── asset2.json
│   └── asset2.png
├── {category2}/
│   ├── asset3.json
│   └── asset3.png
├── {atlas_name}.json        # If create_atlas: true
└── {atlas_name}.png         # If create_atlas: true
```

**Batch Metadata:**

```json
{
  "batch_name": "game_items",
  "total_requests": 10,
  "successful": 9,
  "failed": 1,
  "execution_time": 45.2,
  "started_at": "2025-11-18T16:00:00Z",
  "completed_at": "2025-11-18T16:00:45Z",
  "assets": [
    {
      "name": "chest_wood",
      "success": true,
      "generation_time": 4.2,
      "json_path": "containers/chest_wood.json",
      "png_path": "containers/chest_wood.png"
    }
  ],
  "errors": []
}
```

### Exit Codes

- `0` - Success (all assets generated)
- `0` - Partial success (some failed but `--continue-on-error`)
- `1` - Failure (validation failed, no assets generated, or error with `--no-continue-on-error`)
- `130` - User cancelled (Ctrl+C)

---

## vision create-atlas

Create texture atlas from existing PNG assets.

### Synopsis

```bash
vision create-atlas ASSET_DIR OUTPUT_DIR [OPTIONS]
```

### Arguments

**`ASSET_DIR`** (required)
- Directory containing PNG assets to pack
- Must exist and contain at least one `.png` file
- Searches for `*.png` by default
- Example: `./output/items/`

**`OUTPUT_DIR`** (required)
- Directory for atlas output files
- Created if doesn't exist
- Atlas PNG and JSON saved here
- Example: `./atlases/`

### Options

**`--name NAME`**, **`-n NAME`** (required)
- Atlas base name (without extension)
- Used for output files: `{name}.png`, `{name}.json`
- Example: `items_atlas`, `characters_packed`

**`--algorithm ALGORITHM`**, **`-a ALGORITHM`**
- Sprite packing algorithm
- Default: `MAXRECTS`
- Available algorithms:
  - `MAXRECTS` - Best packing efficiency (~85-95%)
  - `SHELF` - Good for uniform heights (~70-85%)
  - `ROW` - Simple sequential packing (~60-75%)
  - `COLUMN` - Column-wise packing
  - `GRID` - Regular grid layout
- Case insensitive

**`--padding PIXELS`**
- Padding between sprites in pixels
- Default: `2`
- Range: 0-16 pixels
- Useful to prevent texture bleeding

**`--max-size WxH`**
- Maximum atlas dimensions
- Format: `WIDTHxHEIGHT`
- Default: `1024x1024`
- Maximum: `4096x4096`
- Example: `2048x2048`, `1024x2048`

**`--power-of-two`** / **`--no-power-of-two`**
- Force power-of-two dimensions (256, 512, 1024, 2048, etc.)
- Default: `true` (power-of-two enabled)
- Recommended for GPU texture optimization
- Use `--no-power-of-two` for exact dimensions

**`--verbose`**, **`-v`**
- Show detailed packing information
- Lists all sprite coordinates
- Shows packing efficiency statistics

### Examples

#### Basic Atlas Creation

```bash
# Create atlas with default settings
vision create-atlas ./output/items ./atlases --name items_atlas

# Output:
# atlases/items_atlas.png (texture)
# atlases/items_atlas.json (metadata)
```

#### Custom Packing Algorithm

```bash
# Use MaxRects for best efficiency
vision create-atlas ./sprites ./output --name packed --algorithm MAXRECTS

# Use Shelf for uniform heights
vision create-atlas ./tiles ./output --name tiles --algorithm SHELF

# Use Row for simple packing
vision create-atlas ./icons ./output --name icons --algorithm ROW
```

#### Size and Padding Options

```bash
# Larger atlas with padding
vision create-atlas ./assets ./output \
  --name large_atlas \
  --max-size 2048x2048 \
  --padding 4

# No padding, non-power-of-two
vision create-atlas ./assets ./output \
  --name exact_atlas \
  --padding 0 \
  --no-power-of-two \
  --max-size 1920x1080
```

#### Verbose Output

```bash
# Show detailed sprite coordinates
vision create-atlas ./sprites ./output \
  --name detailed \
  --verbose

# Output includes:
# Sprite coordinates for each asset
# Packing efficiency percentage
# Final atlas dimensions
```

### Output

**Atlas Files:**

```
{output_dir}/
├── {name}.png              # Combined texture atlas
└── {name}.json             # Sprite coordinate metadata
```

**Atlas Metadata JSON:**

```json
{
  "atlas_name": "items_atlas",
  "texture_size": [1024, 512],
  "packing_algorithm": "maxrects",
  "sprites": {
    "chest_wood": {
      "x": 0,
      "y": 0,
      "width": 16,
      "height": 16,
      "source_file": "containers/chest_wood.png"
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

### Exit Codes

- `0` - Success
- `1` - Error (no PNG files, packing failed, invalid parameters)
- `130` - User cancelled (Ctrl+C)

---

## vision render

Manually render manifest JSON to PNG.

### Synopsis

```bash
vision render MANIFEST_PATH [OPTIONS]
```

### Arguments

**`MANIFEST_PATH`** (required)
- Path to manifest JSON file
- Must exist and be valid JSON
- Example: `output/abc123/sprite.json`

### Options

**`--output PATH`**, **`-o PATH`**
- Output PNG path
- Default: Same directory and name as manifest
- Example: `--output sprites/custom_name.png`

**`--scale SCALE`**, **`-s SCALE`**
- PNG scaling factor
- Range: 1-16
- Default: `1`
- Example: `--scale 4` creates 4x larger image

**`--transparent-color HEX`**
- Color to treat as transparent
- Format: `#RRGGBB` hex color
- Default: `#FF00FF` (magenta)
- Example: `--transparent-color "#000000"`

**`--verbose`**, **`-v`**
- Show detailed rendering information
- Includes image dimensions and file size
- Shows rendering timing

### Examples

#### Basic Rendering

```bash
# Render to default location
vision render chest.json

# Output: chest.png (same directory)
```

#### Custom Output Path

```bash
# Specify output file
vision render manifest.json --output sprites/chest.png

# Different directory and name
vision render player.json --output ../game/assets/player_sprite.png
```

#### Scaled Rendering

```bash
# Render at 2x size
vision render sprite.json --scale 2

# Render at 4x for preview
vision render icon.json --scale 4 --output preview/icon_large.png
```

#### Custom Transparency

```bash
# Use black as transparent
vision render sprite.json --transparent-color "#000000"

# Use white as transparent
vision render icon.json --transparent-color "#FFFFFF"
```

#### Verbose Output

```bash
# Show detailed information
vision render complex.json --verbose

# Output includes:
# - Rendering time
# - Image dimensions
# - File size
# - Color mode
```

### Output

**Files Created:**

```
{output_path}.png           # Rendered PNG image
```

**Console Output:**

```
Rendering manifest: sprite.json

Settings:
  Scale: 2x
  Transparent color: #FF00FF
  Output: sprite.png

Rendering...

✓ Rendering complete!
  PNG saved to: sprite.png
  File size: 2.3 KB
```

### Exit Codes

- `0` - Success
- `1` - Error (invalid manifest, rendering failed)
- `130` - User cancelled (Ctrl+C)

---

## Other Commands

### vision status

Show current generation status and recent history.

```bash
vision status [OPTIONS]

Options:
  --session-id ID    Show status for specific session
  --json             Output as JSON
```

### vision list

List recent generations.

```bash
vision list [OPTIONS]

Options:
  --limit COUNT      Number of generations to show (default: 10)
  --session-id ID    Filter by session
  --json             Output as JSON
```

### vision config

View or modify Vision configuration.

```bash
# Show current config
vision config show

# Set config value
vision config set KEY VALUE

# Reset to defaults
vision config reset
```

### vision info

Display system and version information.

```bash
vision info

# Shows:
# - Vision version
# - Python version
# - Redis status
# - API configuration
# - Available models
```

---

## Global Options

These options work with all commands:

**`--help`**, **`-h`**
- Show command help
- Works with any command
- Example: `vision generate --help`

**`--version`**
- Show Vision version
- Example: `vision --version`

**`--no-color`**
- Disable colored output
- Useful for logging or non-terminal output
- Example: `vision generate "tree" --no-color`

---

## Exit Codes

Vision uses standard POSIX exit codes:

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error (invalid arguments, generation failed, file not found) |
| `2` | Misuse of shell command (invalid syntax) |
| `130` | Script terminated by Ctrl+C (SIGINT) |

### Checking Exit Codes

```bash
# Bash/Zsh
vision generate "tree"
echo $?  # 0 for success, non-zero for error

# Use in scripts
if vision generate "tree" --no-render; then
  echo "Generation successful"
  vision render output/*/tree.json
else
  echo "Generation failed"
  exit 1
fi
```

---

## Environment Variables

Vision respects these environment variables:

**`ANTHROPIC_API_KEY`**
- Your Anthropic API key
- Required for generation
- Can be set in `.env` file

**`REDIS_HOST`**
- Redis server hostname
- Default: `localhost`

**`REDIS_PORT`**
- Redis server port
- Default: `6379`

**`OUTPUT_DIR`**
- Default output directory
- Overrides config setting
- Default: `./output`

**`RENDER_SCALE`**
- Default render scale factor
- Range: 1-16
- Default: `1`

**`NO_COLOR`**
- Disable colored output
- Set to any value to disable
- Same as `--no-color` flag

---

## Tips and Tricks

### Batch Operations with Shell

```bash
# Generate multiple assets sequentially
for item in chest sword shield; do
  vision generate "$item" --category weapons
done

# Parallel generation with GNU parallel
parallel -j 4 vision generate ::: "tree" "rock" "flower" "bush"
```

### JSON Output for Scripting

```bash
# Capture JSON output
result=$(vision generate "tree" --json)
request_id=$(echo "$result" | jq -r '.request_id')
echo "Generated: $request_id"

# Check if generation succeeded
if echo "$result" | jq -e '.status == "completed"' > /dev/null; then
  echo "Success!"
fi
```

### Using with Make

```makefile
# Makefile for game assets
assets: items characters environment

items:
	vision generate-batch items.yaml

characters:
	vision generate-batch characters.yaml

environment:
	vision generate-batch environment.yaml

atlas:
	vision create-atlas ./output/items ./atlases --name items
	vision create-atlas ./output/characters ./atlases --name characters

clean:
	rm -rf output/ atlases/
```

---

## See Also

- **[Workflow Guide](WORKFLOW_GUIDE.md)** - Complete workflow examples
- **[Batch Generation Guide](BATCH_GENERATION_GUIDE.md)** - Batch operation details
- **[Migration Guide](MIGRATION_GUIDE.md)** - Upgrading from v1.x
- **[QUICKSTART.md](../QUICKSTART.md)** - Getting started guide

---

**Questions or Issues?**
- Check the [Workflow Guide](WORKFLOW_GUIDE.md) for usage examples
- Review [QUICKSTART.md](../QUICKSTART.md) for setup help
- See [README.md](../README.md) for project overview