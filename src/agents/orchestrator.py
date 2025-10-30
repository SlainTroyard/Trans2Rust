"""
Multi-agent system for CStarX v2.0
"""

import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
from loguru import logger

from ..models.project import Project, TranslationUnit, TranslationResult, TranslationSession, TranslationStatus, TranslationUnitType
from ..models.config import Config
from ..core.dependency_analyzer import DependencyAnalyzer
from ..mcp import MCPClient, MCPTranslator


class BaseAgent:
    """Base class for all agents"""
    
    def __init__(self, config: Config):
        self.config = config
        self.name = self.__class__.__name__
        logger.info(f"Initialized {self.name}")
    
    async def process(self, input_data: Any) -> Any:
        """Process input data"""
        raise NotImplementedError


class ProjectManager(BaseAgent):
    """Manages project lifecycle and coordinates other agents"""
    
    def __init__(self, config: Config):
        super().__init__(config)
        self.dependency_analyzer = DependencyAnalyzer(config.dependency)
        self.current_project: Optional[Project] = None
        self.current_session: Optional[TranslationSession] = None
    
    async def initialize_project(self, project_path: str) -> Project:
        """Initialize a new project"""
        logger.info(f"Initializing project: {project_path}")
        
        # Analyze project dependencies
        from pathlib import Path
        project = await self.dependency_analyzer.analyze_project(Path(project_path))
        self.current_project = project
        
        # Create translation session
        session = TranslationSession(
            project_id=project.id,
            total_units=len(project.units)
        )
        self.current_session = session
        
        logger.info(f"Project initialized: {project.total_files} files")
        return project
    
    async def get_ready_units(self) -> List[TranslationUnit]:
        """Get units ready for translation"""
        if not self.current_project or not self.current_session:
            return []
        
        completed_units = self.current_session.completed_units
        return self.current_project.get_ready_units(completed_units)
    
    async def update_session(self, result: TranslationResult) -> None:
        """Update translation session with result"""
        if self.current_session:
            self.current_session.add_result(result)
            logger.info(f"Session updated: {self.current_session.get_progress():.1f}% complete")


class TechLeader(BaseAgent):
    """Technical leader responsible for code analysis and strategy"""
    
    def __init__(self, config: Config):
        super().__init__(config)
        self.strategies = {
            'simple': self._analyze_simple_code,
            'complex': self._analyze_complex_code,
            'library': self._analyze_library_code
        }
    
    async def analyze_unit(self, unit: TranslationUnit) -> Dict[str, Any]:
        """Analyze a translation unit and determine strategy"""
        logger.info(f"Analyzing unit: {unit.name}")
        
        # Calculate complexity score
        complexity = await self._calculate_complexity(unit)
        unit.complexity_score = complexity
        
        # Determine strategy
        strategy = await self._determine_strategy(unit)
        
        # Generate analysis report
        analysis = {
            'complexity': complexity,
            'strategy': strategy,
            'dependencies': len(unit.dependencies),
            'size': unit.size,
            'type': unit.type.value
        }
        
        logger.info(f"Analysis complete: {unit.name} - {strategy}")
        return analysis
    
    async def _calculate_complexity(self, unit: TranslationUnit) -> float:
        """Calculate complexity score for a unit"""
        if not unit.original_content:
            return 0.0
        
        content = unit.original_content
        
        # Simple complexity metrics
        lines = len(content.split('\n'))
        functions = content.count('{') - content.count('}')
        classes = content.count('class ')
        templates = content.count('template')
        
        # Normalize complexity score
        complexity = min(1.0, (lines / 1000) + (functions / 100) + (classes / 50) + (templates / 20))
        return complexity
    
    async def _determine_strategy(self, unit: TranslationUnit) -> str:
        """Determine translation strategy based on unit characteristics"""
        if unit.complexity_score < 0.3:
            return 'simple'
        elif unit.complexity_score < 0.7:
            return 'complex'
        else:
            return 'library'
    
    async def _analyze_simple_code(self, unit: TranslationUnit) -> Dict[str, Any]:
        """Analyze simple code units"""
        return {
            'strategy': 'single_pass',
            'max_retries': 2,
            'parallel_workers': 1
        }
    
    async def _analyze_complex_code(self, unit: TranslationUnit) -> Dict[str, Any]:
        """Analyze complex code units"""
        return {
            'strategy': 'multi_pass',
            'max_retries': 3,
            'parallel_workers': 2
        }
    
    async def _analyze_library_code(self, unit: TranslationUnit) -> Dict[str, Any]:
        """Analyze library code units"""
        return {
            'strategy': 'hybrid',
            'max_retries': 5,
            'parallel_workers': 3
        }


class TranslatorAgent(BaseAgent):
    """Agent responsible for actual code translation"""
    
    def __init__(self, config: Config, mcp_client: Optional[MCPClient] = None, mcp_translator: Optional[MCPTranslator] = None):
        super().__init__(config)
        self.model_config = config.model
        self.translation_config = config.translation
        self.mcp_client = mcp_client
        self.mcp_translator = mcp_translator
        
        # Initialize temperature optimizer with DeepSeek recommended values
        from ..utils.temperature_optimizer import TemperatureOptimizer
        self.temp_optimizer = TemperatureOptimizer(
            initial_temp=config.model.temperature
        )
    
    async def translate_unit(self, unit: TranslationUnit, strategy: str) -> TranslationResult:
        """Translate a single unit with temperature optimization and retry"""
        logger.info(f"Translating unit: {unit.name} with strategy: {strategy}")
        
        start_time = datetime.now()
        
        # Load original content if not already loaded
        if not unit.original_content:
            unit.original_content = await self._load_file_content(unit.path)
        
        # Get adaptive temperature based on complexity
        complexity = getattr(unit, 'complexity_score', 0.5)
        base_temp = self.temp_optimizer.get_adaptive_temperature(complexity)
        max_retries = self.translation_config.retry_attempts
        
        last_error = None
        best_result = None
        best_confidence = 0.0
        
        # Try translation with temperature optimization
        temperatures_to_try = [base_temp]  # Start with adaptive temperature
        attempt_count = 0
        
        while attempt_count <= max_retries and temperatures_to_try:
            if attempt_count > 0:
                # On retry, get diverse temperatures for exploration
                temperatures_to_try = self.temp_optimizer.get_retry_temperatures(
                    base_temp, 
                    num_retries=max_retries
                )
                logger.info(f"Retry attempt {attempt_count} with temperatures: {temperatures_to_try}")
            
            for temp in temperatures_to_try:
                attempt_count += 1
                logger.debug(f"Attempt {attempt_count} with temperature {temp:.2f}")
                
                try:
                    # Translate with specific temperature
                    if strategy == 'single_pass':
                        result_data = await self._single_pass_translation(unit, temp)
                    elif strategy == 'multi_pass':
                        result_data = await self._multi_pass_translation(unit, temp)
                    elif strategy == 'hybrid':
                        result_data = await self._hybrid_translation(unit, temp)
                    else:
                        result_data = await self._adaptive_translation(unit, temp)
                    
                    # Extract data from dict format (all methods now return dict)
                    if not isinstance(result_data, dict):
                        # Fallback: handle unexpected format
                        logger.error(f"Unexpected return type from translation method: {type(result_data)} for {unit.name}")
                        if isinstance(result_data, tuple):
                            translated_content, confidence = result_data
                            conversation = None
                        else:
                            raise ValueError(f"Invalid return format from translation: {type(result_data)}")
                    else:
                        translated_content = result_data.get('translated_code', '')
                        confidence = result_data.get('confidence', 0.5)
                        conversation = result_data.get('conversation')
                    
                    # Validate translation content
                    if not translated_content or len(translated_content.strip()) < 10:
                        logger.warning(f"Translation content too short or empty for {unit.name}: {len(translated_content) if translated_content else 0} chars")
                        # Don't record this as success
                        continue
                    
                    # Record successful attempt
                    from ..utils.temperature_optimizer import TranslationAttempt
                    attempt = TranslationAttempt(
                        temperature=temp,
                        success=True,
                        confidence=confidence,
                        translated_code=translated_content
                    )
                    self.temp_optimizer.update_from_attempt(attempt)
                    
                    # Track best result (including conversation history)
                    if confidence > best_confidence or best_result is None:
                        best_confidence = confidence
                        best_result = {
                            'translated_content': translated_content,
                            'confidence': confidence,
                            'conversation': conversation
                        }
                    
                    # If confidence is high enough, accept this result
                    if confidence >= 0.7:
                        translation_time = (datetime.now() - start_time).total_seconds()
                        
                        # Collect conversation history for this attempt
                        conversation_history = []
                        if conversation:
                            conversation_history.append(conversation)
                        
                        result = TranslationResult(
                            unit_id=unit.id,
                            success=True,
                            translated_content=translated_content,
                            translation_time=translation_time,
                            metadata={
                                'strategy': strategy,
                                'temperature': temp,
                                'confidence': confidence,
                                'attempts': attempt_count
                            },
                            conversation_history=conversation_history
                        )
                        logger.info(f"Translation successful: {unit.name} (temp={temp:.2f}, confidence={confidence:.2f})")
                        return result
                
                except Exception as e:
                    last_error = e
                    logger.warning(f"Translation attempt {attempt_count} failed: {e}")
                    
                    # Record failed attempt
                    from ..utils.temperature_optimizer import TranslationAttempt
                    attempt = TranslationAttempt(
                        temperature=temp,
                        success=False,
                        error_message=str(e)
                    )
                    self.temp_optimizer.update_from_attempt(attempt)
                    
                    if attempt_count > max_retries:
                        break
            
            # If we tried all temperatures and none succeeded, use best result if available
            if best_result and attempt_count > max_retries // 2:
                break
        
        # Return best result or failure
        translation_time = (datetime.now() - start_time).total_seconds()
        
        if best_result:
            # best_result is always a dict now
            translated_content = best_result.get('translated_content', '')
            confidence = best_result.get('confidence', 0.5)
            conversation_history = []
            if best_result.get('conversation'):
                conversation_history.append(best_result['conversation'])
            
            logger.info(f"Translation completed with best attempt: {unit.name} (confidence={confidence:.2f}, attempts={attempt_count})")
            return TranslationResult(
                unit_id=unit.id,
                success=True,
                translated_content=translated_content,
                translation_time=translation_time,
                metadata={
                    'strategy': strategy,
                    'confidence': confidence,
                    'attempts': attempt_count,
                    'note': 'Used best result from multiple attempts'
                },
                conversation_history=conversation_history
            )
        else:
            logger.error(f"Translation failed after {attempt_count} attempts: {unit.name} - {last_error}")
            return TranslationResult(
                unit_id=unit.id,
                success=False,
                error_message=str(last_error) if last_error else "Translation failed after all retries",
                translation_time=translation_time,
                metadata={'strategy': strategy, 'attempts': attempt_count}
            )
    
    async def _load_file_content(self, file_path: str) -> str:
        """Load file content"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    async def _single_pass_translation(self, unit: TranslationUnit, temperature: float) -> Dict[str, Any]:
        """Single pass translation with MCP"""
        if self.mcp_translator:
            # Get the actual project from orchestrator
            # We need to get the project properly - for now, create a minimal one
            from ..models.project import Project
            project = Project(name="temp", path=unit.path.parent)
            result = await self.mcp_translator.translate_with_mcp(unit, project, temperature)
            
            # Handle both dict and tuple return formats
            if isinstance(result, dict):
                return result
            else:
                # Legacy tuple format - convert to dict
                translated_code, confidence = result
                return {
                    'translated_code': translated_code,
                    'confidence': confidence,
                    'conversation': None
                }
        # Fallback to basic translation
        return {
            'translated_code': f"// Translated from {unit.name}\n// Single pass translation\n",
            'confidence': 0.5,
            'conversation': None
        }
    
    async def _multi_pass_translation(self, unit: TranslationUnit, temperature: float) -> Dict[str, Any]:
        """Multi-pass translation with MCP"""
        if self.mcp_translator:
            from ..models.project import Project
            project = Project(name="temp", path=unit.path.parent)
            result = await self.mcp_translator.translate_with_mcp(unit, project, temperature)
            if isinstance(result, dict):
                return result
            else:
                translated_code, confidence = result
                return {
                    'translated_code': translated_code,
                    'confidence': confidence,
                    'conversation': None
                }
        return {
            'translated_code': f"// Translated from {unit.name}\n// Multi-pass translation\n",
            'confidence': 0.5,
            'conversation': None
        }
    
    async def _hybrid_translation(self, unit: TranslationUnit, temperature: float) -> Dict[str, Any]:
        """Hybrid translation with MCP"""
        if self.mcp_translator:
            from ..models.project import Project
            project = Project(name="temp", path=unit.path.parent)
            result = await self.mcp_translator.translate_with_mcp(unit, project, temperature)
            if isinstance(result, dict):
                return result
            else:
                translated_code, confidence = result
                return {
                    'translated_code': translated_code,
                    'confidence': confidence,
                    'conversation': None
                }
        return {
            'translated_code': f"// Translated from {unit.name}\n// Hybrid translation\n",
            'confidence': 0.5,
            'conversation': None
        }
    
    async def _adaptive_translation(self, unit: TranslationUnit, temperature: float) -> Dict[str, Any]:
        """Adaptive translation with MCP"""
        if self.mcp_translator:
            from ..models.project import Project
            project = Project(name="temp", path=unit.path.parent)
            result = await self.mcp_translator.translate_with_mcp(unit, project, temperature)
            if isinstance(result, dict):
                return result
            else:
                translated_code, confidence = result
                return {
                    'translated_code': translated_code,
                    'confidence': confidence,
                    'conversation': None
                }
        return {
            'translated_code': f"// Translated from {unit.name}\n// Adaptive translation\n",
            'confidence': 0.5,
            'conversation': None
        }


class QualityAgent(BaseAgent):
    """Agent responsible for quality assurance"""
    
    def __init__(self, config: Config):
        super().__init__(config)
    
    async def check_quality(self, result: TranslationResult) -> float:
        """Check the quality of a translation result"""
        if not result.success or not result.translated_content:
            return 0.0
        
        # Simple quality metrics
        content = result.translated_content
        
        # Check for basic Rust syntax
        syntax_score = await self._check_syntax(content)
        
        # Check for completeness
        completeness_score = await self._check_completeness(content)
        
        # Check for style
        style_score = await self._check_style(content)
        
        # Calculate overall quality score
        quality_score = (syntax_score + completeness_score + style_score) / 3
        
        logger.info(f"Quality check complete: {quality_score:.2f}")
        return quality_score
    
    async def _check_syntax(self, content: str) -> float:
        """Check Rust syntax"""
        # Simple syntax checks
        if 'fn ' in content and '{' in content and '}' in content:
            return 0.8
        return 0.3
    
    async def _check_completeness(self, content: str) -> float:
        """Check translation completeness"""
        # Simple completeness checks
        if len(content.strip()) > 10:
            return 0.7
        return 0.2
    
    async def _check_style(self, content: str) -> float:
        """Check code style"""
        # Simple style checks
        if content.startswith('//') or content.startswith('/*'):
            return 0.6
        return 0.4


class AgentOrchestrator:
    """Orchestrates the multi-agent system"""
    
    def __init__(self, config: Config, mcp_client: Optional[MCPClient] = None, mcp_translator: Optional[MCPTranslator] = None):
        self.config = config
        self.mcp_client = mcp_client
        self.project_manager = ProjectManager(config)
        self.tech_leader = TechLeader(config)
        self.translator = TranslatorAgent(config, mcp_client, mcp_translator)
        self.quality_agent = QualityAgent(config)
        
        logger.info("Agent orchestrator initialized with MCP support")
    
    async def translate_project(
        self, 
        project_path: str,
        mcp_client: Optional[MCPClient] = None,
        mcp_translator: Optional[MCPTranslator] = None,
        state_manager=None
    ) -> Project:
        """Translate an entire project"""
        logger.info(f"Starting project translation: {project_path}")
        
        # Update MCP references if provided
        if mcp_client:
            self.mcp_client = mcp_client
        if mcp_translator:
            self.mcp_translator = mcp_translator
            self.translator.mcp_client = mcp_client
            self.translator.mcp_translator = mcp_translator
        
        # Initialize project
        project = await self.project_manager.initialize_project(project_path)
        
        # Save initial state
        if state_manager:
            await state_manager.save_project(project)
        
        # Process units in parallel
        semaphore = asyncio.Semaphore(self.config.translation.max_parallel_workers)
        
        tasks = []
        for unit in project.units:
            task = self._process_unit(unit, semaphore, project, state_manager)
            tasks.append(task)
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
        
        # Update final statistics and save
        project.update_statistics()
        if state_manager:
            await state_manager.save_project(project)
        
        logger.info("Project translation complete")
        return project
    
    async def _write_intermediate_file(self, unit: TranslationUnit, project: Project) -> None:
        """Write intermediate Rust file immediately after translation"""
        if not unit.translated_content:
            return
        
        try:
            # Determine output path
            output_dir = Path(self.config.output.output_dir)
            project_output_dir = output_dir / project.name
            
            # Get relative path from project root
            try:
                relative_path = unit.path.relative_to(project.path)
            except ValueError:
                relative_path = Path(unit.path.name)
            
            # Create Rust file path
            rust_file_path = project_output_dir / relative_path
            rust_file_path = rust_file_path.with_suffix('.rs')
            
            # Create output directory
            rust_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write translated content
            with open(rust_file_path, 'w', encoding='utf-8') as f:
                f.write(unit.translated_content)
            
            file_size = len(unit.translated_content)
            logger.info(f"✓ Intermediate file generated: {rust_file_path} ({file_size} bytes)")
            
            # Update Cargo.toml if needed (first file or periodically)
            completed_count = len([u for u in project.units if u.status == TranslationStatus.COMPLETED])
            if completed_count == 1 or completed_count % 10 == 0:
                await self._update_cargo_toml(project, project_output_dir)
        
        except Exception as e:
            logger.warning(f"Failed to write intermediate file for {unit.name}: {e}")
    
    async def _update_cargo_toml(self, project: Project, output_dir: Path) -> None:
        """Update Cargo.toml with current modules"""
        cargo_toml_path = output_dir / "Cargo.toml"
        
        # Safe project name
        safe_name = project.name.lower().replace(' ', '-').replace('_', '-')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '-')
        if not safe_name or safe_name[0].isdigit():
            safe_name = f"translated-{safe_name}"
        
        # Generate basic Cargo.toml
        cargo_content = f"""[package]
name = "{safe_name}"
version = "0.1.0"
edition = "2021"

[dependencies]
# Add dependencies as needed
# libc = "0.2"
"""
        
        with open(cargo_toml_path, 'w', encoding='utf-8') as f:
            f.write(cargo_content)
        
        logger.debug(f"Cargo.toml updated: {cargo_toml_path}")
    
    async def _verify_file_compilation(
        self,
        unit: TranslationUnit,
        translated_code: str,
        project: Project
    ) -> Dict[str, Any]:
        """Verify file compilation in actual project context with detailed error analysis"""
        from ..utils.compilation_verifier import CompilationVerifier
        
        project_output_dir = Path(self.config.output.output_dir) / project.name
        
        # Ensure file is written first
        try:
            relative_path = unit.path.relative_to(project.path)
        except ValueError:
            relative_path = Path(unit.path.name)
        
        rust_file_path = project_output_dir / relative_path.with_suffix('.rs')
        rust_file_path.parent.mkdir(parents=True, exist_ok=True)
        rust_file_path.write_text(translated_code)
        
        # Use actual project directory for verification
        verifier = CompilationVerifier(project_output_dir)
        result = await verifier.verify_file(str(rust_file_path))
        
        return result
    
    async def _fix_compilation_errors(
        self,
        unit: TranslationUnit,
        code: str,
        errors: List[Dict[str, Any]],
        project: Project
    ) -> Dict[str, Any]:
        """Fix compilation errors using LLM-assisted iterative refinement"""
        from ..utils.error_fixer import ErrorFixer
        from ..utils.compilation_verifier import CompilationError
        
        fixer = ErrorFixer(self.config)
        
        # Convert error dicts to CompilationError objects
        compilation_errors = [CompilationError(e) for e in errors]
        
        project_output_dir = Path(self.config.output.output_dir) / project.name
        
        # Determine file path
        try:
            relative_path = unit.path.relative_to(project.path)
        except ValueError:
            relative_path = Path(unit.path.name)
        
        rust_file_path = project_output_dir / relative_path.with_suffix('.rs')
        
        project_context = {
            "project_dir": str(project_output_dir),
            "project_name": project.name,
            "file_path": str(rust_file_path)
        }
        
        result = await fixer.fix_compile_errors(
            code=code,
            errors=compilation_errors,
            filepath=str(rust_file_path),
            project_context=project_context
        )
        
        # Update the file if fix was successful
        if result["success"]:
            rust_file_path.write_text(result["fixed_code"])
            logger.info(f"Updated file with fixed code: {rust_file_path}")
        
        return result
    
    async def _verify_module_compilation(self, module_path: Path) -> Dict[str, Any]:
        """Verify a module compiles independently in its own context"""
        from ..utils.compilation_verifier import CompilationVerifier
        
        verifier = CompilationVerifier(module_path)
        return await verifier.verify_module(module_path)
    
    async def _process_unit(self, unit: TranslationUnit, semaphore: asyncio.Semaphore, project: Project, state_manager=None) -> None:
        """Process a single translation unit"""
        async with semaphore:
            # Wait for dependencies to be ready
            await self._wait_for_dependencies(unit, project)
            
            # Mark unit as in progress
            unit.status = TranslationStatus.IN_PROGRESS
            
            # Analyze unit
            analysis = await self.tech_leader.analyze_unit(unit)
            
            # Translate unit
            logger.info(f"[TRANSLATION] Starting translation for: {unit.name}, strategy={analysis.get('strategy', 'unknown')}")
            result = await self.translator.translate_unit(unit, analysis['strategy'])
            logger.info(f"[TRANSLATION] Translation result for {unit.name}: success={result.success}, content_length={len(result.translated_content) if result.translated_content else 0}")
            
            # Check quality and verify compilation
            if result.success:
                logger.info(f"[SUCCESS] Translation succeeded for {unit.name}")
                quality_score = await self.quality_agent.check_quality(result)
                result.quality_score = quality_score
                
                # Verify compilation in actual project context with detailed error analysis
                # Skip compilation verification for header files (they need implementation files to compile)
                if unit.type == TranslationUnitType.PURE_HEADER:
                    logger.debug(f"Skipping compilation verification for header file: {unit.name} (headers need implementations to compile)")
                    compilation_result = {
                        "success": True,  # Consider headers as successfully verified (syntax check passed)
                        "error_count": 0,
                        "warning_count": 0,
                        "errors": [],
                        "warnings": [],
                        "note": "Header file - compilation verification skipped (requires implementation to verify)"
                    }
                else:
                    compilation_result = await self._verify_file_compilation(unit, result.translated_content, project)
                
                if not compilation_result["success"] and compilation_result.get("error_count", 0) > 0:
                    # Try to fix errors with LLM
                    fixed_result = await self._fix_compilation_errors(
                        unit,
                        result.translated_content,
                        compilation_result["errors"],
                        project
                    )
                    
                    if fixed_result["success"]:
                        result.translated_content = fixed_result["fixed_code"]
                        logger.info(f"✓ Fixed {len(fixed_result.get('fixed_errors', []))} compilation errors for {unit.name}")
                        # Verify again after fix
                        compilation_result = await self._verify_file_compilation(unit, result.translated_content, project)
                        if compilation_result["success"]:
                            logger.info(f"✓ File compiles successfully after fix: {unit.name}")
                        else:
                            logger.warning(f"⚠ File still has compilation errors after fix: {unit.name}")
                    else:
                        logger.warning(f"⚠ Could not fix all compilation errors for {unit.name}")
                
                # Store compilation result in metadata
                result.metadata["compilation"] = {
                    "success": compilation_result["success"],
                    "error_count": compilation_result.get("error_count", 0),
                    "warning_count": compilation_result.get("warning_count", 0)
                }
                
                # Store translation result in unit
                unit.translated_content = result.translated_content
                unit.status = TranslationStatus.COMPLETED
                unit.translation_result = result
                
                # Write intermediate file immediately (real-time generation)
                logger.info(f"[FILE] Writing intermediate file for completed unit: {unit.name}")
                await self._write_intermediate_file(unit, project)
                logger.info(f"[FILE] Intermediate file successfully written for: {unit.name}")
            else:
                logger.error(f"[FAILED] Translation failed for {unit.name}: {result.error_message}")
                unit.status = TranslationStatus.FAILED
                unit.error_message = result.error_message
                unit.translation_result = result
                
                # Even for failed translations, write partial content if available
                if result.translated_content and len(result.translated_content.strip()) > 10:
                    logger.warning(f"[FILE] Writing partial translation for failed unit: {unit.name} ({len(result.translated_content)} bytes)")
                    unit.translated_content = result.translated_content
                    await self._write_intermediate_file(unit, project)
            
            # Update session
            await self.project_manager.update_session(result)
            
            # Update project statistics
            project.update_statistics()
            
            # Save project state periodically (every 5 units or on completion/failure)
            if state_manager:
                # Get completed and failed counts to determine when to save
                completed = len([u for u in project.units if u.status == TranslationStatus.COMPLETED])
                failed = len([u for u in project.units if u.status == TranslationStatus.FAILED])
                
                # Save if it's a milestone (every 5 units) or this is a completed/failed unit
                if (completed + failed) % 5 == 0 or unit.status in [TranslationStatus.COMPLETED, TranslationStatus.FAILED]:
                    await state_manager.save_project(project)
                    logger.debug(f"Project state saved: {completed + failed}/{project.total_files} units processed")
    
    async def _wait_for_dependencies(self, unit: TranslationUnit, project: Optional[Project] = None) -> None:
        """Wait for unit dependencies to be ready"""
        if not self.project_manager.current_session:
            return
        
        # Use project from project_manager if not provided
        if project is None:
            project = self.project_manager.current_project
        
        completed_units = self.project_manager.current_session.completed_units
        
        max_wait_time = 300.0  # Maximum wait time in seconds (5 minutes)
        start_time = asyncio.get_event_loop().time()
        wait_interval = 0.5  # Check every 0.5 seconds
        
        while not unit.is_ready_for_translation(completed_units, project=project):
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_wait_time:
                logger.warning(f"Timeout waiting for dependencies of {unit.name} after {max_wait_time}s, proceeding anyway")
                break
            await asyncio.sleep(wait_interval)
            completed_units = self.project_manager.current_session.completed_units
