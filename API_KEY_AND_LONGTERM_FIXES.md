# API Key Update & Long-term DetailAgent Fixes

**Date:** 2025-11-18  
**Status:** In Progress  

---

## ✅ API Key Update

**Issue:** Project was using wrong/old Anthropic API key  
**Solution:** Updated `.env` with correct key: `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`  
**Backup:** Old `.env` saved to `.env.bak`

The LLM client will now use direct Anthropic API (not OpenRouter) with Claude Sonnet 4.5.

---

## 🎯 Long-term Solutions Plan

### Problem Statement
DetailAgent continues producing invalid color formats despite explicit prompt instructions:
- Attempt 1: `#T`, `#B`, `#H` (symbolic codes)
- Attempt 2: `#rgba(0,0,0,0.12)` (CSS rgba format)
- Attempt 3: `#00000020`, `#00000040` (8-char hex with alpha)

**Root Cause:** DetailAgent's system prompt is ~970 lines and very complex. LLM struggles to follow all constraints consistently.

### Solutions to Implement

## 1. ✅ Simplify DetailAgent Prompt

**Strategy:** Break the massive prompt into focused, digestible sections with clear hierarchy.

**Changes:**
- Move examples to separate section
- Use bullet points instead of paragraphs
- Highlight critical requirements with visual markers
- Reduce token count by 30-40%

**Implementation:** Refactor [`src/agents/prompts.py`](src/agents/prompts.py) DETAIL_AGENT_SYSTEM

## 2. ✅ Add JSON Schema Validation

**Strategy:** Enforce output structure using strict JSON Schema with format validation.

**Implementation Location:** [`src/agents/detail_agent.py`](src/agents/detail_agent.py)

```python
DETAIL_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["pixel_grid", "shading_details", "final_specs"],
    "properties": {
        "pixel_grid": {
            "type": "object",
            "required": ["width", "height", "data", "format"],
            "properties": {
                "width": {"type": "integer", "minimum": 1},
                "height": {"type": "integer", "minimum": 1},
                "data": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {
                            "oneOf": [
                                {
                                    "type": "string",
                                    "pattern": "^#[0-9A-Fa-f]{6}$"  # Strict 6-char hex
                                },
                                {
                                    "type": "string",
                                    "const": "transparent"
                                }
                            ]
                        }
                    }
                },
                "format": {
                    "type": "string",
                    "const": "row-major array of hex colors"
                }
            }
        },
        "final_specs": {
            "type": "object",
            "required": ["colors_used"],
            "properties": {
                "colors_used": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "pattern": "^#[0-9A-Fa-f]{6}$"  # Only 6-char hex
                    }
                }
            }
        }
    }
}
```

**Changes Required:**
1. Update [`src/agents/detail_agent.py`](src/agents/detail_agent.py) to use strict schema
2. Add schema validation before accepting LLM output
3. Return clear error messages if schema validation fails

## 3. ✅ Implement Retry Logic with Error Feedback

**Strategy:** If DetailAgent produces invalid output, send the error back and ask it to fix.

**Implementation:** Add retry loop to [`src/agents/detail_agent.py`](src/agents/detail_agent.py)

```python
async def process(self, input_data: DetailInput) -> DetailOutput:
    """Process with retry logic for invalid outputs."""
    max_retries = 3
    last_error = None
    
    for attempt in range(max_retries):
        try:
            if attempt == 0:
                # First attempt - normal prompt
                response = await self._generate_detail(input_data)
            else:
                # Retry with error feedback
                response = await self._generate_detail_with_feedback(
                    input_data,
                    previous_error=last_error,
                    attempt=attempt
                )
            
            # Validate output
            validation_result = self._validate_colors(response)
            if validation_result.is_valid:
                return response
            
            # Invalid - prepare for retry
            last_error = validation_result.errors
            logger.warning(
                f"DetailAgent output invalid (attempt {attempt+1}/{max_retries}): "
                f"{validation_result.errors}"
            )
            
        except Exception as e:
            last_error = str(e)
            if attempt == max_retries - 1:
                raise
    
    raise ValueError(f"DetailAgent failed after {max_retries} attempts: {last_error}")
```

**Retry Prompt Template:**
```python
RETRY_PROMPT = """
Your previous output had the following issues:
{errors}

CRITICAL: You MUST fix these issues:
- Use ONLY #RRGGBB format (6 characters, e.g., #4d8c2d)
- Use "transparent" for empty pixels (NOT #T, NOT rgba(), NOT 8-char hex)
- NO symbolic colors, NO alpha channels, NO color names

Please regenerate the pixel_grid.data with ONLY valid hex colors.
"""
```

---

## 4. ⚡ Enhance Manifest Converter (Safety Layer)

**Strategy:** Since we can't 100% rely on prompt engineering, add intelligent color normalization.

**Implementation:** Enhance [`src/rendering/manifest_converter.py`](src/rendering/manifest_converter.py)

```python
def _normalize_color(self, color: str) -> str:
    """
    Normalize various LLM-generated color formats to standard #RRGGBB.
    
    This is a safety layer to handle cases where the LLM doesn't follow
    instructions perfectly.
    """
    if not color or color == "transparent":
        return "transparent"
    
    # Strip whitespace
    color = color.strip()
    
    # Handle 8-character hex (with alpha channel) - strip alpha
    if len(color) == 9 and color.startswith('#'):
        logger.warning(f"Found 8-char hex color {color}, stripping alpha channel")
        return color[:7]  # Keep only #RRGGBB
    
    # Handle rgba() format - convert to solid black (can't preserve alpha)
    if 'rgba' in color.lower():
        logger.warning(f"Found rgba() color {color}, converting to black")
        return '#000000'
    
    # Handle rgb() format - try to extract values
    if 'rgb' in color.lower():
        logger.warning(f"Found rgb() color {color}, attempting to parse")
        try:
            # Extract numbers from rgb(r,g,b)
            import re
            nums = re.findall(r'\d+', color)
            if len(nums) >= 3:
                r, g, b = int(nums[0]), int(nums[1]), int(nums[2])
                return f"#{r:02x}{g:02x}{b:02x}"
        except:
            pass
        return '#000000'
    
    # Handle symbolic codes - map to reasonable defaults
    SYMBOLIC_MAP = {
        '#T': 'transparent',
        '#B': '#000000',  # Black
        '#W': '#FFFFFF',  # White
        '#H': '#FFFFFF',  # Highlight -> white
        '#M': '#808080',  # Mid-tone -> gray
        '#D': '#404040',  # Dark -> dark gray
        '#S': '#202020',  # Shadow -> very dark gray
        '#O': '#000000',  # Outline -> black
    }
    
    upper_color = color.upper()
    if upper_color in SYMBOLIC_MAP:
        logger.warning(f"Found symbolic color {color}, mapping to {SYMBOLIC_MAP[upper_color]}")
        return SYMBOLIC_MAP[upper_color]
    
    # Validate proper hex format
    if color.startswith('#'):
        hex_part = color[1:]
        if len(hex_part) == 6 and all(c in '0123456789ABCDEFabcdef' for c in hex_part):
            return color  # Valid!
        elif len(hex_part) == 3:  # 3-char hex - expand
            return f"#{hex_part[0]*2}{hex_part[1]*2}{hex_part[2]*2}"
    
    # Unknown format - return black and log error
    logger.error(f"Unknown color format: {color}, defaulting to black")
    return '#000000'
```

---

## Implementation Status

### ✅ COMPLETED

1. **API Key Update** - DONE
   - Updated `.env` with correct Anthropic API key
   - Backup saved to `.env.bak`
   - Now using direct Anthropic API (not OpenRouter)

2. **Retry Logic with Error Feedback** - DONE
   - Location: [`src/agents/detail_agent.py:112-213`](src/agents/detail_agent.py:112-213)
   - Max 3 retry attempts
   - Temperature decreases on retries (0.6 → 0.5 → 0.4) for more precision
   - Validates color formats with regex pattern `^#[0-9A-Fa-f]{6}$`
   - Provides specific error feedback to LLM on retry
   - Tracks attempt number in metadata
   - **New Methods:**
     - [`_validate_color_formats()`](src/agents/detail_agent.py:391-427): Validates hex colors
     - [`_format_retry_prompt()`](src/agents/detail_agent.py:429-485): Creates retry prompt with error details

3. **Color Normalization in ManifestConverter** - DONE
   - Location: [`src/rendering/manifest_converter.py:183-250`](src/rendering/manifest_converter.py:183-250)
   - **New Method:** [`_normalize_color()`](src/rendering/manifest_converter.py:183-250)
   - Handles all known invalid formats:
     - 8-char hex with alpha (`#00000020` → `#000000`)
     - rgba() format (`#rgba(0,0,0,0.5)` → `#000000`)
     - rgb() format (parses and converts to hex)
     - Symbolic codes (`#T` → `transparent`, `#B` → `#000000`, etc.)
     - 3-char hex (`#FFF` → `#FFFFFF`)
   - Applied to both [`_convert_row_based_data()`](src/rendering/manifest_converter.py:252-268) and [`_convert_flat_hex_data()`](src/rendering/manifest_converter.py:270-287)
   - Logs warnings for all normalizations

### 🔄 OPTIONAL (Not Yet Implemented)

4. **Simplify DetailAgent Prompt** - Future enhancement
   - Current prompt is comprehensive but lengthy
   - Could be condensed for token efficiency
   - Not critical now that retry logic is in place

5. **JSON Schema Validation** - Future enhancement
   - Could add strict JSON Schema to LLM request
   - Would use Claude's structured output feature
   - Not critical now that validation and retry logic are in place

---

## Testing & Verification

### Recommended Test Procedure

1. **Test with a simple asset:**
   ```bash
   python3 -m src.cli.main generate "16x16 green grass tile" --style stardew_valley --verbose
   ```

2. **Monitor logs for:**
   - API key authentication (should NOT see "Detected OpenRouter")
   - DetailAgent retries (if color validation fails)
   - ManifestConverter normalization warnings

3. **Verify output:**
   - Asset renders correctly (not black square)
   - Colors are visible and match description
   - Logs show valid hex colors used

4. **If successful, regenerate Phase 8.2 (smallest phase):**
   ```bash
   python3 -m src.cli.main generate-batch Aris/phase-8-2/assets_batch.yaml --parallel 3 --verbose
   ```

5. **Then proceed with Phase 8.3 and 8.4 if 8.2 succeeds**

---

## Expected Improvements

**With these implementations:**

✅ **Multi-Layer Defense Strategy:**
1. Improved DetailAgent prompt (existing) - First line of defense
2. **NEW:** Retry logic with error feedback - Second line of defense
3. **NEW:** Color normalization in converter - Final safety net

✅ **Robustness:**
- DetailAgent attempts up to 3 times with specific error feedback
- Even if DetailAgent fails after 3 attempts, converter normalizes colors
- Converter maps known invalid formats to sensible defaults

✅ **Visibility:**
- Logs show attempt numbers and retry reasons
- Converter logs all normalizations as warnings
- Easy to track which fixes are being applied

✅ **Result:**
- DetailAgent should produce valid colors more consistently
- Invalid color formats are caught and fixed automatically
- Assets render correctly even with imperfect LLM output
- Significantly reduced black square incidents

---

## Files Modified

1. [`src/agents/detail_agent.py`](src/agents/detail_agent.py)
   - Modified `process()` method with retry loop
   - Added `_validate_color_formats()` method
   - Added `_format_retry_prompt()` method
   - ~100 lines added

2. [`src/rendering/manifest_converter.py`](src/rendering/manifest_converter.py)
   - Added `_normalize_color()` method
   - Updated `_convert_row_based_data()` to use normalization
   - Updated `_convert_flat_hex_data()` to use normalization
   - ~70 lines added

3. [`.env`](.env)
   - Updated ANTHROPIC_API_KEY
   - Backup saved to `.env.bak`

---

## Next Steps

1. **Test the improvements:**
   - Generate a simple test asset
   - Verify colors render correctly
   - Check logs for retry/normalization activity

2. **If successful, regenerate failed assets:**
   - Phase 8.2: 2 assets need regeneration
   - Phase 8.3: 9 assets need regeneration
   - Phase 8.4: 12 assets need regeneration

3. **Long-term monitoring:**
   - Track DetailAgent retry rates
   - Monitor which color normalizations are most common
   - Consider further prompt refinements based on patterns

---

## Summary

Implemented a comprehensive **multi-layer defense strategy** for color format handling:

1. **Layer 1 (Prevention):** Enhanced DetailAgent prompt with explicit requirements
2. **Layer 2 (Recovery):** Retry logic with specific error feedback (NEW)
3. **Layer 3 (Safety Net):** Intelligent color normalization (NEW)

This should **eliminate black square issues** and produce **valid, visible pixel art assets** consistently.