"""
Custom Pydantic models for Phase 3: Video Library Search Engine
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
    uploaded_at: datetime = Field(default_factory=datetime.now, description="Upload timestamp")
    indexed_at: Optional[datetime] = Field(None, description="Indexing completion timestamp")


class VideoChunk(BaseModel):
    """A time-based segment of a video with extracted content"""
    chunk_id: str = Field(..., description="Format: {video_id}_{start_time}_{end_time}")
    video_id: str = Field(..., description="Parent video ID")
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    duration: float = Field(..., description="Chunk duration (typically 60s)")
    visual_description: str = Field(default="", description="AI-generated scene description")
    audio_transcript: str = Field(default="", description="Whisper transcription")
    frame_paths: list[str] = Field(default_factory=list, description="Paths to extracted frames (1 FPS)")
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
                "representative_frame": "frames/abc123_30.jpg"
            }
        }


class VideoChunkWithEmbedding(VideoChunk):
    """VideoChunk with multimodal embedding vector"""
    embedding: list[float] = Field(..., description="1408-dim vector from multimodal-embedding-001")

    class Config:
        json_schema_extra = {
            "example": {
                **VideoChunk.Config.json_schema_extra["example"],
                "embedding": [0.1, 0.2, 0.3]  # Truncated for example
            }
        }


class SearchResult(BaseModel):
    """A single search result from the vector database"""
    chunk_id: str = Field(..., description="Matching chunk ID")
    video_id: str = Field(..., description="Source video ID")
    title: str = Field(..., description="Video title")
    start_time: float = Field(..., description="Chunk start time")
    end_time: float = Field(..., description="Chunk end time")
    visual_description: str = Field(..., description="Scene description")
    audio_transcript: str = Field(..., description="Audio transcript")
    score: float = Field(..., description="Cosine similarity score (0-1)")
    video_path: str = Field(..., description="Path for selective cache creation")
    representative_frame: str = Field(..., description="Thumbnail path")

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "abc123_120_180",
                "video_id": "abc123",
                "title": "Nature Documentary",
                "start_time": 120.0,
                "end_time": 180.0,
                "visual_description": "Eagles soaring above mountains at sunset.",
                "audio_transcript": "The majestic eagle glides effortlessly through the sky.",
                "score": 0.89,
                "video_path": "./videos/abc123.mp4",
                "representative_frame": "frames/abc123_150.jpg"
            }
        }


class LibrarySearchResult(BaseModel):
    """Complete search results from library"""
    results: list[SearchResult] = Field(..., description="Top-K matching chunks")
    total_found: int = Field(..., description="Total number of results")
    query_embedding: list[float] = Field(default_factory=list, description="Query embedding for debugging")

    class Config:
        json_schema_extra = {
            "example": {
                "results": [],
                "total_found": 5,
                "query_embedding": [0.1, 0.2]  # Truncated
            }
        }


class IngestVideoRequest(BaseModel):
    """Request to ingest a video into the library"""
    video_path: str = Field(..., description="Path to local video file")
    title: str = Field(..., description="Display title")

    class Config:
        json_schema_extra = {
            "example": {
                "video_path": "./videos/my_video.mp4",
                "title": "My Awesome Video"
            }
        }


class IngestVideoResponse(BaseModel):
    """Response from video ingestion"""
    video_id: str = Field(..., description="Generated video ID")
    chunks_count: int = Field(..., description="Number of chunks created")
    duration_seconds: float = Field(..., description="Video duration")

    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "abc123",
                "chunks_count": 15,
                "duration_seconds": 900.0
            }
        }


class SearchQueryRequest(BaseModel):
    """Request to search the video library"""
    query: str = Field(..., description="Natural language query")
    top_k: int = Field(5, description="Number of results to return", ge=1, le=50)

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Show me scenes with people cooking",
                "top_k": 5
            }
        }


class ChatWithClipsRequest(BaseModel):
    """Request to chat with selected video clips"""
    query: str = Field(..., description="User question")
    clip_ids: list[str] = Field(..., description="List of chunk IDs to analyze")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What cooking techniques are shown?",
                "clip_ids": ["abc123_60_120", "def456_180_240"]
            }
        }


class ChatWithClipsResponse(BaseModel):
    """Response from chatting with clips"""
    answer: str = Field(..., description="AI-generated answer")
    sources: list[str] = Field(..., description="Source chunk IDs with timestamps")
    cache_used: bool = Field(..., description="Whether context cache was used")

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "The clips show two techniques: sautéing at [01:15] and chopping at [03:20].",
                "sources": ["abc123_60_120 [01:15]", "def456_180_240 [03:20]"],
                "cache_used": True
            }
        }
