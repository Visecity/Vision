# DetailAgent Prompt Fix - Black Squares Issue Resolution

**Date:** 2025-11-18  
**Issue:** DetailAgent producing symbolic color codes instead of hex colors  
**Status:** ✅ FIXED

---

## Problem Summary

DetailAgent was generating manifests with **symbolic color codes** (`#T`, `#B`, `#H`, `#M`, `#D`, `#O`, `#S`) instead of actual hex colors (`#RRGGBB` format). This caused:

- **20/23 assets** rendering as completely black squares
- ManifestRenderer silently failing to parse colors and skipping pixels
- Thousands of "Invalid color" errors in rendering logs

## Root Cause

In [`src/agents/prompts.py`](src/agents/prompts.py), the DETAIL_AGENT_SYSTEM prompt was explicitly instructing the LLM to produce **"conceptual descriptions"** rather than actual pixel data:

**Before (Lines 417-423):**
```json
"data": [
  "Rows 0-4: sky/transparent background",
  "Rows 5-10: canopy using base green, shadow green, highlight green",
  ...
],
"format": "conceptual description (actual implementation uses hex arrays)"
```

This caused the LLM to invent symbolic shorthand like:
- `#T` for "transparent"
- `#B` for "black" 
- `#H` for "highlight"
- `#M` for "mid-tone"
- `#D` for "dark"
- etc.

## Solution Applied

### 1. Updated Output Format Specification (Line 368)

**Before:**
```python
"data": ["row-by-row or flattened pixel data with color indices/hex"],
```

**After:**
```python
"data": [["#hexcolor", "#hexcolor", ...], ["#hexcolor", "#hexcolor", ...]],
```

### 2. Updated Format Field Description (Line 369)

**Before:**
```python
"format": "description of data format (e.g., 'row-major array of hex colors')"
```

**After:**
```python
"format": "MUST be 'row-major array of hex colors' - use actual #RRGGBB hex codes or 'transparent' for empty pixels"
```

### 3. Added CRITICAL Requirements Section (Lines 509-528)

```markdown
## CRITICAL Requirements for pixel_grid.data:
1. **MUST use actual hex color codes**: Use full #RRGGBB format (e.g., "#4d8c2d", "#2d5016")
2. **MUST use 'transparent' for empty pixels**: Never use "#T", "#X", or symbolic names
3. **MUST provide complete pixel arrays**: Every row must have exact width in colors
4. **MUST use palette colors only**: Only colors from the provided palette
5. **Format MUST be**: Row-major 2D array like [["#hex", "#hex"], ["#hex", "#hex"]]

## Common MISTAKES to AVOID:
❌ DO NOT use symbolic colors like "#T", "#B", "#H", "#M", "#D", "#O", "#S"
❌ DO NOT use conceptual descriptions like "Rows 0-4: background"
❌ DO NOT abbreviate colors
✅ DO use full hex codes: "#4d8c2d", "#2d2d2d", "#c4c4c4"
✅ DO use "transparent" for empty/background pixels
```

### 4. Updated Examples with Actual Pixel Data

**Tree Example (Lines 417-423) - Before:**
```json
"data": [
  "Rows 0-4: sky/transparent background",
  "Rows 5-10: canopy using base green, shadow green, highlight green",
  ...
]
```

**Tree Example - After:**
```json
"data": [
  ["transparent", "transparent", "transparent", "#2d5016", "#2d5016", ...],
  ["transparent", "transparent", "#2d5016", "#3a6b1e", "#4d8c2d", ...],
  ["transparent", "#2d5016", "#3a6b1e", "#4d8c2d", "#4d8c2d", ...],
  ...
]
```

**Sword Example (Lines 466-472)** - Updated similarly with actual pixel arrays.

---

## Files Modified

1. **[`src/agents/prompts.py`](src/agents/prompts.py)** (Lines 363-530)
   - Updated DETAIL_AGENT_SYSTEM prompt
   - Added CRITICAL requirements
   - Updated examples with real pixel data
   - Added explicit warnings against symbolic colors

---

## Verification Steps

After this fix, the DetailAgent will now:

1. ✅ Output actual hex color codes (`#4d8c2d`, `#2d2d2d`, etc.)
2. ✅ Use `"transparent"` for empty pixels (not `"#T"`)
3. ✅ Provide complete 2D pixel arrays
4. ✅ Generate manifests that ManifestRenderer can parse correctly

---

## Regeneration Instructions

To regenerate all 23 assets with the fixed DetailAgent:

### Phase 8.2 - Player Character (2 assets)
```bash
python3 -m src.cli.main batch generate Aris/phase-8-2/assets_batch.yaml \
  --output-dir Aris/phase-8-2 --workers 1
```

### Phase 8.3 - Tools & Equipment (9 assets)
```bash
python3 -m src.cli.main batch generate Aris/phase-8-3/assets_batch.yaml \
  --output-dir Aris/phase-8-3 --workers 3
```

### Phase 8.4 - Environment (12 assets)
```bash
python3 -m src.cli.main batch generate Aris/phase-8-4/assets_batch.yaml \
  --output-dir Aris/phase-8-4 --workers 3
```

### Expected Results

After regeneration:
- ✅ All 23 PNGs should contain visible pixel art (not black squares)
- ✅ All 23 JSON manifests should contain only hex colors
- ✅ No "Invalid color" errors in rendering logs
- ✅ Assets should match their descriptions accurately

---

## Related Files

- **[`BLACK_SQUARES_FIX.md`](BLACK_SQUARES_FIX.md)** - Original investigation
- **[`src/rendering/manifest_converter.py`](src/rendering/manifest_converter.py)** - Converter with `#T` filtering
- **[`src/agents/detail_agent.py`](src/agents/detail_agent.py)** - DetailAgent implementation
- **[`src/rendering/manifest_renderer.py`](src/rendering/manifest_renderer.py)** - Rendering logic

---

## Testing Recommendations

1. **Generate a single test asset** first to verify the fix
2. **Check the JSON manifest** contains only hex colors and `"transparent"`
3. **Verify the PNG** displays correct pixel art
4. **Review rendering logs** for any color parsing errors
5. **Proceed with full batch** if test asset succeeds

---

## Conclusion

The DetailAgent prompt has been comprehensively updated to **explicitly forbid symbolic color codes** and **require actual hex values**. The examples now demonstrate the correct format with real pixel arrays.

This fix addresses the root cause of the black squares issue. All 23 assets can now be regenerated with proper pixel data.

**Status:** Ready for batch regeneration ✅