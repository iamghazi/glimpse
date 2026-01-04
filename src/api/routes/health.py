"""
Health Check Routes
Basic service status endpoints
"""
from fastapi import APIRouter
from datetime import datetime

from src.core.config import settings
from src.models.common import HealthCheckResponse
from src.search.vector_db import VideoVectorDB

router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Video Library Search Engine API",
        "version": "4.0.0",
        "status": "running",
        "docs": "/docs",
    }


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint

    Returns service status and Qdrant connection status
    """
    # Check Qdrant connection
    qdrant_connected = False
    try:
        db = VideoVectorDB()
        db.get_collection_info()
        qdrant_connected = True
    except Exception:
        qdrant_connected = False

    return HealthCheckResponse(
        status="healthy",
        version="4.0.0",
        qdrant_connected=qdrant_connected,
    )
