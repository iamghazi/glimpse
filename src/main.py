"""
Video Library Search Engine API
FastAPI application with modular architecture
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.logging import setup_logging
from src.api.routes import health, videos, search, chat

# Setup logging
setup_logging(log_level="INFO", log_file="api.log")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events

    Startup:
    - Initialize directories
    - Log configuration
    - Check Qdrant connection

    Shutdown:
    - Cleanup resources
    """
    # Startup
    logger.info("🚀 Starting Video Library Search Engine API...")
    logger.info(f"Configuration:")
    logger.info(f"  - Data directory: {settings.DATA_DIR}")
    logger.info(f"  - Videos directory: {settings.VIDEOS_DIR}")
    logger.info(f"  - Frames directory: {settings.FRAMES_DIR}")
    logger.info(f"  - Metadata directory: {settings.METADATA_DIR}")
    logger.info(f"  - Qdrant: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    logger.info(f"  - Cascaded reranking: {settings.RERANKING_ENABLED}")
    logger.info(f"  - Embedding workers: {settings.EMBEDDING_MAX_WORKERS}")

    # Check Qdrant connection
    try:
        from src.search.vector_db import VideoVectorDB

        db = VideoVectorDB()
        info = db.get_collection_info()
        logger.info(
            f"✅ Connected to Qdrant: {info['points_count']} vectors in collection '{info['name']}'"
        )
    except Exception as e:
        logger.warning(f"⚠️  Qdrant connection failed: {e}")
        logger.warning("Some features may not work properly")

    logger.info("✅ API startup complete")

    yield

    # Shutdown
    logger.info("👋 Shutting down Video Library Search Engine API...")


# Create FastAPI app
app = FastAPI(
    title="Video Library Search Engine",
    description="Semantic video search with AI-powered analysis and chat",
    version="4.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(videos.router)
app.include_router(search.router)
app.include_router(chat.router)

logger.info("📋 Registered routes: health, videos, search, chat")
