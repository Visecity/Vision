"""
RLE (Run-Length Encoding) decoder for Vision pixel art system.

This module provides utilities to decode RLE-compressed pixel data back
into standard 2D grid format for rendering.
"""

import logging
from typing import Any

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class RLESegment(BaseModel):
    """A run of consecutive pixels with the same color."""
    color: str
    count: int


def decode_rle_to_grid(
    width: int,
    height: int,
    rle_data: list[dict[str, Any]],
    auto_correct: bool = True,
    tolerance: float = 0.05,
) -> list[list[str]]:
    """
    Decode RLE pixel data to 2D grid format with optional auto-correction.
    
    Converts run-length encoded pixel data back into a standard 2D array
    format suitable for rendering. Can automatically correct minor pixel
    count mismatches caused by LLM counting errors.
    
    Args:
        width: Grid width in pixels
        height: Grid height in pixels
        rle_data: List of {"color": "#RRGGBB", "count": N} segments
        auto_correct: Enable automatic correction of small pixel count errors (default: True)
        tolerance: Maximum allowed deviation as fraction (default: 0.05 = 5%)
    
    Returns:
        2D list of hex color strings (row-major order)
    
    Raises:
        ValueError: If RLE data doesn't match expected pixel count or is invalid
    
    Example:
        >>> rle_data = [
        ...     {"color": "#FF0000", "count": 4},
        ...     {"color": "#00FF00", "count": 4}
        ... ]
        >>> grid = decode_rle_to_grid(4, 2, rle_data)
        >>> print(grid)
        [['#FF0000', '#FF0000', '#FF0000', '#FF0000'],
         ['#00FF00', '#00FF00', '#00FF00', '#00FF00']]
    """
    expected_pixels = width * height
    
    if expected_pixels == 0:
        raise ValueError(f"Invalid dimensions: {width}×{height}")
    
    # Decode RLE segments into flat list
    pixels: list[str] = []
    last_color = "transparent"  # Track last color for padding
    
    try:
        for i, segment_dict in enumerate(rle_data):
            # Validate segment structure
            if not isinstance(segment_dict, dict):
                raise ValueError(f"Segment {i} is not a dictionary: {type(segment_dict)}")
            
            if "color" not in segment_dict or "count" not in segment_dict:
                raise ValueError(
                    f"Segment {i} missing required fields. "
                    f"Got: {list(segment_dict.keys())}, expected: ['color', 'count']"
                )
            
            # Parse and validate segment
            try:
                segment = RLESegment(**segment_dict)
            except ValidationError as e:
                raise ValueError(f"Invalid segment {i}: {e}")
            
            # Validate count is positive
            if segment.count <= 0:
                raise ValueError(f"Segment {i} has invalid count: {segment.count}")
            
            # Add pixels
            pixels.extend([segment.color] * segment.count)
            last_color = segment.color
            
            # Check for overflow (but allow if auto_correct is enabled)
            if len(pixels) > expected_pixels and not auto_correct:
                raise ValueError(
                    f"RLE data exceeds expected pixel count after segment {i}: "
                    f"got {len(pixels)}, expected {expected_pixels}"
                )
    
    except Exception as e:
        logger.error(f"Failed to decode RLE segment: {e}")
        raise ValueError(f"RLE decoding failed: {e}")
    
    # Check pixel count and apply auto-correction if needed
    pixel_count = len(pixels)
    pixel_diff = pixel_count - expected_pixels
    
    if pixel_diff != 0:
        # Calculate deviation percentage
        deviation = abs(pixel_diff) / expected_pixels
        
        if auto_correct and deviation <= tolerance:
            # Auto-correct: pad or trim
            if pixel_diff < 0:
                # Too few pixels - pad with last color (usually transparent)
                padding_needed = -pixel_diff
                pixels.extend([last_color] * padding_needed)
                logger.warning(
                    f"Auto-corrected RLE: Padded {padding_needed} pixels with '{last_color}' "
                    f"({pixel_count} → {expected_pixels}, {deviation*100:.1f}% deviation)"
                )
            else:
                # Too many pixels - trim excess
                pixels = pixels[:expected_pixels]
                logger.warning(
                    f"Auto-corrected RLE: Trimmed {pixel_diff} excess pixels "
                    f"({pixel_count} → {expected_pixels}, {deviation*100:.1f}% deviation)"
                )
        else:
            # Error is too large or auto-correct disabled
            error_msg = (
                f"RLE data pixel count mismatch: got {pixel_count} pixels, "
                f"expected {expected_pixels} ({width}×{height}), "
                f"deviation: {deviation*100:.1f}%"
            )
            if not auto_correct:
                error_msg += " (auto-correct disabled)"
            elif deviation > tolerance:
                error_msg += f" (exceeds tolerance of {tolerance*100:.1f}%)"
            
            raise ValueError(error_msg)
    
    # Convert flat list to 2D grid (row-major order)
    grid: list[list[str]] = []
    for y in range(height):
        row_start = y * width
        row_end = row_start + width
        grid.append(pixels[row_start:row_end])
    
    logger.debug(
        f"Decoded RLE: {len(rle_data)} segments → {width}×{height} grid "
        f"({len(pixels)} pixels)"
    )
    
    return grid


def validate_rle_data(
    width: int,
    height: int,
    rle_data: list[dict[str, Any]],
) -> tuple[bool, list[str]]:
    """
    Validate RLE data without decoding it.
    
    Checks that RLE data structure is valid and pixel count matches dimensions.
    Useful for validation before attempting full decoding.
    
    Args:
        width: Expected grid width
        height: Expected grid height
        rle_data: RLE segment data to validate
    
    Returns:
        Tuple of (is_valid, list of error messages)
    
    Example:
        >>> rle_data = [{"color": "#FF0000", "count": 8}]
        >>> is_valid, errors = validate_rle_data(4, 2, rle_data)
        >>> print(is_valid)
        True
    """
    errors: list[str] = []
    
    # Check dimensions
    if width <= 0 or height <= 0:
        errors.append(f"Invalid dimensions: {width}×{height}")
        return False, errors
    
    expected_pixels = width * height
    
    # Check RLE data is a list
    if not isinstance(rle_data, list):
        errors.append(f"RLE data must be a list, got {type(rle_data)}")
        return False, errors
    
    if len(rle_data) == 0:
        errors.append("RLE data is empty")
        return False, errors
    
    # Validate each segment and count total pixels
    total_pixels = 0
    for i, segment in enumerate(rle_data):
        if not isinstance(segment, dict):
            errors.append(f"Segment {i} is not a dictionary")
            continue
        
        if "color" not in segment:
            errors.append(f"Segment {i} missing 'color' field")
        elif not isinstance(segment["color"], str):
            errors.append(f"Segment {i} color is not a string")
        
        if "count" not in segment:
            errors.append(f"Segment {i} missing 'count' field")
        elif not isinstance(segment["count"], int):
            errors.append(f"Segment {i} count is not an integer")
        elif segment["count"] <= 0:
            errors.append(f"Segment {i} count must be positive: {segment['count']}")
        else:
            total_pixels += segment["count"]
    
    # Check total pixel count
    if total_pixels != expected_pixels:
        errors.append(
            f"Pixel count mismatch: RLE has {total_pixels} pixels, "
            f"expected {expected_pixels} ({width}×{height})"
        )
    
    is_valid = len(errors) == 0
    return is_valid, errors


def calculate_compression_ratio(
    width: int,
    height: int,
    rle_segment_count: int,
) -> float:
    """
    Calculate the compression ratio achieved by RLE encoding.
    
    Args:
        width: Grid width
        height: Grid height
        rle_segment_count: Number of RLE segments
    
    Returns:
        Compression ratio (< 1.0 means compression, > 1.0 means expansion)
    
    Example:
        >>> # 32×32 grid compressed to 100 segments
        >>> ratio = calculate_compression_ratio(32, 32, 100)
        >>> print(f"Compression: {(1-ratio)*100:.1f}%")
        Compression: 90.2%
    """
    total_pixels = width * height
    if total_pixels == 0:
        return 1.0
    
    return rle_segment_count / total_pixels


def encode_grid_to_rle(grid: list[list[str]]) -> list[dict[str, Any]]:
    """
    Encode a 2D pixel grid to RLE format.
    
    Utility function to compress standard grid data into RLE format.
    Useful for testing or converting existing data.
    
    Args:
        grid: 2D array of hex color strings
    
    Returns:
        List of RLE segments {"color": str, "count": int}
    
    Example:
        >>> grid = [
        ...     ['#FF0000', '#FF0000', '#00FF00'],
        ...     ['#00FF00', '#00FF00', '#0000FF']
        ... ]
        >>> rle = encode_grid_to_rle(grid)
        >>> print(rle)
        [{'color': '#FF0000', 'count': 2}, 
         {'color': '#00FF00', 'count': 3},
         {'color': '#0000FF', 'count': 1}]
    """
    if not grid or not grid[0]:
        return []
    
    # Flatten grid to 1D (row-major)
    pixels: list[str] = []
    for row in grid:
        pixels.extend(row)
    
    # Run-length encode
    rle_data: list[dict[str, Any]] = []
    if not pixels:
        return rle_data
    
    current_color = pixels[0]
    current_count = 1
    
    for pixel in pixels[1:]:
        if pixel == current_color:
            current_count += 1
        else:
            rle_data.append({"color": current_color, "count": current_count})
            current_color = pixel
            current_count = 1
    
    # Add final segment
    rle_data.append({"color": current_color, "count": current_count})
    
    return rle_data