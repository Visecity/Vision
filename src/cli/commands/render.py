"""
Manual render command for Vision CLI.

This module provides the render command which manually renders
existing manifest JSON files to PNG format.
"""

import json
import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from src.rendering.manifest_renderer import ManifestRenderer, ManifestParseError
from src.rendering.pixel import Color

console = Console()
logger = logging.getLogger(__name__)


def render(
    manifest_path: Path = typer.Argument(
        ...,
        help="Path to manifest JSON file",
        exists=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output PNG path (default: same location as manifest)",
    ),
    scale: int = typer.Option(
        1,
        "--scale",
        "-s",
        help="Scale factor (1-16)",
        min=1,
        max=16,
    ),
    transparent_color: Optional[str] = typer.Option(
        None,
        "--transparent-color",
        help="Color to treat as transparent (e.g., '#FF00FF')",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """
    Manually render manifest JSON to PNG.
    
    Useful for re-rendering existing manifests with different settings
    or when automatic rendering was skipped during generation.
    
    Examples:
    
        # Render manifest to PNG (default location)
        vision render chest.json
        
        # Specify custom output path
        vision render sword.json --output sprites/sword.png
        
        # Render with 4x scaling
        vision render player.json --scale 4
        
        # Use custom transparent color
        vision render icon.json --transparent-color "#FF00FF"
    """
    try:
        # Validate manifest file
        if not manifest_path.exists():
            console.print(f"[bold red]Error:[/bold red] Manifest file not found: {manifest_path}")
            raise typer.Exit(1)
        
        if manifest_path.suffix.lower() != '.json':
            console.print(f"[bold red]Error:[/bold red] File must be a JSON file")
            raise typer.Exit(1)
        
        # Display info
        console.print(f"[bold]Rendering manifest:[/bold] {manifest_path}")
        
        # Load manifest
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        except json.JSONDecodeError as e:
            console.print(f"[bold red]Error:[/bold red] Invalid JSON: {e}")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] Failed to read manifest: {e}")
            raise typer.Exit(1)
        
        # Determine output path
        if output is None:
            output = manifest_path.with_suffix('.png')
        
        # Ensure output directory exists
        output.parent.mkdir(parents=True, exist_ok=True)
        
        # Parse transparent color if provided
        transparent_col = None
        if transparent_color:
            try:
                transparent_col = Color.from_hex(transparent_color)
            except ValueError as e:
                console.print(f"[bold red]Error:[/bold red] Invalid color: {transparent_color}")
                console.print("Expected format: #RRGGBB (e.g., '#FF00FF')")
                raise typer.Exit(1)
        
        # Display render settings
        console.print(f"[bold]Settings:[/bold]")
        console.print(f"  Scale: [cyan]{scale}x[/cyan]")
        if transparent_col:
            console.print(f"  Transparent color: [cyan]{transparent_color}[/cyan]")
        console.print(f"  Output: [cyan]{output}[/cyan]\n")
        
        # Create renderer
        renderer = ManifestRenderer(scale=scale, include_metadata=True)
        
        # Render
        console.print("[bold]Rendering...[/bold]")
        
        try:
            rendered_path = renderer.render_manifest_sync(
                manifest,
                output,
                transparent_color=transparent_col,
            )
        except ManifestParseError as e:
            console.print(f"[bold red]Error:[/bold red] Invalid manifest: {e}")
            if verbose:
                logger.error(f"Manifest parse error: {e}", exc_info=True)
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] Rendering failed: {e}")
            if verbose:
                logger.error(f"Rendering error: {e}", exc_info=True)
            raise typer.Exit(1)
        
        # Success
        console.print()
        console.print("[bold green]✓ Rendering complete![/bold green]")
        console.print(f"  PNG saved to: [cyan]{rendered_path}[/cyan]")
        
        # Display file size
        file_size = rendered_path.stat().st_size
        if file_size < 1024:
            size_str = f"{file_size} bytes"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        
        console.print(f"  File size: [cyan]{size_str}[/cyan]")
        
        # Display dimensions if verbose
        if verbose:
            from PIL import Image
            img = Image.open(rendered_path)
            console.print(f"  Dimensions: [cyan]{img.width}x{img.height}[/cyan]")
            console.print(f"  Mode: [cyan]{img.mode}[/cyan]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Rendering cancelled by user[/yellow]")
        raise typer.Exit(130)
    except typer.Exit:
        raise
    except Exception as e:
        if verbose:
            logger.error(f"Unexpected error: {e}", exc_info=True)
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)