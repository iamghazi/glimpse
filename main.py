# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
# from inngest import Inngest
import os
import shutil
import uuid
from datetime import datetime
from custom_types import VideoMetadata #, IngestVideoRequest, IngestVideoResponse
from vector_db import VideoVectorDB
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

VIDEOS_DIR = Path(os.getenv("VIDEOS_DIR", "./videos"))
# Ensure directories exist
VIDEOS_DIR.mkdir(exist_ok=True)


app = FastAPI(title="Video Library API")

# CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inngest client (To be enabled in Phase 3.5)
# inngest_client = Inngest(app_id="video-library")

# Initialize DB
try:
    vector_db = VideoVectorDB()
    logger.info("✅ Qdrant connection successful.")
except Exception as e:
    logger.error(f"❌ Could not connect to Qdrant: {e}")
    vector_db = None


@app.get("/")
async def root():
    return {"status": "ok", "app": "Video Library API"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    qdrant_status = "disconnected"
    db_info = None

    if vector_db:
        try:
            db_info = vector_db.get_collection_info()
            qdrant_status = "healthy"
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            qdrant_status = "unhealthy"

    return {
        "status": "healthy",
        "qdrant_status": qdrant_status,
        "qdrant_info": db_info,
        "videos_dir_exists": VIDEOS_DIR.exists(),
    }

@app.post("/upload")
async def upload_video(title: str = Body(...), file: UploadFile = File(...)):
    """
    Upload video, save it locally, and trigger indexing.
    Note: Inngest trigger is commented out for now.
    """
    try:
        # Generate video ID
        video_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        file_path = VIDEOS_DIR / f"{video_id}{file_extension}"

        logger.info(f"Receiving file: {file.filename} with title: '{title}'")

        # Save to videos directory
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"File saved locally at: {file_path}")

        # --- Inngest Trigger (Phase 3.5) ---
        # event = IngestVideoRequest(video_id=video_id, title=title, file_path=str(file_path))
        # await inngest_client.send(inngest.Event(name="video/ingest", data=event.dict()))
        # logger.info(f"Sent 'video/ingest' event for video_id: {video_id}")
        # ------------------------------------

        return {
            "video_id": video_id,
            "title": title or file.filename,
            "file_path": str(file_path),
            "status": "uploaded",
            "message": "Video saved locally. Automatic indexing will be added in Phase 3.5."
        }
    except Exception as e:
        logger.error(f"Error during video upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/videos")
async def list_videos():
    """List all indexed videos from the vector database"""
    if not vector_db:
        raise HTTPException(status_code=503, detail="Vector database not connected")
    try:
        video_ids = vector_db.list_videos()
        return {"videos": video_ids, "count": len(video_ids)}
    except Exception as e:
        logger.error(f"Could not list videos from Qdrant: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve video list.")