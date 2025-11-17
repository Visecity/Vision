"""
Info command implementation for Vision CLI.

This module provides the info command which displays system information,
available agents, and version details.
"""

import logging
import platform
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.cli.utils import handle_error
from src.core.config import get_settings

console = Console()
logger = logging.getLogger(__name__)


def info(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output information as JSON",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed system information",
    ),
) -> None:
    """
    Display system information and configuration status.

    This command shows information about the Vision installation,
    available agents, system details, and dependency versions.

    Examples:

        # Show system info
        vision info

        # Show as JSON
        vision info --json

        # Show verbose output
        vision info --verbose
    """
    try:
        if json_output:
            info_dict = _collect_info(verbose)
            import json
            console.print(json.dumps(info_dict, indent=2))
        else:
            _display_info(verbose)

    except Exception as e:
        handle_error(e, verbose)
        raise typer.Exit(1)


def _collect_info(verbose: bool) -> dict:
    """
    Collect system information as dictionary.

    Args:
        verbose: Whether to include detailed information

    Returns:
        Dictionary with system information
    """
    settings = get_settings()

    info_dict = {
        "version": "0.1.0",
        "python_version": sys.version,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "agents": {
            "orchestrator": settings.models.orchestrator_model,
            "design": settings.models.design_agent_model,
            "palette": settings.models.palette_agent_model,
            "detail": settings.models.detail_agent_model,
            "animation": settings.models.animation_agent_model,
        },
        "configuration": {
            "redis_configured": bool(settings.redis.host),
            "api_key_set": bool(settings.anthropic_api_key),
            "output_dir": str(settings.output.output_dir),
        },
    }

    if verbose:
        # Add dependency versions
        try:
            import anthropic
            import langgraph
            import redis
            import PIL
            import typer as typer_pkg
            import rich as rich_pkg

            info_dict["dependencies"] = {
                "anthropic": anthropic.__version__,
                "langgraph": langgraph.__version__ if hasattr(langgraph, "__version__") else "unknown",
                "redis": redis.__version__,
                "pillow": PIL.__version__,
                "typer": typer_pkg.__version__,
                "rich": rich_pkg.__version__,
            }
        except ImportError:
            info_dict["dependencies"] = "Unable to determine versions"

    return info_dict


def _display_info(verbose: bool) -> None:
    """
    Display system information with rich formatting.

    Args:
        verbose: Whether to show detailed information
    """
    settings = get_settings()

    # Header
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Vision Pixel Art Generator[/bold cyan]\n"
        "[dim]AI-powered pixel art generation for 2D games[/dim]",
        border_style="cyan",
    ))
    console.print()

    # Version Information
    table = Table(title="Version Information", show_header=True, header_style="bold cyan")
    table.add_column("Component", style="cyan")
    table.add_column("Version", style="green")
    table.add_row("Vision", "0.1.0")
    table.add_row("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    console.print(table)
    console.print()

    # System Information
    if verbose:
        table = Table(title="System Information", show_header=True, header_style="bold cyan")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Operating System", platform.system())
        table.add_row("Release", platform.release())
        table.add_row("Machine", platform.machine())
        table.add_row("Processor", platform.processor() or "Unknown")
        console.print(table)
        console.print()

    # Available Agents
    table = Table(title="Available Agents", show_header=True, header_style="bold cyan")
    table.add_column("Agent", style="cyan")
    table.add_column("Model", style="green")
    table.add_row("Orchestrator", settings.models.orchestrator_model)
    table.add_row("Design Agent", settings.models.design_agent_model)
    table.add_row("Palette Agent", settings.models.palette_agent_model)
    table.add_row("Detail Agent", settings.models.detail_agent_model)
    table.add_row("Animation Agent", settings.models.animation_agent_model)
    console.print(table)
    console.print()

    # Configuration Status
    table = Table(title="Configuration Status", show_header=True, header_style="bold cyan")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")

    # Check API key
    api_status = "[green]✓ Configured[/green]" if settings.anthropic_api_key else "[red]✗ Not Set[/red]"
    table.add_row("Anthropic API Key", api_status)

    # Check Redis
    redis_status = f"[green]✓ {settings.redis.host}:{settings.redis.port}[/green]"
    table.add_row("Redis Connection", redis_status)

    # Check output directory
    output_status = f"[green]✓ {settings.output.output_dir}[/green]"
    table.add_row("Output Directory", output_status)

    console.print(table)
    console.print()

    # Dependency Versions (verbose only)
    if verbose:
        try:
            import anthropic
            import langgraph
            import redis
            import PIL
            import typer as typer_pkg
            import rich as rich_pkg

            table = Table(title="Dependency Versions", show_header=True, header_style="bold cyan")
            table.add_column("Package", style="cyan")
            table.add_column("Version", style="green")
            table.add_row("anthropic", anthropic.__version__)
            table.add_row("langgraph", getattr(langgraph, "__version__", "unknown"))
            table.add_row("redis", redis.__version__)
            table.add_row("pillow", PIL.__version__)
            table.add_row("typer", typer_pkg.__version__)
            table.add_row("rich", rich_pkg.__version__)
            console.print(table)
            console.print()
        except ImportError as e:
            console.print(f"[yellow]Warning: Unable to determine dependency versions: {e}[/yellow]\n")

    # Usage hints
    console.print("[bold]Quick Start:[/bold]")
    console.print("  • Generate a sprite: [cyan]vision generate 'oak tree'[/cyan]")
    console.print("  • Check status: [cyan]vision status <workflow-id>[/cyan]")
    console.print("  • List workflows: [cyan]vision list[/cyan]")
    console.print("  • View config: [cyan]vision config show[/cyan]")
    console.print()
    console.print("[dim]For more information, use: vision --help[/dim]")