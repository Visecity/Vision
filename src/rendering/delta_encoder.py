"""
Delta Encoding for Animation Frames in Vision pixel art system.

This module provides utilities to compress animation sequences by storing only
the differences (deltas) between frames instead of full frame data. This is
highly effective for animations where frames share many common pixels.

Typical compression: 70-80% for animation sequences.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def encode_animation_with_deltas(
    frames: list[list[list[str]]],
    keyframe_interval: int = 1,
    auto_optimize: bool = True
) -> dict[str, Any]:
    """
    Encode animation frames using delta compression.
    
    Stores only pixel differences between consecutive frames, dramatically
    reducing data size for animations. The first frame (keyframe) is stored
    completely, and subsequent frames store only changed pixels.
    
    Args:
        frames: List of frame grids (each grid is 2D list of hex colors)
        keyframe_interval: Insert full keyframe every N frames (default: 1 = only first frame)
        auto_optimize: Automatically insert keyframes when delta gets too large (default: True)
    
    Returns:
        dict with:
            - keyframe: Full first frame data
            - deltas: List of frame changes
            - width, height: Frame dimensions
            - frame_count: Total frames
            - encoding: "delta"
            - _metadata: Compression statistics
    
    Raises:
        ValueError: If frames are empty or have inconsistent dimensions
        
    Example:
        >>> frames = [
        ...     [['#FF0000', '#FF0000'], ['#00FF00', '#00FF00']],  # Frame 0
        ...     [['#FF0000', '#0000FF'], ['#00FF00', '#00FF00']],  # Frame 1 (1 pixel changed)
        ... ]
        >>> encoded = encode_animation_with_deltas(frames)
        >>> print(len(encoded['deltas'][0]['changes']))
        1  # Only 1 pixel changed
    """
    if not frames:
        raise ValueError("Cannot encode empty animation")
    
    if len(frames) < 2:
        raise ValueError("Animation must have at least 2 frames for delta encoding")
    
    # Validate dimensions
    height = len(frames[0])
    width = len(frames[0][0]) if height > 0 else 0
    
    for i, frame in enumerate(frames):
        if len(frame) != height:
            raise ValueError(f"Frame {i} height mismatch: expected {height}, got {len(frame)}")
        for row in frame:
            if len(row) != width:
                raise ValueError(f"Frame {i} width mismatch: expected {width}, got {len(row)}")
    
    total_pixels = width * height
    logger.info(f"Encoding {len(frames)} frames of {width}×{height} ({total_pixels} pixels each)")
    
    # Store keyframe (first frame)
    keyframe = frames[0]
    
    # Encode deltas for subsequent frames
    deltas = []
    total_changes = 0
    keyframe_indices = [0]  # Track which frames are keyframes
    
    for frame_idx in range(1, len(frames)):
        current_frame = frames[frame_idx]
        
        # Determine reference frame (previous frame or last keyframe)
        reference_frame = frames[frame_idx - 1]
        
        # Calculate changes
        changes = []
        for y in range(height):
            for x in range(width):
                current_color = current_frame[y][x]
                reference_color = reference_frame[y][x]
                
                if current_color != reference_color:
                    changes.append({
                        "x": x,
                        "y": y,
                        "color": current_color
                    })
        
        # Auto-optimize: insert keyframe if delta is too large (>50% pixels changed)
        if auto_optimize and len(changes) > total_pixels * 0.5:
            logger.info(
                f"Frame {frame_idx}: {len(changes)} changes ({len(changes)/total_pixels*100:.1f}%) "
                f"- inserting keyframe"
            )
            # Store as keyframe instead
            deltas.append({
                "frame_index": frame_idx,
                "is_keyframe": True,
                "frame_data": current_frame,
                "changes": []
            })
            keyframe_indices.append(frame_idx)
        else:
            # Store as delta
            deltas.append({
                "frame_index": frame_idx,
                "is_keyframe": False,
                "changes": changes
            })
            total_changes += len(changes)
        
        # Forced keyframe interval
        if keyframe_interval > 1 and frame_idx % keyframe_interval == 0 and frame_idx not in keyframe_indices:
            logger.info(f"Frame {frame_idx}: Forced keyframe (interval={keyframe_interval})")
            deltas[-1]["is_keyframe"] = True
            deltas[-1]["frame_data"] = current_frame
            keyframe_indices.append(frame_idx)
    
    # Calculate compression metrics
    uncompressed_pixels = total_pixels * len(frames)
    compressed_pixels = total_pixels + total_changes  # Keyframe + all changes
    compression_ratio = compressed_pixels / uncompressed_pixels
    
    logger.info(
        f"Delta encoding: {uncompressed_pixels} pixels → {compressed_pixels} "
        f"(keyframe + {total_changes} changes, {(1-compression_ratio)*100:.1f}% compression)"
    )
    
    return {
        "width": width,
        "height": height,
        "frame_count": len(frames),
        "encoding": "delta",
        "keyframe": keyframe,
        "deltas": deltas,
        "_metadata": {
            "total_pixels": uncompressed_pixels,
            "compressed_pixels": compressed_pixels,
            "total_changes": total_changes,
            "compression_ratio": compression_ratio,
            "compression_percent": round((1 - compression_ratio) * 100, 1),
            "keyframe_indices": keyframe_indices,
            "avg_changes_per_frame": round(total_changes / (len(frames) - 1), 1) if len(frames) > 1 else 0
        }
    }


def decode_delta_animation(
    width: int,
    height: int,
    keyframe: list[list[str]],
    deltas: list[dict[str, Any]],
    validate: bool = True
) -> list[list[list[str]]]:
    """
    Decode delta-encoded animation back to full frame sequence.
    
    Reconstructs complete animation frames by applying deltas to keyframe(s).
    
    Args:
        width: Frame width in pixels
        height: Frame height in pixels
        keyframe: Full first frame data
        deltas: List of frame deltas with changes
        validate: Validate frame dimensions (default: True)
    
    Returns:
        List of complete frame grids (2D lists of hex colors)
    
    Raises:
        ValueError: If delta data is invalid or reconstruction fails
        
    Example:
        >>> keyframe = [['#FF0000', '#FF0000'], ['#00FF00', '#00FF00']]
        >>> deltas = [{
        ...     "frame_index": 1,
        ...     "is_keyframe": False,
        ...     "changes": [{"x": 1, "y": 0, "color": "#0000FF"}]
        ... }]
        >>> frames = decode_delta_animation(2, 2, keyframe, deltas)
        >>> print(frames[1][0][1])
        #0000FF
    """
    if validate:
        # Validate keyframe dimensions
        if len(keyframe) != height:
            raise ValueError(f"Keyframe height mismatch: expected {height}, got {len(keyframe)}")
        for row in keyframe:
            if len(row) != width:
                raise ValueError(f"Keyframe width mismatch: expected {width}, got {len(row)}")
    
    # Start with keyframe as frame 0
    frames = [keyframe]
    
    # Apply deltas to reconstruct subsequent frames
    for delta in deltas:
        frame_idx = delta.get("frame_index")
        is_keyframe = delta.get("is_keyframe", False)
        
        if is_keyframe:
            # This delta contains a full frame
            frame_data = delta.get("frame_data")
            if not frame_data:
                raise ValueError(f"Keyframe delta {frame_idx} missing frame_data")
            frames.append(frame_data)
            logger.debug(f"Frame {frame_idx}: Keyframe inserted")
        else:
            # Apply changes to previous frame
            if not frames:
                raise ValueError(f"Cannot apply delta {frame_idx}: no previous frame")
            
            # Deep copy previous frame
            previous_frame = frames[-1]
            new_frame = [row[:] for row in previous_frame]
            
            # Apply changes
            changes = delta.get("changes", [])
            for change in changes:
                x = change.get("x")
                y = change.get("y")
                color = change.get("color")
                
                if x is None or y is None or color is None:
                    raise ValueError(f"Invalid change in delta {frame_idx}: {change}")
                
                if y < 0 or y >= height or x < 0 or x >= width:
                    raise ValueError(
                        f"Change coordinates out of bounds in delta {frame_idx}: "
                        f"({x}, {y}) for {width}×{height} frame"
                    )
                
                new_frame[y][x] = color
            
            frames.append(new_frame)
            logger.debug(f"Frame {frame_idx}: Applied {len(changes)} changes")
    
    logger.info(f"Decoded {len(frames)} frames from delta encoding")
    return frames


def calculate_delta_compression_ratio(
    frame_count: int,
    width: int,
    height: int,
    total_changes: int,
    keyframe_count: int = 1
) -> dict[str, float]:
    """
    Calculate compression metrics for delta-encoded animation.
    
    Compares delta encoding against storing all frames completely.
    
    Args:
        frame_count: Total number of frames
        width: Frame width
        height: Frame height
        total_changes: Total number of pixel changes across all deltas
        keyframe_count: Number of keyframes stored (default: 1)
    
    Returns:
        dict with compression ratios and percentages
        
    Example:
        >>> metrics = calculate_delta_compression_ratio(
        ...     frame_count=10,
        ...     width=16,
        ...     height=16,
        ...     total_changes=320,  # ~32 changes per frame
        ...     keyframe_count=1
        ... )
        >>> print(f"Compression: {metrics['compression_percent']:.1f}%")
        Compression: 87.5%
    """
    total_pixels = width * height
    
    # Uncompressed: all frames stored completely
    uncompressed_pixels = total_pixels * frame_count
    
    # Compressed: keyframes + deltas
    compressed_pixels = (total_pixels * keyframe_count) + total_changes
    
    # Estimate token counts
    # Uncompressed: ~9 tokens per pixel
    uncompressed_tokens = uncompressed_pixels * 9
    
    # Compressed: keyframes (~9 tokens/pixel) + changes (~5 tokens/change)
    compressed_tokens = (total_pixels * keyframe_count * 9) + (total_changes * 5)
    
    compression_ratio = compressed_pixels / uncompressed_pixels if uncompressed_pixels > 0 else 1.0
    token_ratio = compressed_tokens / uncompressed_tokens if uncompressed_tokens > 0 else 1.0
    
    return {
        "compression_ratio": compression_ratio,
        "compression_percent": round((1 - compression_ratio) * 100, 1),
        "token_ratio": token_ratio,
        "token_compression_percent": round((1 - token_ratio) * 100, 1),
        "uncompressed_pixels": uncompressed_pixels,
        "compressed_pixels": compressed_pixels,
        "estimated_uncompressed_tokens": uncompressed_tokens,
        "estimated_compressed_tokens": compressed_tokens,
        "avg_changes_per_frame": round(total_changes / (frame_count - keyframe_count), 1) if frame_count > keyframe_count else 0
    }


def validate_delta_data(
    width: int,
    height: int,
    keyframe: list[list[str]],
    deltas: list[dict[str, Any]]
) -> tuple[bool, list[str]]:
    """
    Validate delta-encoded animation data without full decoding.
    
    Checks structure and coordinates before attempting reconstruction.
    
    Args:
        width: Expected frame width
        height: Expected frame height
        keyframe: Keyframe data to validate
        deltas: Delta data to validate
    
    Returns:
        Tuple of (is_valid, list of error messages)
        
    Example:
        >>> keyframe = [['#FF0000', '#FF0000']]
        >>> deltas = [{"frame_index": 1, "changes": [{"x": 0, "y": 0, "color": "#00FF00"}]}]
        >>> is_valid, errors = validate_delta_data(2, 1, keyframe, deltas)
        >>> print(is_valid)
        True
    """
    errors: list[str] = []
    
    # Validate dimensions
    if width <= 0 or height <= 0:
        errors.append(f"Invalid dimensions: {width}×{height}")
        return False, errors
    
    # Validate keyframe
    if not keyframe:
        errors.append("Keyframe is empty")
        return False, errors
    
    if len(keyframe) != height:
        errors.append(f"Keyframe height mismatch: expected {height}, got {len(keyframe)}")
    
    for y, row in enumerate(keyframe):
        if len(row) != width:
            errors.append(f"Keyframe row {y} width mismatch: expected {width}, got {len(row)}")
    
    # Validate deltas
    if not isinstance(deltas, list):
        errors.append(f"Deltas must be a list, got {type(deltas)}")
        return False, errors
    
    for i, delta in enumerate(deltas):
        if not isinstance(delta, dict):
            errors.append(f"Delta {i} is not a dictionary")
            continue
        
        # Check required fields
        if "frame_index" not in delta:
            errors.append(f"Delta {i} missing 'frame_index' field")
        
        is_keyframe = delta.get("is_keyframe", False)
        
        if is_keyframe:
            # Validate keyframe delta
            if "frame_data" not in delta:
                errors.append(f"Delta {i} is keyframe but missing 'frame_data'")
        else:
            # Validate regular delta
            if "changes" not in delta:
                errors.append(f"Delta {i} missing 'changes' field")
                continue
            
            changes = delta["changes"]
            if not isinstance(changes, list):
                errors.append(f"Delta {i} changes must be a list")
                continue
            
            # Validate each change
            for j, change in enumerate(changes):
                if not isinstance(change, dict):
                    errors.append(f"Delta {i} change {j} is not a dictionary")
                    continue
                
                if "x" not in change or "y" not in change or "color" not in change:
                    errors.append(f"Delta {i} change {j} missing required fields (x, y, color)")
                    continue
                
                x, y = change["x"], change["y"]
                if not isinstance(x, int) or not isinstance(y, int):
                    errors.append(f"Delta {i} change {j} coordinates must be integers")
                    continue
                
                if x < 0 or x >= width or y < 0 or y >= height:
                    errors.append(
                        f"Delta {i} change {j} coordinates out of bounds: "
                        f"({x}, {y}) for {width}×{height} frame"
                    )
    
    is_valid = len(errors) == 0
    return is_valid, errors


def analyze_animation_deltas(frames: list[list[list[str]]]) -> dict[str, Any]:
    """
    Analyze animation frames to estimate delta encoding benefits.
    
    Useful for deciding whether to use delta encoding.
    
    Args:
        frames: List of frame grids to analyze
    
    Returns:
        dict with analysis results:
            - avg_changes_per_frame: Average pixel changes between frames
            - max_changes: Maximum changes in any frame transition
            - min_changes: Minimum changes in any frame transition
            - estimated_compression: Estimated compression percentage
            - recommendation: "use_delta" or "use_full_frames"
        
    Example:
        >>> frames = [
        ...     [['#FF0000'] * 16] * 16,  # Frame 0
        ...     [['#FF0000'] * 16] * 16,  # Frame 1 (identical)
        ... ]
        >>> analysis = analyze_animation_deltas(frames)
        >>> print(analysis['avg_changes_per_frame'])
        0.0
        >>> print(analysis['recommendation'])
        use_delta
    """
    if len(frames) < 2:
        return {
            "avg_changes_per_frame": 0,
            "max_changes": 0,
            "min_changes": 0,
            "estimated_compression": 0,
            "recommendation": "insufficient_frames"
        }
    
    height = len(frames[0])
    width = len(frames[0][0]) if height > 0 else 0
    total_pixels = width * height
    
    # Analyze changes between consecutive frames
    changes_per_frame = []
    
    for i in range(1, len(frames)):
        current_frame = frames[i]
        previous_frame = frames[i - 1]
        
        changes = 0
        for y in range(height):
            for x in range(width):
                if current_frame[y][x] != previous_frame[y][x]:
                    changes += 1
        
        changes_per_frame.append(changes)
    
    avg_changes = sum(changes_per_frame) / len(changes_per_frame) if changes_per_frame else 0
    max_changes = max(changes_per_frame) if changes_per_frame else 0
    min_changes = min(changes_per_frame) if changes_per_frame else 0
    
    # Estimate compression
    total_changes = sum(changes_per_frame)
    uncompressed = total_pixels * len(frames)
    compressed = total_pixels + total_changes  # Keyframe + changes
    estimated_compression = (1 - compressed / uncompressed) * 100 if uncompressed > 0 else 0
    
    # Recommendation
    if avg_changes < total_pixels * 0.3:  # Less than 30% change per frame
        recommendation = "use_delta"
    elif avg_changes < total_pixels * 0.6:  # 30-60% change
        recommendation = "delta_beneficial"
    else:
        recommendation = "use_full_frames"
    
    return {
        "frame_count": len(frames),
        "frame_size": f"{width}×{height}",
        "total_pixels_per_frame": total_pixels,
        "avg_changes_per_frame": round(avg_changes, 1),
        "max_changes": max_changes,
        "min_changes": min_changes,
        "avg_change_percentage": round(avg_changes / total_pixels * 100, 1) if total_pixels > 0 else 0,
        "estimated_compression": round(estimated_compression, 1),
        "recommendation": recommendation
    }