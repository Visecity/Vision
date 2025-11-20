# Phase 8.2: Player Character Assets

**Priority:** CRITICAL  
**Status:** Ready for Generation  
**Dependencies:** None

---

## Overview

Phase 8.2 focuses on creating the core player character sprite with 4-directional movement animation and its accompanying shadow. These are the most critical assets for the Aris game, as the player character is visible in all gameplay contexts.

## Assets in This Phase

### 1. Player Character Animated Sprite
- **File:** `player_animated_32.png` / `player_animated_32.json`
- **Dimensions:** 32 × 128 pixels (sprite sheet)
- **Frame Size:** 16 × 32 pixels per frame
- **Layout:** 2 columns × 4 rows (8 total frames)
- **Animation:** 2-frame walk cycle per direction
- **Directions:** 4 (Down, Up, Left, Right)

**Row Layout:**
- **Row 0 (Down/Front):** Player facing camera, feet at bottom
- **Row 1 (Up/Back):** Player facing away, back of head visible  
- **Row 2 (Left):** Player facing left in profile
- **Row 3 (Right):** Player facing right in profile

**Color Palette:**
- Skin: Beige/Tan (#F5DEB3)
- Hair: Brown (#654321)
- Shirt: Blue (#4169E1)
- Pants: Brown (#8B4513)
- Shoes: Dark Brown (#3D2817)
- Outline: Black (#000000)

### 2. Player Shadow
- **File:** `shadow.png` / `shadow.json`
- **Dimensions:** 16 × 8 pixels
- **Color:** Semi-transparent black (50% opacity)
- **Shape:** Simple oval
- **Purpose:** Rendered beneath player feet for depth perception

---

## Batch Generation

### Generate All Assets

```bash
# From project root
vision generate-batch Aris/phase-8-2/assets_batch.yaml
```

### With Custom Settings

```bash
# Increase parallel processing
vision generate-batch Aris/phase-8-2/assets_batch.yaml --parallel 3

# Dry run to validate
vision generate-batch Aris/phase-8-2/assets_batch.yaml --dry-run
```

---

## Expected Output

After successful generation:

```
Aris/phase-8-2/
├── assets_batch.yaml              # Batch definition (input)
├── README.md                       # This file
├── character/                      # Generated assets organized by category
│   ├── player_animated_32.png      # Player sprite sheet
│   ├── player_animated_32.json     # Manifest JSON with metadata
│   ├── shadow.png                  # Shadow sprite
│   └── shadow.json                 # Shadow manifest
├── phase_8_2_player_character_atlas.png    # Combined texture atlas
├── phase_8_2_player_character_atlas.json   # Atlas metadata
└── batch_metadata.json             # Batch generation metadata
```

---

## Integration

### Loading the Player Sprite

**JavaScript/TypeScript Example:**
```javascript
const playerSheet = await loadImage('Aris/phase-8-2/character/player_animated_32.png');
const playerManifest = await loadJSON('Aris/phase-8-2/character/player_animated_32.json');

// Frame size: 16x32
// Directions: Down=0, Up=1, Left=2, Right=3
// Frames per direction: 2

function getPlayerFrame(direction, frame) {
  const col = frame % 2;        // 0 or 1
  const row = direction;         // 0-3
  return {
    x: col * 16,
    y: row * 32,
    width: 16,
    height: 32
  };
}
```

### Loading the Shadow

**JavaScript/TypeScript Example:**
```javascript
const shadowSprite = await loadImage('Aris/phase-8-2/character/shadow.png');

// Render shadow at player position with 50% opacity
function renderShadow(playerX, playerY) {
  ctx.globalAlpha = 0.5;
  ctx.drawImage(shadowSprite, 
    playerX - 8,     // Center horizontally (16px / 2)
    playerY - 4,     // Center vertically (8px / 2)
    16, 8
  );
  ctx.globalAlpha = 1.0;
}
```

---

## Technical Details

### Animation System

**Walk Cycle:**
- Frame 0: Standing/Step 1
- Frame 1: Walking/Step 2
- Cycle time: ~0.15s per frame (typical)

**Direction Mapping:**
```
0 = Down (facing camera)
1 = Up (facing away)
2 = Left (profile left)
3 = Right (profile right)
```

### Sprite Sheet Structure

```
  Col 0      Col 1
┌─────────┬─────────┐
│ Down F0 │ Down F1 │  Row 0 (Y: 0-31)
├─────────┼─────────┤
│  Up F0  │  Up F1  │  Row 1 (Y: 32-63)
├─────────┼─────────┤
│ Left F0 │ Left F1 │  Row 2 (Y: 64-95)
├─────────┼─────────┤
│Right F0 │Right F1 │  Row 3 (Y: 96-127)
└─────────┴─────────┘
 X: 0-15   X: 16-31
```

---

## Quality Checklist

Before approving assets, verify:

- [ ] Player sprite has clear 16×32 frame boundaries
- [ ] All 8 frames are distinct and recognizable
- [ ] Colors are consistent across all directions
- [ ] Hair and shirt colors match in Up/Back direction
- [ ] Feet are clearly at bottom of each frame
- [ ] Shadow is properly centered oval shape
- [ ] Shadow has correct transparency (50%)
- [ ] Atlas contains all sprites with proper spacing
- [ ] JSON manifests are valid and complete

---

## Troubleshooting

### Issue: Player sprite colors inconsistent

**Solution:** The batch file specifies exact color codes. If colors vary, regenerate using the batch file to ensure consistency.

### Issue: Animation looks choppy

**Solution:** Ensure proper frame timing (0.15s recommended). The 2-frame cycle should be smooth at this rate.

### Issue: Player feet not at ground level

**Solution:** Each 16×32 frame should have feet at Y=31 (bottom). If not, regenerate assets.

---

## Next Steps

After completing Phase 8.2:

1. **Test Integration:** Load assets in game engine
2. **Verify Animation:** Test all 4 directions with walk cycles
3. **Move to Phase 8.3:** Tools & Equipment assets
4. **Iterate if needed:** Adjust colors or proportions as needed

---

## Related Files

- [`../asset-list.md`](../asset-list.md) - Complete Aris asset specifications
- [`assets_batch.yaml`](assets_batch.yaml) - Batch generation definition
- [`../../docs/BATCH_GENERATION_GUIDE.md`](../../docs/BATCH_GENERATION_GUIDE.md) - Batch generation reference
- [`../../docs/RENDERING_GUIDE.md`](../../docs/RENDERING_GUIDE.md) - Asset rendering guide

---

**Last Updated:** 2025-11-18  
**Phase Status:** Ready for Generation
