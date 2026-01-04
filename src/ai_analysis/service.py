"""
AI Analysis Service
Handles audio transcription and visual scene description
"""
import subprocess
import logging
from pathlib import Path
from typing import Optional

from faster_whisper import WhisperModel
from google import genai
from google.genai import types

from src.core.config import settings
from src.core.exceptions import AIAnalysisError

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """Handles AI-powered analysis of video chunks"""

    def __init__(self):
        self.gcp_project_id = settings.GCP_PROJECT_ID
        self.gcp_location = settings.GCP_LOCATION
        self.gemini_model = settings.GEMINI_MODEL

        # Initialize Gemini client with Vertex AI
        self.gemini_client = genai.Client(
            vertexai=True,
            project=self.gcp_project_id,
            location=self.gcp_location,
        )

        # Initialize Whisper model for transcription
        # Using base model for balance between speed and accuracy
        # Options: tiny, base, small, medium, large-v2, large-v3
        logger.info("Loading Whisper model...")
        self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        logger.info("Whisper model loaded!")

    def extract_audio_from_chunk(
        self, video_path: str, start_time: float, end_time: float, output_path: str
    ) -> str:
        """
        Extract audio segment from video chunk
        Returns path to extracted audio file (WAV format)
        """
        # Use ffmpeg to extract audio segment
        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-ss",
            str(start_time),
            "-to",
            str(end_time),
            "-vn",  # No video
            "-acodec",
            "pcm_s16le",  # WAV format
            "-ar",
            "16000",  # 16kHz sample rate (Whisper requirement)
            "-ac",
            "1",  # Mono
            "-y",  # Overwrite output file
            output_path,
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.debug(f"Extracted audio: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg error: {e.stderr.decode()}")
            raise AIAnalysisError(f"Audio extraction failed: {e}")

    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio using faster-whisper with enhanced conversation context
        Returns formatted transcript with speaker changes, pauses, and sound descriptions
        """
        if not Path(audio_path).exists():
            logger.warning(f"Audio file not found: {audio_path}")
            return ""

        try:
            # Transcribe with faster-whisper
            segments, info = self.whisper_model.transcribe(
                audio_path,
                beam_size=5,
                language="en",  # Set to None for auto-detection
                vad_filter=True,  # Voice activity detection
                word_timestamps=True,  # Get word-level timestamps
            )

            # Build enhanced transcript with conversation context
            transcript_parts = []
            prev_end_time = 0

            for segment in segments:
                # Detect pauses (gaps > 1 second indicate speaker change or pause)
                if segment.start - prev_end_time > 1.0:
                    transcript_parts.append("[pause]")

                # Add the segment text
                text = segment.text.strip()
                if text:
                    transcript_parts.append(text)

                prev_end_time = segment.end

            # Combine transcript
            raw_transcript = " ".join(transcript_parts)

            if not raw_transcript or raw_transcript.strip() == "":
                logger.debug("No speech detected in audio")
                return ""

            # Enhance with Gemini to add conversation/sound context
            enhanced_transcript = self._enhance_transcript_with_context(raw_transcript)

            logger.debug(f"Transcription complete: {len(enhanced_transcript)} chars")
            return enhanced_transcript

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""

    def _enhance_transcript_with_context(self, raw_transcript: str) -> str:
        """
        Enhance transcript with conversation context using Gemini
        Adds speaker identification, conversation flow, and sound descriptions
        """
        try:
            prompt = f"""Analyze this audio transcript and enhance it with conversation context.

Raw transcript:
{raw_transcript}

Provide an enhanced version that includes:
1. Identify likely speaker changes (e.g., "Person A says:", "Person B responds:")
2. Describe the conversation style (casual chat, formal discussion, monologue, etc.)
3. Note any emotional tones (excited, calm, arguing, etc.)
4. Describe background sounds if pauses suggest them (music, traffic, silence, etc.)

Format as a natural description suitable for search. Keep it concise (2-3 sentences max).

Example output format:
"A casual conversation between two people. Person A asks about a watch, Person B explains it was a gift from their grandfather. The tone is nostalgic and friendly."
"""

            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=200,
                ),
            )

            enhanced = response.text.strip()

            # Combine raw transcript with enhanced context
            return f"{enhanced} Transcript: {raw_transcript}"

        except Exception as e:
            logger.warning(f"Transcript enhancement error: {e}")
            # Return raw transcript if enhancement fails
            return raw_transcript

    def describe_frames(self, frame_paths: list[str], chunk_info: dict) -> str:
        """
        Generate visual description of video chunk using Gemini
        Samples frames from the chunk and describes what's happening
        """
        if not frame_paths:
            logger.warning("No frames provided for description")
            return ""

        try:
            # Sample frames evenly across the chunk (max 10 frames for API limits)
            max_frames = 10
            if len(frame_paths) > max_frames:
                step = len(frame_paths) // max_frames
                sampled_frames = frame_paths[::step][:max_frames]
            else:
                sampled_frames = frame_paths

            # Read and encode frames
            frame_parts = []
            for frame_path in sampled_frames:
                if not Path(frame_path).exists():
                    logger.warning(f"Frame not found: {frame_path}")
                    continue

                # Read image
                with open(frame_path, "rb") as f:
                    image_data = f.read()

                # Create image part for Gemini
                frame_parts.append(
                    types.Part.from_bytes(data=image_data, mime_type="image/jpeg")
                )

            if not frame_parts:
                logger.error("No valid frames found for description")
                return ""

            # Create prompt for visual description
            prompt = f"""Analyze these frames from a video clip (duration: {chunk_info['duration']:.1f}s, from {chunk_info['start_time']:.1f}s to {chunk_info['end_time']:.1f}s).

Provide a concise description (2-3 sentences) covering:
1. What is happening in the scene
2. Key objects, people, or actions visible
3. The setting/environment

Be specific and descriptive but concise."""

            # Generate description with Gemini
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model, contents=[prompt] + frame_parts
            )

            description = response.text.strip()
            logger.debug(f"Visual description generated: {len(description)} chars")
            return description

        except Exception as e:
            logger.error(f"Frame description error: {e}")
            return ""

    def analyze_chunk(
        self,
        video_path: str,
        chunk_info: dict,
        frame_paths: list[str],
        temp_dir: Path,
    ) -> dict:
        """
        Perform complete AI analysis on a video chunk
        Returns dict with transcript and visual_description
        """
        chunk_id = chunk_info["chunk_id"]
        start_time = chunk_info["start_time"]
        end_time = chunk_info["end_time"]

        logger.info(f"AI Analysis for {chunk_id}...")

        # 1. Extract and transcribe audio
        logger.debug("Extracting audio...")
        audio_path = temp_dir / f"{chunk_id}_audio.wav"

        try:
            self.extract_audio_from_chunk(
                video_path, start_time, end_time, str(audio_path)
            )

            logger.debug("Transcribing audio...")
            transcript = self.transcribe_audio(str(audio_path))

            # Clean up audio file
            if audio_path.exists():
                audio_path.unlink()

        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            transcript = ""

        # 2. Describe visual content
        logger.debug("Describing visual content...")
        visual_description = self.describe_frames(frame_paths, chunk_info)

        return {
            "audio_transcript": transcript,
            "visual_description": visual_description,
        }


# Standalone function for easy import
def analyze_video_chunk(
    video_path: str, chunk_info: dict, frame_paths: list[str], temp_dir: Path
) -> dict:
    """
    Analyze a video chunk - convenience function
    """
    analyzer = AIAnalyzer()
    return analyzer.analyze_chunk(video_path, chunk_info, frame_paths, temp_dir)
