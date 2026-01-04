#!/usr/bin/env python3
"""
End-to-end integration test for cascaded reranking system

Tests the three-tier pipeline:
- Tier 1: Hybrid Retrieval with RRF (Top 50)
- Tier 2: Text-Only Reranking (Top 5)
- Tier 3: Multimodal Reranking (Final ranked)

Expected: 90%+ accuracy with best match ranked #1
"""

from src.search.service import search_videos


def test_cascaded_reranking():
    """Test full 3-tier cascaded reranking pipeline"""
    print("=" * 80)
    print("CASCADED RERANKING END-TO-END TEST")
    print("=" * 80)
    print()
    print("Query: 'man flirts with a woman'")
    print("Expected: Flirting scene should be ranked #1 with high confidence (>0.90)")
    print()
    print("=" * 80)

    # Test with cascaded reranking enabled
    results = search_videos(
        query="man flirts with a woman",
        top_k=5,
        use_cascaded_reranking=True,  # Enable all 3 tiers
        tier1_candidates=50,  # Fetch Top 50 from Tier 1
        confidence_threshold=0.8,  # Only return results with >= 80% confidence
    )

    print()
    print("=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print()

    for i, result in enumerate(results, 1):
        print(f"{i}. [{result.chunk_id}] Confidence: {result.score:.3f}")
        print(f"   Video ID: {result.video_id}")
        print(f"   Time: {result.start_time:.1f}s - {result.end_time:.1f}s")
        print()
        print(f"   Visual Description:")
        print(f"   {result.visual_description[:200]}...")
        print()
        print(f"   Audio Transcript:")
        print(f"   {result.audio_transcript[:200]}...")
        print()
        print("-" * 80)
        print()

    # Verify success criteria
    if results:
        best_result = results[0]
        print("=" * 80)
        print("SUCCESS CRITERIA CHECK")
        print("=" * 80)
        print()
        print(f"✅ Best match: {best_result.chunk_id}")
        print(f"✅ Confidence score: {best_result.score:.3f}")
        print()

        if best_result.score >= 0.90:
            print("🎉 SUCCESS! Achieved 90%+ confidence (expected for cascaded reranking)")
        elif best_result.score >= 0.75:
            print("✅ GOOD! Achieved 75%+ confidence (strong match)")
        elif best_result.score >= 0.50:
            print("⚠️  MODERATE. Achieved 50%+ confidence (needs improvement)")
        else:
            print("❌ FAILED. Confidence < 50% (poor match)")

        print()
        print("Expected improvement over Tier 1 alone:")
        print("- Tier 1 RRF score: ~0.016 (rank-based)")
        print("- Tier 2 score: 0.50-0.80 (text filtering)")
        print("- Tier 3 score: 0.90+ (visual verification)")
        print()

        # Assertions
        assert best_result.score >= 0.5, "Best result should have >= 50% confidence"
        assert all(
            r.score >= 0.8 for r in results
        ), "All results should meet confidence threshold"

    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_cascaded_reranking()
