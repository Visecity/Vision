"""
Generate command implementation for Vision CLI.

This module provides the generate command which creates pixel art sprites
using the Vision multi-agent workflow.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt

from src.cli.utils import (
    ProgressHandler,
    format_generation_result,
    get_output_directory,
    get_session_id,
    handle_error,
    parse_dimensions,
    save_manifest,
    save_metadata,
)
from src.utils.file_manager import derive_asset_name, organize_output_files
from src.rendering.manifest_renderer import ManifestRenderer
from src.core.config import get_settings
from src.core.models import (
    AnimationConfig,
    AssetStyle,
    AssetType,
    Dimensions,
    SpriteRequest,
)
from src.state.executor import WorkflowExecutor

console = Console()
logger = logging.getLogger(__name__)


def generate(
    description: str = typer.Argument(
        ...,
        help="Description of the sprite to generate",
    ),
    dimensions: str = typer.Option(
        "16x16",
        "--dimensions",
        "-d",
        help="Sprite dimensions (e.g., 16x16, 32x32, 64x64)",
    ),
    style: str = typer.Option(
        "stardew_valley",
        "--style",
        "-s",
        help="Art style (stardew_valley, retro_8bit, retro_16bit, pixel_art, custom)",
    ),
    asset_type: str = typer.Option(
        "sprite",
        "--type",
        "-t",
        help="Asset type (sprite, tile, icon, character, object, ui_element)",
    ),
    animate: bool = typer.Option(
        False,
        "--animate",
        "-a",
        help="Generate animation frames",
    ),
    frames: int = typer.Option(
        4,
        "--frames",
        "-f",
        help="Number of animation frames (only used with --animate)",
    ),
    frame_duration: int = typer.Option(
        200,
        "--frame-duration",
        help="Frame duration in milliseconds (only used with --animate)",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        help="Custom asset name (default: derived from description)",
    ),
    no_render: bool = typer.Option(
        False,
        "--no-render",
        help="Skip automatic PNG rendering (generate JSON only)",
    ),
    category: Optional[str] = typer.Option(
        None,
        "--category",
        help="Asset category for organization (e.g., 'items', 'characters')",
    ),
    render_scale: int = typer.Option(
        1,
        "--render-scale",
        help="PNG scale factor (1-16, default: 1)",
    ),
    session_id: Optional[str] = typer.Option(
        None,
        "--session-id",
        help="Session ID for grouping workflows",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for generated files",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Interactive mode with prompts",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output results as JSON",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """
    Generate a pixel art sprite using AI.

    This command uses Vision's multi-agent system to generate pixel art
    sprites from natural language descriptions.

    Examples:

        # Generate a simple sprite with auto-rendering
        vision generate "oak tree"

        # Generate with custom name
        vision generate "wooden chest" --name chest_wood --dimensions 16x16

        # Skip rendering (manifest only)
        vision generate "sword sprite" --no-render

        # With category organization
        vision generate "health potion" --category items --dimensions 12x16

        # Scaled rendering
        vision generate "player character" --render-scale 4 --dimensions 32x32

        # Generate animated sprite
        vision generate "walking farmer" --animate --frames 8

        # Interactive mode
        vision generate --interactive
    """
    try:
        # Interactive mode
        if interactive:
            console.print("[bold cyan]Interactive Sprite Generation[/bold cyan]\n")
            description = Prompt.ask("Enter sprite description")
            dimensions = Prompt.ask("Enter dimensions", default="16x16")
            style = Prompt.ask(
                "Enter style",
                default="stardew_valley",
                choices=["stardew_valley", "retro_8bit", "retro_16bit", "pixel_art", "custom"],
            )
            animate = Confirm.ask("Generate animation?", default=False)
            if animate:
                frames = IntPrompt.ask("Number of frames", default=4)
                frame_duration = IntPrompt.ask("Frame duration (ms)", default=200)

        # Parse dimensions
        try:
            width, height = parse_dimensions(dimensions)
            dims = Dimensions(width=width, height=height)
        except ValueError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(1)

        # Parse style
        try:
            asset_style = AssetStyle(style.lower())
        except ValueError:
            console.print(f"[bold red]Error:[/bold red] Invalid style: {style}")
            console.print(f"Valid styles: {', '.join([s.value for s in AssetStyle])}")
            raise typer.Exit(1)

        # Parse asset type
        try:
            asset_type_enum = AssetType(asset_type.lower())
        except ValueError:
            console.print(f"[bold red]Error:[/bold red] Invalid asset type: {asset_type}")
            console.print(f"Valid types: {', '.join([t.value for t in AssetType])}")
            raise typer.Exit(1)

        # Create animation config if requested
        animation_config = None
        if animate:
            animation_config = AnimationConfig(
                frame_count=frames,
                frame_duration=frame_duration,
                loop=True,
            )

        # Create sprite request
        request = SpriteRequest(
            description=description,
            asset_type=asset_type_enum,
            style=asset_style,
            dimensions=dims,
            animation=animation_config,
        )

        # Display request info
        if not json_output:
            console.print("\n[bold]Generation Request:[/bold]")
            console.print(f"  Description: [cyan]{description}[/cyan]")
            console.print(f"  Dimensions: [cyan]{width}x{height}[/cyan]")
            console.print(f"  Style: [cyan]{style}[/cyan]")
            console.print(f"  Type: [cyan]{asset_type}[/cyan]")
            if animate:
                console.print(f"  Animation: [cyan]{frames} frames @ {frame_duration}ms[/cyan]")
            console.print()

        # Get session ID
        session = get_session_id(session_id)

        # Validate render_scale
        if render_scale < 1 or render_scale > 16:
            console.print(f"[bold red]Error:[/bold red] render-scale must be between 1 and 16")
            raise typer.Exit(1)

        # Get output directory
        settings = get_settings()
        base_output = output_dir or settings.output.output_dir
        request_output_dir = get_output_directory(base_output, str(request.request_id))

        # Derive asset name if not provided
        asset_name = name or derive_asset_name(description)

        # Organize output files with category
        file_paths = organize_output_files(asset_name, request_output_dir, category)

        # Execute workflow
        result = asyncio.run(_execute_generation(request, session, verbose))

        # Save results
        if result.status.value == "completed":
            manifest_path = None
            png_path = None

            if result.manifest_json:
                manifest_path = save_manifest(
                    result.manifest_json,
                    file_paths['directory'],
                    filename=f"{asset_name}.json",
                )
                if not json_output:
                    console.print(f"[green]✓[/green] Manifest saved to: {manifest_path}")

                # Render to PNG unless --no-render specified
                if not no_render:
                    try:
                        renderer = ManifestRenderer(scale=render_scale, include_metadata=True)
                        png_path = renderer.render_manifest_sync(
                            result.manifest_json,
                            file_paths['directory'] / f"{asset_name}.png",
                        )
                        if not json_output:
                            console.print(f"[green]✓[/green] PNG rendered to: {png_path}")
                    except Exception as e:
                        console.print(f"[yellow]⚠[/yellow] Rendering failed: {e}")
                        if verbose:
                            logger.error(f"Rendering error: {e}", exc_info=True)

            if result.metadata:
                metadata_dict = result.metadata.model_dump()
                # Add file paths to metadata
                metadata_dict['files'] = {
                    'manifest': str(manifest_path) if manifest_path else None,
                    'png': str(png_path) if png_path else None,
                }
                metadata_path = save_metadata(
                    metadata_dict,
                    file_paths['directory'],
                )
                if not json_output:
                    console.print(f"[green]✓[/green] Metadata saved to: {metadata_path}")

        # Display results
        if json_output:
            import json
            result_dict = result.model_dump()
            console.print(json.dumps(result_dict, indent=2, default=str))
        else:
            result_dict = result.model_dump()
            panel = format_generation_result(result_dict)
            console.print(panel)

            if result.status.value == "completed":
                console.print(f"\n[bold green]✓ Generation complete![/bold green]")
                console.print(f"Asset name: [cyan]{asset_name}[/cyan]")
                console.print(f"Output directory: [cyan]{file_paths['directory']}[/cyan]")
                if category:
                    console.print(f"Category: [cyan]{category}[/cyan]")
            else:
                console.print(f"\n[bold red]✗ Generation failed[/bold red]")
                if result.error_message:
                    console.print(f"Error: {result.error_message}")

    except KeyboardInterrupt:
        console.print("\n[yellow]Generation cancelled by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        handle_error(e, verbose)
        raise typer.Exit(1)


async def _execute_generation(
    request: SpriteRequest,
    session_id: str,
    verbose: bool,
) -> "GenerationResult":  # type: ignore
    """
    Execute the generation workflow asynchronously.

    Args:
        request: Sprite generation request
        session_id: Session identifier
        verbose: Whether to show verbose output

    Returns:
        Generation result
    """
    # Create executor
    async with WorkflowExecutor() as executor:
        # Create progress handler
        with ProgressHandler("Generating sprite") as progress:
            # Execute workflow with progress callback
            result = await executor.execute(
                request=request,
                session_id=session_id,
                progress_callback=progress.update,
            )

        return result