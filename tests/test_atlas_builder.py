"""
Tests for atlas texture builder.
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil
import json
from PIL import Image

from src.rendering.atlas_builder import (
    AtlasBuilder,
    build_atlas_from_directory,
)
from src.rendering.spritesheet import PackingAlgorithm
from src.rendering.pixel import PixelGrid, Color


class TestAtlasBuilder:
    """Tests for AtlasBuilder class."""
    
    def setup_method(self):
        """Create temporary directory and test assets."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.builder = AtlasBuilder(
            padding=2,
            max_size=(512, 512),
            power_of_two=True,
        )
        
        # Create test images
        self.test_images = {}
        for name, size in [("sprite1", (16, 16)), ("sprite2", (32, 32)), ("sprite3", (24, 24))]:
            img = Image.new('RGB', size, color=(255, 0, 0))
            self.test_images[name] = img
    
    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test AtlasBuilder initialization."""
        builder = AtlasBuilder(
            padding=4,
            max_size=(1024, 1024),
            power_of_two=False,
        )
        
        assert builder.padding == 4
        assert builder.max_size == (1024, 1024)
        assert builder.power_of_two == False
        assert builder.asset_count == 0
    
    def test_initialization_invalid_padding(self):
        """Test that negative padding raises error."""
        with pytest.raises(ValueError, match="Padding must be non-negative"):
            AtlasBuilder(padding=-1)
    
    def test_initialization_invalid_max_size(self):
        """Test that invalid max size raises error."""
        with pytest.raises(ValueError, match="Max size dimensions must be positive"):
            AtlasBuilder(max_size=(0, 512))
        
        with pytest.raises(ValueError, match="Max size cannot exceed"):
            AtlasBuilder(max_size=(5000, 5000))
    
    @pytest.mark.asyncio
    async def test_add_asset(self):
        """Test adding assets to the builder."""
        await self.builder.add_asset("test1", self.test_images["sprite1"])
        
        assert self.builder.asset_count == 1
        assert "test1" in self.builder.asset_names
    
    @pytest.mark.asyncio
    async def test_add_duplicate_asset_name(self):
        """Test that duplicate asset names raise error."""
        await self.builder.add_asset("test1", self.test_images["sprite1"])
        
        with pytest.raises(ValueError, match="already exists"):
            await self.builder.add_asset("test1", self.test_images["sprite2"])
    
    @pytest.mark.asyncio
    async def test_add_asset_with_metadata(self):
        """Test adding asset with metadata."""
        metadata = {"category": "characters", "tags": ["player", "hero"]}
        await self.builder.add_asset("hero", self.test_images["sprite1"], metadata)
        
        assert self.builder.asset_count == 1
        assert "hero" in self.builder.asset_names
    
    @pytest.mark.asyncio
    async def test_add_asset_from_file(self):
        """Test adding asset from file."""
        # Save test image to file
        img_path = self.temp_dir / "test.png"
        self.test_images["sprite1"].save(img_path)
        
        await self.builder.add_asset_from_file("test", img_path)
        
        assert self.builder.asset_count == 1
        assert "test" in self.builder.asset_names
    
    @pytest.mark.asyncio
    async def test_add_asset_from_missing_file(self):
        """Test that missing file raises error."""
        missing_path = self.temp_dir / "missing.png"
        
        with pytest.raises(FileNotFoundError):
            await self.builder.add_asset_from_file("test", missing_path)
    
    @pytest.mark.asyncio
    async def test_build_atlas_no_assets(self):
        """Test that building without assets raises error."""
        with pytest.raises(ValueError, match="No assets to pack"):
            await self.builder.build_atlas(self.temp_dir, "test_atlas")
    
    @pytest.mark.asyncio
    async def test_build_atlas_single_asset(self):
        """Test building atlas with single asset."""
        await self.builder.add_asset("sprite1", self.test_images["sprite1"])
        
        atlas_path = await self.builder.build_atlas(self.temp_dir, "single_atlas")
        
        # Verify files were created
        assert atlas_path.exists()
        assert (self.temp_dir / "single_atlas.png").exists()
        assert (self.temp_dir / "single_atlas.json").exists()
        
        # Verify metadata structure
        with open(self.temp_dir / "single_atlas.json") as f:
            metadata = json.load(f)
        
        assert metadata["atlas_name"] == "single_atlas"
        assert "texture_size" in metadata
        assert "sprites" in metadata
        assert "sprite1" in metadata["sprites"]
        assert metadata["sprites"]["sprite1"]["x"] >= 0
        assert metadata["sprites"]["sprite1"]["width"] == 16
        assert metadata["sprites"]["sprite1"]["height"] == 16
    
    @pytest.mark.asyncio
    async def test_build_atlas_multiple_assets(self):
        """Test building atlas with multiple assets."""
        for name, img in self.test_images.items():
            await self.builder.add_asset(name, img)
        
        atlas_path = await self.builder.build_atlas(self.temp_dir, "multi_atlas")
        
        # Verify files
        assert atlas_path.exists()
        
        # Load and verify metadata
        with open(self.temp_dir / "multi_atlas.json") as f:
            metadata = json.load(f)
        
        assert metadata["atlas_name"] == "multi_atlas"
        assert metadata["metadata"]["total_sprites"] == 3
        assert len(metadata["sprites"]) == 3
        
        # Verify all sprites are present
        for name in self.test_images.keys():
            assert name in metadata["sprites"]
    
    @pytest.mark.asyncio
    async def test_get_metadata_without_building(self):
        """Test getting metadata without building atlas."""
        await self.builder.add_asset("sprite1", self.test_images["sprite1"])
        
        metadata = self.builder.get_metadata()
        
        assert "atlas_name" in metadata
        assert "sprites" in metadata
        assert "sprite1" in metadata["sprites"]
    
    @pytest.mark.asyncio
    async def test_get_metadata_no_assets(self):
        """Test that get_metadata raises error with no assets."""
        with pytest.raises(ValueError, match="No assets added"):
            self.builder.get_metadata()
    
    def test_clear(self):
        """Test clearing the builder."""
        # Use asyncio.run for async operations in sync test
        async def add_assets():
            await self.builder.add_asset("test1", self.test_images["sprite1"])
            await self.builder.add_asset("test2", self.test_images["sprite2"])
        
        asyncio.run(add_assets())
        
        assert self.builder.asset_count == 2
        
        self.builder.clear()
        
        assert self.builder.asset_count == 0
        assert len(self.builder.asset_names) == 0
    
    @pytest.mark.asyncio
    async def test_different_packing_algorithms(self):
        """Test building atlases with different packing algorithms."""
        algorithms = [
            PackingAlgorithm.ROW,
            PackingAlgorithm.COLUMN,
            PackingAlgorithm.GRID,
            PackingAlgorithm.SHELF,
            PackingAlgorithm.MAXRECTS,
        ]
        
        for algo in algorithms:
            builder = AtlasBuilder(
                padding=2,
                max_size=(512, 512),
                packing_algorithm=algo,
            )
            
            # Add test assets
            for name, img in self.test_images.items():
                await builder.add_asset(name, img)
            
            # Build atlas
            atlas_path = await builder.build_atlas(
                self.temp_dir,
                f"atlas_{algo.value}"
            )
            
            assert atlas_path.exists()
            
            # Verify metadata includes algorithm info
            with open(self.temp_dir / f"atlas_{algo.value}.json") as f:
                metadata = json.load(f)
            
            assert metadata["metadata"]["packing_algorithm"] == algo.value
    
    @pytest.mark.asyncio
    async def test_atlas_with_custom_metadata(self):
        """Test that custom metadata is preserved in atlas."""
        metadata1 = {"category": "items", "rarity": "common"}
        metadata2 = {"category": "items", "rarity": "rare"}
        
        await self.builder.add_asset("item1", self.test_images["sprite1"], metadata1)
        await self.builder.add_asset("item2", self.test_images["sprite2"], metadata2)
        
        await self.builder.build_atlas(self.temp_dir, "custom_meta_atlas")
        
        # Load metadata
        with open(self.temp_dir / "custom_meta_atlas.json") as f:
            atlas_metadata = json.load(f)
        
        # Verify custom metadata is preserved
        assert atlas_metadata["sprites"]["item1"]["metadata"] == metadata1
        assert atlas_metadata["sprites"]["item2"]["metadata"] == metadata2


class TestBuildAtlasFromDirectory:
    """Tests for build_atlas_from_directory helper function."""
    
    def setup_method(self):
        """Create temporary directories and test files."""
        self.input_dir = Path(tempfile.mkdtemp())
        self.output_dir = Path(tempfile.mkdtemp())
        
        # Create test PNG files
        for i, size in enumerate([(16, 16), (32, 32), (24, 24)]):
            img = Image.new('RGB', size, color=(i * 80, 0, 0))
            img.save(self.input_dir / f"sprite{i}.png")
    
    def teardown_method(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.input_dir)
        shutil.rmtree(self.output_dir)
    
    @pytest.mark.asyncio
    async def test_build_from_directory(self):
        """Test building atlas from directory of PNGs."""
        atlas_path, metadata = await build_atlas_from_directory(
            self.input_dir,
            self.output_dir,
            "dir_atlas"
        )
        
        # Verify output
        assert atlas_path.exists()
        assert (self.output_dir / "dir_atlas.json").exists()
        
        # Verify metadata
        assert "atlas_name" in metadata
        assert len(metadata["sprites"]) == 3
        assert "sprite0" in metadata["sprites"]
        assert "sprite1" in metadata["sprites"]
        assert "sprite2" in metadata["sprites"]
    
    @pytest.mark.asyncio
    async def test_build_from_directory_with_pattern(self):
        """Test building atlas with custom file pattern."""
        # Add a non-PNG file
        (self.input_dir / "readme.txt").write_text("test")
        
        atlas_path, metadata = await build_atlas_from_directory(
            self.input_dir,
            self.output_dir,
            "pattern_atlas",
            pattern="*.png"
        )
        
        # Should only include PNG files
        assert len(metadata["sprites"]) == 3
    
    @pytest.mark.asyncio
    async def test_build_from_missing_directory(self):
        """Test that missing input directory raises error."""
        missing_dir = Path("/nonexistent/directory")
        
        with pytest.raises(FileNotFoundError):
            await build_atlas_from_directory(
                missing_dir,
                self.output_dir,
                "test"
            )
    
    @pytest.mark.asyncio
    async def test_build_from_empty_directory(self):
        """Test that empty directory raises error."""
        empty_dir = Path(tempfile.mkdtemp())
        
        try:
            with pytest.raises(ValueError, match="No files matching"):
                await build_atlas_from_directory(
                    empty_dir,
                    self.output_dir,
                    "test"
                )
        finally:
            shutil.rmtree(empty_dir)
    
    @pytest.mark.asyncio
    async def test_build_with_custom_parameters(self):
        """Test building with custom atlas parameters."""
        atlas_path, metadata = await build_atlas_from_directory(
            self.input_dir,
            self.output_dir,
            "custom_atlas",
            padding=4,
            power_of_two=False,
            packing_algorithm=PackingAlgorithm.ROW
        )
        
        assert atlas_path.exists()
        
        # Verify custom parameters were applied
        with open(self.output_dir / "custom_atlas.json") as f:
            atlas_metadata = json.load(f)
        
        assert atlas_metadata["metadata"]["padding"] == 4
        assert atlas_metadata["metadata"]["power_of_two"] == False
        assert atlas_metadata["metadata"]["packing_algorithm"] == "row"


class TestAtlasBuilderIntegration:
    """Integration tests for complete atlas building workflows."""
    
    def setup_method(self):
        """Create temporary directory."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete workflow from assets to atlas."""
        # Create test images of various sizes
        assets = {
            "player": (32, 32),
            "enemy1": (24, 24),
            "enemy2": (24, 24),
            "item1": (16, 16),
            "item2": (16, 16),
            "item3": (16, 16),
        }
        
        builder = AtlasBuilder(padding=2, power_of_two=True)
        
        # Add all assets
        for name, size in assets.items():
            img = Image.new('RGBA', size, color=(255, 0, 0, 255))
            await builder.add_asset(name, img)
        
        # Build atlas
        atlas_path = await builder.build_atlas(self.temp_dir, "game_atlas")
        
        # Verify output
        assert atlas_path.exists()
        assert (self.temp_dir / "game_atlas.json").exists()
        
        # Verify atlas image can be loaded
        atlas_img = Image.open(atlas_path)
        assert atlas_img.size[0] > 0
        assert atlas_img.size[1] > 0
        
        # Verify metadata is valid
        with open(self.temp_dir / "game_atlas.json") as f:
            metadata = json.load(f)
        
        assert metadata["metadata"]["total_sprites"] == len(assets)
        
        # Verify all sprites have valid coordinates
        for name in assets.keys():
            sprite = metadata["sprites"][name]
            assert sprite["x"] >= 0
            assert sprite["y"] >= 0
            assert sprite["width"] > 0
            assert sprite["height"] > 0
    
    @pytest.mark.asyncio
    async def test_multiple_atlases(self):
        """Test creating multiple atlases from same builder."""
        builder = AtlasBuilder()
        
        # Build first atlas
        img1 = Image.new('RGB', (16, 16), color=(255, 0, 0))
        await builder.add_asset("sprite1", img1)
        await builder.build_atlas(self.temp_dir, "atlas1")
        
        # Clear and build second atlas
        builder.clear()
        img2 = Image.new('RGB', (32, 32), color=(0, 255, 0))
        await builder.add_asset("sprite2", img2)
        await builder.build_atlas(self.temp_dir, "atlas2")
        
        # Verify both atlases exist
        assert (self.temp_dir / "atlas1.png").exists()
        assert (self.temp_dir / "atlas1.json").exists()
        assert (self.temp_dir / "atlas2.png").exists()
        assert (self.temp_dir / "atlas2.json").exists()