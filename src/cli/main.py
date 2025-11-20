"""
Main CLI application for Vision pixel art generation.

This module provides the main entry point for the Vision CLI, defining
the Typer application and registering all subcommands.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler

from src.cli.commands import config, generate, info, list_cmd, status, batch, atlas, render

# Create console for rich output
console = Console()

# Create main Typer app
app = typer.Typer(
    name="vision",
    help="🎨 AI-powered pixel art generation for 2D games",
    add_completion=False,
    rich_markup_mode="rich",
    pretty_exceptions_enable=True,
)

# Register subcommands
app.command(name="generate", help="Generate a pixel art sprite")(generate.generate)
app.command(name="generate-batch", help="Generate multiple assets from batch file")(batch.generate_batch)
app.command(name="create-atlas", help="Create texture atlas from PNG assets")(atlas.create_atlas)
app.command(name="render", help="Manually render manifest JSON to PNG")(render.render)
app.command(name="status", help="Check workflow status")(status.status)
app.command(name="list", help="List workflows")(list_cmd.list_workflows)
app.command(name="config", help="Manage configuration")(config.config)
app.command(name="info", help="Show system information")(info.info)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print("[bold cyan]Vision Pixel Art Generator[/bold cyan]")
        console.print("Version: [green]0.1.0[/green]")
        console.print("Python: [green]3.11+[/green]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable verbose logging",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug logging",
    ),
) -> None:
    """
    Vision - AI-powered pixel art generation for 2D games.

    Use Vision to generate beautiful pixel art sprites, tiles, and assets
    for your game projects using natural language descriptions.
    """
    # Setup logging
    log_level = logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)
    
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


def cli_main() -> None:
    """Entry point for the CLI application."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    cli_main()