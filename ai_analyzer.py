"""
AI Analyzer Module
Handles audio transcription and visual scene description
Phase 3.6: Transcription with faster-whisper + Scene description with Gemini
"""
import os
from pathlib import Path
from typing import Optional
from faster_whisper import WhisperModel
from google import genai
from google.genai import types
import cv2
import base64
from dotenv import load_dotenv

load_dotenv()


class AIAnalyzer:
    """Handles AI-powered analysis of video chunks"""

    def __init__(self):
        self.gcp_project_id = os.getenv("GCP_PROJECT_ID")
        self.gcp_location = os.getenv("GCP_LOCATION", "us-central1")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

        # Initialize Gemini client with Vertex AI
        self.gemini_client = genai.Client(
            vertexai=True,
            project=self.gcp_project_id,
            location=self.gcp_location
        )

        # Initialize Whisper model for transcription
        # Using base model for balance between speed and accuracy
        # Options: tiny, base, small, medium, large-v2, large-v3
        print("Loading Whisper model...")
        self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        print("Whisper model loaded!")

    def extract_audio_from_chunk(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_path: str
    ) -> str:
        """
        Extract audio segment from video chunk
        Returns path to extracted audio file (WAV format)
        """
        import subprocess

        # Use ffmpeg to extract audio segment
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-ss", str(start_time),
            "-to", str(end_time),
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # WAV format
            "-ar", "16000",  # 16kHz sample rate (Whisper requirement)
            "-ac", "1",  # Mono
            "-y",  # Overwrite output file
            output_path
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"ffmpeg error: {e.stderr.decode()}")
            raise

    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio using faster-whisper
        Returns transcript text
        """
        if not Path(audio_path).exists():
            return ""

        try:
            # Transcribe with faster-whisper
            segments, info = self.whisper_model.transcribe(
                audio_path,
                beam_size=5,
                language="en",  # Set to None for auto-detection
                vad_filter=True,  # Voice activity detection
            )

            # Combine all segments into one transcript
            transcript_parts = []
            for segment in segments:
                transcript_parts.append(segment.text.strip())

            transcript = " ".join(transcript_parts)
            return transcript

        except Exception as e:
            print(f"Transcription error: {e}")
            return ""

    def describe_frames(self, frame_paths: list[str], chunk_info: dict) -> str:
        """
        Generate visual description of video chunk using Gemini
        Samples frames from the chunk and describes what's happening
        """
        if not frame_paths:
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
                    continue

                # Read image
                with open(frame_path, "rb") as f:
                    image_data = f.read()

                # Create image part for Gemini
                frame_parts.append(
                    types.Part.from_bytes(
                        data=image_data,
                        mime_type="image/jpeg"
                    )
                )

            if not frame_parts:
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
                model=self.gemini_model,
                contents=[prompt] + frame_parts
            )

            description = response.text.strip()
            return description

        except Exception as e:
            print(f"Frame description error: {e}")
            return ""

    def analyze_chunk(
        self,
        video_path: str,
        chunk_info: dict,
        frame_paths: list[str],
        temp_dir: Path
    ) -> dict:
        """
        Perform complete AI analysis on a video chunk
        Returns dict with transcript and visual_description
        """
        chunk_id = chunk_info["chunk_id"]
        start_time = chunk_info["start_time"]
        end_time = chunk_info["end_time"]

        print(f"  AI Analysis for {chunk_id}...")

        # 1. Extract and transcribe audio
        print(f"    - Extracting audio...")
        audio_path = temp_dir / f"{chunk_id}_audio.wav"

        try:
            self.extract_audio_from_chunk(
                video_path,
                start_time,
                end_time,
                str(audio_path)
            )

            print(f"    - Transcribing audio...")
            transcript = self.transcribe_audio(str(audio_path))

            # Clean up audio file
            if audio_path.exists():
                audio_path.unlink()

        except Exception as e:
            print(f"    - Audio transcription failed: {e}")
            transcript = ""

        # 2. Describe visual content
        print(f"    - Describing visual content...")
        visual_description = self.describe_frames(frame_paths, chunk_info)

        return {
            "audio_transcript": transcript,
            "visual_description": visual_description
        }


# Standalone function for easy import
def analyze_video_chunk(
    video_path: str,
    chunk_info: dict,
    frame_paths: list[str],
    temp_dir: Path
) -> dict:
    """
    Analyze a video chunk - convenience function
    """
    analyzer = AIAnalyzer()
    return analyzer.analyze_chunk(video_path, chunk_info, frame_paths, temp_dir)
