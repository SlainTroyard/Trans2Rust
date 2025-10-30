"""
Main translator class for CStarX v2.0
"""

import asyncio
import json
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger

from ..models.config import Config
from ..models.project import Project, TranslationStatus
from .dependency_analyzer import DependencyAnalyzer
from .state_manager import StateManager
from ..agents.orchestrator import AgentOrchestrator
from ..mcp import MCPClient, MCPTranslator


class Translator:
    """Main translator class that orchestrates the entire translation process"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.dependency_analyzer = DependencyAnalyzer(self.config.dependency)
        self.state_manager = StateManager(self.config)
        self.mcp_client = MCPClient(self.config)
        self.mcp_translator = MCPTranslator(self.mcp_client, self.config)
        self.orchestrator = AgentOrchestrator(self.config)
        
        logger.info("Translator initialized with MCP support")
    
    async def translate_project(self, project_path: str, output_path: Optional[str] = None) -> Project:
        """Translate a C/C++ project to Rust"""
        logger.info(f"Starting translation: {project_path}")
        
        # Set output path
        if output_path:
            self.config.output.output_dir = Path(output_path)
        
        # Check if project already exists in state
        project_path_obj = Path(project_path).resolve()
        existing_project = await self._find_existing_project(project_path_obj)
        
        if existing_project:
            logger.info(f"Found existing project: {existing_project.id}")
            project = existing_project
            # Clean up duplicate state files for this project path
            await self._cleanup_duplicate_states(project.id, project_path_obj)
        else:
            # Analyze project
            project = await self.dependency_analyzer.analyze_project(project_path_obj)
            await self.state_manager.save_project(project)
        
        # Translate using orchestrator with MCP and state manager
        translated_project = await self.orchestrator.translate_project(
            project_path,
            mcp_client=self.mcp_client,
            mcp_translator=self.mcp_translator,
            state_manager=self.state_manager
        )
        
        # Save final state
        await self.state_manager.save_project(translated_project)
        
        # Always generate output files to final directory
        await self._generate_output_files(translated_project, use_final_dir=True)
        
            # Verify modules compilation in final directory
        final_project_dir = Path(self.config.output.output_dir) / f"{translated_project.name}-final"
        if final_project_dir.exists():
            await self._verify_modules_compilation(translated_project, final_project_dir)
        
        # Verify project compilation in final directory (optional, can be disabled)
        if final_project_dir.exists():
            await self._verify_project_compilation(translated_project, final_project_dir)
        
        logger.info("Translation complete")
        return translated_project
    
    async def _find_existing_project(self, project_path: Path) -> Optional[Project]:
        """Find existing project in state by path"""
        # Try to find project by matching path
        state_dir = self.state_manager.state_dir
        project_files = list(state_dir.glob("project_*.json"))
        
        for project_file in project_files:
            try:
                with open(project_file, 'r') as f:
                    project_data = json.load(f)
                    # Match by normalized path
                    stored_path = Path(project_data.get('path', '')).resolve()
                    current_path = project_path.resolve()
                    if stored_path == current_path:
                        # Found matching project, load it
                        project_id = project_data.get('id')
                        if project_id:
                            project = await self.state_manager.load_project(project_id)
                            if project:
                                logger.info(f"Found existing project by path: {project.id}")
                                return project
            except Exception as e:
                logger.debug(f"Error checking project file {project_file}: {e}")
                continue
        
        return None
    
    async def _generate_output_files(self, project: Project, use_final_dir: bool = False) -> None:
        """Generate output Rust files
        
        Args:
            project: Project to generate files for
            use_final_dir: If True, create a new 'final' directory for final output
                          (e.g., output/{project-name}-final/), otherwise use regular directory
        """
        output_dir = self.config.output.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine output directory name
        if use_final_dir:
            # Final output goes to a separate directory (e.g., output/01-Primary-final/)
            project_output_dir = output_dir / f"{project.name}-final"
            logger.info(f"Generating final output files in: {project_output_dir}")
        else:
            # Regular output directory (for real-time generation)
            project_output_dir = output_dir / project.name
            logger.info(f"Generating output files in: {project_output_dir}")
        
        project_output_dir.mkdir(parents=True, exist_ok=True)
        
        translated_count = 0
        for unit in project.units:
            # Check if translation result exists
            translation_result = unit.translation_result if unit.translation_result else project.get_unit_result(unit.id)
            
            # Also check unit's translated_content directly (fallback)
            if not translation_result and unit.translated_content:
                # Create a minimal result for backward compatibility
                from ..models.project import TranslationResult
                translation_result = TranslationResult(
                    unit_id=unit.id,
                    success=True,
                    translated_content=unit.translated_content,
                    translation_time=0.0
                )
            
            if translation_result and translation_result.success and translation_result.translated_content:
                # Determine output path preserving directory structure
                try:
                    relative_path = unit.path.relative_to(project.path)
                except ValueError:
                    # If paths are not related, use just the filename
                    relative_path = Path(unit.path.name)
                
                # Create Rust file path
                rust_file_path = project_output_dir / relative_path
                rust_file_path = rust_file_path.with_suffix('.rs')
                
                # Create output directory
                rust_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write translated content
                with open(rust_file_path, 'w', encoding='utf-8') as f:
                    f.write(translation_result.translated_content)
                
                translated_count += 1
                logger.info(f"Generated: {rust_file_path}")
            else:
                logger.warning(f"No translation result for {unit.name}, skipping output")
        
        logger.info(f"Generated {translated_count} translated files in {project_output_dir}")
        
        # Generate Cargo.toml if needed
        await self._generate_cargo_toml(project, project_output_dir)
    
    async def _generate_cargo_toml(self, project: Project, output_dir: Path) -> None:
        """Generate Cargo.toml for the Rust project"""
        cargo_toml_path = output_dir / "Cargo.toml"
        
        # Safe project name for Cargo
        safe_name = project.name.lower().replace(' ', '-').replace('_', '-')
        # Remove special characters
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '-')
        if not safe_name or safe_name[0].isdigit():
            safe_name = f"translated-{safe_name}"
        
        cargo_content = f"""[package]
name = "{safe_name}"
version = "0.1.0"
edition = "2021"

[dependencies]
# Add dependencies as needed
# libc = "0.2"
"""
        
        with open(cargo_toml_path, 'w', encoding='utf-8') as f:
            f.write(cargo_content)
        
        logger.info(f"Generated: {cargo_toml_path}")
        
        # Also generate .gitignore
        gitignore_path = output_dir / ".gitignore"
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write("/target/\nCargo.lock\n")
    
    async def _verify_project_compilation(self, project: Project, project_dir: Optional[Path] = None) -> None:
        """Verify that the translated project compiles with detailed error analysis"""
        from ..utils.compilation_verifier import CompilationVerifier
        
        if project_dir is None:
            project_output_dir = Path(self.config.output.output_dir) / project.name
        else:
            project_output_dir = project_dir
        
        if not (project_output_dir / "Cargo.toml").exists():
            logger.warning("Cargo.toml not found, skipping compilation verification")
            return
        
        logger.info(f"Verifying project compilation: {project_output_dir}")
        
        try:
            verifier = CompilationVerifier(project_output_dir)
            result = await verifier.cargo_check()
            
            if result["success"]:
                logger.info(f"✓ Project compilation successful: {project.name}")
                if result.get("warning_count", 0) > 0:
                    logger.info(f"  ({result['warning_count']} warnings)")
            else:
                errors = result.get("errors", [])
                logger.warning(f"⚠ Project compilation failed: {project.name}")
                logger.warning(f"  Found {len(errors)} compilation errors")
                
                # Group errors by file
                errors_by_file = {}
                for err in errors:
                    file_name = err.get("file", "unknown")
                    if file_name not in errors_by_file:
                        errors_by_file[file_name] = []
                    errors_by_file[file_name].append(err)
                
                # Show top 5 errors
                shown = 0
                for file_name, file_errors in list(errors_by_file.items())[:5]:
                    for err in file_errors[:2]:  # Max 2 per file
                        if shown < 5:
                            logger.warning(f"  Error {shown+1}: {Path(file_name).name} - {err.get('message', '')[:80]}")
                            shown += 1
                            if shown >= 5:
                                break
                
                if len(errors) > 5:
                    logger.warning(f"  ... and {len(errors) - 5} more errors")
        
        except FileNotFoundError:
            logger.warning("cargo not found, skipping compilation verification")
        except Exception as e:
            logger.warning(f"Compilation verification failed: {e}")
    
    async def _verify_modules_compilation(self, project: Project, project_dir: Optional[Path] = None) -> None:
        """Verify modules compilation independently, checking each module's integrity"""
        from ..utils.compilation_verifier import CompilationVerifier
        
        if project_dir is None:
            project_output_dir = Path(self.config.output.output_dir) / project.name
        else:
            project_output_dir = project_dir
        
        # Group files by directory to identify modules
        modules = {}
        for unit in project.units:
            if unit.status == TranslationStatus.COMPLETED and unit.translated_content:
                try:
                    relative_path = unit.path.relative_to(project.path)
                    module_dir = relative_path.parent
                    if module_dir not in modules:
                        modules[module_dir] = []
                    modules[module_dir].append(unit)
                except ValueError:
                    continue
        
        logger.info(f"Found {len(modules)} potential modules, verifying compilation")
        
        verified_modules = 0
        failed_modules = 0
        
        for module_dir, units in modules.items():
            module_path = project_output_dir / module_dir
            
            # Check if this is a Rust module (has Cargo.toml)
            if (module_path / "Cargo.toml").exists():
                verifier = CompilationVerifier(module_path)
                result = await verifier.verify_module(module_path)
                
                if result["success"]:
                    verified_modules += 1
                    logger.debug(f"✓ Module verified: {module_dir}")
                else:
                    failed_modules += 1
                    error_count = result.get("error_count", 0)
                    logger.warning(f"⚠ Module failed: {module_dir} ({error_count} errors)")
        
        logger.info(f"Module verification: {verified_modules} passed, {failed_modules} failed")
    
    async def get_translation_status(self) -> Dict[str, Any]:
        """Get current translation status"""
        return await self.state_manager.get_state_summary()
    
    async def pause_translation(self) -> None:
        """Pause current translation"""
        # Create snapshot
        snapshot = await self.state_manager.create_snapshot()
        logger.info(f"Translation paused, snapshot created: {snapshot.timestamp}")
    
    async def resume_translation(self) -> None:
        """Resume translation from last snapshot"""
        # Find latest snapshot
        state_dir = self.state_manager.state_dir
        snapshot_files = list(state_dir.glob("snapshot_*.json"))
        
        if not snapshot_files:
            logger.warning("No snapshots found to resume from")
            return
        
        # Load latest snapshot
        latest_snapshot_file = max(snapshot_files, key=lambda f: f.stat().st_mtime)
        
        with open(latest_snapshot_file, 'r') as f:
            snapshot_data = f.read()
        
        # Restore from snapshot
        from ..core.state_manager import StateSnapshot
        snapshot = StateSnapshot(**json.loads(snapshot_data))
        await self.state_manager.restore_snapshot(snapshot)
        
        logger.info(f"Translation resumed from snapshot: {snapshot.timestamp}")
    
    async def _cleanup_duplicate_states(self, current_project_id: str, project_path: Path) -> None:
        """Clean up duplicate state files for the same project path"""
        state_dir = self.state_manager.state_dir
        project_files = list(state_dir.glob("project_*.json"))
        
        cleaned = 0
        for project_file in project_files:
            try:
                with open(project_file, 'r') as f:
                    project_data = json.load(f)
                    stored_path = Path(project_data.get('path', '')).resolve()
                    stored_id = project_data.get('id')
                    
                    # If same path but different ID, remove the duplicate
                    if stored_path == project_path.resolve() and stored_id != current_project_id:
                        project_file.unlink()
                        cleaned += 1
                        logger.info(f"Removed duplicate state file: {project_file.name}")
            except Exception as e:
                logger.debug(f"Error checking project file {project_file}: {e}")
                continue
        
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} duplicate state file(s)")
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        await self.state_manager.cleanup_old_states()
        logger.info("Cleanup complete")
