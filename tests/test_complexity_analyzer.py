"""
Unit Tests for Sprite Complexity Analyzer

Tests the complexity analysis functions that guide adaptive encoding selection.

Author: Code Mode Agent
Version: 1.0.0
Date: 2025-11-19
"""

import pytest
from src.rendering.complexity_analyzer import (
    analyze_sprite_complexity,
    estimate_complexity_from_design,
    recommend_encoding_strategy,
    get_compression_estimate,
    ComplexityMetrics,
    _find_runs_in_list,
)


class TestAnalyzeSpriteComplexity:
    """Test core sprite complexity analysis."""
    
    def test_uniform_sprite(self):
        """Test analysis of completely uniform sprite (single color)."""
        # 4×4 sprite, all red
        grid = [["#FF0000"] * 4 for _ in range(4)]
        
        metrics = analyze_sprite_complexity(grid)
        
        assert metrics["unique_colors"] == 1
        assert metrics["entropy"] == 0.0  # Perfectly uniform
        assert metrics["repetition_score"] > 0.9  # High repetition
        assert metrics["estimated_rle_ratio"] < 0.1  # Very few runs (should be ~1/16)
        assert metrics["avg_run_length"] == 16.0  # One long run
    
    def test_random_sprite(self):
        """Test analysis of random/noisy sprite (high entropy)."""
        # 4×4 sprite with all different colors
        colors = [f"#{i:06x}" for i in range(16)]
        grid = [colors[i*4:(i+1)*4] for i in range(4)]
        
        metrics = analyze_sprite_complexity(grid)
        
        assert metrics["unique_colors"] == 16
        assert metrics["entropy"] > 0.95  # High randomness
        assert metrics["repetition_score"] < 0.1  # Low repetition
        assert metrics["estimated_rle_ratio"] > 0.9  # Many runs (each pixel is a run)
        assert metrics["avg_run_length"] == 1.0  # Each pixel is its own run
    
    def test_striped_sprite(self):
        """Test analysis of horizontally striped sprite."""
        # 4×4 sprite with alternating red/blue rows
        grid = [
            ["#FF0000"] * 4,  # Red row
            ["#0000FF"] * 4,  # Blue row
            ["#FF0000"] * 4,  # Red row
            ["#0000FF"] * 4,  # Blue row
        ]
        
        metrics = analyze_sprite_complexity(grid)
        
        assert metrics["unique_colors"] == 2
        assert metrics["entropy"] == 1.0  # Two colors equally distributed = max entropy
        assert metrics["repetition_score"] > 0.7  # High horizontal repetition
        assert metrics["structure_score"] >= 0.5  # Geometric structure
        assert metrics["estimated_rle_ratio"] < 0.3  # Good RLE compression (4 runs)
    
    def test_checkerboard_sprite(self):
        """Test analysis of checkerboard pattern."""
        # 4×4 checkerboard
        grid = []
        for y in range(4):
            row = []
            for x in range(4):
                color = "#FF0000" if (x + y) % 2 == 0 else "#0000FF"
                row.append(color)
            grid.append(row)
        
        metrics = analyze_sprite_complexity(grid)
        
        assert metrics["unique_colors"] == 2
        assert metrics["repetition_score"] < 0.5  # Low repetition (alternating)
        assert metrics["estimated_rle_ratio"] > 0.5  # Poor RLE compression (many runs)
        assert 1.0 < metrics["avg_run_length"] <= 1.5  # Short runs due to checkerboard pattern
    
    def test_empty_grid(self):
        """Test analysis of empty grid."""
        grid: list[list[str]] = []
        
        metrics = analyze_sprite_complexity(grid)
        
        assert metrics["unique_colors"] == 0
        assert metrics["entropy"] == 0.0
        assert metrics["repetition_score"] == 0.0
        assert metrics["structure_score"] == 0.0
        assert metrics["estimated_rle_ratio"] == 1.0
        assert metrics["avg_run_length"] == 1.0
    
    def test_single_pixel(self):
        """Test analysis of 1×1 sprite."""
        grid = [["#FF0000"]]
        
        metrics = analyze_sprite_complexity(grid)
        
        assert metrics["unique_colors"] == 1
        assert metrics["entropy"] == 0.0
        assert metrics["repetition_score"] == 0.0  # 1 pixel = 0% additional pixels
        assert metrics["estimated_rle_ratio"] == 1.0  # 1 run / 1 pixel
    
    def test_gradient_sprite(self):
        """Test analysis of gradient (medium complexity)."""
        # 4×4 gradient with 4 distinct shades
        grid = [
            ["#FF0000", "#FF0000", "#CC0000", "#CC0000"],
            ["#FF0000", "#FF0000", "#CC0000", "#CC0000"],
            ["#990000", "#990000", "#660000", "#660000"],
            ["#990000", "#990000", "#660000", "#660000"],
        ]
        
        metrics = analyze_sprite_complexity(grid)
        
        assert metrics["unique_colors"] == 4
        assert metrics["entropy"] == 1.0  # Four colors equally distributed = max entropy
        assert metrics["repetition_score"] >= 0.5  # Some repetition
        assert 0.2 < metrics["estimated_rle_ratio"] <= 0.5  # Moderate compression (can be exactly 0.5)


class TestEstimateComplexityFromDesign:
    """Test complexity estimation from design specifications."""
    
    def test_simple_geometric_design(self):
        """Test estimation for simple geometric design."""
        design = {
            "shape_language": {"primary": "simple geometric shapes"},
            "composition": {"layout": "solid background"}
        }
        
        metrics = estimate_complexity_from_design(design)
        
        assert metrics["structure_score"] > 0.7  # High structure
        assert metrics["repetition_score"] > 0.6  # High repetition
        assert metrics["entropy"] < 0.4  # Low entropy
        assert metrics["unique_colors"] <= 8
        assert metrics["estimated_rle_ratio"] < 0.5  # Good compression
    
    def test_organic_detailed_design(self):
        """Test estimation for organic/detailed design."""
        design = {
            "shape_language": {"primary": "organic detailed forms"},
            "composition": {"layout": "complex varied elements"}
        }
        
        metrics = estimate_complexity_from_design(design)
        
        assert metrics["structure_score"] < 0.5  # Low structure
        assert metrics["entropy"] > 0.6  # High entropy
        assert metrics["unique_colors"] > 8
        assert metrics["estimated_rle_ratio"] > 0.4  # Poorer compression
    
    def test_gradient_design(self):
        """Test estimation for gradient design."""
        design = {
            "composition": {"shading": "gradient shading throughout"}
        }
        
        metrics = estimate_complexity_from_design(design)
        
        assert 0.4 < metrics["repetition_score"] < 0.7  # Medium repetition
        assert 0.3 < metrics["entropy"] < 0.6  # Medium entropy
    
    def test_empty_design_spec(self):
        """Test estimation with minimal design spec."""
        design = {}
        
        metrics = estimate_complexity_from_design(design)
        
        # Should return reasonable defaults (medium complexity)
        assert 0.4 < metrics["entropy"] < 0.6
        assert 0.4 < metrics["repetition_score"] < 0.6
        assert 0.4 < metrics["structure_score"] < 0.6
        assert metrics["unique_colors"] == 8
        assert 0.3 < metrics["estimated_rle_ratio"] < 0.7


class TestRecommendEncodingStrategy:
    """Test encoding strategy recommendation logic."""
    
    def test_recommend_palette_indexing(self):
        """Test recommendation for palette indexing (≤16 colors, >128 pixels)."""
        metrics: ComplexityMetrics = {
            "unique_colors": 8,
            "entropy": 0.4,
            "repetition_score": 0.7,
            "structure_score": 0.6,
            "estimated_rle_ratio": 0.3,
            "avg_run_length": 5.0
        }
        
        strategy = recommend_encoding_strategy(
            metrics,
            pixel_count=256,  # 16×16 sprite
            palette_size=8
        )
        
        assert strategy == "palette_indexed_rle"
    
    def test_recommend_rle_large_sprite(self):
        """Test recommendation for RLE (large sprite >256 pixels)."""
        metrics: ComplexityMetrics = {
            "unique_colors": 20,
            "entropy": 0.5,
            "repetition_score": 0.6,
            "structure_score": 0.5,
            "estimated_rle_ratio": 0.4,
            "avg_run_length": 4.0
        }
        
        strategy = recommend_encoding_strategy(
            metrics,
            pixel_count=512,  # 32×16 sprite
            palette_size=20
        )
        
        assert strategy == "rle"
    
    def test_recommend_rle_high_compression(self):
        """Test recommendation for RLE (high compression predicted)."""
        metrics: ComplexityMetrics = {
            "unique_colors": 25,
            "entropy": 0.3,
            "repetition_score": 0.8,
            "structure_score": 0.7,
            "estimated_rle_ratio": 0.25,  # Very good compression
            "avg_run_length": 8.0
        }
        
        strategy = recommend_encoding_strategy(
            metrics,
            pixel_count=200,  # Medium sprite
            palette_size=25
        )
        
        assert strategy == "rle"  # High compression predicted
    
    def test_recommend_standard_small_sprite(self):
        """Test recommendation for standard (small sprite, moderate complexity)."""
        metrics: ComplexityMetrics = {
            "unique_colors": 20,
            "entropy": 0.6,
            "repetition_score": 0.4,
            "structure_score": 0.4,
            "estimated_rle_ratio": 0.6,  # Poor compression
            "avg_run_length": 2.0
        }
        
        strategy = recommend_encoding_strategy(
            metrics,
            pixel_count=128,  # 8×16 sprite
            palette_size=20
        )
        
        assert strategy == "standard"
    
    def test_recommend_palette_with_none_palette_size(self):
        """Test recommendation using metrics.unique_colors when palette_size is None."""
        metrics: ComplexityMetrics = {
            "unique_colors": 12,
            "entropy": 0.4,
            "repetition_score": 0.7,
            "structure_score": 0.6,
            "estimated_rle_ratio": 0.3,
            "avg_run_length": 5.0
        }
        
        strategy = recommend_encoding_strategy(
            metrics,
            pixel_count=256,
            palette_size=None  # Should use metrics["unique_colors"]
        )
        
        assert strategy == "palette_indexed_rle"


class TestGetCompressionEstimate:
    """Test compression estimation calculations."""
    
    def test_estimate_palette_indexed_rle(self):
        """Test compression estimate for palette indexed RLE."""
        metrics: ComplexityMetrics = {
            "unique_colors": 8,
            "entropy": 0.3,
            "repetition_score": 0.8,
            "structure_score": 0.7,
            "estimated_rle_ratio": 0.2,  # 20% of pixels become segments
            "avg_run_length": 10.0
        }
        
        estimate = get_compression_estimate(
            metrics,
            pixel_count=256,
            encoding="palette_indexed_rle"
        )
        
        # Base tokens = 256 * 9 = 2304
        # Palette tokens = 8 * 10 = 80
        # Segments = 256 * 0.2 = 51.2 segments * 4 tokens = ~205
        # Total ≈ 285 tokens
        assert estimate["compression_ratio"] < 0.2  # Good compression
        assert estimate["token_estimate"] < 400
        assert estimate["token_savings"] > 1900
    
    def test_estimate_rle(self):
        """Test compression estimate for standard RLE."""
        metrics: ComplexityMetrics = {
            "unique_colors": 16,
            "entropy": 0.5,
            "repetition_score": 0.6,
            "structure_score": 0.5,
            "estimated_rle_ratio": 0.3,  # 30% of pixels become segments
            "avg_run_length": 5.0
        }
        
        estimate = get_compression_estimate(
            metrics,
            pixel_count=256,
            encoding="rle"
        )
        
        # Base tokens = 256 * 9 = 2304
        # Segments = 256 * 0.3 = 76.8 segments * 7 tokens = ~538
        assert 0.2 < estimate["compression_ratio"] < 0.3
        assert 400 < estimate["token_estimate"] < 700
        assert estimate["token_savings"] > 1600
    
    def test_estimate_standard(self):
        """Test compression estimate for standard grid (no compression)."""
        metrics: ComplexityMetrics = {
            "unique_colors": 30,
            "entropy": 0.8,
            "repetition_score": 0.3,
            "structure_score": 0.3,
            "estimated_rle_ratio": 0.8,
            "avg_run_length": 1.5
        }
        
        estimate = get_compression_estimate(
            metrics,
            pixel_count=256,
            encoding="standard"
        )
        
        # Base tokens = 256 * 9 = 2304
        assert estimate["compression_ratio"] == 1.0  # No compression
        assert estimate["token_estimate"] == 2304
        assert estimate["token_savings"] == 0
    
    def test_estimate_small_sprite(self):
        """Test compression estimate for small sprite."""
        metrics: ComplexityMetrics = {
            "unique_colors": 4,
            "entropy": 0.2,
            "repetition_score": 0.9,
            "structure_score": 0.8,
            "estimated_rle_ratio": 0.15,
            "avg_run_length": 12.0
        }
        
        estimate = get_compression_estimate(
            metrics,
            pixel_count=64,  # 8×8 sprite
            encoding="palette_indexed_rle"
        )
        
        # Base = 64 * 9 = 576
        # Palette = 4 * 10 = 40
        # Segments = 64 * 0.15 = 9.6 * 4 ≈ 38
        # Total ≈ 78
        assert estimate["compression_ratio"] < 0.2
        assert estimate["token_savings"] > 450


class TestFindRunsInList:
    """Test helper function for finding consecutive runs."""
    
    def test_find_runs_all_same(self):
        """Test finding runs in uniform list."""
        result = _find_runs_in_list(["A", "A", "A", "A"])
        assert result == [4]
    
    def test_find_runs_alternating(self):
        """Test finding runs in alternating list."""
        result = _find_runs_in_list(["A", "B", "A", "B"])
        assert result == [1, 1, 1, 1]
    
    def test_find_runs_mixed(self):
        """Test finding runs in mixed list."""
        result = _find_runs_in_list(["A", "A", "B", "C", "C", "C", "D"])
        assert result == [2, 1, 3, 1]
    
    def test_find_runs_empty(self):
        """Test finding runs in empty list."""
        result = _find_runs_in_list([])
        assert result == []
    
    def test_find_runs_single(self):
        """Test finding runs in single-element list."""
        result = _find_runs_in_list(["A"])
        assert result == [1]


class TestIntegrationScenarios:
    """Test complete workflow with realistic scenarios."""
    
    def test_icon_sprite_workflow(self):
        """Test full analysis workflow for simple icon."""
        # 16×16 icon with 6 colors, mostly solid
        grid = []
        for y in range(16):
            row = []
            for x in range(16):
                if y < 2 or y > 13 or x < 2 or x > 13:
                    row.append("#000000")  # Border
                elif 6 <= y <= 9 and 6 <= x <= 9:
                    row.append("#FF0000")  # Center
                else:
                    row.append("#FFFFFF")  # Background
            grid.append(row)
        
        # Analyze
        metrics = analyze_sprite_complexity(grid)
        assert metrics["unique_colors"] == 3
        assert metrics["structure_score"] > 0.5  # Geometric
        
        # Recommend strategy
        strategy = recommend_encoding_strategy(metrics, 256, 3)
        assert strategy == "palette_indexed_rle"
        
        # Estimate compression
        estimate = get_compression_estimate(metrics, 256, strategy)
        assert estimate["compression_ratio"] < 0.3  # Good compression
    
    def test_character_sprite_workflow(self):
        """Test full analysis workflow for character sprite."""
        # 16×16 character with more colors and detail
        grid = []
        colors = ["#FFE0BD", "#D4A574", "#8B4513", "#654321", "#000000", "transparent"]
        for y in range(16):
            row = []
            for x in range(16):
                # Simulate character outline with varied colors
                if (y + x) % 3 == 0:
                    row.append(colors[y % 5])
                else:
                    row.append(colors[(x + y) % 5])
            grid.append(row)
        
        # Analyze
        metrics = analyze_sprite_complexity(grid)
        assert metrics["unique_colors"] == 5  # Only 5 colors actually used in pattern
        assert metrics["repetition_score"] < 0.7  # More varied
        
        # Recommend strategy
        strategy = recommend_encoding_strategy(metrics, 256, 6)
        assert strategy == "palette_indexed_rle"
        
        # Estimate compression
        estimate = get_compression_estimate(metrics, 256, strategy)
        assert 0.15 < estimate["compression_ratio"] < 0.5  # Allow wider range for complex patterns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])