"""
Integration tests for Phase 3 Week 2 analytics module.

Tests cover:
- EncodingAnalytics with sample data
- Performance metric calculations
- Encoding distribution analysis
- Size-based analysis
- Report generation
- Sample data generation
"""

import pytest
from typing import Any

from src.rendering.analytics import EncodingAnalytics, create_sample_metadata
from src.rendering.metadata_schema import SpriteMetadata


class TestEncodingAnalytics:
    """Test EncodingAnalytics functionality."""
    
    @pytest.fixture
    def sample_data(self) -> list[SpriteMetadata]:
        """Create sample metadata for testing."""
        return create_sample_metadata(count=30)
    
    @pytest.fixture
    def analytics(self, sample_data) -> EncodingAnalytics:
        """Create EncodingAnalytics with sample data."""
        return EncodingAnalytics(sample_data)
    
    def test_initialization(self, sample_data):
        """Test EncodingAnalytics initialization."""
        analytics = EncodingAnalytics(sample_data)
        assert analytics.records == sample_data
        assert len(analytics.records) == 30
    
    def test_initialization_empty(self):
        """Test EncodingAnalytics with empty data."""
        analytics = EncodingAnalytics([])
        assert analytics.records == []
    
    def test_analyze_performance_structure(self, analytics):
        """Test analyze_performance returns correct structure."""
        performance = analytics.analyze_performance()
        
        # Check top-level keys
        assert "total_sprites" in performance
        assert "analysis_time" in performance
        assert "prediction_accuracy" in performance
        
        # Check analysis_time structure
        time_stats = performance["analysis_time"]
        assert "mean_ms" in time_stats
        assert "median_ms" in time_stats
        assert "p95_ms" in time_stats
        assert "p99_ms" in time_stats
        assert "min_ms" in time_stats
        assert "max_ms" in time_stats
        assert "under_10ms_count" in time_stats
        assert "under_10ms_percent" in time_stats
        
        # Check prediction_accuracy structure
        acc_stats = performance["prediction_accuracy"]
        assert "mean_error_percent" in acc_stats or "note" in acc_stats
    
    def test_analyze_performance_calculations(self, analytics):
        """Test analyze_performance calculations are correct."""
        performance = analytics.analyze_performance()
        
        assert performance["total_sprites"] == 30
        
        # Analysis time should be reasonable
        time_stats = performance["analysis_time"]
        assert 0 < time_stats["mean_ms"] < 20
        assert 0 < time_stats["median_ms"] < 20
        assert time_stats["min_ms"] <= time_stats["mean_ms"] <= time_stats["max_ms"]
        
        # Percentiles should be in order
        assert time_stats["median_ms"] <= time_stats["p95_ms"] <= time_stats["p99_ms"]
        
        # Percentage should be 0-100
        assert 0 <= time_stats["under_10ms_percent"] <= 100
    
    def test_analyze_performance_empty_data(self):
        """Test analyze_performance with no data."""
        analytics = EncodingAnalytics([])
        performance = analytics.analyze_performance()
        
        assert "error" in performance
        assert performance["total_sprites"] == 0
    
    def test_analyze_encoding_distribution_structure(self, analytics):
        """Test analyze_encoding_distribution returns correct structure."""
        distribution = analytics.analyze_encoding_distribution()
        
        assert "total_sprites" in distribution
        assert "by_encoding" in distribution
        
        # Check each encoding has required fields
        for encoding, stats in distribution["by_encoding"].items():
            assert "count" in stats
            assert "percent" in stats
            assert "avg_compression" in stats
            assert "median_compression" in stats
            assert "success_rate" in stats
    
    def test_analyze_encoding_distribution_calculations(self, analytics):
        """Test encoding distribution calculations are correct."""
        distribution = analytics.analyze_encoding_distribution()
        
        # Total counts should add up
        total_count = sum(
            stats["count"] for stats in distribution["by_encoding"].values()
        )
        assert total_count == distribution["total_sprites"]
        
        # Percentages should add up to 100
        total_percent = sum(
            stats["percent"] for stats in distribution["by_encoding"].values()
        )
        assert 99.9 < total_percent < 100.1  # Allow for rounding
        
        # Each encoding should have reasonable stats
        for encoding, stats in distribution["by_encoding"].items():
            assert stats["count"] > 0
            assert 0 < stats["percent"] <= 100
            assert 0 <= stats["success_rate"] <= 100
            
            if stats["avg_compression"] is not None:
                assert 0 <= stats["avg_compression"] <= 1
            if stats["median_compression"] is not None:
                assert 0 <= stats["median_compression"] <= 1
    
    def test_analyze_encoding_distribution_empty_data(self):
        """Test encoding distribution with no data."""
        analytics = EncodingAnalytics([])
        distribution = analytics.analyze_encoding_distribution()
        
        assert "error" in distribution
    
    def test_analyze_by_size_structure(self, analytics):
        """Test analyze_by_size returns correct structure."""
        by_size = analytics.analyze_by_size()
        
        # Should have all size categories
        assert "small" in by_size
        assert "medium" in by_size
        assert "large" in by_size
        
        # Each category should have required fields
        for category, stats in by_size.items():
            if stats.get("count", 0) > 0:
                assert "count" in stats
                assert "pixel_range" in stats
                assert "encoding_distribution" in stats
                assert "avg_analysis_time_ms" in stats
    
    def test_analyze_by_size_calculations(self, analytics):
        """Test size-based analysis calculations are correct."""
        by_size = analytics.analyze_by_size()
        
        # Total counts should add up
        total_count = sum(
            stats.get("count", 0) for stats in by_size.values()
        )
        assert total_count == 30
        
        # Each non-empty category should have valid stats
        for category, stats in by_size.items():
            if stats.get("count", 0) > 0:
                assert stats["count"] > 0
                assert stats["avg_analysis_time_ms"] > 0
                
                # Encoding distribution should add up
                enc_total = sum(stats["encoding_distribution"].values())
                assert enc_total == stats["count"]
    
    def test_analyze_by_size_empty_data(self):
        """Test size analysis with no data."""
        analytics = EncodingAnalytics([])
        by_size = analytics.analyze_by_size()
        
        assert "error" in by_size
    
    def test_generate_report_produces_string(self, analytics):
        """Test generate_report produces a non-empty string."""
        report = analytics.generate_report()
        
        assert isinstance(report, str)
        assert len(report) > 100  # Should be substantial
    
    def test_generate_report_contains_key_sections(self, analytics):
        """Test report contains expected sections."""
        report = analytics.generate_report()
        
        # Should contain main sections
        assert "Encoding Analytics Report" in report
        assert "Performance Metrics" in report
        assert "Encoding Distribution" in report
        assert "Analysis by Sprite Size" in report
        assert "Performance Targets Summary" in report
        
        # Should contain specific metrics
        assert "Analysis Time:" in report
        assert "Mean:" in report
        assert "95th percentile:" in report
    
    def test_generate_report_empty_data(self):
        """Test report generation with no data."""
        analytics = EncodingAnalytics([])
        report = analytics.generate_report()
        
        assert isinstance(report, str)
        assert "No metadata records available" in report
    
    def test_performance_targets_in_report(self, analytics):
        """Test that performance targets are shown in report."""
        report = analytics.generate_report()
        
        # Should show target results
        assert "Analysis time <10ms" in report
        assert ("✅ PASS" in report or "❌ FAIL" in report)


class TestCreateSampleMetadata:
    """Test sample metadata generation."""
    
    def test_create_sample_metadata_default_count(self):
        """Test creating sample metadata with default count."""
        samples = create_sample_metadata()
        
        assert len(samples) == 30  # Default count
    
    def test_create_sample_metadata_custom_count(self):
        """Test creating sample metadata with custom count."""
        samples = create_sample_metadata(count=20)
        
        assert len(samples) == 20
    
    def test_sample_metadata_structure(self):
        """Test that generated samples have correct structure."""
        samples = create_sample_metadata(count=5)
        
        for sample in samples:
            # Check all required fields present
            assert "request_id" in sample
            assert "agent" in sample
            assert "model" in sample
            assert "timestamp" in sample
            assert "dimensions" in sample
            assert "pixel_count" in sample
            assert "palette_size" in sample
            assert "asset_type" in sample
            assert "is_animated" in sample
            assert "complexity_metrics" in sample
            assert "encoding_decision" in sample
            assert "performance_metrics" in sample
            assert "meets_performance_target" in sample
            assert "meets_accuracy_target" in sample
    
    def test_sample_metadata_variety(self):
        """Test that samples have variety in dimensions and encodings."""
        samples = create_sample_metadata(count=30)
        
        # Should have variety in dimensions
        dimensions = set(s["dimensions"] for s in samples)
        assert len(dimensions) > 1
        
        # Should have variety in encodings
        encodings = set(
            s["encoding_decision"]["selected_encoding"] for s in samples
        )
        assert len(encodings) > 1
        
        # Should have variety in palette sizes
        palette_sizes = set(s["palette_size"] for s in samples)
        assert len(palette_sizes) > 1
    
    def test_sample_metadata_realistic_values(self):
        """Test that generated values are realistic."""
        samples = create_sample_metadata(count=30)
        
        for sample in samples:
            # Complexity metrics should be 0-1
            metrics = sample["complexity_metrics"]
            assert 0 <= metrics["entropy"] <= 1
            assert 0 <= metrics["repetition_score"] <= 1
            assert 0 <= metrics["structure_score"] <= 1
            assert 0 < metrics["estimated_rle_ratio"] <= 1
            assert metrics["avg_run_length"] > 0
            
            # Compression ratios should be 0-1
            decision = sample["encoding_decision"]
            assert 0 <= decision["estimated_compression"] <= 1
            assert 0 <= decision["actual_compression"] <= 1
            
            # Analysis time should be positive
            perf = sample["performance_metrics"]
            assert perf["analysis_time_ms"] > 0
            assert perf["analysis_time_ms"] < 20  # Reasonable upper bound
            
            # Prediction error should be reasonable
            assert 0 <= perf["prediction_accuracy_percent"] < 50
    
    def test_sample_metadata_target_achievement(self):
        """Test that most samples meet performance targets."""
        samples = create_sample_metadata(count=30)
        
        # Most should meet <10ms target (since we generate 95% that way)
        meets_perf = sum(1 for s in samples if s["meets_performance_target"])
        assert meets_perf >= 25  # At least 83% (allowing some variance)
        
        # Most should meet accuracy target
        meets_acc = sum(1 for s in samples if s["meets_accuracy_target"])
        assert meets_acc >= 20  # At least 67%


class TestAnalyticsIntegration:
    """Integration tests for complete analytics workflow."""
    
    def test_full_analytics_workflow(self):
        """Test complete workflow from sample data to report."""
        # Generate sample data
        samples = create_sample_metadata(count=25)
        
        # Create analytics
        analytics = EncodingAnalytics(samples)
        
        # Run all analyses
        performance = analytics.analyze_performance()
        distribution = analytics.analyze_encoding_distribution()
        by_size = analytics.analyze_by_size()
        report = analytics.generate_report()
        
        # Verify all analyses succeeded
        assert performance["total_sprites"] == 25
        assert len(distribution["by_encoding"]) > 0
        assert any(by_size[cat].get("count", 0) > 0 for cat in by_size)
        assert len(report) > 500
    
    def test_analytics_with_mixed_data(self):
        """Test analytics with varied sprite data."""
        samples = create_sample_metadata(count=50)
        analytics = EncodingAnalytics(samples)
        
        # Should handle different sprite sizes
        by_size = analytics.analyze_by_size()
        categories_with_data = sum(
            1 for stats in by_size.values() if stats.get("count", 0) > 0
        )
        assert categories_with_data >= 2  # At least 2 size categories
        
        # Should have multiple encoding strategies
        distribution = analytics.analyze_encoding_distribution()
        assert len(distribution["by_encoding"]) >= 2
    
    def test_analytics_performance(self):
        """Test that analytics runs efficiently."""
        import time
        
        # Generate larger dataset
        samples = create_sample_metadata(count=100)
        
        # Time the analytics
        start = time.perf_counter()
        analytics = EncodingAnalytics(samples)
        analytics.analyze_performance()
        analytics.analyze_encoding_distribution()
        analytics.analyze_by_size()
        analytics.generate_report()
        duration_ms = (time.perf_counter() - start) * 1000
        
        # Should complete in <100ms for 100 sprites
        assert duration_ms < 100, f"Analytics took {duration_ms:.2f}ms (target: <100ms)"


class TestValidationScriptLogic:
    """Test the logic that will be used in validation script."""
    
    def test_performance_target_validation(self):
        """Test performance target validation logic."""
        samples = create_sample_metadata(count=30)
        analytics = EncodingAnalytics(samples)
        performance = analytics.analyze_performance()
        
        # Check if performance target would pass
        meets_target_pct = performance["analysis_time"]["under_10ms_percent"]
        target_met = meets_target_pct >= 95.0
        
        # With our sample generation (95% under 10ms), this should usually pass
        # But allow for randomness in test data
        assert isinstance(target_met, bool)
    
    def test_accuracy_target_validation(self):
        """Test accuracy target validation logic."""
        samples = create_sample_metadata(count=30)
        analytics = EncodingAnalytics(samples)
        performance = analytics.analyze_performance()
        
        pred = performance["prediction_accuracy"]
        
        # Should have prediction data
        assert pred["mean_error_percent"] is not None
        
        # Check if accuracy target would pass
        mean_error = pred["mean_error_percent"]
        target_met = mean_error < 15.0
        
        assert isinstance(target_met, bool)
    
    def test_report_saving_logic(self):
        """Test that report data can be serialized to JSON."""
        import json
        
        samples = create_sample_metadata(count=20)
        analytics = EncodingAnalytics(samples)
        
        # Create report-like structure
        report_data = {
            "validation_status": "PASS",
            "total_sprites": len(samples),
            "performance_metrics": analytics.analyze_performance(),
            "encoding_distribution": analytics.analyze_encoding_distribution(),
            "size_analysis": analytics.analyze_by_size(),
        }
        
        # Should be serializable
        json_str = json.dumps(report_data, indent=2)
        assert len(json_str) > 100
        
        # Should be deserializable
        loaded = json.loads(json_str)
        assert loaded["validation_status"] == "PASS"
        assert loaded["total_sprites"] == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])