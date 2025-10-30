# CStarX v2.0 - Advanced C/C++ to Rust Translation Tool

A multi-agent system for intelligent C/C++ to Rust code translation, featuring dependency analysis, state management, and MCP integration.

## Features

### Multi-Agent Architecture
- Project Manager: Orchestrates the entire translation process
- Tech Leader: Analyzes code complexity and determines translation strategies
- Translator Agent: Executes intelligent code translation
- Quality Agent: Ensures translation quality and correctness

### Advanced Dependency Analysis
- Static Analysis: Based on clang AST for precise dependency detection
- Topological Sorting: Intelligent ordering for parallel processing
- Dynamic Analysis: Runtime dependency detection and optimization

### State Management
- Persistent State: Save and resume translation sessions
- Snapshot System: Create checkpoints for long-running translations
- Progress Tracking: Real-time monitoring of translation progress

### Modern Technology Stack
- MCP Integration: Model Context Protocol for enhanced LLM interactions
- FastAPI Backend: High-performance web API
- React Frontend: Modern, responsive user interface
- Async Processing: Concurrent translation for improved performance

## Requirements

- Python 3.11+
- Rust 1.70+
- Node.js 18+ (for frontend)
- clang/LLVM (for dependency analysis)
- Git

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/cstarx/cstarx-v2.git
cd cstarx-v2
```

### 2. Install Python Dependencies
```bash
pip install -e .
```

### 3. Install Frontend Dependencies
```bash
cd frontend
npm install
```

### 4. Configure Environment
```bash
cp env.example .env
# Edit .env with your API keys and settings
```

## Quick Start

### Basic Usage
```bash
# Translate a project
cstarx translate Input/01-Primary --output Output/01-Primary

# Check translation status
cstarx status

# Resume paused translation
cstarx resume Input/01-Primary
```

### DeepSeek API Configuration
```bash
# Environment variables
CSTARX_MODEL_PROVIDER=openai
CSTARX_MODEL_NAME=deepseek-chat
CSTARX_API_KEY=sk-d1c3ee0a9f304a368e15a67eae7db1c2
CSTARX_BASE_URL=https://api.deepseek.com
```

Available DeepSeek Models:
- `deepseek-chat`: Standard chat model (DeepSeek-V3.2-Exp non-reasoning mode)
- `deepseek-reasoner`: Reasoning model (DeepSeek-V3.2-Exp reasoning mode)

### Web Interface
```bash
# Start the API server
python -m src.api

# Start the frontend (in another terminal)
cd frontend
npm run dev
```

Visit `http://localhost:3000` to access the web interface.

### Python API
```python
from src import Translator, Config

# Create translator
config = Config()
translator = Translator(config)

# Translate project
project = await translator.translate_project("Input/01-Primary", "Output/01-Primary")
print(f"Translated {project.translated_files}/{project.total_files} files")
```

## Project Structure

```
cstarx/
├── src/                    # Core source code
│   ├── agents/            # Multi-agent system
│   ├── core/              # Core engines
│   ├── models/            # Data models
│   ├── utils/             # Utility functions
│   ├── api/               # Web API
│   ├── cli/               # CLI interface
│   └── mcp/               # MCP integration
├── frontend/              # React frontend
├── Input/                 # Test input projects
│   ├── 01-Primary/
│   └── 02-Medium/
├── Output/                # Translation output
├── tests/                 # Test code
└── docs/                  # Documentation
```

## Usage Examples

### Basic Translation
```python
import asyncio
from src import Translator, Config

async def main():
    config = Config()
    translator = Translator(config)
    
    # Translate a project
    project = await translator.translate_project("Input/01-Primary", "Output/01-Primary")
    
    # Check results
    print(f"Project: {project.name}")
    print(f"Files translated: {project.translated_files}")
    print(f"Success rate: {project.translated_files / project.total_files * 100:.1f}%")

asyncio.run(main())
```

### Custom Configuration
```python
from src import Config, ModelProvider, TranslationStrategy

# Create custom configuration
config = Config(
    model=ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="deepseek-chat",
        temperature=0.7,
        max_tokens=8192
    ),
    translation=TranslationConfig(
        strategy=TranslationStrategy.ADAPTIVE,
        max_parallel_workers=8,
        enable_quality_check=True
    )
)

translator = Translator(config)
```

## Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Server    │    │   Core Engine   │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (Python)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   State Store   │
                       │   (JSON/SQLite) │
                       └─────────────────┘
```

### Multi-Agent System

```
Project Manager
├── Project Initialization
├── Task Coordination
└── Progress Monitoring

Tech Leader
├── Code Analysis
├── Strategy Selection
└── Quality Assessment

Translator Agent
├── Code Translation
├── Error Handling
└── Result Generation

Quality Agent
├── Syntax Checking
├── Completeness Verification
└── Style Validation
```

## Configuration

### Environment Variables
```bash
# Model Configuration
CSTARX_MODEL_PROVIDER=openai
CSTARX_MODEL_NAME=deepseek-chat
CSTARX_API_KEY=your_api_key_here
CSTARX_BASE_URL=https://api.deepseek.com

# Translation Settings
CSTARX_MAX_PARALLEL_WORKERS=5
CSTARX_ENABLE_QUALITY_CHECK=true
CSTARX_ENABLE_MEMORY=true

# Output Settings
CSTARX_OUTPUT_DIR=./Output
CSTARX_PRESERVE_STRUCTURE=true
```

## Testing

### Run Tests
```bash
# Python tests
pytest tests/

# Frontend tests
cd frontend
npm test

# Integration tests
pytest tests/integration/
```

### Test Coverage
```bash
pytest --cov=src tests/
```

## Performance

### Benchmarks
- Small Project (< 10 files): ~30 seconds
- Medium Project (10-100 files): ~5 minutes
- Large Project (100+ files): ~30 minutes

### Optimization Features
- Parallel processing with configurable worker count
- Intelligent dependency ordering
- Incremental translation with state persistence
- Memory-efficient processing for large projects

## Contributing

We welcome contributions! Please see our Contributing Guide for details.

### Development Setup
```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run linting
flake8 src/
black src/
mypy src/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- Documentation: https://docs.cstarx.dev
- Issues: https://github.com/cstarx/cstarx-v2/issues
- Discussions: https://github.com/cstarx/cstarx-v2/discussions
- Email: support@cstarx.dev