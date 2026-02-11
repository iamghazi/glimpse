"""
Search Service
Orchestrates 3-tier cascaded search for video chunks
"""
import logging
from typing import Optional

from src.core.config import settings
from src.models.search import SearchResult
from src.embeddings.service import EmbeddingGenerator
from src.search.vector_db import VideoVectorDB
from src.search.reranker import TextReranker, MultimodalReranker

logger = logging.getLogger(__name__)


def search_videos(
    query: str,
    top_k: int = 5,
    video_id_filter: Optional[str] = None,
    score_threshold: float = 0.3,
    use_cascaded_reranking: bool = True,
    tier1_candidates: int = 50,
    confidence_threshold: float = 0.8,
) -> list[SearchResult]:
    """
    Three-tier cascaded reranking search for maximum precision

    TIER 1: Hybrid Retrieval with RRF (Fetch Top 50 candidates)
    TIER 2: Text-Only Reranking with Gemini Flash (Filter to Top 5)
    TIER 3: Multimodal Reranking with frames + Gemini (Final precision ranking)

    Uses RRF to combine rankings from text and visual searches, finding chunks that
    rank high in BOTH dimensions. Then progressively refines with LLM reranking.

    Automatically determines whether the query is text-heavy (emotions, interactions)
    or visual-heavy (colors, objects) and weights the embeddings accordingly.

    Args:
        query: Natural language search query
        top_k: Number of final results to return (default 5)
        video_id_filter: Optional video ID to search within
        score_threshold: Minimum similarity score for Tier 1 RRF (0.0-1.0, default 0.3)
        use_cascaded_reranking: Enable Tiers 2 & 3 for higher precision (default True)
        tier1_candidates: Number of candidates to fetch from vector search (default 50)
        confidence_threshold: Minimum confidence score for final results (0.0-1.0, default 0.8)
                            Only clips with confidence >= 0.8 are returned as "winners"

    Examples:
        "man flirts with woman" → 80% text weight (social interaction)
        "red car on street" → 80% visual weight (colors, objects)
        "woman picks up paper" → 50/50 balance (action + object)

    Returns:
        List of SearchResult objects ranked by relevance
    """
    # Initialize components
    embedding_generator = EmbeddingGenerator()

    # === TIER 1: Hybrid Retrieval with RRF ===
    logger.info("🔍 Tier 1: Hybrid Retrieval with RRF")

    # Analyze query to determine optimal weights
    text_weight, visual_weight = embedding_generator.analyze_query_weights(query)
    logger.info(f"Query weights: text={text_weight:.1%}, visual={visual_weight:.1%}")

    # Generate BOTH text and visual query embeddings
    (
        text_embedding,
        visual_embedding,
    ) = embedding_generator.generate_dual_query_embeddings(query)

    # Search using dual embeddings with RRF and intelligent weights
    tier1_results = embedding_generator.vector_db.search_dual(
        text_query_embedding=text_embedding,
        visual_query_embedding=visual_embedding,
        text_weight=text_weight,
        visual_weight=visual_weight,
        top_k=tier1_candidates,  # Fetch more candidates
        video_id_filter=video_id_filter,
        score_threshold=score_threshold,
        tier1_candidates=tier1_candidates,
    )

    logger.info(f"✅ Retrieved {len(tier1_results)} candidates")

    # If cascaded reranking disabled, return Tier 1 results
    if not use_cascaded_reranking:
        logger.warning("Cascaded reranking disabled - returning Tier 1 results")
        return tier1_results[:top_k]

    # === TIER 2: Text-Only Reranking ===
    logger.info("🔍 Tier 2: Text-Only Reranking")

    text_reranker = TextReranker()
    tier2_results = text_reranker.rerank(
        query=query, candidates=tier1_results, top_k=5  # Filter to Top 5
    )

    logger.info(f"✅ Filtered to {len(tier2_results)} high-confidence candidates")

    # If only 1 result, skip Tier 3
    if len(tier2_results) <= 1:
        logger.info("Only 1 candidate - skipping Tier 3")
        return tier2_results[:top_k]

    # === TIER 3: Multimodal Reranking ===
    logger.info("🔍 Tier 3: Multimodal Reranking with Video Frames")

    multimodal_reranker = MultimodalReranker()
    final_results = multimodal_reranker.rerank(query=query, candidates=tier2_results)

    logger.info("✅ Final ranking complete")

    # === FINAL FILTERING: Apply confidence threshold ===
    # Sort by score (descending) - should already be sorted, but ensure it
    final_results.sort(key=lambda x: x.score, reverse=True)

    # Detect whether reranking actually updated scores.
    # RRF fusion scores are always < 0.1; LLM confidence scores are 0.0-1.0.
    # If the best score is still in the RRF range, both rerankers fell back
    # and applying a confidence threshold would incorrectly discard everything.
    best_score = final_results[0].score if final_results else 0.0
    reranking_applied = best_score >= 0.1

    if not reranking_applied and final_results:
        logger.warning(
            "Reranking tiers fell back — returning top Tier 1 results "
            "without confidence filtering"
        )
        return final_results[:top_k]

    # Filter to only high-confidence results (>= threshold)
    high_confidence_results = [
        r for r in final_results if r.score >= confidence_threshold
    ]

    logger.info(
        f"🎯 Found {len(high_confidence_results)} winners with confidence >= {confidence_threshold:.0%}"
    )

    if len(high_confidence_results) == 0:
        logger.warning(
            f"No results meet confidence threshold {confidence_threshold:.0%}"
        )
        if final_results:
            logger.info(f"Best score was {final_results[0].score:.3f}")

    return high_confidence_results[:top_k]
