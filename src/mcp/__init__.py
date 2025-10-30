"""
MCP (Model Context Protocol) integration module for enhanced LLM interactions
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from loguru import logger

from ..models.config import Config
from ..models.project import TranslationUnit, Project


@dataclass
class MCPTool:
    """Represents an MCP tool"""
    name: str
    description: str
    parameters: Dict[str, Any]
    returns: Dict[str, Any]


@dataclass
class MCPContext:
    """Represents MCP context"""
    files: List[str]
    dependencies: List[str]
    compilation_context: Dict[str, Any]
    translation_history: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class MCPClient:
    """MCP client for tool-assisted translation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.tools: Dict[str, MCPTool] = {}
        self.contexts: Dict[str, MCPContext] = {}
        self._register_tools()
    
    def _register_tools(self):
        """Register available MCP tools"""
        self.tools = {
            "read_file": MCPTool(
                name="read_file",
                description="Read contents of a source file",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path to read"}
                    },
                    "required": ["path"]
                },
                returns={"type": "string", "description": "File contents"}
            ),
            "write_file": MCPTool(
                name="write_file",
                description="Write contents to a file",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path to write"},
                        "content": {"type": "string", "description": "Content to write"}
                    },
                    "required": ["path", "content"]
                },
                returns={"type": "boolean", "description": "Success status"}
            ),
            "compile_check": MCPTool(
                name="compile_check",
                description="Check if Rust code compiles",
                parameters={
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Rust code to check"},
                        "dependencies": {"type": "array", "description": "Required dependencies"}
                    },
                    "required": ["code"]
                },
                returns={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "errors": {"type": "array"},
                        "warnings": {"type": "array"}
                    }
                }
            ),
            "analyze_dependencies": MCPTool(
                name="analyze_dependencies",
                description="Analyze dependencies in code",
                parameters={
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code to analyze"},
                        "language": {"type": "string", "description": "Programming language"}
                    },
                    "required": ["code", "language"]
                },
                returns={
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of dependencies"
                }
            ),
            "suggest_translation": MCPTool(
                name="suggest_translation",
                description="Suggest translation for code snippet",
                parameters={
                    "type": "object",
                    "properties": {
                        "source_code": {"type": "string"},
                        "source_lang": {"type": "string"},
                        "target_lang": {"type": "string"},
                        "context": {"type": "object"}
                    },
                    "required": ["source_code", "source_lang", "target_lang"]
                },
                returns={
                    "type": "object",
                    "properties": {
                        "translated_code": {"type": "string"},
                        "confidence": {"type": "number"},
                        "suggestions": {"type": "array"}
                    }
                }
            )
        }
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Call an MCP tool"""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        tool = self.tools[tool_name]
        logger.info(f"Calling MCP tool: {tool_name}")
        
        # Dispatch to appropriate tool implementation
        if tool_name == "read_file":
            return await self._read_file(parameters["path"])
        elif tool_name == "write_file":
            return await self._write_file(parameters["path"], parameters["content"])
        elif tool_name == "compile_check":
            return await self._compile_check(
                parameters.get("code", ""),
                parameters.get("dependencies", []),
                project_dir=parameters.get("project_dir"),
                filepath=parameters.get("filepath")
            )
        elif tool_name == "analyze_dependencies":
            return await self._analyze_dependencies(parameters["code"], parameters["language"])
        elif tool_name == "suggest_translation":
            return await self._suggest_translation(
                parameters["source_code"],
                parameters["source_lang"],
                parameters["target_lang"],
                parameters.get("context", {}),
                parameters.get("temperature")
            )
        else:
            raise ValueError(f"Tool {tool_name} not implemented")
    
    async def _read_file(self, path: str) -> str:
        """Read file contents"""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    async def _write_file(self, path: str, content: str) -> bool:
        """Write file contents"""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    
    async def _compile_check(self, code: str, dependencies: List[str], project_dir: Optional[str] = None, filepath: Optional[str] = None) -> Dict[str, Any]:
        """Check if Rust code compiles - enhanced with project context verification
        
        Args:
            code: Rust code to check
            dependencies: List of dependencies
            project_dir: Optional actual project directory for context-aware checking
            filepath: Optional path to the file being checked
        """
        # If project_dir is provided, use real project context for accurate verification
        if project_dir:
            from ..utils.compilation_verifier import CompilationVerifier
            verifier = CompilationVerifier(Path(project_dir))
            
            if filepath:
                result = await verifier.verify_file(filepath)
            else:
                # Check entire project
                result = await verifier.cargo_check()
            
            return result
        
        # Fallback: temporary directory check (legacy behavior)
        import tempfile
        
        result = {
            "success": False,
            "errors": [],
            "warnings": []
        }
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                cargo_toml = f"""[package]
name = "temp_check"
version = "0.1.0"
edition = "2021"

[dependencies]
"""
                for dep in dependencies:
                    cargo_toml += f'{dep} = "*"\n'
                
                (Path(tmpdir) / "Cargo.toml").write_text(cargo_toml)
                (Path(tmpdir) / "src").mkdir(exist_ok=True)
                (Path(tmpdir) / "src" / "main.rs").write_text(code)
                
                proc = await asyncio.create_subprocess_exec(
                    "cargo", "check", "--message-format", "json",
                    cwd=tmpdir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await proc.communicate()
                
                # Parse JSON output for detailed errors
                errors = []
                for line in stdout.decode('utf-8', errors='ignore').split('\n'):
                    if line.strip():
                        try:
                            msg = json.loads(line)
                            if msg.get("reason") == "compiler-message":
                                error_msg = msg.get("message", {})
                                if error_msg.get("level") == "error":
                                    errors.append({
                                        "message": error_msg.get("message", ""),
                                        "code": error_msg.get("code"),
                                        "rendered": error_msg.get("rendered", ""),
                                        "spans": error_msg.get("spans", [])
                                    })
                        except:
                            pass
                
                if proc.returncode == 0:
                    result["success"] = True
                else:
                    result["errors"] = errors if errors else [{"message": stderr.decode('utf-8', errors='ignore')}]
        
        except Exception as e:
            result["errors"] = [{"message": str(e)}]
        
        return result
    
    async def _analyze_dependencies(self, code: str, language: str) -> List[str]:
        """Analyze dependencies in code"""
        dependencies = []
        
        if language == "rust":
            # Extract use statements
            import re
            use_pattern = r'use\s+([\w:]+)'
            matches = re.findall(use_pattern, code)
            dependencies = [m.replace('::', '/') for m in matches]
        
        elif language in ["c", "cpp"]:
            # Extract include statements
            import re
            include_pattern = r'#include\s*[<"]([^>"]+)[>"]'
            matches = re.findall(include_pattern, code)
            dependencies = matches
        
        return dependencies
    
    async def _suggest_translation(self, source_code: str, source_lang: str, target_lang: str, context: Dict[str, Any], temperature: Optional[float] = None) -> Dict[str, Any]:
        """Suggest translation using LLM with MCP context"""
        import openai
        
        client = openai.OpenAI(
            api_key=self.config.model.api_key,
            base_url=self.config.model.base_url
        )
        
        # Build enhanced prompt with MCP context
        system_prompt = """You are an expert code translator specializing in C/C++ to Rust translation.
Use the provided MCP tools to:
1. Analyze code structure and dependencies
2. Check compilation errors
3. Suggest idiomatic Rust translations

Always prioritize:
- Memory safety
- Performance
- Idiomatic Rust patterns
- Correctness"""
        
        user_prompt = f"""Translate the following {source_lang} code to {target_lang}:

```{source_lang}
{source_code}
```

Context: {json.dumps(context, indent=2)}

Provide:
1. Complete translated code in Rust
2. Translation confidence (0-1)
3. Any suggestions or notes about the translation"""
        
        try:
            use_temp = temperature if temperature is not None else self.config.model.temperature
            
            # Log API request details (to file and console)
            logger.info(f"LLM API Request: model={self.config.model.model_name}, temperature={use_temp:.2f}, "
                       f"max_tokens={self.config.model.max_tokens}, base_url={self.config.model.base_url}")
            # Log truncated version for console readability
            logger.debug(f"LLM Request Prompt (first 500 chars): {user_prompt[:500]}...")
            # Log full prompt to file (INFO level so it's always saved)
            logger.info(f"LLM Full Request Prompt: {user_prompt}")
            logger.info(f"LLM System Prompt: {system_prompt}")
            
            # Make API call (note: top_p is removed, using OpenAI SDK default)
            response = client.chat.completions.create(
                model=self.config.model.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=use_temp,
                max_tokens=self.config.model.max_tokens
            )
            
            # Log API response details
            usage_info = response.usage.model_dump() if hasattr(response, 'usage') and response.usage else 'N/A'
            finish_reason = response.choices[0].finish_reason if response.choices else 'N/A'
            logger.info(f"LLM API Response: model={response.model}, "
                       f"usage={usage_info}, finish_reason={finish_reason}")
            
            content = response.choices[0].message.content
            
            # Log response content (truncated for readability in console)
            response_preview = content[:300] + "..." if len(content) > 300 else content
            logger.debug(f"LLM Response (first 300 chars): {response_preview}")
            
            # Log full response to file (not truncated)
            logger.debug(f"LLM Full Response: {content}")
            
            # Parse response
            import re
            code_match = re.search(r'```rust\n?(.*?)\n?```', content, re.DOTALL)
            translated_code = code_match.group(1) if code_match else ""
            
            confidence_match = re.search(r'confidence[:\s]+([\d.]+)', content, re.IGNORECASE)
            confidence = float(confidence_match.group(1)) if confidence_match else 0.5
            
            # Log translation result
            logger.info(f"Translation parsed: confidence={confidence:.2f}, "
                       f"code_length={len(translated_code)} chars, "
                       f"found_code_block={bool(code_match)}")
            
            # Store full conversation for later retrieval
            conversation_entry = {
                "timestamp": datetime.now().isoformat(),
                "temperature": use_temp,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response": content,
                "usage": usage_info,
                "finish_reason": finish_reason
            }
            
            return {
                "translated_code": translated_code,
                "confidence": confidence,
                "suggestions": content.split('\n')[-5:],  # Last 5 lines as suggestions
                "conversation": conversation_entry  # Full conversation history
            }
        
        except Exception as e:
            logger.error(f"LLM API call failed: {e}", exc_info=True)
            logger.error(f"API Error Details: model={self.config.model.model_name}, "
                        f"temperature={use_temp if 'use_temp' in locals() else 'N/A'}, "
                        f"base_url={self.config.model.base_url}")
            return {
                "translated_code": "",
                "confidence": 0.0,
                "suggestions": [f"Error: {str(e)}"]
            }
    
    def create_context(self, project: Project, unit: TranslationUnit) -> MCPContext:
        """Create MCP context for a translation unit"""
        context = MCPContext(
            files=[str(unit.path)],
            dependencies=[dep.target for dep in unit.dependencies],
            compilation_context={
                "language": "c" if unit.path.suffix in [".c", ".h"] else "cpp",
                "standard": "c17" if unit.path.suffix == ".c" else "c++17"
            },
            translation_history=[],
            metadata={
                "complexity": unit.complexity_score,
                "size": unit.size,
                "type": unit.type.value
            }
        )
        
        self.contexts[unit.id] = context
        return context
    
    def get_context(self, unit_id: str) -> Optional[MCPContext]:
        """Get MCP context for a unit"""
        return self.contexts.get(unit_id)
    
    def update_context(self, unit_id: str, updates: Dict[str, Any]) -> None:
        """Update MCP context"""
        if unit_id in self.contexts:
            context = self.contexts[unit_id]
            for key, value in updates.items():
                setattr(context, key, value)


class MCPTranslator:
    """MCP-enhanced translator"""
    
    def __init__(self, mcp_client: MCPClient, config: Config):
        self.mcp_client = mcp_client
        self.config = config
    
    async def translate_with_mcp(self, unit: TranslationUnit, project: Project, temperature: Optional[float] = None) -> Dict[str, Any]:
        """Translate using MCP tools for enhanced accuracy"""
        # Create context
        context = self.mcp_client.create_context(project, unit)
        
        # Read source code
        source_code = await self.mcp_client.call_tool("read_file", {"path": str(unit.path)})
        
        # Analyze dependencies
        deps = await self.mcp_client.call_tool(
            "analyze_dependencies",
            {
                "code": source_code,
                "language": "cpp" if unit.path.suffix in [".cpp", ".hpp"] else "c"
            }
        )
        
        # Get translation suggestion with dynamic temperature
        use_temp = temperature if temperature is not None else self.config.model.temperature
        suggestion = await self.mcp_client.call_tool(
            "suggest_translation",
            {
                "source_code": source_code,
                "source_lang": "cpp" if unit.path.suffix in [".cpp", ".hpp"] else "c",
                "target_lang": "rust",
                "context": asdict(context),
                "temperature": use_temp
            }
        )
        
        translated_code = suggestion.get("translated_code", "")
        confidence = suggestion.get("confidence", 0.5)
        conversation = suggestion.get("conversation")
        
            # Enhanced compilation check: use actual project context when available for accurate verification
        project_output_dir = Path(self.config.output.output_dir) / project.name
        
        # Write file temporarily for context-aware compilation check
        rust_file_path = None
        try:
            relative_path = unit.path.relative_to(project.path)
        except ValueError:
            relative_path = Path(unit.path.name)
        
        if confidence > 0.7 and translated_code:
            # High confidence, verify compilation in actual project context
            try:
                rust_file_path = project_output_dir / relative_path.with_suffix('.rs')
                rust_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write file for context-aware compilation
                rust_file_path.write_text(translated_code)
                
                # Check compilation in actual project directory for context-aware verification
                compile_result = await self.mcp_client.call_tool(
                    "compile_check",
                    {
                        "code": translated_code,
                        "dependencies": deps,
                        "project_dir": str(project_output_dir),
                        "filepath": str(rust_file_path)
                    }
                )
                
                if not compile_result.get("success", True):
                    error_count = compile_result.get("error_count", len(compile_result.get("errors", [])))
                    # Reduce confidence based on error count
                    confidence_reduction = min(0.4, 0.1 * error_count)
                    confidence = max(0.3, confidence - confidence_reduction)
                    logger.warning(f"Compilation check failed for {unit.name}: {error_count} errors, confidence adjusted to {confidence:.2f}")
                    
                    # Log first few errors
                    errors = compile_result.get("errors", [])
                    for i, err in enumerate(errors[:3], 1):
                        logger.debug(f"  Error {i}: {err.get('message', '')[:100]}")
            except Exception as e:
                logger.debug(f"Compilation check skipped: {e}")
        
        if not translated_code:
            # Fallback translation
            logger.warning(f"Translation failed for {unit.name}, using fallback")
            translated_code = f"// Translated from {unit.name}\n// Translation failed with temperature {use_temp:.2f}\n"
            confidence = 0.1
            conversation = None
        
        # Return dict format with conversation history
        return {
            'translated_code': translated_code,
            'confidence': confidence,
            'conversation': conversation
        }
