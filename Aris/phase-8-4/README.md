# Phase 8.4: Environment Assets

**Priority:** High  
**Status:** Ready for Generation  
**Dependencies:** Phase 8.3 (Tools & Equipment)

---

## Overview

Phase 8.4 focuses on creating static environmental objects that populate the game world. This includes trees, rocks, ore nodes, and fences - the core building blocks for creating diverse outdoor environments.

## Assets in This Phase

### Trees

#### 1. Oak Tree
- **File:** `tree_oak.png` / `tree_oak.json`
- **Dimensions:** 16 × 32 pixels
- **Type:** Deciduous tree
- **Colors:** Green canopy (#228B22), brown trunk (#8B4513)
- **Footprint:** 12×8 pixels at base
- **Purpose:** Natural obstacles, woodcutting resource

#### 2. Pine Tree
- **File:** `tree_pine.png` / `tree_pine.json`
- **Dimensions:** 16 × 32 pixels
- **Type:** Evergreen conifer
- **Colors:** Dark green needles (#006400), dark brown trunk (#654321)
- **Footprint:** 12×8 pixels at base
- **Purpose:** Forest biome, woodcutting resource

#### 3. Tree Stump
- **File:** `tree_stump.png` / `tree_stump.json`
- **Dimensions:** 16 × 16 pixels
- **Type:** Chopped tree remnant
- **Colors:** Brown with visible tree rings
- **Purpose:** Post-harvest state of trees

### Rocks & Ores

#### 4. Small Rock
- **File:** `rock_small.png` / `rock_small.json`
- **Dimensions:** 16 × 16 pixels
- **Colors:** Gray tones (#808080, #A9A9A9, #696969)
- **Purpose:** Small obstacles, mining resource

#### 5. Large Rock
- **File:** `rock_large.png` / `rock_large.json`
- **Dimensions:** 16 × 24 pixels
- **Colors:** Gray tones with depth
- **Purpose:** Larger obstacles, mining resource

#### 6. Iron Ore Node
- **File:** `ore_iron.png` / `ore_iron.json`
- **Dimensions:** 16 × 16 pixels
- **Colors:** Gray rock with silver metallic veins
- **Purpose:** Iron mining resource

#### 7. Copper Ore Node
- **File:** `ore_copper.png` / `ore_copper.json`
- **Dimensions:** 16 × 16 pixels
- **Colors:** Gray rock with orange-copper veins
- **Purpose:** Copper mining resource

#### 8. Gold Ore Node
- **File:** `ore_gold.png` / `ore_gold.json`
- **Dimensions:** 16 × 16 pixels
- **Colors:** Gray rock with golden yellow veins
- **Purpose:** Gold mining resource (rare)

### Fences

#### 9. Wooden Fence (Standalone)
- **File:** `fence_wood_standalone.png` / `fence_wood_standalone.json`
- **Dimensions:** 16 × 16 pixels
- **Purpose:** Single fence post, not connected

#### 10. Wooden Fence (End)
- **File:** `fence_wood_end.png` / `fence_wood_end.json`
- **Dimensions:** 16 × 16 pixels
- **Purpose:** End cap for fence lines

#### 11. Wooden Fence (Middle)
- **File:** `fence_wood_middle.png` / `fence_wood_middle.json`
- **Dimensions:** 16 × 16 pixels
- **Purpose:** Connecting segment for fence lines

#### 12. Wooden Fence (Corner)
- **File:** `fence_wood_corner.png` / `fence_wood_corner.json`
- **Dimensions:** 16 × 16 pixels
- **Purpose:** 90-degree corner piece

---

## Batch Generation

### Generate All Assets

```bash
# From project root
vision generate-batch Aris/phase-8-4/assets_batch.yaml
```

### With Custom Settings

```bash
# Increase parallel processing (4 recommended for this larger phase)
vision generate-batch Aris/phase-8-4/assets_batch.yaml --parallel 4

# Dry run to validate
vision generate-batch Aris/phase-8-4/assets_batch.yaml --dry-run
```

---

## Expected Output

After successful generation:

```
Aris/phase-8-4/
├── assets_batch.yaml                       # Batch definition (input)
├── README.md                               # This file
├── terrain/                                # Trees and natural elements
│   ├── tree_oak.png
│   ├── tree_oak.json
│   ├── tree_pine.png
│   ├── tree_pine.json
│   ├── tree_stump.png
│   ├── tree_stump.json
│   ├── rock_small.png
│   ├── rock_small.json
│   ├── rock_large.png
│   └── rock_large.json
├── resources/                              # Ore nodes
│   ├── ore_iron.png
│   ├── ore_iron.json
│   ├── ore_copper.png
│   ├── ore_copper.json
│   ├── ore_gold.png
│   └── ore_gold.json
├── objects/                                # Fences and structures
│   ├── fence_wood_standalone.png
│   ├── fence_wood_standalone.json
│   ├── fence_wood_end.png
│   ├── fence_wood_end.json
│   ├── fence_wood_middle.png
│   ├── fence_wood_middle.json
│   ├── fence_wood_corner.png
│   └── fence_wood_corner.json
├── phase_8_4_environment_atlas.png        # Combined texture atlas
├── phase_8_4_environment_atlas.json       # Atlas metadata
└── batch_metadata.json                     # Batch generation metadata
```

---

## Integration

### Loading Environment Objects

**JavaScript/TypeScript Example:**
```javascript
// Load terrain sprites
const terrain = {
  oakTree: await loadImage('Aris/phase-8-4/terrain/tree_oak.png'),
  pineTree: await loadImage('Aris/phase-8-4/terrain/tree_pine.png'),
  stump: await loadImage('Aris/phase-8-4/terrain/tree_stump.png'),
  rockSmall: await loadImage('Aris/phase-8-4/terrain/rock_small.png'),
  rockLarge: await loadImage('Aris/phase-8-4/terrain/rock_large.png')
};

// Load ore sprites
const ores = {
  iron: await loadImage('Aris/phase-8-4/resources/ore_iron.png'),
  copper: await loadImage('Aris/phase-8-4/resources/ore_copper.png'),
  gold: await loadImage('Aris/phase-8-4/resources/ore_gold.png')
};

// Render tree with proper positioning
function renderTree(tree, x, y) {
  // Trees are 16x32, position is at base (feet)
  // Draw so base aligns with y coordinate
  ctx.drawImage(tree, x - 8, y - 32, 16, 32);
}
```

### Collision Detection

**Example Collision System:**
```javascript
class EnvironmentObject {
  constructor(sprite, x, y, footprintWidth, footprintHeight) {
    this.sprite = sprite;
    this.x = x;
    this.y = y;
    this.footprintWidth = footprintWidth;
    this.footprintHeight = footprintHeight;
  }
  
  getCollisionBox() {
    // Return collision box at object's base
    return {
      x: this.x - this.footprintWidth / 2,
      y: this.y - this.footprintHeight,
      width: this.footprintWidth,
      height: this.footprintHeight
    };
  }
  
  checkCollision(playerX, playerY, playerRadius = 8) {
    const box = this.getCollisionBox();
    // Simple circle-rect collision
    return (
      playerX + playerRadius > box.x &&
      playerX - playerRadius < box.x + box.width &&
      playerY + playerRadius > box.y &&
      playerY - playerRadius < box.y + box.height
    );
  }
}

// Create tree with collision
const oakTree = new EnvironmentObject(
  terrain.oakTree, 
  100, 100,  // Position
  12, 8      // Footprint: 12x8 pixels
);
```

### Smart Fence Placement System

**Example Fence Connection Logic:**
```javascript
class FenceSystem {
  constructor() {
    this.fences = new Map(); // key: "x,y", value: fence type
  }
  
  getFenceType(x, y) {
    const key = `${x},${y}`;
    const hasLeft = this.fences.has(`${x-16},${y}`);
    const hasRight = this.fences.has(`${x+16},${y}`);
    const hasUp = this.fences.has(`${x},${y-16}`);
    const hasDown = this.fences.has(`${x},${y+16}`);
    
    const connections = [hasLeft, hasRight, hasUp, hasDown];
    const count = connections.filter(c => c).length;
    
    if (count === 0) return 'standalone';
    if (count === 1) return 'end';
    if (count === 2) {
      // Check if corner (perpendicular connections)
      if ((hasLeft || hasRight) && (hasUp || hasDown)) {
        return 'corner';
      }
      return 'middle';
    }
    // 3+ connections - use middle for now
    return 'middle';
  }
  
  placeFence(x, y) {
    const key = `${x},${y}`;
    const type = this.getFenceType(x, y);
    this.fences.set(key, type);
    
    // Update adjacent fences
    this.updateAdjacent(x, y);
  }
}
```

### Using Texture Atlas (Optimized)

**JavaScript/TypeScript Example:**
```javascript
// Load atlas instead of individual sprites
const envAtlas = await loadImage('Aris/phase-8-4/phase_8_4_environment_atlas.png');
const envData = await loadJSON('Aris/phase-8-4/phase_8_4_environment_atlas.json');

function renderFromAtlas(spriteName, x, y) {
  const sprite = envData.sprites[spriteName];
  ctx.drawImage(
    envAtlas,
    sprite.x, sprite.y, sprite.width, sprite.height,  // Source
    x, y, sprite.width, sprite.height                  // Destination
  );
}

// Render various objects
renderFromAtlas('tree_oak', 100, 100);
renderFromAtlas('rock_small', 150, 80);
renderFromAtlas('ore_gold', 200, 120);
```

---

## Technical Details

### Object Footprints

Understanding footprints is crucial for collision and sorting:

**Trees (16×32):**
- Visual size: 16×32 pixels
- Footprint: 12×8 pixels at base
- Position represents bottom-center of trunk

**Rocks:**
- Small (16×16): Footprint ~14×12 pixels
- Large (16×24): Footprint ~14×16 pixels

**Ore Nodes (16×16):**
- Similar to small rocks
- Footprint ~14×12 pixels

**Fences (16×16):**
- Full tile footprint: 16×16 pixels
- Block movement completely

### Rendering Order (Z-Sorting)

Proper rendering order for depth illusion:

```javascript
// Sort objects by Y position (back to front)
objects.sort((a, b) => a.y - b.y);

// Render in sorted order
objects.forEach(obj => {
  renderObject(obj);
});

// Player should be sorted with objects by Y position
```

### Resource Yield System

**Example harvest system:**
```javascript
const resourceYields = {
  tree_oak: { item: 'wood', amount: [3, 5] },
  tree_pine: { item: 'wood', amount: [2, 4] },
  rock_small: { item: 'stone', amount: [2, 3] },
  rock_large: { item: 'stone', amount: [4, 6] },
  ore_iron: { item: 'iron_ore', amount: 1 },
  ore_copper: { item: 'copper_ore', amount: 1 },
  ore_gold: { item: 'gold_ore', amount: 1 }
};

function harvestResource(objectType) {
  const resource = resourceYields[objectType];
  if (!resource) return null;
  
  const amount = Array.isArray(resource.amount)
    ? randomRange(resource.amount[0], resource.amount[1])
    : resource.amount;
    
  return {
    item: resource.item,
    quantity: amount
  };
}
```

---

## Quality Checklist

Before approving assets, verify:

### Trees
- [ ] Oak and Pine trees are clearly distinguishable
- [ ] Canopy shape appropriate for tree type (round vs triangular)
- [ ] Trunk visible at bottom
- [ ] 12×8 footprint area is clear
- [ ] Tree stump shows visible rings/texture

### Rocks & Ores
- [ ] Small and large rocks have clear size difference
- [ ] Gray tones create 3D roundness effect
- [ ] Ore veins are visible and distinctive
- [ ] Iron (silver), Copper (orange), Gold (yellow) colors distinct
- [ ] Ores look harvestable

### Fences
- [ ] All four fence types are distinct
- [ ] Fence connections are logical
- [ ] Standalone shows single post clearly
- [ ] End piece shows termination
- [ ] Middle shows bilateral connections
- [ ] Corner shows 90-degree turn

### Atlas
- [ ] All 12 sprites packed efficiently
- [ ] 2048×2048 max size not exceeded
- [ ] Proper 2px padding between sprites
- [ ] JSON metadata complete and accurate

---

## Environment Design Tips

### Tree Placement
- Create clusters for forests
- Mix oak and pine for variety
- Leave stumps after player chops trees
- Use irregular spacing for natural look

### Rock Distribution
- Scatter small rocks as minor obstacles
- Place large rocks as terrain features
- Create rock clusters in mountainous areas
- Mix rocks with ore nodes (sparse)

### Ore Spawning
- Iron: Common (15-20% of rocks)
- Copper: Uncommon (10-15% of rocks)
- Gold: Rare (5% of rocks)

### Fence Usage
- Farm boundaries
- Animal pen enclosures
- Property demarcation
- Path definitions

---

## Troubleshooting

### Issue: Trees not sorting correctly with player

**Solution:** Ensure trees use Y position of base (y + 32) for depth sorting, not top of sprite.

### Issue: Player walks through solid objects

**Solution:** Implement footprint-based collision using the specified footprint dimensions (12×8 for trees, etc).

### Issue: Fence connections don't update

**Solution:** When placing/removing fences, recalculate fence types for all adjacent tiles.

### Issue: Ore nodes don't look valuable

**Solution:** Ensure metallic vein colors are vibrant and distinct. Iron=silver, Copper=orange, Gold=bright yellow.

---

## Next Steps

After completing Phase 8.4:

1. **Test Integration:** Place environment objects in game world
2. **Test Collisions:** Verify footprint-based collision works
3. **Test Fences:** Verify smart fence connection system
4. **Build Test Level:** Create sample environment with all assets
5. **Move to Phase 8.5-8.6:** Combat and enemy assets

---

## Related Files

- [`../asset-list.md`](../asset-list.md) - Complete Aris asset specifications
- [`assets_batch.yaml`](assets_batch.yaml) - Batch generation definition
- [`../../docs/BATCH_GENERATION_GUIDE.md`](../../docs/BATCH_GENERATION_GUIDE.md) - Batch generation reference
- [`../../docs/RENDERING_GUIDE.md`](../../docs/RENDERING_GUIDE.md) - Asset rendering guide

---

**Last Updated:** 2025-11-18  
**Phase Status:** Ready for Generation  
**Asset Count:** 12 sprites (3 trees + 5 rocks/ores + 4 fences)