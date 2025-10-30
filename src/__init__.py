"""
CStarX v2.0 - Advanced C/C++ to Rust Translation Tool

A multi-agent system for intelligent code translation with dependency analysis,
state management, and MCP integration.
"""

__version__ = "2.0.0"
__author__ = "CStarX Team"
__email__ = "team@cstarx.dev"

from .core.translator import Translator
from .core.dependency_analyzer import DependencyAnalyzer
from .core.state_manager import StateManager
from .agents.orchestrator import AgentOrchestrator
from .models.project import Project, TranslationUnit
from .models.config import Config
from .mcp import MCPClient, MCPTranslator

__all__ = [
    "Translator",
    "DependencyAnalyzer", 
    "StateManager",
    "AgentOrchestrator",
    "Project",
    "TranslationUnit",
    "Config",
    "MCPClient",
    "MCPTranslator",
]
