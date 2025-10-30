"""
Main entry point for CStarX v2.0
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional
from loguru import logger

from .core.translator import Translator
from .models.config import Config


async def main():
    """Main entry point"""
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<green>{time}</green> | <level>{level}</level> | {message}")
    
    # Load configuration
    config = Config.from_env()
    
    # Create translator
    translator = Translator(config)
    
    try:
        # Example usage
        project_path = "input/01-Primary"
        output_path = "output/01-Primary"
        
        logger.info("Starting CStarX v2.0")
        
        # Translate project
        project = await translator.translate_project(project_path, output_path)
        
        logger.info(f"Translation complete: {project.name}")
        logger.info(f"Translated {project.translated_files}/{project.total_files} files")
        
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        sys.exit(1)
    
    finally:
        await translator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
