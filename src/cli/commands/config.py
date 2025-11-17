"""
Config command implementation for Vision CLI.

This module provides the config command which manages configuration
settings, validates connections, and displays current settings.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from src.cli.utils import handle_error
from src.core.config import get_settings, reset_settings

console = Console()
logger = logging.getLogger(__name__)

# Create subcommands
config_app = typer.Typer(name="config", help="Manage configuration")


def config(
    ctx: typer.Context,
) -> None:
    """
    Manage Vision configuration settings.

    This command provides subcommands to view, update, and validate
    the Vision configuration.

    Examples:

        # Show current configuration
        vision config show

        # Validate configuration
        vision config validate

        # Set environment variable
        vision config set ANTHROPIC_API_KEY sk-ant-...
    """
    # This is the main command, subcommands will be registered
    pass


@config_app.command("show")
def show_config(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output configuration as JSON",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show all configuration details",
    ),
) -> None:
    """
    Show current configuration settings.

    Displays the current Vision configuration, including API keys
    (masked), Redis settings, model configuration, and output directories.

    Examples:

        # Show configuration
        vision config show

        # Show as JSON
        vision config show --json

        # Show verbose output
        vision config show --verbose
    """
    try:
        settings = get_settings()

        if json_output:
            import json
            config_dict = {
                "anthropic_api_key": "***" + settings.anthropic_api_key[-8:] if settings.anthropic_api_key else None,
                "redis": {
                    "host": settings.redis.host,
                    "port": settings.redis.port,
                    "db": settings.redis.db,
                },
                "models": {
                    "orchestrator": settings.models.orchestrator_model,
                    "design_agent": settings.models.design_agent_model,
                    "palette_agent": settings.models.palette_agent_model,
                    "detail_agent": settings.models.detail_agent_model,
                    "animation_agent": settings.models.animation_agent_model,
                },
                "output": {
                    "output_dir": str(settings.output.output_dir),
                    "asset_dir": str(settings.output.asset_dir),
                    "temp_dir": str(settings.output.temp_dir),
                },
                "performance": {
                    "max_retries": settings.performance.max_retries,
                    "timeout": settings.performance.timeout,
                    "enable_caching": settings.performance.enable_caching,
                },
                "debug": settings.debug,
                "log_level": settings.log_level,
            }
            console.print(json.dumps(config_dict, indent=2))
        else:
            # Display as formatted table
            console.print("\n[bold cyan]Vision Configuration[/bold cyan]\n")

            # API Configuration
            table = Table(title="API Configuration", show_header=True, header_style="bold")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")
            
            masked_key = "***" + settings.anthropic_api_key[-8:] if settings.anthropic_api_key else "[red]Not Set[/red]"
            table.add_row("Anthropic API Key", masked_key)
            console.print(table)
            console.print()

            # Redis Configuration
            table = Table(title="Redis Configuration", show_header=True, header_style="bold")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Host", settings.redis.host)
            table.add_row("Port", str(settings.redis.port))
            table.add_row("Database", str(settings.redis.db))
            table.add_row("URL", settings.redis.url)
            console.print(table)
            console.print()

            # Model Configuration
            if verbose:
                table = Table(title="Model Configuration", show_header=True, header_style="bold")
                table.add_column("Agent", style="cyan")
                table.add_column("Model", style="green")
                table.add_row("Orchestrator", settings.models.orchestrator_model)
                table.add_row("Design Agent", settings.models.design_agent_model)
                table.add_row("Palette Agent", settings.models.palette_agent_model)
                table.add_row("Detail Agent", settings.models.detail_agent_model)
                table.add_row("Animation Agent", settings.models.animation_agent_model)
                console.print(table)
                console.print()

            # Output Configuration
            table = Table(title="Output Configuration", show_header=True, header_style="bold")
            table.add_column("Setting", style="cyan")
            table.add_column("Path", style="green")
            table.add_row("Output Directory", str(settings.output.output_dir))
            table.add_row("Asset Directory", str(settings.output.asset_dir))
            table.add_row("Temp Directory", str(settings.output.temp_dir))
            console.print(table)
            console.print()

            # Performance Configuration
            if verbose:
                table = Table(title="Performance Configuration", show_header=True, header_style="bold")
                table.add_column("Setting", style="cyan")
                table.add_column("Value", style="green")
                table.add_row("Max Retries", str(settings.performance.max_retries))
                table.add_row("Timeout", f"{settings.performance.timeout}s")
                table.add_row("Enable Caching", str(settings.performance.enable_caching))
                table.add_row("Max Concurrent Agents", str(settings.performance.max_concurrent_agents))
                console.print(table)
                console.print()

            # General Settings
            table = Table(title="General Settings", show_header=True, header_style="bold")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Debug Mode", str(settings.debug))
            table.add_row("Log Level", settings.log_level)
            console.print(table)

    except Exception as e:
        handle_error(e, verbose)
        raise typer.Exit(1)


@config_app.command("validate")
def validate_config(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed validation results",
    ),
) -> None:
    """
    Validate configuration and test connections.

    This command checks if all required configuration is present and
    tests connections to Redis and the Anthropic API.

    Examples:

        # Validate configuration
        vision config validate

        # Validate with verbose output
        vision config validate --verbose
    """
    try:
        console.print("\n[bold cyan]Validating Configuration...[/bold cyan]\n")

        # Check settings
        settings = get_settings()
        validation_passed = True

        # Check API key
        console.print("[cyan]Checking Anthropic API key...[/cyan]")
        if settings.anthropic_api_key:
            console.print("[green]✓[/green] API key is set")
        else:
            console.print("[red]✗[/red] API key is not set")
            console.print("  Set ANTHROPIC_API_KEY environment variable")
            validation_passed = False

        # Check Redis connection
        console.print("\n[cyan]Checking Redis connection...[/cyan]")
        redis_ok = asyncio.run(_test_redis_connection(settings, verbose))
        if redis_ok:
            console.print("[green]✓[/green] Redis connection successful")
        else:
            console.print("[red]✗[/red] Redis connection failed")
            console.print(f"  Check Redis is running at {settings.redis.host}:{settings.redis.port}")
            validation_passed = False

        # Check output directories
        console.print("\n[cyan]Checking output directories...[/cyan]")
        dirs_ok = _check_output_directories(settings)
        if dirs_ok:
            console.print("[green]✓[/green] Output directories exist and are writable")
        else:
            console.print("[red]✗[/red] Output directory check failed")
            validation_passed = False

        # Final result
        console.print()
        if validation_passed:
            console.print("[bold green]✓ Configuration is valid[/bold green]")
        else:
            console.print("[bold red]✗ Configuration validation failed[/bold red]")
            console.print("\nPlease fix the issues above and try again.")
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        handle_error(e, verbose)
        raise typer.Exit(1)


@config_app.command("set")
def set_config(
    key: str = typer.Argument(..., help="Configuration key to set"),
    value: str = typer.Argument(..., help="Value to set"),
    env_file: Optional[Path] = typer.Option(
        None,
        "--env-file",
        help="Path to .env file (default: .env in current directory)",
    ),
) -> None:
    """
    Set a configuration value in .env file.

    This command updates or adds a configuration value to your .env file.

    Examples:

        # Set API key
        vision config set ANTHROPIC_API_KEY sk-ant-...

        # Set Redis host
        vision config set REDIS_HOST localhost

        # Use custom .env file
        vision config set REDIS_PORT 6380 --env-file /path/to/.env
    """
    try:
        # Determine .env file path
        env_path = env_file or Path(".env")

        # Read existing content
        env_content = {}
        if env_path.exists():
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "=" in line:
                            k, v = line.split("=", 1)
                            env_content[k.strip()] = v.strip()

        # Update value
        env_content[key] = value

        # Write back
        with open(env_path, "w") as f:
            for k, v in env_content.items():
                f.write(f"{k}={v}\n")

        console.print(f"[green]✓[/green] Set {key} in {env_path}")
        console.print("\n[yellow]Note:[/yellow] You may need to restart the application for changes to take effect")

        # Reset settings cache
        reset_settings()

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


async def _test_redis_connection(settings: "Settings", verbose: bool) -> bool:  # type: ignore
    """
    Test Redis connection.

    Args:
        settings: Application settings
        verbose: Whether to show verbose output

    Returns:
        True if connection successful
    """
    try:
        from src.state.manager import StateManager

        async with StateManager() as manager:
            redis = await manager._get_redis()
            await redis.ping()
            return True
    except Exception as e:
        if verbose:
            console.print(f"  Error: {str(e)}")
        return False


def _check_output_directories(settings: "Settings") -> bool:  # type: ignore
    """
    Check if output directories exist and are writable.

    Args:
        settings: Application settings

    Returns:
        True if all checks pass
    """
    try:
        settings.output.ensure_directories()

        # Test write permission
        for directory in [settings.output.output_dir, settings.output.asset_dir, settings.output.temp_dir]:
            test_file = directory / ".test"
            test_file.touch()
            test_file.unlink()

        return True
    except Exception:
        return False


# Register subcommands to main config command
config.callback = config_app.callback
config.command = config_app.command