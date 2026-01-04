#!/usr/bin/env python3
"""
Integration test for RRF (Reciprocal Rank Fusion) search implementation
"""

from src.search.service import search_videos


def test_rrf_search():
    """Test RRF implementation with real query"""
    # Test query: "man flirts with a woman"
    # This should use RRF with tier1_candidates=50
    print("Testing RRF implementation...")
    print("=" * 60)
    print("Query: 'man flirts with a woman'")
    print("=" * 60)

    results = search_videos(
        query="man flirts with a woman",
        top_k=5,
        tier1_candidates=50,  # Fetch Top 50, then rank with RRF
        use_cascaded_reranking=False,  # Test RRF only (Tier 1)
    )

    print(f"\nFound {len(results)} results:\n")

    for i, result in enumerate(results, 1):
        print(f"{i}. [{result.chunk_id}] Score: {result.score:.4f}")
        print(f"   Video: {result.video_id}")
        print(f"   Time: {result.start_time}s - {result.end_time}s")
        print(f"   Visual: {result.visual_description[:100]}...")
        print(f"   Audio: {result.audio_transcript[:100]}...")
        print()

    print("=" * 60)
    print("RRF Test Complete!")
    print("=" * 60)

    # Basic assertions
    assert len(results) > 0, "Should return at least one result"
    assert all(
        hasattr(r, "score") for r in results
    ), "All results should have scores"


if __name__ == "__main__":
    test_rrf_search()
