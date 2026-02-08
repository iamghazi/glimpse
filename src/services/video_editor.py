"""
Video Editor Service
FFmpeg-based video rendering for timeline assembly
"""
import asyncio
import subprocess
import json
import tempfile
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from src.core.config import settings

logger = logging.getLogger(__name__)


class FFmpegRenderer:
    """
    Renders video timelines using FFmpeg directly

    Uses FFmpeg directly for reliable, cross-platform rendering.
    """

    def __init__(self):
        """Initialize the renderer and verify FFmpeg is available"""
        self._verify_ffmpeg()

    def _verify_ffmpeg(self):
        """Verify FFmpeg is installed"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError("FFmpeg not working properly")
            logger.debug("FFmpeg verified")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg not found. Install with: brew install ffmpeg")

    def generate_spec(
        self,
        clips: List[Dict[str, Any]],
        output_path: str,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
        audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a render specification from timeline clips

        Args:
            clips: List of clip dictionaries with source_path, cut_from, cut_to
            output_path: Path for output video
            width: Output video width
            height: Output video height
            fps: Output frames per second
            audio_path: Optional background audio track

        Returns:
            Render specification dictionary
        """
        return {
            "clips": clips,
            "output_path": output_path,
            "width": width,
            "height": height,
            "fps": fps,
            "audio_path": audio_path
        }

    async def render(
        self,
        spec: Dict[str, Any],
        preview_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Render clips to a single video using FFmpeg concat

        Args:
            spec: Render specification dictionary
            preview_mode: If True, render at lower resolution for speed

        Returns:
            Dictionary with success status, output_path, duration, or error
        """
        clips = spec["clips"]
        output_path = spec["output_path"]

        # Apply preview settings
        if preview_mode:
            width = settings.AGENT_PREVIEW_WIDTH
            height = settings.AGENT_PREVIEW_HEIGHT
        else:
            width = spec.get("width", 1920)
            height = spec.get("height", 1080)

        fps = spec.get("fps", 30)

        logger.info(f"🎬 Rendering video: {output_path}")
        logger.info(f"   Resolution: {width}x{height}")
        logger.info(f"   Clips: {len(clips)}")
        logger.info(f"   Preview mode: {preview_mode}")

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            if len(clips) == 1:
                # Single clip - just trim and resize
                result = await self._render_single_clip(
                    clips[0], output_path, width, height, fps, preview_mode
                )
            else:
                # Multiple clips - use concat filter
                result = await self._render_multiple_clips(
                    clips, output_path, width, height, fps, preview_mode
                )

            if result["success"]:
                duration = await self._get_duration(output_path)
                result["duration"] = duration
                logger.info(f"✅ Render complete: {output_path} ({duration:.1f}s)")

            return result

        except Exception as e:
            logger.error(f"❌ Render error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _render_single_clip(
        self,
        clip: Dict[str, Any],
        output_path: str,
        width: int,
        height: int,
        fps: int,
        fast: bool
    ) -> Dict[str, Any]:
        """Render a single clip with trimming"""
        source = clip["source_path"]
        start = clip["cut_from"]
        end = clip["cut_to"]
        duration = end - start

        # Build FFmpeg command
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", source,
            "-t", str(duration),
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
            "-r", str(fps),
            "-c:v", "libx264",
            "-preset", "ultrafast" if fast else "medium",
            "-crf", "28" if fast else "23",
            "-c:a", "aac",
            "-b:a", "128k",
            output_path
        ]

        return await self._run_ffmpeg(cmd)

    async def _render_multiple_clips(
        self,
        clips: List[Dict[str, Any]],
        output_path: str,
        width: int,
        height: int,
        fps: int,
        fast: bool
    ) -> Dict[str, Any]:
        """Render multiple clips with concat"""
        # Create temporary trimmed clips
        temp_dir = tempfile.mkdtemp(prefix="video_render_")
        temp_clips = []

        try:
            # First, create individual trimmed clips
            for i, clip in enumerate(clips):
                temp_path = os.path.join(temp_dir, f"clip_{i:03d}.mp4")
                source = clip["source_path"]
                start = clip["cut_from"]
                end = clip["cut_to"]
                duration = end - start

                # Trim and normalize each clip
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", str(start),
                    "-i", source,
                    "-t", str(duration),
                    "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps={fps}",
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-crf", "23",
                    "-c:a", "aac",
                    "-ar", "44100",
                    "-ac", "2",
                    "-b:a", "128k",
                    temp_path
                ]

                result = await self._run_ffmpeg(cmd)
                if not result["success"]:
                    return result

                temp_clips.append(temp_path)
                logger.debug(f"   Processed clip {i + 1}/{len(clips)}")

            # Create concat file
            concat_file = os.path.join(temp_dir, "concat.txt")
            with open(concat_file, "w") as f:
                for temp_path in temp_clips:
                    f.write(f"file '{temp_path}'\n")

            # Concatenate all clips
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c:v", "libx264",
                "-preset", "ultrafast" if fast else "medium",
                "-crf", "28" if fast else "23",
                "-c:a", "aac",
                "-b:a", "128k",
                output_path
            ]

            return await self._run_ffmpeg(cmd)

        finally:
            # Cleanup temp files
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    async def _run_ffmpeg(self, cmd: List[str]) -> Dict[str, Any]:
        """Run an FFmpeg command asynchronously"""
        logger.debug(f"Running: {' '.join(cmd[:10])}...")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=settings.AGENT_RENDER_TIMEOUT
            )

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown FFmpeg error"
                # Extract the most relevant error line
                error_lines = [l for l in error_msg.split('\n') if 'error' in l.lower()]
                short_error = error_lines[-1] if error_lines else error_msg[-500:]
                logger.error(f"FFmpeg error: {short_error}")
                return {
                    "success": False,
                    "error": short_error
                }

            return {
                "success": True,
                "output_path": cmd[-1]  # Last arg is output path
            }

        except asyncio.TimeoutError:
            process.kill()
            return {
                "success": False,
                "error": f"Render timed out after {settings.AGENT_RENDER_TIMEOUT} seconds"
            }

    async def _get_duration(self, video_path: str) -> float:
        """Get video duration using ffprobe"""
        try:
            process = await asyncio.create_subprocess_exec(
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                video_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, _ = await process.communicate()
            data = json.loads(stdout.decode())
            return float(data["format"]["duration"])

        except Exception as e:
            logger.warning(f"Failed to get duration: {e}")
            return 0.0


# Convenience function for simple rendering
async def render_timeline(
    clips: List[Dict[str, Any]],
    output_path: str,
    preview: bool = True
) -> Dict[str, Any]:
    """
    Render a timeline to video

    Args:
        clips: List of clip dictionaries
        output_path: Output file path
        preview: Whether to render in preview mode

    Returns:
        Render result dictionary
    """
    renderer = FFmpegRenderer()
    spec = renderer.generate_spec(clips, output_path)
    return await renderer.render(spec, preview_mode=preview)
