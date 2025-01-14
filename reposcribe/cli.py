# reposcribe/cli.py
import sys
from pathlib import Path
from typing import List, Optional
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
import logging

from .config import Config, ConfigError
from .git import GitHandler
from .walker import FileSystemWalker
from .formatter import MarkdownFormatter
from .stats import StatsCollector
from .messages import MessageHandler

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

@click.command()
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
    "--force",
    is_flag=True,
    help="Force processing of non-git directory",
)
def main(
    repo_url: Optional[str],
    root_dir: Optional[str],
    target_dir: str,
    output_file: str,
    config_file: Optional[str],
    include: List[str],
    exclude: List[str],
    force: bool,
    branch: Optional[str],
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
        
        with setup_progress() as progress:
            # Initialize components
            git_handler = GitHandler(config, progress)
            walker = FileSystemWalker(config, progress)
            formatter = MarkdownFormatter(config)
            stats_collector = StatsCollector()

            # Main workflow
            process_repository(
                config,
                git_handler,
                walker,
                formatter,
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

def load_configuration(config_file: Optional[str], cli_args: dict) -> Config:
    """Load and merge configuration from file and CLI arguments."""
    try:
        target_dir = Path(cli_args.get('target_dir', '.'))
        default_config_path = target_dir / '.reposcribe.yml'
        
        # Create default config if none exists
        if not config_file and not default_config_path.exists():
            Config.create_default_config(default_config_path)
            console.print(f"[green]Created default configuration file: {default_config_path}[/green]")
            config_file = str(default_config_path)

        # Load config
        config = Config.from_yaml(config_file) if config_file else Config()
        
        # Apply smart defaults if no patterns configured
        config.apply_smart_defaults()
        
        # Load .gitignore patterns
        config._load_gitignore_patterns(target_dir)
        
        # Merge CLI arguments
        filtered_args = {
            k: v for k, v in cli_args.items()
            if k in ['repo_url', 'target_dir', 'output_file', 'include', 'exclude', 'branch']
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
    formatter: MarkdownFormatter,
    stats_collector: StatsCollector,
    progress: Progress,
    force: bool,
    message_handler: MessageHandler = None,
) -> None:
    """Main processing workflow."""
    
    # Setup progress tracking
    clone_task = progress.add_task("Cloning repository...", total=1, visible=bool(config.repo_url))
    walk_task = progress.add_task("Analyzing files...", total=None)
    stats_task = progress.add_task("Collecting statistics...", total=None)
    format_task = progress.add_task("Generating documentation...", total=None)
    
    try:
        # Handle repository
        repo_path = git_handler.prepare_repository(force)
        progress.update(clone_task, completed=1)
        
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
                stats_collector.process_file(file, content)
                processed_files.append((file, content))
            progress.update(walk_task, advance=1)
            
        progress.update(stats_task, total=1, completed=0)
        stats = stats_collector.get_stats(repo_info.get('branch', 'unknown'))
        progress.update(stats_task, completed=1)
            
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

if __name__ == "__main__":
    main()