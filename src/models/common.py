"""
Common Pydantic Models and Base Classes
"""
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Health check response"""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    qdrant_connected: bool = Field(..., description="Qdrant connection status")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "qdrant_connected": True,
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""

    error: str = Field(..., description="Error message")
    detail: str = Field(default="", description="Detailed error information")
    code: int = Field(..., description="Error code")

    class Config:
        json_schema_extra = {
            "example": {"error": "Video not found", "detail": "video_id=abc123", "code": 404}
        }
