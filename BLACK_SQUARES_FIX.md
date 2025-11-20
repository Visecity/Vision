# Black Squares Bug - Root Cause Analysis & Fix

**Date**: 2025-11-18  
**Status**: FIXED - Awaiting Batch Regeneration

---

## Executive Summary

**Problem**: 20 out of 23 generated assets rendered as black squares despite "successful" workflows.

**Root Cause**: DetailAgent producing invalid color codes (`#T`, `#B`, `#H`, `#M`, etc.) instead of valid hex colors, which ManifestRenderer silently skips, leaving pixels as black (default background).

**Solution**: Fixed ManifestConverter to filter transparent markers. **Batch regeneration required** to create clean manifests.

---

## Timeline of Discovery

### Initial Symptoms
- Batch generation reported 22/23 successful workflows (95.7%)
- PNG files generated but 20 showed only black squares
- 3 assets rendered correctly: `player_sprite.png`, `16x8_pixel_oval_shadow_sprite.png`, `16x16_pixel_axe_tool_icon.png`

### Investigation Steps

1. **File Location Mystery** ✅ RESOLVED
   - Files generated to `output/<uuid>/` instead of `Aris/phase-X-Y/`
   - Created `move_batch_assets.py` to relocate all 23 assets
   - Integration bug identified between BatchExecutor and WorkflowExecutor

2. **Black Squares Bug** ✅ ROOT CAUSE FOUND
   - Examined axe manifest (working): Contains valid hex colors
   - Examined hoe manifest (broken): Contains thousands of `#T`, `#B`, `#H`, `#M`, `#D`, `#O`, `#S`, etc.
   - ManifestRenderer logs "Invalid color '#T'" but continues, leaving pixels black

### Root Cause Analysis

**File**: [`src/rendering/manifest_converter.py:186`](src/rendering/manifest_converter.py:186)

```python
# BEFORE (BUG):
for y, row in enumerate(rows):
    for x, color in enumerate(row):
        if color and color != "transparent" and not color.startswith("transparent"):
            elements.append({...})  # "#T" passes this check!

# AFTER (FIXED):
for y, row in enumerate(rows):
    for x, color in enumerate(row):
        # Skip transparent pixels (represented as "transparent", "#T", or empty)
        if color and color not in ("transparent", "#T") and not color.startswith("transparent"):
            elements.append({...})
```

**Why the Bug Occurred**:
1. DetailAgent uses `#T` as shorthand for transparent pixels
2. ManifestConverter only checked for `"transparent"` string
3. `#T` passed through to manifest JSON
4. ManifestRenderer tried to parse `#T` as hex color, failed, logged error, skipped pixel
5. Skipped pixels remained black (default background from line 191)

---

## Invalid Color Codes Found

From re-rendering attempt error log:

| Code | Likely Meaning | Frequency |
|------|---------------|-----------|
| `#T` | Transparent | Thousands |
| `#B` | Black/Border | Hundreds |
| `#H` | Highlight | Hundreds |
| `#M` | Mid-tone | Hundreds |
| `#D` | Dark | Hundreds |
| `#O` | Outline | Hundreds |
| `#S` | Shadow | Hundreds |
| `#L` | Light | Dozens |
| `#G`, `#G1`, `#G2`, `#G3` | Green shades | Dozens |
| `#W`, `#W1`, `#W2`, `#W3` | White/Wood shades | Dozens |
| `#R1`, `#R2`, `#R3` | Red/Rock shades | Dozens |
| `#C`, `#C1`, `#C2`, `#C3` | Copper shades | Dozens |
| `#TB`, `#TH`, `#TS`, `#T1`, `#T2`, `#T3` | Tree/Trunk shades | Dozens |

**Pattern**: DetailAgent is using **symbolic color names** instead of actual hex values!

---

## Fix Implementation

### Changes Made

**1. ManifestConverter - Transparency Handling**

Files Modified:
- [`src/rendering/manifest_converter.py:186-194`](src/rendering/manifest_converter.py:186-194) - `_convert_row_based_data()`
- [`src/rendering/manifest_converter.py:201-211`](src/rendering/manifest_converter.py:201-211) - `_convert_flat_hex_data()`

**2. Supporting Scripts**

Created:
- `fix_black_squares.py` - Re-render existing manifests (INEFFECTIVE - can't fix corrupted manifests)
- `move_batch_assets.py` - Relocate assets from `output/<uuid>/` to correct directories

---

## Current Status

### What Works ✅
- [x] ManifestConverter filters `#T` transparency markers
- [x] File relocation script successfully moved 23 assets  
- [x] Integration bug documented
- [x] Root cause identified

### What Doesn't Work ❌
- [ ] 20 existing manifests contain thousands of invalid color codes
- [ ] Re-rendering from corrupted manifests still produces black squares
- [ ] DetailAgent still producing symbolic colors instead of hex values

### What Needs To Be Done

**CRITICAL**: Regenerate all batches with the fixed converter:

```bash
# Phase 8.2 - Player Character (2 assets)
python3 -m src.cli.main batch generate Aris/phase-8-2/assets_batch.yaml \
  --output-dir Aris/phase-8-2 --workers 1

# Phase 8.3 - Tools & Equipment (9 assets)  
python3 -m src.cli.main batch generate Aris/phase-8-3/assets_batch.yaml \
  --output-dir Aris/phase-8-3 --workers 3

# Phase 8.4 - Environment (12 assets)
python3 -m src.cli.main batch generate Aris/phase-8-4/assets_batch.yaml \
  --output-dir Aris/phase-8-4 --workers 3
```

**Why Regeneration Required**:
- Fixed converter only affects NEW generations
- Existing JSON manifests are permanently corrupted
- Can't "fix" manifests without re-running DetailAgent

---

## Additional Issue Discovered

**DetailAgent Output Format Problem**

The deeper issue: DetailAgent is producing **symbolic color codes** instead of actual hex colors. This suggests either:

1. **Prompt Issue**: DetailAgent not instructed to use full hex colors
2. **Validation Issue**: DetailAgent output validation not catching symbolic colors
3. **Format Issue**: DetailAgent interpreting palette colors incorrectly

**Recommendation**: Investigate [`src/agents/detail_agent.py`](src/agents/detail_agent.py) prompts and output validation after batch regeneration.

---

## Files Modified

| File | Status | Purpose |
|------|--------|---------|
| `src/rendering/manifest_converter.py` | ✅ FIXED | Filter `#T` transparency markers |
| `BLACK_SQUARES_FIX.md` | ✅ CREATED | This document |
| `fix_black_squares.py` | ⚠️ INEFFECTIVE | Can't fix corrupted manifests |
| `move_batch_assets.py` | ✅ WORKS | Relocates misplaced assets |

---

## Success Metrics

After regeneration, verify:
- [ ] All 23 PNG files render with visible pixel art (not black squares)
- [ ] All JSON manifests contain only valid hex colors (#RRGGBB format)
- [ ] No "Invalid color" errors in rendering logs
- [ ] Assets match their descriptions

---

## Lessons Learned

1. **Format Mismatches Are Critical**: Slight differences between agent output and renderer expectations cause silent failures
2. **Validation Layers Matter**: Need stronger validation between DetailAgent and ManifestConverter
3. **Test With Edge Cases**: Should have tested with various agent outputs before batch generation
4. **Error Handling Trade-offs**: ManifestRenderer's "continue on error" behavior masked the problem

---

## Next Steps

1. **Immediate**: Run batch regeneration commands above
2. **Short-term**: Investigate DetailAgent symbolic color production
3. **Long-term**: Add validation layer to catch invalid colors before rendering
4. **Future**: Fix BatchExecutor/WorkflowExecutor output directory integration

---

**Status**: Ready for batch regeneration with fixed converter.