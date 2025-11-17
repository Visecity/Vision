"""
Status command implementation for Vision CLI.

This module provides the status command which checks the progress
of running or completed workflows.
"""

import asyncio
import logging
from typing import Optional
from uuid import UUID

import typer
from rich.console import Console

from src.cli.utils import format_workflow_status, handle_error
from src.state.executor import WorkflowExecutor

console = Console()
logger = logging.getLogger(__name__)


def status(
    workflow_id: str = typer.Argument(
        ...,
        help="Workflow ID to check status for",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output status as JSON",
    ),
    watch: bool = typer.Option(
        False,
        "--watch",
        "-w",
        help="Watch status updates (refresh every 2 seconds)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """
    Check the status of a workflow execution.

    This command retrieves the current status of a workflow, showing
    progress, completed steps, and any errors.

    Examples:

        # Check workflow status
        vision status 123e4567-e89b-12d3-a456-426614174000

        # Get JSON output
        vision status <workflow-id> --json

        # Watch status updates
        vision status <workflow-id> --watch
    """
    try:
        # Parse workflow ID
        try:
            wf_id = UUID(workflow_id)
        except ValueError:
            console.print(f"[bold red]Error:[/bold red] Invalid workflow ID: {workflow_id}")
            console.print("Workflow ID must be a valid UUID")
            raise typer.Exit(1)

        # Get status
        if watch:
            asyncio.run(_watch_status(wf_id, json_output, verbose))
        else:
            status_result = asyncio.run(_get_status(wf_id, verbose))
            _display_status(status_result, json_output)

    except KeyboardInterrupt:
        console.print("\n[yellow]Status check cancelled by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        handle_error(e, verbose)
        raise typer.Exit(1)


async def _get_status(workflow_id: UUID, verbose: bool) -> dict:
    """
    Get workflow status asynchronously.

    Args:
        workflow_id: Workflow identifier
        verbose: Whether to show verbose output

    Returns:
        Status dictionary
    """
    async with WorkflowExecutor() as executor:
        status = await executor.get_status(workflow_id)
        return status


async def _watch_status(workflow_id: UUID, json_output: bool, verbose: bool) -> None:
    """
    Watch workflow status with periodic updates.

    Args:
        workflow_id: Workflow identifier
        json_output: Whether to output as JSON
        verbose: Whether to show verbose output
    """
    import time

    console.print(f"[cyan]Watching workflow {workflow_id}[/cyan]")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")

    async with WorkflowExecutor() as executor:
        previous_status = None

        while True:
            try:
                status = await executor.get_status(workflow_id)

                # Only update display if status changed
                if status != previous_status:
                    if not json_output:
                        console.clear()
                    _display_status(status, json_output)
                    previous_status = status

                # Check if workflow is complete
                status_value = status.get("status", "")
                if status_value in ("completed", "failed", "cancelled"):
                    console.print(f"\n[bold]Workflow {status_value}[/bold]")
                    break

                # Wait before next check
                await asyncio.sleep(2)

            except KeyboardInterrupt:
                break


def _display_status(status: dict, json_output: bool) -> None:
    """
    Display workflow status.

    Args:
        status: Status dictionary
        json_output: Whether to output as JSON
    """
    if json_output:
        import json
        console.print(json.dumps(status, indent=2, default=str))
    else:
        if status.get("status") == "not_found":
            console.print("[bold red]Workflow not found[/bold red]")
            console.print(f"Error: {status.get('error', 'Unknown error')}")
        else:
            panel = format_workflow_status(status)
            console.print(panel)