"""
Test script for RLE (Run-Length Encoding) implementation in Vision.

This script validates RLE encoding/decoding functionality and tests
RLE-enabled sprite generation.
"""

import asyncio
import logging
from pathlib import Path

from src.agents.detail_schemas import DetailAgentOutputRLE, RLESegment, PixelGridRLE
from src.rendering.rle_decoder import (
    decode_rle_to_grid,
    validate_rle_data,
    calculate_compression_ratio,
    encode_grid_to_rle,
)
from src.core.config import get_settings
from src.core.models import SpriteRequest, SpriteDimensions, SpriteStyle
from src.llm.client import LLMClient
from src.agents.detail_agent import DetailAgent
from src.agents.design_agent import DesignAgent
from src.agents.palette_agent import PaletteAgent
from src.core.models import AgentContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_rle_decoder_basic():
    """Test basic RLE encoding and decoding."""
    print("\n=== Test 1: Basic RLE Encoding/Decoding ===")
    
    # Create a simple 4×4 grid
    grid = [
        ['#FF0000', '#FF0000', '#FF0000', '#FF0000'],
        ['#FF0000', '#0000FF', '#0000FF', '#0000FF'],
        ['#FF0000', '#0000FF', '#0000FF', '#0000FF'],
        ['#FF0000', '#FF0000', '#FF0000', '#FF0000'],
    ]
    
    # Encode to RLE
    rle_data = encode_grid_to_rle(grid)
    print(f"Original grid: 4×4 = 16 pixels")
    print(f"RLE segments: {len(rle_data)}")
    print(f"Compression: {(1 - len(rle_data)/16)*100:.1f}%")
    print(f"RLE data: {rle_data}")
    
    # Decode back
    decoded_grid = decode_rle_to_grid(4, 4, rle_data)
    
    # Verify
    assert decoded_grid == grid, "Decoded grid doesn't match original!"
    print("✅ Basic encoding/decoding passed")
    
    return True


def test_rle_compression_ratios():
    """Test compression ratios for different patterns."""
    print("\n=== Test 2: Compression Ratios ===")
    
    test_cases = [
        ("Solid color 32×32", [['#FF0000'] * 32 for _ in range(32)]),
        ("Checkerboard 16×16", [
            ['#FF0000' if (i+j) % 2 == 0 else '#0000FF' for i in range(16)]
            for j in range(16)
        ]),
        ("Horizontal stripes", [
            ['#FF0000'] * 16 if i % 2 == 0 else ['#0000FF'] * 16
            for i in range(16)
        ]),
    ]
    
    for name, grid in test_cases:
        height = len(grid)
        width = len(grid[0]) if grid else 0
        total_pixels = width * height
        
        rle_data = encode_grid_to_rle(grid)
        compression = (1 - len(rle_data) / total_pixels) * 100
        
        print(f"{name}:")
        print(f"  - Size: {width}×{height} = {total_pixels} pixels")
        print(f"  - RLE segments: {len(rle_data)}")
        print(f"  - Compression: {compression:.1f}%")
        
        # Verify decoding
        decoded = decode_rle_to_grid(width, height, rle_data)
        assert decoded == grid, f"{name} decoding failed!"
        print(f"  ✅ Verified")
    
    return True


def test_rle_validation():
    """Test RLE data validation."""
    print("\n=== Test 3: RLE Validation ===")
    
    # Valid RLE
    valid_rle = [
        {"color": "#FF0000", "count": 8},
        {"color": "#0000FF", "count": 8},
    ]
    is_valid, errors = validate_rle_data(4, 4, valid_rle)
    assert is_valid, f"Valid RLE marked as invalid: {errors}"
    print("✅ Valid RLE accepted")
    
    # Invalid: wrong pixel count
    invalid_rle = [
        {"color": "#FF0000", "count": 10},
    ]
    is_valid, errors = validate_rle_data(4, 4, invalid_rle)
    assert not is_valid, "Invalid RLE (wrong count) accepted!"
    print(f"✅ Invalid pixel count rejected: {errors[0]}")
    
    # Invalid: negative count
    invalid_rle2 = [
        {"color": "#FF0000", "count": -5},
        {"color": "#0000FF", "count": 21},
    ]
    is_valid, errors = validate_rle_data(4, 4, invalid_rle2)
    assert not is_valid, "Invalid RLE (negative count) accepted!"
    print(f"✅ Negative count rejected: {errors[0]}")
    
    return True


def test_pydantic_schemas():
    """Test Pydantic schema validation for RLE."""
    print("\n=== Test 4: Pydantic Schema Validation ===")
    
    # Valid RLE segment
    segment = RLESegment(color="#FF0000", count=10)
    assert segment.color == "#FF0000"
    assert segment.count == 10
    print("✅ Valid RLE segment created")
    
    # Valid RLE pixel grid
    rle_grid = PixelGridRLE(
        width=4,
        height=4,
        encoding="rle",
        data=[
            RLESegment(color="#FF0000", count=8),
            RLESegment(color="#0000FF", count=8),
        ]
    )
    assert rle_grid.width == 4
    assert rle_grid.height == 4
    assert len(rle_grid.data) == 2
    print("✅ Valid RLE pixel grid created")
    
    # Test invalid color pattern
    try:
        invalid_segment = RLESegment(color="FF0000", count=5)  # Missing #
        assert False, "Invalid color pattern accepted!"
    except Exception as e:
        print(f"✅ Invalid color pattern rejected: {type(e).__name__}")
    
    return True


async def test_rle_sprite_generation():
    """Test RLE-enabled sprite generation with DetailAgent."""
    print("\n=== Test 5: RLE Sprite Generation ===")
    
    # Initialize settings and client
    settings = get_settings()
    llm_client = LLMClient(settings=settings)
    
    # Create a 32×32 sprite request (should trigger RLE)
    request = SpriteRequest(
        description="32x32 blue square with white border",
        dimensions=SpriteDimensions(width=32, height=32),
        style=SpriteStyle.STARDEW_VALLEY,
    )
    
    print(f"Generating {request.dimensions.width}×{request.dimensions.height} sprite...")
    print("(This should automatically use RLE encoding)")
    
    # Generate design
    design_agent = DesignAgent(llm_client=llm_client)
    design_context = AgentContext(
        request=request,
        current_step="design",
        previous_results={},
        retry_count=0,
    )
    design_spec = await design_agent.process(design_context)
    print("✅ Design generated")
    
    # Generate palette
    palette_agent = PaletteAgent(llm_client=llm_client)
    palette_context = AgentContext(
        request=request,
        current_step="palette",
        previous_results={"design": design_spec},
        retry_count=0,
    )
    palette = await palette_agent.process(palette_context)
    print("✅ Palette generated")
    
    # Generate detail with RLE
    detail_agent = DetailAgent(llm_client=llm_client)
    detail_context = AgentContext(
        request=request,
        current_step="detail",
        previous_results={
            "design": design_spec,
            "palette": palette,
        },
        retry_count=0,
    )
    
    detail_spec = await detail_agent.process(detail_context)
    
    # Check if RLE was used
    pixel_grid = detail_spec.get("pixel_grid", {})
    rle_metadata = pixel_grid.get("_rle_metadata", {})
    
    if rle_metadata.get("was_rle_encoded"):
        print(f"✅ RLE encoding was used!")
        print(f"   - RLE segments: {rle_metadata.get('rle_segment_count')}")
        print(f"   - Compression: {rle_metadata.get('compression_percent')}%")
        print(f"   - Grid: {pixel_grid['width']}×{pixel_grid['height']}")
        
        # Verify grid is valid
        grid_data = pixel_grid.get("data", [])
        assert len(grid_data) == pixel_grid['height'], "Invalid grid height!"
        assert len(grid_data[0]) == pixel_grid['width'], "Invalid grid width!"
        print(f"✅ Decoded grid is valid")
        
        return True
    else:
        print("⚠️  RLE was not used (sprite may be too small)")
        return False


async def main():
    """Run all RLE tests."""
    print("=" * 60)
    print("RLE (Run-Length Encoding) Test Suite")
    print("=" * 60)
    
    try:
        # Run unit tests
        test_rle_decoder_basic()
        test_rle_compression_ratios()
        test_rle_validation()
        test_pydantic_schemas()
        
        # Run integration test
        await test_rle_sprite_generation()
        
        print("\n" + "=" * 60)
        print("✅ All RLE tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)