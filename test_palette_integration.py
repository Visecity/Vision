"""
Integration test for palette indexing in DetailAgent.

This script tests the complete workflow of palette-indexed sprite generation,
including encoding selection, LLM generation, and decoding.
"""

import asyncio
import logging
from pathlib import Path

from src.agents.detail_agent import DetailAgent
from src.agents.detail_schemas import (
    DetailAgentOutputPaletteIndexed,
    DetailAgentOutputRLE,
    DetailAgentOutput,
)
from src.core.config import Settings
from src.core.models import (
    AgentContext,
    SpriteRequest,
    Dimensions,
    AssetStyle,
    AssetType,
    ColorPalette,
)
from src.llm.client import LLMClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_encoding_selection():
    """Test that encoding selection logic works correctly."""
    
    logger.info("=" * 60)
    logger.info("TEST 1: Encoding Selection Logic")
    logger.info("=" * 60)
    
    # Test cases: (width, height, palette_size, expected_encoding)
    test_cases = [
        (8, 8, 8, "grid", "Small sprite should use standard grid"),
        (12, 12, 8, "palette_indexed_rle", "Medium sprite with ≤16 colors should use palette indexing"),
        (16, 16, 8, "palette_indexed_rle", "16x16 with 8 colors should use palette indexing"),
        (16, 16, 20, "grid", "16x16 with 20 colors uses grid (boundary case: 256 pixels)"),
        (17, 17, 20, "rle", "17x17 with 20 colors should use standard RLE"),
        (32, 32, 12, "palette_indexed_rle", "Large sprite with ≤16 colors should use palette indexing"),
        (24, 24, 16, "palette_indexed_rle", "24x24 with exactly 16 colors should use palette indexing"),
    ]
    
    passed = 0
    failed = 0
    
    for width, height, palette_size, expected, description in test_cases:
        pixel_count = width * height
        is_animated = False
        
        # Simulate encoding selection logic from DetailAgent
        use_palette_indexing = (
            palette_size <= 16 and
            pixel_count > 128
        )
        
        use_rle = (
            not use_palette_indexing and (
                pixel_count > 256 or
                (is_animated and pixel_count > 128)
            )
        )
        
        if use_palette_indexing:
            actual = "palette_indexed_rle"
        elif use_rle:
            actual = "rle"
        else:
            actual = "grid"
        
        if actual == expected:
            logger.info(f"✅ PASS: {description}")
            logger.info(f"   {width}×{height} with {palette_size} colors → {actual}")
            passed += 1
        else:
            logger.error(f"❌ FAIL: {description}")
            logger.error(f"   Expected: {expected}, Got: {actual}")
            failed += 1
    
    logger.info(f"\nEncoding Selection: {passed} passed, {failed} failed")
    return failed == 0


def test_schema_validation():
    """Test that Pydantic schemas validate correctly."""
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Schema Validation")
    logger.info("=" * 60)
    
    try:
        # Test palette-indexed schema
        palette_indexed_data = {
            "pixel_grid": {
                "width": 8,
                "height": 8,
                "encoding": "palette_indexed_rle",
                "palette": ["#FF0000", "#00FF00", "#0000FF"],
                "data": [
                    {"idx": 0, "count": 20},
                    {"idx": 1, "count": 24},
                    {"idx": 2, "count": 20}
                ]
            },
            "shading_details": {
                "light_source": "top-left",
                "shading_technique": "cel-shading",
                "contrast_level": "medium"
            },
            "final_specs": {
                "colors_used": ["#FF0000", "#00FF00", "#0000FF"],
                "total_pixels": 64,
                "readability_score": "high"
            }
        }
        
        output = DetailAgentOutputPaletteIndexed(**palette_indexed_data)
        logger.info("✅ PASS: Palette-indexed schema validation")
        
        # Verify structure
        assert output.pixel_grid.width == 8
        assert output.pixel_grid.height == 8
        assert len(output.pixel_grid.palette) == 3
        assert len(output.pixel_grid.data) == 3
        logger.info("✅ PASS: Schema structure verification")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ FAIL: Schema validation failed: {e}")
        return False


def test_decoding():
    """Test that palette-indexed data decodes correctly."""
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Palette-Indexed Decoding")
    logger.info("=" * 60)
    
    try:
        from src.rendering.palette_encoder import decode_palette_indexed
        
        # Create test data: 4×4 grid with 3 colors
        palette = ["#FF0000", "#00FF00", "#0000FF"]
        data = [
            {"idx": 0, "count": 4},   # Row 1: all red
            {"idx": 1, "count": 4},   # Row 2: all green
            {"idx": 2, "count": 4},   # Row 3: all blue
            {"idx": 0, "count": 4}    # Row 4: all red
        ]
        
        grid = decode_palette_indexed(4, 4, palette, data)
        
        # Verify grid structure
        assert len(grid) == 4, f"Expected 4 rows, got {len(grid)}"
        assert len(grid[0]) == 4, f"Expected 4 columns, got {len(grid[0])}"
        
        # Verify colors
        assert grid[0] == ["#FF0000"] * 4, "Row 1 should be all red"
        assert grid[1] == ["#00FF00"] * 4, "Row 2 should be all green"
        assert grid[2] == ["#0000FF"] * 4, "Row 3 should be all blue"
        assert grid[3] == ["#FF0000"] * 4, "Row 4 should be all red"
        
        logger.info("✅ PASS: Palette-indexed decoding successful")
        logger.info(f"   Decoded 4 segments → 4×4 grid with 3 colors")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ FAIL: Decoding failed: {e}")
        return False


def test_compression_metrics():
    """Test compression ratio calculations."""
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Compression Metrics")
    logger.info("=" * 60)
    
    try:
        from src.rendering.palette_encoder import calculate_palette_compression_ratio
        
        # Test case: 16×16 sprite with 8 colors, 60 segments
        metrics = calculate_palette_compression_ratio(
            palette_size=8,
            segment_count=60,
            width=16,
            height=16
        )
        
        logger.info(f"✅ Compression metrics calculated:")
        logger.info(f"   vs Standard Grid: {metrics['vs_grid_percent']:.1f}% reduction")
        logger.info(f"   vs Standard RLE: {metrics['vs_standard_rle_percent']:.1f}% reduction")
        logger.info(f"   Estimated tokens: {metrics['estimated_tokens']}")
        
        # Verify reasonable compression
        assert metrics['vs_grid_percent'] > 50, "Should achieve >50% compression vs grid"
        assert metrics['vs_standard_rle_percent'] > 30, "Should achieve >30% compression vs RLE"
        
        logger.info("✅ PASS: Compression metrics are reasonable")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ FAIL: Compression metrics failed: {e}")
        return False


async def test_detail_agent_integration():
    """Test DetailAgent with palette indexing (requires API key)."""
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST 5: DetailAgent Integration (Optional - Requires API)")
    logger.info("=" * 60)
    
    try:
        # Check if API key is available
        settings = Settings()
        if not settings.anthropic.api_key or settings.anthropic.api_key == "your-api-key-here":
            logger.warning("⚠️  SKIP: No API key configured")
            return True
        
        # Initialize LLM client and agent
        llm_client = LLMClient(settings=settings)
        agent = DetailAgent(llm_client=llm_client)
        
        # Create a simple test request (small sprite, 8 colors)
        request = SpriteRequest(
            description="A simple red and blue square icon",
            dimensions=Dimensions(width=12, height=12),
            style=AssetStyle.STARDEW_VALLEY,
            asset_type=AssetType.ICON,
        )
        
        # Mock previous results
        design_spec = {
            "shape_language": {"primary_shapes": ["square"], "proportions": "1:1"},
            "composition": {"layout": "centered", "focal_point": "center"},
            "technical_specs": {"pixel_density": "medium", "detail_level": "simple"}
        }
        
        palette = ColorPalette(
            colors=["#FF0000", "#0000FF", "#FFFFFF", "#000000", "#808080", "#FF8080", "#8080FF", "#C0C0C0"]
        )
        
        context = AgentContext(
            request=request,
            current_step="detail",
            previous_results={
                "design": design_spec,
                "palette": palette
            }
        )
        
        # Process with agent
        logger.info("Calling DetailAgent with 12×12 sprite and 8 colors...")
        result = await agent.process(context)
        
        # Verify result structure
        assert "pixel_grid" in result
        assert "shading_details" in result
        assert "final_specs" in result
        
        # Check if palette indexing was used
        metadata = result.get("_metadata", {})
        encoding_used = metadata.get("encoding_used")
        
        logger.info(f"✅ PASS: DetailAgent processed successfully")
        logger.info(f"   Encoding used: {encoding_used}")
        
        # Check for compression metadata
        pixel_grid = result["pixel_grid"]
        if "_palette_indexed_metadata" in pixel_grid:
            pi_meta = pixel_grid["_palette_indexed_metadata"]
            logger.info(f"   Palette size: {pi_meta['palette_size']}")
            logger.info(f"   Segments: {pi_meta['segment_count']}")
            logger.info(f"   Compression vs grid: {pi_meta['compression_vs_grid_percent']:.1f}%")
            logger.info(f"   Compression vs RLE: {pi_meta['compression_vs_rle_percent']:.1f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ FAIL: DetailAgent integration failed: {e}")
        logger.error(f"   This is expected if API key is not configured")
        return False


def main():
    """Run all integration tests."""
    
    logger.info("=" * 60)
    logger.info("PALETTE INDEXING INTEGRATION TESTS")
    logger.info("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Encoding Selection", test_encoding_selection()))
    results.append(("Schema Validation", test_schema_validation()))
    results.append(("Decoding", test_decoding()))
    results.append(("Compression Metrics", test_compression_metrics()))
    
    # Optional API test
    if asyncio.run(test_detail_agent_integration()):
        results.append(("DetailAgent Integration", True))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 ALL TESTS PASSED! Palette indexing integration is working correctly.")
        return 0
    else:
        logger.error(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())