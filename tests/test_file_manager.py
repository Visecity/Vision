"""
Tests for file management utilities.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.utils.file_manager import (
    derive_asset_name,
    ensure_unique_filename,
    organize_output_files,
    sanitize_filename,
    get_output_metadata_path,
    create_directory_structure,
)


class TestDeriveAssetName:
    """Tests for derive_asset_name function."""
    
    def test_simple_description(self):
        """Test with simple two-word description."""
        result = derive_asset_name("wooden chest")
        assert result == "wooden_chest"
    
    def test_longer_description(self):
        """Test with longer description."""
        result = derive_asset_name("blue healing potion")
        assert result == "blue_healing_potion"
    
    def test_with_dimensions(self):
        """Test description with dimensions."""
        result = derive_asset_name("player sprite 32x32")
        assert result == "player_sprite_32x32"
    
    def test_with_articles(self):
        """Test that articles are filtered out."""
        result = derive_asset_name("a small wooden chest")
        assert result == "small_wooden_chest"
        
        result = derive_asset_name("the red potion")
        assert result == "red_potion"
    
    def test_max_length_truncation(self):
        """Test that long names are truncated."""
        long_desc = "a very long description that definitely exceeds the maximum allowed length"
        result = derive_asset_name(long_desc, max_length=30)
        assert len(result) <= 30
        assert result == "very_long_description_that_de"
    
    def test_special_characters_removed(self):
        """Test that special characters are removed."""
        result = derive_asset_name("chest@#$%with!special*chars")
        assert "@" not in result
        assert "#" not in result
        assert "!" not in result
        assert "chest" in result
    
    def test_multiple_underscores_collapsed(self):
        """Test that multiple underscores are collapsed."""
        result = derive_asset_name("test    with    spaces")
        assert "___" not in result
        assert "test_with_spaces" == result
    
    def test_empty_description_fallback(self):
        """Test fallback for empty descriptions."""
        result = derive_asset_name("")
        assert result == "asset"
        
        result = derive_asset_name("   ")
        assert result == "asset"
    
    def test_only_filler_words(self):
        """Test description with only filler words."""
        result = derive_asset_name("a an the of")
        assert len(result) > 0  # Should have some fallback
    
    def test_mixed_case_normalized(self):
        """Test that mixed case is normalized to lowercase."""
        result = derive_asset_name("Blue Healing Potion")
        assert result == "blue_healing_potion"


class TestEnsureUniqueFilename:
    """Tests for ensure_unique_filename function."""
    
    def setup_method(self):
        """Create temporary directory for tests."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_unique_filename_not_exists(self):
        """Test when file doesn't exist."""
        base_path = self.temp_dir / "chest"
        result = ensure_unique_filename(base_path)
        assert result == self.temp_dir / "chest.json"
    
    def test_unique_filename_exists_once(self):
        """Test when file exists once."""
        base_path = self.temp_dir / "chest"
        
        # Create the original file
        (self.temp_dir / "chest.json").touch()
        
        result = ensure_unique_filename(base_path)
        assert result == self.temp_dir / "chest_001.json"
    
    def test_unique_filename_exists_multiple(self):
        """Test when multiple versions exist."""
        base_path = self.temp_dir / "chest"
        
        # Create multiple versions
        (self.temp_dir / "chest.json").touch()
        (self.temp_dir / "chest_001.json").touch()
        (self.temp_dir / "chest_002.json").touch()
        
        result = ensure_unique_filename(base_path)
        assert result == self.temp_dir / "chest_003.json"
    
    def test_custom_extension(self):
        """Test with custom file extension."""
        base_path = self.temp_dir / "image"
        result = ensure_unique_filename(base_path, extension=".png")
        assert result == self.temp_dir / "image.png"
    
    def test_extension_without_dot(self):
        """Test that extension without dot is handled."""
        base_path = self.temp_dir / "image"
        result = ensure_unique_filename(base_path, extension="png")
        assert result == self.temp_dir / "image.png"


class TestOrganizeOutputFiles:
    """Tests for organize_output_files function."""
    
    def setup_method(self):
        """Create temporary directory for tests."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_organize_without_category(self):
        """Test organizing files without category."""
        result = organize_output_files("chest", self.temp_dir)
        
        assert result['manifest'] == self.temp_dir / "chest.json"
        assert result['png'] == self.temp_dir / "chest.png"
        assert result['directory'] == self.temp_dir
        assert result['directory'].exists()
    
    def test_organize_with_category(self):
        """Test organizing files with category."""
        result = organize_output_files("chest", self.temp_dir, category="items")
        
        items_dir = self.temp_dir / "items"
        assert result['manifest'] == items_dir / "chest.json"
        assert result['png'] == items_dir / "chest.png"
        assert result['directory'] == items_dir
        assert items_dir.exists()
    
    def test_directory_creation(self):
        """Test that directories are created."""
        category_dir = self.temp_dir / "new_category"
        assert not category_dir.exists()
        
        result = organize_output_files("asset", self.temp_dir, category="new_category")
        
        assert result['directory'].exists()
        assert category_dir.exists()


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""
    
    def test_removes_special_characters(self):
        """Test removal of problematic characters."""
        result = sanitize_filename("my*file?.txt")
        assert "*" not in result
        assert "?" not in result
        assert result == "my_file_.txt"
    
    def test_removes_slashes(self):
        """Test removal of forward and back slashes."""
        result = sanitize_filename("file/with\\slashes.png")
        assert "/" not in result
        assert "\\" not in result
        assert result == "file_with_slashes.png"
    
    def test_strips_dots_and_spaces(self):
        """Test stripping of leading/trailing dots and spaces."""
        result = sanitize_filename("  .file.txt.  ")
        assert not result.startswith(" ")
        assert not result.startswith(".")
        assert not result.endswith(" ")
        assert not result.endswith(".")
    
    def test_empty_filename_fallback(self):
        """Test fallback for empty filename."""
        result = sanitize_filename("")
        assert result == "file"
        
        result = sanitize_filename("   ")
        assert result == "file"
    
    def test_max_length_truncation(self):
        """Test truncation to max length."""
        long_name = "a" * 300
        result = sanitize_filename(long_name, max_length=100)
        assert len(result) <= 100
    
    def test_preserves_extension_when_truncating(self):
        """Test that extension is preserved when truncating."""
        long_name = "a" * 300 + ".png"
        result = sanitize_filename(long_name, max_length=100)
        assert len(result) <= 100
        assert result.endswith(".png")


class TestGetOutputMetadataPath:
    """Tests for get_output_metadata_path function."""
    
    def test_metadata_path(self):
        """Test metadata path generation."""
        directory = Path("/output/assets")
        result = get_output_metadata_path(directory)
        assert result == Path("/output/assets/metadata.json")


class TestCreateDirectoryStructure:
    """Tests for create_directory_structure function."""
    
    def setup_method(self):
        """Create temporary directory for tests."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_create_base_only(self):
        """Test creating just base directory."""
        base_dir = self.temp_dir / "output"
        result = create_directory_structure(base_dir)
        
        assert base_dir.exists()
        assert result == {'base': base_dir}
    
    def test_create_with_subdirectories(self):
        """Test creating subdirectories."""
        base_dir = self.temp_dir / "output"
        subdirs = ["items", "characters", "tiles"]
        
        result = create_directory_structure(base_dir, subdirs)
        
        assert base_dir.exists()
        assert result['base'] == base_dir
        
        for subdir in subdirs:
            subdir_path = base_dir / subdir
            assert subdir_path.exists()
            assert result[subdir] == subdir_path
    
    def test_existing_directories(self):
        """Test that existing directories don't cause errors."""
        base_dir = self.temp_dir / "output"
        base_dir.mkdir(parents=True)
        (base_dir / "items").mkdir()
        
        # Should not raise error
        result = create_directory_structure(base_dir, ["items", "characters"])
        
        assert result['items'].exists()
        assert result['characters'].exists()


# Additional integration tests
class TestFileManagerIntegration:
    """Integration tests for file manager functionality."""
    
    def setup_method(self):
        """Create temporary directory for tests."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_complete_asset_workflow(self):
        """Test complete workflow from description to organized files."""
        # Derive name from description
        description = "blue healing potion"
        asset_name = derive_asset_name(description)
        assert asset_name == "blue_healing_potion"
        
        # Organize files
        file_paths = organize_output_files(
            asset_name,
            self.temp_dir,
            category="potions"
        )
        
        # Verify structure
        assert file_paths['directory'].exists()
        assert file_paths['manifest'] == self.temp_dir / "potions" / "blue_healing_potion.json"
        assert file_paths['png'] == self.temp_dir / "potions" / "blue_healing_potion.png"
    
    def test_collision_handling_workflow(self):
        """Test handling name collisions."""
        # Create first asset
        asset_name = derive_asset_name("wooden chest")
        base_path = self.temp_dir / asset_name
        
        # First file
        first_file = ensure_unique_filename(base_path)
        first_file.touch()
        assert first_file.name == "wooden_chest.json"
        
        # Second file with same name
        second_file = ensure_unique_filename(base_path)
        second_file.touch()
        assert second_file.name == "wooden_chest_001.json"
        
        # Third file
        third_file = ensure_unique_filename(base_path)
        assert third_file.name == "wooden_chest_002.json"