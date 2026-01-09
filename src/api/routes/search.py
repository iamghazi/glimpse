"""
Search Routes
Video semantic search endpoints
"""
import logging

from fastapi import APIRouter, HTTPException

from src.models.search import SearchQueryRequest, SearchResult
from src.search.service import search_videos

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=dict)
async def search(request: SearchQueryRequest):
    """
    Search for video chunks using natural language query

    Three-tier cascaded search:
    1. Hybrid RRF retrieval (text + visual embeddings)
    2. Text-only LLM reranking
    3. Multimodal LLM reranking with frames

    Args:
        request: Search request with query and parameters

    Returns:
        Ranked search results with confidence scores
    """
    try:
        logger.info(f"Search query: '{request.query}' (top_k={request.top_k})")

        results = search_videos(
            query=request.query,
            top_k=request.top_k,
            video_id_filter=request.video_id_filter,
            score_threshold=request.score_threshold if request.score_threshold is not None else 0.3,
            use_cascaded_reranking=request.use_cascaded_reranking,
            tier1_candidates=request.tier1_candidates if request.tier1_candidates is not None else 50,
            confidence_threshold=request.confidence_threshold,
        )

        # Convert SearchResult objects to dicts for JSON response
        results_dicts = [
            {
                "chunk_id": r.chunk_id,
                "video_id": r.video_id,
                "title": r.title,
                "start_time": r.start_time,
                "end_time": r.end_time,
                "visual_description": r.visual_description,
                "audio_transcript": r.audio_transcript,
                "score": r.score,
                "video_path": r.video_path,
                "representative_frame": r.representative_frame,
            }
            for r in results
        ]

        logger.info(
            f"Search completed: {len(results)} results "
            f"(threshold: {request.confidence_threshold:.0%})"
        )

        return {
            "query": request.query,
            "num_results": len(results),
            "results": results_dicts,
            "config": {
                "score_threshold": request.score_threshold,
                "confidence_threshold": request.confidence_threshold,
                "cascaded_reranking": request.use_cascaded_reranking,
            },
        }

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
