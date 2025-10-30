"""
Data models for CStarX v2.0
"""

from typing import Dict, List, Optional, Set, Any, Union
from pathlib import Path
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class TranslationUnitType(str, Enum):
    """Types of translation units"""
    PURE_HEADER = "pure_header"
    PURE_IMPL = "pure_impl"
    COMPLETE = "complete"
    TEST = "test"


class TranslationStatus(str, Enum):
    """Translation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DependencyType(str, Enum):
    """Types of dependencies"""
    INCLUDE = "include"
    IMPORT = "import"
    LINK = "link"
    RUNTIME = "runtime"


class Dependency(BaseModel):
    """Represents a dependency relationship"""
    source: str = Field(description="Source file path")
    target: str = Field(description="Target file path")
    type: DependencyType = Field(description="Type of dependency")
    line_number: Optional[int] = Field(default=None, description="Line number where dependency occurs")
    context: Optional[str] = Field(default=None, description="Context around the dependency")


class TranslationUnit(BaseModel):
    """Represents a translation unit (file or module)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(description="Name of the translation unit")
    path: Path = Field(description="File path")
    type: TranslationUnitType = Field(description="Type of translation unit")
    status: TranslationStatus = Field(default=TranslationStatus.PENDING)
    
    # File content
    original_content: Optional[str] = Field(default=None)
    translated_content: Optional[str] = Field(default=None)
    
    # Dependencies
    dependencies: List[Dependency] = Field(default_factory=list)
    dependents: List[str] = Field(default_factory=list)
    
    # Metadata
    size: int = Field(default=0, description="File size in bytes")
    complexity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Translation metadata
    translation_time: Optional[float] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    quality_score: Optional[float] = Field(default=None)
    translation_result: Optional['TranslationResult'] = Field(default=None)
    
    def get_dependencies(self) -> List[str]:
        """Get list of dependency file paths"""
        return [dep.target for dep in self.dependencies]
    
    def add_dependency(self, target: str, dep_type: DependencyType, line_number: Optional[int] = None) -> None:
        """Add a dependency"""
        dep = Dependency(
            source=str(self.path),
            target=target,
            type=dep_type,
            line_number=line_number
        )
        self.dependencies.append(dep)
    
    def is_ready_for_translation(self, completed_units: Set[str], project: Optional['Project'] = None) -> bool:
        """Check if this unit is ready for translation
        
        Args:
            completed_units: Set of completed unit IDs (or paths if project is None)
            project: Optional project to map dependency paths to unit IDs
        """
        dependency_paths = self.get_dependencies()
        
        # If project is provided, map dependency paths to unit IDs
        if project:
            # Filter out system includes (like /usr/include/*)
            project_deps = [dep for dep in dependency_paths if not dep.startswith('/usr/include')]
            
            if not project_deps:
                # No project dependencies, ready to translate
                return True
            
            # Check if all project dependencies are completed
            for dep_path in project_deps:
                # Find unit by path
                dep_unit = project.find_unit_by_path(dep_path)
                if dep_unit and dep_unit.id not in completed_units:
                    return False
            return True
        else:
            # Fallback: check if paths are directly in completed_units
            # (for backward compatibility, but may not work correctly)
            return all(dep in completed_units for dep in dependency_paths)


class Project(BaseModel):
    """Represents a C/C++ project"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(description="Project name")
    path: Path = Field(description="Project root path")
    target_language: str = Field(default="rust")
    
    # Translation units
    units: List[TranslationUnit] = Field(default_factory=list)
    
    # Project metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Statistics
    total_files: int = Field(default=0)
    translated_files: int = Field(default=0)
    failed_files: int = Field(default=0)
    
    # Configuration
    config: Optional[Dict[str, Any]] = Field(default=None)
    
    def add_unit(self, unit: TranslationUnit) -> None:
        """Add a translation unit to the project"""
        self.units.append(unit)
        self.total_files = len(self.units)
        self.updated_at = datetime.now()
    
    def get_units_by_status(self, status: TranslationStatus) -> List[TranslationUnit]:
        """Get units by status"""
        return [unit for unit in self.units if unit.status == status]
    
    def get_ready_units(self, completed_units: Set[str]) -> List[TranslationUnit]:
        """Get units ready for translation"""
        return [unit for unit in self.units if unit.is_ready_for_translation(completed_units, project=self)]
    
    def update_statistics(self) -> None:
        """Update project statistics"""
        self.total_files = len(self.units)
        self.translated_files = len(self.get_units_by_status(TranslationStatus.COMPLETED))
        self.failed_files = len(self.get_units_by_status(TranslationStatus.FAILED))
        self.updated_at = datetime.now()
    
    def get_unit_result(self, unit_id: str) -> Optional['TranslationResult']:
        """Get translation result for a unit"""
        for unit in self.units:
            if unit.id == unit_id:
                return unit.translation_result
        return None
    
    def find_unit_by_path(self, path: str) -> Optional['TranslationUnit']:
        """Find a unit by its file path"""
        path_obj = Path(path)
        for unit in self.units:
            # Try exact match first
            if str(unit.path) == path or str(unit.path.resolve()) == str(path_obj.resolve()):
                return unit
            # Try relative path match
            try:
                if path in str(unit.path) or str(unit.path).endswith(path) or path.endswith(str(unit.path)):
                    return unit
            except:
                pass
        return None


class TranslationResult(BaseModel):
    """Result of a translation operation"""
    unit_id: str = Field(description="ID of the translated unit")
    success: bool = Field(description="Whether translation was successful")
    translated_content: Optional[str] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    translation_time: float = Field(description="Time taken for translation")
    quality_score: Optional[float] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # Conversation history for debugging and analysis
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Full LLM conversation including prompts and responses")


class TranslationSession(BaseModel):
    """Represents a translation session"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = Field(description="ID of the project being translated")
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(default=None)
    
    # Session state
    current_unit: Optional[str] = Field(default=None)
    completed_units: Set[str] = Field(default_factory=set)
    failed_units: Set[str] = Field(default_factory=set)
    
    # Results
    results: List[TranslationResult] = Field(default_factory=list)
    
    # Statistics
    total_units: int = Field(default=0)
    completed_count: int = Field(default=0)
    failed_count: int = Field(default=0)
    
    def is_complete(self) -> bool:
        """Check if session is complete"""
        return self.completed_count + self.failed_count >= self.total_units
    
    def add_result(self, result: TranslationResult) -> None:
        """Add a translation result"""
        self.results.append(result)
        if result.success:
            self.completed_units.add(result.unit_id)
            self.completed_count += 1
        else:
            self.failed_units.add(result.unit_id)
            self.failed_count += 1
    
    def get_progress(self) -> float:
        """Get translation progress as percentage"""
        if self.total_units == 0:
            return 0.0
        return (self.completed_count + self.failed_count) / self.total_units * 100
