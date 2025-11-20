"""
Sprite Complexity Analyzer for Adaptive Encoding Selection

This module analyzes pixel art sprites to determine their complexity characteristics,
which are used to intelligently select the optimal compression encoding strategy.

Key Metrics:
- Entropy: Color randomness (0.0 = uniform, 1.0 = random)
- Repetition: How often colors repeat consecutively (0.0 = no repetition, 1.0 = high)
- Structure: Geometric vs organic patterns (0.0 = organic, 1.0 = geometric)
- RLE Ratio: Predicted RLE compression efficiency

Author: Code Mode Agent
Version: 1.0.0
Date: 2025-11-19
"""

import math
from typing import Any, TypedDict


class ComplexityMetrics(TypedDict):
    """Sprite complexity analysis metrics."""
    unique_colors: int
    entropy: float  # 0.0 (uniform) to 1.0 (random)
    repetition_score: float  # 0.0 (no repetition) to 1.0 (high repetition)
    structure_score: float  # 0.0 (organic) to 1.0 (geometric)
    estimated_rle_ratio: float  # Predicted RLE segments/pixels ratio (lower = better compression)
    avg_run_length: float  # Average consecutive pixel run length


def analyze_sprite_complexity(grid: list[list[str]]) -> ComplexityMetrics:
    """
    Analyze sprite complexity to guide encoding selection.
    
    This function computes various metrics that predict how well different
    compression strategies will perform on the given sprite.
    
    Args:
        grid: 2D pixel array where each element is a color hex code or "transparent"
    
    Returns:
        ComplexityMetrics containing:
        - unique_colors: Number of distinct colors
        - entropy: Normalized color randomness (0-1)
        - repetition_score: How often colors repeat (0-1)
        - structure_score: Geometric vs organic (0-1)
        - estimated_rle_ratio: Predicted RLE compression (lower = better)
        - avg_run_length: Average run length in pixels
    
    Example:
        >>> grid = [["#FF0000", "#FF0000"], ["#00FF00", "#00FF00"]]
        >>> metrics = analyze_sprite_complexity(grid)
        >>> print(f"Entropy: {metrics['entropy']:.2f}")
        >>> print(f"RLE would compress to {metrics['estimated_rle_ratio']:.1%} of original")
    """
    height = len(grid)
    width = len(grid[0]) if grid else 0
    total_pixels = width * height
    
    if total_pixels == 0:
        return ComplexityMetrics(
            unique_colors=0,
            entropy=0.0,
            repetition_score=0.0,
            structure_score=0.0,
            estimated_rle_ratio=1.0,
            avg_run_length=1.0
        )
    
    # Flatten grid for 1D analysis
    pixels = []
    for row in grid:
        pixels.extend(row)
    
    # 1. Count unique colors
    unique_colors = len(set(pixels))
    
    # 2. Calculate entropy (color randomness)
    color_counts: dict[str, int] = {}
    for pixel in pixels:
        color_counts[pixel] = color_counts.get(pixel, 0) + 1
    
    entropy = 0.0
    for count in color_counts.values():
        prob = count / total_pixels
        if prob > 0:
            entropy -= prob * math.log2(prob)
    
    # Normalize entropy (0.0 = uniform, 1.0 = max randomness)
    max_entropy = math.log2(unique_colors) if unique_colors > 1 else 1.0
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
    
    # 3. Calculate repetition score (consecutive pixel runs)
    consecutive_runs = 0
    run_length_sum = 0
    current_color = pixels[0]
    current_run = 1
    
    for pixel in pixels[1:]:
        if pixel == current_color:
            current_run += 1
        else:
            consecutive_runs += 1
            run_length_sum += current_run
            current_color = pixel
            current_run = 1
    
    # Add final run
    consecutive_runs += 1
    run_length_sum += current_run
    
    avg_run_length = run_length_sum / consecutive_runs if consecutive_runs > 0 else 1.0
    
    # Repetition score: higher when fewer runs (more repetition)
    repetition_score = 1.0 - (consecutive_runs / total_pixels)
    
    # 4. Calculate structure score (geometric vs organic)
    # Analyze horizontal and vertical line consistency
    horizontal_runs = 0
    for row in grid:
        runs = _find_runs_in_list(row)
        horizontal_runs += len(runs)
    
    vertical_runs = 0
    for x in range(width):
        column = [grid[y][x] for y in range(height)]
        runs = _find_runs_in_list(column)
        vertical_runs += len(runs)
    
    # Structure score: geometric patterns have more horizontal/vertical runs
    total_possible_lines = height + width
    if total_possible_lines > 0:
        structure_score = (horizontal_runs + vertical_runs) / (total_possible_lines * 5)
        structure_score = min(1.0, structure_score)  # Clamp to [0, 1]
    else:
        structure_score = 0.5
    
    # 5. Estimate RLE compression ratio
    # This is the ratio of RLE segments to total pixels (lower = better compression)
    estimated_rle_ratio = consecutive_runs / total_pixels
    
    return ComplexityMetrics(
        unique_colors=unique_colors,
        entropy=normalized_entropy,
        repetition_score=repetition_score,
        structure_score=structure_score,
        estimated_rle_ratio=estimated_rle_ratio,
        avg_run_length=avg_run_length
    )


def estimate_complexity_from_design(design_spec: dict[str, Any]) -> ComplexityMetrics:
    """
    Estimate complexity from design specification before pixel implementation.
    
    This uses heuristics based on design language to predict sprite complexity
    without having the actual pixel data yet. Useful for pre-selecting encoding
    strategies in DetailAgent.
    
    Args:
        design_spec: Design specification from DesignAgent, containing:
            - shape_language: Description of shapes used
            - composition: Layout and structure description
            - complexity_level: Optional explicit complexity rating
    
    Returns:
        ComplexityMetrics with estimated values
    
    Example:
        >>> design = {
        ...     "shape_language": {"primary": "simple geometric shapes"},
        ...     "composition": {"layout": "solid background with centered icon"}
        ... }
        >>> metrics = estimate_complexity_from_design(design)
        >>> # metrics.structure_score will be high (geometric)
    """
    # Extract design attributes
    shape_language = design_spec.get("shape_language", {})
    composition = design_spec.get("composition", {})
    
    # Heuristic scoring (default: medium complexity)
    estimated_entropy = 0.5
    estimated_repetition = 0.5
    estimated_structure = 0.5
    estimated_unique_colors = 8
    
    # Analyze shape language keywords
    shapes_text = str(shape_language).lower()
    
    if any(keyword in shapes_text for keyword in ["simple", "geometric", "basic", "clean"]):
        estimated_structure = 0.8
        estimated_repetition = 0.7
        estimated_entropy = 0.3
        estimated_unique_colors = 6
    elif any(keyword in shapes_text for keyword in ["organic", "detailed", "complex", "intricate"]):
        estimated_structure = 0.3
        estimated_entropy = 0.7
        estimated_repetition = 0.4
        estimated_unique_colors = 12
    
    # Analyze composition keywords
    comp_text = str(composition).lower()
    
    if any(keyword in comp_text for keyword in ["solid", "uniform", "flat", "simple"]):
        estimated_repetition = 0.9
        estimated_entropy = 0.2
        estimated_structure = 0.8
    elif any(keyword in comp_text for keyword in ["gradient", "shading", "dithered"]):
        estimated_repetition = 0.6
        estimated_entropy = 0.5
    elif any(keyword in comp_text for keyword in ["detailed", "complex", "varied"]):
        estimated_entropy = 0.7
        estimated_repetition = 0.4
    
    # Estimate RLE ratio based on entropy and repetition
    # Lower entropy + higher repetition = better RLE compression
    estimated_rle_ratio = 0.3 + (estimated_entropy * 0.3) - (estimated_repetition * 0.2)
    estimated_rle_ratio = max(0.1, min(1.0, estimated_rle_ratio))  # Clamp to [0.1, 1.0]
    
    # Estimate average run length
    avg_run_length = 1.0 + (estimated_repetition * 9.0)  # 1-10 pixels
    
    return ComplexityMetrics(
        unique_colors=estimated_unique_colors,
        entropy=estimated_entropy,
        repetition_score=estimated_repetition,
        structure_score=estimated_structure,
        estimated_rle_ratio=estimated_rle_ratio,
        avg_run_length=avg_run_length
    )


def _find_runs_in_list(lst: list[str]) -> list[int]:
    """
    Find runs of consecutive same values in a list.
    
    Args:
        lst: List of values (typically colors)
    
    Returns:
        List of run lengths
    
    Example:
        >>> _find_runs_in_list(["A", "A", "B", "C", "C", "C"])
        [2, 1, 3]
    """
    if not lst:
        return []
    
    runs = []
    current_val = lst[0]
    current_len = 1
    
    for val in lst[1:]:
        if val == current_val:
            current_len += 1
        else:
            runs.append(current_len)
            current_val = val
            current_len = 1
    
    # Add final run
    runs.append(current_len)
    return runs


def recommend_encoding_strategy(
    complexity: ComplexityMetrics,
    pixel_count: int,
    palette_size: int | None = None
) -> str:
    """
    Recommend optimal encoding strategy based on complexity metrics.
    
    Decision logic:
    1. Palette indexing: Best for limited palettes (≤16 colors) and medium+ sprites
    2. RLE: Best for high repetition and low entropy
    3. Standard grid: Best for small sprites or high complexity
    
    Args:
        complexity: ComplexityMetrics from analyze_sprite_complexity()
        pixel_count: Total number of pixels (width × height)
        palette_size: Number of unique colors (optional, uses complexity.unique_colors if None)
    
    Returns:
        Encoding strategy: "palette_indexed_rle", "rle", or "standard"
    
    Example:
        >>> metrics = analyze_sprite_complexity(grid)
        >>> strategy = recommend_encoding_strategy(metrics, 256, 8)
        >>> print(f"Recommended: {strategy}")
    """
    if palette_size is None:
        palette_size = complexity["unique_colors"]
    
    # Strategy 1: Palette indexing (best for limited palettes)
    # Use when: ≤16 colors AND sprite is medium-large (>128 pixels)
    if palette_size <= 16 and pixel_count > 128:
        return "palette_indexed_rle"
    
    # Strategy 2: RLE (best for high repetition)
    # Use when: Large sprite (>256 pixels) OR high compression predicted
    if pixel_count > 256 or complexity["estimated_rle_ratio"] < 0.4:
        # High compression predicted (RLE ratio < 0.4 means < 40% segments)
        return "rle"
    
    # Strategy 3: Standard grid (no compression overhead needed)
    # Use for: Small sprites, high complexity, low repetition
    return "standard"


def get_compression_estimate(
    complexity: ComplexityMetrics,
    pixel_count: int,
    encoding: str
) -> dict[str, float]:
    """
    Estimate compression ratio and token savings for a given encoding strategy.
    
    Args:
        complexity: ComplexityMetrics from analysis
        pixel_count: Total pixels (width × height)
        encoding: Encoding strategy ("palette_indexed_rle", "rle", or "standard")
    
    Returns:
        Dictionary containing:
        - compression_ratio: Ratio of compressed/uncompressed (lower = better)
        - token_estimate: Estimated token count
        - token_savings: Estimated tokens saved vs standard
    
    Example:
        >>> estimate = get_compression_estimate(metrics, 256, "palette_indexed_rle")
        >>> print(f"Estimated compression: {estimate['compression_ratio']:.1%}")
    """
    # Base token estimate for standard grid
    base_tokens = pixel_count * 9  # ~9 tokens per pixel for standard format
    
    if encoding == "palette_indexed_rle":
        # Palette overhead + indexed RLE segments
        palette_tokens = complexity["unique_colors"] * 10  # ~10 tokens per color
        segment_count = pixel_count * complexity["estimated_rle_ratio"]
        segment_tokens = segment_count * 4  # ~4 tokens per indexed segment
        total_tokens = palette_tokens + segment_tokens
        
    elif encoding == "rle":
        # RLE segments with full hex codes
        segment_count = pixel_count * complexity["estimated_rle_ratio"]
        total_tokens = segment_count * 7  # ~7 tokens per RLE segment
        
    else:  # standard
        total_tokens = base_tokens
    
    compression_ratio = total_tokens / base_tokens
    token_savings = base_tokens - total_tokens
    
    return {
        "compression_ratio": compression_ratio,
        "token_estimate": int(total_tokens),
        "token_savings": int(token_savings)
    }