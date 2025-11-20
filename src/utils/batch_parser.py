"""
Batch file parsing for YAML and JSON batch definitions.

This module provides functionality to parse batch definition files
in YAML or JSON format.
"""

import json
import logging
from pathlib import Path
from typing import Any

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from src.core.models import (
    AnimationConfig,
    AssetDefinition,
    AssetStyle,
    AssetType,
    BatchDefinition,
    Dimensions,
)

logger = logging.getLogger(__name__)


class BatchParseError(Exception):
    """Exception raised when batch file parsing fails."""
    pass


def parse_batch_file(file_path: Path) -> BatchDefinition:
    """
    Parse YAML or JSON batch definition file.
    
    Automatically detects file format from extension (.yaml, .yml, .json).
    
    Args:
        file_path: Path to batch definition file
    
    Returns:
        BatchDefinition object
    
    Raises:
        FileNotFoundError: If file doesn't exist
        BatchParseError: If file cannot be parsed
        ValueError: If batch definition is invalid
    
    Example:
        >>> batch_def = parse_batch_file(Path("assets/items.yaml"))
        >>> print(f"Batch: {batch_def.batch_name}, {len(batch_def.assets)} assets")
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Batch file not found: {file_path}")
    
    # Determine format from extension
    extension = file_path.suffix.lower()
    
    if extension in ('.yaml', '.yml'):
        if not YAML_AVAILABLE:
            raise BatchParseError(
                "YAML support not available. Install PyYAML: pip install pyyaml"
            )
        return parse_yaml(file_path)
    elif extension == '.json':
        return parse_json(file_path)
    else:
        raise BatchParseError(
            f"Unsupported file format: {extension}. "
            "Use .yaml, .yml, or .json"
        )


def parse_yaml(file_path: Path) -> BatchDefinition:
    """
    Parse YAML batch definition file.
    
    Args:
        file_path: Path to YAML file
    
    Returns:
        BatchDefinition object
    
    Raises:
        BatchParseError: If YAML cannot be parsed
    """
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        
        logger.info(f"Parsed YAML batch file: {file_path}")
        return _parse_batch_data(data, file_path)
        
    except yaml.YAMLError as e:
        raise BatchParseError(f"Invalid YAML in {file_path}: {e}")
    except Exception as e:
        raise BatchParseError(f"Failed to parse YAML {file_path}: {e}")


def parse_json(file_path: Path) -> BatchDefinition:
    """
    Parse JSON batch definition file.
    
    Args:
        file_path: Path to JSON file
    
    Returns:
        BatchDefinition object
    
    Raises:
        BatchParseError: If JSON cannot be parsed
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        logger.info(f"Parsed JSON batch file: {file_path}")
        return _parse_batch_data(data, file_path)
        
    except json.JSONDecodeError as e:
        raise BatchParseError(f"Invalid JSON in {file_path}: {e}")
    except Exception as e:
        raise BatchParseError(f"Failed to parse JSON {file_path}: {e}")


def _parse_batch_data(data: dict[str, Any], file_path: Path) -> BatchDefinition:
    """
    Parse batch data dictionary into BatchDefinition.
    
    Args:
        data: Parsed YAML/JSON data
        file_path: Original file path (for error messages)
    
    Returns:
        BatchDefinition object
    
    Raises:
        BatchParseError: If data structure is invalid
    """
    try:
        # Extract batch-level settings
        batch_name = data.get('batch_name')
        if not batch_name:
            raise BatchParseError("Missing required field: batch_name")
        
        output_dir_str = data.get('output_dir')
        if not output_dir_str:
            raise BatchParseError("Missing required field: output_dir")
        output_dir = Path(output_dir_str)
        
        # Optional settings
        create_atlas = data.get('create_atlas', False)
        atlas_name = data.get('atlas_name')
        parallel_count = data.get('parallel_count', 1)
        
        # Default settings
        default_style_str = data.get('default_style', 'stardew_valley')
        default_style = AssetStyle(default_style_str)
        
        default_dimensions_data = data.get('default_dimensions', {'width': 16, 'height': 16})
        default_dimensions = Dimensions(**default_dimensions_data)
        
        default_asset_type_str = data.get('default_asset_type', 'sprite')
        default_asset_type = AssetType(default_asset_type_str)
        
        # Parse assets
        assets_data = data.get('assets', [])
        if not assets_data:
            raise BatchParseError("No assets defined in batch")
        
        assets = []
        for i, asset_data in enumerate(assets_data):
            try:
                asset_def = _parse_asset_definition(asset_data)
                assets.append(asset_def)
            except Exception as e:
                raise BatchParseError(f"Error parsing asset {i+1}: {e}")
        
        # Create BatchDefinition
        batch_def = BatchDefinition(
            batch_name=batch_name,
            output_dir=output_dir,
            create_atlas=create_atlas,
            atlas_name=atlas_name,
            default_style=default_style,
            default_dimensions=default_dimensions,
            default_asset_type=default_asset_type,
            assets=assets,
            parallel_count=parallel_count,
        )
        
        logger.debug(
            f"Parsed batch definition: {batch_name}, "
            f"{len(assets)} assets, parallel={parallel_count}"
        )
        
        return batch_def
        
    except ValueError as e:
        raise BatchParseError(f"Invalid batch definition in {file_path}: {e}")
    except KeyError as e:
        raise BatchParseError(f"Missing required field in {file_path}: {e}")


def _parse_asset_definition(data: dict[str, Any]) -> AssetDefinition:
    """
    Parse asset definition from dictionary.
    
    Args:
        data: Asset data dictionary
    
    Returns:
        AssetDefinition object
    """
    # Required field
    description = data.get('description')
    if not description:
        raise ValueError("Missing required field: description")
    
    # Optional fields
    name = data.get('name')
    category = data.get('category')
    tags = data.get('tags', [])
    
    # Optional dimensions
    dimensions = None
    if 'dimensions' in data:
        dim_data = data['dimensions']
        if isinstance(dim_data, list) and len(dim_data) == 2:
            dimensions = Dimensions(width=dim_data[0], height=dim_data[1])
        elif isinstance(dim_data, dict):
            dimensions = Dimensions(**dim_data)
        elif isinstance(dim_data, str):
            # Parse "16x16" format
            parts = dim_data.lower().split('x')
            if len(parts) == 2:
                dimensions = Dimensions(width=int(parts[0]), height=int(parts[1]))
    
    # Optional style
    style = None
    if 'style' in data:
        style = AssetStyle(data['style'])
    
    # Optional asset type
    asset_type = None
    if 'asset_type' in data:
        asset_type = AssetType(data['asset_type'])
    
    # Optional animation
    animation = None
    if 'animation' in data:
        anim_data = data['animation']
        if isinstance(anim_data, dict):
            animation = AnimationConfig(**anim_data)
    
    return AssetDefinition(
        description=description,
        name=name,
        dimensions=dimensions,
        style=style,
        asset_type=asset_type,
        category=category,
        tags=tags,
        animation=animation,
    )


def validate_batch_file(file_path: Path) -> tuple[bool, list[str]]:
    """
    Validate a batch file without fully parsing it.
    
    Useful for checking files before submission.
    
    Args:
        file_path: Path to batch file
    
    Returns:
        Tuple of (is_valid, list of error messages)
    
    Example:
        >>> is_valid, errors = validate_batch_file(Path("batch.yaml"))
        >>> if not is_valid:
        ...     for error in errors:
        ...         print(f"Error: {error}")
    """
    errors = []
    
    if not file_path.exists():
        errors.append(f"File not found: {file_path}")
        return False, errors
    
    try:
        batch_def = parse_batch_file(file_path)
        
        # Additional validation checks
        if len(batch_def.assets) == 0:
            errors.append("Batch contains no assets")
        
        if batch_def.parallel_count < 1 or batch_def.parallel_count > 10:
            errors.append(f"parallel_count must be 1-10, got {batch_def.parallel_count}")
        
        # Validate each asset
        for i, asset in enumerate(batch_def.assets, 1):
            if len(asset.description) < 10:
                errors.append(f"Asset {i}: description too short (minimum 10 characters)")
            
            if asset.dimensions:
                if asset.dimensions.width < 1 or asset.dimensions.height < 1:
                    errors.append(f"Asset {i}: invalid dimensions {asset.dimensions}")
        
        return len(errors) == 0, errors
        
    except Exception as e:
        errors.append(str(e))
        return False, errors


def create_example_batch_file(
    output_path: Path,
    format: str = 'yaml',
) -> None:
    """
    Create an example batch file.
    
    Useful for users learning the batch file format.
    
    Args:
        output_path: Where to save the example file
        format: File format ('yaml' or 'json')
    
    Example:
        >>> create_example_batch_file(Path("example_batch.yaml"))
    """
    example_data = {
        'batch_name': 'example_batch',
        'output_dir': './output/examples',
        'create_atlas': True,
        'atlas_name': 'example_atlas',
        'parallel_count': 2,
        'default_style': 'stardew_valley',
        'default_dimensions': {'width': 16, 'height': 16},
        'default_asset_type': 'sprite',
        'assets': [
            {
                'description': 'wooden chest for storing items',
                'name': 'chest_wood',
                'category': 'containers',
                'tags': ['furniture', 'storage'],
            },
            {
                'description': 'red health potion in a glass bottle',
                'name': 'potion_health',
                'dimensions': [12, 16],
                'category': 'consumables',
                'tags': ['potion', 'healing'],
            },
            {
                'description': 'gold coin with shine effect',
                'name': 'coin_gold',
                'dimensions': [8, 8],
                'category': 'currency',
            },
        ],
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if format.lower() == 'yaml':
        if not YAML_AVAILABLE:
            raise RuntimeError("YAML support not available")
        with open(output_path, 'w') as f:
            yaml.dump(example_data, f, default_flow_style=False, sort_keys=False)
    elif format.lower() == 'json':
        with open(output_path, 'w') as f:
            json.dump(example_data, f, indent=2)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    logger.info(f"Created example batch file: {output_path}")