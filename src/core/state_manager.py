"""
State management system for CStarX v2.0
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from loguru import logger

from ..models.project import Project, TranslationUnit, TranslationSession, TranslationResult
from ..models.config import Config


@dataclass
class StateSnapshot:
    """Represents a snapshot of the system state"""
    timestamp: datetime
    project_id: str
    session_id: str
    completed_units: Set[str]
    failed_units: Set[str]
    current_unit: Optional[str]
    progress: float
    metadata: Dict[str, Any]


class StateManager:
    """Manages system state and persistence"""
    
    def __init__(self, config: Config):
        self.config = config
        self.state_dir = Path(config.output.output_dir) / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_project: Optional[Project] = None
        self.current_session: Optional[TranslationSession] = None
        self.state_lock = asyncio.Lock()
        
        logger.info("State manager initialized")
    
    async def save_project(self, project: Project) -> None:
        """Save project state"""
        async with self.state_lock:
            project_file = self.state_dir / f"project_{project.id}.json"
            
            project_data = {
                'id': project.id,
                'name': project.name,
                'path': str(project.path),
                'target_language': project.target_language,
                'units': [self._unit_to_dict(unit) for unit in project.units],
                'created_at': project.created_at.isoformat(),
                'updated_at': project.updated_at.isoformat(),
                'total_files': project.total_files,
                'translated_files': project.translated_files,
                'failed_files': project.failed_files,
                'config': project.config
            }
            
            with open(project_file, 'w') as f:
                json.dump(project_data, f, indent=2)
            
            self.current_project = project
            logger.info(f"Project saved: {project.id}")
    
    async def load_project(self, project_id: str) -> Optional[Project]:
        """Load project state"""
        async with self.state_lock:
            project_file = self.state_dir / f"project_{project_id}.json"
            
            if not project_file.exists():
                return None
            
            with open(project_file, 'r') as f:
                project_data = json.load(f)
            
            # Reconstruct project
            project = Project(
                id=project_data['id'],
                name=project_data['name'],
                path=Path(project_data['path']),
                target_language=project_data['target_language'],
                created_at=datetime.fromisoformat(project_data['created_at']),
                updated_at=datetime.fromisoformat(project_data['updated_at']),
                total_files=project_data['total_files'],
                translated_files=project_data['translated_files'],
                failed_files=project_data['failed_files'],
                config=project_data.get('config')
            )
            
            # Reconstruct units
            units = []
            for unit_data in project_data['units']:
                unit = self._dict_to_unit(unit_data)
                units.append(unit)
            
            project.units = units
            self.current_project = project
            
            logger.info(f"Project loaded: {project.id}")
            return project
    
    async def save_session(self, session: TranslationSession) -> None:
        """Save session state"""
        async with self.state_lock:
            session_file = self.state_dir / f"session_{session.id}.json"
            
            session_data = {
                'id': session.id,
                'project_id': session.project_id,
                'started_at': session.started_at.isoformat(),
                'completed_at': session.completed_at.isoformat() if session.completed_at else None,
                'current_unit': session.current_unit,
                'completed_units': list(session.completed_units),
                'failed_units': list(session.failed_units),
                'total_units': session.total_units,
                'completed_count': session.completed_count,
                'failed_count': session.failed_count,
                'results': [self._result_to_dict(result) for result in session.results]
            }
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            self.current_session = session
            logger.info(f"Session saved: {session.id}")
    
    async def load_session(self, session_id: str) -> Optional[TranslationSession]:
        """Load session state"""
        async with self.state_lock:
            session_file = self.state_dir / f"session_{session_id}.json"
            
            if not session_file.exists():
                return None
            
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Reconstruct session
            session = TranslationSession(
                id=session_data['id'],
                project_id=session_data['project_id'],
                started_at=datetime.fromisoformat(session_data['started_at']),
                completed_at=datetime.fromisoformat(session_data['completed_at']) if session_data['completed_at'] else None,
                current_unit=session_data['current_unit'],
                completed_units=set(session_data['completed_units']),
                failed_units=set(session_data['failed_units']),
                total_units=session_data['total_units'],
                completed_count=session_data['completed_count'],
                failed_count=session_data['failed_count']
            )
            
            # Reconstruct results
            results = []
            for result_data in session_data['results']:
                result = self._dict_to_result(result_data)
                results.append(result)
            
            session.results = results
            self.current_session = session
            
            logger.info(f"Session loaded: {session.id}")
            return session
    
    async def create_snapshot(self) -> StateSnapshot:
        """Create a state snapshot"""
        if not self.current_project or not self.current_session:
            raise ValueError("No active project or session")
        
        snapshot = StateSnapshot(
            timestamp=datetime.now(),
            project_id=self.current_project.id,
            session_id=self.current_session.id,
            completed_units=self.current_session.completed_units.copy(),
            failed_units=self.current_session.failed_units.copy(),
            current_unit=self.current_session.current_unit,
            progress=self.current_session.get_progress(),
            metadata={
                'total_units': self.current_session.total_units,
                'completed_count': self.current_session.completed_count,
                'failed_count': self.current_session.failed_count
            }
        )
        
        # Save snapshot
        snapshot_file = self.state_dir / f"snapshot_{snapshot.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(snapshot_file, 'w') as f:
            json.dump(asdict(snapshot), f, indent=2, default=str)
        
        logger.info(f"Snapshot created: {snapshot_file}")
        return snapshot
    
    async def restore_snapshot(self, snapshot: StateSnapshot) -> None:
        """Restore from a state snapshot"""
        # Load project and session
        project = await self.load_project(snapshot.project_id)
        session = await self.load_session(snapshot.session_id)
        
        if not project or not session:
            raise ValueError("Failed to load project or session from snapshot")
        
        # Restore state
        session.completed_units = snapshot.completed_units.copy()
        session.failed_units = snapshot.failed_units.copy()
        session.current_unit = snapshot.current_unit
        
        # Update counts
        session.completed_count = len(session.completed_units)
        session.failed_count = len(session.failed_units)
        
        # Save restored state
        await self.save_project(project)
        await self.save_session(session)
        
        logger.info(f"State restored from snapshot: {snapshot.timestamp}")
    
    def _unit_to_dict(self, unit: TranslationUnit) -> Dict[str, Any]:
        """Convert TranslationUnit to dictionary"""
        return {
            'id': unit.id,
            'name': unit.name,
            'path': str(unit.path),
            'type': unit.type.value,
            'status': unit.status.value,
            'original_content': unit.original_content,
            'translated_content': unit.translated_content,
            'dependencies': [self._dependency_to_dict(dep) for dep in unit.dependencies],
            'dependents': unit.dependents,
            'size': unit.size,
            'complexity_score': unit.complexity_score,
            'created_at': unit.created_at.isoformat(),
            'updated_at': unit.updated_at.isoformat(),
            'translation_time': unit.translation_time,
            'error_message': unit.error_message,
            'quality_score': unit.quality_score
        }
    
    def _dict_to_unit(self, data: Dict[str, Any]) -> TranslationUnit:
        """Convert dictionary to TranslationUnit"""
        from ..models.project import Dependency, DependencyType, TranslationUnitType, TranslationStatus
        
        # Reconstruct dependencies
        dependencies = []
        for dep_data in data['dependencies']:
            dep = Dependency(
                source=dep_data['source'],
                target=dep_data['target'],
                type=DependencyType(dep_data['type']),
                line_number=dep_data.get('line_number'),
                context=dep_data.get('context')
            )
            dependencies.append(dep)
        
        unit = TranslationUnit(
            id=data['id'],
            name=data['name'],
            path=Path(data['path']),
            type=TranslationUnitType(data['type']),
            status=TranslationStatus(data['status']),
            original_content=data.get('original_content'),
            translated_content=data.get('translated_content'),
            dependencies=dependencies,
            dependents=data['dependents'],
            size=data['size'],
            complexity_score=data['complexity_score'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            translation_time=data.get('translation_time'),
            error_message=data.get('error_message'),
            quality_score=data.get('quality_score')
        )
        
        return unit
    
    def _dependency_to_dict(self, dep: 'Dependency') -> Dict[str, Any]:
        """Convert Dependency to dictionary"""
        return {
            'source': dep.source,
            'target': dep.target,
            'type': dep.type.value,
            'line_number': dep.line_number,
            'context': dep.context
        }
    
    def _result_to_dict(self, result: TranslationResult) -> Dict[str, Any]:
        """Convert TranslationResult to dictionary"""
        return {
            'unit_id': result.unit_id,
            'success': result.success,
            'translated_content': result.translated_content,
            'error_message': result.error_message,
            'translation_time': result.translation_time,
            'quality_score': result.quality_score,
            'metadata': result.metadata,
            'conversation_history': result.conversation_history if hasattr(result, 'conversation_history') else []
        }
    
    def _dict_to_result(self, data: Dict[str, Any]) -> TranslationResult:
        """Convert dictionary to TranslationResult"""
        return TranslationResult(
            unit_id=data['unit_id'],
            success=data['success'],
            translated_content=data.get('translated_content'),
            error_message=data.get('error_message'),
            translation_time=data['translation_time'],
            quality_score=data.get('quality_score'),
            metadata=data.get('metadata', {})
        )
    
    async def cleanup_old_states(self, days: int = 7) -> None:
        """Clean up old state files"""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for state_file in self.state_dir.glob("*.json"):
            if state_file.stat().st_mtime < cutoff_time:
                state_file.unlink()
                logger.info(f"Cleaned up old state file: {state_file}")
    
    async def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of current state"""
        if not self.current_project or not self.current_session:
            return {'status': 'no_active_project'}
        
        return {
            'status': 'active',
            'project': {
                'id': self.current_project.id,
                'name': self.current_project.name,
                'total_files': self.current_project.total_files,
                'translated_files': self.current_project.translated_files,
                'failed_files': self.current_project.failed_files
            },
            'session': {
                'id': self.current_session.id,
                'progress': self.current_session.get_progress(),
                'completed_count': self.current_session.completed_count,
                'failed_count': self.current_session.failed_count,
                'is_complete': self.current_session.is_complete()
            }
        }
