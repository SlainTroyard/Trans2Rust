"""
Unit tests for CStarX v2.0
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch

from cstarx.models.config import Config, ModelProvider, TranslationStrategy
from cstarx.models.project import Project, TranslationUnit, TranslationUnitType, TranslationStatus
from cstarx.core.dependency_analyzer import DependencyAnalyzer, DependencyGraph
from cstarx.core.state_manager import StateManager
from cstarx.agents.orchestrator import AgentOrchestrator


class TestConfig:
    """Test configuration management"""
    
    def test_default_config(self):
        """Test default configuration"""
        config = Config()
        assert config.model.provider == ModelProvider.OPENAI
        assert config.translation.strategy == TranslationStrategy.ADAPTIVE
        assert config.translation.max_parallel_workers == 5
    
    def test_config_from_env(self):
        """Test configuration from environment variables"""
        config = Config.from_env()
        assert isinstance(config, Config)
    
    def test_config_validation(self):
        """Test configuration validation"""
        config = Config()
        assert config.model.temperature >= 0.0
        assert config.model.temperature <= 2.0
        assert config.translation.max_parallel_workers >= 1
        assert config.translation.max_parallel_workers <= 20


class TestTranslationUnit:
    """Test translation unit model"""
    
    def test_translation_unit_creation(self):
        """Test creating a translation unit"""
        unit = TranslationUnit(
            name="test.cpp",
            path=Path("test.cpp"),
            type=TranslationUnitType.PURE_IMPL
        )
        
        assert unit.name == "test.cpp"
        assert unit.type == TranslationUnitType.PURE_IMPL
        assert unit.status == TranslationStatus.PENDING
    
    def test_translation_unit_dependencies(self):
        """Test translation unit dependencies"""
        unit = TranslationUnit(
            name="test.cpp",
            path=Path("test.cpp"),
            type=TranslationUnitType.COMPLETE
        )
        
        unit.add_dependency("header.h", "include")
        assert len(unit.dependencies) == 1
        assert unit.get_dependencies() == ["header.h"]
    
    def test_translation_unit_ready_check(self):
        """Test if unit is ready for translation"""
        unit = TranslationUnit(
            name="test.cpp",
            path=Path("test.cpp"),
            type=TranslationUnitType.COMPLETE
        )
        
        unit.add_dependency("header.h", "include")
        
        # Not ready - dependency not completed
        assert not unit.is_ready_for_translation(set())
        
        # Ready - dependency completed
        assert unit.is_ready_for_translation({"header.h"})


class TestProject:
    """Test project model"""
    
    def test_project_creation(self):
        """Test creating a project"""
        project = Project(
            name="test_project",
            path=Path("test_project")
        )
        
        assert project.name == "test_project"
        assert project.total_files == 0
        assert project.translated_files == 0
    
    def test_project_add_unit(self):
        """Test adding units to project"""
        project = Project(
            name="test_project",
            path=Path("test_project")
        )
        
        unit = TranslationUnit(
            name="test.cpp",
            path=Path("test.cpp"),
            type=TranslationUnitType.PURE_IMPL
        )
        
        project.add_unit(unit)
        assert project.total_files == 1
        assert len(project.units) == 1
    
    def test_project_statistics(self):
        """Test project statistics"""
        project = Project(
            name="test_project",
            path=Path("test_project")
        )
        
        # Add units with different statuses
        unit1 = TranslationUnit(
            name="test1.cpp",
            path=Path("test1.cpp"),
            type=TranslationUnitType.PURE_IMPL,
            status=TranslationStatus.COMPLETED
        )
        
        unit2 = TranslationUnit(
            name="test2.cpp",
            path=Path("test2.cpp"),
            type=TranslationUnitType.PURE_IMPL,
            status=TranslationStatus.FAILED
        )
        
        project.add_unit(unit1)
        project.add_unit(unit2)
        
        project.update_statistics()
        
        assert project.total_files == 2
        assert project.translated_files == 1
        assert project.failed_files == 1


class TestDependencyAnalyzer:
    """Test dependency analysis"""
    
    def test_dependency_graph_creation(self):
        """Test creating a dependency graph"""
        units = [
            TranslationUnit(
                name="main.cpp",
                path=Path("main.cpp"),
                type=TranslationUnitType.PURE_IMPL
            ),
            TranslationUnit(
                name="header.h",
                path=Path("header.h"),
                type=TranslationUnitType.PURE_HEADER
            )
        ]
        
        # Add dependency
        units[0].add_dependency("header.h", "include")
        
        analyzer = DependencyAnalyzer(Mock())
        graph = analyzer.build_dependency_graph(units)
        
        assert "main.cpp" in graph.nodes
        assert "header.h" in graph.nodes
        assert "header.h" in graph.edges["main.cpp"]
    
    def test_topological_sort(self):
        """Test topological sorting"""
        analyzer = DependencyAnalyzer(Mock())
        
        # Create a simple graph
        nodes = {"A", "B", "C"}
        edges = {"A": {"B"}, "B": {"C"}, "C": set()}
        in_degree = {"A": 0, "B": 1, "C": 1}
        out_degree = {"A": 1, "B": 1, "C": 0}
        
        graph = DependencyGraph(nodes, edges, in_degree, out_degree)
        
        # Test DFS sort
        sorted_nodes = analyzer.topological_sort(graph, use_dfs=True)
        assert len(sorted_nodes) == 3
        assert "A" in sorted_nodes
        assert "B" in sorted_nodes
        assert "C" in sorted_nodes
        
        # Test BFS sort
        sorted_nodes = analyzer.topological_sort(graph, use_dfs=False)
        assert len(sorted_nodes) == 3


class TestStateManager:
    """Test state management"""
    
    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for testing"""
        return tmp_path
    
    @pytest.fixture
    def config(self, temp_dir):
        """Create test configuration"""
        config = Config()
        config.output.output_dir = temp_dir
        return config
    
    @pytest.fixture
    def state_manager(self, config):
        """Create state manager for testing"""
        return StateManager(config)
    
    @pytest.mark.asyncio
    async def test_save_load_project(self, state_manager, temp_dir):
        """Test saving and loading project"""
        project = Project(
            name="test_project",
            path=temp_dir
        )
        
        unit = TranslationUnit(
            name="test.cpp",
            path=temp_dir / "test.cpp",
            type=TranslationUnitType.PURE_IMPL
        )
        
        project.add_unit(unit)
        
        # Save project
        await state_manager.save_project(project)
        
        # Load project
        loaded_project = await state_manager.load_project(project.id)
        
        assert loaded_project is not None
        assert loaded_project.name == project.name
        assert len(loaded_project.units) == 1
    
    @pytest.mark.asyncio
    async def test_state_summary(self, state_manager):
        """Test state summary"""
        summary = await state_manager.get_state_summary()
        assert summary['status'] == 'no_active_project'


class TestAgentOrchestrator:
    """Test agent orchestrator"""
    
    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return Config()
    
    @pytest.fixture
    def orchestrator(self, config):
        """Create orchestrator for testing"""
        return AgentOrchestrator(config)
    
    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization"""
        assert orchestrator.project_manager is not None
        assert orchestrator.tech_leader is not None
        assert orchestrator.translator is not None
        assert orchestrator.quality_agent is not None


# Integration tests
class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_translation(self, tmp_path):
        """Test end-to-end translation process"""
        # This would be a more comprehensive test
        # that tests the entire translation pipeline
        pass


if __name__ == "__main__":
    pytest.main([__file__])
