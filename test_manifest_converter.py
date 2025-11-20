"""
Test script for manifest converter.

Verifies that DetailAgent output can be converted to Manifest JSON DSL
and rendered successfully.
"""

import asyncio
import json
import logging
from pathlib import Path

from src.rendering.manifest_converter import convert_detail_to_manifest
from src.rendering.manifest_renderer import ManifestRenderer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_detail_output() -> dict:
    """Create a sample DetailAgent output for testing."""
    return {
        "pixel_grid": {
            "width": 16,
            "height": 16,
            "data": [
                "Sample row-by-row pixel data",
                "This is conceptual description format",
                "Will trigger placeholder creation"
            ],
            "format": "conceptual description"
        },
        "shading_details": {
            "light_source": "top-left",
            "shading_technique": "hue-shifting",
            "shadow_placement": ["right side", "bottom"],
            "highlight_placement": ["top-left edges"]
        },
        "final_specs": {
            "colors_used": ["#4d8c2d", "#3a6b1e", "#69b03e", "#2d5016", "#6b4423"],
            "total_pixels": 180,
            "readability_score": "high",
            "complexity_achieved": "medium"
        },
        "implementation_notes": {
            "key_decisions": ["Used rounded edges", "Applied strategic shading"],
            "challenges": ["Limited resolution"],
            "optimizations": ["Efficient color use"]
        },
        "rendering_hints": {
            "anti_aliasing": "minimal",
            "dithering": "none",
            "texture_technique": "solid colors"
        }
    }


async def test_converter():
    """Test the manifest converter and renderer."""
    logger.info("="*60)
    logger.info("Testing Manifest Converter")
    logger.info("="*60)
    
    # Step 1: Create sample DetailAgent output
    logger.info("\n1. Creating sample DetailAgent output...")
    detail_output = create_sample_detail_output()
    logger.info(f"   ✓ Created detail output: {detail_output['pixel_grid']['width']}x{detail_output['pixel_grid']['height']}")
    logger.info(f"   ✓ Colors used: {len(detail_output['final_specs']['colors_used'])}")
    
    # Step 2: Convert to Manifest JSON
    logger.info("\n2. Converting to Manifest JSON DSL...")
    try:
        manifest = convert_detail_to_manifest(
            detail_spec=detail_output,
            asset_name="test_sprite",
            asset_description="Test sprite for converter validation"
        )
        logger.info("   ✓ Conversion successful!")
        logger.info(f"   ✓ Manifest version: {manifest.get('version')}")
        logger.info(f"   ✓ Canvas: {manifest['metadata']['canvas']['width']}x{manifest['metadata']['canvas']['height']}")
        logger.info(f"   ✓ Layers: {len(manifest.get('layers', []))}")
        logger.info(f"   ✓ Elements: {len(manifest['layers'][0]['elements']) if manifest.get('layers') else 0}")
        
        # Save manifest for inspection
        manifest_path = Path("test_output/test_converter_manifest.json")
        manifest_path.parent.mkdir(exist_ok=True)
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"   ✓ Saved manifest to: {manifest_path}")
        
    except Exception as e:
        logger.error(f"   ✗ Conversion failed: {e}")
        raise
    
    # Step 3: Validate manifest structure
    logger.info("\n3. Validating manifest structure...")
    required_fields = ['version', 'metadata', 'layers']
    for field in required_fields:
        if field not in manifest:
            raise ValueError(f"Missing required field: {field}")
        logger.info(f"   ✓ Has '{field}' field")
    
    if 'canvas' not in manifest['metadata']:
        raise ValueError("Missing metadata.canvas")
    logger.info("   ✓ Has 'metadata.canvas' field")
    
    # Step 4: Render to PNG
    logger.info("\n4. Rendering manifest to PNG...")
    try:
        renderer = ManifestRenderer(scale=4, include_metadata=True)
        
        output_path = Path("test_output/test_converter_output.png")
        output_path.parent.mkdir(exist_ok=True)
        
        rendered_path = await renderer.render_manifest_async(
            manifest=manifest,
            output_path=output_path,
            transparent_color=None
        )
        
        logger.info(f"   ✓ Rendered successfully to: {rendered_path}")
        logger.info(f"   ✓ File size: {rendered_path.stat().st_size} bytes")
        
    except Exception as e:
        logger.error(f"   ✗ Rendering failed: {e}")
        raise
    
    # Success!
    logger.info("\n" + "="*60)
    logger.info("✓ ALL TESTS PASSED!")
    logger.info("="*60)
    logger.info(f"\nOutput files:")
    logger.info(f"  - Manifest: {manifest_path}")
    logger.info(f"  - PNG: {rendered_path}")
    logger.info("\nThe converter successfully transforms DetailAgent output")
    logger.info("into renderable Manifest JSON DSL format!")


async def test_with_hex_array():
    """Test with a flat hex color array."""
    logger.info("\n" + "="*60)
    logger.info("Testing with Hex Color Array")
    logger.info("="*60)
    
    # Create a simple 8x8 gradient
    detail_output = {
        "pixel_grid": {
            "width": 8,
            "height": 8,
            "data": [
                "#FF0000", "#FF3300", "#FF6600", "#FF9900", "#FFCC00", "#FFFF00", "#CCFF00", "#99FF00",
                "#66FF00", "#33FF00", "#00FF00", "#00FF33", "#00FF66", "#00FF99", "#00FFCC", "#00FFFF",
                "#00CCFF", "#0099FF", "#0066FF", "#0033FF", "#0000FF", "#3300FF", "#6600FF", "#9900FF",
                "#CC00FF", "#FF00FF", "#FF00CC", "#FF0099", "#FF0066", "#FF0033", "#FF0000", "#FF0000",
                "#CC0000", "#990000", "#660000", "#330000", "#000000", "#333333", "#666666", "#999999",
                "#CCCCCC", "#FFFFFF", "#CCCCCC", "#999999", "#666666", "#333333", "#000000", "#000000",
                "#000033", "#000066", "#000099", "#0000CC", "#0000FF", "#3333FF", "#6666FF", "#9999FF",
                "#CCCCFF", "#FFFFFF", "#CCCCFF", "#9999FF", "#6666FF", "#3333FF", "#0000FF", "#0000CC"
            ],
            "format": "flat hex array"
        },
        "shading_details": {
            "light_source": "top-left",
            "shading_technique": "gradient",
        },
        "final_specs": {
            "colors_used": ["#FF0000", "#00FF00", "#0000FF", "#FFFFFF", "#000000"],
            "total_pixels": 64,
            "readability_score": "high",
        }
    }
    
    logger.info("Converting 8x8 gradient test...")
    manifest = convert_detail_to_manifest(detail_output, "gradient_test", "Color gradient")
    
    renderer = ManifestRenderer(scale=8, include_metadata=False)
    output_path = Path("test_output/test_gradient.png")
    await renderer.render_manifest_async(manifest, output_path)
    
    logger.info(f"✓ Gradient test successful: {output_path}")


async def main():
    """Run all tests."""
    try:
        await test_converter()
        await test_with_hex_array()
        
        logger.info("\n" + "="*60)
        logger.info("🎉 ALL CONVERTER TESTS PASSED!")
        logger.info("="*60)
        logger.info("\nThe manifest converter is working correctly.")
        logger.info("Ready to re-run batch generation with rendering enabled.")
        
    except Exception as e:
        logger.error("\n" + "="*60)
        logger.error("❌ TESTS FAILED")
        logger.error("="*60)
        logger.error(f"\nError: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())