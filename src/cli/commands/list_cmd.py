"""
List command implementation for Vision CLI.

This module provides the list command which displays all workflows,
optionally filtered by session.
"""

import asyncio
import logging
from typing import Optional

import typer
from rich.console import Console

from src.cli.utils import format_table, get_session_id, handle_error
from src.state.manager import StateManager

console = Console()
logger = logging.getLogger(__name__)


def list_workflows(
    session_id: Optional[str] = typer.Option(
        None,
        "--session-id",
        "-s",
        help="Filter by session ID",
    ),
    limit: int = typer.Option(
        100,
        "--limit",
        "-l",
        help="Maximum number of workflows to display",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output workflows as JSON",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """
    List all workflows, optionally filtered by session.

    This command retrieves and displays a list of workflows from the
    state manager, showing their status, description, and timestamps.

    Examples:

        # List all workflows
        vision list

        # List workflows for a specific session
        vision list --session-id user-123

        # Limit results
        vision list --limit 20

        # JSON output
        vision list --json
    """
    try:
        # Get workflows
        workflows = asyncio.run(_list_workflows(session_id, limit, verbose))

        if not workflows:
            console.print("[yellow]No workflows found[/yellow]")
            return

        # Display workflows
        if json_output:
            import json
            workflows_dict = [w.model_dump() for w in workflows]
            console.print(json.dumps(workflows_dict, indent=2, default=str))
        else:
            # Format as table
            workflow_data = []
            for wf in workflows:
                workflow_data.append({
                    "workflow_id": str(wf.workflow_id)[:8] + "...",  # Truncate for display
                    "status": wf.status,
                    "description": (wf.description[:50] + "..." 
                                   if len(wf.description) > 50 
                                   else wf.description),
                    "current_step": wf.current_step or "N/A",
                    "created_at": wf.created_at,
                })

            columns = [
                ("workflow_id", "Workflow ID"),
                ("status", "Status"),
                ("description", "Description"),
                ("current_step", "Current Step"),
                ("created_at", "Created"),
            ]

            title = f"Workflows (Total: {len(workflows)})"
            if session_id:
                title += f" - Session: {session_id}"

            table = format_table(workflow_data, columns, title)
            console.print(table)

            # Show summary
            console.print(f"\n[dim]Showing {len(workflows)} workflow(s)[/dim]")

    except KeyboardInterrupt:
        console.print("\n[yellow]List operation cancelled by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        handle_error(e, verbose)
        raise typer.Exit(1)


async def _list_workflows(
    session_id: Optional[str],
    limit: int,
    verbose: bool,
) -> list:
    """
    List workflows asynchronously.

    Args:
        session_id: Optional session ID to filter by
        limit: Maximum number of workflows to return
        verbose: Whether to show verbose output

    Returns:
        List of workflow snapshots
    """
    async with StateManager() as manager:
        workflows = await manager.list_states(
            session_id=session_id,
            limit=limit,
        )
        return workflows