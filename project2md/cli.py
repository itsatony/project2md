# project2md/cli.py
import sys
from pathlib import Path
from typing import List, Optional
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
import logging

from .config import Config, ConfigError, OutputFormat
from .git import GitHandler
from .walker import FileSystemWalker
from .formatters.factory import get_formatter  # Single formatter import
from .formatters.base import BaseFormatter
from .stats import StatsCollector
from .messages import MessageHandler
from .explicit_config_generator import generate_explicit_config

VERSION = "1.3.1"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

def setup_progress() -> Progress:
    """Create a Rich progress bar instance."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    )

@click.group(invoke_without_command=True, help=f"Project2MD v{VERSION} - Transform repositories into comprehensive Markdown documentation.")
@click.pass_context
def cli(ctx):
    if not ctx.invoked_subcommand:
        click.echo(ctx.command.get_help(ctx))
        ctx.exit()

@cli.command()
@click.option(
    "--root-dir",
    type=click.Path(file_okay=False, dir_okay=True),
    help="Root directory for initialization (defaults to current directory)",
    default="."
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing config file",
)
def init(root_dir: str, force: bool):
    """Initialize project2md by creating a default configuration file."""
    try:
        target_path = Path(root_dir) / '.project2md.yml'
        if target_path.exists() and not force:
            console.print(f"[yellow]Configuration file already exists at {target_path}[/yellow]")
            console.print("[yellow]Use --force to overwrite[/yellow]")
            return

        Config.create_default_config(target_path)
        console.print(f"[green]Created default configuration at {target_path}[/green]")

    except Exception as e:
        console.print(f"[red]Error creating configuration: {e}[/red]")
        sys.exit(1)

@cli.command()
@click.option(
    "--repo",
    "repo_url",
    help="Git repository URL to clone and process",
)
@click.option(
    "--root-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Root directory to process (defaults to current directory if no repo URL given)",
)
@click.option(
    "--branch",
    help="Specific branch to checkout (defaults to 'main')",
)
@click.option(
    "--target",
    "target_dir",
    type=click.Path(),
    help="Target directory for cloning repository",
    default=".",
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(),
    help="Output file path",
    default="project_summary.md",
)
@click.option(
    "--config",
    "config_file",
    type=click.Path(exists=True),
    help="Configuration file path",
)
@click.option(
    "--include",
    multiple=True,
    help="Patterns to include (can be specified multiple times)",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Patterns to exclude (can be specified multiple times)",
)
@click.option(
    "--include-extra",
    multiple=True,
    help="Additional patterns to include (adds to defaults)",
)
@click.option(
    "--exclude-extra",
    multiple=True,
    help="Additional patterns to exclude (adds to defaults)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force processing of non-git directory",
)
@click.option(
    "--format",
    type=click.Choice(['markdown', 'json', 'yaml'], case_sensitive=False),
    default='markdown',
    help="Output format (default: markdown)",
)
@click.option(
    "--signatures",
    is_flag=True,
    help="Extract only function signatures from code files and headers from markdown files",
)
def process(
    repo_url: Optional[str],
    root_dir: Optional[str],
    target_dir: str,
    output_file: str,
    config_file: Optional[str],
    include: List[str],
    exclude: List[str],
    include_extra: List[str],
    exclude_extra: List[str],
    force: bool,
    branch: Optional[str],
    format: str,
    signatures: bool,
) -> None:
    """
    Transform Git repositories or local directories into comprehensive Markdown documentation.
    
    If neither repository URL nor root directory is provided, processes the current directory.
    """
    console = Console()
    message_handler = MessageHandler(console)
    
    try:
        # Determine working directory
        working_dir = Path(root_dir) if root_dir else (
            Path(target_dir) if repo_url else Path.cwd()
        )

        # Load configuration
        message_handler.info("Loading configuration...")
        config = load_configuration(config_file, {
            **locals(),
            'target_dir': str(working_dir)
        })
        
        # Update target directory in config
        config.target_dir = working_dir
        
        # Set signatures mode in config
        config.signatures_mode = signatures

        with setup_progress() as progress:
            # Initialize components
            git_handler = GitHandler(config, progress)
            walker = FileSystemWalker(config, progress)
            stats_collector = StatsCollector()

            # Get appropriate formatter using factory
            formatter = get_formatter(config)

            # Main workflow
            process_repository(
                config,
                git_handler,
                walker,
                formatter,  # Pass the formatter
                stats_collector,
                progress,
                force,
                message_handler
            )

            # Print completion message with statistics
            message_handler.print_completion_message(str(config.output_file))

    except ConfigError as e:
        message_handler.error("Configuration error", e)
        sys.exit(1)
    except Exception as e:
        message_handler.error("Unexpected error occurred", e)
        logger.exception("Unexpected error occurred")
        sys.exit(1)

@cli.command()
@click.option(
    "--directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=".",
    help="Directory to analyze."
)
def explicit(directory):
    """
    Generate or overwrite explicit.config.project2md.yml based on current directory tree.
    Uses the same config logic (includes/excludes) as 'process'.
    """
    try:
        from .config import Config
        # Load config from project2md.yml or defaults
        config = load_configuration(None, {
            'repo_url': None,
            'target_dir': directory,
        })
        output_path = Path(directory) / "explicit.config.project2md.yml"

        # Call the improved function using the loaded config
        generate_explicit_config(Path(directory), config, output_path)
        console.print(f"[green]Explicit config generated at {output_path}[/green]")
    except Exception as e:
        console.print(f"[red]Error generating explicit config: {e}[/red]")
        sys.exit(1)

@cli.command()
def version():
    """Show the current project2md version."""
    click.echo(f"project2md version {VERSION}")

def load_configuration(config_file: Optional[str], cli_args: dict) -> Config:
    """Load and merge configuration from file and CLI arguments."""
    try:
        config = None
        
        if config_file:
            # User explicitly specified a config file
            config = Config.from_yaml(config_file)
            logger.info(f"Using configuration from {config_file}")
        else:
            # Look for config in current working directory
            cwd_config = Path.cwd() / '.project2md.yml'
            if cwd_config.exists():
                config = Config.from_yaml(cwd_config)
                logger.info(f"Using configuration from {cwd_config}")
            else:
                # Load from default config (handled in Config.from_yaml)
                config = Config.from_yaml("")

        # Apply smart defaults if no patterns configured
        config.apply_smart_defaults()
        
        # Load .gitignore patterns only for local directories
        if not cli_args.get('repo_url'):
            config._load_gitignore_patterns(Path.cwd())
        
        # Merge CLI arguments
        filtered_args = {
            k: v for k, v in cli_args.items()
            if k in ['repo_url', 'target_dir', 'output_file', 'include', 'exclude', 'branch', 'format', 'signatures']
            and v is not None
        }
        config.merge_cli_args(filtered_args)
        
        # Validate the final configuration
        config.validate()
        
        return config
        
    except Exception as e:
        raise ConfigError(f"Failed to load configuration: {e}")

def process_repository(
    config: Config,
    git_handler: GitHandler,
    walker: FileSystemWalker,
    formatter: BaseFormatter,
    stats_collector: StatsCollector,
    progress: Progress,
    force: bool,
    message_handler: MessageHandler
) -> None:
    """
    Process a repository and generate documentation.
    
    Args:
        root_dir: Path to the repository root directory
        config: Configuration object
        formatter: Formatter instance to use
        output_path: Path where to save the output
        repo_url: Optional repository URL to clone
        branch: Optional branch to process
    """
    
    # Setup progress tracking
    clone_task = progress.add_task("Cloning repository...", total=1, visible=bool(config.repo_url))
    walk_task = progress.add_task("Analyzing files...", total=None)
    stats_task = progress.add_task("Collecting statistics...", total=None)
    format_task = progress.add_task("Generating documentation...", total=None)
    
    try:
        # Handle repository
        repo_path = git_handler.prepare_repository(force)
        progress.update(clone_task, completed=1)
        
        # Ensure output directory exists
        config.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Get repository information
        repo_info = git_handler.get_repo_info()
        
        # Collect files
        files = walker.collect_files(repo_path)
        progress.update(walk_task, total=len(files), completed=0)
        
        # Process files and collect statistics
        processed_files = []
        for file in files:
            content = walker.read_file(file)
            if content is not None or not config.general.stats_in_output:
                # Apply signature processing if enabled
                if config.signatures_mode and content is not None:
                    from .signature_processor import SignatureProcessor
                    processor = SignatureProcessor()
                    content = processor.process_file(file, content)
                
                stats_collector.process_file(file, content)
                processed_files.append((file, content))
            progress.update(walk_task, advance=1)
            
        progress.update(stats_task, total=1, completed=0)
        stats = stats_collector.get_stats(repo_info.get('branch', 'unknown'))
        progress.update(stats_task, completed=1)
            
        # Get appropriate formatter using factory
        formatter = get_formatter(config)  # This will now properly handle the format
        
        # Generate output
        progress.update(format_task, total=1, completed=0)
        formatter.generate_output(
            repo_path,
            processed_files,
            stats,
            config.output_file
        )
        progress.update(format_task, completed=1)
        
        # Print summary
        console.print("\n[bold green]Documentation generated successfully![/bold green]")
        console.print(f"[green]Output file: {config.output_file}[/green]")
        
        # Print quick stats summary
        if config.general.stats_in_output:
            console.print("\n[bold blue]Quick Statistics:[/bold blue]")
            console.print(f"  • Total Files: {stats['total_files']}")
            console.print(f"  • Text Files: {stats['text_files']} ({stats['text_files_percentage']}%)")
            console.print(f"  • Repository Size: {stats['repo_size']}")
            console.print(f"  • Current Branch: {stats['branch']}")
            
            if stats['file_types']:
                console.print("\n[blue]Top File Types:[/blue]")
                for ext, count in list(stats['file_types'].items())[:3]:
                    console.print(f"  • {ext}: {count} files")
                    
        
    except Exception as e:
        raise click.ClickException(str(e))

def main():
    try:
        cli(standalone_mode=False)
    except click.UsageError as e:
        console.print(f"[red]{e}[/red]")
        with click.Context(cli) as ctx:
            console.print(ctx.command.get_help(ctx))
        sys.exit(1)
    except click.ClickException as e:
        console.print(f"[red]{e}[/red]")
        with click.Context(cli) as ctx:
            console.print(ctx.command.get_help(ctx))
        sys.exit(1)

if __name__ == "__main__":
    main()