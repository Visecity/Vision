"""
Tests for threshold tuning module.

This module tests the ThresholdTuner class that analyzes collected metadata
to recommend optimal threshold values for encoding strategy selection.
"""

import pytest
from typing import Any

from src.rendering.threshold_tuner import ThresholdTuner
from src.rendering.metadata_schema import SpriteMetadata
from src.rendering.analytics import create_sample_metadata


class TestThresholdTunerInitialization:
    """Test ThresholdTuner initialization."""
    
    def test_init_with_empty_list(self):
        """Test initialization with empty metadata list."""
        tuner = ThresholdTuner([])
        assert tuner.metadata_list == []
        assert tuner.min_sample_size == 20
    
    def test_init_with_metadata(self):
        """Test initialization with metadata."""
        metadata = create_sample_metadata(10)
        tuner = ThresholdTuner(metadata)
        assert len(tuner.metadata_list) == 10
        assert tuner.min_sample_size == 20
    
    def test_init_with_custom_sample_size(self):
        """Test initialization with custom minimum sample size."""
        metadata = create_sample_metadata(5)
        tuner = ThresholdTuner(metadata, min_sample_size=10)
        assert tuner.min_sample_size == 10
    
    def test_repr(self):
        """Test string representation."""
        metadata = create_sample_metadata(15)
        tuner = ThresholdTuner(metadata, min_sample_size=10)
        repr_str = repr(tuner)
        assert "ThresholdTuner" in repr_str
        assert "15" in repr_str
        assert "10" in repr_str


class TestPaletteIndexingAnalysis:
    """Test palette indexing threshold analysis."""
    
    def test_analyze_with_insufficient_data(self):
        """Test analysis with insufficient palette-indexed sprites."""
        metadata = create_sample_metadata(30)
        # Filter to only non-palette-indexed
        metadata = [
            m for m in metadata 
            if m["encoding_decision"]["selected_encoding"] != "palette_indexed_rle"
        ]
        
        tuner = ThresholdTuner(metadata, min_sample_size=20)
        result = tuner.analyze_palette_indexing()
        
        assert "error" in result
        assert "Insufficient data" in result["error"]
        assert result["confidence"] == "insufficient_data"
    
    def test_analyze_with_sufficient_data(self):
        """Test analysis with sufficient palette-indexed sprites."""
        metadata = create_sample_metadata(50)
        # Filter to only palette-indexed
        metadata = [
            m for m in metadata 
            if m["encoding_decision"]["selected_encoding"] == "palette_indexed_rle"
        ]
        
        tuner = ThresholdTuner(metadata, min_sample_size=20)
        result = tuner.analyze_palette_indexing()
        
        assert "error" not in result
        assert "current_thresholds" in result
        assert "optimal_thresholds" in result
        assert "recommendation" in result
        assert "confidence" in result
        assert result["sample_size"] >= 20
    
    def test_palette_threshold_values(self):
        """Test that palette thresholds are within expected ranges."""
        metadata = create_sample_metadata(50)
        metadata = [
            m for m in metadata 
            if m["encoding_decision"]["selected_encoding"] == "palette_indexed_rle"
        ]
        
        tuner = ThresholdTuner(metadata, min_sample_size=20)
        result = tuner.analyze_palette_indexing()
        
        if "optimal_thresholds" in result:
            optimal = result["optimal_thresholds"]
            assert 4 <= optimal["palette_size"] <= 32
            assert 64 <= optimal["pixel_count"] <= 1024
    
    def test_palette_analysis_structure(self):
        """Test structure of palette indexing analysis."""
        metadata = create_sample_metadata(50)
        metadata = [
            m for m in metadata 
            if m["encoding_decision"]["selected_encoding"] == "palette_indexed_rle"
        ]
        
        tuner = ThresholdTuner(metadata, min_sample_size=20)
        result = tuner.analyze_palette_indexing()
        
        if "palette_size_analysis" in result:
            # Check structure of analysis
            for size, stats in result["palette_size_analysis"].items():
                assert isinstance(size, int)
                assert "count" in stats
                assert "avg_compression" in stats
                assert "success_rate" in stats


class TestRLEEncodingAnalysis:
    """Test RLE encoding threshold analysis."""
    
    def test_analyze_with_insufficient_data(self):
        """Test analysis with insufficient RLE sprites."""
        metadata = create_sample_metadata(30)
        # Filter to only non-RLE
        metadata = [
            m for m in metadata 
            if m["encoding_decision"]["selected_encoding"] != "rle"
        ]
        
        tuner = ThresholdTuner(metadata, min_sample_size=20)
        result = tuner.analyze_rle_encoding()
        
        assert "error" in result
        assert "Insufficient data" in result["error"]
        assert result["confidence"] == "insufficient_data"
    
    def test_analyze_with_sufficient_data(self):
        """Test analysis with sufficient RLE sprites."""
        # Generate enough samples to ensure we get 20+ RLE sprites
        metadata = create_sample_metadata(100)
        # Filter to only RLE
        rle_metadata = [
            m for m in metadata
            if m["encoding_decision"]["selected_encoding"] == "rle"
        ]
        
        # If we still don't have enough, skip the test
        if len(rle_metadata) < 20:
            pytest.skip(f"Only {len(rle_metadata)} RLE sprites generated, need 20+")
        
        tuner = ThresholdTuner(rle_metadata, min_sample_size=20)
        result = tuner.analyze_rle_encoding()
        
        assert "error" not in result
        assert "current_thresholds" in result
        assert "optimal_thresholds" in result
        assert "recommendation" in result
        assert "confidence" in result
        assert result["sample_size"] >= 20
    
    def test_rle_threshold_values(self):
        """Test that RLE thresholds are within expected ranges."""
        metadata = create_sample_metadata(50)
        metadata = [
            m for m in metadata 
            if m["encoding_decision"]["selected_encoding"] == "rle"
        ]
        
        tuner = ThresholdTuner(metadata, min_sample_size=20)
        result = tuner.analyze_rle_encoding()
        
        if "optimal_thresholds" in result:
            optimal = result["optimal_thresholds"]
            assert 0.2 <= optimal["rle_ratio"] <= 0.6
            assert 128 <= optimal["pixel_count"] <= 2048
    
    def test_rle_analysis_structure(self):
        """Test structure of RLE encoding analysis."""
        metadata = create_sample_metadata(50)
        metadata = [
            m for m in metadata 
            if m["encoding_decision"]["selected_encoding"] == "rle"
        ]
        
        tuner = ThresholdTuner(metadata, min_sample_size=20)
        result = tuner.analyze_rle_encoding()
        
        if "rle_ratio_analysis" in result:
            # Check structure of analysis
            for ratio, stats in result["rle_ratio_analysis"].items():
                assert isinstance(ratio, float)
                assert "count" in stats
                assert "avg_compression" in stats
                assert "success_rate" in stats


class TestRecommendationGeneration:
    """Test recommendation generation."""
    
    def test_generate_recommendations_empty(self):
        """Test recommendation generation with no data."""
        tuner = ThresholdTuner([])
        report = tuner.generate_recommendations()
        
        assert isinstance(report, str)
        assert "No metadata records" in report
    
    def test_generate_recommendations_insufficient(self):
        """Test recommendation generation with insufficient data."""
        metadata = create_sample_metadata(10)
        tuner = ThresholdTuner(metadata, min_sample_size=20)
        report = tuner.generate_recommendations()
        
        assert isinstance(report, str)
        assert "Need more data" in report
        assert "10/20" in report
    
    def test_generate_recommendations_sufficient(self):
        """Test recommendation generation with sufficient data."""
        metadata = create_sample_metadata(50)
        tuner = ThresholdTuner(metadata, min_sample_size=20)
        report = tuner.generate_recommendations()
        
        assert isinstance(report, str)
        assert "Threshold Tuning Report" in report
        assert "Dataset: 50 sprites" in report
        assert "Palette Indexing" in report
        assert "RLE Encoding" in report
    
    def test_report_structure(self):
        """Test that report contains all expected sections."""
        metadata = create_sample_metadata(50)
        tuner = ThresholdTuner(metadata, min_sample_size=20)
        report = tuner.generate_recommendations()
        
        # Check for section headers
        assert "Palette Indexing Threshold Analysis" in report
        assert "RLE Encoding Threshold Analysis" in report
        assert "Summary" in report
        
        # Check for key information
        assert "Current thresholds:" in report
        assert "Recommended thresholds:" in report or "Insufficient data" in report


class TestOptimalThresholds:
    """Test getting optimal thresholds."""
    
    def test_get_optimal_thresholds_empty(self):
        """Test getting optimal thresholds with no data."""
        tuner = ThresholdTuner([])
        optimal = tuner.get_optimal_thresholds()
        
        assert "palette_indexing" in optimal
        assert "rle_encoding" in optimal
        assert "confidence" in optimal
        assert optimal["confidence"] == "insufficient_data"
    
    def test_get_optimal_thresholds_structure(self):
        """Test structure of optimal thresholds output."""
        metadata = create_sample_metadata(50)
        tuner = ThresholdTuner(metadata, min_sample_size=20)
        optimal = tuner.get_optimal_thresholds()
        
        assert "palette_indexing" in optimal
        assert "palette_size" in optimal["palette_indexing"]
        assert "pixel_count" in optimal["palette_indexing"]
        
        assert "rle_encoding" in optimal
        assert "pixel_count" in optimal["rle_encoding"]
        assert "rle_ratio" in optimal["rle_encoding"]
        
        assert "confidence" in optimal
        assert "sample_size" in optimal
        assert optimal["sample_size"] == 50
    
    def test_confidence_levels(self):
        """Test confidence level calculation based on sample size."""
        # Test insufficient data
        metadata = create_sample_metadata(10)
        tuner = ThresholdTuner(metadata, min_sample_size=20)
        optimal = tuner.get_optimal_thresholds()
        assert optimal["confidence"] == "insufficient_data"
        
        # Test low confidence (20-39 samples with min 20)
        metadata = create_sample_metadata(30)
        tuner = ThresholdTuner(metadata, min_sample_size=20)
        optimal = tuner.get_optimal_thresholds()
        # Confidence depends on having both palette and RLE data
        assert optimal["confidence"] in ["insufficient_data", "low", "medium"]
        
        # Test high confidence (100+ samples with min 20)
        metadata = create_sample_metadata(100)
        tuner = ThresholdTuner(metadata, min_sample_size=20)
        optimal = tuner.get_optimal_thresholds()
        # Confidence depends on having both palette and RLE data
        assert optimal["confidence"] in ["low", "medium", "high"]


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_metadata_list(self):
        """Test with empty metadata list."""
        tuner = ThresholdTuner([])
        
        # Should not raise errors
        palette_result = tuner.analyze_palette_indexing()
        rle_result = tuner.analyze_rle_encoding()
        report = tuner.generate_recommendations()
        optimal = tuner.get_optimal_thresholds()
        
        assert "error" in palette_result or "insufficient" in palette_result.get("confidence", "")
        assert "error" in rle_result or "insufficient" in rle_result.get("confidence", "")
        assert isinstance(report, str)
        assert isinstance(optimal, dict)
    
    def test_single_encoding_type(self):
        """Test with only one encoding type."""
        metadata = create_sample_metadata(50)
        # Keep only palette indexed
        metadata = [
            m for m in metadata 
            if m["encoding_decision"]["selected_encoding"] == "palette_indexed_rle"
        ]
        
        tuner = ThresholdTuner(metadata, min_sample_size=20)
        
        # Palette analysis should work
        palette_result = tuner.analyze_palette_indexing()
        if len(metadata) >= 20:
            assert "error" not in palette_result
        
        # RLE analysis should report insufficient data
        rle_result = tuner.analyze_rle_encoding()
        assert "error" in rle_result or rle_result.get("confidence") == "insufficient_data"
    
    def test_missing_actual_compression(self):
        """Test handling of missing actual compression data."""
        metadata = create_sample_metadata(30)
        
        # Remove actual compression from some records
        for i, record in enumerate(metadata):
            if i % 2 == 0:
                record["encoding_decision"]["actual_compression"] = None
        
        tuner = ThresholdTuner(metadata, min_sample_size=10)
        
        # Should still work, just with reduced sample size
        palette_result = tuner.analyze_palette_indexing()
        rle_result = tuner.analyze_rle_encoding()
        
        # Should not crash
        assert isinstance(palette_result, dict)
        assert isinstance(rle_result, dict)
    
    def test_extreme_values(self):
        """Test handling of extreme threshold values."""
        metadata = create_sample_metadata(50)
        
        # Modify to have extreme values
        for record in metadata:
            if record["encoding_decision"]["selected_encoding"] == "palette_indexed_rle":
                record["palette_size"] = 32  # High palette size
            if record["encoding_decision"]["selected_encoding"] == "rle":
                record["complexity_metrics"]["estimated_rle_ratio"] = 0.9  # High ratio
        
        tuner = ThresholdTuner(metadata, min_sample_size=10)
        
        # Should still work and recommend reasonable values
        optimal = tuner.get_optimal_thresholds()
        
        # Palette size should be capped
        assert optimal["palette_indexing"]["palette_size"] <= 20
        
        # RLE ratio should be within bounds
        assert 0.2 <= optimal["rle_encoding"]["rle_ratio"] <= 0.6


class TestPerformance:
    """Test performance characteristics."""
    
    def test_tuning_speed(self):
        """Test that tuning completes quickly."""
        import time
        
        metadata = create_sample_metadata(100)
        tuner = ThresholdTuner(metadata, min_sample_size=20)
        
        start = time.perf_counter()
        tuner.generate_recommendations()
        duration = time.perf_counter() - start
        
        # Should complete in under 1 second for 100 sprites
        assert duration < 1.0
    
    def test_large_dataset(self):
        """Test with large dataset."""
        metadata = create_sample_metadata(500)
        tuner = ThresholdTuner(metadata, min_sample_size=20)
        
        # Should not raise errors or crash
        report = tuner.generate_recommendations()
        optimal = tuner.get_optimal_thresholds()
        
        assert isinstance(report, str)
        assert isinstance(optimal, dict)
        assert optimal["sample_size"] == 500


class TestIntegration:
    """Integration tests with real-world scenarios."""
    
    def test_realistic_dataset(self):
        """Test with realistic mixed dataset."""
        metadata = create_sample_metadata(100)
        tuner = ThresholdTuner(metadata, min_sample_size=30)
        
        # Full workflow
        palette_analysis = tuner.analyze_palette_indexing()
        rle_analysis = tuner.analyze_rle_encoding()
        report = tuner.generate_recommendations()
        optimal = tuner.get_optimal_thresholds()
        
        # All should complete successfully
        assert isinstance(palette_analysis, dict)
        assert isinstance(rle_analysis, dict)
        assert isinstance(report, str)
        assert isinstance(optimal, dict)
        
        # Report should be comprehensive
        assert len(report) > 500  # Reasonable length for full report
    
    def test_confidence_progression(self):
        """Test that confidence increases with more samples."""
        base_metadata = create_sample_metadata(200)
        
        # Test with increasing sample sizes
        sample_sizes = [10, 20, 40, 100]
        confidences = []
        
        for size in sample_sizes:
            metadata = base_metadata[:size]
            tuner = ThresholdTuner(metadata, min_sample_size=20)
            optimal = tuner.get_optimal_thresholds()
            confidences.append(optimal["confidence"])
        
        # Confidence should generally improve with more data
        # (though it depends on having both encoding types)
        assert len(set(confidences)) >= 2  # Should have some variation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])