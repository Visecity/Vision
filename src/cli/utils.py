"""
Utility functions for the Vision CLI.

This module provides helper functions for formatting output, handling progress,
managing sessions, and error handling.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from uuid import UUID

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

console = Console()
logger = logging.getLogger(__name__)


class ProgressHandler:
    """Handles progress updates with Rich progress bars."""

    def __init__(self, description: str = "Processing") -> None:
        """Initialize progress handler."""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        )
        self.task_id: int | None = None
        self.description = description

    def __enter__(self) -> "ProgressHandler":
        """Enter progress context."""
        self.progress.start()
        self.task_id = self.progress.add_task(self.description, total=100)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit progress context."""
        self.progress.stop()

    def update(self, step: str, percentage: float, data: dict[str, Any]) -> None:
        """
        Update progress bar.

        Args:
            step: Current step name
            percentage: Progress percentage (0-100)
            data: Additional data from workflow
        """
        if self.task_id is not None:
            description = f"{self.description} - {step}"
            self.progress.update(self.task_id, completed=percentage, description=description)
            
            # Log workflow_id if present
            if "workflow_id" in data:
                logger.debug(f"Workflow ID: {data['workflow_id']}")


def format_table(
    data: list[dict[str, Any]],
    columns: list[tuple[str, str]],
    title: str | None = None,
) -> Table:
    """
    Format data as a Rich table.

    Args:
        data: List of dictionaries with data
        columns: List of (key, header) tuples
        title: Optional table title

    Returns:
        Rich Table object
    """
    table = Table(title=title, show_header=True, header_style="bold cyan")

    # Add columns
    for _, header in columns:
        table.add_column(header, overflow="fold")

    # Add rows
    for row in data:
        values = []
        for key, _ in columns:
            value = row.get(key, "")
            if isinstance(value, datetime):
                value = value.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, UUID):
                value = str(value)
            elif isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            values.append(str(value))
        table.add_row(*values)

    return table


def format_json(data: dict[str, Any], title: str | None = None) -> str:
    """
    Format data as pretty JSON.

    Args:
        data: Dictionary to format
        title: Optional title

    Returns:
        Formatted JSON string
    """
    json_str = json.dumps(data, indent=2, default=str)
    if title:
        return f"\n{title}\n{'=' * len(title)}\n{json_str}"
    return json_str


def format_workflow_status(status: dict[str, Any]) -> Panel:
    """
    Format workflow status as a Rich panel.

    Args:
        status: Workflow status dictionary

    Returns:
        Rich Panel with formatted status
    """
    # Determine status color
    status_value = status.get("status", "unknown")
    if status_value == "completed":
        status_color = "green"
    elif status_value == "in_progress":
        status_color = "yellow"
    elif status_value == "failed":
        status_color = "red"
    else:
        status_color = "blue"

    # Build status text
    lines = []
    lines.append(f"[bold]Workflow ID:[/bold] {status.get('workflow_id', 'N/A')}")
    lines.append(f"[bold]Status:[/bold] [{status_color}]{status_value}[/{status_color}]")
    lines.append(f"[bold]Current Step:[/bold] {status.get('current_step', 'N/A')}")
    lines.append(f"[bold]Progress:[/bold] {status.get('progress_percentage', 0):.1f}%")
    
    completed_steps = status.get("completed_steps", [])
    if completed_steps:
        lines.append(f"[bold]Completed Steps:[/bold] {', '.join(completed_steps)}")
    
    if status.get("error"):
        lines.append(f"[bold red]Error:[/bold red] {status['error']}")
    
    lines.append(f"[bold]Created:[/bold] {status.get('created_at', 'N/A')}")
    lines.append(f"[bold]Updated:[/bold] {status.get('updated_at', 'N/A')}")

    return Panel(
        "\n".join(lines),
        title="Workflow Status",
        border_style=status_color,
    )


def format_generation_result(result: dict[str, Any]) -> Panel:
    """
    Format generation result as a Rich panel.

    Args:
        result: Generation result dictionary

    Returns:
        Rich Panel with formatted result
    """
    lines = []
    lines.append(f"[bold]Request ID:[/bold] {result.get('request_id', 'N/A')}")
    lines.append(f"[bold]Status:[/bold] {result.get('status', 'N/A')}")
    
    metadata = result.get("metadata")
    if metadata:
        lines.append(f"[bold]Asset Type:[/bold] {metadata.get('asset_type', 'N/A')}")
        lines.append(f"[bold]Style:[/bold] {metadata.get('style', 'N/A')}")
        
        dimensions = metadata.get("dimensions", {})
        lines.append(f"[bold]Dimensions:[/bold] {dimensions.get('width', 0)}x{dimensions.get('height', 0)}")
        
        lines.append(f"[bold]Frame Count:[/bold] {metadata.get('frame_count', 1)}")
        lines.append(f"[bold]Generation Time:[/bold] {metadata.get('generation_time_seconds', 0):.2f}s")
    
    if result.get("error_message"):
        lines.append(f"[bold red]Error:[/bold red] {result['error_message']}")
    
    warnings = result.get("warnings", [])
    if warnings:
        lines.append(f"[bold yellow]Warnings:[/bold yellow]")
        for warning in warnings:
            lines.append(f"  • {warning}")

    return Panel(
        "\n".join(lines),
        title="Generation Result",
        border_style="green" if result.get("status") == "completed" else "red",
    )


def save_manifest(
    manifest_json: dict[str, Any],
    output_dir: Path,
    filename: str = "manifest.json",
) -> Path:
    """
    Save manifest JSON to file.

    Args:
        manifest_json: Manifest dictionary
        output_dir: Output directory
        filename: Filename for manifest

    Returns:
        Path to saved manifest file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / filename
    
    with open(manifest_path, "w") as f:
        json.dump(manifest_json, f, indent=2, default=str)
    
    logger.info(f"Saved manifest to {manifest_path}")
    return manifest_path


def save_metadata(
    metadata: dict[str, Any],
    output_dir: Path,
    filename: str = "metadata.json",
) -> Path:
    """
    Save metadata to file.

    Args:
        metadata: Metadata dictionary
        output_dir: Output directory
        filename: Filename for metadata

    Returns:
        Path to saved metadata file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = output_dir / filename
    
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    
    logger.info(f"Saved metadata to {metadata_path}")
    return metadata_path


def get_session_id(provided_id: str | None = None) -> str:
    """
    Get or generate session ID.

    Args:
        provided_id: Optional session ID provided by user

    Returns:
        Session ID to use
    """
    if provided_id:
        return provided_id
    
    # Try to load from environment or generate default
    import os
    return os.environ.get("VISION_SESSION_ID", "default")


def handle_error(error: Exception, verbose: bool = False) -> None:
    """
    Handle and display errors with user-friendly messages.

    Args:
        error: Exception that occurred
        verbose: Whether to show full traceback
    """
    error_messages = {
        "ConnectionError": "Could not connect to Redis. Please ensure Redis is running.",
        "AuthenticationError": "Invalid API key. Please check your ANTHROPIC_API_KEY.",
        "ValidationError": "Invalid input. Please check your command parameters.",
        "FileNotFoundError": "File not found. Please check the file path.",
    }
    
    error_type = type(error).__name__
    message = error_messages.get(error_type, str(error))
    
    console.print(f"[bold red]Error:[/bold red] {message}")
    
    if verbose:
        console.print_exception()


def confirm_action(message: str, default: bool = False) -> bool:
    """
    Ask user to confirm an action.

    Args:
        message: Confirmation message
        default: Default value if user just presses Enter

    Returns:
        True if user confirms, False otherwise
    """
    default_str = "Y/n" if default else "y/N"
    response = console.input(f"{message} [{default_str}]: ").strip().lower()
    
    if not response:
        return default
    
    return response in ("y", "yes")


def parse_dimensions(dim_str: str) -> tuple[int, int]:
    """
    Parse dimension string like "16x16" into width and height.

    Args:
        dim_str: Dimension string (e.g., "16x16", "32x32")

    Returns:
        Tuple of (width, height)

    Raises:
        ValueError: If dimension string is invalid
    """
    try:
        parts = dim_str.lower().split("x")
        if len(parts) != 2:
            raise ValueError("Invalid format")
        
        width = int(parts[0].strip())
        height = int(parts[1].strip())
        
        if width <= 0 or height <= 0:
            raise ValueError("Dimensions must be positive")
        
        if width > 512 or height > 512:
            raise ValueError("Dimensions cannot exceed 512x512")
        
        return width, height
    
    except (ValueError, AttributeError) as e:
        raise ValueError(
            f"Invalid dimension format: {dim_str}. Use format like '16x16', '32x32', etc."
        ) from e


def get_output_directory(base_dir: Path | str, request_id: str) -> Path:
    """
    Get output directory for a specific request.

    Args:
        base_dir: Base output directory
        request_id: Request identifier

    Returns:
        Path to output directory for this request
    """
    base_path = Path(base_dir) if isinstance(base_dir, str) else base_dir
    output_dir = base_path / request_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir