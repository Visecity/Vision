#!/usr/bin/env python3
"""
Threshold tuning script for adaptive encoding optimization.

This script analyzes collected sprite metadata to recommend optimal threshold
values for encoding strategy selection (palette indexing and RLE encoding).

Usage:
    python scripts/tune_thresholds.py [--save-json]
    
Options:
    --save-json     Save recommendations to JSON file
    --min-samples N Set minimum sample size (default: 20)
    --help          Show this help message

Example:
    # Run tuning and display recommendations
    python scripts/tune_thresholds.py
    
    # Save recommendations to file
    python scripts/tune_thresholds.py --save-json
"""

import sys
import json
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rendering.metadata_collector import MetadataCollector
from src.rendering.threshold_tuner import ThresholdTuner


def main() -> int:
    """Main entry point for threshold tuning script."""
    parser = argparse.ArgumentParser(
        description="Analyze and tune adaptive encoding thresholds",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--save-json",
        action="store_true",
        help="Save recommendations to JSON file"
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=20,
        help="Minimum sample size for recommendations (default: 20)"
    )
    parser.add_argument(
        "--storage-dir",
        type=str,
        default="metadata",
        help="Metadata storage directory (default: metadata)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Adaptive Threshold Tuning")
    print("=" * 70)
    print()
    
    # Load collected metadata
    print(f"Loading metadata from {args.storage_dir}/...")
    collector = MetadataCollector(storage_dir=args.storage_dir)
    metadata_list = collector.get_all()
    
    if not metadata_list:
        print("❌ No metadata records found.")
        print()
        print("To collect metadata:")
        print("1. Generate sprites using the Vision system")
        print("2. Metadata is automatically collected during generation")
        print("3. Run this script again after generating sprites")
        print()
        return 1
    
    print(f"✅ Loaded {len(metadata_list)} metadata records")
    print()
    
    # Initialize threshold tuner
    print(f"Analyzing thresholds (min sample size: {args.min_samples})...")
    tuner = ThresholdTuner(metadata_list, min_sample_size=args.min_samples)
    
    # Generate and display recommendations
    recommendations_text = tuner.generate_recommendations()
    print(recommendations_text)
    
    # Save to JSON if requested
    if args.save_json:
        output_path = Path(args.storage_dir) / "threshold_recommendations.json"
        
        # Get structured recommendations
        optimal_thresholds = tuner.get_optimal_thresholds()
        palette_analysis = tuner.analyze_palette_indexing()
        rle_analysis = tuner.analyze_rle_encoding()
        
        # Build output structure
        output_data = {
            "summary": {
                "total_sprites": len(metadata_list),
                "min_sample_size": args.min_samples,
                "confidence": optimal_thresholds["confidence"],
            },
            "optimal_thresholds": optimal_thresholds,
            "palette_indexing_analysis": palette_analysis,
            "rle_encoding_analysis": rle_analysis,
        }
        
        # Save to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
        
        print()
        print(f"📊 Recommendations saved to: {output_path}")
        print()
    
    # Display optimal thresholds summary
    optimal = tuner.get_optimal_thresholds()
    print()
    print("=" * 70)
    print("Quick Reference - Optimal Thresholds")
    print("=" * 70)
    print()
    print("Palette Indexing:")
    print(f"  palette_size ≤ {optimal['palette_indexing']['palette_size']}")
    print(f"  pixel_count > {optimal['palette_indexing']['pixel_count']}")
    print()
    print("RLE Encoding:")
    print(f"  pixel_count > {optimal['rle_encoding']['pixel_count']} OR")
    print(f"  rle_ratio < {optimal['rle_encoding']['rle_ratio']}")
    print()
    print(f"Confidence: {optimal['confidence']}")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())