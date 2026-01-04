"""
Embeddings Module
Generates multimodal embeddings and indexes them in Qdrant
Phase 3.7: Embedding generation + Qdrant indexing
"""
import os
from pathlib import Path
from typing import Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv
from custom_types import VideoChunkWithEmbedding
from vector_db import VideoVectorDB
import json
import vertexai
from vertexai.vision_models import Video, VideoSegmentConfig, MultiModalEmbeddingModel
import time
from google.api_core import exceptions as google_exceptions

load_dotenv()


def retry_with_backoff(func, max_retries=3, initial_delay=1.0):
    """
    Retry a function with exponential backoff for quota/rate limit errors

    Args:
        func: Function to retry (should be a lambda/callable)
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds (doubles each retry)
    """
    delay = initial_delay

    for attempt in range(max_retries + 1):
        try:
            return func()
        except google_exceptions.ResourceExhausted as e:
            # Quota exceeded error
            if attempt < max_retries:
                print(f"    Quota exceeded, retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                print(f"    Max retries reached. Quota error: {e}")
                raise
        except google_exceptions.InvalidArgument as e:
            # Video size limit or other invalid argument - don't retry
            if "excceeds allowed maximum" in str(e):
                print(f"    Video size exceeds limit, using fallback embedding")
                raise
            else:
                raise
        except Exception as e:
            # Other errors - don't retry
            raise

    return None


class EmbeddingGenerator:
    """Generates multimodal embeddings using Vertex AI"""

    def __init__(self):
        self.gcp_project_id = os.getenv("GCP_PROJECT_ID")
        self.gcp_location = os.getenv("GCP_LOCATION", "us-central1")

        # Use multimodal embedding model
        self.embedding_dimensions = 1408  # Maximum dimension for multimodalembedding@001

        # Initialize Vertex AI
        vertexai.init(project=self.gcp_project_id, location=self.gcp_location)

        # Initialize multimodal embedding model (for visual embeddings)
        self.visual_model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")

        # Initialize text embedding model (for semantic understanding)
        # Using gemini-embedding-001 for better semantic understanding
        self.text_dimensions = 3072  # gemini-embedding-001 dimensions (default)

        # Initialize Gemini client
        self.client = genai.Client(
            vertexai=True,
            project=self.gcp_project_id,
            location=self.gcp_location
        )

        # Initialize vector DB
        self.vector_db = VideoVectorDB()

    def generate_dual_embeddings(
        self,
        chunk_data: dict,
        chunk_video_path: Optional[str] = None
    ) -> tuple[list[float], list[float]]:
        """
        Generate BOTH text and visual embeddings for a video chunk

        Returns:
            (text_embedding, visual_embedding) tuple
            - text_embedding: 768-dim semantic embedding from descriptions (text-embedding-005)
            - visual_embedding: 1408-dim visual embedding from video (multimodalembedding@001)
        """
        # Generate text embedding for semantic understanding
        text_embedding = self._generate_text_embedding(chunk_data)

        # Generate visual embedding from video
        visual_embedding = self._generate_visual_embedding(chunk_data, chunk_video_path)

        return text_embedding, visual_embedding

    def _generate_text_embedding(self, chunk_data: dict) -> list[float]:
        """
        Generate text-only embedding for semantic understanding
        Combines visual description + audio transcript

        Returns 768-dimensional embedding (gemini-embedding-001)
        """
        try:
            # Combine all text information
            text_parts = []
            if chunk_data.get("visual_description"):
                text_parts.append(chunk_data["visual_description"])
            if chunk_data.get("audio_transcript"):
                text_parts.append(chunk_data["audio_transcript"])

            combined_text = " ".join(text_parts) if text_parts else "video content"

            # Generate text embedding using Gemini with retry
            result = retry_with_backoff(
                lambda: self.client.models.embed_content(
                    model="gemini-embedding-001",
                    contents=combined_text
                ),
                max_retries=3,
                initial_delay=1.0
            )

            return result.embeddings[0].values

        except Exception as e:
            print(f"Text embedding error: {e}")
            return [0.0] * self.text_dimensions

    def _generate_visual_embedding(
        self,
        chunk_data: dict,
        chunk_video_path: Optional[str] = None
    ) -> list[float]:
        """
        Generate visual embedding from video frames/video file

        Returns 1408-dimensional embedding (multimodalembedding@001)
        """
        try:
            # Prepare audio transcription as contextual text
            # This provides audio context that video embeddings don't capture
            contextual_text = chunk_data.get("audio_transcript", "")

            embedding = None
            use_text_fallback = False

            # Check if video chunk file exists
            if chunk_video_path and Path(chunk_video_path).exists():
                # Configure video segment
                # We'll process the entire chunk (already chunked to 30 seconds)
                start_time = chunk_data.get("start_time", 0)
                end_time = chunk_data.get("end_time", 60)
                duration = end_time - start_time

                # Validate duration - must be at least 1 second for the API
                if duration < 1.0:
                    print(f"      Chunk too short ({duration:.2f}s), using text-only embedding")
                    use_text_fallback = True
                else:
                    # Load video segment
                    video = Video.load_from_file(chunk_video_path)

                    duration = min(duration, 120)  # Max 2 minutes per API docs

                    # Use ceiling to ensure at least 1 second even for short clips
                    import math
                    end_offset = max(1, math.ceil(duration))

                    video_config = VideoSegmentConfig(
                        start_offset_sec=0,  # Start from beginning of chunk file
                        end_offset_sec=end_offset,
                        interval_sec=10  # Generate embedding every 10 seconds (Standard tier)
                    )

                    # Generate video-based visual embedding with audio context (with retry)
                    try:
                        embeddings = retry_with_backoff(
                            lambda: self.visual_model.get_embeddings(
                                video=video,
                                video_segment_config=video_config,
                                contextual_text=contextual_text if contextual_text else None,
                                dimension=self.embedding_dimensions
                            ),
                            max_retries=3,
                            initial_delay=2.0
                        )

                        # Video embeddings returns a list of embeddings (one per interval)
                        # Average them for a comprehensive representation
                        if hasattr(embeddings, 'video_embeddings') and embeddings.video_embeddings:
                            # Extract embedding values from VideoEmbedding objects
                            import numpy as np
                            embedding_values = [emb.embedding for emb in embeddings.video_embeddings]
                            embedding = np.mean(embedding_values, axis=0).tolist()
                        elif hasattr(embeddings, 'text_embedding'):
                            # Fallback to text embedding
                            embedding = embeddings.text_embedding
                        else:
                            # Last resort fallback
                            embedding = [0.0] * self.embedding_dimensions

                    except google_exceptions.InvalidArgument as e:
                        # Video too large - fall back to text-only embedding
                        if "excceeds allowed maximum" in str(e):
                            print(f"      Video chunk too large, falling back to text-only embedding")
                            use_text_fallback = True
                        else:
                            raise
            else:
                use_text_fallback = True

            # Fallback for visual embedding
            if use_text_fallback or embedding is None:
                # Fallback: Text-based visual embedding if video chunk not available
                # Combine visual description + transcript
                text_parts = []
                if chunk_data.get("visual_description"):
                    text_parts.append(chunk_data['visual_description'])
                if contextual_text:
                    text_parts.append(contextual_text)

                combined_text = " ".join(text_parts) if text_parts else "video content"

                # Generate text-only visual embedding with retry
                embeddings = retry_with_backoff(
                    lambda: self.visual_model.get_embeddings(
                        contextual_text=combined_text,
                        dimension=self.embedding_dimensions
                    ),
                    max_retries=3,
                    initial_delay=2.0
                )
                embedding = embeddings.text_embedding

            return embedding

        except Exception as e:
            print(f"Visual embedding generation error: {e}")
            import traceback
            traceback.print_exc()
            # Return zero vector as fallback
            return [0.0] * self.embedding_dimensions

    def _process_single_chunk(self, chunk_data: dict, chunk_index: int, total_chunks: int) -> dict:
        """
        Process a single chunk (generate embeddings) - used for parallel processing

        Returns:
            Chunk data with embeddings added
        """
        chunk_id = chunk_data["chunk_id"]
        print(f"  [{chunk_index+1}/{total_chunks}] Generating dual embeddings for {chunk_id}...")

        try:
            # Generate BOTH text and visual embeddings
            chunk_video_path = chunk_data.get("chunk_video_path")
            text_embedding, visual_embedding = self.generate_dual_embeddings(
                chunk_data,
                chunk_video_path=chunk_video_path
            )

            # Create chunk with both embeddings
            chunk_with_embedding = {
                **chunk_data,
                "text_embedding": text_embedding,
                "visual_embedding": visual_embedding
            }

            print(f"  ✅ [{chunk_index+1}/{total_chunks}] Completed {chunk_id}")
            return chunk_with_embedding

        except Exception as e:
            print(f"  ❌ [{chunk_index+1}/{total_chunks}] Failed {chunk_id}: {e}")
            # Return chunk with zero embeddings as fallback
            return {
                **chunk_data,
                "text_embedding": [0.0] * self.text_dimensions,
                "visual_embedding": [0.0] * self.embedding_dimensions
            }

    def index_video_chunks(self, video_id: str, chunks_metadata_path: str, max_workers: int = 5) -> dict:
        """
        Generate embeddings for all chunks IN PARALLEL and index them in Qdrant

        Args:
            video_id: Video identifier
            chunks_metadata_path: Path to chunks metadata JSON
            max_workers: Maximum number of parallel workers (default 5)

        Returns:
            Summary with number of chunks indexed
        """
        print(f"Generating embeddings and indexing chunks for {video_id}...")
        print(f"  Using {max_workers} parallel workers")

        # Load chunk metadata
        with open(chunks_metadata_path, "r") as f:
            chunks = json.load(f)

        # Process chunks in parallel using ThreadPoolExecutor
        from concurrent.futures import ThreadPoolExecutor, as_completed

        chunks_with_embeddings = [None] * len(chunks)  # Pre-allocate to preserve order

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all chunks for processing
            future_to_index = {
                executor.submit(self._process_single_chunk, chunk_data, i, len(chunks)): i
                for i, chunk_data in enumerate(chunks)
            }

            # Collect results as they complete
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                    chunks_with_embeddings[index] = result
                except Exception as e:
                    print(f"  ❌ Error processing chunk {index}: {e}")
                    # Use fallback chunk
                    chunks_with_embeddings[index] = {
                        **chunks[index],
                        "text_embedding": [0.0] * self.text_dimensions,
                        "visual_embedding": [0.0] * self.embedding_dimensions
                    }

        # Index all chunks in Qdrant with dual embeddings
        print(f"  Indexing {len(chunks_with_embeddings)} chunks in Qdrant...")
        self.vector_db.upsert_chunks_dual(chunks_with_embeddings)

        print(f"  ✅ Successfully indexed {len(chunks_with_embeddings)} chunks")

        return {
            "video_id": video_id,
            "num_chunks_indexed": len(chunks_with_embeddings),
            "status": "indexed"
        }

    def analyze_query_weights(self, query: str) -> tuple[float, float]:
        """
        Analyze query to determine optimal text vs. visual weights

        Returns:
            (text_weight, visual_weight) tuple summing to 1.0

        Examples:
            "man flirts with woman" → (0.8, 0.2) - text-heavy (social interaction)
            "red car on street" → (0.2, 0.8) - visual-heavy (colors, objects)
            "woman picks up paper" → (0.5, 0.5) - balanced (action + object)
        """
        query_lower = query.lower()

        # Text-heavy indicators (emotions, social interactions, abstract concepts)
        text_indicators = [
            'flirt', 'conversation', 'talk', 'discuss', 'argue', 'laugh', 'cry',
            'angry', 'happy', 'sad', 'excited', 'nervous', 'surprised',
            'romantic', 'playful', 'serious', 'funny', 'emotional',
            'meeting', 'interview', 'presentation', 'speech'
        ]

        # Visual-heavy indicators (colors, objects, locations, visual attributes)
        visual_indicators = [
            'red', 'blue', 'green', 'yellow', 'black', 'white', 'color',
            'car', 'bus', 'building', 'tree', 'street', 'park', 'room',
            'wearing', 'holding', 'sitting', 'standing', 'walking', 'running',
            'appearance', 'looks like', 'dressed in', 'background'
        ]

        # Count indicators
        text_count = sum(1 for word in text_indicators if word in query_lower)
        visual_count = sum(1 for word in visual_indicators if word in query_lower)

        # Default balanced weights
        if text_count == 0 and visual_count == 0:
            return (0.6, 0.4)  # Slight text preference for semantic understanding

        # Calculate weights
        total = text_count + visual_count
        text_weight = min(0.9, max(0.1, (text_count / total) if total > 0 else 0.5))
        visual_weight = 1.0 - text_weight

        return (text_weight, visual_weight)

    def generate_dual_query_embeddings(self, query: str) -> tuple[list[float], list[float]]:
        """
        Generate BOTH text and visual embeddings for a search query

        Returns:
            (text_embedding, visual_embedding) tuple
        """
        try:
            # Text embedding using Gemini
            text_result = retry_with_backoff(
                lambda: self.client.models.embed_content(
                    model="gemini-embedding-001",
                    contents=query
                ),
                max_retries=3,
                initial_delay=1.0
            )
            text_embedding = text_result.embeddings[0].values

            # Visual embedding using multimodal model (text-only input for query)
            visual_result = retry_with_backoff(
                lambda: self.visual_model.get_embeddings(
                    contextual_text=query,
                    dimension=self.embedding_dimensions
                ),
                max_retries=3,
                initial_delay=1.0
            )
            visual_embedding = visual_result.text_embedding

            return (text_embedding, visual_embedding)

        except Exception as e:
            print(f"Query embedding error: {e}")
            return ([0.0] * self.text_dimensions, [0.0] * self.embedding_dimensions)


# Standalone functions for easy import
def index_video_in_qdrant(video_id: str, chunks_metadata_path: str, max_workers: Optional[int] = None) -> dict:
    """
    Index a video's chunks in Qdrant with parallel processing - convenience function

    Args:
        video_id: Video identifier
        chunks_metadata_path: Path to chunks metadata JSON
        max_workers: Number of parallel workers (default: from env EMBEDDING_MAX_WORKERS or 5)
    """
    if max_workers is None:
        max_workers = int(os.getenv("EMBEDDING_MAX_WORKERS", "5"))

    generator = EmbeddingGenerator()
    return generator.index_video_chunks(video_id, chunks_metadata_path, max_workers=max_workers)


def search_videos(
    query: str,
    top_k: int = 5,
    video_id_filter: Optional[str] = None,
    score_threshold: float = 0.3,
    use_cascaded_reranking: bool = True,
    tier1_candidates: int = 50,
    confidence_threshold: float = 0.8,
) -> list[dict]:
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
    """
    generator = EmbeddingGenerator()

    # === TIER 1: Hybrid Retrieval with RRF ===
    print(f"\n🔍 Tier 1: Hybrid Retrieval with RRF")

    # Analyze query to determine optimal weights
    text_weight, visual_weight = generator.analyze_query_weights(query)
    print(f"  Query weights: text={text_weight:.1%}, visual={visual_weight:.1%}")

    # Generate BOTH text and visual query embeddings
    text_embedding, visual_embedding = generator.generate_dual_query_embeddings(query)

    # Search using dual embeddings with RRF and intelligent weights
    tier1_results = generator.vector_db.search_dual(
        text_query_embedding=text_embedding,
        visual_query_embedding=visual_embedding,
        text_weight=text_weight,
        visual_weight=visual_weight,
        top_k=tier1_candidates,  # Fetch more candidates
        video_id_filter=video_id_filter,
        score_threshold=score_threshold,
        tier1_candidates=tier1_candidates,
    )

    print(f"  ✅ Retrieved {len(tier1_results)} candidates")

    # If cascaded reranking disabled, return Tier 1 results
    if not use_cascaded_reranking:
        print(f"  ⚠️  Cascaded reranking disabled - returning Tier 1 results")
        return tier1_results[:top_k]

    # === TIER 2: Text-Only Reranking ===
    print(f"\n🔍 Tier 2: Text-Only Reranking")

    from reranker import TextReranker

    text_reranker = TextReranker()
    tier2_results = text_reranker.rerank(
        query=query,
        candidates=tier1_results,
        top_k=5  # Filter to Top 5
    )

    print(f"  ✅ Filtered to {len(tier2_results)} high-confidence candidates")

    # If only 1 result, skip Tier 3
    if len(tier2_results) <= 1:
        print(f"  ⚠️  Only 1 candidate - skipping Tier 3")
        return tier2_results[:top_k]

    # === TIER 3: Multimodal Reranking ===
    print(f"\n🔍 Tier 3: Multimodal Reranking with Video Frames")

    from reranker import MultimodalReranker

    multimodal_reranker = MultimodalReranker()
    final_results = multimodal_reranker.rerank(
        query=query,
        candidates=tier2_results
    )

    print(f"  ✅ Final ranking complete")

    # === FINAL FILTERING: Apply confidence threshold ===
    # Sort by score (descending) - should already be sorted, but ensure it
    final_results.sort(key=lambda x: x.score, reverse=True)

    # Filter to only high-confidence results (>= threshold)
    high_confidence_results = [r for r in final_results if r.score >= confidence_threshold]

    print(f"  🎯 Found {len(high_confidence_results)} winners with confidence >= {confidence_threshold:.0%}")

    if len(high_confidence_results) == 0:
        print(f"  ⚠️  No results meet confidence threshold {confidence_threshold:.0%}")
        print(f"     Best score was {final_results[0].score:.3f}" if final_results else "No results")

    print()

    return high_confidence_results[:top_k]
