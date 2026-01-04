"""
Application Configuration
Centralized environment variable management
"""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Google Cloud Configuration
    GCP_PROJECT_ID: str
    GCP_LOCATION: str = "us-central1"
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"

    # Qdrant Vector Database
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    # Video Processing
    CHUNK_DURATION_SECONDS: float = 30.0
    CHUNK_OVERLAP_SECONDS: float = 5.0
    FRAME_EXTRACTION_FPS: float = 1.0

    # Storage Paths (relative to project root)
    DATA_DIR: Path = Path("data")
    VIDEOS_DIR: Path = DATA_DIR / "videos"
    FRAMES_DIR: Path = DATA_DIR / "frames"
    METADATA_DIR: Path = DATA_DIR / "metadata"
    QDRANT_STORAGE_DIR: Path = DATA_DIR / "qdrant_storage"

    # Prompts Directory
    PROMPTS_DIR: Path = Path("prompts")

    # Embeddings Configuration
    EMBEDDING_MAX_WORKERS: int = 5
    TEXT_EMBEDDING_MODEL: str = "gemini-embedding-001"
    TEXT_VECTOR_SIZE: int = 3072  # gemini-embedding-001 dimensions
    VISUAL_EMBEDDING_MODEL: str = "multimodalembedding@001"
    VISUAL_VECTOR_SIZE: int = 1408  # multimodalembedding@001 dimensions

    # Cascaded Reranking Configuration
    RERANKING_ENABLED: bool = True
    TIER1_CANDIDATES: int = 50
    TIER2_MODEL: str = "gemini-2.0-flash-exp"
    TIER3_FRAMES_PER_CLIP: int = 5
    CONFIDENCE_THRESHOLD: float = 0.8

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # Desktop app (Electron/Tauri)
        "http://localhost:8501",  # Streamlit (deprecated)
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8501",
    ]

    # API Server Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure all data directories exist
        self._ensure_directories()

    def _ensure_directories(self):
        """Create all required directories if they don't exist"""
        directories = [
            self.DATA_DIR,
            self.VIDEOS_DIR,
            self.FRAMES_DIR,
            self.METADATA_DIR,
            self.QDRANT_STORAGE_DIR,
            self.PROMPTS_DIR,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
