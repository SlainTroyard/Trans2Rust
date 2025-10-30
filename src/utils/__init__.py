"""
Utility functions for CStarX v2.0
"""

import os
import hashlib
import shutil
from typing import List, Optional, Dict, Any
from pathlib import Path
from loguru import logger


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def find_files_by_extension(directory: Path, extensions: List[str]) -> List[Path]:
    """Find files with specific extensions in a directory"""
    files = []
    for ext in extensions:
        files.extend(directory.rglob(f"*{ext}"))
    return sorted(files)


def create_directory_structure(base_path: Path, structure: Dict[str, Any]) -> None:
    """Create directory structure from a dictionary"""
    for name, content in structure.items():
        path = base_path / name
        if isinstance(content, dict):
            path.mkdir(parents=True, exist_ok=True)
            create_directory_structure(path, content)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                f.write(content)


def copy_project_structure(source: Path, destination: Path) -> None:
    """Copy project structure preserving directory layout"""
    for item in source.rglob('*'):
        if item.is_file():
            relative_path = item.relative_to(source)
            dest_path = destination / relative_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest_path)


def clean_directory(directory: Path, keep_files: Optional[List[str]] = None) -> None:
    """Clean directory contents, optionally keeping specific files"""
    if not directory.exists():
        return
    
    keep_files = keep_files or []
    
    for item in directory.iterdir():
        if item.name in keep_files:
            continue
        
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)


def get_project_info(project_path: Path) -> Dict[str, Any]:
    """Get basic information about a project"""
    info = {
        'path': str(project_path),
        'name': project_path.name,
        'exists': project_path.exists(),
        'is_directory': project_path.is_dir(),
        'size': 0,
        'file_count': 0,
        'directories': []
    }
    
    if project_path.exists() and project_path.is_dir():
        total_size = 0
        file_count = 0
        
        for item in project_path.rglob('*'):
            if item.is_file():
                total_size += item.stat().st_size
                file_count += 1
            elif item.is_dir():
                info['directories'].append(str(item.relative_to(project_path)))
        
        info['size'] = total_size
        info['file_count'] = file_count
    
    return info


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def validate_project_path(project_path: str) -> Path:
    """Validate and return project path"""
    path = Path(project_path)
    
    if not path.exists():
        raise ValueError(f"Project path does not exist: {project_path}")
    
    if not path.is_dir():
        raise ValueError(f"Project path is not a directory: {project_path}")
    
    return path


def find_cmake_files(project_path: Path) -> List[Path]:
    """Find CMakeLists.txt files in project"""
    return list(project_path.rglob("CMakeLists.txt"))


def find_makefiles(project_path: Path) -> List[Path]:
    """Find Makefile files in project"""
    makefile_names = ["Makefile", "makefile", "GNUmakefile"]
    makefiles = []
    
    for name in makefile_names:
        makefiles.extend(project_path.rglob(name))
    
    return makefiles


def detect_build_system(project_path: Path) -> Optional[str]:
    """Detect the build system used by the project"""
    if find_cmake_files(project_path):
        return "cmake"
    elif find_makefiles(project_path):
        return "make"
    elif (project_path / "Cargo.toml").exists():
        return "cargo"
    elif (project_path / "package.json").exists():
        return "npm"
    else:
        return None


def get_compiler_info() -> Dict[str, str]:
    """Get information about available compilers"""
    compilers = {
        'gcc': 'gcc --version',
        'clang': 'clang --version',
        'clang++': 'clang++ --version',
        'g++': 'g++ --version'
    }
    
    info = {}
    for compiler, command in compilers.items():
        try:
            result = os.popen(command).read().strip()
            info[compiler] = result.split('\n')[0] if result else "Not found"
        except:
            info[compiler] = "Not found"
    
    return info


def setup_logging(log_level: str = "INFO", log_file: Optional[Path] = None) -> None:
    """Setup logging configuration"""
    from loguru import logger
    
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Add file handler if specified
    if log_file:
        logger.add(
            sink=str(log_file),
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="7 days"
        )
