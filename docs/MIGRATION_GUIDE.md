# Vision Migration Guide

**Version:** 2.0.0  
**Last Updated:** 2025-11-18  
**Migration From:** Vision v1.x → v2.0

---

## Table of Contents

1. [Overview](#overview)
2. [What Changed](#what-changed)
3. [Breaking Changes](#breaking-changes)
4. [Migration Steps](#migration-steps)
5. [Old vs New Workflows](#old-vs-new-workflows)
6. [Configuration Changes](#configuration-changes)
7. [Script Migration](#script-migration)
8. [Troubleshooting](#troubleshooting)

---

## Overview

Vision 2.0 introduces significant workflow improvements that fundamentally change how you interact with the system. This guide will help you migrate from v1.x to v2.0 smoothly.

### Summary of Changes

**Major Improvements:**
- ✅ Automatic PNG rendering (no more manual scripts)
- ✅ Batch generation from YAML/JSON files
- ✅ Atlas texture creation
- ✅ Consistent naming (.json and .png match)
- ✅ Enhanced CLI with new commands

**Breaking Changes:**
- 🔴 Default output structure changed
- 🔴 Manifest filenames derived from description
- 🔴 New configuration format
- 🟡 Some CLI flags renamed/added

**Good News:**
- ✅ Backward compatibility mode available
- ✅ Existing manifests still work
- ✅ Gradual migration supported

---

## What Changed

### Workflow Changes

**Before (v1.x):**
```bash
# Step 1: Generate manifest
vision generate "chest" > chest.json

# Step 2: Create rendering script
cat > render.py << 'EOF'
from src.rendering import render_manifest
render_manifest("chest.json", "chest.png")
EOF

# Step 3: Run rendering script
python render.py
```

**After (v2.0):**
```bash
# Single command does everything
vision generate "chest" --dimensions 16x16

# Output:
# ✓ chest.json (manifest)
# ✓ chest.png (rendered image)
# ✓ metadata.json (generation info)
```

### File Organization Changes

**Before (v1.x):**
```
output/
├── manifest_abc123.json
└── ... (PNG created manually, anywhere)
```

**After (v2.0):**
```
output/
└── abc123-def4-5678-9012-345678901234/
    ├── chest.json          # Derived name
    ├── chest.png           # Auto-rendered
    └── metadata.json       # Generation info
```

### New Features

1. **Automatic Rendering**
   - PNG created automatically after generation
   - No manual rendering scripts needed
   - Consistent naming guaranteed

2. **Batch Generation**
   - Generate multiple assets from YAML/JSON
   - Parallel processing support
   - Optional atlas creation

3. **Atlas Textures**
   - Combine assets into sprite sheets
   - Metadata with sprite coordinates
   - Multiple packing algorithms

4. **Enhanced CLI**
   - `vision generate-batch` - Batch operations
   - `vision create-atlas` - Atlas creation
   - `vision render` - Manual rendering

---

## Breaking Changes

### 1. Output File Naming

**Before:** Manifest saved as `manifest.json` or custom filename  
**After:** Derived from description (e.g., `"wooden chest"` → `wooden_chest.json`)

**Impact:** HIGH  
**Migration:** Use `--name` flag for explicit naming

**Example:**
```bash
# v1.x behavior
vision generate "chest" > my_chest.json

# v2.0 equivalent
vision generate "chest" --name my_chest
```

### 2. Output Directory Structure

**Before:** Flat structure in output directory  
**After:** Each generation in `{request_id}/` subdirectory

**Impact:** MEDIUM  
**Migration:** Update file paths in scripts

**Example:**
```bash
# v1.x
output/manifest_abc123.json

# v2.0
output/abc123-def4-5678-9012-345678901234/chest.json
```

### 3. Automatic PNG Generation

**Before:** No PNG generated (manual rendering required)  
**After:** PNG generated automatically by default

**Impact:** LOW (feature addition)  
**Migration:** Use `--no-render` to skip PNG generation if needed

**Example:**
```bash
# v2.0 - skip rendering (like v1.x)
vision generate "chest" --no-render

# v2.0 - with rendering (default)
vision generate "chest"
```

### 4. Configuration Format

**Before:**
```env
OUTPUT_DIR=./output
```

**After:**
```env
OUTPUT_DIR=./output
RENDER_SCALE=1
TRANSPARENT_COLOR=#FF00FF
```

**Impact:** LOW  
**Migration:** Add new config options (have sensible defaults)

---

## Migration Steps

### Step 1: Backup Existing Work

```bash
# Backup current output directory
cp -r output output_backup_v1

# Backup configuration
cp .env .env.backup_v1
```

### Step 2: Update Vision

```bash
# Pull latest version
git pull origin main

# Update dependencies
pip install -e ".[dev]"

# Verify installation
vision --version  # Should show 2.0.0
```

### Step 3: Update Configuration

Add new configuration options to `.env`:

```bash
# Add to existing .env file
echo "
# v2.0 Rendering Configuration
RENDER_SCALE=1
TRANSPARENT_COLOR=#FF00FF
AUTO_RENDER=true
" >> .env
```

### Step 4: Test New Workflow

```bash
# Test single generation
vision generate "test sprite" --dimensions 16x16

# Verify output
ls output/*/
# Should see: test_sprite.json, test_sprite.png, metadata.json
```

### Step 5: Migrate Existing Scripts

See [Script Migration](#script-migration) section for details.

---

## Old vs New Workflows

### Scenario 1: Single Asset Generation

**Old Workflow (v1.x):**
```bash
# Generate manifest
vision generate "oak tree" > oak_tree.json

# Create rendering script
cat > render_oak.py << 'EOF'
from src.rendering import load_manifest, render_to_png
manifest = load_manifest("oak_tree.json")
render_to_png(manifest, "oak_tree.png")
EOF

# Run rendering
python render_oak.py

# Clean up
rm render_oak.py
```

**New Workflow (v2.0):**
```bash
# Single command
vision generate "oak tree" --dimensions 16x16

# Done! Both .json and .png created
```

---

### Scenario 2: Multiple Related Assets

**Old Workflow (v1.x):**
```bash
# Generate each manually
vision generate "wooden chest" > chest_wood.json
vision generate "stone chest" > chest_stone.json
vision generate "gold chest" > chest_gold.json

# Create batch rendering script
cat > render_all.py << 'EOF'
from src.rendering import render_manifest
for name in ["chest_wood", "chest_stone", "chest_gold"]:
    render_manifest(f"{name}.json", f"{name}.png")
EOF

# Run rendering
python render_all.py
```

**New Workflow (v2.0):**
```bash
# Create batch file
cat > chests.yaml << 'EOF'
batch_name: "chests"
output_dir: "./assets/furniture"

assets:
  - description: "wooden chest"
    name: "chest_wood"
  - description: "stone chest"
    name: "chest_stone"
  - description: "gold chest"
    name: "chest_gold"
EOF

# Generate all at once
vision generate-batch chests.yaml --parallel 2
```

---

### Scenario 3: Re-rendering with Different Settings

**Old Workflow (v1.x):**
```bash
# Modify rendering script for different scale
cat > render_scaled.py << 'EOF'
from src.rendering import render_manifest
render_manifest("sprite.json", "sprite_2x.png", scale=2)
render_manifest("sprite.json", "sprite_4x.png", scale=4)
EOF

python render_scaled.py
```

**New Workflow (v2.0):**
```bash
# Use render command with different scales
vision render sprite.json --scale 2 --output sprite_2x.png
vision render sprite.json --scale 4 --output sprite_4x.png
```

---

## Configuration Changes

### Environment Variables

**New in v2.0:**

| Variable | Default | Description |
|----------|---------|-------------|
| `RENDER_SCALE` | `1` | Default PNG scale factor |
| `TRANSPARENT_COLOR` | `#FF00FF` | Default transparency color |
| `AUTO_RENDER` | `true` | Enable automatic rendering |

**Example .env:**
```env
# Existing v1.x config
ANTHROPIC_API_KEY=sk-ant-...
REDIS_HOST=localhost
REDIS_PORT=6379

# New v2.0 config
RENDER_SCALE=1
TRANSPARENT_COLOR=#FF00FF
AUTO_RENDER=true
```

### Configuration File

**New in v2.0:** `src/core/config.py` includes `RenderingConfig`

If you've customized configuration:

```python
# Update your config overrides
from src.core.config import Settings

settings = Settings(
    # Existing settings
    anthropic_api_key="...",
    
    # New rendering settings
    rendering=RenderingConfig(
        auto_render=True,
        render_scale=1,
        transparent_color="#FF00FF"
    )
)
```

---

## Script Migration

### Pattern 1: Simple Rendering Script

**Before (v1.x):**
```python
# render.py
from src.rendering import load_manifest, render_to_png

manifest = load_manifest("sprite.json")
render_to_png(manifest, "sprite.png")
```

**After (v2.0):**
```bash
# No script needed - use CLI
vision render sprite.json
```

**Or keep script using new API:**
```python
# render.py (v2.0)
from src.rendering.manifest_renderer import ManifestRenderer

renderer = ManifestRenderer()
renderer.render_manifest_sync(
    manifest="sprite.json",
    output_path="sprite.png"
)
```

---

### Pattern 2: Batch Rendering Script

**Before (v1.x):**
```python
# render_all.py
from pathlib import Path
from src.rendering import render_manifest

for json_file in Path("output").glob("*.json"):
    png_file = json_file.with_suffix(".png")
    render_manifest(json_file, png_file)
```

**After (v2.0):**
```bash
# Use batch generation instead
vision generate-batch assets.yaml
```

**Or migrate script:**
```python
# render_all.py (v2.0)
from pathlib import Path
from src.rendering.manifest_renderer import ManifestRenderer

renderer = ManifestRenderer()
for json_file in Path("output").glob("**/*.json"):
    renderer.render_manifest_sync(json_file, json_file.with_suffix(".png"))
```

---

### Pattern 3: Automation Scripts

**Before (v1.x):**
```bash
#!/bin/bash
# generate_and_render.sh

# Generate
vision generate "sprite $1" > "sprite_$1.json"

# Render
python render.py "sprite_$1.json"
```

**After (v2.0):**
```bash
#!/bin/bash
# generate_and_render.sh

# Single command does both
vision generate "sprite $1" --name "sprite_$1" --dimensions 16x16
```

---

## Troubleshooting

### Issue: Can't Find Generated Files

**Symptom:** Files not where expected after generation

**Solution:**
```bash
# v2.0 uses request_id directories
# List recent generations
vision list

# Or search for files
find output -name "*.png" -type f

# Use explicit output directory
vision generate "sprite" --output-dir ./my_sprites
```

---

### Issue: Want Old Naming Behavior

**Symptom:** Prefer explicit filenames over derived names

**Solution:**
```bash
# Always specify --name explicitly
vision generate "complex description here" --name simple_name

# Or use wrapper script
alias vision-generate='vision generate $1 --name $2'
```

---

### Issue: Scripts Break with New Directory Structure

**Symptom:** Existing scripts can't find files

**Solution 1 - Update script paths:**
```python
# Before
manifest_path = "output/manifest.json"

# After - find by glob
import glob
manifest_path = glob.glob("output/*/manifest.json")[0]
```

**Solution 2 - Use flat output:**
```bash
# Generate to specific directory
vision generate "sprite" --output-dir ./output --name sprite

# Output: ./output/sprite.json, ./output/sprite.png
```

---

### Issue: Don't Want Automatic Rendering

**Symptom:** Only want JSON manifests (like v1.x)

**Solution:**
```bash
# Skip rendering
vision generate "sprite" --no-render

# Or set environment variable
export AUTO_RENDER=false
vision generate "sprite"
```

---

### Issue: Need Different Render Settings

**Symptom:** Want to render with custom scale/colors

**Solution:**
```bash
# Generate without rendering
vision generate "sprite" --no-render

# Render manually with custom settings
vision render output/*/sprite.json --scale 4 --transparent-color "#000000"
```

---

### Issue: Batch File Too Complex

**Symptom:** Prefer CLI for simple batches

**Solution:**
```bash
# Use shell loop for simple cases
for item in chest coin sword; do
  vision generate "$item" --category items
done

# Use batch file for complex cases (100+ assets, with atlas, etc.)
```

---

## Compatibility Mode

Vision 2.0 supports a compatibility mode for gradual migration:

```bash
# Enable v1.x compatibility
export VISION_COMPAT_MODE=v1

# This restores:
# - Flat output directory
# - No automatic rendering
# - Original naming behavior

vision generate "sprite"  # Works like v1.x
```

**Note:** Compatibility mode will be removed in v3.0. Migrate as soon as possible.

---

## Checklist: Migration Complete

Use this checklist to verify successful migration:

- [ ] Vision 2.0 installed and version verified
- [ ] Configuration updated with new options
- [ ] Test generation works (single asset)
- [ ] Test batch generation works
- [ ] Test manual rendering works
- [ ] Existing manifests can be rendered
- [ ] Automation scripts updated
- [ ] Team members informed of changes
- [ ] Old output backed up
- [ ] Documentation bookmarked

---

## Getting Help

**Documentation:**
- [Workflow Guide](WORKFLOW_GUIDE.md) - New workflow examples
- [CLI Reference](CLI_REFERENCE.md) - Complete command reference
- [Batch Guide](BATCH_GENERATION_GUIDE.md) - Batch operations

**Need More Help?**
- Check [QUICKSTART.md](../QUICKSTART.md) for setup
- Review [README.md](../README.md) for overview
- See [examples/](../examples/) for sample code

**Still Stuck?**
- Open an issue on GitHub
- Check existing issues for solutions
- Review changelog for all changes

---

## What's Next?

After migrating to v2.0, explore new features:

1. **Try batch generation:**
   ```bash
   vision generate-batch examples/batch_examples/items_batch.yaml
   ```

2. **Create texture atlases:**
   ```bash
   vision create-atlas ./output/items ./atlases --name game_items
   ```

3. **Experiment with categories:**
   ```bash
   vision generate "sword" --category weapons
   vision generate "potion" --category items
   ```

4. **Set up automation:**
   - Create batch YAML files for your game assets
   - Integrate into build pipeline
   - Generate atlases for game engine

---

**Congratulations!** You've successfully migrated to Vision 2.0. Enjoy the improved workflow!