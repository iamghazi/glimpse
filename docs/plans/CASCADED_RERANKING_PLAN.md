# Cascaded Reranking Implementation Plan

## Overview
Three-tier funnel to progressively refine search results from Top 50 → Top 5 → Final Top 1-3

---

## Tier 1: Hybrid Retrieval with RRF

### Current State
- ✅ Dual embeddings (text + visual)
- ✅ Weighted scoring
- ⚠️ Issue: Weighted average can miss clips relevant in both dimensions

### Changes Needed

1. **Implement Reciprocal Rank Fusion (RRF)**
   - File: `vector_db.py` - `search_dual()` method
   - Replace weighted average with RRF formula:
     ```
     RRF_score = Σ (1 / (k + rank_i))
     where k = 60 (typical constant)
     ```
   - This ranks clips higher if they appear high in BOTH rankings

2. **Fetch Top 50 instead of Top 5**
   - Increase initial retrieval limit
   - Keep computational cost low (just vector search)

**Files to modify:**
- `vector_db.py`: Update `search_dual()` to use RRF
- `embeddings.py`: Update `search_videos()` to fetch Top 50 initially

**Estimated effort:** 30 minutes

---

## Tier 2: "Cheap" Text-Only Reranking

### Purpose
Filter Top 50 → Top 5 using LLM reasoning on text metadata only

### Implementation

1. **Create Reranker Module**
   - New file: `reranker.py`
   - Class: `TextReranker`

2. **Input Data**
   - For each of Top 50 clips:
     - `visual_description` (already generated)
     - `audio_transcript` (already generated)
     - `chunk_id`, `start_time`, `end_time`

3. **LLM Strategy**
   - **Option A: Cross-Encoder** (Recommended)
     - Use a small cross-encoder model (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2`)
     - Score each (query, clip_text) pair
     - Fast, cheap, runs locally

   - **Option B: Gemini Flash**
     - Send batch prompt with all 50 clips
     - Ask model to rank by relevance
     - Format: JSON output with scores

4. **Batch Processing**
   - Send all 50 at once to minimize API calls
   - Prompt template:
     ```
     Query: "{query}"

     Rank these 50 clips by relevance (0-10 scale):

     Clip 1: {visual_desc} | {audio}
     Clip 2: {visual_desc} | {audio}
     ...

     Output JSON: [{"clip_id": 1, "score": 8.5}, ...]
     ```

5. **Output**
   - Top 5 clips with highest text-reranking scores
   - Preserve original vector scores for reference

**Files to create:**
- `reranker.py`: Main reranking logic
- `prompts/text_rerank_prompt.txt`: Prompt template

**Dependencies:**
- Cross-encoder: `sentence-transformers` (if using Option A)
- Or use existing Gemini client

**Estimated effort:** 1-2 hours

---

## Tier 3: "Quality" Multimodal Reranking

### Purpose
Final precision ranking on Top 5 using actual video frames + Gemini 2.5 Flash

### Implementation

1. **Frame Extraction**
   - For each Top 5 clip, load representative frames
   - Use existing `frame_paths` from metadata
   - Sample: 3-5 frames evenly distributed across clip

2. **Multimodal Prompt**
   - Send frames + query to Gemini 2.5 Flash
   - Prompt template:
     ```
     I have 5 clips that might answer: "{query}"

     Look at the frames of these 5 clips and tell me which one
     actually shows the event and explain why.

     Clip 1 ({start}-{end}s):
     [Frame 1] [Frame 2] [Frame 3]
     Visual Summary: {visual_desc}
     Audio: {transcript}

     Clip 2 ({start}-{end}s):
     ...

     Output JSON:
     {
       "ranked_clips": [
         {"clip_id": "X", "confidence": 0.95, "reasoning": "..."},
         ...
       ],
       "best_match": "clip_id_X"
     }
     ```

3. **Gemini API Call**
   - Use `gemini-2.5-flash` model
   - Include actual image frames
   - Parse JSON response

4. **Final Output**
   - Re-ranked Top 5 (or fewer)
   - Confidence scores (0-1.0)
   - Reasoning for each ranking
   - Best match highlighted

**Files to modify/create:**
- `reranker.py`: Add `MultimodalReranker` class
- `prompts/multimodal_rerank_prompt.txt`: Prompt template
- Update `search_videos()` to optionally use 3-tier pipeline

**Estimated effort:** 2-3 hours

---

## Integration: Updated Search Flow

### New `search_videos()` Function

```python
def search_videos(
    query: str,
    top_k: int = 5,
    use_cascaded_reranking: bool = True,
    tier1_candidates: int = 50,
) -> list[SearchResult]:
    """
    Three-tier cascaded reranking search
    """
    # TIER 1: Hybrid Retrieval with RRF (Top 50)
    tier1_results = _tier1_hybrid_retrieval(query, top_k=tier1_candidates)

    if not use_cascaded_reranking:
        return tier1_results[:top_k]

    # TIER 2: Text-Only Reranking (Top 50 → Top 5)
    tier2_results = _tier2_text_reranking(query, tier1_results, top_k=5)

    # TIER 3: Multimodal Reranking (Top 5 → Final ranked)
    final_results = _tier3_multimodal_reranking(query, tier2_results)

    return final_results[:top_k]
```

---

## File Structure

```
video-analyser/
├── embeddings.py          # Update search_videos()
├── vector_db.py           # Update search_dual() with RRF
├── reranker.py            # NEW: Tier 2 & 3 logic
├── prompts/
│   ├── text_rerank_prompt.txt      # NEW
│   └── multimodal_rerank_prompt.txt # NEW
└── .env                   # Add RERANKING_ENABLED=true
```

---

## Configuration (.env)

```bash
# Cascaded Reranking Settings
RERANKING_ENABLED=true
TIER1_CANDIDATES=50       # Top N from vector search
TIER2_MODEL=gemini-flash  # or "cross-encoder"
TIER3_FRAMES_PER_CLIP=5   # Frames to send to Gemini
```

---

## Testing Strategy

1. **Test Tier 1 RRF**
   - Compare RRF vs weighted average scores
   - Verify clips relevant in both dimensions rank higher

2. **Test Tier 2 Text Reranking**
   - Mock 50 clips with known relevance
   - Verify Top 5 selection accuracy

3. **Test Tier 3 Multimodal**
   - Test with 5 clips, ensure best match selected
   - Verify reasoning quality

4. **End-to-End Test**
   - Query: "man flirts with a woman"
   - Expected: High precision (90%+) final result

---

## Expected Performance Improvements

### Current System
- Top 1 accuracy: ~66% (score 0.661)
- Sometimes relevant clips ranked lower

### After Cascaded Reranking
- **Tier 1 (RRF)**: Better initial ranking (clips good in both dimensions)
- **Tier 2**: Filters out 90% of irrelevant clips cheaply
- **Tier 3**: Final precision ranking with visual verification
- **Expected Top 1 accuracy: 90%+**

### Cost Analysis
- Tier 1: ~$0.001 per search (existing embeddings)
- Tier 2: ~$0.002 per search (text-only LLM on 50 clips)
- Tier 3: ~$0.01 per search (5 clips × 5 frames to Gemini Flash)
- **Total: ~$0.013 per search** (still very affordable)

---

## Implementation Order

1. **Phase 1: RRF (30 min)**
   - Implement RRF in `search_dual()`
   - Test improvement over weighted average

2. **Phase 2: Text Reranker (1-2 hours)**
   - Create `reranker.py`
   - Implement Tier 2 with Gemini Flash or Cross-Encoder
   - Test Top 50 → Top 5 filtering

3. **Phase 3: Multimodal Reranker (2-3 hours)**
   - Implement Tier 3 with frame extraction
   - Create multimodal prompt
   - Test final precision ranking

4. **Phase 4: Integration (1 hour)**
   - Wire all tiers together in `search_videos()`
   - Add configuration options
   - End-to-end testing

**Total estimated time: 5-7 hours**

---

## Success Criteria

✅ RRF improves initial ranking
✅ Tier 2 successfully filters to Top 5
✅ Tier 3 achieves 90%+ precision
✅ Total search time < 5 seconds
✅ Cost per search < $0.02
✅ Query "man flirts with a woman" returns perfect match as #1 with 90%+ confidence
