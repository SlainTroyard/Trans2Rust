"""
Configuration management for CStarX v2.0
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import BaseModel, Field
from enum import Enum


class ModelProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    ZHIPU = "zhipu"
    DEEPSEEK = "deepseek"
    LOCAL = "local"


class TranslationStrategy(str, Enum):
    """Translation strategies"""
    SINGLE_PASS = "single_pass"
    MULTI_PASS = "multi_pass"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"


class ModelConfig(BaseModel):
    """Model configuration"""
    provider: ModelProvider = ModelProvider.OPENAI
    model_name: str = "gpt-4"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=8192, ge=1, le=32768)
    timeout: int = Field(default=60, ge=1, le=300)
    
    model_config = {"protected_namespaces": ()}


class DependencyConfig(BaseModel):
    """Dependency analysis configuration"""
    use_clang: bool = True
    clang_path: Optional[str] = None
    compile_commands_path: Optional[str] = None
    include_paths: List[str] = Field(default_factory=list)
    define_macros: List[str] = Field(default_factory=list)
    optimization_level: int = Field(default=0, ge=0, le=3)


class TranslationConfig(BaseModel):
    """Translation configuration"""
    strategy: TranslationStrategy = TranslationStrategy.ADAPTIVE
    max_parallel_workers: int = Field(default=5, ge=1, le=20)
    retry_attempts: int = Field(default=3, ge=0, le=10)
    enable_memory: bool = True
    enable_quality_check: bool = True
    enable_test_generation: bool = True


class OutputConfig(BaseModel):
    """Output configuration"""
    output_dir: Path = Path("./Output")
    preserve_structure: bool = True
    generate_tests: bool = True
    generate_docs: bool = False
    format_code: bool = True


class Config(BaseModel):
    """Main configuration class"""
    model: ModelConfig = Field(default_factory=ModelConfig)
    dependency: DependencyConfig = Field(default_factory=DependencyConfig)
    translation: TranslationConfig = Field(default_factory=TranslationConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    
    # Project specific settings
    project_name: Optional[str] = None
    project_path: Optional[Path] = None
    target_language: str = "rust"
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[Path] = None
    
    # Development mode
    dev_mode: bool = False
    debug: bool = False
    
    class Config:
        env_prefix = "CSTARX_"
        case_sensitive = False

    def save(self, path: Path) -> None:
        """Save configuration to file"""
        with open(path, 'w') as f:
            f.write(self.model_dump_json(indent=2))
    
    @classmethod
    def load(cls, path: Path) -> "Config":
        """Load configuration from file"""
        with open(path, 'r') as f:
            data = f.read()
        return cls.model_validate_json(data)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        import os
        
        # Try to load .env file if it exists
        env_path = Path(".env")
        if env_path.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_path)
            except ImportError:
                # If dotenv is not available, manually parse .env file
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            os.environ.setdefault(key, value)
        
        config = cls()
        
        # Load model configuration
        if os.getenv("CSTARX_MODEL_PROVIDER"):
            try:
                config.model.provider = ModelProvider(os.getenv("CSTARX_MODEL_PROVIDER").lower())
            except ValueError:
                pass
        
        if os.getenv("CSTARX_MODEL_NAME"):
            config.model.model_name = os.getenv("CSTARX_MODEL_NAME")
        
        if os.getenv("CSTARX_API_KEY"):
            config.model.api_key = os.getenv("CSTARX_API_KEY")
        
        if os.getenv("CSTARX_BASE_URL"):
            config.model.base_url = os.getenv("CSTARX_BASE_URL")
        
        if os.getenv("CSTARX_TEMPERATURE"):
            try:
                config.model.temperature = float(os.getenv("CSTARX_TEMPERATURE"))
            except ValueError:
                pass
        
        if os.getenv("CSTARX_MAX_TOKENS"):
            try:
                config.model.max_tokens = int(os.getenv("CSTARX_MAX_TOKENS"))
            except ValueError:
                pass
        
        if os.getenv("CSTARX_OUTPUT_DIR"):
            config.output.output_dir = Path(os.getenv("CSTARX_OUTPUT_DIR"))
        
        # Load logging configuration
        if os.getenv("CSTARX_LOG_LEVEL"):
            config.log_level = os.getenv("CSTARX_LOG_LEVEL")
        
        if os.getenv("CSTARX_LOG_FILE"):
            config.log_file = Path(os.getenv("CSTARX_LOG_FILE"))
        
        return config
