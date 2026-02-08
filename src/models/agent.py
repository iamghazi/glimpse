"""
Agent Models
Data models for the autonomous video editing agent
"""
from datetime import datetime
from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel, Field
import uuid


# Agent status type
AgentStatus = Literal["planning", "executing", "evaluating", "complete", "failed"]


class EvaluationResult(BaseModel):
    """Result of evaluating an agent execution"""

    # Hard constraints
    duration_ok: bool = Field(..., description="Whether duration is within tolerance")
    target_duration: float = Field(..., description="Target duration in seconds")
    actual_duration: float = Field(..., description="Actual rendered duration in seconds")
    render_success: bool = Field(..., description="Whether render completed successfully")

    # Soft metrics
    clip_count: int = Field(..., description="Number of clips in timeline", ge=0)

    # Decision
    satisfied: bool = Field(..., description="Whether all constraints are met")
    refinements: List[str] = Field(
        default_factory=list,
        description="List of suggested refinements if not satisfied"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "duration_ok": True,
                "target_duration": 60.0,
                "actual_duration": 58.5,
                "render_success": True,
                "clip_count": 4,
                "satisfied": True,
                "refinements": []
            }
        }


class PlanStep(BaseModel):
    """A single step in an agent execution plan"""

    tool: str = Field(..., description="Tool name to execute")
    params: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    description: Optional[str] = Field(None, description="Human-readable step description")
    executed: bool = Field(False, description="Whether this step has been executed")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result")


class AgentPlan(BaseModel):
    """Execution plan created by the planner"""

    steps: List[PlanStep] = Field(default_factory=list, description="Ordered list of steps")
    reasoning: Optional[str] = Field(None, description="Planner's reasoning for this plan")


class ExecutionResult(BaseModel):
    """Result of executing an agent plan"""

    success: bool = Field(..., description="Whether execution succeeded")
    project_id: Optional[str] = Field(None, description="Created/updated project ID")
    preview_path: Optional[str] = Field(None, description="Path to rendered preview")
    duration: Optional[float] = Field(None, description="Rendered video duration")
    clip_count: int = Field(0, description="Number of clips in timeline")
    error: Optional[str] = Field(None, description="Error message if failed")
    tool_results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Results from individual tool executions"
    )


class AgentSession(BaseModel):
    """A complete agent editing session"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique session ID")
    project_id: str = Field("", description="Associated project ID (set after creation)")
    user_request: str = Field(..., description="Original user request")

    # State
    iteration: int = Field(0, description="Current iteration (1-indexed when running)")
    max_iterations: int = Field(5, description="Maximum allowed iterations")
    status: AgentStatus = Field("planning", description="Current agent status")

    # Plan & Results
    current_plan: Optional[AgentPlan] = Field(None, description="Current execution plan")
    execution_results: List[ExecutionResult] = Field(
        default_factory=list,
        description="Results from each iteration"
    )
    evaluation_results: List[EvaluationResult] = Field(
        default_factory=list,
        description="Evaluation results from each iteration"
    )

    # Output
    preview_path: Optional[str] = Field(None, description="Path to latest preview")
    final_output_path: Optional[str] = Field(None, description="Path to final rendered video")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None)

    @property
    def is_active(self) -> bool:
        """Whether the session is still running"""
        return self.status in ("planning", "executing", "evaluating")

    @property
    def latest_evaluation(self) -> Optional[EvaluationResult]:
        """Get the most recent evaluation result"""
        return self.evaluation_results[-1] if self.evaluation_results else None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "session-123",
                "project_id": "proj-456",
                "user_request": "Create a 60-second highlight reel",
                "iteration": 1,
                "max_iterations": 5,
                "status": "executing",
                "preview_path": None,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }


# API Request/Response Models

class EditRequest(BaseModel):
    """Request to start an autonomous edit session"""

    request: str = Field(..., description="Natural language editing request", min_length=10)

    class Config:
        json_schema_extra = {
            "example": {
                "request": "Create a 60-second highlight reel of product demos with smooth transitions"
            }
        }


class EditResponse(BaseModel):
    """Response from an edit session"""

    session_id: str = Field(..., description="Session ID for tracking")
    status: AgentStatus = Field(..., description="Current session status")
    preview_path: Optional[str] = Field(None, description="Path to preview video")
    iterations: int = Field(..., description="Number of iterations completed")
    message: str = Field(..., description="Human-readable status message")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session-123",
                "status": "complete",
                "preview_path": "/data/exports/session-123-preview.mp4",
                "iterations": 2,
                "message": "Edit completed after 2 iterations"
            }
        }


class FeedbackRequest(BaseModel):
    """Request to provide feedback for refinement"""

    feedback: str = Field(..., description="User feedback for refinement", min_length=5)

    class Config:
        json_schema_extra = {
            "example": {
                "feedback": "The video is too long, please trim 15 seconds from the middle section"
            }
        }


class ApproveResponse(BaseModel):
    """Response from approving a session"""

    success: bool = Field(..., description="Whether final render succeeded")
    output_path: Optional[str] = Field(None, description="Path to final video")
    message: str = Field(..., description="Status message")
