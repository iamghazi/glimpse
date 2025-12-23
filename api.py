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
from video_processor import process_video_file
from embeddings import search_videos
from chat_handler import chat_with_video_clips
from pydantic import BaseModel

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
    Phase 3.5: Upload + process (chunk, extract frames)
    Phase 3.6+: Will add transcription and visual descriptions
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
        metadata = {
            "video_id": video_id,
            "title": title,
            "file_path": str(video_path),
            "duration_seconds": 0.0,  # Will be populated by processor
            "fps": 0.0,  # Will be populated by processor
            "resolution": [0, 0],  # Will be populated by processor
            "file_size_mb": file_size_mb,
            "uploaded_at": datetime.utcnow().isoformat(),
            "indexed_at": None,  # Will be set when full processing completes
            "original_filename": file.filename
        }

        # Save initial metadata
        metadata_path = METADATA_DIR / f"{video_id}.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        # Process video (chunk + extract frames)
        print(f"Starting video processing for {video_id}...")
        processing_result = process_video_file(video_id, str(video_path), title)

        return JSONResponse(
            status_code=200,
            content={
                "video_id": video_id,
                "message": "Video uploaded and processed successfully",
                "file_path": str(video_path),
                "file_size_mb": round(file_size_mb, 2),
                "metadata_path": str(metadata_path),
                "processing": {
                    "num_chunks": processing_result["num_chunks"],
                    "total_frames": processing_result["total_frames"],
                    "status": processing_result["status"]
                },
                "note": "Transcription and visual descriptions will be added in Phase 3.6"
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

        # Read all metadata files (exclude chunks files)
        for metadata_file in METADATA_DIR.glob("*.json"):
            # Skip chunk metadata files
            if "_chunks.json" in metadata_file.name:
                continue

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


@app.get("/videos/{video_id}/chunks")
async def get_video_chunks(video_id: str):
    """
    Get all chunks for a specific video
    """
    try:
        chunks_metadata_path = METADATA_DIR / f"{video_id}_chunks.json"

        if not chunks_metadata_path.exists():
            return {
                "video_id": video_id,
                "chunks": [],
                "message": "No chunks found - video may not be processed yet"
            }

        with open(chunks_metadata_path, "r") as f:
            chunks = json.load(f)

        return {
            "video_id": video_id,
            "num_chunks": len(chunks),
            "chunks": chunks
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chunks: {str(e)}")


class SearchRequest(BaseModel):
    """Search request model"""
    query: str
    top_k: int = 5
    video_id: str | None = None


class ChatRequest(BaseModel):
    """Chat request model"""
    chunk_ids: list[str]
    question: str
    cache_name: str | None = None


@app.post("/search")
async def search(request: SearchRequest):
    """
    Search for video chunks using natural language query
    Returns ranked results with similarity scores
    """
    try:
        results = search_videos(
            query=request.query,
            top_k=request.top_k,
            video_id_filter=request.video_id
        )

        return {
            "query": request.query,
            "num_results": len(results),
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat with selected video clips using Gemini with context caching
    """
    try:
        if not request.chunk_ids:
            raise HTTPException(status_code=400, detail="No clips selected")

        if not request.question:
            raise HTTPException(status_code=400, detail="No question provided")

        result = chat_with_video_clips(
            chunk_ids=request.chunk_ids,
            question=request.question
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


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

        # Delete chunks metadata if exists
        chunks_metadata_path = METADATA_DIR / f"{video_id}_chunks.json"
        if chunks_metadata_path.exists():
            chunks_metadata_path.unlink()

        # Delete frames directory if exists
        frames_dir = FRAMES_DIR / video_id
        if frames_dir.exists():
            shutil.rmtree(frames_dir)

        # Delete from Qdrant
        # Note: Qdrant doesn't have a built-in delete by filter, so we keep points for now
        # They'll be cleaned up when the collection is recreated

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
