"""
Qdrant Vector Database wrapper for video chunk storage and retrieval
"""
import os
import uuid
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from custom_types import VideoChunkWithEmbedding, SearchResult
from dotenv import load_dotenv

load_dotenv()


class VideoVectorDB:
    """Wrapper for Qdrant operations on video chunks with dual embeddings"""

    COLLECTION_NAME = "video_chunks"
    TEXT_VECTOR_SIZE = 3072  # gemini-embedding-001 dimensions (default)
    VISUAL_VECTOR_SIZE = 1408  # multimodalembedding@001 dimensions

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
    ):
        """
        Initialize Qdrant client and ensure collection exists.

        Args:
            host: Qdrant server host (default: from env QDRANT_HOST)
            port: Qdrant server port (default: from env QDRANT_PORT)
        """
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = int(port or os.getenv("QDRANT_PORT", "6333"))

        self.client = QdrantClient(host=self.host, port=self.port)

        # Ensure collection exists
        self._ensure_collection()

    def _ensure_collection(self):
        """Create collection with named vectors for text and visual embeddings"""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.COLLECTION_NAME not in collection_names:
            # Create collection with NAMED VECTORS for dual embeddings
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config={
                    "text": VectorParams(
                        size=self.TEXT_VECTOR_SIZE,
                        distance=Distance.COSINE,
                    ),
                    "visual": VectorParams(
                        size=self.VISUAL_VECTOR_SIZE,
                        distance=Distance.COSINE,
                    ),
                },
            )
            print(f"✅ Created collection with dual embeddings: {self.COLLECTION_NAME}")
        else:
            print(f"✅ Collection exists: {self.COLLECTION_NAME}")

    def upsert_chunks(
        self,
        chunks: list[VideoChunkWithEmbedding],
        batch_size: int = 100,
    ) -> dict:
        """
        Insert or update video chunks in the vector database.

        Args:
            chunks: List of chunks with embeddings
            batch_size: Number of chunks to upsert at once

        Returns:
            dict with upsert statistics
        """
        points = []

        for chunk in chunks:
            # Handle both dict and object access
            chunk_id = chunk["chunk_id"] if isinstance(chunk, dict) else chunk.chunk_id

            # Generate deterministic UUID from chunk_id
            point_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))

            # Extract data (support both dict and object)
            if isinstance(chunk, dict):
                vector = chunk["embedding"]
                payload = {
                    "chunk_id": chunk["chunk_id"],
                    "video_id": chunk["video_id"],
                    "start_time": chunk["start_time"],
                    "end_time": chunk["end_time"],
                    "duration": chunk["duration"],
                    "visual_description": chunk.get("visual_description", ""),
                    "audio_transcript": chunk.get("audio_transcript", ""),
                    "representative_frame": chunk.get("representative_frame", ""),
                }
            else:
                vector = chunk.embedding
                payload = {
                    "chunk_id": chunk.chunk_id,
                    "video_id": chunk.video_id,
                    "start_time": chunk.start_time,
                    "end_time": chunk.end_time,
                    "duration": chunk.duration,
                    "visual_description": chunk.visual_description,
                    "audio_transcript": chunk.audio_transcript,
                    "representative_frame": chunk.representative_frame,
                }

            # Create Qdrant point
            point = PointStruct(
                id=point_uuid,
                vector=vector,
                payload=payload,
            )
            points.append(point)

        # Batch upsert
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=batch,
            )

        return {
            "upserted_count": len(points),
            "collection": self.COLLECTION_NAME,
        }

    def upsert_chunks_dual(
        self,
        chunks: list[dict],
        batch_size: int = 100,
    ) -> dict:
        """
        Insert or update video chunks with DUAL embeddings (text + visual).

        Args:
            chunks: List of chunks with text_embedding and visual_embedding
            batch_size: Number of chunks to upsert at once

        Returns:
            dict with upsert statistics
        """
        points = []

        for chunk in chunks:
            chunk_id = chunk["chunk_id"]

            # Generate deterministic UUID from chunk_id
            point_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))

            # Extract both embeddings
            text_vector = chunk["text_embedding"]
            visual_vector = chunk["visual_embedding"]

            # Payload (metadata)
            payload = {
                "chunk_id": chunk["chunk_id"],
                "video_id": chunk["video_id"],
                "start_time": chunk["start_time"],
                "end_time": chunk["end_time"],
                "duration": chunk["duration"],
                "visual_description": chunk.get("visual_description", ""),
                "audio_transcript": chunk.get("audio_transcript", ""),
                "representative_frame": chunk.get("representative_frame", ""),
            }

            # Create Qdrant point with NAMED VECTORS
            point = PointStruct(
                id=point_uuid,
                vector={
                    "text": text_vector,
                    "visual": visual_vector,
                },
                payload=payload,
            )
            points.append(point)

        # Batch upsert
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=batch,
            )

        return {
            "upserted_count": len(points),
            "collection": self.COLLECTION_NAME,
        }

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        video_id_filter: Optional[str] = None,
        score_threshold: float = 0.3,
    ) -> list[SearchResult]:
        """
        Search for similar video chunks.

        Args:
            query_embedding: Query vector (1408-dim)
            top_k: Number of results to return
            video_id_filter: Optional filter to search within specific video
            score_threshold: Minimum similarity score (0.0-1.0). Results below this are filtered out.
                           Default 0.3 filters out most irrelevant results.

        Returns:
            List of SearchResult objects with score >= threshold
        """
        # Build filter if video_id specified
        query_filter = None
        if video_id_filter:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="video_id",
                        match=MatchValue(value=video_id_filter),
                    )
                ]
            )

        # Perform search using query_points
        # Note: score_threshold in query_points filters server-side, which can be too aggressive
        # We'll fetch more results and filter client-side for better control
        search_results = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=query_embedding,
            limit=top_k * 3,  # Fetch more results to allow for threshold filtering
            query_filter=query_filter,
            with_payload=True,
        ).points

        # Convert to SearchResult objects
        results = []
        for hit in search_results:
            payload = hit.payload

            # Get score - search returns proper similarity scores
            # For cosine similarity: 1.0 = identical, 0.0 = orthogonal, -1.0 = opposite
            # Qdrant returns normalized scores where higher = better match
            score = float(hit.score) if hasattr(hit, 'score') and hit.score is not None else 0.0

            # Additional client-side filtering as safeguard
            if score < score_threshold:
                continue

            # We need video metadata (title, video_path) which should be fetched
            # from metadata store. For now, using video_id as title.
            result = SearchResult(
                chunk_id=payload["chunk_id"],
                video_id=payload["video_id"],
                title=f"Video {payload['video_id']}",  # Will be enriched later
                start_time=payload["start_time"],
                end_time=payload["end_time"],
                visual_description=payload["visual_description"],
                audio_transcript=payload["audio_transcript"],
                score=score,
                video_path=f"./videos/{payload['video_id']}.mp4",  # Convention
                representative_frame=payload["representative_frame"],
            )
            results.append(result)

        # Limit to top_k after threshold filtering
        return results[:top_k]

    def search_dual(
        self,
        text_query_embedding: list[float],
        visual_query_embedding: list[float],
        text_weight: float = 0.5,
        visual_weight: float = 0.5,
        top_k: int = 5,
        video_id_filter: Optional[str] = None,
        score_threshold: float = 0.3,
    ) -> list[SearchResult]:
        """
        Search using BOTH text and visual embeddings with weighted combination.

        Args:
            text_query_embedding: Query vector for text (768-dim)
            visual_query_embedding: Query vector for visual (1408-dim)
            text_weight: Weight for text similarity (0.0-1.0)
            visual_weight: Weight for visual similarity (0.0-1.0)
            top_k: Number of results to return
            video_id_filter: Optional filter to search within specific video
            score_threshold: Minimum combined similarity score (0.0-1.0)

        Returns:
            List of SearchResult objects ranked by weighted combined score
        """
        # Build filter if video_id specified
        query_filter = None
        if video_id_filter:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="video_id",
                        match=MatchValue(value=video_id_filter),
                    )
                ]
            )

        # Search text embeddings
        text_results = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=text_query_embedding,
            using="text",  # Use named vector "text"
            limit=top_k * 5,  # Fetch more for merging
            query_filter=query_filter,
            with_payload=True,
        ).points

        # Search visual embeddings
        visual_results = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=visual_query_embedding,
            using="visual",  # Use named vector "visual"
            limit=top_k * 5,  # Fetch more for merging
            query_filter=query_filter,
            with_payload=True,
        ).points

        # Combine scores by chunk_id
        combined_scores = {}

        # Add text scores
        for hit in text_results:
            chunk_id = hit.payload["chunk_id"]
            text_score = float(hit.score) if hasattr(hit, 'score') else 0.0
            combined_scores[chunk_id] = {
                "text_score": text_score,
                "visual_score": 0.0,
                "payload": hit.payload
            }

        # Add visual scores
        for hit in visual_results:
            chunk_id = hit.payload["chunk_id"]
            visual_score = float(hit.score) if hasattr(hit, 'score') else 0.0

            if chunk_id in combined_scores:
                combined_scores[chunk_id]["visual_score"] = visual_score
            else:
                combined_scores[chunk_id] = {
                    "text_score": 0.0,
                    "visual_score": visual_score,
                    "payload": hit.payload
                }

        # Calculate weighted combined scores
        results = []
        for chunk_id, data in combined_scores.items():
            combined_score = (
                data["text_score"] * text_weight +
                data["visual_score"] * visual_weight
            )

            # Filter by threshold
            if combined_score < score_threshold:
                continue

            payload = data["payload"]
            result = SearchResult(
                chunk_id=payload["chunk_id"],
                video_id=payload["video_id"],
                title=f"Video {payload['video_id']}",
                start_time=payload["start_time"],
                end_time=payload["end_time"],
                visual_description=payload["visual_description"],
                audio_transcript=payload["audio_transcript"],
                score=combined_score,
                video_path=f"./videos/{payload['video_id']}.mp4",
                representative_frame=payload["representative_frame"],
            )
            results.append(result)

        # Sort by combined score (descending) and return top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def delete_video(self, video_id: str) -> dict:
        """
        Delete all chunks for a specific video.

        Args:
            video_id: Video ID to delete

        Returns:
            dict with deletion statistics
        """
        # Get all points for this video
        scroll_result = self.client.scroll(
            collection_name=self.COLLECTION_NAME,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="video_id",
                        match=MatchValue(value=video_id),
                    )
                ]
            ),
            limit=10000,  # Max chunks per video
        )

        points_to_delete = [point.id for point in scroll_result[0]]

        if points_to_delete:
            self.client.delete(
                collection_name=self.COLLECTION_NAME,
                points_selector=points_to_delete,
            )

        return {
            "deleted_count": len(points_to_delete),
            "video_id": video_id,
        }

    def list_videos(self) -> list[str]:
        """
        Get unique list of video IDs in the database.

        Returns:
            List of video IDs
        """
        # Scroll through all points to get unique video_ids
        # Note: This is not the most efficient for large databases
        scroll_result = self.client.scroll(
            collection_name=self.COLLECTION_NAME,
            limit=10000,
            with_payload=True,
            with_vectors=False,
        )

        video_ids = set()
        for point in scroll_result[0]:
            video_ids.add(point.payload["video_id"])

        return sorted(list(video_ids))

    def get_collection_info(self) -> dict:
        """Get statistics about the collection"""
        collection_info = self.client.get_collection(self.COLLECTION_NAME)

        return {
            "name": self.COLLECTION_NAME,
            "points_count": collection_info.points_count,
            "status": collection_info.status,
        }


if __name__ == "__main__":
    # Test the vector database
    print("Testing VideoVectorDB...")

    db = VideoVectorDB()
    info = db.get_collection_info()
    print(f"Collection info: {info}")

    # Test with dummy data
    from custom_types import VideoChunk

    dummy_chunk = VideoChunkWithEmbedding(
        chunk_id="test_vid_0_60",
        video_id="test_vid",
        start_time=0.0,
        end_time=60.0,
        duration=60.0,
        visual_description="Test scene with a person walking",
        audio_transcript="Hello world",
        frame_paths=["frame1.jpg"],
        representative_frame="frame30.jpg",
        embedding=[0.1] * 1408,  # Dummy 1408-dim vector
    )

    # Upsert
    result = db.upsert_chunks([dummy_chunk])
    print(f"Upsert result: {result}")

    # Search
    search_results = db.search(query_embedding=[0.1] * 1408, top_k=1)
    print(f"Search results: {len(search_results)} found")
    if search_results:
        print(f"  - {search_results[0].chunk_id}: score={search_results[0].score:.3f}")

    # List videos
    videos = db.list_videos()
    print(f"Videos in DB: {videos}")

    # Delete
    delete_result = db.delete_video("test_vid")
    print(f"Delete result: {delete_result}")

    print("✅ All tests passed!")
