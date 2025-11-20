"""
Batch generation command for Vision CLI.

This module provides the generate-batch command which creates multiple
pixel art sprites from batch definition files (YAML/JSON).
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from src.utils.batch_parser import parse_batch_file, validate_batch_file, BatchParseError
from src.workflows.batch_executor import execute_batch
from src.core.config import get_settings

console = Console()
logger = logging.getLogger(__name__)


def generate_batch(
    batch_file: Path = typer.Argument(
        ...,
        help="Path to batch definition file (YAML or JSON)",
        exists=True,
    ),
    parallel: int = typer.Option(
        2,
        "--parallel",
        "-p",
        help="Number of concurrent generations (1-10)",
        min=1,
        max=10,
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Validate batch file without generating assets",
    ),
    continue_on_error: bool = typer.Option(
        True,
        "--continue-on-error",
        help="Continue batch if individual assets fail",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """
    Generate multiple assets from a batch definition file.
    
    Supports YAML (.yaml, .yml) and JSON (.json) formats.
    
    Examples:
    
        # Generate batch with default settings
        vision generate-batch items.yaml
        
        # Use parallel generation
        vision generate-batch dungeon_assets.yaml --parallel 4
        
        # Dry run to validate batch file
        vision generate-batch items.json --dry-run
        
        # Stop on first error
        vision generate-batch assets.yaml --no-continue-on-error
    """
    try:
        # Validate batch file first
        console.print(f"[bold]Parsing batch file:[/bold] {batch_file}")
        
        is_valid, errors = validate_batch_file(batch_file)
        
        if not is_valid:
            console.print("[bold red]✗ Batch file validation failed:[/bold red]\n")
            for error in errors:
                console.print(f"  • {error}")
            raise typer.Exit(1)
        
        # Parse batch definition
        try:
            batch_def = parse_batch_file(batch_file)
        except BatchParseError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(1)
        
        # Display batch info
        console.print(f"[green]✓[/green] Batch file validated\n")
        console.print(f"[bold]Batch:[/bold] {batch_def.batch_name}")
        console.print(f"[bold]Assets:[/bold] {len(batch_def.assets)}")
        console.print(f"[bold]Output:[/bold] {batch_def.output_dir}")
        if batch_def.create_atlas:
            atlas_name = batch_def.atlas_name or batch_def.batch_name
            console.print(f"[bold]Atlas:[/bold] {atlas_name}")
        console.print()
        
        # Dry run mode - just validate and exit
        if dry_run:
            console.print("[bold green]✓ Dry run successful - batch file is valid[/bold green]")
            console.print("\n[dim]Run without --dry-run to generate assets[/dim]")
            return
        
        # Override parallel count if specified
        if parallel != batch_def.parallel_count:
            batch_def.parallel_count = parallel
        
        # Execute batch generation
        console.print(f"[bold]Starting batch generation...[/bold]")
        console.print(f"Parallel workers: {batch_def.parallel_count}\n")
        
        result = asyncio.run(_execute_batch_with_progress(batch_def, verbose))
        
        # Display results
        _display_batch_results(result, batch_def)
        
        # Exit with appropriate code
        if result.failed > 0 and not continue_on_error:
            raise typer.Exit(1)
        elif result.successful == 0:
            raise typer.Exit(1)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Batch generation cancelled by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        if verbose:
            logger.error(f"Batch generation error: {e}", exc_info=True)
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


async def _execute_batch_with_progress(batch_def, verbose: bool):
    """Execute batch with progress bar."""
    total_assets = len(batch_def.assets)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            "Generating assets...",
            total=total_assets,
        )
        
        # We can't easily update progress during batch execution
        # since it's handled internally, so we'll show indeterminate progress
        progress.update(task, completed=0)
        
        # Execute batch
        result = await execute_batch(batch_def)
        
        # Update to show completion
        progress.update(task, completed=total_assets)
    
    return result


def _display_batch_results(result, batch_def) -> None:
    """Display batch generation results in a formatted table."""
    console.print()
    
    # Summary statistics
    console.print("[bold]Batch Generation Summary:[/bold]\n")
    
    summary_table = Table(show_header=False, box=None)
    summary_table.add_column("Label", style="bold")
    summary_table.add_column("Value")
    
    summary_table.add_row("Batch Name", result.batch_name)
    summary_table.add_row("Total Assets", str(result.total_requests))
    summary_table.add_row(
        "Successful",
        f"[green]{result.successful}[/green]",
    )
    
    if result.failed > 0:
        summary_table.add_row(
            "Failed",
            f"[red]{result.failed}[/red]",
        )
    
    summary_table.add_row(
        "Execution Time",
        f"{result.execution_time:.2f}s",
    )
    
    if result.atlas_path:
        summary_table.add_row("Atlas", str(result.atlas_path))
    
    console.print(summary_table)
    console.print()
    
    # Asset results
    if result.assets:
        console.print("[bold]Asset Results:[/bold]\n")
        
        asset_table = Table(show_header=True)
        asset_table.add_column("Asset", style="cyan")
        asset_table.add_column("Status", style="bold")
        asset_table.add_column("Time", justify="right")
        asset_table.add_column("Details")
        
        for asset in result.assets:
            if asset.success:
                status = "[green]✓ Success[/green]"
                details = ""
                if asset.png_path:
                    details = f"PNG: {asset.png_path.name}"
            else:
                status = "[red]✗ Failed[/red]"
                details = asset.error or "Unknown error"
            
            time_str = f"{asset.generation_time:.1f}s" if asset.generation_time else "-"
            
            asset_table.add_row(
                asset.name,
                status,
                time_str,
                details,
            )
        
        console.print(asset_table)
        console.print()
    
    # Errors
    if result.errors:
        console.print("[bold red]Batch Errors:[/bold red]\n")
        for error in result.errors:
            console.print(f"  • {error}")
        console.print()
    
    # Final message
    if result.failed == 0:
        console.print("[bold green]✓ Batch generation completed successfully![/bold green]")
    elif result.successful > 0:
        console.print(
            f"[bold yellow]⚠ Batch completed with {result.failed} failure(s)[/bold yellow]"
        )
    else:
        console.print("[bold red]✗ Batch generation failed[/bold red]")
    
    console.print(f"\nOutput directory: [cyan]{batch_def.output_dir}[/cyan]")