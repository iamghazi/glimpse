"""
Settings Routes
Configuration management endpoints for the desktop application
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.core.config import settings
from pathlib import Path

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsResponse(BaseModel):
    """Current settings from backend"""
    GCP_PROJECT_ID: str
    GCP_LOCATION: str
    GEMINI_MODEL: str
    CHUNK_DURATION_SECONDS: float
    CHUNK_OVERLAP_SECONDS: float
    FRAME_EXTRACTION_FPS: float
    EMBEDDING_MAX_WORKERS: int
    TIER1_CANDIDATES: int
    CONFIDENCE_THRESHOLD: float
    DATA_DIR: str
    VIDEOS_DIR: str
    FRAMES_DIR: str
    METADATA_DIR: str
    QDRANT_STORAGE_DIR: str


@router.get("", response_model=SettingsResponse)
async def get_settings():
    """
    Get current settings from backend configuration

    Returns all configuration values currently in use by the backend.
    """
    return SettingsResponse(
        GCP_PROJECT_ID=settings.GCP_PROJECT_ID,
        GCP_LOCATION=settings.GCP_LOCATION,
        GEMINI_MODEL=settings.GEMINI_MODEL,
        CHUNK_DURATION_SECONDS=settings.CHUNK_DURATION_SECONDS,
        CHUNK_OVERLAP_SECONDS=settings.CHUNK_OVERLAP_SECONDS,
        FRAME_EXTRACTION_FPS=settings.FRAME_EXTRACTION_FPS,
        EMBEDDING_MAX_WORKERS=settings.EMBEDDING_MAX_WORKERS,
        TIER1_CANDIDATES=settings.TIER1_CANDIDATES,
        CONFIDENCE_THRESHOLD=settings.CONFIDENCE_THRESHOLD,
        DATA_DIR=str(settings.DATA_DIR),
        VIDEOS_DIR=str(settings.VIDEOS_DIR),
        FRAMES_DIR=str(settings.FRAMES_DIR),
        METADATA_DIR=str(settings.METADATA_DIR),
        QDRANT_STORAGE_DIR=str(settings.DATA_DIR / "qdrant_storage"),
    )


@router.put("")
async def update_settings(update: dict):
    """
    Update settings in .env file

    Updates the .env file with new configuration values.
    Note: Backend server restart required for changes to take effect.
    """
    try:
        env_path = Path(".env")
        env_lines = []

        if env_path.exists():
            with open(env_path, "r") as f:
                env_lines = f.readlines()

        # Update values
        for key, value in update.items():
            found = False
            for i, line in enumerate(env_lines):
                if line.startswith(f"{key}="):
                    env_lines[i] = f"{key}={value}\n"
                    found = True
                    break

            if not found:
                env_lines.append(f"{key}={value}\n")

        # Write back
        with open(env_path, "w") as f:
            f.writelines(env_lines)

        return {
            "message": "Settings updated successfully. Restart server to apply changes.",
            "updated_fields": list(update.keys())
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


@router.post("/test-connection")
async def test_gcp_connection():
    """
    Test GCP credentials

    Attempts to initialize Vertex AI with current GCP credentials
    to verify they are valid.
    """
    try:
        from google.cloud import aiplatform

        aiplatform.init(
            project=settings.GCP_PROJECT_ID,
            location=settings.GCP_LOCATION
        )

        return {"connected": True}

    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }
