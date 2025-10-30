"""
LLM-assisted compilation error fixing.

Features:
- Iterative error fixing with multiple attempts
- Context-aware error analysis
- Automatic code correction using LLM
"""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from loguru import logger
from datetime import datetime

from ..models.config import Config
from .compilation_verifier import CompilationError, CompilationVerifier


class ErrorFixer:
    """LLM-assisted error fixer"""
    
    def __init__(self, config: Config):
        self.config = config
        self.max_fix_attempts = 5
        self.max_errors_per_fix = 20  # Limit errors to avoid token overflow
    
    async def fix_compile_errors(
        self,
        code: str,
        errors: List[CompilationError],
        filepath: str,
        project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fix compilation errors using LLM
        
        Args:
            code: The Rust code with errors
            errors: List of CompilationError objects
            filepath: Path to the file being fixed
            project_context: Optional context about the project
        
        Returns:
            Dict with 'success', 'fixed_code', 'fixed_errors', 'attempts'
        """
        if not errors:
            return {
                "success": True,
                "fixed_code": code,
                "fixed_errors": [],
                "attempts": 0
            }
        
        # Limit number of errors to process
        errors_to_fix = errors[:self.max_errors_per_fix]
        if len(errors) > self.max_errors_per_fix:
            logger.warning(f"Limiting error fixing to {self.max_errors_per_fix} errors (total: {len(errors)})")
        
        # Prepare error information
        error_document = {}
        errors_list = []
        
        for error in errors_to_fix:
            # Collect error code explanations
            if error.code and error.code.get("code"):
                error_code = error.code["code"]
                if error_code not in error_document:
                    error_document[error_code] = error.code.get("explanation", "")
            
            errors_list.append({
                "rendered": error.rendered,
                "message": error.message,
                "file": error.get_file(),
                "line": error.get_line(),
                "code": error.code.get("code") if error.code else None
            })
        
        # Build error explanations
        explanations = []
        for error_code, explanation in error_document.items():
            explanations.append(f"## {error_code}\n{explanation}\n")
        
        error_text = "\n\n".join([err["rendered"] for err in errors_list])
        explanations_text = "\n".join(explanations) if explanations else ""
        
        # Attempt fixes
        fixed_code = code
        attempts = 0
        remaining_errors = errors_to_fix
        
        while attempts < self.max_fix_attempts and remaining_errors:
            attempts += 1
            logger.info(f"Fix attempt {attempts}/{self.max_fix_attempts} for {filepath}")
            
            # Call LLM to fix errors
            fixed_code = await self._request_fix(
                fixed_code,
                remaining_errors,
                explanations_text,
                filepath,
                project_context
            )
            
            # Verify the fix
            if project_context and "project_dir" in project_context:
                verifier = CompilationVerifier(project_context["project_dir"])
                check_result = await verifier.verify_file(filepath)
                
                if check_result["success"]:
                    logger.info(f"✓ Fix successful after {attempts} attempts")
                    return {
                        "success": True,
                        "fixed_code": fixed_code,
                        "fixed_errors": errors_to_fix,
                        "attempts": attempts
                    }
                else:
                    # Update remaining errors
                    remaining_errors = [
                        CompilationError(e) for e in check_result["errors"]
                        if self._is_relevant_error(e, filepath)
                    ]
                    logger.info(f"Still {len(remaining_errors)} errors remaining after fix attempt {attempts}")
            else:
                # If no project context, return after first attempt
                logger.warning("No project context for verification, returning fixed code")
                return {
                    "success": True,
                    "fixed_code": fixed_code,
                    "fixed_errors": errors_to_fix[:len(remaining_errors)],
                    "attempts": attempts
                }
        
        # Max attempts reached
        logger.warning(f"Failed to fix all errors after {attempts} attempts")
        return {
            "success": False,
            "fixed_code": fixed_code,
            "fixed_errors": remaining_errors,
            "attempts": attempts
        }
    
    async def _request_fix(
        self,
        code: str,
        errors: List[CompilationError],
        explanations: str,
        filepath: str,
        project_context: Optional[Dict[str, Any]]
    ) -> str:
        """Request LLM to fix compilation errors"""
        import openai
        
        client = openai.OpenAI(
            api_key=self.config.model.api_key,
            base_url=self.config.model.base_url
        )
        
        # Build system prompt
        system_prompt = """You are an expert Rust compiler error fixer. Your task is to analyze compilation errors and provide corrected code.

Guidelines:
1. Fix all reported compilation errors
2. Maintain code functionality and logic
3. Follow Rust best practices and idiomatic patterns
4. Preserve code structure and formatting
5. Provide complete corrected code, not just patches"""
        
        # Build user prompt
        errors_text = "\n\n".join([f"Error {i+1}:\n{e.rendered}" for i, e in enumerate(errors)])
        
        explanations_part = f'\nError code explanations:\n{explanations}' if explanations else ''
        context_part = f'\nProject context: {json.dumps(project_context, indent=2)}' if project_context else ''
        
        user_prompt = f"""Fix the following Rust code that has compilation errors.

File: {Path(filepath).name}

Current code:
```rust
{code}
```

Compilation errors:
{errors_text}{explanations_part}{context_part}

Please provide the complete corrected Rust code. Return ONLY the corrected code in a code block, no explanations."""
        
        try:
            # Use lower temperature for fixing (more deterministic)
            fix_temperature = 0.3
            
            logger.info(f"Requesting LLM fix: {len(errors)} errors, temperature={fix_temperature:.2f}")
            
            response = client.chat.completions.create(
                model=self.config.model.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=fix_temperature,
                max_tokens=self.config.model.max_tokens
            )
            
            content = response.choices[0].message.content
            
            # Extract code from response
            import re
            code_match = re.search(r'```rust\n?(.*?)\n?```', content, re.DOTALL)
            if code_match:
                fixed_code = code_match.group(1)
            else:
                # If no code block, try to extract code directly
                fixed_code = content.strip()
                # Remove markdown if present
                if fixed_code.startswith('```'):
                    fixed_code = re.sub(r'```rust?\n?', '', fixed_code)
                    fixed_code = re.sub(r'\n?```\n?$', '', fixed_code)
            
            logger.info(f"LLM fix response received: {len(fixed_code)} chars")
            logger.debug(f"Fixed code preview: {fixed_code[:200]}...")
            
            return fixed_code.strip()
        
        except Exception as e:
            logger.error(f"LLM error fix request failed: {e}", exc_info=True)
            # Return original code on error
            return code
    
    def _is_relevant_error(self, error_dict: Dict[str, Any], filepath: str) -> bool:
        """Check if error is relevant to the file being fixed"""
        error_file = error_dict.get("file", "")
        if not error_file:
            return True  # Include if file is unknown
        
        filepath_str = str(filepath)
        # Check if error file matches
        return filepath_str.endswith(error_file) or error_file.endswith(Path(filepath_str).name)

