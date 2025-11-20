"""
Metadata schema for adaptive threshold monitoring in Phase 3.

This module defines TypedDict structures for tracking encoding decisions,
complexity analysis, and performance metrics across sprite generation.
"""

from typing import TypedDict, Literal, Optional
from datetime import datetime


class ComplexityMetrics(TypedDict):
    """Complexity analysis results from sprite analysis."""
    
    unique_colors: int
    """Number of distinct colors in the sprite"""
    
    entropy: float
    """Color randomness measure (0.0 = uniform, 1.0 = random)"""
    
    repetition_score: float
    """Consecutive pixel repetition (0.0 = none, 1.0 = high)"""
    
    structure_score: float
    """Geometric vs organic (0.0 = organic, 1.0 = geometric)"""
    
    estimated_rle_ratio: float
    """Predicted RLE compression ratio (segments/pixels)"""
    
    avg_run_length: float
    """Average consecutive pixel run length"""


class EncodingDecision(TypedDict):
    """Encoding strategy decision details with predictions and actuals."""
    
    # Recommendation
    recommended_encoding: Literal["palette_indexed_rle", "rle", "standard"]
    """Encoding strategy selected by complexity analyzer"""
    
    selected_encoding: Literal["palette_indexed_rle", "rle", "standard"]
    """Actual encoding used (may differ from recommended)"""
    
    reasons: list[str]
    """Human-readable reasons for encoding selection"""
    
    # Compression estimates
    estimated_compression: float
    """Predicted compression ratio before generation"""
    
    actual_compression: Optional[float]
    """Actual compression ratio after generation (if available)"""


class PerformanceMetrics(TypedDict):
    """Performance tracking for analysis operations."""
    
    analysis_time_ms: float
    """Time spent on complexity analysis in milliseconds"""
    
    prediction_accuracy_percent: Optional[float]
    """Prediction error percentage (if actual data available)"""


class SpriteMetadata(TypedDict):
    """Complete metadata for a single sprite generation with adaptive thresholds."""
    
    # Core identification
    request_id: str
    """Unique identifier for the sprite request"""
    
    agent: str
    """Agent that generated the sprite (e.g., 'detail')"""
    
    model: str
    """LLM model used (e.g., 'claude-3-5-sonnet-20241022')"""
    
    timestamp: str
    """ISO 8601 timestamp of generation"""
    
    # Sprite characteristics
    dimensions: str
    """Sprite dimensions as string (e.g., '16x16')"""
    
    pixel_count: int
    """Total number of pixels (width * height)"""
    
    palette_size: int
    """Number of colors in the palette"""
    
    asset_type: str
    """Type of asset (e.g., 'sprite', 'icon', 'character')"""
    
    is_animated: bool
    """Whether the sprite is animated"""
    
    # Analysis results
    complexity_metrics: ComplexityMetrics
    """Complexity analysis measurements"""
    
    encoding_decision: EncodingDecision
    """Encoding strategy decision details"""
    
    performance_metrics: PerformanceMetrics
    """Performance tracking data"""
    
    # Validation flags
    meets_performance_target: bool
    """Whether analysis_time_ms < 10ms target"""
    
    meets_accuracy_target: Optional[bool]
    """Whether prediction error < 15% target (if data available)"""