"""
Chat Handler Module
Handles chat with video clips using Gemini context caching
Phase 3.9: Multi-clip chat with selective caching
"""
import os
from pathlib import Path
from typing import Optional
from google import genai
from google.genai import types
from datetime import datetime
from dotenv import load_dotenv
import json

load_dotenv()


class ChatHandler:
    """Handles chat sessions with video clips using context caching"""

    def __init__(self):
        self.gcp_project_id = os.getenv("GCP_PROJECT_ID")
        self.gcp_location = os.getenv("GCP_LOCATION", "us-central1")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        self.metadata_dir = Path(os.getenv("METADATA_DIR", "./metadata"))

        # Initialize Gemini client with Vertex AI
        self.client = genai.Client(
            vertexai=True,
            project=self.gcp_project_id,
            location=self.gcp_location
        )

        # Cache TTL (1 hour as per spec)
        self.cache_ttl_seconds = 3600

    def load_chunk_data(self, chunk_id: str) -> Optional[dict]:
        """Load chunk data from metadata"""
        # Extract video_id from chunk_id (format: vid_XXX_start_end)
        video_id = "_".join(chunk_id.split("_")[:2])

        chunks_file = self.metadata_dir / f"{video_id}_chunks.json"
        if not chunks_file.exists():
            return None

        with open(chunks_file, "r") as f:
            chunks = json.load(f)

        for chunk in chunks:
            if chunk.get("chunk_id") == chunk_id:
                return chunk

        return None

    def prepare_context_for_clips(self, chunk_ids: list[str]) -> list[types.Part]:
        """
        Prepare context parts for selected clips
        Includes frames, visual descriptions, and transcripts
        """
        context_parts = []

        for chunk_id in chunk_ids:
            chunk_data = self.load_chunk_data(chunk_id)
            if not chunk_data:
                continue

            # Add chunk header
            header_text = f"\n=== Clip: {chunk_id} ===\nTime range: {chunk_data['start_time']:.1f}s - {chunk_data['end_time']:.1f}s\n"
            context_parts.append(types.Part.from_text(text=header_text))

            # Add visual description
            if chunk_data.get("visual_description"):
                visual_text = f"Visual description: {chunk_data['visual_description']}\n"
                context_parts.append(types.Part.from_text(text=visual_text))

            # Add audio transcript
            if chunk_data.get("audio_transcript"):
                audio_text = f"Audio transcript: {chunk_data['audio_transcript']}\n"
                context_parts.append(types.Part.from_text(text=audio_text))

            # Add representative frame
            frame_path = chunk_data.get("representative_frame")
            if frame_path and Path(frame_path).exists():
                with open(frame_path, "rb") as f:
                    image_data = f.read()
                context_parts.append(
                    types.Part.from_bytes(
                        data=image_data,
                        mime_type="image/jpeg"
                    )
                )

        return context_parts

    def chat_with_clips(
        self,
        chunk_ids: list[str],
        question: str,
        cache_name: Optional[str] = None
    ) -> dict:
        """
        Chat with selected video clips using context caching

        Returns:
            dict with answer, sources, cache_info
        """
        try:
            # Prepare context from clips
            context_parts = self.prepare_context_for_clips(chunk_ids)

            if not context_parts:
                return {
                    "answer": "No clips found. Please select some clips first.",
                    "sources": [],
                    "cache_info": {"cache_hit": False}
                }

            # Add system prompt
            system_text = ("You are analyzing video clips. Answer questions about the content based on "
                          "the visual descriptions, audio transcripts, and frames provided. "
                          "When referencing specific information, mention which clip and approximate timestamp it came from.")
            system_prompt = types.Part.from_text(text=system_text)

            # Check if we should use caching
            # Context caching is beneficial when context > 32k tokens
            # For now, we'll use it if we have multiple clips
            use_caching = len(chunk_ids) > 1

            if use_caching:
                # Create or retrieve cached content
                cache_config = types.CachedContent(
                    model=self.gemini_model,
                    contents=[system_prompt] + context_parts,
                    ttl=f"{self.cache_ttl_seconds}s",
                    display_name=cache_name or f"clips_{'_'.join(chunk_ids[:3])}"
                )

                # Note: In production, you'd check if cache exists and reuse it
                # For now, we create a new cache each time
                # The actual caching happens on Gemini's side

                # Generate response with cached context
                response = self.client.models.generate_content(
                    model=self.gemini_model,
                    contents=[question],
                    config=types.GenerateContentConfig(
                        cached_content=cache_config,
                        temperature=0.7,
                    )
                )

                cache_info = {
                    "cache_hit": False,  # First question always creates cache
                    "cache_name": cache_name or f"clips_{'_'.join(chunk_ids[:3])}",
                    "cached_clips": len(chunk_ids)
                }

            else:
                # Single clip - no caching needed
                question_part = types.Part.from_text(text=question)
                response = self.client.models.generate_content(
                    model=self.gemini_model,
                    contents=[system_prompt] + context_parts + [question_part],
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                    )
                )

                cache_info = {
                    "cache_hit": False,
                    "cache_used": False,
                    "reason": "Single clip - caching not beneficial"
                }

            answer = response.text

            # Extract sources (chunk IDs mentioned in context)
            sources = [f"{chunk_id}" for chunk_id in chunk_ids]

            return {
                "answer": answer,
                "sources": sources,
                "cache_info": cache_info,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            print(f"Chat error: {e}")
            return {
                "answer": f"Error generating response: {str(e)}",
                "sources": [],
                "cache_info": {"error": str(e)}
            }


# Standalone function for easy import
def chat_with_video_clips(chunk_ids: list[str], question: str) -> dict:
    """
    Chat with video clips - convenience function
    """
    handler = ChatHandler()
    return handler.chat_with_clips(chunk_ids, question)
