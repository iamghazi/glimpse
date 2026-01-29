"""
Videos Routes
Video upload, list, get, and delete operations
"""
import logging
import json
import shutil
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse

from src.core.config import settings
from src.video_processing.service import VideoProcessor
from src.search.vector_db import VideoVectorDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/videos", tags=["videos"])


@router.post("/upload")
async def upload_video(file: UploadFile = File(...), title: str = Form(...)):
    """
    Upload a video file to the library

    Automatically processes the video:
    - Chunks into segments
    - Extracts frames
    - Generates AI analysis (transcription + visual descriptions)
    - Generates embeddings
    - Indexes in Qdrant

    Args:
        file: Video file to upload
        title: Video title

    Returns:
        Upload and processing summary
    """
    try:
        # Generate video ID from timestamp
        video_id = f"vid_{int(datetime.utcnow().timestamp())}"

        # Get file extension
        file_extension = Path(file.filename).suffix
        video_filename = f"{video_id}{file_extension}"
        video_path = settings.VIDEOS_DIR / video_filename

        logger.info(f"Uploading video: {video_id} ({title})")

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
            "original_filename": file.filename,
        }

        # Save initial metadata
        metadata_path = settings.METADATA_DIR / f"{video_id}.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        # Process video (chunk + extract frames + AI analysis + indexing)
        logger.info(f"Starting video processing for {video_id}...")
        processor = VideoProcessor(enable_ai_analysis=True, enable_indexing=True)
        processing_result = processor.process_video(video_id, str(video_path), title)

        logger.info(
            f"✅ Video {video_id} uploaded and processed successfully "
            f"({processing_result['num_chunks']} chunks, "
            f"{processing_result['total_frames']} frames)"
        )

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
                    "status": processing_result["status"],
                    "indexing": processing_result.get("indexing"),
                },
            },
        )

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("")
async def list_videos():
    """
    List all videos in the library with their metadata

    Returns:
        List of videos with metadata, sorted by upload date (newest first)
    """
    try:
        videos = []

        # Read all metadata files (exclude chunks files)
        for metadata_file in settings.METADATA_DIR.glob("*.json"):
            # Skip chunk metadata files
            if "_chunks.json" in metadata_file.name:
                continue

            with open(metadata_file, "r") as f:
                metadata = json.load(f)

                # Add representative_frame from first chunk for thumbnail
                video_id = metadata.get("video_id")
                if video_id:
                    chunks_file = settings.METADATA_DIR / f"{video_id}_chunks.json"
                    if chunks_file.exists():
                        try:
                            with open(chunks_file, "r") as cf:
                                chunks = json.load(cf)
                                if chunks and len(chunks) > 0:
                                    representative_frame = chunks[0].get("representative_frame")
                                    if representative_frame:
                                        metadata["representative_frame"] = representative_frame
                        except Exception as e:
                            logger.debug(f"Could not load representative_frame for {video_id}: {e}")

                videos.append(metadata)

        # Sort by upload date (newest first)
        videos.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)

        logger.debug(f"Listed {len(videos)} videos")

        return {"count": len(videos), "videos": videos}

    except Exception as e:
        logger.error(f"Failed to list videos: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list videos: {str(e)}")


@router.get("/{video_id}")
async def get_video(video_id: str):
    """
    Get metadata for a specific video

    Args:
        video_id: Video identifier

    Returns:
        Video metadata
    """
    try:
        metadata_path = settings.METADATA_DIR / f"{video_id}.json"

        if not metadata_path.exists():
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        return metadata

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get video: {str(e)}")


@router.get("/{video_id}/chunks")
async def get_video_chunks(video_id: str):
    """
    Get all chunks for a specific video

    Args:
        video_id: Video identifier

    Returns:
        List of video chunks with metadata
    """
    try:
        chunks_metadata_path = settings.METADATA_DIR / f"{video_id}_chunks.json"

        if not chunks_metadata_path.exists():
            return {
                "video_id": video_id,
                "chunks": [],
                "message": "No chunks found - video may not be processed yet",
            }

        with open(chunks_metadata_path, "r") as f:
            chunks = json.load(f)

        logger.debug(f"Retrieved {len(chunks)} chunks for video {video_id}")

        return {"video_id": video_id, "num_chunks": len(chunks), "chunks": chunks}

    except Exception as e:
        logger.error(f"Failed to get chunks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get chunks: {str(e)}")


@router.delete("/{video_id}")
async def delete_video(video_id: str):
    """
    Delete a video and all associated data

    Deletes:
    - Video file
    - Metadata files
    - Chunks metadata
    - Frames
    - Qdrant vectors

    Args:
        video_id: Video identifier

    Returns:
        Deletion summary
    """
    try:
        metadata_path = settings.METADATA_DIR / f"{video_id}.json"

        if not metadata_path.exists():
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

        logger.info(f"Deleting video: {video_id}")

        # Read metadata to get file path
        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        # Delete video file
        video_path = Path(metadata["file_path"])
        if video_path.exists():
            video_path.unlink()
            logger.debug(f"Deleted video file: {video_path}")

        # Delete metadata file
        metadata_path.unlink()
        logger.debug(f"Deleted metadata file: {metadata_path}")

        # Delete chunks metadata if exists
        chunks_metadata_path = settings.METADATA_DIR / f"{video_id}_chunks.json"
        if chunks_metadata_path.exists():
            chunks_metadata_path.unlink()
            logger.debug(f"Deleted chunks metadata: {chunks_metadata_path}")

        # Delete frames directory
        frames_dir = settings.FRAMES_DIR / video_id
        if frames_dir.exists():
            shutil.rmtree(frames_dir)
            logger.debug(f"Deleted frames directory: {frames_dir}")

        # Delete from Qdrant
        try:
            db = VideoVectorDB()
            delete_result = db.delete_video(video_id)
            logger.debug(
                f"Deleted {delete_result['deleted_count']} vectors from Qdrant"
            )
        except Exception as e:
            logger.warning(f"Failed to delete from Qdrant: {e}")

        logger.info(f"✅ Video {video_id} deleted successfully")

        return {
            "video_id": video_id,
            "message": "Video deleted successfully",
            "deleted": {
                "video_file": str(video_path),
                "metadata": str(metadata_path),
                "chunks_metadata": str(chunks_metadata_path),
                "frames_dir": str(frames_dir),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete video: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete video: {str(e)}")
