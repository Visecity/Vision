"""
Atlas creation command for Vision CLI.

This module provides the create-atlas command which combines multiple
PNG assets into a single texture atlas with metadata.
"""

import asyncio
import logging
from pathlib import Path

import typer
from rich.console import Console

from src.rendering.atlas_builder import build_atlas_from_directory
from src.rendering.spritesheet import PackingAlgorithm

console = Console()
logger = logging.getLogger(__name__)


def create_atlas(
    asset_dir: Path = typer.Argument(
        ...,
        help="Directory containing PNG assets",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    output_path: Path = typer.Argument(
        ...,
        help="Output directory for atlas files",
    ),
    name: str = typer.Option(
        ...,
        "--name",
        "-n",
        help="Atlas name (used for output files)",
    ),
    algorithm: PackingAlgorithm = typer.Option(
        PackingAlgorithm.MAXRECTS,
        "--algorithm",
        "-a",
        help="Packing algorithm",
        case_sensitive=False,
    ),
    padding: int = typer.Option(
        2,
        "--padding",
        help="Padding between sprites in pixels",
        min=0,
    ),
    max_size: str = typer.Option(
        "1024x1024",
        "--max-size",
        help="Maximum atlas size (e.g., '1024x1024')",
    ),
    power_of_two: bool = typer.Option(
        True,
        "--power-of-two/--no-power-of-two",
        help="Use power-of-two dimensions for GPU optimization",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """
    Create texture atlas from existing PNG assets.
    
    Combines multiple individual PNG files into a single texture atlas
    with coordinate metadata for game engine integration.
    
    Examples:
    
        # Create atlas with default settings
        vision create-atlas ./output/items ./atlases --name items_atlas
        
        # Use shelf packing algorithm
        vision create-atlas ./sprites ./output --name characters --algorithm SHELF
        
        # Larger atlas with more padding
        vision create-atlas ./assets ./output --name world --max-size 2048x2048 --padding 4
        
        # Without power-of-two constraint
        vision create-atlas ./icons ./output --name ui_icons --no-power-of-two
    """
    try:
        # Parse max_size
        try:
            width_str, height_str = max_size.lower().split('x')
            max_width = int(width_str)
            max_height = int(height_str)
            
            if max_width <= 0 or max_height <= 0:
                raise ValueError("Dimensions must be positive")
            if max_width > 4096 or max_height > 4096:
                raise ValueError("Maximum atlas size is 4096x4096")
                
        except ValueError as e:
            console.print(
                f"[bold red]Error:[/bold red] Invalid max-size format: {max_size}"
            )
            console.print("Expected format: WIDTHxHEIGHT (e.g., '1024x1024')")
            raise typer.Exit(1)
        
        # Display configuration
        console.print(f"[bold]Creating texture atlas:[/bold] {name}\n")
        console.print(f"Scanning directory: [cyan]{asset_dir}[/cyan]")
        
        # Count PNG files
        png_files = list(asset_dir.glob("*.png"))
        if not png_files:
            console.print(f"[bold red]Error:[/bold red] No PNG files found in {asset_dir}")
            raise typer.Exit(1)
        
        console.print(f"Found: [cyan]{len(png_files)}[/cyan] PNG assets\n")
        
        console.print("[bold]Atlas Configuration:[/bold]")
        console.print(f"  Algorithm: [cyan]{algorithm.value}[/cyan]")
        console.print(f"  Max size: [cyan]{max_width}x{max_height}[/cyan]")
        console.print(f"  Padding: [cyan]{padding}px[/cyan]")
        console.print(f"  Power of two: [cyan]{power_of_two}[/cyan]\n")
        
        # Build atlas
        console.print("[bold]Building atlas...[/bold]")
        
        atlas_path, metadata = asyncio.run(
            build_atlas_from_directory(
                asset_dir,
                output_path,
                name,
                pattern="*.png",
                padding=padding,
                max_size=(max_width, max_height),
                power_of_two=power_of_two,
                packing_algorithm=algorithm,
            )
        )
        
        # Display results
        console.print()
        console.print("[bold green]✓ Atlas created successfully![/bold green]\n")
        
        atlas_metadata = metadata.get("metadata", {})
        texture_size = metadata.get("texture_size", [0, 0])
        total_sprites = atlas_metadata.get("total_sprites", 0)
        
        console.print(f"  Texture: [cyan]{atlas_path}[/cyan]")
        console.print(f"  Size: [cyan]{texture_size[0]}x{texture_size[1]}[/cyan]")
        console.print(f"  Metadata: [cyan]{atlas_path.parent / f'{name}.json'}[/cyan]")
        console.print(f"  Sprites: [cyan]{total_sprites}[/cyan]")
        
        # Calculate packing efficiency
        if total_sprites > 0:
            sprites_dict = metadata.get("sprites", {})
            total_sprite_area = sum(
                s["width"] * s["height"] for s in sprites_dict.values()
            )
            atlas_area = texture_size[0] * texture_size[1]
            efficiency = (total_sprite_area / atlas_area * 100) if atlas_area > 0 else 0
            console.print(f"  Efficiency: [cyan]{efficiency:.1f}%[/cyan]")
        
        console.print()
        
        if verbose:
            console.print("[bold]Sprite Coordinates:[/bold]")
            sprites = metadata.get("sprites", {})
            for sprite_name, coords in sprites.items():
                console.print(
                    f"  {sprite_name}: "
                    f"({coords['x']}, {coords['y']}) "
                    f"{coords['width']}x{coords['height']}"
                )
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Atlas creation cancelled by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        if verbose:
            logger.error(f"Atlas creation error: {e}", exc_info=True)
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)