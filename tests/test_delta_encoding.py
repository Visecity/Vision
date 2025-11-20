"""
Unit tests for delta encoding animation compression.

Tests cover encoding, decoding, validation, compression metrics,
and integration with Pydantic schemas.
"""

import pytest
from src.rendering.delta_encoder import (
    encode_animation_with_deltas,
    decode_delta_animation,
    calculate_delta_compression_ratio,
    validate_delta_data,
    analyze_animation_deltas,
)
from src.agents.detail_schemas import (
    AnimationDelta,
    FrameDelta,
    PixelChange,
    AnimationAgentOutputDelta,
)


class TestDeltaEncoding:
    """Test delta encoding of animation frames."""
    
    def test_encode_simple_animation(self):
        """Test encoding a simple 2-frame animation."""
        frames = [
            [['#FF0000', '#FF0000'], ['#00FF00', '#00FF00']],  # Frame 0
            [['#FF0000', '#0000FF'], ['#00FF00', '#00FF00']],  # Frame 1 (1 pixel changed)
        ]
        
        encoded = encode_animation_with_deltas(frames)
        
        assert encoded['width'] == 2
        assert encoded['height'] == 2
        assert encoded['frame_count'] == 2
        assert encoded['encoding'] == 'delta'
        assert len(encoded['deltas']) == 1
        assert len(encoded['deltas'][0]['changes']) == 1
        assert encoded['deltas'][0]['changes'][0] == {'x': 1, 'y': 0, 'color': '#0000FF'}
    
    def test_encode_no_changes(self):
        """Test encoding animation with identical frames (no changes)."""
        frames = [
            [['#FF0000'] * 4] * 4,
            [['#FF0000'] * 4] * 4,
        ]
        
        encoded = encode_animation_with_deltas(frames)
        
        assert len(encoded['deltas']) == 1
        assert len(encoded['deltas'][0]['changes']) == 0
        assert encoded['_metadata']['total_changes'] == 0
        # 2 frames, 16 pixels each: 32 uncompressed → 16 compressed (1 keyframe) = 50% compression
        assert encoded['_metadata']['compression_percent'] == 50.0
    
    def test_encode_all_pixels_change(self):
        """Test encoding animation where all pixels change."""
        frames = [
            [['#FF0000', '#FF0000'], ['#00FF00', '#00FF00']],
            [['#0000FF', '#0000FF'], ['#FFFF00', '#FFFF00']],
        ]
        
        encoded = encode_animation_with_deltas(frames, auto_optimize=True)
        
        # All 4 pixels changed - should insert keyframe due to auto-optimization
        assert encoded['deltas'][0]['is_keyframe'] == True
        assert 'frame_data' in encoded['deltas'][0]
    
    def test_encode_multiple_frames(self):
        """Test encoding multi-frame animation."""
        frames = [
            [['#FF0000'] * 4] * 4,  # Frame 0: all red
            [['#00FF00'] * 4] * 4,  # Frame 1: all green (16 changes)
            [['#00FF00'] * 4] * 4,  # Frame 2: no change
            [['#0000FF'] * 4] * 4,  # Frame 3: all blue (16 changes)
        ]
        
        encoded = encode_animation_with_deltas(frames)
        
        assert encoded['frame_count'] == 4
        assert len(encoded['deltas']) == 3
        
        # Frame 1 should have 16 changes (all pixels)
        # But auto-optimize should make it a keyframe (>50% changed)
        assert encoded['deltas'][0]['is_keyframe'] == True
        
        # Frame 2 should have 0 changes
        assert encoded['deltas'][1]['is_keyframe'] == False
        assert len(encoded['deltas'][1]['changes']) == 0
    
    def test_encode_keyframe_interval(self):
        """Test forced keyframe insertion at intervals."""
        frames = [
            [['#FF0000'] * 2] * 2,  # Frame 0
            [['#FF0001'] * 2] * 2,  # Frame 1 (small change)
            [['#FF0002'] * 2] * 2,  # Frame 2 (small change)
            [['#FF0003'] * 2] * 2,  # Frame 3 (small change)
        ]
        
        encoded = encode_animation_with_deltas(frames, keyframe_interval=2)
        
        # Frame 2 should be forced keyframe
        assert encoded['deltas'][1]['frame_index'] == 2
        assert encoded['deltas'][1]['is_keyframe'] == True


class TestDeltaDecoding:
    """Test delta decoding back to full frames."""
    
    def test_decode_simple_animation(self):
        """Test decoding a simple animation."""
        keyframe = [['#FF0000', '#FF0000'], ['#00FF00', '#00FF00']]
        deltas = [
            {
                'frame_index': 1,
                'is_keyframe': False,
                'changes': [{'x': 1, 'y': 0, 'color': '#0000FF'}]
            }
        ]
        
        frames = decode_delta_animation(2, 2, keyframe, deltas)
        
        assert len(frames) == 2
        assert frames[0] == keyframe
        assert frames[1][0][1] == '#0000FF'  # Changed pixel
        assert frames[1][0][0] == '#FF0000'  # Unchanged pixel
    
    def test_decode_no_changes(self):
        """Test decoding animation with no changes."""
        keyframe = [['#FF0000'] * 4] * 4
        deltas = [
            {
                'frame_index': 1,
                'is_keyframe': False,
                'changes': []
            }
        ]
        
        frames = decode_delta_animation(4, 4, keyframe, deltas)
        
        assert len(frames) == 2
        assert frames[0] == frames[1]  # Identical frames
    
    def test_decode_with_keyframe(self):
        """Test decoding animation with embedded keyframe."""
        keyframe = [['#FF0000'] * 2] * 2
        deltas = [
            {
                'frame_index': 1,
                'is_keyframe': True,
                'frame_data': [['#00FF00'] * 2] * 2,
                'changes': []
            },
            {
                'frame_index': 2,
                'is_keyframe': False,
                'changes': [{'x': 0, 'y': 0, 'color': '#0000FF'}]
            }
        ]
        
        frames = decode_delta_animation(2, 2, keyframe, deltas)
        
        assert len(frames) == 3
        assert frames[1] == [['#00FF00'] * 2] * 2  # Keyframe
        assert frames[2][0][0] == '#0000FF'  # Change applied to keyframe
    
    def test_decode_multiple_changes(self):
        """Test decoding frame with multiple pixel changes."""
        keyframe = [['#000000', '#000000'], ['#000000', '#000000']]
        deltas = [
            {
                'frame_index': 1,
                'is_keyframe': False,
                'changes': [
                    {'x': 0, 'y': 0, 'color': '#FF0000'},
                    {'x': 1, 'y': 1, 'color': '#00FF00'},
                ]
            }
        ]
        
        frames = decode_delta_animation(2, 2, keyframe, deltas)
        
        assert frames[1][0][0] == '#FF0000'
        assert frames[1][1][1] == '#00FF00'
        assert frames[1][0][1] == '#000000'  # Unchanged


class TestLosslessRoundtrip:
    """Test that encoding and decoding is lossless."""
    
    def test_roundtrip_simple(self):
        """Test lossless roundtrip for simple animation."""
        original_frames = [
            [['#FF0000', '#FF0000'], ['#00FF00', '#00FF00']],
            [['#FF0000', '#0000FF'], ['#00FF00', '#00FF00']],
        ]
        
        # Encode
        encoded = encode_animation_with_deltas(original_frames)
        
        # Decode
        decoded_frames = decode_delta_animation(
            encoded['width'],
            encoded['height'],
            encoded['keyframe'],
            encoded['deltas']
        )
        
        # Verify lossless
        assert len(decoded_frames) == len(original_frames)
        for i, (original, decoded) in enumerate(zip(original_frames, decoded_frames)):
            assert original == decoded, f"Frame {i} mismatch"
    
    def test_roundtrip_complex(self):
        """Test lossless roundtrip for complex multi-frame animation."""
        original_frames = [
            [['#FF0000'] * 4] * 4,
            [['#00FF00'] * 4] * 4,
            [['#00FF00'] * 4] * 4,
            [['#0000FF'] * 4] * 4,
            [['#0000FF', '#0000FF', '#FFFF00', '#FFFF00']] * 4,
        ]
        
        # Encode
        encoded = encode_animation_with_deltas(original_frames, auto_optimize=True)
        
        # Decode
        decoded_frames = decode_delta_animation(
            encoded['width'],
            encoded['height'],
            encoded['keyframe'],
            encoded['deltas']
        )
        
        # Verify lossless
        assert len(decoded_frames) == len(original_frames)
        for i, (original, decoded) in enumerate(zip(original_frames, decoded_frames)):
            assert original == decoded, f"Frame {i} mismatch"


class TestCompressionMetrics:
    """Test compression ratio calculations."""
    
    def test_perfect_compression(self):
        """Test metrics for animation with no changes (perfect compression)."""
        metrics = calculate_delta_compression_ratio(
            frame_count=10,
            width=16,
            height=16,
            total_changes=0,
            keyframe_count=1
        )
        
        assert metrics['compression_percent'] == 90.0  # Only 1 keyframe out of 10 frames
        assert metrics['avg_changes_per_frame'] == 0
    
    def test_moderate_compression(self):
        """Test metrics for animation with moderate changes."""
        # 10 frames, 16×16, average 32 changes per frame
        metrics = calculate_delta_compression_ratio(
            frame_count=10,
            width=16,
            height=16,
            total_changes=288,  # 32 changes × 9 frames (1 keyframe)
            keyframe_count=1
        )
        
        # 256 pixels × 10 frames = 2560 uncompressed
        # 256 (keyframe) + 288 (changes) = 544 compressed
        # Compression: (1 - 544/2560) × 100 = 78.75%
        assert metrics['compression_percent'] == 78.8
        assert metrics['avg_changes_per_frame'] == 32.0
    
    def test_poor_compression(self):
        """Test metrics when most pixels change (poor compression)."""
        metrics = calculate_delta_compression_ratio(
            frame_count=5,
            width=16,
            height=16,
            total_changes=1024,  # 256 changes × 4 frames
            keyframe_count=1
        )
        
        # All pixels change in each frame - no compression benefit
        assert metrics['compression_percent'] == 0.0
    
    def test_multiple_keyframes(self):
        """Test metrics with multiple keyframes."""
        metrics = calculate_delta_compression_ratio(
            frame_count=10,
            width=16,
            height=16,
            total_changes=256,  # ~32 changes per non-keyframe
            keyframe_count=3  # 3 keyframes
        )
        
        # 3 keyframes (768 pixels) + 256 changes = 1024 compressed
        # 2560 uncompressed
        # Compression: (1 - 1024/2560) × 100 = 60%
        assert metrics['compression_percent'] == 60.0


class TestValidation:
    """Test delta data validation."""
    
    def test_validate_correct_data(self):
        """Test validation of correct delta data."""
        keyframe = [['#FF0000', '#FF0000'], ['#00FF00', '#00FF00']]
        deltas = [
            {
                'frame_index': 1,
                'is_keyframe': False,
                'changes': [{'x': 1, 'y': 0, 'color': '#0000FF'}]
            }
        ]
        
        is_valid, errors = validate_delta_data(2, 2, keyframe, deltas)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_keyframe_height_mismatch(self):
        """Test validation catches keyframe dimension mismatch."""
        keyframe = [['#FF0000'] * 2]  # Only 1 row instead of 2
        deltas = []
        
        is_valid, errors = validate_delta_data(2, 2, keyframe, deltas)
        
        assert not is_valid
        assert any('height mismatch' in err for err in errors)
    
    def test_validate_coordinates_out_of_bounds(self):
        """Test validation catches out-of-bounds coordinates."""
        keyframe = [['#FF0000', '#FF0000'], ['#00FF00', '#00FF00']]
        deltas = [
            {
                'frame_index': 1,
                'is_keyframe': False,
                'changes': [{'x': 5, 'y': 0, 'color': '#0000FF'}]  # x=5 out of bounds
            }
        ]
        
        is_valid, errors = validate_delta_data(2, 2, keyframe, deltas)
        
        assert not is_valid
        assert any('out of bounds' in err for err in errors)
    
    def test_validate_missing_changes_field(self):
        """Test validation catches missing required fields."""
        keyframe = [['#FF0000'] * 2] * 2
        deltas = [
            {
                'frame_index': 1,
                'is_keyframe': False,
                # Missing 'changes' field
            }
        ]
        
        is_valid, errors = validate_delta_data(2, 2, keyframe, deltas)
        
        assert not is_valid
        assert any('missing' in err.lower() for err in errors)


class TestAnalysis:
    """Test animation delta analysis."""
    
    def test_analyze_identical_frames(self):
        """Test analysis of animation with identical frames."""
        frames = [
            [['#FF0000'] * 4] * 4,
            [['#FF0000'] * 4] * 4,
            [['#FF0000'] * 4] * 4,
        ]
        
        analysis = analyze_animation_deltas(frames)
        
        assert analysis['avg_changes_per_frame'] == 0.0
        assert analysis['max_changes'] == 0
        assert analysis['min_changes'] == 0
        # 3 frames, no changes: 48 uncompressed → 16 compressed = 66.7% compression
        assert analysis['estimated_compression'] == 66.7
        assert analysis['recommendation'] == 'use_delta'
    
    def test_analyze_small_changes(self):
        """Test analysis of animation with small changes."""
        frames = [
            [['#FF0000'] * 4] * 4,  # Frame 0
            [['#FF0001'] * 4] * 4,  # Frame 1 (all pixels slightly changed)
        ]
        
        analysis = analyze_animation_deltas(frames)
        
        assert analysis['avg_changes_per_frame'] == 16.0  # All 16 pixels changed
        assert analysis['avg_change_percentage'] == 100.0  # All pixels changed
        # When 100% of pixels change, full frames are better than delta
        assert analysis['recommendation'] == 'use_full_frames'
    
    def test_analyze_large_changes(self):
        """Test analysis of animation with large changes."""
        frames = [
            [['#FF0000'] * 4] * 4,  # Frame 0: all red
            [['#00FF00'] * 4] * 4,  # Frame 1: all green (all changed)
            [['#0000FF'] * 4] * 4,  # Frame 2: all blue (all changed)
        ]
        
        analysis = analyze_animation_deltas(frames)
        
        assert analysis['avg_changes_per_frame'] == 16.0  # 100% change
        assert analysis['avg_change_percentage'] == 100.0
        assert analysis['recommendation'] == 'use_full_frames'
    
    def test_analyze_mixed_changes(self):
        """Test analysis with varying change rates."""
        frames = [
            [['#FF0000'] * 4] * 4,  # Frame 0
            [['#FF0000', '#FF0000', '#FF0000', '#00FF00']] * 4,  # Frame 1: 4 changes
            [['#FF0000', '#FF0000', '#FF0000', '#00FF00']] * 4,  # Frame 2: 0 changes
        ]
        
        analysis = analyze_animation_deltas(frames)
        
        assert analysis['avg_changes_per_frame'] == 2.0  # (4 + 0) / 2
        assert analysis['max_changes'] == 4
        assert analysis['min_changes'] == 0


class TestPydanticSchemas:
    """Test Pydantic schema validation for delta encoding."""
    
    def test_pixel_change_schema(self):
        """Test PixelChange schema validation."""
        change = PixelChange(x=5, y=10, color='#FF0000')
        
        assert change.x == 5
        assert change.y == 10
        assert change.color == '#FF0000'
    
    def test_pixel_change_invalid_color(self):
        """Test PixelChange rejects invalid color."""
        with pytest.raises(ValueError):
            PixelChange(x=0, y=0, color='invalid')
    
    def test_frame_delta_schema(self):
        """Test FrameDelta schema validation."""
        delta = FrameDelta(
            frame_index=1,
            is_keyframe=False,
            changes=[
                PixelChange(x=0, y=0, color='#FF0000'),
                PixelChange(x=1, y=1, color='#00FF00'),
            ]
        )
        
        assert delta.frame_index == 1
        assert not delta.is_keyframe
        assert len(delta.changes) == 2
    
    def test_frame_delta_keyframe(self):
        """Test FrameDelta with keyframe data."""
        delta = FrameDelta(
            frame_index=5,
            is_keyframe=True,
            frame_data=[['#FF0000'] * 4] * 4,
            changes=[]
        )
        
        assert delta.is_keyframe
        assert delta.frame_data is not None
        assert len(delta.changes) == 0
    
    def test_animation_delta_schema(self):
        """Test AnimationDelta schema validation."""
        anim = AnimationDelta(
            width=4,
            height=4,
            frame_count=2,
            keyframe=[['#FF0000'] * 4] * 4,
            deltas=[
                FrameDelta(
                    frame_index=1,
                    is_keyframe=False,
                    changes=[PixelChange(x=0, y=0, color='#00FF00')]
                )
            ]
        )
        
        assert anim.width == 4
        assert anim.height == 4
        assert anim.frame_count == 2
        assert anim.encoding == 'delta'
        assert len(anim.deltas) == 1
    
    def test_animation_agent_output_schema(self):
        """Test complete AnimationAgentOutputDelta schema."""
        output = AnimationAgentOutputDelta(
            animation=AnimationDelta(
                width=4,
                height=4,
                frame_count=2,
                keyframe=[['#FF0000'] * 4] * 4,
                deltas=[
                    FrameDelta(
                        frame_index=1,
                        is_keyframe=False,
                        changes=[]
                    )
                ]
            ),
            animation_specs={'fps': 12, 'loop': True},
            implementation_notes='Simple 2-frame animation'
        )
        
        assert output.animation.frame_count == 2
        assert output.animation_specs['fps'] == 12
        assert output.implementation_notes is not None


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_encode_empty_frames(self):
        """Test encoding with empty frames list."""
        with pytest.raises(ValueError, match="empty"):
            encode_animation_with_deltas([])
    
    def test_encode_single_frame(self):
        """Test encoding with single frame (requires at least 2)."""
        with pytest.raises(ValueError, match="at least 2 frames"):
            encode_animation_with_deltas([[['#FF0000']]])
    
    def test_decode_invalid_coordinates(self):
        """Test decoding with invalid change coordinates."""
        keyframe = [['#FF0000'] * 2] * 2
        deltas = [
            {
                'frame_index': 1,
                'is_keyframe': False,
                'changes': [{'x': 10, 'y': 10, 'color': '#0000FF'}]  # Out of bounds
            }
        ]
        
        with pytest.raises(ValueError, match="out of bounds"):
            decode_delta_animation(2, 2, keyframe, deltas)
    
    def test_decode_missing_keyframe_data(self):
        """Test decoding keyframe delta without frame_data."""
        keyframe = [['#FF0000'] * 2] * 2
        deltas = [
            {
                'frame_index': 1,
                'is_keyframe': True,
                # Missing frame_data
            }
        ]
        
        with pytest.raises(ValueError, match="missing frame_data"):
            decode_delta_animation(2, 2, keyframe, deltas)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])