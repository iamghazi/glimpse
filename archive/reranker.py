"""
Cascaded Reranking System for Video Search

Tier 2: Text-Only Reranking (Top 50 → Top 5)
Tier 3: Multimodal Reranking (Top 5 → Final ranked)
"""

import os
import json
from typing import Optional
from pathlib import Path
from google import genai
from custom_types import SearchResult
from dotenv import load_dotenv

load_dotenv()


class TextReranker:
    """
    Tier 2: Text-Only Reranking with Gemini Flash

    Filters Top 50 candidates from Tier 1 to Top 5 using LLM reasoning
    on text metadata only (visual descriptions + audio transcripts).

    Cost: ~$0.002 per search (cheap, text-only)
    """

    def __init__(self, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize TextReranker with Gemini Flash

        Args:
            model: Gemini model to use (default: gemini-2.0-flash-exp)
        """
        self.gcp_project_id = os.getenv("GCP_PROJECT_ID")
        self.gcp_location = os.getenv("GCP_LOCATION", "us-central1")
        self.model = model

        # Initialize Gemini client
        self.client = genai.Client(
            vertexai=True,
            project=self.gcp_project_id,
            location=self.gcp_location
        )

        # Load prompt template
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load text reranking prompt template"""
        prompt_path = Path("prompts/text_rerank_prompt.txt")

        if prompt_path.exists():
            return prompt_path.read_text()

        # Default prompt if file doesn't exist
        return """You are a video search ranking expert. Your task is to re-rank video clips based on their relevance to a search query.

Query: "{query}"

Below are {num_clips} video clips with their descriptions and audio transcripts. Rank them by relevance to the query on a scale of 0-10.

{clips_text}

Output ONLY a JSON array with scores for each clip, ordered by relevance (highest first). Format:
[
  {{"clip_id": "...", "score": 9.5, "reasoning": "..."}},
  {{"clip_id": "...", "score": 8.0, "reasoning": "..."}},
  ...
]

Return ONLY the top {top_k} most relevant clips. DO NOT include clips that are not relevant to the query."""

    def rerank(
        self,
        query: str,
        candidates: list[SearchResult],
        top_k: int = 5
    ) -> list[SearchResult]:
        """
        Rerank candidates using text-only LLM reasoning

        Args:
            query: User's search query
            candidates: List of candidate clips from Tier 1 (typically 50)
            top_k: Number of top results to return (default 5)

        Returns:
            Top K clips re-ranked by text relevance
        """
        if not candidates:
            return []

        if len(candidates) <= top_k:
            return candidates[:top_k]

        # Format clips for LLM
        clips_text = self._format_clips_for_llm(candidates)

        # Create prompt
        prompt = self.prompt_template.format(
            query=query,
            num_clips=len(candidates),
            clips_text=clips_text,
            top_k=top_k
        )

        # Call Gemini Flash for reranking
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": 0.0,  # Deterministic for ranking
                    "response_mime_type": "application/json"
                }
            )

            # Parse JSON response
            ranked_clips = json.loads(response.text)

            # Map clip IDs back to SearchResult objects
            clip_map = {clip.chunk_id: clip for clip in candidates}
            reranked_results = []

            for ranked_clip in ranked_clips[:top_k]:
                clip_id = ranked_clip["clip_id"]
                if clip_id in clip_map:
                    result = clip_map[clip_id]
                    # Update score with reranking score
                    result.score = ranked_clip["score"] / 10.0  # Normalize to 0-1
                    reranked_results.append(result)

            print(f"  Tier 2: Reranked {len(candidates)} → {len(reranked_results)} clips")
            return reranked_results

        except Exception as e:
            print(f"  ⚠️ Text reranking failed: {e}")
            print(f"     Falling back to top {top_k} from Tier 1")
            return candidates[:top_k]

    def _format_clips_for_llm(self, clips: list[SearchResult]) -> str:
        """Format clips as text for LLM processing"""
        formatted = []

        for i, clip in enumerate(clips, 1):
            clip_text = f"""Clip {i} (ID: {clip.chunk_id}):
  Time: {clip.start_time:.1f}s - {clip.end_time:.1f}s
  Visual Description: {clip.visual_description}
  Audio Transcript: {clip.audio_transcript}
"""
            formatted.append(clip_text)

        return "\n".join(formatted)


class MultimodalReranker:
    """
    Tier 3: Multimodal Reranking with Gemini 2.5 Flash + Video Frames

    Final precision ranking on Top 5 using actual video frames and
    Gemini 2.5 Flash's multimodal capabilities.

    Cost: ~$0.01 per search (5 clips × 5 frames)
    """

    def __init__(self, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize MultimodalReranker

        Args:
            model: Gemini model to use (default: gemini-2.0-flash-exp)
        """
        self.gcp_project_id = os.getenv("GCP_PROJECT_ID")
        self.gcp_location = os.getenv("GCP_LOCATION", "us-central1")
        self.model = model
        self.frames_per_clip = int(os.getenv("TIER3_FRAMES_PER_CLIP", "5"))

        # Initialize Gemini client
        self.client = genai.Client(
            vertexai=True,
            project=self.gcp_project_id,
            location=self.gcp_location
        )

        # Load prompt template
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load multimodal reranking prompt template"""
        prompt_path = Path("prompts/multimodal_rerank_prompt.txt")

        if prompt_path.exists():
            return prompt_path.read_text()

        # Default prompt if file doesn't exist
        return """You are a video search ranking expert with access to actual video frames. Your task is to re-rank video clips based on visual verification.

Query: "{query}"

I have {num_clips} clips that might match this query. Look at the frames from each clip and determine which one actually shows what the user is looking for.

{clips_description}

Based on the VISUAL EVIDENCE from the frames, rank these clips by how well they match the query. Consider:
1. Visual content matching the query
2. Context and setting
3. Actions and events shown
4. Audio transcript alignment with visuals

Output ONLY a JSON object with this format:
{{
  "ranked_clips": [
    {{"clip_id": "...", "confidence": 0.95, "reasoning": "Clearly shows..."}},
    {{"clip_id": "...", "confidence": 0.75, "reasoning": "..."}}
  ],
  "best_match": "clip_id_of_best_match"
}}

Rank ALL {num_clips} clips. The best match should have the highest confidence score (0.0-1.0)."""

    def rerank(
        self,
        query: str,
        candidates: list[SearchResult],
    ) -> list[SearchResult]:
        """
        Rerank candidates using multimodal LLM with video frames

        Args:
            query: User's search query
            candidates: List of candidate clips from Tier 2 (typically 5)

        Returns:
            Clips re-ranked with confidence scores and reasoning
        """
        if not candidates:
            return []

        if len(candidates) == 1:
            return candidates

        # Load frames for each clip
        clips_with_frames = self._load_frames_for_clips(candidates)

        # Create multimodal prompt with frames
        prompt_parts = self._create_multimodal_prompt(query, clips_with_frames)

        # Call Gemini 2.5 Flash for multimodal reranking
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt_parts,
                config={
                    "temperature": 0.0,  # Deterministic for ranking
                    "response_mime_type": "application/json"
                }
            )

            # Parse JSON response
            result = json.loads(response.text)
            ranked_clips = result.get("ranked_clips", [])

            # Map clip IDs back to SearchResult objects
            clip_map = {clip.chunk_id: clip for clip in candidates}
            reranked_results = []

            for ranked_clip in ranked_clips:
                clip_id = ranked_clip["clip_id"]
                if clip_id in clip_map:
                    result_obj = clip_map[clip_id]
                    # Update score with confidence
                    result_obj.score = ranked_clip["confidence"]
                    reranked_results.append(result_obj)

            print(f"  Tier 3: Final ranking complete - Best match: {result.get('best_match', 'N/A')}")
            return reranked_results

        except Exception as e:
            print(f"  ⚠️ Multimodal reranking failed: {e}")
            print(f"     Falling back to Tier 2 results")
            return candidates

    def _load_frames_for_clips(self, clips: list[SearchResult]) -> list[dict]:
        """Load representative frames for each clip"""
        clips_with_frames = []

        for clip in clips:
            # Get frame paths from metadata
            frames_dir = Path(os.getenv("FRAMES_DIR", "./frames"))
            video_frames_dir = frames_dir / clip.video_id

            # Load metadata to get frame paths
            metadata_path = Path(os.getenv("METADATA_DIR", "./metadata")) / f"{clip.video_id}_chunks.json"

            frame_paths = []
            if metadata_path.exists():
                with open(metadata_path) as f:
                    chunks_data = json.load(f)
                    # Find matching chunk
                    for chunk in chunks_data:
                        if chunk["chunk_id"] == clip.chunk_id:
                            # Get evenly distributed frames
                            all_frames = chunk.get("frame_paths", [])
                            if all_frames:
                                # Sample frames evenly
                                step = max(1, len(all_frames) // self.frames_per_clip)
                                frame_paths = all_frames[::step][:self.frames_per_clip]
                            break

            clips_with_frames.append({
                "clip": clip,
                "frame_paths": frame_paths
            })

        return clips_with_frames

    def _create_multimodal_prompt(self, query: str, clips_with_frames: list[dict]) -> list:
        """Create multimodal prompt with text and images"""
        prompt_parts = []

        # Start with text prompt
        clips_description = ""
        for i, item in enumerate(clips_with_frames, 1):
            clip = item["clip"]
            clips_description += f"""
Clip {i} (ID: {clip.chunk_id}):
  Time: {clip.start_time:.1f}s - {clip.end_time:.1f}s
  Visual Summary: {clip.visual_description}
  Audio: {clip.audio_transcript}
  Frames: {len(item['frame_paths'])} frames below
"""

        prompt_text = self.prompt_template.format(
            query=query,
            num_clips=len(clips_with_frames),
            clips_description=clips_description
        )

        prompt_parts.append(prompt_text)

        # Add frames for each clip
        for i, item in enumerate(clips_with_frames, 1):
            prompt_parts.append(f"\n--- Clip {i} Frames ---")

            for frame_path in item["frame_paths"]:
                frame_file = Path(frame_path)
                if frame_file.exists():
                    # Add image to prompt
                    try:
                        import PIL.Image
                        img = PIL.Image.open(frame_file)
                        prompt_parts.append(img)
                    except Exception as e:
                        print(f"    ⚠️ Could not load frame {frame_path}: {e}")

        return prompt_parts


if __name__ == "__main__":
    # Test reranker
    print("Testing TextReranker...")

    # Create mock SearchResult objects
    from custom_types import SearchResult

    mock_candidates = [
        SearchResult(
            chunk_id="test_1",
            video_id="vid_1",
            title="Test Video 1",
            start_time=0.0,
            end_time=30.0,
            visual_description="A man and woman talking flirtatiously",
            audio_transcript="Hi, can I get your number?",
            score=0.016,
            video_path="./videos/vid_1.mp4",
            representative_frame="frame.jpg"
        ),
        SearchResult(
            chunk_id="test_2",
            video_id="vid_2",
            title="Test Video 2",
            start_time=0.0,
            end_time=30.0,
            visual_description="A woman picking up paper",
            audio_transcript="Here's the paper you dropped",
            score=0.015,
            video_path="./videos/vid_2.mp4",
            representative_frame="frame.jpg"
        ),
    ]

    reranker = TextReranker()
    results = reranker.rerank(
        query="man flirts with a woman",
        candidates=mock_candidates,
        top_k=2
    )

    print(f"\nReranked {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.chunk_id} - Score: {result.score:.3f}")

    print("\n✅ TextReranker test complete!")
