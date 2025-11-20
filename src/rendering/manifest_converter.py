"""
Converter to transform DetailAgent output into Manifest JSON DSL format.

This module bridges the gap between the DetailAgent's pixel implementation
output and the ManifestRenderer's expected Manifest JSON format.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ManifestConversionError(Exception):
    """Raised when conversion from DetailAgent output to Manifest fails."""
    pass


class ManifestConverter:
    """
    Converts DetailAgent output to Manifest JSON DSL format.
    
    DetailAgent produces:
    - pixel_grid: Abstract pixel data
    - shading_details: Shading information
    - final_specs: Colors used and stats
    
    ManifestRenderer expects:
    - metadata: Canvas dimensions
    - layers: Renderable elements (rect, circle, line, pixel)
    """
    
    def __init__(self) -> None:
        """Initialize the manifest converter."""
        pass
    
    def convert_detail_to_manifest(
        self,
        detail_spec: dict[str, Any],
        asset_name: str = "Generated Asset",
        asset_description: str = "AI-generated pixel art",
    ) -> dict[str, Any]:
        """
        Convert DetailAgent output to Manifest JSON format.
        
        Args:
            detail_spec: DetailAgent output with pixel_grid, shading_details, final_specs
            asset_name: Name for the asset metadata
            asset_description: Description for the asset metadata
            
        Returns:
            dict: Manifest JSON compatible with ManifestRenderer
            
        Raises:
            ManifestConversionError: If conversion fails
        """
        try:
            # Extract pixel grid data
            pixel_grid = detail_spec.get("pixel_grid", {})
            if not pixel_grid:
                raise ManifestConversionError("Missing pixel_grid in detail specification")
            
            width = pixel_grid.get("width")
            height = pixel_grid.get("height")
            
            if not width or not height:
                raise ManifestConversionError("Missing width or height in pixel_grid")
            
            # Create manifest structure
            manifest = {
                "version": "1.0",
                "metadata": {
                    "name": asset_name,
                    "description": asset_description,
                    "canvas": {
                        "width": width,
                        "height": height
                    }
                },
                "layers": []
            }
            
            # Extract color information
            final_specs = detail_spec.get("final_specs", {})
            colors_used = final_specs.get("colors_used", [])
            
            # Convert pixel data to renderable elements
            pixel_data = pixel_grid.get("data")
            
            if pixel_data:
                elements = self._convert_pixel_data_to_elements(
                    pixel_data=pixel_data,
                    width=width,
                    height=height,
                    colors_used=colors_used
                )
                
                # Create a single layer with all elements
                manifest["layers"].append({
                    "name": "Main Layer",
                    "elements": elements
                })
            else:
                logger.warning("No pixel data found in detail specification")
                # Create empty layer
                manifest["layers"].append({
                    "name": "Main Layer",
                    "elements": []
                })
            
            # Add palette information if available
            if colors_used:
                manifest["palette"] = {
                    f"color{i}": color
                    for i, color in enumerate(colors_used, 1)
                }
            
            logger.info(f"Converted detail spec to manifest: {width}x{height}, "
                       f"{len(manifest['layers'][0]['elements'])} elements")
            
            return manifest
            
        except Exception as e:
            logger.error(f"Failed to convert detail spec to manifest: {e}")
            raise ManifestConversionError(f"Conversion failed: {e}") from e
    
    def _convert_pixel_data_to_elements(
        self,
        pixel_data: Any,
        width: int,
        height: int,
        colors_used: list[str],
    ) -> list[dict[str, Any]]:
        """
        Convert pixel data to renderable elements.
        
        This handles various pixel data formats that the DetailAgent might produce:
        - List of hex colors (row-major)
        - List of lists (rows)
        - Conceptual description strings
        
        Args:
            pixel_data: Pixel data from DetailAgent
            width: Canvas width
            height: Canvas height
            colors_used: List of colors used in the sprite
            
        Returns:
            list: List of renderable elements (pixel elements)
        """
        elements: list[dict[str, Any]] = []
        
        # Handle different pixel data formats
        if isinstance(pixel_data, list):
            if len(pixel_data) > 0 and isinstance(pixel_data[0], list):
                # List of lists (rows)
                elements = self._convert_row_based_data(pixel_data)
            elif len(pixel_data) > 0 and isinstance(pixel_data[0], str):
                # Check if it's hex colors or descriptions
                if pixel_data[0].startswith("#"):
                    # Flattened array of hex colors
                    elements = self._convert_flat_hex_data(pixel_data, width)
                else:
                    # Conceptual descriptions - create placeholder
                    logger.warning("Pixel data contains descriptions, creating placeholder")
                    elements = self._create_placeholder_elements(width, height, colors_used)
            else:
                logger.warning(f"Unknown pixel data format: {type(pixel_data[0])}")
                elements = self._create_placeholder_elements(width, height, colors_used)
        elif isinstance(pixel_data, str):
            # Description string - create placeholder
            logger.warning("Pixel data is a description string, creating placeholder")
            elements = self._create_placeholder_elements(width, height, colors_used)
        else:
            logger.warning(f"Unknown pixel data type: {type(pixel_data)}")
            elements = self._create_placeholder_elements(width, height, colors_used)
        
        return elements
    
    def _normalize_color(self, color: str) -> str:
        """
        Normalize various LLM-generated color formats to standard #RRGGBB.
        
        This is a safety layer to handle cases where the LLM doesn't follow
        instructions perfectly despite retries.
        
        Args:
            color: Color string in various formats
            
        Returns:
            str: Normalized color in #RRGGBB format or "transparent"
        """
        if not color or color == "transparent":
            return "transparent"
        
        # Strip whitespace
        color = color.strip()
        
        # Handle 8-character hex (with alpha channel) - strip alpha
        if len(color) == 9 and color.startswith('#'):
            logger.warning(f"Found 8-char hex color {color}, stripping alpha channel")
            return color[:7]  # Keep only #RRGGBB
        
        # Handle rgba() format - convert to solid black (can't preserve alpha)
        if 'rgba' in color.lower():
            logger.warning(f"Found rgba() color {color}, converting to black")
            return '#000000'
        
        # Handle rgb() format - try to extract values
        if 'rgb' in color.lower():
            logger.warning(f"Found rgb() color {color}, attempting to parse")
            try:
                # Extract numbers from rgb(r,g,b)
                import re
                nums = re.findall(r'\d+', color)
                if len(nums) >= 3:
                    r, g, b = int(nums[0]), int(nums[1]), int(nums[2])
                    return f"#{r:02x}{g:02x}{b:02x}"
            except:
                pass
            return '#000000'
        
        # Handle symbolic codes - map to reasonable defaults
        SYMBOLIC_MAP = {
            '#T': 'transparent',
            '#B': '#000000',  # Black
            '#W': '#FFFFFF',  # White
            '#H': '#FFFFFF',  # Highlight -> white
            '#M': '#808080',  # Mid-tone -> gray
            '#D': '#404040',  # Dark -> dark gray
            '#S': '#202020',  # Shadow -> very dark gray
            '#O': '#000000',  # Outline -> black
        }
        
        upper_color = color.upper()
        if upper_color in SYMBOLIC_MAP:
            logger.warning(f"Found symbolic color {color}, mapping to {SYMBOLIC_MAP[upper_color]}")
            return SYMBOLIC_MAP[upper_color]
        
        # Handle 3-char hex - expand to 6-char
        if color.startswith('#') and len(color) == 4:
            hex_part = color[1:]
            if all(c in '0123456789ABCDEFabcdef' for c in hex_part):
                normalized = f"#{hex_part[0]*2}{hex_part[1]*2}{hex_part[2]*2}"
                logger.info(f"Expanded 3-char hex {color} to {normalized}")
                return normalized
        
        # Validate proper hex format
        if color.startswith('#'):
            hex_part = color[1:]
            if len(hex_part) == 6 and all(c in '0123456789ABCDEFabcdef' for c in hex_part):
                return color  # Valid!
        
        # Unknown format - return black and log error
        logger.error(f"Unknown color format: {color}, defaulting to black")
        return '#000000'
    
    def _convert_row_based_data(self, rows: list[list[str]]) -> list[dict[str, Any]]:
        """Convert row-based pixel data to pixel elements with color normalization."""
        elements = []
        
        for y, row in enumerate(rows):
            for x, color in enumerate(row):
                # Normalize color (handles transparent, symbolic codes, etc.)
                normalized = self._normalize_color(color)
                
                # Skip transparent pixels
                if normalized != "transparent":
                    elements.append({
                        "type": "pixel",
                        "x": x,
                        "y": y,
                        "fill": normalized
                    })
        
        return elements
    
    def _convert_flat_hex_data(self, data: list[str], width: int) -> list[dict[str, Any]]:
        """Convert flattened hex color array to pixel elements with color normalization."""
        elements = []
        
        for i, color in enumerate(data):
            # Normalize color
            normalized = self._normalize_color(color)
            
            # Skip transparent pixels
            if normalized != "transparent":
                x = i % width
                y = i // width
                elements.append({
                    "type": "pixel",
                    "x": x,
                    "y": y,
                    "fill": normalized
                })
        
        return elements
    
    def _create_placeholder_elements(
        self,
        width: int,
        height: int,
        colors_used: list[str],
    ) -> list[dict[str, Any]]:
        """
        Create placeholder elements when pixel data is not parseable.
        
        This creates a simple colored rectangle as a fallback.
        """
        elements = []
        
        # Use first color or default to gray
        fill_color = colors_used[0] if colors_used else "#888888"
        
        # Create a centered rectangle (80% of canvas)
        padding = max(1, min(width, height) // 10)
        
        elements.append({
            "type": "rect",
            "x": padding,
            "y": padding,
            "width": width - (padding * 2),
            "height": height - (padding * 2),
            "fill": fill_color
        })
        
        logger.info(f"Created placeholder element: {width}x{height} rectangle with color {fill_color}")
        
        return elements


# Convenience function
def convert_detail_to_manifest(
    detail_spec: dict[str, Any],
    asset_name: str = "Generated Asset",
    asset_description: str = "AI-generated pixel art",
) -> dict[str, Any]:
    """
    Convert DetailAgent output to Manifest JSON format.
    
    Convenience function that creates a converter and performs conversion.
    
    Args:
        detail_spec: DetailAgent output
        asset_name: Name for the asset
        asset_description: Description for the asset
        
    Returns:
        dict: Manifest JSON compatible with ManifestRenderer
        
    Example:
        >>> detail_output = {"pixel_grid": {...}, "shading_details": {...}}
        >>> manifest = convert_detail_to_manifest(detail_output, "My Sprite")
        >>> renderer.render_manifest_sync(manifest, "output.png")
    """
    converter = ManifestConverter()
    return converter.convert_detail_to_manifest(
        detail_spec=detail_spec,
        asset_name=asset_name,
        asset_description=asset_description
    )