"""
CLI interface for CStarX v2.0
"""

import asyncio
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from loguru import logger

from ..core.translator import Translator
from ..models.config import Config
from ..utils.progress_viewer import ProgressViewer

app = typer.Typer(name="cstarx", help="CStarX v2.0 - Advanced C/C++ to Rust Translation Tool")
console = Console()


@app.command()
def translate(
    project_path: str = typer.Argument(..., help="Path to the C/C++ project"),
    output_path: Optional[str] = typer.Option(None, "--output", "-o", help="Output directory for Rust code"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Configuration file path"),
    dev_mode: bool = typer.Option(False, "--dev", help="Enable development mode"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")
):
    """Translate a C/C++ project to Rust"""
    
    # Load configuration first to get log settings
    if config_file:
        config = Config.load(Path(config_file))
    else:
        config = Config.from_env()
    
    if dev_mode:
        config.dev_mode = True
    
    # Configure logging with file output for model interactions
    logger.remove()
    
    # Always add file logger for model interactions (if log_file is configured)
    log_file_path = config.log_file
    if not log_file_path:
        # Default log file in output directory
        log_file_path = config.output.output_dir / "logs" / "cstarx.log"
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Add file logger (includes all model interactions)
    logger.add(
        str(log_file_path),
        level=config.log_level if not verbose else "DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="50 MB",
        retention="30 days",
        compression="zip"
    )
    
    # Add console logger
    console_level = "DEBUG" if verbose else config.log_level
    import sys
    if verbose:
        # Verbose mode: use rich formatting
        logger.add(
            sys.stderr,
            level=console_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - {message}",
            colorize=True
        )
    else:
        # Normal mode: simple console output
        logger.add(
            sys.stderr,
            level=console_level,
            format="{time:HH:mm:ss} | {level: <8} | {message}",
            colorize=False
        )
    
    logger.info(f"Logging configured: file={log_file_path}, level={console_level}")
    logger.info(f"All logs including model interactions will be saved to: {log_file_path}")
    
    # Run translation
    asyncio.run(_run_translation(project_path, output_path, config))


@app.command()
def status(
    project_path: Optional[str] = typer.Option(None, "--project", "-p", help="Project path to check status"),
    project_id: Optional[str] = typer.Option(None, "--id", help="Project ID to check status"),
    project_name: Optional[str] = typer.Option(None, "--name", "-n", help="Project name to check status"),
    all_projects: bool = typer.Option(False, "--all", "-a", help="Show all projects summary"),
    state_dir: Optional[str] = typer.Option(None, "--state-dir", help="State directory path")
):
    """Check translation status"""
    if all_projects or project_id or project_name:
        # Use progress viewer
        from pathlib import Path
        viewer = ProgressViewer(state_dir=Path(state_dir) if state_dir else None)
        if project_id:
            viewer.display_project_details(project_id=project_id)
        elif project_name:
            viewer.display_project_details(project_name=project_name)
        else:
            viewer.display_summary()
    else:
        # Use old method (backward compatibility)
        asyncio.run(_check_status(project_path))


@app.command()
def resume(
    project_path: str = typer.Argument(..., help="Path to the project to resume")
):
    """Resume a paused translation"""
    asyncio.run(_resume_translation(project_path))


@app.command()
def pause(
    project_path: str = typer.Argument(..., help="Path to the project to pause")
):
    """Pause current translation"""
    asyncio.run(_pause_translation(project_path))


@app.command()
def clean():
    """Clean up old state files"""
    asyncio.run(_cleanup())


async def _run_translation(project_path: str, output_path: Optional[str], config: Config):
    """Run the translation process"""
    translator = Translator(config)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        task = progress.add_task("Translating project...", total=None)
        
        try:
            project = await translator.translate_project(project_path, output_path)
            
            progress.update(task, description="Translation complete!")
            
            # Display results
            _display_results(project)
            
        except Exception as e:
            progress.update(task, description=f"Translation failed: {e}")
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
        
        finally:
            await translator.cleanup()


async def _check_status(project_path: Optional[str]):
    """Check translation status"""
    config = Config.from_env()
    translator = Translator(config)
    
    status = await translator.get_translation_status()
    
    if status['status'] == 'no_active_project':
        console.print("[yellow]No active project found[/yellow]")
        return
    
    # Display status table
    table = Table(title="Translation Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="magenta")
    
    project_info = status['project']
    session_info = status['session']
    
    table.add_row("Project Name", project_info['name'])
    table.add_row("Total Files", str(project_info['total_files']))
    table.add_row("Translated Files", str(project_info['translated_files']))
    table.add_row("Failed Files", str(project_info['failed_files']))
    table.add_row("Progress", f"{session_info['progress']:.1f}%")
    table.add_row("Completed", str(session_info['completed_count']))
    table.add_row("Failed", str(session_info['failed_count']))
    table.add_row("Complete", "Yes" if session_info['is_complete'] else "No")
    
    console.print(table)


async def _resume_translation(project_path: str):
    """Resume translation"""
    config = Config.from_env()
    translator = Translator(config)
    
    try:
        await translator.resume_translation()
        console.print("[green]Translation resumed successfully[/green]")
    except Exception as e:
        console.print(f"[red]Failed to resume translation: {e}[/red]")
        raise typer.Exit(1)


async def _pause_translation(project_path: str):
    """Pause translation"""
    config = Config.from_env()
    translator = Translator(config)
    
    try:
        await translator.pause_translation()
        console.print("[green]Translation paused successfully[/green]")
    except Exception as e:
        console.print(f"[red]Failed to pause translation: {e}[/red]")
        raise typer.Exit(1)


async def _cleanup():
    """Clean up old state files"""
    config = Config.from_env()
    translator = Translator(config)
    
    await translator.cleanup()
    console.print("[green]Cleanup complete[/green]")


def _display_results(project):
    """Display translation results"""
    table = Table(title="Translation Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Project Name", project.name)
    table.add_row("Total Files", str(project.total_files))
    table.add_row("Translated Files", str(project.translated_files))
    table.add_row("Failed Files", str(project.failed_files))
    table.add_row("Success Rate", f"{(project.translated_files / project.total_files * 100):.1f}%" if project.total_files > 0 else "0%")
    
    console.print(table)


if __name__ == "__main__":
    app()
