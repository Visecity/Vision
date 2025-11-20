"""
Integration tests for adaptive encoding selection in DetailAgent.

Tests the complete flow of:
1. Complexity analysis from design specifications
2. Encoding strategy recommendation
3. Actual compression performance
4. Prediction accuracy monitoring
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.agents.detail_agent import DetailAgent
from src.core.models import (
    AgentContext,
    SpriteRequest,
    Dimensions,
    AssetStyle,
    AssetType,
    ColorPalette,
)
from src.llm.client import LLMClient
import json


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    client = MagicMock(spec=LLMClient)
    return client


@pytest.fixture
def simple_geometric_design():
    """Design spec for simple geometric sprite (high structure, low entropy)."""
    return {
        "shape_language": "simple geometric shapes - circles and rectangles",
        "composition": "centered icon with clear silhouette",
        "technical_specs": {
            "dimensions": "16x16",
            "style_notes": "clean lines, solid colors",
        }
    }


@pytest.fixture
def organic_detailed_design():
    """Design spec for organic detailed sprite (high entropy, low structure)."""
    return {
        "shape_language": "organic flowing forms with natural textures",
        "composition": "detailed character with varied elements",
        "technical_specs": {
            "dimensions": "32x32",
            "style_notes": "rich detail, varied shading",
        }
    }


@pytest.fixture
def gradient_design():
    """Design spec for gradient-heavy sprite (medium entropy, low repetition)."""
    return {
        "shape_language": "smooth gradients and color transitions",
        "composition": "background tile with color flow",
        "technical_specs": {
            "dimensions": "16x16",
            "style_notes": "gradient shading, smooth transitions",
        }
    }


@pytest.fixture
def small_palette():
    """Small color palette (8 colors)."""
    return ColorPalette(
        name="small_palette",
        colors=[
            "#FF0000", "#00FF00", "#0000FF",
            "#FFFF00", "#FF00FF", "#00FFFF",
            "#FFFFFF", "#000000"
        ],
        description="8-color palette"
    )


@pytest.fixture
def large_palette():
    """Large color palette (20 colors)."""
    colors = [f"#{i:02x}{i:02x}{i:02x}" for i in range(0, 255, 12)][:20]
    return ColorPalette(
        name="large_palette",
        colors=colors,
        description="20-color palette"
    )


class TestAdaptiveEncodingSelection:
    """Test adaptive encoding strategy selection based on complexity."""

    @pytest.mark.asyncio
    async def test_simple_geometric_selects_palette_indexing(
        self, mock_llm_client, simple_geometric_design, small_palette
    ):
        """Simple geometric sprite with small palette should use palette indexing."""
        # Setup
        agent = DetailAgent(llm_client=mock_llm_client)
        
        # Mock LLM response with palette-indexed output
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "pixel_grid": {
                "width": 16,
                "height": 16,
                "encoding": "palette_indexed_rle",
                "palette": ["#FF0000", "#00FF00", "#0000FF"],
                "data": [
                    {"idx": 0, "count": 100},
                    {"idx": 1, "count": 80},
                    {"idx": 2, "count": 76}
                ]
            },
            "shading_details": {
                "light_source": "top-left",
                "shading_technique": "cel shading"
            },
            "final_specs": {
                "colors_used": ["#FF0000", "#00FF00", "#0000FF"],
                "readability_score": 0.95
            }
        }))]
        mock_llm_client.create_message = AsyncMock(return_value=mock_response)
        
        # Create context
        request = SpriteRequest(
            description="Simple geometric icon for testing",
            asset_type=AssetType.ICON,
            dimensions=Dimensions(width=16, height=16),
            style=AssetStyle.STARDEW_VALLEY,
        )
        context = AgentContext(
            request=request,
            current_step="detail",
            previous_results={
                "design": simple_geometric_design,
                "palette": small_palette,
            }
        )
        
        # Execute
        result = await agent.process(context)
        
        # Verify encoding decision
        assert "_metadata" in result
        metadata = result["_metadata"]
        assert "encoding_decision" in metadata
        assert metadata["encoding_decision"]["recommended"] == "palette_indexed_rle"
        
        # Verify complexity metrics
        assert "complexity_metrics" in metadata
        complexity = metadata["complexity_metrics"]
        assert complexity["structure_score"] >= 0.6  # High structure
        assert complexity["entropy"] <= 0.5  # Low entropy

    @pytest.mark.asyncio
    async def test_organic_detailed_selects_rle(
        self, mock_llm_client, organic_detailed_design, large_palette
    ):
        """Organic detailed sprite with large palette should use RLE."""
        # Setup
        agent = DetailAgent(llm_client=mock_llm_client)
        
        # Mock LLM response with RLE output
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "pixel_grid": {
                "width": 32,
                "height": 32,
                "encoding": "rle",
                "data": [
                    {"color": "#FF0000", "count": 50},
                    {"color": "#00FF00", "count": 100},
                    {"color": "#0000FF", "count": 874}
                ]
            },
            "shading_details": {
                "light_source": "top-left",
                "shading_technique": "soft shading"
            },
            "final_specs": {
                "colors_used": ["#FF0000", "#00FF00", "#0000FF"],
                "readability_score": 0.88
            }
        }))]
        mock_llm_client.create_message = AsyncMock(return_value=mock_response)
        
        # Create context
        request = SpriteRequest(
            description="Detailed character sprite for testing",
            asset_type=AssetType.CHARACTER,
            dimensions=Dimensions(width=32, height=32),
            style=AssetStyle.STARDEW_VALLEY,
        )
        context = AgentContext(
            request=request,
            current_step="detail",
            previous_results={
                "design": organic_detailed_design,
                "palette": large_palette,
            }
        )
        
        # Execute
        result = await agent.process(context)
        
        # Verify encoding decision
        metadata = result["_metadata"]
        assert metadata["encoding_decision"]["recommended"] == "rle"
        
        # Verify complexity metrics
        complexity = metadata["complexity_metrics"]
        assert complexity["entropy"] >= 0.5  # Higher entropy
        assert complexity["structure_score"] <= 0.5  # Lower structure

    @pytest.mark.asyncio
    async def test_small_sprite_selects_standard_grid(
        self, mock_llm_client, gradient_design, small_palette
    ):
        """Small sprite should use standard grid format."""
        # Setup
        agent = DetailAgent(llm_client=mock_llm_client)
        
        # Mock LLM response with grid output
        mock_response = MagicMock()
        grid_data = ["#FF0000"] * 64  # 8x8 grid
        mock_response.content = [MagicMock(text=json.dumps({
            "pixel_grid": {
                "width": 8,
                "height": 8,
                "encoding": "grid",
                "data": grid_data
            },
            "shading_details": {
                "light_source": "top",
                "shading_technique": "gradient"
            },
            "final_specs": {
                "colors_used": ["#FF0000"],
                "readability_score": 0.90
            }
        }))]
        mock_llm_client.create_message = AsyncMock(return_value=mock_response)
        
        # Create context
        request = SpriteRequest(
            description="Small icon sprite for testing",
            asset_type=AssetType.ICON,
            dimensions=Dimensions(width=8, height=8),
            style=AssetStyle.STARDEW_VALLEY,
        )
        context = AgentContext(
            request=request,
            current_step="detail",
            previous_results={
                "design": gradient_design,
                "palette": small_palette,
            }
        )
        
        # Execute
        result = await agent.process(context)
        
        # Verify encoding decision
        metadata = result["_metadata"]
        assert metadata["encoding_decision"]["recommended"] == "standard"


class TestCompressionMetadataLogging:
    """Test comprehensive metadata logging for monitoring."""

    @pytest.mark.asyncio
    async def test_palette_indexed_metadata_complete(
        self, mock_llm_client, simple_geometric_design, small_palette
    ):
        """Verify complete metadata for palette-indexed encoding."""
        # Setup
        agent = DetailAgent(llm_client=mock_llm_client)
        
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "pixel_grid": {
                "width": 16,
                "height": 16,
                "encoding": "palette_indexed_rle",
                "palette": ["#FF0000", "#00FF00"],
                "data": [
                    {"idx": 0, "count": 128},
                    {"idx": 1, "count": 128}
                ]
            },
            "shading_details": {
                "light_source": "top-left",
                "shading_technique": "flat"
            },
            "final_specs": {
                "colors_used": ["#FF0000", "#00FF00"],
                "readability_score": 0.95
            }
        }))]
        mock_llm_client.create_message = AsyncMock(return_value=mock_response)
        
        # Create context
        request = SpriteRequest(
            description="Test sprite for palette indexing",
            asset_type=AssetType.SPRITE,
            dimensions=Dimensions(width=16, height=16),
            style=AssetStyle.STARDEW_VALLEY,
        )
        context = AgentContext(
            request=request,
            current_step="detail",
            previous_results={
                "design": simple_geometric_design,
                "palette": small_palette,
            }
        )
        
        # Execute
        result = await agent.process(context)
        
        # Verify metadata structure
        assert "_metadata" in result
        metadata = result["_metadata"]
        
        # Check encoding decision fields
        assert "encoding_decision" in metadata
        decision = metadata["encoding_decision"]
        assert "recommended" in decision
        assert "estimated_compression_ratio" in decision
        assert "estimated_token_count" in decision
        assert "estimated_token_savings" in decision
        assert "actual_compression_ratio" in decision
        assert "actual_compression_vs_grid_percent" in decision
        
        # Check complexity metrics
        assert "complexity_metrics" in metadata
        complexity = metadata["complexity_metrics"]
        assert "entropy" in complexity
        assert "repetition_score" in complexity
        assert "structure_score" in complexity
        assert "estimated_rle_ratio" in complexity
        assert "avg_run_length" in complexity

    @pytest.mark.asyncio
    async def test_rle_metadata_complete(
        self, mock_llm_client, organic_detailed_design, large_palette
    ):
        """Verify complete metadata for RLE encoding."""
        # Setup
        agent = DetailAgent(llm_client=mock_llm_client)
        
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "pixel_grid": {
                "width": 32,
                "height": 32,
                "encoding": "rle",
                "data": [
                    {"color": "#FF0000", "count": 512},
                    {"color": "#00FF00", "count": 512}
                ]
            },
            "shading_details": {
                "light_source": "top-left",
                "shading_technique": "soft"
            },
            "final_specs": {
                "colors_used": ["#FF0000", "#00FF00"],
                "readability_score": 0.90
            }
        }))]
        mock_llm_client.create_message = AsyncMock(return_value=mock_response)
        
        # Create context
        request = SpriteRequest(
            description="Test sprite for RLE encoding",
            asset_type=AssetType.SPRITE,
            dimensions=Dimensions(width=32, height=32),
            style=AssetStyle.STARDEW_VALLEY,
        )
        context = AgentContext(
            request=request,
            current_step="detail",
            previous_results={
                "design": organic_detailed_design,
                "palette": large_palette,
            }
        )
        
        # Execute
        result = await agent.process(context)
        
        # Verify RLE-specific metadata
        metadata = result["_metadata"]
        decision = metadata["encoding_decision"]
        assert "actual_compression_ratio" in decision
        assert "actual_compression_percent" in decision


class TestPredictionAccuracy:
    """Test compression prediction accuracy monitoring."""

    @pytest.mark.asyncio
    async def test_prediction_accuracy_logged(
        self, mock_llm_client, simple_geometric_design, small_palette, caplog
    ):
        """Verify prediction accuracy is calculated and logged."""
        # Setup
        agent = DetailAgent(llm_client=mock_llm_client)
        
        # Mock LLM response with known compression
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "pixel_grid": {
                "width": 16,
                "height": 16,
                "encoding": "palette_indexed_rle",
                "palette": ["#FF0000", "#00FF00", "#0000FF"],
                "data": [
                    {"idx": 0, "count": 100},
                    {"idx": 1, "count": 80},
                    {"idx": 2, "count": 76}
                ]
            },
            "shading_details": {
                "light_source": "top-left",
                "shading_technique": "cel"
            },
            "final_specs": {
                "colors_used": ["#FF0000", "#00FF00", "#0000FF"],
                "readability_score": 0.95
            }
        }))]
        mock_llm_client.create_message = AsyncMock(return_value=mock_response)
        
        # Create context
        request = SpriteRequest(
            description="Test sprite for prediction accuracy",
            asset_type=AssetType.SPRITE,
            dimensions=Dimensions(width=16, height=16),
            style=AssetStyle.STARDEW_VALLEY,
        )
        context = AgentContext(
            request=request,
            current_step="detail",
            previous_results={
                "design": simple_geometric_design,
                "palette": small_palette,
            }
        )
        
        # Execute with logging capture
        with caplog.at_level("INFO"):
            result = await agent.process(context)
        
        # Verify prediction accuracy was logged
        log_messages = [record.message for record in caplog.records]
        accuracy_logs = [msg for msg in log_messages if "prediction accuracy" in msg.lower()]
        assert len(accuracy_logs) > 0
        
        # Verify metadata includes both estimated and actual
        metadata = result["_metadata"]
        decision = metadata["encoding_decision"]
        assert "estimated_compression_ratio" in decision
        assert "actual_compression_ratio" in decision


class TestEncodingStrategyEdgeCases:
    """Test edge cases in encoding strategy selection."""

    @pytest.mark.asyncio
    async def test_exactly_16_colors_uses_palette_indexing(
        self, mock_llm_client, simple_geometric_design
    ):
        """Exactly 16 colors should still use palette indexing."""
        # Setup with exactly 16 colors
        palette_16 = ColorPalette(
            name="16_colors",
            colors=[f"#{i:02x}0000" for i in range(16)],
            description="Exactly 16 colors"
        )
        
        agent = DetailAgent(llm_client=mock_llm_client)
        
        # Mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "pixel_grid": {
                "width": 16,
                "height": 16,
                "encoding": "palette_indexed_rle",
                "palette": palette_16.colors,
                "data": [{"idx": i, "count": 16} for i in range(16)]
            },
            "shading_details": {"light_source": "top", "shading_technique": "flat"},
            "final_specs": {"colors_used": palette_16.colors, "readability_score": 0.90}
        }))]
        mock_llm_client.create_message = AsyncMock(return_value=mock_response)
        
        request = SpriteRequest(
            description="Test sprite with 16 colors",
            asset_type=AssetType.SPRITE,
            dimensions=Dimensions(width=16, height=16),
            style=AssetStyle.STARDEW_VALLEY,
        )
        context = AgentContext(
            request=request,
            current_step="detail",
            previous_results={
                "design": simple_geometric_design,
                "palette": palette_16,
            }
        )
        
        result = await agent.process(context)
        
        # Should use palette indexing
        metadata = result["_metadata"]
        assert metadata["encoding_decision"]["recommended"] == "palette_indexed_rle"

    @pytest.mark.asyncio
    async def test_17_colors_uses_rle(
        self, mock_llm_client, organic_detailed_design
    ):
        """More than 16 colors should use RLE instead."""
        # Setup with 17 colors
        palette_17 = ColorPalette(
            name="17_colors",
            colors=[f"#{i:02x}0000" for i in range(17)],
            description="17 colors"
        )
        
        agent = DetailAgent(llm_client=mock_llm_client)
        
        # Mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "pixel_grid": {
                "width": 32,
                "height": 32,
                "encoding": "rle",
                "data": [{"color": "#FF0000", "count": 1024}]
            },
            "shading_details": {"light_source": "top", "shading_technique": "soft"},
            "final_specs": {"colors_used": ["#FF0000"], "readability_score": 0.85}
        }))]
        mock_llm_client.create_message = AsyncMock(return_value=mock_response)
        
        request = SpriteRequest(
            description="Test sprite with 17 colors",
            asset_type=AssetType.SPRITE,
            dimensions=Dimensions(width=32, height=32),
            style=AssetStyle.STARDEW_VALLEY,
        )
        context = AgentContext(
            request=request,
            current_step="detail",
            previous_results={
                "design": organic_detailed_design,
                "palette": palette_17,
            }
        )
        
        result = await agent.process(context)
        
        # Should use RLE, not palette indexing
        metadata = result["_metadata"]
        assert metadata["encoding_decision"]["recommended"] == "rle"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])