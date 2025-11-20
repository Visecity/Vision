# Aris - Asset List

Comprehensive list of all sprite assets needed for the game, organized by priority and phase.

## Asset Specifications Format

Each asset includes:
- **Name**: Descriptive asset name
- **File**: Target filename
- **Dimensions**: Width × Height in pixels
- **Format**: Image format (PNG with transparency)
- **Atlas Layout**: For animated sprites (columns × rows)
- **Frame Size**: Individual frame dimensions for atlases
- **Color Palette**: Suggested colors
- **Description**: What the asset represents
- **Priority**: Critical/High/Medium/Low
- **Phase**: When it's needed (Current/8.x/Future)

---

## Current Priority Assets

### Player Character (CRITICAL - Phase 8.2)

**Asset: Player Sprite 16×32**
- **File**: `player_animated_32.png`
- **Dimensions**: 32 × 128 pixels
- **Atlas Layout**: 2 columns × 4 rows
- **Frame Size**: 16 × 32 pixels per frame
- **Animation**: 2-frame walk cycle per direction
- **Directions**: 4 (Down/Up/Left/Right in rows 0/1/2/3)
- **Color Palette**: 
  - Skin: Beige/Tan (#F5DEB3)
  - Hair: Brown (#654321)
  - Shirt: Blue (#4169E1)
  - Pants: Brown (#8B4513)
  - Shoes: Dark Brown (#3D2817)
- **Description**: Protagonist character, 16px wide × 32px tall, orthographic view. Position represents feet. Sprite extends upward from ground position.
- **Details**:
  - **Row 0 (Down/Front)**: Player facing camera, feet at bottom
  - **Row 1 (Up/Back)**: Player facing away, back of head visible
  - **Row 2 (Left)**: Player facing left, profile view
  - **Row 3 (Right)**: Player facing right, profile view (can mirror Row 2)
  - Frame 0: Standing/step 1, Frame 1: Walking/step 2
  - Consistent colors across all directions (especially hair/shirt in Up direction)
  - Feet should be clearly at bottom of 16×32 frame
- **Priority**: CRITICAL
- **Phase**: Current (8.2) - Fixes needed

**Asset: Player Shadow**
- **File**: `shadow.png` (update existing)
- **Dimensions**: 16 × 8 pixels
- **Format**: PNG with alpha
- **Color**: Semi-transparent black (50% opacity, #000000)
- **Description**: Oval shadow beneath player feet, centered at player position
- **Priority**: High
- **Phase**: Current

---

## Phase 8.3: Tools & Weapons

### Tool Icons (16×16 each)

**Asset: Tool Icon Sheet**
- **File**: `tools.png`
- **Dimensions**: 128 × 16 pixels (8 icons × 16px each)
- **Layout**: Horizontal strip, 8 tools
- **Icons**:
  1. **Hoe** (existing) - Brown L-shaped tool
  2. **Watering Can** - Blue/gray watering can
  3. **Axe** - Gray blade, brown handle
  4. **Pickaxe** - Gray pointed tool, brown handle
  5. **Sword** - Silver blade, brown/gold hilt
  6. **Bow** - Brown curved wood with string
  7. **Fishing Rod** - Brown pole with line
  8. **Scythe** - Silver curved blade, brown handle
- **Priority**: High
- **Phase**: 8.3

**Asset: Weapon Swing Effects**
- **File**: `weapon_effects.png`
- **Dimensions**: 64 × 32 pixels (4 frames × 16×32 each)
- **Description**: Slash/swing arc effects for melee weapons
- **Frames**: 4-frame swing animation
- **Colors**: White/light blue semi-transparent arc
- **Priority**: Medium
- **Phase**: 8.3

---

## Phase 8.4: Static World Objects

### Trees (16×32 each)

**Asset: Oak Tree**
- **File**: `tree_oak.png`
- **Dimensions**: 16 × 32 pixels
- **Description**: Basic deciduous tree, green canopy, brown trunk
- **Footprint**: 12×8 pixels (trunk at bottom)
- **Colors**:
  - Canopy: Green (#228B22)
  - Trunk: Brown (#8B4513)
- **Priority**: High
- **Phase**: 8.4

**Asset: Pine Tree**
- **File**: `tree_pine.png`
- **Dimensions**: 16 × 32 pixels
- **Description**: Evergreen tree, triangular shape
- **Footprint**: 12×8 pixels
- **Colors**:
  - Needles: Dark green (#006400)
  - Trunk: Dark brown (#654321)
- **Priority**: Medium
- **Phase**: 8.4

**Asset: Tree Stump**
- **File**: `tree_stump.png`
- **Dimensions**: 16 × 16 pixels
- **Description**: Chopped tree remnant
- **Colors**: Brown with rings
- **Priority**: High
- **Phase**: 8.4

### Rocks & Ores

**Asset: Rock Small**
- **File**: `rock_small.png`
- **Dimensions**: 16 × 16 pixels
- **Description**: Small gray rock
- **Priority**: High
- **Phase**: 8.4

**Asset: Rock Large**
- **File**: `rock_large.png`
- **Dimensions**: 16 × 24 pixels
- **Description**: Larger boulder
- **Priority**: Medium
- **Phase**: 8.4

**Asset: Ore Nodes**
- **File**: `ores.png`
- **Dimensions**: 48 × 16 pixels (3 types × 16×16 each)
- **Types**: Iron (gray), Copper (orange), Gold (yellow)
- **Priority**: Medium
- **Phase**: 8.4

### Fences

**Asset: Wooden Fence**
- **File**: `fence_wood.png`
- **Dimensions**: 64 × 16 pixels (4 connection states)
- **States**: Standalone, End, Middle, Corner
- **Description**: Connect-able fence pieces
- **Priority**: Medium
- **Phase**: 8.4

---

## Phase 8.5-8.6: Combat & Enemies

### Enemy Sprites (Animated)

**Asset: Slime Enemy**
- **File**: `enemy_slime.png`
- **Dimensions**: 32 × 32 pixels (2 frames × 16×16 each)
- **Animation**: 2-frame bounce
- **Colors**: Green (#00FF00) with darker outline
- **Description**: Basic melee enemy, bounces toward player
- **Priority**: High
- **Phase**: 8.6

**Asset: Goblin Enemy**
- **File**: `enemy_goblin.png`
- **Dimensions**: 32 × 64 pixels (2 columns × 4 rows)
- **Frame Size**: 16 × 32 per frame
- **Directions**: 4 (like player)
- **Colors**: Green skin, brown clothes
- **Description**: Humanoid ranged enemy
- **Priority**: High
- **Phase**: 8.6

**Asset: Bat Enemy**
- **File**: `enemy_bat.png`
- **Dimensions**: 32 × 16 pixels (2 frames)
- **Frame Size**: 16 × 16 per frame
- **Description**: Flying enemy, 2-frame wing flap
- **Priority**: Medium
- **Phase**: 8.6

### Combat Effects

**Asset: Hit Effect**
- **File**: `hit_effect.png`
- **Dimensions**: 16 × 16 pixels
- **Description**: Star/spark effect on hit
- **Frames**: 4 frame animation
- **Priority**: Medium
- **Phase**: 8.5

**Asset: Projectile Arrow**
- **File**: `projectile_arrow.png`
- **Dimensions**: 16 × 4 pixels
- **Description**: Arrow projectile (4 directions via rotation)
- **Priority**: High
- **Phase**: 8.5

**Asset: Projectile Fireball**
- **File**: `projectile_fireball.png`
- **Dimensions**: 32 × 8 pixels (4 frames)
- **Description**: Enemy magic projectile
- **Priority**: Medium
- **Phase**: 8.6

---

## Phase 8.8: Animal NPCs

**Asset: Chicken**
- **File**: `animal_chicken.png`
- **Dimensions**: 32 × 32 pixels (2 frames × 16×16 each)
- **Animation**: 2-frame peck/walk
- **Colors**: White/brown body, red comb
- **Priority**: Medium
- **Phase**: 8.8

**Asset: Cow**
- **File**: `animal_cow.png`
- **Dimensions**: 48 × 32 pixels (2 frames)
- **Frame Size**: 24 × 32 per frame
- **Description**: Larger farm animal
- **Colors**: Brown/white patches
- **Priority**: Medium
- **Phase**: 8.8

---

## Phase 8.9: Buildings

**Asset: Barn**
- **File**: `building_barn.png`
- **Dimensions**: 32 × 32 pixels (multi-tile 2×2)
- **Description**: Animal housing building
- **Colors**: Red walls, gray roof
- **Priority**: Medium
- **Phase**: 8.9

**Asset: Coop**
- **File**: `building_coop.png`
- **Dimensions**: 24 × 24 pixels
- **Description**: Chicken coop
- **Colors**: Brown wood, gray roof
- **Priority**: Medium
- **Phase**: 8.9

---

## Existing Assets (Keep/Update)

### Current Sprites
- `crops.png` (16×64 - 4 growth stages × 16×16) - **Keep as is**
- `items.png` (existing items) - **Keep, may expand**
- `tiles.png` (terrain tiles) - **Keep as is**
- `ui_icons.png` (UI elements) - **Keep, may expand**
- `ui_panel.png` (UI backgrounds) - **Keep as is**
- `particle.png` (4×4 particle) - **Keep as is**

### Needs Update
- `shadow.png` - Update for 16×32 player (current is 16×16)

---

## Future/Optional Assets

### Additional Tools
- Hammer, Sickle, Shovel, Seeds packets

### More Enemies
- Skeleton, Spider, Wolf, Boss enemies

### More Buildings
- House, Shop, Workshop, Storage shed

### Environmental
- Bushes, Flowers, Grass variations, Stones, Water effects

### UI Elements
- Health bar, Energy bar, Combat indicators

---

## Technical Notes

### Sprite Conventions
- **Transparency**: Use PNG with alpha channel
- **Pixel Perfect**: No anti-aliasing, clean pixel edges
- **Color Depth**: 32-bit RGBA
- **Pivot Point**: Bottom-center for most sprites (feet position)
- **Consistency**: Maintain palette across related sprites
- **Orthographic**: Top-down perspective with slight front angle

### Atlas Format
- **Player/Enemy animations**: Columns = frames, Rows = directions
- **Tools/Items**: Horizontal strips or grids
- **Effects**: Horizontal animation strips (left to right)

### Naming Convention
- Category_Name_Variant.png (e.g., enemy_slime_green.png)
- Lowercase with underscores
- Descriptive and specific

---

## Summary

**Immediate Priority (Phase 8.2-8.3):**
1. Player 16×32 sprite (CRITICAL - fix current issues)
2. Shadow update
3. Tool icons (8 tools)
4. Weapon swing effects

**High Priority (Phase 8.4-8.6):**
5. Trees (Oak, Pine, Stump)
6. Rocks and ores
7. Enemy sprites (Slime, Goblin)
8. Combat effects (hit, arrow)

**Medium Priority (Phase 8.7-8.9):**
9. Fences
10. Animal NPCs (Chicken, Cow)
11. Buildings (Barn, Coop)
12. Additional enemies (Bat)

**Total New Assets Needed**: ~30-40 sprites
**Existing Assets to Keep**: ~7 sprites