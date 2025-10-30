"""
Progress viewer utility for CStarX v2.0
用于查看翻译进度的工具
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, SpinnerColumn
from rich.panel import Panel
from rich import box

console = Console()


class ProgressViewer:
    """View translation progress from state files"""
    
    def __init__(self, state_dir: Optional[Path] = None):
        if state_dir is None:
            # Default to output/state
            self.state_dir = Path("output/state")
        else:
            self.state_dir = Path(state_dir)
        
        if not self.state_dir.exists():
            self.state_dir.mkdir(parents=True, exist_ok=True)
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects in state directory"""
        projects = []
        
        for project_file in self.state_dir.glob("project_*.json"):
            try:
                with open(project_file, 'r') as f:
                    data = json.load(f)
                
                # Calculate progress
                total = data.get('total_files', 0)
                translated = data.get('translated_files', 0)
                failed = data.get('failed_files', 0)
                progress = (translated + failed) / total * 100 if total > 0 else 0
                
                projects.append({
                    'id': data['id'],
                    'name': data.get('name', 'Unknown'),
                    'path': data.get('path', ''),
                    'total_files': total,
                    'translated_files': translated,
                    'failed_files': failed,
                    'progress': progress,
                    'updated_at': data.get('updated_at', ''),
                    'file': project_file
                })
            except Exception as e:
                console.print(f"[red]Error reading {project_file}: {e}[/red]")
        
        # Sort by updated_at (most recent first)
        projects.sort(key=lambda x: x['updated_at'], reverse=True)
        return projects
    
    def get_project_details(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a project"""
        project_file = self.state_dir / f"project_{project_id}.json"
        
        if not project_file.exists():
            return None
        
        with open(project_file, 'r') as f:
            data = json.load(f)
        
        # Analyze units by status
        units = data.get('units', [])
        status_counts = {}
        status_details = {
            'pending': [],
            'in_progress': [],
            'completed': [],
            'failed': []
        }
        
        for unit in units:
            status = unit.get('status', 'pending')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if status in status_details:
                status_details[status].append({
                    'name': unit.get('name', ''),
                    'path': unit.get('path', ''),
                    'complexity': unit.get('complexity_score', 0),
                    'size': unit.get('size', 0),
                    'confidence': unit.get('translation_result', {}).get('metadata', {}).get('confidence', None) if unit.get('translation_result') else None
                })
        
        return {
            'id': data['id'],
            'name': data.get('name', 'Unknown'),
            'path': data.get('path', ''),
            'target_language': data.get('target_language', 'rust'),
            'total_files': data.get('total_files', len(units)),
            'translated_files': data.get('translated_files', 0),
            'failed_files': data.get('failed_files', 0),
            'created_at': data.get('created_at', ''),
            'updated_at': data.get('updated_at', ''),
            'status_counts': status_counts,
            'status_details': status_details,
            'units': units
        }
    
    def display_summary(self):
        """Display summary of all projects"""
        projects = self.list_projects()
        
        if not projects:
            console.print("[yellow]No projects found in state directory[/yellow]")
            return
        
        table = Table(title="Translation Projects Summary", box=box.ROUNDED, show_header=True)
        table.add_column("Project Name", style="cyan", width=20)
        table.add_column("Path", style="blue", width=30)
        table.add_column("Total", justify="right", style="green", width=8)
        table.add_column("Translated", justify="right", style="green", width=10)
        table.add_column("Failed", justify="right", style="red", width=8)
        table.add_column("Progress", justify="right", style="magenta", width=10)
        table.add_column("Last Updated", style="yellow", width=20)
        
        for proj in projects:
            progress_bar = f"{proj['progress']:.1f}%"
            updated = proj['updated_at'][:19] if proj['updated_at'] else 'N/A'
            
            table.add_row(
                proj['name'],
                proj['path'],
                str(proj['total_files']),
                str(proj['translated_files']),
                str(proj['failed_files']),
                progress_bar,
                updated
            )
        
        console.print(table)
    
    def display_project_details(self, project_id: Optional[str] = None, project_name: Optional[str] = None):
        """Display detailed information about a project"""
        if project_id is None and project_name is None:
            # Show latest project
            projects = self.list_projects()
            if not projects:
                console.print("[yellow]No projects found[/yellow]")
                return
            project_id = projects[0]['id']
        elif project_name:
            # Find project by name
            projects = self.list_projects()
            for proj in projects:
                if proj['name'] == project_name:
                    project_id = proj['id']
                    break
            else:
                console.print(f"[red]Project '{project_name}' not found[/red]")
                return
        
        details = self.get_project_details(project_id)
        if not details:
            console.print(f"[red]Project '{project_id}' not found[/red]")
            return
        
        # Display project info
        info_panel = Panel(
            f"[cyan]Name:[/cyan] {details['name']}\n"
            f"[cyan]Path:[/cyan] {details['path']}\n"
            f"[cyan]Target Language:[/cyan] {details['target_language']}\n"
            f"[cyan]Total Files:[/cyan] {details['total_files']}\n"
            f"[cyan]Translated:[/cyan] {details['translated_files']}\n"
            f"[cyan]Failed:[/cyan] {details['failed_files']}\n"
            f"[cyan]Last Updated:[/cyan] {details['updated_at'][:19] if details['updated_at'] else 'N/A'}",
            title="Project Information",
            border_style="blue"
        )
        console.print(info_panel)
        console.print()
        
        # Display status summary
        status_table = Table(title="Translation Status", box=box.ROUNDED)
        status_table.add_column("Status", style="cyan")
        status_table.add_column("Count", justify="right", style="magenta")
        
        total = details['total_files']
        for status, count in details['status_counts'].items():
            percentage = count / total * 100 if total > 0 else 0
            status_table.add_row(status, f"{count} ({percentage:.1f}%)")
        
        console.print(status_table)
        console.print()
        
        # Display file details (show first 10 of each status)
        for status, files in details['status_details'].items():
            if not files:
                continue
            
            files_table = Table(title=f"{status.upper()} Files", box=box.ROUNDED, show_header=True)
            files_table.add_column("File Name", style="green")
            files_table.add_column("Complexity", justify="right", style="yellow")
            files_table.add_column("Size (bytes)", justify="right", style="blue")
            
            if status == 'completed':
                files_table.add_column("Confidence", justify="right", style="cyan")
            
            for file_info in files[:10]:  # Show first 10
                row = [
                    file_info['name'],
                    f"{file_info['complexity']:.2f}",
                    str(file_info['size'])
                ]
                if status == 'completed' and file_info.get('confidence') is not None:
                    row.append(f"{file_info['confidence']:.2f}")
                elif status == 'completed':
                    row.append("N/A")
                
                files_table.add_row(*row)
            
            if len(files) > 10:
                files_table.add_row(f"... and {len(files) - 10} more files", "", "", "")
            
            if files:
                console.print(files_table)
                console.print()


def view_progress(state_dir: Optional[Path] = None, project_id: Optional[str] = None, project_name: Optional[str] = None):
    """Convenience function to view progress"""
    viewer = ProgressViewer(state_dir)
    
    if project_id or project_name:
        viewer.display_project_details(project_id, project_name)
    else:
        viewer.display_summary()


if __name__ == "__main__":
    import sys
    
    viewer = ProgressViewer()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all" or sys.argv[1] == "-a":
            viewer.display_summary()
        elif sys.argv[1].startswith("project_") or len(sys.argv[1]) == 36:  # UUID format
            viewer.display_project_details(project_id=sys.argv[1])
        else:
            viewer.display_project_details(project_name=sys.argv[1])
    else:
        viewer.display_summary()

