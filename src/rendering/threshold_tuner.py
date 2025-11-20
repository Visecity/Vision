"""
Threshold tuning module for adaptive encoding optimization.

This module provides intelligent threshold analysis to optimize encoding decisions
based on collected sprite generation metadata. It analyzes success rates at different
threshold values and recommends optimal settings for palette indexing and RLE encoding.

Example:
    >>> from src.rendering.metadata_collector import MetadataCollector
    >>> from src.rendering.threshold_tuner import ThresholdTuner
    >>> 
    >>> collector = MetadataCollector()
    >>> tuner = ThresholdTuner(collector.get_all())
    >>> recommendations = tuner.generate_recommendations()
    >>> print(recommendations)
"""

import statistics
from typing import Any, Optional
from collections import defaultdict

from src.rendering.metadata_schema import SpriteMetadata


class ThresholdTuner:
    """
    Analyze and tune adaptive threshold parameters based on collected data.
    
    This class analyzes collected sprite metadata to determine optimal threshold
    values for encoding strategy selection. It evaluates success rates at different
    threshold values and recommends adjustments for:
    
    - Palette indexing thresholds (palette_size, pixel_count)
    - RLE encoding thresholds (pixel_count, estimated_rle_ratio)
    
    Attributes:
        metadata_list: List of sprite metadata records to analyze
        min_sample_size: Minimum samples required for confident recommendations
    
    Example:
        >>> tuner = ThresholdTuner(metadata_records, min_sample_size=20)
        >>> palette_analysis = tuner.analyze_palette_indexing()
        >>> rle_analysis = tuner.analyze_rle_encoding()
        >>> recommendations = tuner.generate_recommendations()
    """
    
    def __init__(
        self,
        metadata_list: list[SpriteMetadata],
        min_sample_size: int = 20
    ):
        """
        Initialize threshold tuner with collected metadata.
        
        Args:
            metadata_list: List of SpriteMetadata from MetadataCollector
            min_sample_size: Minimum samples required for recommendations (default: 20)
        """
        self.metadata_list = metadata_list
        self.min_sample_size = min_sample_size
    
    def analyze_palette_indexing(self) -> dict[str, Any]:
        """
        Analyze optimal thresholds for palette indexing decisions.
        
        Current thresholds:
        - palette_size ≤ 16
        - pixel_count > 128
        
        This method analyzes actual compression success rates at different
        threshold values to find the sweet spot that maximizes correct decisions.
        
        Returns:
            Dictionary containing:
            - current_thresholds: Current palette indexing thresholds
            - palette_size_analysis: Success rates by palette size
            - pixel_count_analysis: Success rates by pixel count
            - optimal_thresholds: Recommended threshold values
            - confidence: Confidence level based on sample size
            - recommendation: Human-readable recommendation text
            
        Example:
            >>> tuner = ThresholdTuner(records)
            >>> analysis = tuner.analyze_palette_indexing()
            >>> print(f"Optimal palette size: {analysis['optimal_thresholds']['palette_size']}")
        """
        # Find sprites that used palette indexing
        palette_indexed = [
            r for r in self.metadata_list
            if r["encoding_decision"]["selected_encoding"] == "palette_indexed_rle"
        ]
        
        if len(palette_indexed) < self.min_sample_size:
            return {
                "error": f"Insufficient data: {len(palette_indexed)} palette indexed sprites (minimum: {self.min_sample_size})",
                "current_thresholds": {
                    "palette_size": 16,
                    "pixel_count": 128
                },
                "confidence": "insufficient_data",
            }
        
        # Analyze compression success by palette size
        compressions_by_palette: dict[int, list[float]] = defaultdict(list)
        for record in palette_indexed:
            palette_size = record["palette_size"]
            actual = record["encoding_decision"].get("actual_compression")
            if actual is not None:
                compressions_by_palette[palette_size].append(actual)
        
        # Calculate average compression by palette size
        palette_analysis = {}
        for size in sorted(compressions_by_palette.keys()):
            ratios = compressions_by_palette[size]
            # Success = compression ratio < 0.5 (50%+ reduction)
            success_count = sum(1 for r in ratios if r < 0.5)
            palette_analysis[size] = {
                "count": len(ratios),
                "avg_compression": statistics.mean(ratios),
                "success_rate": (success_count / len(ratios) * 100) if ratios else 0,
            }
        
        # Analyze by pixel count (bucketed)
        compressions_by_pixels: dict[int, list[float]] = defaultdict(list)
        for record in palette_indexed:
            pixel_count = record["pixel_count"]
            bucket = (pixel_count // 64) * 64  # 64-pixel buckets
            actual = record["encoding_decision"].get("actual_compression")
            if actual is not None:
                compressions_by_pixels[bucket].append(actual)
        
        # Calculate success rates by pixel count bucket
        pixel_analysis = {}
        for bucket in sorted(compressions_by_pixels.keys()):
            ratios = compressions_by_pixels[bucket]
            success_count = sum(1 for r in ratios if r < 0.5)
            pixel_analysis[bucket] = {
                "count": len(ratios),
                "avg_compression": statistics.mean(ratios),
                "success_rate": (success_count / len(ratios) * 100) if ratios else 0,
            }
        
        # Determine optimal thresholds
        optimal_palette_size = self._find_optimal_palette_threshold(palette_analysis)
        optimal_pixel_count = self._find_optimal_pixel_threshold(pixel_analysis)
        
        # Generate recommendation
        recommendation = self._generate_palette_recommendation(
            optimal_palette_size,
            optimal_pixel_count,
            len(palette_indexed)
        )
        
        # Calculate confidence based on sample size
        confidence = self._calculate_confidence(len(palette_indexed))
        
        return {
            "current_thresholds": {
                "palette_size": 16,
                "pixel_count": 128
            },
            "palette_size_analysis": palette_analysis,
            "pixel_count_analysis": pixel_analysis,
            "optimal_thresholds": {
                "palette_size": optimal_palette_size,
                "pixel_count": optimal_pixel_count
            },
            "sample_size": len(palette_indexed),
            "confidence": confidence,
            "recommendation": recommendation,
        }
    
    def analyze_rle_encoding(self) -> dict[str, Any]:
        """
        Analyze optimal thresholds for RLE encoding decisions.
        
        Current thresholds:
        - pixel_count > 256 OR
        - estimated_rle_ratio < 0.4
        
        This method analyzes actual compression success rates to find optimal
        threshold values that maximize compression effectiveness.
        
        Returns:
            Dictionary containing:
            - current_thresholds: Current RLE encoding thresholds
            - rle_ratio_analysis: Success rates by RLE ratio
            - pixel_count_analysis: Success rates by pixel count
            - optimal_thresholds: Recommended threshold values
            - confidence: Confidence level based on sample size
            - recommendation: Human-readable recommendation text
            
        Example:
            >>> tuner = ThresholdTuner(records)
            >>> analysis = tuner.analyze_rle_encoding()
            >>> print(f"Optimal RLE ratio: {analysis['optimal_thresholds']['rle_ratio']}")
        """
        # Find sprites that used RLE encoding
        rle_encoded = [
            r for r in self.metadata_list
            if r["encoding_decision"]["selected_encoding"] == "rle"
        ]
        
        if len(rle_encoded) < self.min_sample_size:
            return {
                "error": f"Insufficient data: {len(rle_encoded)} RLE sprites (minimum: {self.min_sample_size})",
                "current_thresholds": {
                    "pixel_count": 256,
                    "rle_ratio": 0.4
                },
                "confidence": "insufficient_data",
            }
        
        # Analyze by estimated RLE ratio (bucketed to 0.1 increments)
        compressions_by_ratio: dict[float, list[float]] = defaultdict(list)
        for record in rle_encoded:
            ratio = record["complexity_metrics"]["estimated_rle_ratio"]
            bucket = round(ratio, 1)  # Round to 0.1
            actual = record["encoding_decision"].get("actual_compression")
            if actual is not None:
                compressions_by_ratio[bucket].append(actual)
        
        # Calculate success rates by RLE ratio
        ratio_analysis = {}
        for bucket in sorted(compressions_by_ratio.keys()):
            ratios = compressions_by_ratio[bucket]
            success_count = sum(1 for r in ratios if r < 0.7)  # RLE success = <70% ratio
            ratio_analysis[bucket] = {
                "count": len(ratios),
                "avg_compression": statistics.mean(ratios),
                "success_rate": (success_count / len(ratios) * 100) if ratios else 0,
            }
        
        # Analyze by pixel count (128-pixel buckets)
        compressions_by_pixels: dict[int, list[float]] = defaultdict(list)
        for record in rle_encoded:
            pixel_count = record["pixel_count"]
            bucket = (pixel_count // 128) * 128
            actual = record["encoding_decision"].get("actual_compression")
            if actual is not None:
                compressions_by_pixels[bucket].append(actual)
        
        # Calculate success rates by pixel count
        pixel_analysis = {}
        for bucket in sorted(compressions_by_pixels.keys()):
            ratios = compressions_by_pixels[bucket]
            success_count = sum(1 for r in ratios if r < 0.7)
            pixel_analysis[bucket] = {
                "count": len(ratios),
                "avg_compression": statistics.mean(ratios),
                "success_rate": (success_count / len(ratios) * 100) if ratios else 0,
            }
        
        # Determine optimal thresholds
        optimal_rle_ratio = self._find_optimal_rle_ratio_threshold(ratio_analysis)
        optimal_pixel_count = self._find_optimal_pixel_threshold(pixel_analysis)
        
        # Generate recommendation
        recommendation = self._generate_rle_recommendation(
            optimal_rle_ratio,
            optimal_pixel_count,
            len(rle_encoded)
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(len(rle_encoded))
        
        return {
            "current_thresholds": {
                "pixel_count": 256,
                "rle_ratio": 0.4
            },
            "rle_ratio_analysis": ratio_analysis,
            "pixel_count_analysis": pixel_analysis,
            "optimal_thresholds": {
                "pixel_count": optimal_pixel_count,
                "rle_ratio": optimal_rle_ratio
            },
            "sample_size": len(rle_encoded),
            "confidence": confidence,
            "recommendation": recommendation,
        }
    
    def generate_recommendations(self) -> str:
        """
        Generate comprehensive threshold tuning report with recommendations.
        
        Creates a formatted text report combining:
        - Dataset summary
        - Palette indexing analysis and recommendations
        - RLE encoding analysis and recommendations
        - Confidence levels and next steps
        
        Returns:
            Formatted multi-line string report
            
        Example:
            >>> tuner = ThresholdTuner(records)
            >>> print(tuner.generate_recommendations())
            ====== Threshold Tuning Report ======
            Dataset: 50 sprites analyzed
            ...
        """
        if not self.metadata_list:
            return "No metadata records available for threshold tuning."
        
        lines = [
            "=" * 70,
            "Threshold Tuning Report",
            "=" * 70,
            "",
            f"Dataset: {len(self.metadata_list)} sprites analyzed",
            f"Minimum sample size for recommendations: {self.min_sample_size}",
            "",
        ]
        
        # Date range
        timestamps = [r["timestamp"] for r in self.metadata_list]
        if timestamps:
            lines.extend([
                f"Date range: {min(timestamps)} to {max(timestamps)}",
                "",
            ])
        
        # Palette indexing analysis
        lines.extend([
            "-" * 70,
            "1. Palette Indexing Threshold Analysis",
            "-" * 70,
            "",
        ])
        
        palette_analysis = self.analyze_palette_indexing()
        
        if "error" in palette_analysis:
            lines.extend([
                f"⚠️  {palette_analysis['error']}",
                "",
                "Current thresholds:",
                f"  - Palette size ≤ {palette_analysis['current_thresholds']['palette_size']}",
                f"  - Pixel count > {palette_analysis['current_thresholds']['pixel_count']}",
                "",
            ])
        else:
            current = palette_analysis["current_thresholds"]
            optimal = palette_analysis["optimal_thresholds"]
            
            lines.extend([
                f"Sample size: {palette_analysis['sample_size']} sprites",
                f"Confidence: {palette_analysis['confidence']}",
                "",
                "Current thresholds:",
                f"  - Palette size ≤ {current['palette_size']}",
                f"  - Pixel count > {current['pixel_count']}",
                "",
                "Recommended thresholds:",
                f"  - Palette size ≤ {optimal['palette_size']}",
                f"  - Pixel count > {optimal['pixel_count']}",
                "",
                f"💡 {palette_analysis['recommendation']}",
                "",
            ])
        
        # RLE encoding analysis
        lines.extend([
            "-" * 70,
            "2. RLE Encoding Threshold Analysis",
            "-" * 70,
            "",
        ])
        
        rle_analysis = self.analyze_rle_encoding()
        
        if "error" in rle_analysis:
            lines.extend([
                f"⚠️  {rle_analysis['error']}",
                "",
                "Current thresholds:",
                f"  - Pixel count > {rle_analysis['current_thresholds']['pixel_count']} OR",
                f"  - RLE ratio < {rle_analysis['current_thresholds']['rle_ratio']}",
                "",
            ])
        else:
            current = rle_analysis["current_thresholds"]
            optimal = rle_analysis["optimal_thresholds"]
            
            lines.extend([
                f"Sample size: {rle_analysis['sample_size']} sprites",
                f"Confidence: {rle_analysis['confidence']}",
                "",
                "Current thresholds:",
                f"  - Pixel count > {current['pixel_count']} OR",
                f"  - RLE ratio < {current['rle_ratio']}",
                "",
                "Recommended thresholds:",
                f"  - Pixel count > {optimal['pixel_count']} OR",
                f"  - RLE ratio < {optimal['rle_ratio']}",
                "",
                f"💡 {rle_analysis['recommendation']}",
                "",
            ])
        
        # Summary
        lines.extend([
            "=" * 70,
            "Summary",
            "=" * 70,
            "",
        ])
        
        if len(self.metadata_list) < self.min_sample_size:
            lines.extend([
                f"⚠️  Need more data: {len(self.metadata_list)}/{self.min_sample_size} sprites",
                "",
                "Next steps:",
                "1. Generate more sprites to reach minimum sample size",
                "2. Run threshold tuning again with larger dataset",
                "3. Ensure diverse sprite sizes and complexities",
                "",
            ])
        else:
            lines.extend([
                "✅ Sufficient data for threshold tuning",
                "",
                "Next steps:",
                "1. Review recommendations above",
                "2. Update thresholds in src/rendering/complexity_analyzer.py",
                "3. Re-run validation to verify improvements",
                "4. Monitor performance with new thresholds",
                "",
            ])
        
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def get_optimal_thresholds(self) -> dict[str, Any]:
        """
        Get dictionary of recommended threshold values for direct use.
        
        Returns:
            Dictionary with optimal threshold values for:
            - palette_indexing: {palette_size, pixel_count}
            - rle_encoding: {pixel_count, rle_ratio}
            - confidence: Overall confidence level
            
        Example:
            >>> tuner = ThresholdTuner(records)
            >>> thresholds = tuner.get_optimal_thresholds()
            >>> print(f"Use palette size ≤ {thresholds['palette_indexing']['palette_size']}")
        """
        palette_analysis = self.analyze_palette_indexing()
        rle_analysis = self.analyze_rle_encoding()
        
        # Determine overall confidence
        palette_conf = palette_analysis.get("confidence", "insufficient_data")
        rle_conf = rle_analysis.get("confidence", "insufficient_data")
        
        if palette_conf == "high" and rle_conf == "high":
            overall_confidence = "high"
        elif palette_conf == "medium" or rle_conf == "medium":
            overall_confidence = "medium"
        elif palette_conf == "low" or rle_conf == "low":
            overall_confidence = "low"
        else:
            overall_confidence = "insufficient_data"
        
        return {
            "palette_indexing": palette_analysis.get("optimal_thresholds", {
                "palette_size": 16,
                "pixel_count": 128
            }),
            "rle_encoding": rle_analysis.get("optimal_thresholds", {
                "pixel_count": 256,
                "rle_ratio": 0.4
            }),
            "confidence": overall_confidence,
            "sample_size": len(self.metadata_list),
            "min_sample_size": self.min_sample_size,
        }
    
    def _find_optimal_palette_threshold(self, analysis: dict[int, dict[str, Any]]) -> int:
        """Find optimal palette size threshold based on success rates."""
        if not analysis:
            return 16  # Default
        
        # Find palette size with best success rate
        best_size = 16
        best_rate = 0
        
        for size, stats in analysis.items():
            if stats["count"] >= 5:  # Require minimum 5 samples
                if stats["success_rate"] > best_rate:
                    best_rate = stats["success_rate"]
                    best_size = size
        
        # Be conservative - prefer not to increase threshold too much
        return min(best_size, 20)
    
    def _find_optimal_pixel_threshold(self, analysis: dict[int, dict[str, Any]]) -> int:
        """Find optimal pixel count threshold based on success rates."""
        if not analysis:
            return 128  # Default for palette, varies for RLE
        
        # Find pixel count bucket with best success rate
        best_bucket = min(analysis.keys()) if analysis else 128
        best_rate = 0
        
        for bucket, stats in analysis.items():
            if stats["count"] >= 5:  # Require minimum 5 samples
                if stats["success_rate"] > best_rate:
                    best_rate = stats["success_rate"]
                    best_bucket = bucket
        
        return best_bucket
    
    def _find_optimal_rle_ratio_threshold(self, analysis: dict[float, dict[str, Any]]) -> float:
        """Find optimal RLE ratio threshold based on success rates."""
        if not analysis:
            return 0.4  # Default
        
        # Find RLE ratio with best success rate
        best_ratio = 0.4
        best_rate = 0
        
        for ratio, stats in analysis.items():
            if stats["count"] >= 5:  # Require minimum 5 samples
                if stats["success_rate"] > best_rate:
                    best_rate = stats["success_rate"]
                    best_ratio = ratio
        
        # Stay within reasonable bounds
        return max(0.2, min(best_ratio, 0.6))
    
    def _generate_palette_recommendation(
        self,
        optimal_palette: int,
        optimal_pixels: int,
        sample_size: int
    ) -> str:
        """Generate human-readable recommendation for palette indexing."""
        if sample_size < self.min_sample_size:
            return f"Need {self.min_sample_size - sample_size} more sprites for confident recommendations"
        
        current_palette = 16
        current_pixels = 128
        
        changes = []
        if optimal_palette != current_palette:
            direction = "increase" if optimal_palette > current_palette else "decrease"
            changes.append(f"{direction} palette size threshold from {current_palette} to {optimal_palette}")
        
        if optimal_pixels != current_pixels:
            direction = "increase" if optimal_pixels > current_pixels else "decrease"
            changes.append(f"{direction} pixel count threshold from {current_pixels} to {optimal_pixels}")
        
        if not changes:
            return "Current thresholds appear optimal based on collected data"
        
        return "Consider: " + " and ".join(changes)
    
    def _generate_rle_recommendation(
        self,
        optimal_ratio: float,
        optimal_pixels: int,
        sample_size: int
    ) -> str:
        """Generate human-readable recommendation for RLE encoding."""
        if sample_size < self.min_sample_size:
            return f"Need {self.min_sample_size - sample_size} more sprites for confident recommendations"
        
        current_ratio = 0.4
        current_pixels = 256
        
        changes = []
        if abs(optimal_ratio - current_ratio) > 0.05:  # Significant change
            direction = "increase" if optimal_ratio > current_ratio else "decrease"
            changes.append(f"{direction} RLE ratio threshold from {current_ratio:.1f} to {optimal_ratio:.1f}")
        
        if abs(optimal_pixels - current_pixels) > 64:  # Significant change
            direction = "increase" if optimal_pixels > current_pixels else "decrease"
            changes.append(f"{direction} pixel count threshold from {current_pixels} to {optimal_pixels}")
        
        if not changes:
            return "Current thresholds appear optimal based on collected data"
        
        return "Consider: " + " and ".join(changes)
    
    def _calculate_confidence(self, sample_size: int) -> str:
        """Calculate confidence level based on sample size."""
        if sample_size < self.min_sample_size:
            return "insufficient_data"
        elif sample_size < self.min_sample_size * 2:
            return "low"
        elif sample_size < self.min_sample_size * 5:
            return "medium"
        else:
            return "high"
    
    def __repr__(self) -> str:
        """String representation of the tuner."""
        return f"ThresholdTuner(sprites={len(self.metadata_list)}, min_samples={self.min_sample_size})"