# Threshold Tuning Guide

**Version:** 1.0.0  
**Phase:** 3 - Adaptive Thresholds  
**Date:** 2025-11-20

---

## Overview

This guide explains the threshold tuning methodology for optimizing adaptive encoding decisions in the Vision pixel art generation system. Threshold tuning ensures that encoding strategy selection achieves >90% optimal performance with minimal overhead.

### What is Threshold Tuning?

Threshold tuning is the process of analyzing collected sprite generation metadata to determine optimal threshold values for encoding strategy selection. The system currently uses fixed thresholds to decide when to use:

1. **Palette Indexing + RLE**: For sprites with few colors (≤16) and sufficient size (>128 pixels)
2. **Standard RLE**: For larger sprites (>256 pixels) or high repetition (ratio <0.4)
3. **Standard Grid**: For small sprites with moderate complexity

Threshold tuning analyzes actual compression success rates to recommend adjustments to these threshold values.

---

## Current Default Thresholds

### Palette Indexing Decision

Located in [`src/rendering/complexity_analyzer.py`](../src/rendering/complexity_analyzer.py:recommend_encoding_strategy):

```python
if palette_size <= 16 and pixel_count > 128:
    return "palette_indexed_rle"
```

**Thresholds:**
- `palette_size ≤ 16`: Maximum colors for palette indexing
- `pixel_count > 128`: Minimum pixels to justify overhead

**Rationale:** Palette indexing provides 60-75% compression for sprites with limited colors, but only worth the overhead for sprites larger than 128 pixels.

### RLE Encoding Decision

```python
if pixel_count > 256 or complexity["estimated_rle_ratio"] < 0.4:
    return "rle"
```

**Thresholds:**
- `pixel_count > 256`: Size where RLE overhead is justified
- `estimated_rle_ratio < 0.4`: High repetition (fewer than 40% of pixels are segment headers)

**Rationale:** RLE provides compression for repetitive patterns, but overhead makes it inefficient for small or complex sprites.

---

## Threshold Tuning Process

### Step 1: Collect Metadata

Metadata is automatically collected during sprite generation:

```python
from src.rendering.metadata_collector import MetadataCollector

# Metadata collector runs automatically in DetailAgent
# Check collected data
collector = MetadataCollector()
summary = collector.get_summary()
print(f"Collected {summary['total_records']} sprites")
```

**Metadata Location:** `metadata/*.json`

**Required Sample Size:** Minimum 20 sprites per encoding type (40-50 total recommended)

### Step 2: Run Threshold Tuning

Use the tuning script to analyze collected data:

```bash
# Basic tuning
python scripts/tune_thresholds.py

# Save recommendations to JSON
python scripts/tune_thresholds.py --save-json

# Custom minimum sample size
python scripts/tune_thresholds.py --min-samples 30
```

**Output:**
- Console report with analysis and recommendations
- Optional JSON file: `metadata/threshold_recommendations.json`

### Step 3: Review Recommendations

The tuning report provides:

1. **Current vs Optimal Thresholds**: Comparison of current and recommended values
2. **Success Rate Analysis**: How well each threshold performs
3. **Confidence Level**: Based on sample size (high/medium/low/insufficient_data)
4. **Actionable Recommendations**: Specific threshold adjustments

Example output:

```
======================================================================
Threshold Tuning Report
======================================================================

Dataset: 50 sprites analyzed
Minimum sample size for recommendations: 20

----------------------------------------------------------------------
1. Palette Indexing Threshold Analysis
----------------------------------------------------------------------

Sample size: 25 sprites
Confidence: medium

Current thresholds:
  - Palette size ≤ 16
  - Pixel count > 128

Recommended thresholds:
  - Palette size ≤ 16
  - Pixel count > 64

💡 Consider: decrease pixel count threshold from 128 to 64

----------------------------------------------------------------------
2. RLE Encoding Threshold Analysis
----------------------------------------------------------------------

Sample size: 20 sprites
Confidence: low

Current thresholds:
  - Pixel count > 256 OR
  - RLE ratio < 0.4

Recommended thresholds:
  - Pixel count > 256 OR
  - RLE ratio < 0.4

💡 Current thresholds appear optimal based on collected data
```

### Step 4: Update Thresholds

If recommendations suggest changes, update [`src/rendering/complexity_analyzer.py`](../src/rendering/complexity_analyzer.py):

```python
def recommend_encoding_strategy(
    complexity: ComplexityMetrics,
    pixel_count: int,
    palette_size: int
) -> str:
    """Recommend encoding strategy based on sprite characteristics."""
    
    # Update threshold values here based on tuning recommendations
    if palette_size <= 16 and pixel_count > 64:  # Changed from 128
        return "palette_indexed_rle"
    
    if pixel_count > 256 or complexity["estimated_rle_ratio"] < 0.4:
        return "rle"
    
    return "standard"
```

### Step 5: Validate Changes

After updating thresholds, validate the changes:

```bash
# Run validation script
python scripts/validate_phase3.py

# Generate new sprites to test
# Monitor performance and compression ratios
```

---

## Understanding the Analysis

### Success Rate Calculation

**For Palette Indexing:**
- Success = actual compression ratio < 0.5 (50%+ size reduction)
- Analyzes success rates at different palette sizes and pixel counts
- Recommends threshold that maximizes success rate

**For RLE Encoding:**
- Success = actual compression ratio < 0.7 (30%+ size reduction)
- Analyzes success rates at different RLE ratios and pixel counts
- Recommends threshold that maximizes efficiency

### Confidence Levels

The tuning system provides confidence levels based on sample size:

| Confidence Level | Sample Size | Description |
|-----------------|-------------|-------------|
| `insufficient_data` | < min_sample_size | Need more sprites |
| `low` | min_sample_size to 2× | Limited confidence in recommendations |
| `medium` | 2× to 5× min_sample_size | Moderate confidence |
| `high` | > 5× min_sample_size | High confidence in recommendations |

**Default minimum sample size:** 20 sprites per encoding type

### Threshold Boundaries

The tuning system enforces reasonable boundaries:

**Palette Indexing:**
- `palette_size`: 4-20 colors (conservative, won't recommend >20)
- `pixel_count`: 64-1024 pixels

**RLE Encoding:**
- `rle_ratio`: 0.2-0.6 (stay within practical compression range)
- `pixel_count`: 128-2048 pixels

---

## Best Practices

### Data Collection

1. **Diverse Dataset**: Generate sprites of varying:
   - Sizes (8×8 to 64×64)
   - Complexities (simple to detailed)
   - Color counts (4 to 32+ colors)

2. **Sufficient Samples**: Aim for 50-100 sprites before tuning
   - Ensures representation across encoding types
   - Provides statistical significance

3. **Real-World Usage**: Collect data from actual sprite generation
   - Don't rely solely on test data
   - Include common use cases

### Interpreting Recommendations

1. **Small Changes (<10%)**: Usually safe to implement
   - Example: 128 → 120 pixels
   - Low risk of negative impact

2. **Large Changes (>25%)**: Review carefully
   - Example: 128 → 64 pixels
   - May indicate dataset bias or special use case

3. **Conflicting Signals**: 
   - Palette analysis suggests increase, RLE suggests decrease
   - May indicate need for more data or separate thresholds by sprite type

### When to Retune

Retune thresholds when:

1. **After Major Changes**: 
   - Updated encoding algorithms
   - Modified complexity analyzer
   - Changed LLM model or prompts

2. **Performance Degradation**:
   - Encoding selection success rate drops below 85%
   - Prediction errors increase above 15%

3. **New Use Cases**:
   - Different sprite styles
   - New size ranges
   - Different complexity patterns

4. **Periodic Review**:
   - Monthly for active development
   - Quarterly for stable production

---

## Troubleshooting

### "Insufficient data" Error

**Problem:** Not enough sprites collected for analysis

**Solutions:**
1. Generate more sprites (aim for 50+ total)
2. Lower `--min-samples` (risky, reduces confidence)
3. Wait for more natural usage to accumulate data

### Unrealistic Recommendations

**Problem:** Tuning suggests extreme threshold values

**Possible Causes:**
1. **Dataset Bias**: All sprites similar size/complexity
   - Solution: Generate more diverse sprites
   
2. **Small Sample Size**: Recommendations based on few sprites
   - Solution: Collect more data
   
3. **Outliers**: Few sprites with extreme characteristics
   - Solution: Review collected metadata for anomalies

### Low Confidence Despite Sufficient Samples

**Problem:** Confidence remains "low" with 40+ sprites

**Possible Causes:**
1. **Imbalanced Encoding Types**: 
   - 35 palette-indexed, 5 RLE
   - Solution: Generate sprites that trigger other encodings
   
2. **Missing Actual Compression Data**:
   - Metadata collected but compressions not calculated
   - Solution: Ensure metadata includes actual compression ratios

### Contradictory Recommendations

**Problem:** Multiple tuning runs suggest different values

**Possible Causes:**
1. **Insufficient Sample Size**: Natural variation in small datasets
2. **Dataset Shift**: Different sprite types between runs
3. **Threshold Interdependence**: Changes in one affect success of another

**Solution:** Collect larger dataset (100+ sprites) and tune once

---

## Programmatic Usage

### Python API

```python
from src.rendering.metadata_collector import MetadataCollector
from src.rendering.threshold_tuner import ThresholdTuner

# Load collected metadata
collector = MetadataCollector()
metadata = collector.get_all()

# Initialize tuner
tuner = ThresholdTuner(metadata, min_sample_size=20)

# Analyze palette indexing
palette_analysis = tuner.analyze_palette_indexing()
print(f"Palette recommendation: {palette_analysis['recommendation']}")

# Analyze RLE encoding
rle_analysis = tuner.analyze_rle_encoding()
print(f"RLE recommendation: {rle_analysis['recommendation']}")

# Get optimal thresholds
optimal = tuner.get_optimal_thresholds()
print(f"Confidence: {optimal['confidence']}")
print(f"Palette size ≤ {optimal['palette_indexing']['palette_size']}")
print(f"Pixel count > {optimal['palette_indexing']['pixel_count']}")

# Generate full report
report = tuner.generate_recommendations()
print(report)
```

### Custom Analysis

```python
# Analyze specific sprite characteristics
palette_indexed_sprites = [
    m for m in metadata 
    if m["encoding_decision"]["selected_encoding"] == "palette_indexed_rle"
]

# Calculate average compression by palette size
from collections import defaultdict
import statistics

compressions = defaultdict(list)
for sprite in palette_indexed_sprites:
    palette_size = sprite["palette_size"]
    actual = sprite["encoding_decision"]["actual_compression"]
    if actual is not None:
        compressions[palette_size].append(actual)

for size, ratios in sorted(compressions.items()):
    avg = statistics.mean(ratios)
    print(f"Palette size {size}: {avg:.3f} avg compression ({len(ratios)} sprites)")
```

---

## Advanced Topics

### Multi-Dimensional Threshold Optimization

Current thresholds are independent (palette size AND pixel count). Advanced optimization could consider:

1. **Combined Thresholds**: `f(palette_size, pixel_count, complexity)`
2. **Decision Trees**: More complex decision logic
3. **Machine Learning**: Train classifier on metadata

### A/B Testing

Test threshold changes in production:

```python
# Randomly assign thresholds for comparison
import random

def recommend_encoding_strategy_ab(complexity, pixel_count, palette_size):
    """A/B test different thresholds."""
    use_new_thresholds = random.random() < 0.5
    
    if use_new_thresholds:
        # New thresholds from tuning
        palette_threshold = 64
    else:
        # Current thresholds
        palette_threshold = 128
    
    # ... rest of logic
    
    # Log which threshold set was used
    # Compare performance after collecting data
```

### Continuous Optimization

Set up automated threshold tuning:

```bash
# Cron job to run weekly
0 0 * * 0 cd /path/to/vision && python scripts/tune_thresholds.py --save-json
```

Review recommendations regularly and update thresholds when confidence is high.

---

## Examples

### Example 1: First-Time Tuning

```bash
# Generate initial dataset
python scripts/render_all_assets.py

# Check collected data
python -c "from src.rendering.metadata_collector import MetadataCollector; \
           c = MetadataCollector(); \
           print(c.get_summary())"

# Run tuning
python scripts/tune_thresholds.py --save-json

# Review recommendations in metadata/threshold_recommendations.json
```

### Example 2: Investigating Poor Performance

```python
from src.rendering.metadata_collector import MetadataCollector
from src.rendering.analytics import EncodingAnalytics

# Load and analyze
collector = MetadataCollector()
analytics = EncodingAnalytics(collector.get_all())

# Check performance
perf = analytics.analyze_performance()
print(f"Mean prediction error: {perf['prediction_accuracy']['mean_error_percent']:.1f}%")

# If error is high (>15%), run tuning
from src.rendering.threshold_tuner import ThresholdTuner
tuner = ThresholdTuner(collector.get_all())
print(tuner.generate_recommendations())
```

### Example 3: Validating Threshold Changes

```python
# Before: Collect baseline metrics
from src.rendering.metadata_collector import MetadataCollector
baseline_collector = MetadataCollector()
baseline_data = baseline_collector.get_all()

# Update thresholds in complexity_analyzer.py
# ...

# After: Generate new sprites with updated thresholds
# ...

# Compare performance
from src.rendering.analytics import EncodingAnalytics

baseline_analytics = EncodingAnalytics(baseline_data)
new_analytics = EncodingAnalytics(new_collector.get_all())

baseline_perf = baseline_analytics.analyze_performance()
new_perf = new_analytics.analyze_performance()

print(f"Baseline prediction error: {baseline_perf['prediction_accuracy']['mean_error_percent']:.1f}%")
print(f"New prediction error: {new_perf['prediction_accuracy']['mean_error_percent']:.1f}%")
```

---

## FAQ

### How often should I tune thresholds?

- **Development**: After major algorithm changes
- **Production**: Monthly review, tune quarterly if needed
- **Low usage**: When you accumulate 50+ new sprites

### What if I don't have enough data?

Generate more sprites or lower the minimum sample size (not recommended below 10):

```bash
python scripts/tune_thresholds.py --min-samples 10
```

### Can I tune for specific sprite types?

Yes, filter metadata before tuning:

```python
metadata = collector.get_all()
character_sprites = [m for m in metadata if m["asset_type"] == "character"]
tuner = ThresholdTuner(character_sprites)
```

### How do I know if new thresholds are better?

Run validation and compare:
- Prediction error should decrease
- Analysis time should remain <10ms
- Compression ratios should improve or stay same

---

## References

- [Phase 3 Architecture](../ADAPTIVE_THRESHOLDS_ARCHITECTURE.md)
- [Complexity Analyzer](../src/rendering/complexity_analyzer.py)
- [Metadata Schema](../src/rendering/metadata_schema.py)
- [Analytics Module](../src/rendering/analytics.py)

---

**Last Updated:** 2025-11-20  
**Version:** 1.0.0  
**Maintainer:** Vision Development Team