"""
FastAPI Backend for Video Library Search Engine
Phase 3.4: Basic upload and list endpoints
"""
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
from datetime import datetime
import os
import shutil
from dotenv import load_dotenv
from custom_types import VideoMetadata
import json

load_dotenv()

app = FastAPI(title="Video Library API", version="3.0.0")

# CORS configuration for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify Streamlit URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
VIDEOS_DIR = Path(os.getenv("VIDEOS_DIR", "./videos"))
METADATA_DIR = Path(os.getenv("METADATA_DIR", "./metadata"))
FRAMES_DIR = Path(os.getenv("FRAMES_DIR", "./frames"))

# Ensure directories exist
VIDEOS_DIR.mkdir(exist_ok=True)
METADATA_DIR.mkdir(exist_ok=True)
FRAMES_DIR.mkdir(exist_ok=True)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Video Library Search Engine API",
        "version": "3.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "videos_dir": str(VIDEOS_DIR),
        "metadata_dir": str(METADATA_DIR),
        "frames_dir": str(FRAMES_DIR)
    }


@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...)
):
    """
    Upload a video file to the library
    Phase 3.4: Basic upload - saves file and creates metadata
    Phase 3.5+: Will trigger processing pipeline
    """
    try:
        # Generate video ID from timestamp
        video_id = f"vid_{int(datetime.utcnow().timestamp())}"

        # Get file extension
        file_extension = Path(file.filename).suffix
        video_filename = f"{video_id}{file_extension}"
        video_path = VIDEOS_DIR / video_filename

        # Save uploaded file
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Get file stats
        file_stats = video_path.stat()
        file_size_mb = file_stats.st_size / (1024 * 1024)

        # Create basic metadata
        # Note: Duration, FPS, resolution will be added in Phase 3.5 with video processing
        metadata = {
            "video_id": video_id,
            "title": title,
            "file_path": str(video_path),
            "duration_seconds": 0.0,  # Placeholder - will be populated in Phase 3.5
            "fps": 0.0,  # Placeholder
            "resolution": [0, 0],  # Placeholder
            "file_size_mb": file_size_mb,
            "uploaded_at": datetime.utcnow().isoformat(),
            "indexed_at": None,  # Will be set when processing completes
            "original_filename": file.filename
        }

        # Save metadata
        metadata_path = METADATA_DIR / f"{video_id}.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return JSONResponse(
            status_code=200,
            content={
                "video_id": video_id,
                "message": "Video uploaded successfully. Processing pipeline will be added in Phase 3.5",
                "file_path": str(video_path),
                "file_size_mb": round(file_size_mb, 2),
                "metadata_path": str(metadata_path)
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/videos")
async def list_videos():
    """
    List all videos in the library with their metadata
    """
    try:
        videos = []

        # Read all metadata files
        for metadata_file in METADATA_DIR.glob("*.json"):
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
                videos.append(metadata)

        # Sort by upload date (newest first)
        videos.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)

        return {
            "count": len(videos),
            "videos": videos
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list videos: {str(e)}")


@app.get("/videos/{video_id}")
async def get_video(video_id: str):
    """
    Get metadata for a specific video
    """
    try:
        metadata_path = METADATA_DIR / f"{video_id}.json"

        if not metadata_path.exists():
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        return metadata

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get video: {str(e)}")


@app.delete("/videos/{video_id}")
async def delete_video(video_id: str):
    """
    Delete a video and its associated data
    """
    try:
        metadata_path = METADATA_DIR / f"{video_id}.json"

        if not metadata_path.exists():
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

        # Read metadata to get file path
        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        # Delete video file
        video_path = Path(metadata["file_path"])
        if video_path.exists():
            video_path.unlink()

        # Delete metadata file
        metadata_path.unlink()

        # Delete frames directory if exists (will be created in Phase 3.5)
        frames_dir = FRAMES_DIR / video_id
        if frames_dir.exists():
            shutil.rmtree(frames_dir)

        return {
            "message": f"Video {video_id} deleted successfully",
            "video_id": video_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete video: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
