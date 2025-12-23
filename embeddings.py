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

load_dotenv()


class EmbeddingGenerator:
    """Generates multimodal embeddings using Vertex AI"""

    def __init__(self):
        self.gcp_project_id = os.getenv("GCP_PROJECT_ID")
        self.gcp_location = os.getenv("GCP_LOCATION", "us-central1")

        # Use multimodal embedding model
        self.embedding_model = "multimodal-embedding-001"

        # Initialize Gemini client with Vertex AI
        self.client = genai.Client(
            vertexai=True,
            project=self.gcp_project_id,
            location=self.gcp_location
        )

        # Initialize vector DB
        self.vector_db = VideoVectorDB()

    def generate_chunk_embedding(
        self,
        chunk_data: dict,
        representative_frame_path: Optional[str] = None
    ) -> list[float]:
        """
        Generate multimodal embedding for a video chunk
        Combines visual (image) and textual (transcript + description) data

        Returns 1408-dimensional embedding vector
        """
        try:
            # Prepare content parts for embedding
            content_parts = []

            # 1. Add representative frame (visual component)
            if representative_frame_path and Path(representative_frame_path).exists():
                with open(representative_frame_path, "rb") as f:
                    image_data = f.read()

                content_parts.append(
                    types.Part.from_bytes(
                        data=image_data,
                        mime_type="image/jpeg"
                    )
                )

            # 2. Add textual components (transcript + visual description)
            text_parts = []

            if chunk_data.get("visual_description"):
                text_parts.append(f"Visual: {chunk_data['visual_description']}")

            if chunk_data.get("audio_transcript"):
                text_parts.append(f"Audio: {chunk_data['audio_transcript']}")

            if text_parts:
                combined_text = " ".join(text_parts)
                content_parts.append(types.Part.from_text(combined_text))

            # If no content, use a placeholder
            if not content_parts:
                content_parts.append(types.Part.from_text("empty video chunk"))

            # Generate embedding using multimodal model
            response = self.client.models.embed_content(
                model=self.embedding_model,
                contents=content_parts
            )

            # Extract embedding vector
            embedding = response.embeddings[0].values

            return embedding

        except Exception as e:
            print(f"Embedding generation error: {e}")
            # Return zero vector as fallback
            return [0.0] * 1408

    def index_video_chunks(self, video_id: str, chunks_metadata_path: str) -> dict:
        """
        Generate embeddings for all chunks and index them in Qdrant

        Returns summary with number of chunks indexed
        """
        print(f"Generating embeddings and indexing chunks for {video_id}...")

        # Load chunk metadata
        with open(chunks_metadata_path, "r") as f:
            chunks = json.load(f)

        # Generate embeddings for each chunk
        chunks_with_embeddings = []

        for i, chunk_data in enumerate(chunks):
            chunk_id = chunk_data["chunk_id"]
            print(f"  [{i+1}/{len(chunks)}] Generating embedding for {chunk_id}...")

            # Generate embedding
            embedding = self.generate_chunk_embedding(
                chunk_data,
                chunk_data.get("representative_frame")
            )

            # Create chunk with embedding
            chunk_with_embedding = {
                **chunk_data,
                "embedding": embedding
            }

            chunks_with_embeddings.append(chunk_with_embedding)

        # Index all chunks in Qdrant
        print(f"  Indexing {len(chunks_with_embeddings)} chunks in Qdrant...")
        self.vector_db.upsert_chunks(chunks_with_embeddings)

        print(f"  ✅ Successfully indexed {len(chunks_with_embeddings)} chunks")

        return {
            "video_id": video_id,
            "num_chunks_indexed": len(chunks_with_embeddings),
            "status": "indexed"
        }

    def generate_query_embedding(self, query_text: str) -> list[float]:
        """
        Generate embedding for a search query (text-only)

        Returns 1408-dimensional embedding vector
        """
        try:
            response = self.client.models.embed_content(
                model=self.embedding_model,
                contents=[types.Part.from_text(query_text)]
            )

            embedding = response.embeddings[0].values
            return embedding

        except Exception as e:
            print(f"Query embedding error: {e}")
            return [0.0] * 1408


# Standalone functions for easy import
def index_video_in_qdrant(video_id: str, chunks_metadata_path: str) -> dict:
    """
    Index a video's chunks in Qdrant - convenience function
    """
    generator = EmbeddingGenerator()
    return generator.index_video_chunks(video_id, chunks_metadata_path)


def search_videos(query: str, top_k: int = 5, video_id_filter: Optional[str] = None) -> list[dict]:
    """
    Search for video chunks using natural language query
    """
    generator = EmbeddingGenerator()

    # Generate query embedding
    query_embedding = generator.generate_query_embedding(query)

    # Search in Qdrant
    results = generator.vector_db.search(
        query_embedding=query_embedding,
        top_k=top_k,
        video_id_filter=video_id_filter
    )

    return results
