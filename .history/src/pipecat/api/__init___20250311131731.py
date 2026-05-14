"""
Public API for the pipecat framework.

This module provides the main user-facing interfaces and functions that users
will directly interact with when building applications with pipecat.
"""

from ..pipeline import Pipeline, PipelineTask, PipelineRunner
from ..pipeline.task import PipelineParams

__all__ = ["Pipeline", "PipelineTask", "PipelineRunner", "PipelineParams"]

"""
API endpoints for Pipecat.
"""
from fastapi import FastAPI

def create_api() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI()

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok"}

    @app.get("/readiness")
    async def readiness_check():
        """Readiness check endpoint."""
        return {"status": "ready"}

    return app
