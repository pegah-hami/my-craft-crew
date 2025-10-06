"""
Main entry point for MyCraftCrew.

This module initializes the FastAPI application and starts the server.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

from config.settings import settings, setup_logging, create_directories
from api.routes import router
from api.middleware import setup_middleware
from agents.design_agent import DesignAgent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logging.info("Starting MyCraftCrew...")
    
    # Create necessary directories
    create_directories(settings)
    
    # Initialize and start agents
    design_agent = DesignAgent()
    await design_agent.start()
    
    # Store agents in app state
    app.state.design_agent = design_agent
    
    logging.info("MyCraftCrew started successfully")
    
    yield
    
    # Shutdown
    logging.info("Shutting down MyCraftCrew...")
    
    # Stop agents
    if hasattr(app.state, 'design_agent'):
        await app.state.design_agent.stop()
    
    logging.info("MyCraftCrew stopped")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    # Setup logging
    setup_logging(settings)
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="MyCraftCrew - A multi-agent system for generating product designs and collages",
        lifespan=lifespan,
        debug=settings.debug
    )
    
    # Setup middleware
    setup_middleware(app)
    
    # Include routers
    app.include_router(router)
    
    # Mount static files (if needed)
    if settings.debug:
        app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Welcome to MyCraftCrew",
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/api/v1/health"
        }
    
    return app


def main():
    """
    Main entry point for running the application.
    """
    # Create app
    app = create_app()
    
    # Run server
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
