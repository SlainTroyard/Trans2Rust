"""
FastAPI web interface for CStarX v2.0
"""

import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

from ..core.translator import Translator
from ..models.config import Config

# Create FastAPI app
app = FastAPI(
    title="CStarX v2.0 API",
    description="Advanced C/C++ to Rust Translation Tool",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global translator instance
translator: Optional[Translator] = None


class TranslationRequest(BaseModel):
    """Request model for translation"""
    project_path: str
    output_path: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class TranslationResponse(BaseModel):
    """Response model for translation"""
    project_id: str
    status: str
    message: str


class StatusResponse(BaseModel):
    """Response model for status"""
    status: str
    project: Optional[Dict[str, Any]] = None
    session: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Initialize translator on startup"""
    global translator
    config = Config.from_env()
    translator = Translator(config)
    logger.info("CStarX API started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global translator
    if translator:
        await translator.cleanup()
    logger.info("CStarX API stopped")


@app.post("/translate", response_model=TranslationResponse)
async def translate_project(request: TranslationRequest, background_tasks: BackgroundTasks):
    """Start translation of a project"""
    if not translator:
        raise HTTPException(status_code=500, detail="Translator not initialized")
    
    try:
        # Update config if provided
        if request.config:
            # Update translator config
            pass
        
        # Start translation in background
        background_tasks.add_task(
            _run_translation,
            request.project_path,
            request.output_path
        )
        
        return TranslationResponse(
            project_id="temp_id",  # This would be the actual project ID
            status="started",
            message="Translation started successfully"
        )
        
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get current translation status"""
    if not translator:
        raise HTTPException(status_code=500, detail="Translator not initialized")
    
    try:
        status = await translator.get_translation_status()
        return StatusResponse(**status)
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pause")
async def pause_translation():
    """Pause current translation"""
    if not translator:
        raise HTTPException(status_code=500, detail="Translator not initialized")
    
    try:
        await translator.pause_translation()
        return {"status": "paused", "message": "Translation paused successfully"}
    except Exception as e:
        logger.error(f"Failed to pause translation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/resume")
async def resume_translation():
    """Resume paused translation"""
    if not translator:
        raise HTTPException(status_code=500, detail="Translator not initialized")
    
    try:
        await translator.resume_translation()
        return {"status": "resumed", "message": "Translation resumed successfully"}
    except Exception as e:
        logger.error(f"Failed to resume translation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cleanup")
async def cleanup():
    """Clean up old state files"""
    if not translator:
        raise HTTPException(status_code=500, detail="Translator not initialized")
    
    try:
        await translator.cleanup()
        return {"status": "cleaned", "message": "Cleanup completed successfully"}
    except Exception as e:
        logger.error(f"Failed to cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}


async def _run_translation(project_path: str, output_path: Optional[str]):
    """Run translation in background"""
    try:
        await translator.translate_project(project_path, output_path)
        logger.info("Background translation completed")
    except Exception as e:
        logger.error(f"Background translation failed: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
