"""
Chat-related Pydantic Models
"""
from pydantic import BaseModel, Field


class ChatWithClipsRequest(BaseModel):
    """Request to chat with selected video clips"""

    query: str = Field(..., description="User question")
    clip_ids: list[str] = Field(..., description="List of chunk IDs to analyze")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What cooking techniques are shown?",
                "clip_ids": ["abc123_60_120", "def456_180_240"],
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
                "cache_used": True,
            }
        }
