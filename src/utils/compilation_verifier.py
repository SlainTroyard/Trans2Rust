"""
Advanced compilation verification with detailed error analysis.

Features:
- JSON-based error parsing from cargo check
- Module-level and file-level verification
- Detailed error information extraction
- Context-aware compilation checking
"""

import asyncio
import json
import subprocess
from typing import Dict, List, Optional, Any
from pathlib import Path
from loguru import logger


class CompilationError:
    """Detailed compilation error information"""
    
    def __init__(self, data: Dict[str, Any]):
        self.rendered = data.get("rendered", "")
        self.message = data.get("message", "")
        self.code = data.get("code")
        self.level = data.get("level", "error")
        self.spans = data.get("spans", [])
        self.message_type = data.get("message_type")
        self.children = data.get("children", [])
    
    def get_file(self) -> Optional[str]:
        """Get the file path from spans"""
        if self.spans:
            return self.spans[0].get("file_name")
        return None
    
    def get_line(self) -> Optional[int]:
        """Get the line number from spans"""
        if self.spans:
            return self.spans[0].get("line_start")
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "rendered": self.rendered,
            "message": self.message,
            "code": self.code,
            "level": self.level,
            "file": self.get_file(),
            "line": self.get_line(),
            "spans": self.spans
        }


class CompilationVerifier:
    """Advanced compilation verifier with detailed error analysis"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir).resolve()
    
    async def cargo_check(
        self,
        filepaths: Optional[List[str]] = None,
        ignore_codes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run cargo check with detailed JSON error parsing
        
        Args:
            filepaths: Optional list of file paths to filter errors for
            ignore_codes: Optional list of error codes to ignore
        
        Returns:
            Dict with 'success', 'errors', 'warnings', 'output'
        """
        ignore_codes = ignore_codes or []
        filepaths = filepaths or []
        
        # Convert to relative paths if needed
        if filepaths:
            filepaths = [
                str(Path(f).relative_to(self.project_dir)) if Path(f).is_absolute() else f
                for f in filepaths
            ]
        
        cargo_check_command = ["cargo", "check", "--message-format", "json"]
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cargo_check_command,
                cwd=self.project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Add timeout to prevent hanging (60 seconds for cargo check)
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=60.0
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                logger.warning(f"cargo check timed out after 60 seconds in {self.project_dir}")
                return {
                    "success": False,
                    "errors": [{"message": "cargo check timeout (60s) - compilation may be hanging"}],
                    "warnings": [],
                    "output": "",
                    "error_count": 1,
                    "warning_count": 0,
                    "timeout": True
                }
            output_lines = stdout.decode('utf-8', errors='ignore').split('\n')
            stderr_output = stderr.decode('utf-8', errors='ignore')
            
            compile_errors = []
            warnings = []
            
            for output_line in output_lines:
                if not output_line.strip():
                    continue
                
                try:
                    cargo_output = json.loads(output_line)
                    
                    if cargo_output.get("reason") != "compiler-message":
                        continue
                    
                    compiler_message = cargo_output.get("message", {})
                    level = compiler_message.get("level", "")
                    
                    # Filter by error level
                    if level not in ["error", "warning"]:
                        continue
                    
                    # Filter by ignore codes
                    error_code = compiler_message.get("code")
                    if error_code and error_code.get("code") in ignore_codes:
                        continue
                    
                    # Filter by filepaths if specified
                    if filepaths:
                        spans = compiler_message.get("spans", [])
                        is_relevant = False
                        for span in spans:
                            file_name = span.get("file_name", "")
                            # Check if this file is in our target list
                            for target_file in filepaths:
                                if target_file in file_name or file_name.endswith(target_file):
                                    is_relevant = True
                                    break
                            if is_relevant:
                                break
                        
                        if not is_relevant:
                            continue
                    
                    # Extract error information
                    error_data = {
                        "rendered": compiler_message.get("rendered", ""),
                        "message_type": compiler_message.get("$message_type"),
                        "children": compiler_message.get("children", []),
                        "code": error_code,
                        "level": level,
                        "message": compiler_message.get("message", ""),
                        "spans": compiler_message.get("spans", [])
                    }
                    
                    error_obj = CompilationError(error_data)
                    
                    if level == "error":
                        compile_errors.append(error_obj)
                    elif level == "warning":
                        warnings.append(error_obj)
                
                except (json.JSONDecodeError, KeyError) as e:
                    logger.debug(f"Failed to parse cargo output line: {e}")
                    continue
            
            result = {
                "success": len(compile_errors) == 0,
                "errors": [e.to_dict() for e in compile_errors],
                "warnings": [w.to_dict() for w in warnings],
                "output": stderr_output,
                "error_count": len(compile_errors),
                "warning_count": len(warnings)
            }
            
            return result
        
        except FileNotFoundError:
            logger.error("cargo not found, cannot verify compilation")
            return {
                "success": False,
                "errors": [{"message": "cargo not found"}],
                "warnings": [],
                "output": "",
                "error_count": 1,
                "warning_count": 0
            }
        except Exception as e:
            logger.error(f"Compilation check failed: {e}", exc_info=True)
            return {
                "success": False,
                "errors": [{"message": str(e)}],
                "warnings": [],
                "output": "",
                "error_count": 1,
                "warning_count": 0
            }
    
    async def verify_file(self, filepath: str) -> Dict[str, Any]:
        """Verify a specific file compiles in project context"""
        relative_path = Path(filepath).relative_to(self.project_dir) if Path(filepath).is_absolute() else filepath
        return await self.cargo_check(filepaths=[str(relative_path)])
    
    async def verify_module(self, module_path: Path) -> Dict[str, Any]:
        """Verify a module compiles independently"""
        module_path = Path(module_path).resolve()
        
        if not (module_path / "Cargo.toml").exists():
            return {
                "success": False,
                "errors": [{"message": f"No Cargo.toml found in {module_path}"}],
                "warnings": [],
                "output": "",
                "error_count": 1,
                "warning_count": 0
            }
        
        # Create verifier for module
        module_verifier = CompilationVerifier(module_path)
        return await module_verifier.cargo_check()
    
    async def cargo_test(self, timeout: int = 120) -> Dict[str, Any]:
        """Run cargo test with timeout"""
        cargo_test_command = ["cargo", "test", "--message-format", "json"]
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cargo_test_command,
                cwd=self.project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                return {
                    "success": False,
                    "errors": [{"message": f"Test timeout after {timeout}s"}],
                    "output": "",
                    "timeout": True
                }
            
            output_lines = stdout.decode('utf-8', errors='ignore').split('\n')
            stderr_output = stderr.decode('utf-8', errors='ignore')
            
            test_errors = []
            for line in output_lines:
                if not line.strip():
                    continue
                try:
                    msg = json.loads(line)
                    if msg.get("reason") == "compiler-message":
                        error_msg = msg.get("message", {})
                        if error_msg.get("level") == "error":
                            test_errors.append({
                                "message": error_msg.get("message", ""),
                                "rendered": error_msg.get("rendered", "")
                            })
                except:
                    pass
            
            return {
                "success": proc.returncode == 0 and len(test_errors) == 0,
                "errors": test_errors,
                "output": stderr_output,
                "timeout": False
            }
        
        except Exception as e:
            logger.error(f"Cargo test failed: {e}", exc_info=True)
            return {
                "success": False,
                "errors": [{"message": str(e)}],
                "output": "",
                "timeout": False
            }

