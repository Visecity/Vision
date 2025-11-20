"""
Tests for manifest rendering functionality.

Tests the ManifestRenderer class and related functions to ensure
proper rendering of Vision Manifest JSON to PNG files.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.rendering.manifest_renderer import (
    ManifestRenderer,
    ManifestParseError,
    render_animation_frames,
    quick_render,
)
from src.rendering.pixel import Color, PixelGrid


# Sample valid manifest for testing
VALID_MANIFEST = {
    "version": "1.0",
    "metadata": {
        "name": "Test Sprite",
        "description": "A test sprite",
        "canvas": {"width": 16, "height": 16},
    },
    "layers": [
        {
            "name": "Layer 1",
            "elements": [
                {"type": "rect", "x": 4, "y": 4, "width": 8, "height": 8, "fill": "#FF0000"},
                {"type": "pixel", "x": 8, "y": 8, "fill": "#00FF00"},
            ],
        }
    ],
}


ANIMATION_MANIFEST = {
    "version": "1.0",
    "metadata": {
        "name": "Test Animation",
        "canvas": {"width": 32, "height": 16},
    },
    "layers": [
        {
            "name": "Frame 0",
            "elements": [
                {"type": "rect", "x": 0, "y": 0, "width": 16, "height": 16, "fill": "#FF0000"},
            ],
        },
        {
            "name": "Frame 1",
            "elements": [
                {"type": "rect", "x": 16, "y": 0, "width": 16, "height": 16, "fill": "#00FF00"},
            ],
        },
    ],
}


class TestManifestRenderer:
    """Tests for ManifestRenderer class."""

    def test_init_default(self):
        """Test renderer initialization with defaults."""
        renderer = ManifestRenderer()
        assert renderer.scale == 1
        assert renderer.include_metadata == True

    def test_init_custom(self):
        """Test renderer initialization with custom values."""
        renderer = ManifestRenderer(scale=2, include_metadata=False)
        assert renderer.scale == 2
        assert renderer.include_metadata == False

    def test_init_invalid_scale(self):
        """Test that invalid scale raises ValueError."""
        with pytest.raises(ValueError, match="Scale must be between"):
            ManifestRenderer(scale=0)
        
        with pytest.raises(ValueError, match="Scale must be between"):
            ManifestRenderer(scale=20)

    def test_validate_manifest_valid(self):
        """Test validation of valid manifest."""
        renderer = ManifestRenderer()
        # Should not raise
        renderer._validate_manifest(VALID_MANIFEST)

    def test_validate_manifest_not_dict(self):
        """Test validation fails for non-dict."""
        renderer = ManifestRenderer()
        with pytest.raises(ManifestParseError, match="must be a dictionary"):
            renderer._validate_manifest("not a dict")

    def test_validate_manifest_missing_metadata(self):
        """Test validation fails without metadata."""
        renderer = ManifestRenderer()
        manifest = {"layers": []}
        with pytest.raises(ManifestParseError, match="missing 'metadata'"):
            renderer._validate_manifest(manifest)

    def test_validate_manifest_missing_canvas(self):
        """Test validation fails without canvas."""
        renderer = ManifestRenderer()
        manifest = {"metadata": {}}
        with pytest.raises(ManifestParseError, match="missing 'canvas'"):
            renderer._validate_manifest(manifest)

    def test_validate_manifest_missing_dimensions(self):
        """Test validation fails without width/height."""
        renderer = ManifestRenderer()
        manifest = {"metadata": {"canvas": {"width": 16}}}
        with pytest.raises(ManifestParseError, match="missing 'width' or 'height'"):
            renderer._validate_manifest(manifest)

    def test_validate_manifest_no_layers_or_frames(self):
        """Test validation fails without layers or frames."""
        renderer = ManifestRenderer()
        manifest = {
            "metadata": {"canvas": {"width": 16, "height": 16}}
        }
        with pytest.raises(ManifestParseError, match="must have either 'layers' or 'frames'"):
            renderer._validate_manifest(manifest)

    def test_parse_color_valid(self):
        """Test parsing valid hex colors."""
        renderer = ManifestRenderer()
        
        color = renderer._parse_color("#FF0000")
        assert color.r == 255
        assert color.g == 0
        assert color.b == 0

        color = renderer._parse_color("#00FF00")
        assert color.r == 0
        assert color.g == 255
        assert color.b == 0

    def test_parse_color_invalid(self):
        """Test parsing invalid color raises error."""
        renderer = ManifestRenderer()
        with pytest.raises(ManifestParseError, match="Invalid color"):
            renderer._parse_color("not-a-color")

    def test_extract_metadata(self):
        """Test metadata extraction from manifest."""
        renderer = ManifestRenderer()
        metadata = renderer._extract_metadata(VALID_MANIFEST)
        
        assert "vision_manifest_version" in metadata
        assert metadata["vision_manifest_version"] == "1.0"
        assert "asset_name" in metadata
        assert metadata["asset_name"] == "Test Sprite"
        assert "canvas_size" in metadata
        assert metadata["canvas_size"] == "16x16"

    def test_render_rect_element(self):
        """Test rendering rectangle element."""
        renderer = ManifestRenderer()
        grid = PixelGrid(16, 16)
        ctx = Mock()
        ctx.draw_rect = Mock()
        
        element = {"type": "rect", "x": 4, "y": 4, "width": 8, "height": 8, "fill": "#FF0000"}
        
        with patch('src.rendering.manifest_renderer.DrawingContext', return_value=ctx):
            renderer._render_rect(ctx, element)
            ctx.draw_rect.assert_called_once()

    def test_render_pixel_element(self):
        """Test rendering pixel element."""
        renderer = ManifestRenderer()
        ctx = Mock()
        ctx.draw_pixel = Mock()
        
        element = {"type": "pixel", "x": 8, "y": 8, "fill": "#FF0000"}
        renderer._render_pixel(ctx, element)
        ctx.draw_pixel.assert_called_once()

    def test_render_circle_element(self):
        """Test rendering circle element."""
        renderer = ManifestRenderer()
        ctx = Mock()
        ctx.draw_circle = Mock()
        
        element = {"type": "circle", "cx": 8, "cy": 8, "radius": 4, "fill": "#FF0000"}
        renderer._render_circle(ctx, element)
        ctx.draw_circle.assert_called_once()

    def test_render_line_element(self):
        """Test rendering line element."""
        renderer = ManifestRenderer()
        ctx = Mock()
        ctx.draw_line = Mock()
        
        element = {"type": "line", "x1": 0, "y1": 0, "x2": 15, "y2": 15, "stroke": "#FF0000"}
        renderer._render_line(ctx, element)
        ctx.draw_line.assert_called_once()

    def test_render_to_grid_layers(self):
        """Test rendering layer-based manifest to grid."""
        renderer = ManifestRenderer()
        grid = renderer._render_to_grid(VALID_MANIFEST)
        
        assert isinstance(grid, PixelGrid)
        assert grid.width == 16
        assert grid.height == 16

    def test_render_to_grid_frames(self):
        """Test rendering frame-based manifest to grid."""
        renderer = ManifestRenderer()
        
        frames_manifest = {
            "metadata": {"canvas": {"width": 16, "height": 16}},
            "frames": [
                {
                    "name": "Frame 0",
                    "elements": [
                        {"type": "rect", "x": 0, "y": 0, "width": 16, "height": 16, "fill": "#FF0000"}
                    ],
                }
            ],
        }
        
        grid = renderer._render_to_grid(frames_manifest)
        assert isinstance(grid, PixelGrid)

    @pytest.mark.asyncio
    async def test_render_manifest_async(self, tmp_path):
        """Test async rendering of manifest."""
        renderer = ManifestRenderer()
        output_path = tmp_path / "test_sprite.png"
        
        with patch.object(renderer, 'render_manifest_sync', return_value=output_path) as mock_sync:
            result = await renderer.render_manifest_async(VALID_MANIFEST, output_path)
            assert result == output_path
            mock_sync.assert_called_once()

    def test_render_manifest_sync(self, tmp_path):
        """Test synchronous rendering of manifest."""
        renderer = ManifestRenderer(scale=1, include_metadata=False)
        output_path = tmp_path / "test_sprite"  # Without extension
        
        result = renderer.render_manifest_sync(VALID_MANIFEST, output_path)
        
        # Check PNG was created with correct extension
        assert result.suffix == ".png"
        assert result.exists()

    def test_render_manifest_sync_with_extension(self, tmp_path):
        """Test rendering with .png extension already provided."""
        renderer = ManifestRenderer()
        output_path = tmp_path / "test_sprite.png"
        
        result = renderer.render_manifest_sync(VALID_MANIFEST, output_path)
        assert result == output_path.absolute()

    def test_render_manifest_sync_with_transparent_color(self, tmp_path):
        """Test rendering with transparent color."""
        renderer = ManifestRenderer()
        output_path = tmp_path / "test_sprite.png"
        transparent_color = Color(255, 0, 255)  # Magenta
        
        result = renderer.render_manifest_sync(
            VALID_MANIFEST,
            output_path,
            transparent_color=transparent_color
        )
        assert result.exists()


class TestAnimationFrameRendering:
    """Tests for animation frame rendering."""

    def test_render_animation_frames(self, tmp_path):
        """Test rendering individual animation frames."""
        output_dir = tmp_path / "frames"
        
        frame_paths = render_animation_frames(
            ANIMATION_MANIFEST,
            output_dir,
            name_prefix="test_anim",
            scale=1,
        )
        
        assert len(frame_paths) == 2
        assert all(p.exists() for p in frame_paths)
        assert frame_paths[0].name == "test_anim_0000.png"
        assert frame_paths[1].name == "test_anim_0001.png"

    def test_render_animation_frames_with_transparent(self, tmp_path):
        """Test rendering frames with transparent color."""
        output_dir = tmp_path / "frames"
        transparent_color = Color(255, 0, 255)
        
        frame_paths = render_animation_frames(
            ANIMATION_MANIFEST,
            output_dir,
            name_prefix="test",
            scale=1,
            transparent_color=transparent_color,
        )
        
        assert len(frame_paths) == 2


class TestQuickRender:
    """Tests for quick_render convenience function."""

    def test_quick_render(self, tmp_path):
        """Test quick render function."""
        output_path = tmp_path / "quick_test.png"
        
        result = quick_render(VALID_MANIFEST, output_path, scale=1)
        
        assert result.exists()
        assert result == output_path.absolute()

    def test_quick_render_with_scale(self, tmp_path):
        """Test quick render with custom scale."""
        output_path = tmp_path / "scaled_test.png"
        
        result = quick_render(VALID_MANIFEST, output_path, scale=2)
        assert result.exists()

    def test_quick_render_with_transparent(self, tmp_path):
        """Test quick render with transparent color."""
        output_path = tmp_path / "transparent_test.png"
        transparent_color = Color(255, 0, 255)
        
        result = quick_render(
            VALID_MANIFEST,
            output_path,
            transparent_color=transparent_color
        )
        assert result.exists()


class TestErrorHandling:
    """Tests for error handling in manifest rendering."""

    def test_render_with_invalid_manifest(self):
        """Test that invalid manifest raises appropriate error."""
        renderer = ManifestRenderer()
        with pytest.raises(ManifestParseError):
            renderer.render_manifest_sync({"invalid": "manifest"}, "output.png")

    def test_render_element_with_missing_type(self):
        """Test rendering element without type field."""
        renderer = ManifestRenderer()
        ctx = Mock()
        element = {"x": 0, "y": 0}  # Missing 'type'
        
        with pytest.raises(ManifestParseError, match="missing 'type'"):
            renderer._render_element(ctx, element)

    def test_render_unknown_element_type(self):
        """Test rendering unknown element type logs warning."""
        renderer = ManifestRenderer()
        ctx = Mock()
        element = {"type": "unknown", "x": 0, "y": 0}
        
        # Should not raise, just log warning
        renderer._render_element(ctx, element)


class TestIntegration:
    """Integration tests for complete workflow."""

    def test_full_rendering_workflow(self, tmp_path):
        """Test complete rendering workflow from manifest to PNG."""
        renderer = ManifestRenderer(scale=2, include_metadata=True)
        output_path = tmp_path / "integration_test.png"
        
        # Render
        result = renderer.render_manifest_sync(VALID_MANIFEST, output_path)
        
        # Verify
        assert result.exists()
        assert result.suffix == ".png"
        
        # Check file has content
        assert result.stat().st_size > 0

    def test_animation_complete_workflow(self, tmp_path):
        """Test complete animation rendering workflow."""
        # Render sprite sheet
        renderer = ManifestRenderer()
        sheet_path = tmp_path / "anim_sheet.png"
        result = renderer.render_manifest_sync(ANIMATION_MANIFEST, sheet_path)
        assert result.exists()
        
        # Render individual frames
        frames_dir = tmp_path / "frames"
        frame_paths = render_animation_frames(
            ANIMATION_MANIFEST,
            frames_dir,
            "anim",
        )
        assert len(frame_paths) == 2
        assert all(p.exists() for p in frame_paths)