"""
Project Models
Data models for video editing projects and timelines
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
import uuid


class TimelineClip(BaseModel):
    """A single clip in the project timeline"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique clip ID")
    video_id: str = Field(..., description="Source video ID")
    source_path: str = Field(..., description="Path to source video file")
    cut_from: float = Field(..., description="Start time in source video (seconds)", ge=0)
    cut_to: float = Field(..., description="End time in source video (seconds)", ge=0)
    order: int = Field(..., description="Position in timeline (0-indexed)")
    transition: Optional[str] = Field("fade", description="Transition type (fade, directional-left, etc.)")
    transition_duration: float = Field(0.5, description="Transition duration in seconds", ge=0, le=2.0)

    @property
    def duration(self) -> float:
        """Calculate clip duration in seconds"""
        return self.cut_to - self.cut_from

    class Config:
        json_schema_extra = {
            "example": {
                "id": "clip-123",
                "video_id": "video-456",
                "source_path": "/data/videos/demo.mp4",
                "cut_from": 10.0,
                "cut_to": 25.0,
                "order": 0,
                "transition": "fade",
                "transition_duration": 0.5
            }
        }


class Project(BaseModel):
    """A video editing project containing a timeline of clips"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique project ID")
    name: str = Field(..., description="Project name")
    goal: str = Field(..., description="What this edit aims to achieve")
    clips: List[TimelineClip] = Field(default_factory=list, description="Timeline clips in order")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    @property
    def total_duration(self) -> float:
        """Calculate total timeline duration (excluding transitions)"""
        return sum(clip.duration for clip in self.clips)

    @property
    def clip_count(self) -> int:
        """Number of clips in timeline"""
        return len(self.clips)

    def add_clip(self, clip: TimelineClip) -> None:
        """Add a clip to the end of the timeline"""
        clip.order = len(self.clips)
        self.clips.append(clip)
        self.updated_at = datetime.utcnow()

    def remove_clip(self, clip_index: int) -> Optional[TimelineClip]:
        """Remove a clip by index and reorder remaining clips"""
        if 0 <= clip_index < len(self.clips):
            removed = self.clips.pop(clip_index)
            # Reorder remaining clips
            for i, clip in enumerate(self.clips):
                clip.order = i
            self.updated_at = datetime.utcnow()
            return removed
        return None

    def reorder_clips(self, new_order: List[int]) -> bool:
        """Reorder clips based on new index order"""
        if len(new_order) != len(self.clips):
            return False
        if set(new_order) != set(range(len(self.clips))):
            return False

        self.clips = [self.clips[i] for i in new_order]
        for i, clip in enumerate(self.clips):
            clip.order = i
        self.updated_at = datetime.utcnow()
        return True

    class Config:
        json_schema_extra = {
            "example": {
                "id": "proj-789",
                "name": "Product Demo Highlight",
                "goal": "Create a 60-second highlight reel",
                "clips": [],
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class Export(BaseModel):
    """An export/render job for a project"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique export ID")
    project_id: str = Field(..., description="Associated project ID")
    status: Literal["pending", "processing", "completed", "failed"] = Field(
        "pending", description="Export status"
    )
    progress: int = Field(0, description="Export progress (0-100)", ge=0, le=100)
    output_path: Optional[str] = Field(None, description="Path to rendered video")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    preview_mode: bool = Field(False, description="Whether this is a low-res preview")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "export-abc",
                "project_id": "proj-789",
                "status": "completed",
                "progress": 100,
                "output_path": "/data/exports/proj-789-preview.mp4",
                "preview_mode": True
            }
        }
