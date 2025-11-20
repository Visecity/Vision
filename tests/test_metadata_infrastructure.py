"""
Unit tests for Phase 3 metadata infrastructure.

Tests cover:
- Metadata schema validation
- MetadataCollector functionality
- Non-blocking operation
- DetailAgent metadata building
"""

import json
import pytest
import tempfile
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Any

from src.rendering.metadata_schema import (
    ComplexityMetrics,
    EncodingDecision,
    PerformanceMetrics,
    SpriteMetadata,
)
from src.rendering.metadata_collector import MetadataCollector


class TestMetadataSchema:
    """Test metadata schema TypedDict definitions."""
    
    def test_complexity_metrics_structure(self):
        """Test ComplexityMetrics has required fields."""
        metrics: ComplexityMetrics = {
            "unique_colors": 8,
            "entropy": 0.65,
            "repetition_score": 0.42,
            "structure_score": 0.78,
            "estimated_rle_ratio": 0.35,
            "avg_run_length": 2.8,
        }
        
        assert metrics["unique_colors"] == 8
        assert metrics["entropy"] == 0.65
        assert metrics["repetition_score"] == 0.42
        assert metrics["structure_score"] == 0.78
        assert metrics["estimated_rle_ratio"] == 0.35
        assert metrics["avg_run_length"] == 2.8
    
    def test_encoding_decision_structure(self):
        """Test EncodingDecision has required fields."""
        decision: EncodingDecision = {
            "recommended_encoding": "palette_indexed_rle",
            "selected_encoding": "palette_indexed_rle",
            "reasons": ["Small palette (8 colors)", "Large sprite (512 pixels)"],
            "estimated_compression": 0.25,
            "actual_compression": 0.22,
        }
        
        assert decision["recommended_encoding"] == "palette_indexed_rle"
        assert decision["selected_encoding"] == "palette_indexed_rle"
        assert len(decision["reasons"]) == 2
        assert decision["estimated_compression"] == 0.25
        assert decision["actual_compression"] == 0.22
    
    def test_performance_metrics_structure(self):
        """Test PerformanceMetrics has required fields."""
        perf: PerformanceMetrics = {
            "analysis_time_ms": 5.2,
            "prediction_accuracy_percent": 12.5,
        }
        
        assert perf["analysis_time_ms"] == 5.2
        assert perf["prediction_accuracy_percent"] == 12.5
    
    def test_sprite_metadata_structure(self):
        """Test complete SpriteMetadata structure."""
        metadata: SpriteMetadata = {
            "request_id": "test-123",
            "agent": "detail",
            "model": "claude-3-5-sonnet-20241022",
            "timestamp": "2025-11-20T02:00:00.000Z",
            "dimensions": "16x16",
            "pixel_count": 256,
            "palette_size": 8,
            "asset_type": "sprite",
            "is_animated": False,
            "complexity_metrics": {
                "unique_colors": 8,
                "entropy": 0.65,
                "repetition_score": 0.42,
                "structure_score": 0.78,
                "estimated_rle_ratio": 0.35,
                "avg_run_length": 2.8,
            },
            "encoding_decision": {
                "recommended_encoding": "palette_indexed_rle",
                "selected_encoding": "palette_indexed_rle",
                "reasons": ["Test reason"],
                "estimated_compression": 0.25,
                "actual_compression": 0.22,
            },
            "performance_metrics": {
                "analysis_time_ms": 5.2,
                "prediction_accuracy_percent": 12.5,
            },
            "meets_performance_target": True,
            "meets_accuracy_target": True,
        }
        
        assert metadata["request_id"] == "test-123"
        assert metadata["agent"] == "detail"
        assert metadata["pixel_count"] == 256
        assert metadata["meets_performance_target"] is True


class TestMetadataCollector:
    """Test MetadataCollector service functionality."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def collector(self, temp_storage):
        """Create MetadataCollector with temporary storage."""
        # Clear singleton instance for testing
        MetadataCollector._instance = None
        return MetadataCollector(storage_dir=temp_storage)
    
    @pytest.fixture
    def sample_metadata(self) -> SpriteMetadata:
        """Create sample metadata for testing."""
        return {
            "request_id": "test-abc123",
            "agent": "detail",
            "model": "claude-3-5-sonnet-20241022",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "dimensions": "16x16",
            "pixel_count": 256,
            "palette_size": 8,
            "asset_type": "sprite",
            "is_animated": False,
            "complexity_metrics": {
                "unique_colors": 8,
                "entropy": 0.65,
                "repetition_score": 0.42,
                "structure_score": 0.78,
                "estimated_rle_ratio": 0.35,
                "avg_run_length": 2.8,
            },
            "encoding_decision": {
                "recommended_encoding": "palette_indexed_rle",
                "selected_encoding": "palette_indexed_rle",
                "reasons": ["Test reason"],
                "estimated_compression": 0.25,
                "actual_compression": 0.22,
            },
            "performance_metrics": {
                "analysis_time_ms": 5.2,
                "prediction_accuracy_percent": 12.5,
            },
            "meets_performance_target": True,
            "meets_accuracy_target": True,
        }
    
    def test_collector_initialization(self, temp_storage):
        """Test MetadataCollector initialization creates storage directory."""
        MetadataCollector._instance = None
        collector = MetadataCollector(storage_dir=temp_storage)
        
        assert Path(temp_storage).exists()
        assert Path(temp_storage).is_dir()
    
    def test_collect_metadata(self, collector, sample_metadata):
        """Test metadata collection stores file correctly."""
        collector.collect(sample_metadata)
        
        # Check file was created
        files = list(Path(collector.storage_dir).glob("*.json"))
        assert len(files) == 1
        
        # Verify content
        with open(files[0], "r") as f:
            stored_metadata = json.load(f)
        
        assert stored_metadata["request_id"] == sample_metadata["request_id"]
        assert stored_metadata["agent"] == sample_metadata["agent"]
    
    def test_get_all_metadata(self, collector, sample_metadata):
        """Test retrieving all collected metadata."""
        # Collect multiple metadata entries
        for i in range(3):
            metadata = sample_metadata.copy()
            metadata["request_id"] = f"test-{i}"
            metadata["timestamp"] = datetime.utcnow().isoformat() + "Z"
            time.sleep(0.01)  # Ensure different timestamps
            collector.collect(metadata)
        
        # Retrieve all
        all_metadata = collector.get_all()
        
        assert len(all_metadata) == 3
        # Should be sorted by timestamp (newest first)
        assert all_metadata[0]["request_id"] == "test-2"
    
    def test_clear_metadata(self, collector, sample_metadata):
        """Test clearing all metadata."""
        # Collect some metadata
        for i in range(3):
            metadata = sample_metadata.copy()
            metadata["request_id"] = f"test-{i}"
            collector.collect(metadata)
        
        # Clear
        deleted_count = collector.clear()
        
        assert deleted_count == 3
        assert collector.get_count() == 0
    
    def test_get_count(self, collector, sample_metadata):
        """Test getting metadata count."""
        assert collector.get_count() == 0
        
        collector.collect(sample_metadata)
        assert collector.get_count() == 1
        
        collector.collect(sample_metadata)
        assert collector.get_count() == 2
    
    def test_get_summary(self, collector, sample_metadata):
        """Test getting summary statistics."""
        # Empty summary
        summary = collector.get_summary()
        assert summary["total_records"] == 0
        
        # Collect metadata with different encodings
        metadata1 = sample_metadata.copy()
        metadata1["encoding_decision"]["selected_encoding"] = "palette_indexed_rle"
        collector.collect(metadata1)
        
        metadata2 = sample_metadata.copy()
        metadata2["encoding_decision"]["selected_encoding"] = "rle"
        collector.collect(metadata2)
        
        # Get summary
        summary = collector.get_summary()
        
        assert summary["total_records"] == 2
        assert summary["encoding_distribution"]["palette_indexed_rle"] == 1
        assert summary["encoding_distribution"]["rle"] == 1
        assert summary["avg_analysis_time_ms"] == 5.2
    
    def test_non_blocking_collection(self, collector, sample_metadata):
        """Test that metadata collection doesn't raise exceptions."""
        # Test with invalid metadata (missing fields)
        invalid_metadata: dict[str, Any] = {"request_id": "test"}
        
        # Should not raise exception
        collector.collect(invalid_metadata)  # type: ignore
        
        # Should still work with valid metadata
        collector.collect(sample_metadata)
        assert collector.get_count() == 1  # Only valid one stored
    
    def test_thread_safety(self, collector, sample_metadata):
        """Test concurrent metadata collection is thread-safe."""
        def collect_metadata(collector, metadata, thread_id):
            for i in range(5):
                meta = metadata.copy()
                meta["request_id"] = f"thread-{thread_id}-{i}"
                collector.collect(meta)
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(
                target=collect_metadata,
                args=(collector, sample_metadata, i)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Should have collected all metadata
        assert collector.get_count() == 15  # 3 threads × 5 entries
    
    def test_singleton_pattern(self, temp_storage):
        """Test MetadataCollector uses singleton pattern."""
        MetadataCollector._instance = None
        
        collector1 = MetadataCollector(storage_dir=temp_storage)
        collector2 = MetadataCollector(storage_dir="different_dir")
        
        assert collector1 is collector2
        # Should use same storage dir (first initialization)
        assert collector1.storage_dir == collector2.storage_dir


class TestMetadataPerformance:
    """Test metadata collection performance."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def collector(self, temp_storage):
        """Create MetadataCollector with temporary storage."""
        MetadataCollector._instance = None
        return MetadataCollector(storage_dir=temp_storage)
    
    @pytest.fixture
    def sample_metadata(self) -> SpriteMetadata:
        """Create sample metadata for testing."""
        return {
            "request_id": "perf-test",
            "agent": "detail",
            "model": "claude-3-5-sonnet-20241022",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "dimensions": "16x16",
            "pixel_count": 256,
            "palette_size": 8,
            "asset_type": "sprite",
            "is_animated": False,
            "complexity_metrics": {
                "unique_colors": 8,
                "entropy": 0.65,
                "repetition_score": 0.42,
                "structure_score": 0.78,
                "estimated_rle_ratio": 0.35,
                "avg_run_length": 2.8,
            },
            "encoding_decision": {
                "recommended_encoding": "palette_indexed_rle",
                "selected_encoding": "palette_indexed_rle",
                "reasons": ["Performance test"],
                "estimated_compression": 0.25,
                "actual_compression": None,
            },
            "performance_metrics": {
                "analysis_time_ms": 5.0,
                "prediction_accuracy_percent": None,
            },
            "meets_performance_target": True,
            "meets_accuracy_target": None,
        }
    
    def test_collection_overhead_under_1ms(self, collector, sample_metadata):
        """Test that metadata collection overhead is < 1ms."""
        # Warm up
        collector.collect(sample_metadata)
        
        # Measure collection time
        start = time.perf_counter()
        collector.collect(sample_metadata)
        duration_ms = (time.perf_counter() - start) * 1000
        
        # Should be very fast (< 1ms for file write)
        assert duration_ms < 1.0, f"Collection took {duration_ms:.2f}ms (target: <1ms)"


class TestDetailAgentMetadataIntegration:
    """Test DetailAgent metadata building (integration with actual agent tested separately)."""
    
    def test_metadata_has_all_required_fields(self):
        """Test that metadata structure matches schema requirements."""
        # This is a structural test - actual integration with DetailAgent
        # is tested in test_adaptive_encoding.py
        
        required_fields = [
            "request_id",
            "agent",
            "model",
            "timestamp",
            "dimensions",
            "pixel_count",
            "palette_size",
            "asset_type",
            "is_animated",
            "complexity_metrics",
            "encoding_decision",
            "performance_metrics",
            "meets_performance_target",
            "meets_accuracy_target",
        ]
        
        # Verify all fields are in SpriteMetadata TypedDict annotations
        from typing import get_type_hints
        hints = get_type_hints(SpriteMetadata)
        
        for field in required_fields:
            assert field in hints, f"Missing required field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])