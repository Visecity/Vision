"""
Analytics module for adaptive threshold monitoring in Phase 3.

This module provides comprehensive analysis of encoding decisions, performance
metrics, and compression effectiveness based on collected sprite metadata.

Example:
    >>> from src.rendering.metadata_collector import MetadataCollector
    >>> from src.rendering.analytics import EncodingAnalytics
    >>> 
    >>> collector = MetadataCollector()
    >>> analytics = EncodingAnalytics(collector.get_all())
    >>> report = analytics.generate_report()
    >>> print(report)
"""

import statistics
from typing import Any, Optional
from collections import defaultdict

from src.rendering.metadata_schema import SpriteMetadata


class EncodingAnalytics:
    """
    Analyze adaptive threshold performance and encoding effectiveness.
    
    This class provides comprehensive analytics on:
    - Overall performance metrics (analysis time, prediction accuracy)
    - Encoding strategy distribution and effectiveness
    - Size-based analysis patterns
    - Formatted reporting for monitoring
    
    Attributes:
        records: List of sprite metadata records to analyze
    """
    
    def __init__(self, metadata_records: list[SpriteMetadata]):
        """
        Initialize analytics with collected metadata.
        
        Args:
            metadata_records: List of SpriteMetadata from MetadataCollector
        """
        self.records = metadata_records
    
    def analyze_performance(self) -> dict[str, Any]:
        """
        Analyze overall system performance metrics.
        
        Evaluates:
        - Analysis time statistics (mean, median, p95, p99)
        - Prediction accuracy statistics
        - Performance target achievement rates
        
        Returns:
            Dictionary containing:
            - total_sprites: Total number of sprites analyzed
            - analysis_time: Statistics on analysis duration
            - prediction_accuracy: Statistics on compression prediction errors
            
        Example:
            >>> analytics = EncodingAnalytics(records)
            >>> perf = analytics.analyze_performance()
            >>> print(f"Mean time: {perf['analysis_time']['mean_ms']:.2f}ms")
        """
        if not self.records:
            return {
                "error": "No metadata records available",
                "total_sprites": 0,
            }
        
        # Collect analysis times
        analysis_times = [
            r["performance_metrics"]["analysis_time_ms"]
            for r in self.records
        ]
        
        # Collect prediction errors (where available)
        prediction_errors = [
            r["performance_metrics"]["prediction_accuracy_percent"]
            for r in self.records
            if r["performance_metrics"]["prediction_accuracy_percent"] is not None
        ]
        
        # Calculate percentiles for analysis time
        sorted_times = sorted(analysis_times)
        n = len(sorted_times)
        p95_idx = int(n * 0.95)
        p99_idx = int(n * 0.99)
        
        analysis_stats = {
            "mean_ms": statistics.mean(analysis_times),
            "median_ms": statistics.median(analysis_times),
            "p95_ms": sorted_times[p95_idx] if n > 0 else 0,
            "p99_ms": sorted_times[p99_idx] if n > 0 else 0,
            "min_ms": min(analysis_times),
            "max_ms": max(analysis_times),
            "under_10ms_count": sum(1 for t in analysis_times if t < 10.0),
            "under_10ms_percent": (sum(1 for t in analysis_times if t < 10.0) / len(analysis_times) * 100),
        }
        
        # Calculate prediction accuracy stats
        if prediction_errors:
            accuracy_stats = {
                "mean_error_percent": statistics.mean(prediction_errors),
                "median_error_percent": statistics.median(prediction_errors),
                "min_error_percent": min(prediction_errors),
                "max_error_percent": max(prediction_errors),
                "under_15_percent_count": sum(1 for e in prediction_errors if e < 15.0),
                "under_15_percent_rate": (sum(1 for e in prediction_errors if e < 15.0) / len(prediction_errors) * 100),
                "total_with_actuals": len(prediction_errors),
            }
        else:
            accuracy_stats = {
                "mean_error_percent": None,
                "median_error_percent": None,
                "total_with_actuals": 0,
                "note": "No actual compression data available for accuracy calculation",
            }
        
        return {
            "total_sprites": len(self.records),
            "analysis_time": analysis_stats,
            "prediction_accuracy": accuracy_stats,
        }
    
    def analyze_encoding_distribution(self) -> dict[str, Any]:
        """
        Analyze encoding strategy usage and effectiveness.
        
        Provides breakdown of:
        - Count and percentage by encoding type
        - Success rate by encoding
        - Average compression ratio by encoding
        
        Returns:
            Dictionary with encoding distribution statistics
            
        Example:
            >>> analytics = EncodingAnalytics(records)
            >>> dist = analytics.analyze_encoding_distribution()
            >>> for enc, stats in dist['by_encoding'].items():
            ...     print(f"{enc}: {stats['count']} sprites ({stats['percent']:.1f}%)")
        """
        if not self.records:
            return {"error": "No metadata records available"}
        
        encoding_counts: dict[str, int] = defaultdict(int)
        encoding_compressions: dict[str, list[float]] = defaultdict(list)
        encoding_success: dict[str, int] = defaultdict(int)
        
        for record in self.records:
            enc = record["encoding_decision"]["selected_encoding"]
            encoding_counts[enc] += 1
            
            # Track actual compression ratios
            actual = record["encoding_decision"].get("actual_compression")
            if actual is not None:
                encoding_compressions[enc].append(actual)
                
                # Count as success if compression < 0.5 (50%+ reduction)
                if actual < 0.5:
                    encoding_success[enc] += 1
        
        total = len(self.records)
        
        result = {
            "total_sprites": total,
            "by_encoding": {},
        }
        
        for encoding in encoding_counts:
            count = encoding_counts[encoding]
            compressions = encoding_compressions[encoding]
            
            result["by_encoding"][encoding] = {
                "count": count,
                "percent": (count / total * 100),
                "avg_compression": statistics.mean(compressions) if compressions else None,
                "median_compression": statistics.median(compressions) if compressions else None,
                "success_rate": (encoding_success[encoding] / count * 100) if count > 0 else 0,
            }
        
        return result
    
    def analyze_by_size(self) -> dict[str, Any]:
        """
        Analyze performance by sprite size categories.
        
        Categorizes sprites as:
        - small: ≤256 pixels (e.g., 16×16)
        - medium: 257-1024 pixels (e.g., 32×32)
        - large: >1024 pixels (e.g., 64×64+)
        
        Returns:
            Dictionary with size-based analysis including:
            - Count per category
            - Encoding preferences by size
            - Average compression ratios by size
            
        Example:
            >>> analytics = EncodingAnalytics(records)
            >>> sizes = analytics.analyze_by_size()
            >>> for cat, stats in sizes.items():
            ...     print(f"{cat}: {stats['count']} sprites")
        """
        if not self.records:
            return {"error": "No metadata records available"}
        
        size_categories: dict[str, list[SpriteMetadata]] = {
            "small": [],      # ≤256 pixels
            "medium": [],     # 257-1024 pixels
            "large": [],      # >1024 pixels
        }
        
        for record in self.records:
            pixel_count = record["pixel_count"]
            if pixel_count <= 256:
                category = "small"
            elif pixel_count <= 1024:
                category = "medium"
            else:
                category = "large"
            size_categories[category].append(record)
        
        result = {}
        
        for category, records in size_categories.items():
            if not records:
                result[category] = {
                    "count": 0,
                    "note": "No sprites in this size category",
                }
                continue
            
            # Count encoding preferences
            encoding_counts: dict[str, int] = defaultdict(int)
            compressions: list[float] = []
            analysis_times: list[float] = []
            
            for record in records:
                enc = record["encoding_decision"]["selected_encoding"]
                encoding_counts[enc] += 1
                
                actual = record["encoding_decision"].get("actual_compression")
                if actual is not None:
                    compressions.append(actual)
                
                analysis_times.append(record["performance_metrics"]["analysis_time_ms"])
            
            result[category] = {
                "count": len(records),
                "pixel_range": self._get_pixel_range(category),
                "encoding_distribution": dict(encoding_counts),
                "avg_compression": statistics.mean(compressions) if compressions else None,
                "avg_analysis_time_ms": statistics.mean(analysis_times),
            }
        
        return result
    
    def _get_pixel_range(self, category: str) -> str:
        """Get human-readable pixel range for a size category."""
        ranges = {
            "small": "≤256 pixels (e.g., 16×16)",
            "medium": "257-1024 pixels (e.g., 32×32)",
            "large": ">1024 pixels (e.g., 64×64+)",
        }
        return ranges.get(category, "unknown")
    
    def generate_report(self) -> str:
        """
        Generate formatted text report combining all analyses.
        
        Creates a comprehensive human-readable report including:
        - Overall performance summary
        - Encoding distribution breakdown
        - Size-based analysis
        - Target achievement status
        
        Returns:
            Formatted multi-line string report
            
        Example:
            >>> analytics = EncodingAnalytics(records)
            >>> print(analytics.generate_report())
            ====== Encoding Analytics Report ======
            Total sprites analyzed: 50
            ...
        """
        if not self.records:
            return "No metadata records available for analysis."
        
        performance = self.analyze_performance()
        distribution = self.analyze_encoding_distribution()
        by_size = self.analyze_by_size()
        
        lines = [
            "=" * 60,
            "Encoding Analytics Report",
            "=" * 60,
            "",
            f"Total sprites analyzed: {performance['total_sprites']}",
            "",
            "--- Performance Metrics ---",
            "",
            "Analysis Time:",
            f"  Mean: {performance['analysis_time']['mean_ms']:.2f}ms",
            f"  Median: {performance['analysis_time']['median_ms']:.2f}ms",
            f"  95th percentile: {performance['analysis_time']['p95_ms']:.2f}ms",
            f"  99th percentile: {performance['analysis_time']['p99_ms']:.2f}ms",
            f"  Range: {performance['analysis_time']['min_ms']:.2f}ms - {performance['analysis_time']['max_ms']:.2f}ms",
            f"  Meeting <10ms target: {performance['analysis_time']['under_10ms_count']}/{performance['total_sprites']} ({performance['analysis_time']['under_10ms_percent']:.1f}%)",
            "",
        ]
        
        # Add prediction accuracy if available
        pred = performance['prediction_accuracy']
        if pred.get('mean_error_percent') is not None:
            lines.extend([
                "Prediction Accuracy:",
                f"  Mean error: {pred['mean_error_percent']:.2f}%",
                f"  Median error: {pred['median_error_percent']:.2f}%",
                f"  Range: {pred['min_error_percent']:.2f}% - {pred['max_error_percent']:.2f}%",
                f"  Meeting <15% target: {pred['under_15_percent_count']}/{pred['total_with_actuals']} ({pred['under_15_percent_rate']:.1f}%)",
                "",
            ])
        else:
            lines.extend([
                "Prediction Accuracy: No actual compression data available yet",
                "",
            ])
        
        # Encoding distribution
        lines.extend([
            "--- Encoding Distribution ---",
            "",
        ])
        
        for encoding, stats in distribution['by_encoding'].items():
            lines.append(f"{encoding}:")
            lines.append(f"  Count: {stats['count']} ({stats['percent']:.1f}%)")
            if stats['avg_compression'] is not None:
                lines.append(f"  Avg compression: {stats['avg_compression']:.3f}")
                lines.append(f"  Median compression: {stats['median_compression']:.3f}")
            lines.append(f"  Success rate: {stats['success_rate']:.1f}%")
            lines.append("")
        
        # Size-based analysis
        lines.extend([
            "--- Analysis by Sprite Size ---",
            "",
        ])
        
        for category in ["small", "medium", "large"]:
            stats = by_size.get(category, {})
            if stats.get("count", 0) == 0:
                continue
            
            lines.append(f"{category.capitalize()} sprites ({stats['pixel_range']}):")
            lines.append(f"  Count: {stats['count']}")
            lines.append(f"  Avg analysis time: {stats['avg_analysis_time_ms']:.2f}ms")
            if stats['avg_compression'] is not None:
                lines.append(f"  Avg compression: {stats['avg_compression']:.3f}")
            lines.append("  Encoding preferences:")
            for enc, count in stats['encoding_distribution'].items():
                lines.append(f"    {enc}: {count}")
            lines.append("")
        
        # Performance targets summary
        lines.extend([
            "=" * 60,
            "Performance Targets Summary",
            "=" * 60,
            "",
        ])
        
        # Check analysis time target
        time_target_met = performance['analysis_time']['under_10ms_percent'] >= 95
        time_status = "✅ PASS" if time_target_met else "❌ FAIL"
        lines.append(f"Analysis time <10ms (target: >95%): {time_status}")
        lines.append(f"  Actual: {performance['analysis_time']['under_10ms_percent']:.1f}%")
        lines.append("")
        
        # Check prediction accuracy target
        if pred.get('under_15_percent_rate') is not None:
            acc_target_met = pred['under_15_percent_rate'] >= 85
            acc_status = "✅ PASS" if acc_target_met else "❌ FAIL"
            lines.append(f"Prediction error <15% (target: >85%): {acc_status}")
            lines.append(f"  Actual: {pred['under_15_percent_rate']:.1f}%")
        else:
            lines.append("Prediction accuracy: ⚠️  No data available yet")
        
        lines.extend([
            "",
            "=" * 60,
        ])
        
        return "\n".join(lines)


def create_sample_metadata(count: int = 30) -> list[SpriteMetadata]:
    """
    Generate sample sprite metadata for testing analytics.
    
    Creates realistic sample data covering:
    - Various sprite sizes (small, medium, large)
    - Different encoding strategies
    - Range of complexities and compression ratios
    - Some prediction errors for accuracy testing
    
    Args:
        count: Number of sample metadata records to generate (default: 30)
        
    Returns:
        List of SpriteMetadata samples
        
    Example:
        >>> samples = create_sample_metadata(20)
        >>> analytics = EncodingAnalytics(samples)
        >>> print(analytics.generate_report())
    """
    import random
    from datetime import datetime, timedelta
    
    samples: list[SpriteMetadata] = []
    base_time = datetime.utcnow()
    
    # Define sprite configurations
    sprite_configs = [
        # Small sprites (16×16 = 256 pixels)
        {"dimensions": "16x16", "pixel_count": 256, "palette_size": 8, "encoding": "palette_indexed_rle"},
        {"dimensions": "16x16", "pixel_count": 256, "palette_size": 12, "encoding": "palette_indexed_rle"},
        {"dimensions": "16x16", "pixel_count": 256, "palette_size": 4, "encoding": "standard"},
        
        # Medium sprites (32×32 = 1024 pixels)
        {"dimensions": "32x32", "pixel_count": 1024, "palette_size": 14, "encoding": "palette_indexed_rle"},
        {"dimensions": "32x32", "pixel_count": 1024, "palette_size": 20, "encoding": "rle"},
        {"dimensions": "24x24", "pixel_count": 576, "palette_size": 10, "encoding": "palette_indexed_rle"},
        
        # Large sprites (48×48 = 2304 pixels)
        {"dimensions": "48x48", "pixel_count": 2304, "palette_size": 16, "encoding": "rle"},
        {"dimensions": "64x32", "pixel_count": 2048, "palette_size": 18, "encoding": "rle"},
    ]
    
    for i in range(count):
        config = random.choice(sprite_configs)
        encoding = config["encoding"]
        
        # Generate complexity metrics
        if encoding == "palette_indexed_rle":
            entropy = random.uniform(0.4, 0.7)
            repetition = random.uniform(0.6, 0.9)
            structure = random.uniform(0.6, 0.9)
            rle_ratio = random.uniform(0.2, 0.4)
        elif encoding == "rle":
            entropy = random.uniform(0.5, 0.8)
            repetition = random.uniform(0.5, 0.8)
            structure = random.uniform(0.4, 0.7)
            rle_ratio = random.uniform(0.3, 0.5)
        else:  # standard
            entropy = random.uniform(0.7, 0.95)
            repetition = random.uniform(0.1, 0.4)
            structure = random.uniform(0.3, 0.6)
            rle_ratio = random.uniform(0.6, 0.9)
        
        # Estimated compression
        estimated = rle_ratio * (1 - random.uniform(0, 0.15))
        
        # Actual compression (with some prediction error)
        error_factor = random.uniform(0.85, 1.15)  # ±15% error
        actual = estimated * error_factor
        
        # Calculate prediction accuracy
        pred_error = abs(estimated - actual) / actual * 100 if actual > 0 else 0
        
        # Analysis time (mostly under 10ms, some over for testing)
        if random.random() < 0.95:
            analysis_time = random.uniform(3.0, 9.5)
        else:
            analysis_time = random.uniform(10.0, 15.0)
        
        # Create timestamp with small increments
        timestamp = (base_time + timedelta(seconds=i * 10)).isoformat() + "Z"
        
        metadata: SpriteMetadata = {
            "request_id": f"sample-{i:03d}",
            "agent": "detail",
            "model": "claude-3-5-sonnet-20241022",
            "timestamp": timestamp,
            "dimensions": config["dimensions"],
            "pixel_count": config["pixel_count"],
            "palette_size": config["palette_size"],
            "asset_type": random.choice(["sprite", "icon", "character"]),
            "is_animated": random.random() < 0.2,
            "complexity_metrics": {
                "unique_colors": config["palette_size"],
                "entropy": round(entropy, 3),
                "repetition_score": round(repetition, 3),
                "structure_score": round(structure, 3),
                "estimated_rle_ratio": round(rle_ratio, 3),
                "avg_run_length": round(1 / rle_ratio if rle_ratio > 0 else 1, 2),
            },
            "encoding_decision": {
                "recommended_encoding": encoding,
                "selected_encoding": encoding,
                "reasons": [f"Test reason for {encoding}"],
                "estimated_compression": round(estimated, 3),
                "actual_compression": round(actual, 3),
            },
            "performance_metrics": {
                "analysis_time_ms": round(analysis_time, 2),
                "prediction_accuracy_percent": round(pred_error, 2),
            },
            "meets_performance_target": analysis_time < 10.0,
            "meets_accuracy_target": pred_error < 15.0,
        }
        
        samples.append(metadata)
    
    return samples