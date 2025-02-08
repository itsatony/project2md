# project2md/messages.py
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

class MessageHandler:
    """Handles user messages and error reporting."""
    
    def __init__(self, console: Console):
        self.console = console
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def success(self, message: str) -> None:
        """Display a success message."""
        self.console.print(f"[bold green]✓[/bold green] {message}")

    def error(self, message: str, exception: Optional[Exception] = None) -> None:
        """Log and display an error message."""
        self.errors.append(message)
        if exception:
            logger.error(f"{message}: {str(exception)}")
            self.console.print(f"[bold red]✗[/bold red] {message}: {str(exception)}")
        else:
            logger.error(message)
            self.console.print(f"[bold red]✗[/bold red] {message}")

    def warning(self, message: str) -> None:
        """Log and display a warning message."""
        self.warnings.append(message)
        logger.warning(message)
        self.console.print(f"[bold yellow]![/bold yellow] {message}")

    def info(self, message: str) -> None:
        """Display an information message."""
        self.console.print(f"[bold blue]ℹ[/bold blue] {message}")

    def print_stats_summary(self, stats: Dict) -> None:
        """Display a summary of repository statistics."""
        summary = Text()
        summary.append("\nRepository Statistics\n", style="bold blue")
        summary.append("─" * 20 + "\n", style="blue")
        
        # Add statistics
        summary.append(f"Total Files: {stats['total_files']}\n", style="dim")
        summary.append(
            f"Text Files: {stats['text_files']} "
            f"({stats.get('text_files_percentage', 0)}%)\n",
            style="dim"
        )
        summary.append(f"Repository Size: {stats['repo_size']}\n", style="dim")
        summary.append(f"Current Branch: {stats['branch']}\n", style="dim")
        
        # Add top file types
        if stats.get('file_types'):
            summary.append("\nTop File Types\n", style="blue")
            for ext, count in list(stats['file_types'].items())[:3]:
                summary.append(f"• {ext}: {count} files\n", style="dim")
        
        # Add languages if available
        if stats.get('languages'):
            summary.append("\nTop Languages\n", style="blue")
            for lang, count in list(stats['languages'].items())[:3]:
                summary.append(f"• {lang}: {count} files\n", style="dim")
        
        self.console.print(Panel(summary, expand=False))

    def print_completion_message(self, output_path: str) -> None:
        """Display a completion message with summary of warnings/errors."""
        # Print success message
        self.console.print("\n")
        self.success("Documentation generated successfully!")
        self.console.print(f"Output file: [blue]{output_path}[/blue]")
        
        # Print warnings if any
        if self.warnings:
            self.console.print("\n[yellow]Warnings encountered:[/yellow]")
            for warning in self.warnings:
                self.console.print(f"  • {warning}")
        
        # Print errors if any
        if self.errors:
            self.console.print("\n[red]Errors encountered:[/red]")
            for error in self.errors:
                self.console.print(f"  • {error}")

    def clear(self) -> None:
        """Clear all stored warnings and errors."""
        self.warnings.clear()
        self.errors.clear()