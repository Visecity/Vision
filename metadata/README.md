# Metadata Storage Directory

This directory stores metadata from sprite generation operations for Phase 3 Adaptive Thresholds monitoring and analysis.

## Purpose

The MetadataCollector service automatically stores metadata as JSON files in this directory. This data is used for:

- Performance monitoring (analysis time tracking)
- Encoding decision analysis
- Threshold tuning and optimization
- Prediction accuracy validation

## File Format

Each file is named: `{timestamp}_{request_id}.json`

Example: `2025-11-20T02-00-00-000Z_abc12345.json`

## Data Collection

Metadata is automatically collected by DetailAgent during sprite generation:
- Non-blocking operation (doesn't slow down generation)
- Thread-safe for concurrent operations
- Includes complexity metrics, encoding decisions, and performance data

## Usage

```python
from src.rendering.metadata_collector import MetadataCollector

# Get all collected metadata
collector = MetadataCollector()
records = collector.get_all()

# Get summary statistics
summary = collector.get_summary()
print(f"Total records: {summary['total_records']}")
print(f"Avg analysis time: {summary['avg_analysis_time_ms']:.2f}ms")

# Clear old data (use with caution!)
# collector.clear()
```

## Important Notes

- JSON files in this directory are automatically generated
- Do not manually edit these files
- Old data can be cleared using `collector.clear()` if needed
- This directory is tracked in git but JSON files are ignored