"""
Search-related Pydantic Models
"""
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """A single search result from the vector database"""

    chunk_id: str = Field(..., description="Matching chunk ID")
    video_id: str = Field(..., description="Source video ID")
    title: str = Field(..., description="Video title")
    start_time: float = Field(..., description="Chunk start time")
    end_time: float = Field(..., description="Chunk end time")
    visual_description: str = Field(..., description="Scene description")
    audio_transcript: str = Field(..., description="Audio transcript")
    score: float = Field(..., description="Similarity/confidence score (0-1)")
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
                "representative_frame": "frames/abc123_150.jpg",
            }
        }


class LibrarySearchResult(BaseModel):
    """Complete search results from library"""

    results: list[SearchResult] = Field(..., description="Top-K matching chunks")
    total_found: int = Field(..., description="Total number of results")
    query_embedding: list[float] = Field(
        default_factory=list, description="Query embedding for debugging"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "results": [],
                "total_found": 5,
                "query_embedding": [0.1, 0.2],  # Truncated
            }
        }


class SearchQueryRequest(BaseModel):
    """Request to search the video library"""

    query: str = Field(..., description="Natural language query")
    top_k: int = Field(5, description="Number of results to return", ge=1, le=50)
    use_cascaded_reranking: bool = Field(
        True, description="Enable 3-tier cascaded reranking"
    )
    confidence_threshold: float = Field(
        0.8, description="Minimum confidence score", ge=0.0, le=1.0
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Show me scenes with people cooking",
                "top_k": 5,
                "use_cascaded_reranking": True,
                "confidence_threshold": 0.8,
            }
        }


class IngestVideoRequest(BaseModel):
    """Request to ingest a video into the library"""

    video_path: str = Field(..., description="Path to local video file")
    title: str = Field(..., description="Display title")

    class Config:
        json_schema_extra = {
            "example": {"video_path": "./videos/my_video.mp4", "title": "My Awesome Video"}
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
                "duration_seconds": 900.0,
            }
        }
