"""
Chat Routes
Chat with video clips using Gemini with context caching
"""
import logging

from fastapi import APIRouter, HTTPException

from src.models.chat import ChatWithClipsRequest, ChatWithClipsResponse
from src.chat.service import ChatHandler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=dict)
async def chat(request: ChatWithClipsRequest):
    """
    Chat with selected video clips using Gemini with context caching

    Uses Gemini context caching for efficient multi-turn conversations
    with the same clips. Caching is automatically applied for multiple clips.

    Args:
        request: Chat request with clip IDs and question

    Returns:
        Chat response with answer, sources, and cache info
    """
    try:
        if not request.clip_ids:
            raise HTTPException(status_code=400, detail="No clips selected")

        if not request.query:
            raise HTTPException(status_code=400, detail="No question provided")

        logger.info(
            f"Chat request: {len(request.clip_ids)} clips, query: '{request.query[:50]}...'"
        )

        handler = ChatHandler()
        result = handler.chat_with_clips(
            chunk_ids=request.clip_ids, question=request.query
        )

        logger.info(
            f"Chat completed: {len(result['sources'])} sources "
            f"(cache: {result['cache_info'].get('cache_used', False)})"
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
