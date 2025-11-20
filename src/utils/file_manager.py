"""
File management utilities for Vision asset organization.

This module provides centralized file naming, organization, and collision handling
for generated assets.
"""

import re
from pathlib import Path
from typing import Any


def derive_asset_name(description: str, max_length: int = 50) -> str:
    """
    Derive asset name from description.
    
    Converts natural language description to safe filename using snake_case.
    Takes first 3-5 significant words and sanitizes them.
    
    Args:
        description: User's asset description
        max_length: Maximum filename length
    
    Returns:
        Sanitized filename (snake_case, no special chars)
    
    Examples:
        >>> derive_asset_name("wooden chest")
        'wooden_chest'
        >>> derive_asset_name("blue healing potion")
        'blue_healing_potion'
        >>> derive_asset_name("player sprite 32x32")
        'player_sprite_32x32'
        >>> derive_asset_name("A very long description that needs truncation here")
        'very_long_description_that_needs'
    """
    # Convert to lowercase and split
    words = description.lower().split()
    
    # Filter out common filler words and keep significant words
    filler_words = {'a', 'an', 'the', 'of', 'in', 'on', 'at', 'to', 'for', 'and', 'or'}
    significant_words = [w for w in words if w not in filler_words and len(w) > 1]
    
    # Take first 5 significant words
    selected_words = significant_words[:5]
    
    if not selected_words:
        # Fallback: use all words if no significant ones found
        selected_words = [w for w in words if w][:5]
    
    if not selected_words:
        # Ultimate fallback
        return "asset"
    
    # Join with underscores
    base_name = "_".join(selected_words)
    
    # Remove special characters except underscore and hyphen
    base_name = re.sub(r'[^a-z0-9_-]', '', base_name)
    
    # Remove multiple consecutive underscores
    base_name = re.sub(r'_+', '_', base_name)
    
    # Trim leading/trailing underscores
    base_name = base_name.strip('_')
    
    # Ensure not empty after sanitization
    if not base_name:
        return "asset"
    
    # Truncate to max length
    return base_name[:max_length] if len(base_name) > max_length else base_name


def ensure_unique_filename(base_path: Path, extension: str = ".json") -> Path:
    """
    Ensure filename is unique by adding numeric suffix if needed.
    
    If the file already exists, appends _001, _002, etc. until a unique name is found.
    
    Args:
        base_path: Desired file path (without extension)
        extension: File extension (including dot)
    
    Returns:
        Unique file path with extension
    
    Examples:
        >>> ensure_unique_filename(Path("output/chest"))
        Path("output/chest.json")  # if not exists
        >>> ensure_unique_filename(Path("output/chest"))
        Path("output/chest_001.json")  # if chest.json exists
        >>> ensure_unique_filename(Path("output/chest"))
        Path("output/chest_002.json")  # if chest.json and chest_001.json exist
    """
    # Ensure extension starts with dot
    if not extension.startswith('.'):
        extension = f'.{extension}'
    
    # Try original name first
    full_path = Path(str(base_path) + extension)
    if not full_path.exists():
        return full_path
    
    # Find unique name with numeric suffix
    counter = 1
    while True:
        suffixed_path = Path(f"{base_path}_{counter:03d}{extension}")
        if not suffixed_path.exists():
            return suffixed_path
        counter += 1
        
        # Safety check to prevent infinite loop
        if counter > 9999:
            raise ValueError(f"Too many files with base name: {base_path}")


def organize_output_files(
    base_name: str,
    output_dir: Path,
    category: str | None = None
) -> dict[str, Path]:
    """
    Create organized directory structure for assets.
    
    Returns paths for manifest JSON, rendered PNG, and the parent directory.
    Optionally organizes files by category subdirectory.
    
    Args:
        base_name: Asset base name (without extension)
        output_dir: Output directory
        category: Optional category for organization (e.g., "items", "characters")
    
    Returns:
        Dictionary with keys: 'manifest', 'png', 'directory'
    
    Examples:
        >>> organize_output_files("chest", Path("output"), category="items")
        {
            'manifest': Path('output/items/chest.json'),
            'png': Path('output/items/chest.png'),
            'directory': Path('output/items')
        }
        >>> organize_output_files("chest", Path("output"))
        {
            'manifest': Path('output/chest.json'),
            'png': Path('output/chest.png'),
            'directory': Path('output')
        }
    """
    # Determine target directory
    if category:
        target_dir = output_dir / category
    else:
        target_dir = output_dir
    
    # Create directory if it doesn't exist
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Build file paths
    manifest_path = target_dir / f"{base_name}.json"
    png_path = target_dir / f"{base_name}.png"
    
    return {
        'manifest': manifest_path,
        'png': png_path,
        'directory': target_dir,
    }


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a filename to be safe for all filesystems.
    
    Removes or replaces characters that are problematic on various filesystems.
    
    Args:
        filename: Original filename
        max_length: Maximum allowed length
    
    Returns:
        Sanitized filename
    
    Examples:
        >>> sanitize_filename("my*file?.txt")
        'my_file_.txt'
        >>> sanitize_filename("file/with\\slashes.png")
        'file_with_slashes.png'
    """
    # Replace problematic characters with underscore
    # Problematic: < > : " / \ | ? *
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
    
    # Remove leading/trailing dots and spaces (problematic on Windows)
    sanitized = sanitized.strip('. ')
    
    # Ensure not empty
    if not sanitized:
        sanitized = "file"
    
    # Truncate to max length
    if len(sanitized) > max_length:
        # Try to preserve extension if present
        name, *ext_parts = sanitized.rsplit('.', 1)
        if ext_parts:
            ext = f".{ext_parts[0]}"
            max_name_length = max_length - len(ext)
            sanitized = name[:max_name_length] + ext
        else:
            sanitized = sanitized[:max_length]
    
    return sanitized


def get_output_metadata_path(directory: Path) -> Path:
    """
    Get path for metadata file in an output directory.
    
    Args:
        directory: Output directory
    
    Returns:
        Path to metadata.json file
    """
    return directory / "metadata.json"


def create_directory_structure(
    base_dir: Path,
    subdirs: list[str] | None = None
) -> dict[str, Path]:
    """
    Create a standard directory structure for assets.
    
    Args:
        base_dir: Base directory path
        subdirs: Optional list of subdirectory names to create
    
    Returns:
        Dictionary mapping subdirectory names to paths
    
    Examples:
        >>> create_directory_structure(Path("output"), ["items", "characters", "tiles"])
        {
            'items': Path('output/items'),
            'characters': Path('output/characters'),
            'tiles': Path('output/tiles')
        }
    """
    # Create base directory
    base_dir.mkdir(parents=True, exist_ok=True)
    
    if not subdirs:
        return {'base': base_dir}
    
    # Create subdirectories
    paths = {'base': base_dir}
    for subdir in subdirs:
        subdir_path = base_dir / subdir
        subdir_path.mkdir(parents=True, exist_ok=True)
        paths[subdir] = subdir_path
    
    return paths