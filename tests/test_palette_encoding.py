"""
Unit tests for palette indexing + RLE compression.

Tests the encode_with_palette and decode_palette_indexed functions,
as well as Pydantic schema validation for palette-indexed formats.
"""

import pytest
from pydantic import ValidationError

from src.rendering.palette_encoder import (
    encode_with_palette,
    decode_palette_indexed,
    validate_palette_indexed_data,
    calculate_palette_compression_ratio,
)
from src.agents.detail_schemas import (
    PaletteIndexSegment,
    PixelGridPaletteIndexed,
    DetailAgentOutputPaletteIndexed,
    ShadingDetails,
    FinalSpecs,
)


class TestPaletteEncoding:
    """Test palette indexing encoding/decoding."""
    
    def test_encode_decode_roundtrip_basic(self):
        """Test basic encode/decode produces identical output."""
        # Create 4×4 grid with 3 colors
        grid = [
            ['#FF0000', '#FF0000', '#00FF00', '#00FF00'],
            ['#FF0000', '#FF0000', '#00FF00', '#00FF00'],
            ['#0000FF', '#0000FF', 'transparent', 'transparent'],
            ['#0000FF', '#0000FF', 'transparent', 'transparent']
        ]
        
        # Encode
        encoded = encode_with_palette(grid, max_colors=16)
        
        # Verify encoding structure
        assert encoded['encoding'] == 'palette_indexed_rle'
        assert encoded['width'] == 4
        assert encoded['height'] == 4
        assert len(encoded['palette']) == 3  # 3 unique colors
        assert '#FF0000' in encoded['palette']
        assert '#00FF00' in encoded['palette']
        assert '#0000FF' in encoded['palette']
        
        # Decode
        decoded = decode_palette_indexed(
            width=encoded['width'],
            height=encoded['height'],
            palette=encoded['palette'],
            data=encoded['data']
        )
        
        # Verify roundtrip is lossless
        assert decoded == grid
    
    def test_encode_decode_roundtrip_16x16(self):
        """Test roundtrip on 16×16 sprite."""
        # Create checkerboard pattern with 8 colors
        colors = [
            '#FF0000', '#00FF00', '#0000FF', '#FFFF00',
            '#FF00FF', '#00FFFF', '#FFFFFF', '#000000'
        ]
        
        grid = []
        for y in range(16):
            row = []
            for x in range(16):
                color_idx = (y * 16 + x) % len(colors)
                row.append(colors[color_idx])
            grid.append(row)
        
        # Encode
        encoded = encode_with_palette(grid, max_colors=16)
        
        # Decode
        decoded = decode_palette_indexed(
            width=16,
            height=16,
            palette=encoded['palette'],
            data=encoded['data']
        )
        
        # Verify lossless
        assert decoded == grid
    
    def test_compression_solid_color(self):
        """Test compression on solid color grid."""
        # 16×16 solid red
        grid = [['#FF0000'] * 16 for _ in range(16)]
        
        encoded = encode_with_palette(grid)
        
        # Should compress to 1 palette entry + 1 RLE segment
        assert len(encoded['palette']) == 1
        assert len(encoded['data']) == 1
        assert encoded['data'][0]['count'] == 256
        
        # Verify high compression
        metadata = encoded['_metadata']
        assert metadata['compression_percent'] > 99.0
    
    def test_compression_two_colors(self):
        """Test compression on two-color pattern."""
        # 16×16 checkerboard (worst case for RLE)
        grid = []
        for y in range(16):
            row = []
            for x in range(16):
                color = '#FF0000' if (x + y) % 2 == 0 else '#00FF00'
                row.append(color)
            grid.append(row)
        
        encoded = encode_with_palette(grid)
        
        # Should have 2 palette entries
        assert len(encoded['palette']) == 2
        
        # Many segments due to alternating pattern
        # But still better than standard grid
        assert len(encoded['data']) > 100  # Many segments
        assert len(encoded['data']) < 256  # But not every pixel
    
    def test_compression_horizontal_stripes(self):
        """Test compression on horizontal stripes (good for RLE)."""
        # 16×16 with 4-row horizontal stripes (4 colors)
        # Create 4 blocks of 4 rows each with same color
        colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00']
        grid = []
        for y in range(16):
            color = colors[y // 4]  # Changed from y%4 to y//4 for contiguous blocks
            grid.append([color] * 16)
        
        encoded = encode_with_palette(grid)
        
        # Should have 4 palette entries and 4 RLE segments (one per 4-row stripe)
        assert len(encoded['palette']) == 4
        assert len(encoded['data']) == 4  # One segment per stripe
        
        # Each segment should be 64 pixels (4 rows × 16 cols)
        for segment in encoded['data']:
            assert segment['count'] == 64
        
        # Very good compression
        metadata = encoded['_metadata']
        assert metadata['compression_percent'] > 95.0
    
    def test_encode_with_transparent(self):
        """Test encoding with transparent pixels."""
        # 4×4 grid with transparent regions
        grid = [
            ['#FF0000', '#FF0000', 'transparent', 'transparent'],
            ['#FF0000', '#FF0000', 'transparent', 'transparent'],
            ['#00FF00', '#00FF00', 'transparent', 'transparent'],
            ['#00FF00', '#00FF00', 'transparent', 'transparent']
        ]
        
        encoded = encode_with_palette(grid)
        
        # Palette should have 2 colors (not including transparent)
        assert len(encoded['palette']) == 2
        
        # Decode and verify
        decoded = decode_palette_indexed(
            width=4,
            height=4,
            palette=encoded['palette'],
            data=encoded['data']
        )
        
        assert decoded == grid
    
    def test_encode_too_many_colors(self):
        """Test that encoding fails when exceeding max colors."""
        # Create grid with 20 unique colors
        grid = []
        for y in range(4):
            row = []
            for x in range(5):
                color_num = y * 5 + x
                color = f'#{color_num:02x}{color_num:02x}{color_num:02x}'
                row.append(color)
            grid.append(row)
        
        # Should fail with max_colors=16
        with pytest.raises(ValueError) as exc_info:
            encode_with_palette(grid, max_colors=16)
        
        assert "Too many unique colors" in str(exc_info.value)
    
    def test_encode_empty_grid(self):
        """Test encoding empty grid."""
        grid = []
        
        encoded = encode_with_palette(grid)
        
        assert encoded['width'] == 0
        assert encoded['height'] == 0
        assert encoded['palette'] == []
        assert encoded['data'] == []
    
    def test_decode_with_auto_correct(self):
        """Test decoder auto-correction for pixel count mismatches."""
        palette = ['#FF0000', '#00FF00']
        
        # Data with too few pixels (15 instead of 16)
        data = [
            {'idx': 0, 'count': 8},
            {'idx': 1, 'count': 7}  # Missing 1 pixel
        ]
        
        # Should auto-correct by padding (with 10% tolerance)
        decoded = decode_palette_indexed(
            width=4,
            height=4,
            palette=palette,
            data=data,
            auto_correct=True,
            tolerance=0.10  # 10% tolerance (6.2% deviation should pass)
        )
        
        # Verify dimensions
        assert len(decoded) == 4
        assert all(len(row) == 4 for row in decoded)
        
        # Last pixel should be padded with last color (#00FF00)
        assert decoded[3][3] == '#00FF00'
    
    def test_decode_without_auto_correct(self):
        """Test decoder rejects mismatches when auto_correct=False."""
        palette = ['#FF0000']
        data = [{'idx': 0, 'count': 15}]  # Too few
        
        with pytest.raises(ValueError) as exc_info:
            decode_palette_indexed(
                width=4,
                height=4,
                palette=palette,
                data=data,
                auto_correct=False
            )
        
        assert "pixel count mismatch" in str(exc_info.value).lower()


class TestPaletteValidation:
    """Test palette data validation."""
    
    def test_validate_correct_data(self):
        """Test validation passes for correct data."""
        palette = ['#FF0000', '#00FF00']
        data = [
            {'idx': 0, 'count': 8},
            {'idx': 1, 'count': 8}
        ]
        
        is_valid, errors = validate_palette_indexed_data(4, 4, palette, data)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_invalid_palette_size(self):
        """Test validation fails for oversized palette."""
        palette = [f'#{i:02x}{i:02x}{i:02x}' for i in range(256)]  # Too many
        data = [{'idx': 0, 'count': 16}]
        
        is_valid, errors = validate_palette_indexed_data(4, 4, palette, data)
        
        assert not is_valid
        assert any('too large' in err.lower() for err in errors)
    
    def test_validate_invalid_palette_colors(self):
        """Test validation fails for invalid hex colors."""
        palette = ['#FF0000', 'invalid', '#00FF00']
        data = [{'idx': 0, 'count': 16}]
        
        is_valid, errors = validate_palette_indexed_data(4, 4, palette, data)
        
        assert not is_valid
        assert any('invalid' in str(err).lower() for err in errors)
    
    def test_validate_pixel_count_mismatch(self):
        """Test validation fails for pixel count mismatch."""
        palette = ['#FF0000']
        data = [{'idx': 0, 'count': 20}]  # Too many
        
        is_valid, errors = validate_palette_indexed_data(4, 4, palette, data)
        
        assert not is_valid
        assert any('mismatch' in err.lower() for err in errors)
    
    def test_validate_invalid_index(self):
        """Test validation fails for out-of-bounds index."""
        palette = ['#FF0000', '#00FF00']
        data = [
            {'idx': 0, 'count': 8},
            {'idx': 5, 'count': 8}  # Index 5 > palette size
        ]
        
        is_valid, errors = validate_palette_indexed_data(4, 4, palette, data)
        
        assert not is_valid
        assert any('out of' in err.lower() for err in errors)
    
    def test_validate_negative_count(self):
        """Test validation fails for negative count."""
        palette = ['#FF0000']
        data = [{'idx': 0, 'count': -1}]
        
        is_valid, errors = validate_palette_indexed_data(4, 4, palette, data)
        
        assert not is_valid
        assert any('positive' in err.lower() for err in errors)


class TestPydanticSchemas:
    """Test Pydantic schema validation."""
    
    def test_palette_index_segment_valid(self):
        """Test valid PaletteIndexSegment creation."""
        segment = PaletteIndexSegment(idx=0, count=50)
        
        assert segment.idx == 0
        assert segment.count == 50
    
    def test_palette_index_segment_invalid_idx(self):
        """Test PaletteIndexSegment rejects invalid index."""
        with pytest.raises(ValidationError):
            PaletteIndexSegment(idx=256, count=10)  # Max is 255
        
        with pytest.raises(ValidationError):
            PaletteIndexSegment(idx=-1, count=10)
    
    def test_palette_index_segment_invalid_count(self):
        """Test PaletteIndexSegment rejects invalid count."""
        with pytest.raises(ValidationError):
            PaletteIndexSegment(idx=0, count=0)  # Must be >= 1
        
        with pytest.raises(ValidationError):
            PaletteIndexSegment(idx=0, count=5000)  # Max is 4096
    
    def test_pixel_grid_palette_indexed_valid(self):
        """Test valid PixelGridPaletteIndexed creation."""
        grid = PixelGridPaletteIndexed(
            width=16,
            height=16,
            encoding="palette_indexed_rle",
            palette=["#FF0000", "#00FF00", "#0000FF"],
            data=[
                PaletteIndexSegment(idx=0, count=85),
                PaletteIndexSegment(idx=1, count=85),
                PaletteIndexSegment(idx=2, count=86)
            ]
        )
        
        assert grid.width == 16
        assert grid.height == 16
        assert len(grid.palette) == 3
        assert len(grid.data) == 3
    
    def test_pixel_grid_palette_indexed_too_many_colors(self):
        """Test PixelGridPaletteIndexed rejects oversized palette."""
        with pytest.raises(ValidationError):
            PixelGridPaletteIndexed(
                width=16,
                height=16,
                encoding="palette_indexed_rle",
                palette=[f'#{i:02x}{i:02x}{i:02x}' for i in range(256)],  # Too many
                data=[]
            )
    
    def test_detail_agent_output_palette_indexed(self):
        """Test DetailAgentOutputPaletteIndexed validation."""
        output = DetailAgentOutputPaletteIndexed(
            pixel_grid=PixelGridPaletteIndexed(
                width=8,
                height=8,
                encoding="palette_indexed_rle",
                palette=["#FF0000", "#00FF00"],
                data=[
                    PaletteIndexSegment(idx=0, count=32),
                    PaletteIndexSegment(idx=1, count=32)
                ]
            ),
            shading_details=ShadingDetails(
                light_source="top-left",
                shading_technique="cel-shading",
                contrast_level="medium"
            ),
            final_specs=FinalSpecs(
                colors_used=["#FF0000", "#00FF00"],
                total_pixels=64,
                readability_score="high"
            )
        )
        
        assert output.pixel_grid.width == 8
        assert len(output.pixel_grid.palette) == 2


class TestCompressionMetrics:
    """Test compression ratio calculations."""
    
    def test_calculate_compression_vs_grid(self):
        """Test compression metrics vs standard grid."""
        metrics = calculate_palette_compression_ratio(
            palette_size=8,
            segment_count=60,
            width=16,
            height=16
        )
        
        # Should show significant compression vs standard grid
        assert metrics['vs_grid_percent'] > 60.0
        assert metrics['vs_grid_ratio'] < 0.4
    
    def test_calculate_compression_vs_rle(self):
        """Test compression metrics vs standard RLE."""
        metrics = calculate_palette_compression_ratio(
            palette_size=8,
            segment_count=60,
            width=16,
            height=16
        )
        
        # Should show improvement vs standard RLE (30-40% is realistic)
        assert metrics['vs_standard_rle_percent'] > 30.0
        assert metrics['vs_standard_rle_ratio'] < 0.7
    
    def test_calculate_compression_best_case(self):
        """Test compression metrics for best case (solid color)."""
        metrics = calculate_palette_compression_ratio(
            palette_size=1,
            segment_count=1,
            width=32,
            height=32
        )
        
        # Should show >95% compression
        assert metrics['vs_grid_percent'] > 95.0
        assert metrics['estimated_tokens'] < 50


def test_integration_full_workflow():
    """Integration test: encode, validate, decode full workflow."""
    # Create 16×16 sprite with 6 colors
    colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF']
    grid = []
    for y in range(16):
        row = []
        for x in range(16):
            # Create horizontal stripes
            color_idx = (y // 3) % len(colors)
            row.append(colors[color_idx])
        grid.append(row)
    
    # Step 1: Encode
    encoded = encode_with_palette(grid, max_colors=16)
    
    assert encoded['encoding'] == 'palette_indexed_rle'
    assert len(encoded['palette']) == 6
    
    # Step 2: Validate
    is_valid, errors = validate_palette_indexed_data(
        width=encoded['width'],
        height=encoded['height'],
        palette=encoded['palette'],
        data=encoded['data']
    )
    
    assert is_valid, f"Validation failed: {errors}"
    
    # Step 3: Decode
    decoded = decode_palette_indexed(
        width=encoded['width'],
        height=encoded['height'],
        palette=encoded['palette'],
        data=encoded['data']
    )
    
    # Step 4: Verify lossless
    assert decoded == grid
    
    # Step 5: Check compression
    metadata = encoded['_metadata']
    assert metadata['compression_percent'] > 85.0  # Should achieve good compression


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])