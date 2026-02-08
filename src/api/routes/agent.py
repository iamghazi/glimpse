"""
Agent API Routes
Endpoints for the autonomous video editing agent
"""
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import asyncio
import json

from src.models.agent import (
    EditRequest,
    EditResponse,
    FeedbackRequest,
    ApproveResponse,
    AgentSession
)
from src.agent.orchestrator import AgentOrchestrator
from src.agent.state import state_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/edit", response_model=EditResponse)
async def create_edit(request: EditRequest):
    """
    Start an autonomous edit session

    The agent will:
    1. Search for relevant clips based on the request
    2. Build a timeline with appropriate clips
    3. Render a preview
    4. Iterate if necessary to meet goals

    Returns session ID and status for tracking.
    """
    logger.info(f"🎬 Starting edit session: {request.request[:50]}...")

    try:
        orchestrator = AgentOrchestrator()
        session = await orchestrator.run(request.request)

        return EditResponse(
            session_id=session.id,
            status=session.status,
            preview_path=session.preview_path,
            iterations=session.iteration,
            message=f"Edit {'completed' if session.status == 'complete' else 'failed'} after {session.iteration} iteration(s)"
        )

    except Exception as e:
        logger.exception(f"Edit session failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Edit session failed: {str(e)}"
        )


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Get details about an edit session

    Returns full session state including evaluations and preview path.
    """
    session = state_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session.id,
        "project_id": session.project_id,
        "user_request": session.user_request,
        "status": session.status,
        "iteration": session.iteration,
        "max_iterations": session.max_iterations,
        "preview_path": session.preview_path,
        "final_output_path": session.final_output_path,
        "created_at": session.created_at.isoformat(),
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "evaluations": [
            {
                "duration_ok": e.duration_ok,
                "target_duration": e.target_duration,
                "actual_duration": e.actual_duration,
                "render_success": e.render_success,
                "clip_count": e.clip_count,
                "satisfied": e.satisfied,
                "refinements": e.refinements
            }
            for e in session.evaluation_results
        ]
    }


@router.post("/sessions/{session_id}/approve", response_model=ApproveResponse)
async def approve_session(session_id: str):
    """
    Approve the session and render final full-quality video

    Call this after reviewing the preview to export the final video.
    """
    logger.info(f"🎬 Approving session: {session_id}")

    session = state_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status not in ("complete", "evaluating"):
        raise HTTPException(
            status_code=400,
            detail=f"Session not ready for approval (status: {session.status})"
        )

    try:
        orchestrator = AgentOrchestrator()
        output_path = await orchestrator.render_final(session_id)

        return ApproveResponse(
            success=True,
            output_path=output_path,
            message="Final video rendered successfully"
        )

    except Exception as e:
        logger.exception(f"Final render failed: {e}")
        return ApproveResponse(
            success=False,
            output_path=None,
            message=f"Final render failed: {str(e)}"
        )


@router.post("/sessions/{session_id}/feedback", response_model=EditResponse)
async def provide_feedback(session_id: str, request: FeedbackRequest):
    """
    Provide feedback for another iteration

    Use this to refine the edit if the preview doesn't meet expectations.
    """
    logger.info(f"📝 Feedback for session {session_id}: {request.feedback[:50]}...")

    session = state_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.iteration >= session.max_iterations:
        raise HTTPException(
            status_code=400,
            detail="Maximum iterations reached"
        )

    try:
        orchestrator = AgentOrchestrator()
        updated_session = await orchestrator.continue_with_feedback(
            session_id,
            request.feedback
        )

        return EditResponse(
            session_id=updated_session.id,
            status=updated_session.status,
            preview_path=updated_session.preview_path,
            iterations=updated_session.iteration,
            message=f"Refined after feedback (iteration {updated_session.iteration})"
        )

    except Exception as e:
        logger.exception(f"Feedback iteration failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Feedback iteration failed: {str(e)}"
        )


@router.get("/sessions/{session_id}/events")
async def session_events(session_id: str):
    """
    Server-Sent Events stream for session updates

    Subscribe to real-time updates about session progress.
    Events include: status_change, iteration_start, tool_executing, etc.
    """
    session = state_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator():
        """Generate SSE events for session updates"""
        last_status = session.status
        last_iteration = session.iteration

        while True:
            # Reload session to get latest state
            current_session = state_manager.get_session(session_id)
            if not current_session:
                break

            # Check for status change
            if current_session.status != last_status:
                event = {
                    "type": "status_change",
                    "session_id": session_id,
                    "data": {
                        "status": current_session.status,
                        "preview_path": current_session.preview_path
                    }
                }
                yield f"data: {json.dumps(event)}\n\n"
                last_status = current_session.status

            # Check for iteration change
            if current_session.iteration != last_iteration:
                event = {
                    "type": "iteration_start",
                    "session_id": session_id,
                    "data": {
                        "iteration": current_session.iteration
                    }
                }
                yield f"data: {json.dumps(event)}\n\n"
                last_iteration = current_session.iteration

            # Check if session is complete
            if current_session.status in ("complete", "failed"):
                event = {
                    "type": "session_complete",
                    "session_id": session_id,
                    "data": {
                        "status": current_session.status,
                        "preview_path": current_session.preview_path,
                        "message": f"Session {current_session.status}"
                    }
                }
                yield f"data: {json.dumps(event)}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/sessions")
async def list_sessions(limit: int = 20):
    """
    List recent edit sessions

    Returns most recent sessions with basic info.
    """
    sessions = state_manager.list_sessions()[:limit]

    return {
        "count": len(sessions),
        "sessions": [
            {
                "session_id": s.id,
                "user_request": s.user_request[:100],
                "status": s.status,
                "iterations": s.iteration,
                "created_at": s.created_at.isoformat(),
                "has_preview": s.preview_path is not None
            }
            for s in sessions
        ]
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete an edit session

    Removes session data but not exported videos.
    """
    deleted = state_manager.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"success": True, "message": f"Session {session_id} deleted"}
