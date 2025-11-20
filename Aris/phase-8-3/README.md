# Phase 8.3: Tools & Equipment Assets

**Priority:** High  
**Status:** Ready for Generation  
**Dependencies:** Phase 8.2 (Player Character)

---

## Overview

Phase 8.3 focuses on creating tools, weapons, and equipment sprites for the player's inventory system. These assets include farming tools, harvesting tools, combat weapons, and weapon effect animations.

## Assets in This Phase

### Farming Tools (16×16 each)

#### 1. Hoe
- **File:** `tool_hoe.png` / `tool_hoe.json`
- **Purpose:** Tilling soil for farming
- **Design:** Brown L-shaped handle with gray metal blade

#### 2. Watering Can
- **File:** `tool_watering_can.png` / `tool_watering_can.json`
- **Purpose:** Watering crops
- **Design:** Blue/gray metal can with spout

### Harvesting Tools (16×16 each)

#### 3. Axe
- **File:** `tool_axe.png` / `tool_axe.json`
- **Purpose:** Chopping trees
- **Design:** Gray metal blade with brown handle

#### 4. Pickaxe
- **File:** `tool_pickaxe.png` / `tool_pickaxe.json`
- **Purpose:** Mining rocks and ores
- **Design:** Gray pointed metal head with brown handle

#### 5. Scythe
- **File:** `tool_scythe.png` / `tool_scythe.json`
- **Purpose:** Harvesting crops
- **Design:** Silver curved blade with brown handle

#### 6. Fishing Rod
- **File:** `tool_fishing_rod.png` / `tool_fishing_rod.json`
- **Purpose:** Catching fish
- **Design:** Brown pole with visible fishing line

### Combat Weapons (16×16 each)

#### 7. Sword
- **File:** `weapon_sword.png` / `weapon_sword.json`
- **Purpose:** Melee combat
- **Design:** Silver blade with brown and gold hilt

#### 8. Bow
- **File:** `weapon_bow.png` / `weapon_bow.json`
- **Purpose:** Ranged combat
- **Design:** Brown curved wood with string

### Weapon Effects

#### 9. Weapon Swing Effect
- **File:** `weapon_swing_effect.png` / `weapon_swing_effect.json`
- **Dimensions:** 64 × 32 pixels (4 frames)
- **Animation:** 4-frame slash arc animation
- **Purpose:** Visual effect for melee weapon swings
- **Design:** White/light blue semi-transparent arc

---

## Batch Generation

### Generate All Assets

```bash
# From project root
vision generate-batch Aris/phase-8-3/assets_batch.yaml
```

### With Custom Settings

```bash
# Increase parallel processing (3 recommended for this phase)
vision generate-batch Aris/phase-8-3/assets_batch.yaml --parallel 3

# Dry run to validate
vision generate-batch Aris/phase-8-3/assets_batch.yaml --dry-run
```

---

## Expected Output

After successful generation:

```
Aris/phase-8-3/
├── assets_batch.yaml                       # Batch definition (input)
├── README.md                               # This file
├── tools/                                  # Farming and harvesting tools
│   ├── tool_hoe.png
│   ├── tool_hoe.json
│   ├── tool_watering_can.png
│   ├── tool_watering_can.json
│   ├── tool_axe.png
│   ├── tool_axe.json
│   ├── tool_pickaxe.png
│   ├── tool_pickaxe.json
│   ├── tool_scythe.png
│   ├── tool_scythe.json
│   └── tool_fishing_rod.png
│   └── tool_fishing_rod.json
├── weapons/                                # Combat weapons
│   ├── weapon_sword.png
│   ├── weapon_sword.json
│   ├── weapon_bow.png
│   └── weapon_bow.json
├── effects/                                # Combat effects
│   ├── weapon_swing_effect.png
│   └── weapon_swing_effect.json
├── phase_8_3_tools_equipment_atlas.png    # Combined texture atlas
├── phase_8_3_tools_equipment_atlas.json   # Atlas metadata
└── batch_metadata.json                     # Batch generation metadata
```

---

## Integration

### Loading Tool Icons for Inventory

**JavaScript/TypeScript Example:**
```javascript
// Load individual tool sprites
const toolSprites = {
  hoe: await loadImage('Aris/phase-8-3/tools/tool_hoe.png'),
  wateringCan: await loadImage('Aris/phase-8-3/tools/tool_watering_can.png'),
  axe: await loadImage('Aris/phase-8-3/tools/tool_axe.png'),
  pickaxe: await loadImage('Aris/phase-8-3/tools/tool_pickaxe.png'),
  scythe: await loadImage('Aris/phase-8-3/tools/tool_scythe.png'),
  fishingRod: await loadImage('Aris/phase-8-3/tools/tool_fishing_rod.png'),
  sword: await loadImage('Aris/phase-8-3/weapons/weapon_sword.png'),
  bow: await loadImage('Aris/phase-8-3/weapons/weapon_bow.png')
};

// Render tool in inventory slot
function renderInventoryItem(tool, x, y) {
  ctx.drawImage(toolSprites[tool], x, y, 16, 16);
}
```

### Using the Weapon Swing Effect

**JavaScript/TypeScript Example:**
```javascript
const swingEffect = await loadImage('Aris/phase-8-3/effects/weapon_swing_effect.png');

class WeaponSwingAnimation {
  constructor() {
    this.currentFrame = 0;
    this.maxFrames = 4;
    this.frameWidth = 16;
    this.frameHeight = 32;
  }
  
  render(x, y) {
    // Extract current frame from sprite sheet
    const srcX = this.currentFrame * this.frameWidth;
    
    ctx.globalAlpha = 0.8; // Semi-transparent
    ctx.drawImage(
      swingEffect,
      srcX, 0,                          // Source position
      this.frameWidth, this.frameHeight, // Source size
      x, y,                             // Destination position
      this.frameWidth, this.frameHeight  // Destination size
    );
    ctx.globalAlpha = 1.0;
    
    this.currentFrame = (this.currentFrame + 1) % this.maxFrames;
  }
}
```

### Using Texture Atlas (Optimized)

**JavaScript/TypeScript Example:**
```javascript
// Load atlas instead of individual sprites
const atlas = await loadImage('Aris/phase-8-3/phase_8_3_tools_equipment_atlas.png');
const atlasData = await loadJSON('Aris/phase-8-3/phase_8_3_tools_equipment_atlas.json');

function renderFromAtlas(spriteName, x, y) {
  const sprite = atlasData.sprites[spriteName];
  ctx.drawImage(
    atlas,
    sprite.x, sprite.y, sprite.width, sprite.height,  // Source
    x, y, sprite.width, sprite.height                  // Destination
  );
}

// Example usage
renderFromAtlas('tool_hoe', 10, 10);
renderFromAtlas('weapon_sword', 30, 10);
```

---

## Technical Details

### Tool Icons

All tool icons are **16×16 pixels** designed for:
- Inventory display
- Hotbar/quick access
- Item tooltips
- Crafting menus

**Style Guide:**
- Top-down or side perspective
- Clear, recognizable silhouettes
- Consistent color palette
- Black outline for visibility

### Weapon Swing Effect

**Animation Structure:**
```
Frame 0: Start of swing (small arc)
Frame 1: Mid-swing (growing arc)
Frame 2: Full extension (complete arc)
Frame 3: Fade out (dissipating arc)
```

**Sprite Sheet Layout:**
```
┌────────┬────────┬────────┬────────┐
│Frame 0 │Frame 1 │Frame 2 │Frame 3 │
│ 16x32  │ 16x32  │ 16x32  │ 16x32  │
└────────┴────────┴────────┴────────┘
 X: 0-15  X: 16-31 X: 32-47 X: 48-63
```

**Timing:** ~0.05s per frame (20 FPS) for fast swing

---

## Quality Checklist

Before approving assets, verify:

### Tools
- [ ] All tools are clearly recognizable at 16×16
- [ ] Consistent style across all tools
- [ ] Appropriate colors for materials (brown wood, gray metal, etc.)
- [ ] Clear black outlines for visibility
- [ ] Tools fit well in inventory grid

### Weapons
- [ ] Sword has clear blade and hilt
- [ ] Bow shows characteristic curved shape
- [ ] Weapons are distinct from tools
- [ ] Appropriate fantasy/medieval aesthetic

### Effects
- [ ] Swing effect has 4 distinct frames
- [ ] Arc motion is smooth and readable
- [ ] Semi-transparent appearance suitable for overlay
- [ ] Effect size appropriate for 16×32 character

### Atlas
- [ ] All sprites packed efficiently
- [ ] Proper padding between sprites (2px)
- [ ] JSON metadata is complete and accurate
- [ ] Atlas dimensions are power-of-two (if enabled)

---

## Item Categories

### By Function

**Farming:**
- Hoe (soil preparation)
- Watering Can (crop hydration)
- Scythe (harvesting)

**Resource Gathering:**
- Axe (woodcutting)
- Pickaxe (mining)
- Fishing Rod (fishing)

**Combat:**
- Sword (melee weapon)
- Bow (ranged weapon)

### By Usage Pattern

**Active Tools:** Require player action
- All tools and weapons

**Passive Items:** Equipped for stat bonuses
- (Future: armor, accessories)

---

## Troubleshooting

### Issue: Tools too similar to distinguish

**Solution:** Ensure each tool has distinctive shape and color scheme. Hoe = L-shape, Watering Can = spout, Axe = blade, etc.

### Issue: Weapon swing effect not visible

**Solution:** Verify semi-transparency is applied (80% opacity recommended). Effect should overlay on character without completely obscuring them.

### Issue: Atlas too large

**Solution:** Phase 8.3 atlas should be under 1024×1024. If exceeded, check that all sprites are correctly sized (16×16 for tools, 64×32 for effect).

---

## Next Steps

After completing Phase 8.3:

1. **Test Integration:** Load tools in inventory system
2. **Test Combat:** Verify weapon swing effects display correctly
3. **Move to Phase 8.4:** Environment assets (trees, rocks, ores)
4. **Plan Combat System:** How weapons interact with enemies

---

## Related Files

- [`../asset-list.md`](../asset-list.md) - Complete Aris asset specifications
- [`assets_batch.yaml`](assets_batch.yaml) - Batch generation definition
- [`../../docs/BATCH_GENERATION_GUIDE.md`](../../docs/BATCH_GENERATION_GUIDE.md) - Batch generation reference
- [`../../docs/RENDERING_GUIDE.md`](../../docs/RENDERING_GUIDE.md) - Asset rendering guide

---

**Last Updated:** 2025-11-18  
**Phase Status:** Ready for Generation  
**Asset Count:** 9 sprites (6 tools + 2 weapons + 1 effect animation)
