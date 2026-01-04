"""
Video-related Pydantic Models
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class VideoMetadata(BaseModel):
    """Metadata for a video in the library"""

    video_id: str = Field(..., description="Unique identifier (UUID)")
    title: str = Field(..., description="Display name")
    file_path: str = Field(..., description="Local path: ./videos/{video_id}.mp4")
    duration_seconds: float = Field(..., description="Total video duration")
    fps: float = Field(..., description="Frames per second")
    resolution: tuple[int, int] = Field(..., description="(width, height)")
    file_size_mb: float = Field(..., description="File size in megabytes")
    uploaded_at: datetime = Field(
        default_factory=datetime.now, description="Upload timestamp"
    )
    indexed_at: Optional[datetime] = Field(
        None, description="Indexing completion timestamp"
    )


class VideoChunk(BaseModel):
    """A time-based segment of a video with extracted content"""

    chunk_id: str = Field(
        ..., description="Format: {video_id}_{start_time}_{end_time}"
    )
    video_id: str = Field(..., description="Parent video ID")
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    duration: float = Field(..., description="Chunk duration (typically 60s)")
    visual_description: str = Field(
        default="", description="AI-generated scene description"
    )
    audio_transcript: str = Field(default="", description="Whisper transcription")
    frame_paths: list[str] = Field(
        default_factory=list, description="Paths to extracted frames (1 FPS)"
    )
    representative_frame: str = Field(default="", description="Middle frame for thumbnails")

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "abc123_0_60",
                "video_id": "abc123",
                "start_time": 0.0,
                "end_time": 60.0,
                "duration": 60.0,
                "visual_description": "A person walking through a forest with sunlight filtering through trees.",
                "audio_transcript": "The sound of birds chirping and leaves rustling in the wind.",
                "frame_paths": ["frames/abc123_0.jpg", "frames/abc123_1.jpg"],
                "representative_frame": "frames/abc123_30.jpg",
            }
        }


class VideoChunkWithEmbedding(VideoChunk):
    """VideoChunk with dual embeddings (text + visual)"""

    text_embedding: list[float] = Field(
        ..., description="3072-dim vector from gemini-embedding-001"
    )
    visual_embedding: list[float] = Field(
        ..., description="1408-dim vector from multimodalembedding@001"
    )

    class Config:
        json_schema_extra = {
            "example": {
                **VideoChunk.Config.json_schema_extra["example"],
                "text_embedding": [0.1, 0.2, 0.3],  # Truncated
                "visual_embedding": [0.4, 0.5, 0.6],  # Truncated
            }
        }
