"""
Video Processing Module
Handles video chunking, frame extraction, and metadata extraction
Phase 3.5: Core video processing without AI analysis
"""
import cv2
import os
from pathlib import Path
from typing import Optional
import json
from datetime import datetime
from custom_types import VideoMetadata, VideoChunk
from dotenv import load_dotenv
from ai_analyzer import AIAnalyzer
from embeddings import index_video_in_qdrant

load_dotenv()


class VideoProcessor:
    """Handles video chunking and frame extraction"""

    def __init__(self, enable_ai_analysis: bool = True, enable_indexing: bool = True):
        self.chunk_duration = float(os.getenv("CHUNK_DURATION_SECONDS", "60"))
        self.chunk_overlap = float(os.getenv("CHUNK_OVERLAP_SECONDS", "10"))
        self.frame_fps = float(os.getenv("FRAME_EXTRACTION_FPS", "1"))
        self.frames_dir = Path(os.getenv("FRAMES_DIR", "./frames"))
        self.metadata_dir = Path(os.getenv("METADATA_DIR", "./metadata"))

        # Ensure directories exist
        self.frames_dir.mkdir(exist_ok=True)
        self.metadata_dir.mkdir(exist_ok=True)

        # Initialize AI analyzer if enabled
        self.enable_ai_analysis = enable_ai_analysis
        self.enable_indexing = enable_indexing

        if self.enable_ai_analysis:
            print("Initializing AI analyzer...")
            self.ai_analyzer = AIAnalyzer()
            print("AI analyzer ready!")

    def extract_video_metadata(self, video_path: str) -> dict:
        """
        Extract metadata from video file using OpenCV
        Returns dict with duration, fps, resolution, etc.
        """
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        try:
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # Calculate duration
            duration_seconds = frame_count / fps if fps > 0 else 0

            # Get file size
            file_size_bytes = Path(video_path).stat().st_size
            file_size_mb = file_size_bytes / (1024 * 1024)

            metadata = {
                "duration_seconds": round(duration_seconds, 2),
                "fps": round(fps, 2),
                "resolution": [width, height],
                "frame_count": frame_count,
                "file_size_mb": round(file_size_mb, 2)
            }

            return metadata

        finally:
            cap.release()

    def generate_chunks(self, video_id: str, duration_seconds: float) -> list[dict]:
        """
        Generate chunk definitions based on video duration
        Returns list of chunk info dicts with start/end times
        """
        chunks = []
        current_start = 0.0

        while current_start < duration_seconds:
            # Calculate end time for this chunk
            end_time = min(current_start + self.chunk_duration, duration_seconds)

            # Calculate chunk duration
            chunk_duration_actual = end_time - current_start

            # Skip chunks that are too short (< 1 second) - they cause issues with embedding API
            if chunk_duration_actual < 1.0:
                print(f"    Skipping tiny chunk at {current_start}s (duration: {chunk_duration_actual:.2f}s)")
                break

            # Create chunk info
            chunk_info = {
                "chunk_id": f"{video_id}_{int(current_start)}_{int(end_time)}",
                "video_id": video_id,
                "start_time": round(current_start, 2),
                "end_time": round(end_time, 2),
                "duration": round(chunk_duration_actual, 2)
            }

            chunks.append(chunk_info)

            # Move to next chunk with overlap
            current_start += (self.chunk_duration - self.chunk_overlap)

            # Prevent infinite loop if chunk_duration <= chunk_overlap
            if self.chunk_duration <= self.chunk_overlap:
                break

        return chunks

    def extract_video_chunk(
        self,
        video_path: str,
        chunk_info: dict
    ) -> str:
        """
        Extract video chunk as a separate video file
        Returns path to the chunk video file
        """
        import subprocess

        chunk_id = chunk_info["chunk_id"]
        video_id = chunk_info["video_id"]
        start_time = chunk_info["start_time"]
        end_time = chunk_info["end_time"]

        # Create directory for video chunks
        chunks_dir = self.frames_dir / video_id / "chunks"
        chunks_dir.mkdir(parents=True, exist_ok=True)

        # Output path for chunk video
        chunk_video_path = chunks_dir / f"{chunk_id}.mp4"

        # Extract video chunk using ffmpeg with optimized compression
        # Target: Keep chunks under 20MB for multimodal embedding API
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-ss", str(start_time),
            "-to", str(end_time),
            "-c:v", "libx264",      # Re-encode video
            "-preset", "medium",     # Balanced encoding speed/quality
            "-crf", "28",           # Higher CRF = more compression (18-28 range, 28 is good)
            "-vf", "scale='min(1280,iw)':'min(720,ih)':force_original_aspect_ratio=decrease",  # Max 720p
            "-c:a", "aac",          # Re-encode audio
            "-b:a", "96k",          # Lower audio bitrate (96kbps is sufficient)
            "-movflags", "+faststart",  # Optimize for streaming
            "-y",                   # Overwrite output file
            str(chunk_video_path)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return str(chunk_video_path)
        except subprocess.CalledProcessError as e:
            print(f"ffmpeg error extracting chunk: {e.stderr.decode()}")
            return ""

    def extract_frames_from_chunk(
        self,
        video_path: str,
        chunk_info: dict,
        video_fps: float
    ) -> list[str]:
        """
        Extract frames from a specific chunk at specified FPS
        Returns list of saved frame paths
        """
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        try:
            chunk_id = chunk_info["chunk_id"]
            video_id = chunk_info["video_id"]
            start_time = chunk_info["start_time"]
            end_time = chunk_info["end_time"]

            # Create directory for this video's frames
            video_frames_dir = self.frames_dir / video_id / chunk_id
            video_frames_dir.mkdir(parents=True, exist_ok=True)

            # Calculate frame interval based on desired FPS
            # If video is 30fps and we want 1fps, extract every 30th frame
            frame_interval = int(video_fps / self.frame_fps) if self.frame_fps > 0 else 1

            # Set video position to chunk start
            start_frame = int(start_time * video_fps)
            end_frame = int(end_time * video_fps)

            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

            frame_paths = []
            frame_number = start_frame

            while frame_number < end_frame:
                ret, frame = cap.read()

                if not ret:
                    break

                # Check if this frame should be extracted
                relative_frame = frame_number - start_frame
                if relative_frame % frame_interval == 0:
                    # Calculate timestamp for this frame
                    timestamp = frame_number / video_fps

                    # Save frame
                    frame_filename = f"frame_{int(timestamp * 1000):08d}.jpg"
                    frame_path = video_frames_dir / frame_filename

                    cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                    frame_paths.append(str(frame_path))

                frame_number += 1

            return frame_paths

        finally:
            cap.release()

    def process_video(self, video_id: str, video_path: str, title: str) -> dict:
        """
        Main processing pipeline for a video
        1. Extract metadata
        2. Generate chunks
        3. Extract frames for each chunk
        4. Save chunk metadata

        Returns processing summary
        """
        print(f"Processing video: {video_id}")

        # Step 1: Extract video metadata
        print("  - Extracting video metadata...")
        video_metadata = self.extract_video_metadata(video_path)

        # Update the main video metadata file
        metadata_path = self.metadata_dir / f"{video_id}.json"

        with open(metadata_path, "r") as f:
            existing_metadata = json.load(f)

        existing_metadata.update({
            "duration_seconds": video_metadata["duration_seconds"],
            "fps": video_metadata["fps"],
            "resolution": video_metadata["resolution"]
        })

        with open(metadata_path, "w") as f:
            json.dump(existing_metadata, f, indent=2)

        # Step 2: Generate chunk definitions
        print("  - Generating chunks...")
        chunks = self.generate_chunks(video_id, video_metadata["duration_seconds"])
        print(f"    Generated {len(chunks)} chunks")

        # Step 3: Extract frames and analyze each chunk
        print("  - Extracting frames and analyzing content...")
        processed_chunks = []

        # Create temp directory for audio extraction
        temp_dir = self.frames_dir / video_id / "_temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        for i, chunk_info in enumerate(chunks):
            print(f"    Processing chunk {i+1}/{len(chunks)}: {chunk_info['chunk_id']}")

            # Extract video chunk as separate file
            print(f"      - Extracting video chunk...")
            chunk_video_path = self.extract_video_chunk(video_path, chunk_info)

            # Extract frames
            print(f"      - Extracting frames...")
            frame_paths = self.extract_frames_from_chunk(
                video_path,
                chunk_info,
                video_metadata["fps"]
            )

            # AI Analysis (transcription + visual description)
            if self.enable_ai_analysis:
                print(f"      - Analyzing content (AI)...")
                analysis = self.ai_analyzer.analyze_chunk(
                    video_path,
                    chunk_info,
                    frame_paths,
                    temp_dir
                )
                visual_description = analysis["visual_description"]
                audio_transcript = analysis["audio_transcript"]
            else:
                visual_description = ""
                audio_transcript = ""

            # Create chunk metadata
            chunk_data = {
                "chunk_id": chunk_info["chunk_id"],
                "video_id": video_id,
                "start_time": chunk_info["start_time"],
                "end_time": chunk_info["end_time"],
                "duration": chunk_info["duration"],
                "chunk_video_path": chunk_video_path,  # NEW: path to chunk video file
                "frame_paths": frame_paths,
                "representative_frame": frame_paths[len(frame_paths) // 2] if frame_paths else "",
                "visual_description": visual_description,
                "audio_transcript": audio_transcript,
                "num_frames": len(frame_paths)
            }

            processed_chunks.append(chunk_data)

        # Clean up temp directory
        if temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir)

        # Step 4: Save chunk metadata
        print("  - Saving chunk metadata...")
        chunks_metadata_path = self.metadata_dir / f"{video_id}_chunks.json"

        with open(chunks_metadata_path, "w") as f:
            json.dump(processed_chunks, f, indent=2)

        # Calculate total frames
        total_frames = sum(chunk["num_frames"] for chunk in processed_chunks)

        print(f"Processing complete: {len(chunks)} chunks, {total_frames} frames extracted")

        # Step 5: Generate embeddings and index in Qdrant
        indexing_result = None
        if self.enable_indexing:
            print("  - Generating embeddings and indexing in Qdrant...")
            try:
                indexing_result = index_video_in_qdrant(video_id, str(chunks_metadata_path))
                print(f"  - ✅ Indexed {indexing_result['num_chunks_indexed']} chunks in Qdrant")

                # Update video metadata with indexed_at timestamp
                metadata_path = self.metadata_dir / f"{video_id}.json"
                if metadata_path.exists():
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)

                    metadata["indexed_at"] = datetime.utcnow().isoformat()

                    with open(metadata_path, "w") as f:
                        json.dump(metadata, f, indent=2)

            except Exception as e:
                print(f"  - ⚠️ Indexing failed: {e}")
                indexing_result = {"status": "indexing_failed", "error": str(e)}

        return {
            "video_id": video_id,
            "num_chunks": len(chunks),
            "total_frames": total_frames,
            "chunks_metadata_path": str(chunks_metadata_path),
            "status": "processed",
            "indexing": indexing_result
        }


# Standalone function for easy import
def process_video_file(video_id: str, video_path: str, title: str) -> dict:
    """
    Process a video file - convenience function
    """
    processor = VideoProcessor()
    return processor.process_video(video_id, video_path, title)
