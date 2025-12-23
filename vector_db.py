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
    """Wrapper for Qdrant operations on video chunks"""

    COLLECTION_NAME = "video_chunks"
    VECTOR_SIZE = 1408  # multimodal-embedding-001 dimensions

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
        """Create collection if it doesn't exist"""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.COLLECTION_NAME not in collection_names:
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
            print(f"✅ Created collection: {self.COLLECTION_NAME}")
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

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        video_id_filter: Optional[str] = None,
    ) -> list[SearchResult]:
        """
        Search for similar video chunks.

        Args:
            query_embedding: Query vector (1408-dim)
            top_k: Number of results to return
            video_id_filter: Optional filter to search within specific video

        Returns:
            List of SearchResult objects
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

        # Perform search
        search_results = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=query_embedding,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        ).points

        # Convert to SearchResult objects
        results = []
        for hit in search_results:
            payload = hit.payload

            # Get score - query_points returns score as a float
            # Score ranges from 0 (dissimilar) to 1 (similar) for cosine similarity
            score = float(hit.score) if hasattr(hit, 'score') and hit.score is not None else 0.0

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

        return results

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
