"""
Core dependency analysis engine for CStarX v2.0
"""

import os
import subprocess
import json
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from loguru import logger

from ..models.project import Project, TranslationUnit, Dependency, DependencyType, TranslationUnitType
from ..models.config import DependencyConfig


@dataclass
class DependencyGraph:
    """Represents a dependency graph"""
    nodes: Set[str]
    edges: Dict[str, Set[str]]
    in_degree: Dict[str, int]
    out_degree: Dict[str, int]


class DependencyAnalyzer:
    """Analyzes dependencies in C/C++ projects"""
    
    def __init__(self, config: DependencyConfig):
        self.config = config
        self.clang_path = config.clang_path or "clang"
        self.compile_commands_path = config.compile_commands_path
        
    async def analyze_project(self, project_path: Path) -> Project:
        """Analyze a C/C++ project and extract dependencies"""
        logger.info(f"Analyzing project: {project_path}")
        
        # Find all source files
        source_files = await self._find_source_files(project_path)
        logger.info(f"Found {len(source_files)} source files")
        
        # Create translation units
        units = await self._create_translation_units(source_files)
        
        # Analyze dependencies
        await self._analyze_dependencies(units)
        
        # Create project
        project = Project(
            name=project_path.name,
            path=project_path,
            units=units
        )
        
        project.update_statistics()
        logger.info(f"Project analysis complete: {project.total_files} files")
        
        return project
    
    async def _find_source_files(self, project_path: Path) -> List[Path]:
        """Find all C/C++ source files in the project"""
        source_extensions = {'.c', '.cpp', '.cc', '.cxx', '.c++', '.h', '.hpp', '.hxx', '.h++'}
        source_files = []
        
        for root, dirs, files in os.walk(project_path):
            # Skip build directories
            dirs[:] = [d for d in dirs if d not in {'build', 'cmake-build', '.git', 'node_modules'}]
            
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in source_extensions:
                    source_files.append(file_path)
        
        return sorted(source_files)
    
    async def _create_translation_units(self, source_files: List[Path]) -> List[TranslationUnit]:
        """Create translation units from source files"""
        units = []
        header_files = set()
        
        # First pass: identify header files
        for file_path in source_files:
            if file_path.suffix.lower() in {'.h', '.hpp', '.hxx', '.h++'}:
                header_files.add(file_path)
        
        # Second pass: create units
        for file_path in source_files:
            unit_type = self._determine_unit_type(file_path, header_files)
            
            unit = TranslationUnit(
                name=file_path.name,
                path=file_path,
                type=unit_type,
                size=file_path.stat().st_size if file_path.exists() else 0
            )
            
            units.append(unit)
        
        return units
    
    def _determine_unit_type(self, file_path: Path, header_files: Set[Path]) -> TranslationUnitType:
        """Determine the type of translation unit"""
        suffix = file_path.suffix.lower()
        
        if suffix in {'.h', '.hpp', '.hxx', '.h++'}:
            return TranslationUnitType.PURE_HEADER
        elif suffix in {'.c', '.cpp', '.cc', '.cxx', '.c++'}:
            # Check if there's a corresponding header
            header_path = file_path.with_suffix('.h')
            if header_path in header_files:
                return TranslationUnitType.COMPLETE
            else:
                return TranslationUnitType.PURE_IMPL
        else:
            return TranslationUnitType.PURE_IMPL
    
    async def _analyze_dependencies(self, units: List[TranslationUnit]) -> None:
        """Analyze dependencies between translation units"""
        logger.info("Analyzing dependencies...")
        
        for unit in units:
            if unit.path.exists():
                dependencies = await self._extract_dependencies(unit.path)
                unit.dependencies = dependencies
                
                # Update dependents
                for dep in dependencies:
                    target_unit = self._find_unit_by_path(units, dep.target)
                    if target_unit:
                        target_unit.dependents.append(str(unit.path))
    
    async def _extract_dependencies(self, file_path: Path) -> List[Dependency]:
        """Extract dependencies from a source file"""
        dependencies = []
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract #include statements
            import re
            include_pattern = r'#include\s*[<"]([^>"]+)[>"]'
            matches = re.finditer(include_pattern, content)
            
            for match in matches:
                include_path = match.group(1)
                line_number = content[:match.start()].count('\n') + 1
                
                # Resolve include path
                resolved_path = await self._resolve_include_path(file_path, include_path)
                if resolved_path:
                    dep = Dependency(
                        source=str(file_path),
                        target=str(resolved_path),
                        type=DependencyType.INCLUDE,
                        line_number=line_number
                    )
                    dependencies.append(dep)
        
        except Exception as e:
            logger.warning(f"Failed to analyze dependencies for {file_path}: {e}")
        
        return dependencies
    
    async def _resolve_include_path(self, source_file: Path, include_path: str) -> Optional[Path]:
        """Resolve an include path to an actual file"""
        # Try relative to source file directory
        relative_path = source_file.parent / include_path
        if relative_path.exists():
            return relative_path
        
        # Try include paths from config
        for include_dir in self.config.include_paths:
            full_path = Path(include_dir) / include_path
            if full_path.exists():
                return full_path
        
        # Try system include paths
        system_paths = [
            Path("/usr/include"),
            Path("/usr/local/include"),
            Path("/usr/include/c++"),
        ]
        
        for system_path in system_paths:
            full_path = system_path / include_path
            if full_path.exists():
                return full_path
        
        return None
    
    def _find_unit_by_path(self, units: List[TranslationUnit], path: str) -> Optional[TranslationUnit]:
        """Find a translation unit by path"""
        for unit in units:
            if str(unit.path) == path:
                return unit
        return None
    
    def build_dependency_graph(self, units: List[TranslationUnit]) -> DependencyGraph:
        """Build a dependency graph from translation units"""
        nodes = set()
        edges = {}
        in_degree = {}
        out_degree = {}
        
        # Initialize nodes
        for unit in units:
            path = str(unit.path)
            nodes.add(path)
            edges[path] = set()
            in_degree[path] = 0
            out_degree[path] = 0
        
        # Add edges
        for unit in units:
            source = str(unit.path)
            for dep in unit.dependencies:
                target = dep.target
                if target in nodes:
                    edges[source].add(target)
                    in_degree[target] += 1
                    out_degree[source] += 1
        
        return DependencyGraph(nodes, edges, in_degree, out_degree)
    
    def topological_sort(self, graph: DependencyGraph, use_dfs: bool = True) -> List[str]:
        """Perform topological sort on the dependency graph"""
        if use_dfs:
            return self._topological_sort_dfs(graph)
        else:
            return self._topological_sort_bfs(graph)
    
    def _topological_sort_dfs(self, graph: DependencyGraph) -> List[str]:
        """Topological sort using DFS"""
        visited = set()
        result = []
        
        def dfs(node: str) -> None:
            if node in visited:
                return
            visited.add(node)
            
            for neighbor in graph.edges[node]:
                dfs(neighbor)
            
            result.append(node)
        
        for node in graph.nodes:
            if node not in visited:
                dfs(node)
        
        return result
    
    def _topological_sort_bfs(self, graph: DependencyGraph) -> List[str]:
        """Topological sort using BFS (Kahn's algorithm)"""
        from collections import deque
        
        queue = deque()
        result = []
        in_degree_copy = graph.in_degree.copy()
        
        # Start with nodes that have no incoming edges
        for node in graph.nodes:
            if in_degree_copy[node] == 0:
                queue.append(node)
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            # Remove current node and update in-degrees
            for neighbor in graph.edges[current]:
                in_degree_copy[neighbor] -= 1
                if in_degree_copy[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
    
    def optimize_translation_order(self, units: List[TranslationUnit]) -> List[TranslationUnit]:
        """Optimize the order of translation units for parallel processing"""
        graph = self.build_dependency_graph(units)
        sorted_paths = self.topological_sort(graph)
        
        # Create a mapping from path to unit
        path_to_unit = {str(unit.path): unit for unit in units}
        
        # Return units in topological order
        ordered_units = []
        for path in sorted_paths:
            if path in path_to_unit:
                ordered_units.append(path_to_unit[path])
        
        return ordered_units
