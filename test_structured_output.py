"""Test script for Anthropic Structured Outputs implementation."""

import asyncio
from src.llm.client import create_llm_client
from src.agents.detail_schemas import DetailAgentOutput


async def test_structured_output():
    """Test structured output generation."""
    
    client = create_llm_client()
    
    # Simple test prompt
    test_prompt = """Create a simple 8x8 pixel grass tile sprite in Stardew Valley style.

PALETTE COLORS:
#228B22 (forest green), #32CD32 (lime green), #90EE90 (light green), #006400 (dark green)

SIZE: 8x8

Return the pixel grid with proper shading to create a grass texture."""
    
    print("Testing Anthropic Structured Outputs...")
    print("=" * 60)
    
    try:
        result = await client.create_structured_message(
            model="claude-sonnet-4-5",
            messages=[{"role": "user", "content": test_prompt}],
            output_format=DetailAgentOutput,
            max_tokens=4096,
            temperature=0.7,
        )
        
        print(f"✅ SUCCESS! Structured output received.")
        print(f"   - Grid size: {result.pixel_grid.width}x{result.pixel_grid.height}")
        print(f"   - Colors used: {len(result.final_specs.colors_used)}")
        print(f"   - Shading: {result.shading_details.shading_technique}")
        print(f"   - Readability: {result.final_specs.readability_score}")
        print(f"\nFirst 3 rows of pixel data:")
        for i, row in enumerate(result.pixel_grid.data[:3]):
            print(f"   Row {i}: {row[:8]}")
        
        # Verify all colors are valid 6-char hex
        all_colors = result.final_specs.colors_used
        invalid_colors = [c for c in all_colors if not (c.startswith('#') and len(c) == 7)]
        
        if invalid_colors:
            print(f"\n⚠️  WARNING: Found invalid color formats: {invalid_colors}")
        else:
            print(f"\n✅ All colors are valid 6-character hex codes!")
            
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_structured_output())
    exit(0 if success else 1)