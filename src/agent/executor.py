"""
Agent Executor
Executes tool calls from the agent plan
"""
import logging
from typing import Any, Dict, Optional

from src.core.config import settings
from src.models.agent import AgentSession, AgentPlan, ExecutionResult, PlanStep
from src.models.project import Project, TimelineClip
from src.models.search import SearchResult
from src.agent.state import state_manager
from src.search.service import search_videos
from src.search.vector_db import VideoVectorDB

logger = logging.getLogger(__name__)


class AgentExecutor:
    """Executes agent plans by calling tools"""

    def __init__(self):
        self.vector_db = VideoVectorDB()

    def _resolve_params(
        self,
        params: Dict[str, Any],
        step_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve template variables in parameters using previous step results.

        Handles patterns like:
        - {search_clips.clips[0].video_id}
        - {create_project.project_id}
        - {search_clips.results[0].source_path}

        Args:
            params: Parameters that may contain template variables
            step_results: Results from previous steps keyed by tool name

        Returns:
            Resolved parameters with actual values
        """
        import re

        def resolve_value(value: Any) -> Any:
            if not isinstance(value, str):
                return value

            # Pattern: {step_name.path.to.value} or {step_name.array[index].field}
            pattern = r'\{([a-z_]+)\.([^}]+)\}'

            resolved_value = None  # Track the resolved value for type preservation

            def replacer(match):
                nonlocal resolved_value
                step_name = match.group(1)
                path = match.group(2)

                if step_name not in step_results:
                    logger.warning(f"Step result not found: {step_name}")
                    return match.group(0)  # Return original if not found

                result = step_results[step_name]

                # Navigate the path (e.g., "clips[0].video_id" or "project_id")
                try:
                    for part in re.split(r'\.', path):
                        # Handle array access like "clips[0]" or "results[1]"
                        array_match = re.match(r'([a-z_]+)\[(\d+)\]', part)
                        if array_match:
                            key = array_match.group(1)
                            index = int(array_match.group(2))
                            result = result[key][index]
                        else:
                            result = result[part] if isinstance(result, dict) else getattr(result, part)

                    resolved_value = result  # Store for type preservation
                    return str(result) if result is not None else ""
                except (KeyError, IndexError, AttributeError, TypeError) as e:
                    logger.warning(f"Failed to resolve {match.group(0)}: {e}")
                    return match.group(0)

            resolved = re.sub(pattern, replacer, value)

            # If the entire string was a single variable, preserve its original type
            if resolved_value is not None and value.startswith('{') and value.endswith('}') and value.count('{') == 1:
                return resolved_value

            # Try to convert numeric strings to appropriate types
            if resolved != value:  # Something was resolved
                try:
                    if '.' in resolved:
                        return float(resolved)
                    elif resolved.isdigit():
                        return int(resolved)
                except (ValueError, AttributeError):
                    pass

            return resolved

        # Recursively resolve all string values in params
        resolved = {}
        for key, value in params.items():
            if isinstance(value, dict):
                resolved[key] = self._resolve_params(value, step_results)
            elif isinstance(value, list):
                resolved[key] = [resolve_value(v) for v in value]
            else:
                resolved[key] = resolve_value(value)

        return resolved

    def _has_unresolved_placeholders(self, params: Dict[str, Any]) -> bool:
        """Check if any parameters contain unresolved placeholders like {step.path}"""
        import re
        pattern = r'\{[a-z_]+\.[^}]+\}'

        def check_value(value: Any) -> bool:
            if isinstance(value, str):
                return bool(re.search(pattern, value))
            elif isinstance(value, dict):
                return any(check_value(v) for v in value.values())
            elif isinstance(value, list):
                return any(check_value(v) for v in value)
            return False

        return any(check_value(v) for v in params.values())

    async def execute_plan(
        self,
        plan: AgentPlan,
        session: AgentSession
    ) -> ExecutionResult:
        """
        Execute all steps in a plan sequentially

        Args:
            plan: The plan to execute
            session: Current agent session

        Returns:
            ExecutionResult with success status and outputs
        """
        logger.info(f"🚀 Executing plan with {len(plan.steps)} steps")

        result = ExecutionResult(
            success=True,
            clip_count=0,
            tool_results=[]
        )

        project: Optional[Project] = None
        if session.project_id:
            project = state_manager.get_project(session.project_id)

        # Store results from each step for variable substitution
        step_results: Dict[str, Any] = {}

        for i, step in enumerate(plan.steps):
            logger.info(f"📍 Step {i + 1}/{len(plan.steps)}: {step.tool}")

            # Substitute variables in params from previous step results
            resolved_params = self._resolve_params(step.params, step_results)
            logger.debug(f"Params: {resolved_params}")

            # Check for unresolved placeholders (e.g., clips[2] when only 2 clips exist)
            if self._has_unresolved_placeholders(resolved_params):
                logger.warning(f"⚠️ Skipping step {i + 1}: unresolved placeholders in params")
                step.executed = True
                step.result = {"skipped": True, "reason": "unresolved placeholders"}
                result.tool_results.append({
                    "tool": step.tool,
                    "success": True,
                    "skipped": True,
                    "reason": "Referenced data not available (e.g., clip index out of range)"
                })
                continue

            try:
                tool_result = await self._execute_tool(
                    step.tool,
                    resolved_params,
                    project,
                    session
                )

                # Store result for variable substitution in future steps
                step_results[step.tool] = tool_result

                step.executed = True
                step.result = tool_result
                result.tool_results.append({
                    "tool": step.tool,
                    "success": True,
                    "result": tool_result
                })

                # Handle special tool outputs
                if step.tool == "create_project" and tool_result.get("project_id"):
                    result.project_id = tool_result["project_id"]
                    session.project_id = tool_result["project_id"]
                    project = state_manager.get_project(result.project_id)

                if step.tool == "render_preview" and tool_result.get("output_path"):
                    result.preview_path = tool_result["output_path"]
                    result.duration = tool_result.get("duration", 0)

                logger.info(f"✅ Step {i + 1} complete")

            except Exception as e:
                logger.error(f"❌ Step {i + 1} failed: {e}")
                step.executed = True
                step.result = {"error": str(e)}
                result.tool_results.append({
                    "tool": step.tool,
                    "success": False,
                    "error": str(e)
                })
                result.success = False
                result.error = f"Step {i + 1} ({step.tool}) failed: {e}"
                break

        # Update clip count from final project state
        if project:
            result.clip_count = project.clip_count

        logger.info(f"{'✅' if result.success else '❌'} Plan execution {'complete' if result.success else 'failed'}")
        return result

    async def _execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        project: Optional[Project],
        session: AgentSession
    ) -> Dict[str, Any]:
        """Execute a single tool and return result"""

        if tool_name == "search_clips":
            return await self._search_clips(params)

        elif tool_name == "get_clip_info":
            return await self._get_clip_info(params)

        elif tool_name == "create_project":
            return await self._create_project(params, session)

        elif tool_name == "add_clip_to_timeline":
            return await self._add_clip_to_timeline(params, project)

        elif tool_name == "remove_clip_from_timeline":
            return await self._remove_clip_from_timeline(params, project)

        elif tool_name == "update_clip_trim":
            return await self._update_clip_trim(params, project)

        elif tool_name == "reorder_clips":
            return await self._reorder_clips(params, project)

        elif tool_name == "get_timeline_info":
            return await self._get_timeline_info(params, project)

        elif tool_name == "render_preview":
            return await self._render_preview(params, project)

        elif tool_name == "denoise_audio":
            return await self._denoise_audio(params, project)

        elif tool_name == "remove_silent_parts":
            return await self._remove_silent_parts(params, project)

        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _search_clips(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for clips matching query"""
        query = params["query"]
        top_k = params.get("top_k", 10)

        logger.info(f"🔍 Searching for: '{query}'")

        results = search_videos(
            query=query,
            top_k=top_k,
            use_cascaded_reranking=True,
            confidence_threshold=0.5  # Lower threshold for agent
        )

        # Get video metadata to resolve actual file paths
        video_paths = await self._get_video_paths()

        duration_cache: dict[str, float] = {}
        clips = []
        for r in results:
            # Resolve actual video path from metadata
            video_path = video_paths.get(r.video_id, f"data/videos/{r.video_id}.mp4")
            if video_path not in duration_cache:
                duration_cache[video_path] = await _get_video_duration(video_path)

            clips.append({
                "chunk_id": r.chunk_id,
                "video_id": r.video_id,
                "title": r.title,
                "start_time": r.start_time,
                "end_time": r.end_time,
                "duration": r.end_time - r.start_time,
                "visual_description": r.visual_description,
                "audio_transcript": r.audio_transcript,
                "score": r.score,
                "video_path": video_path,
                "video_duration": duration_cache[video_path],
            })

        logger.info(f"Found {len(clips)} clips")

        if not clips:
            raise ValueError(
                f"No clips found for query: '{query}'. "
                "Try a broader search term or verify that videos have been indexed."
            )

        return {
            "query": query,
            "num_results": len(clips),
            "clips": clips
        }

    async def _get_video_paths(self) -> Dict[str, str]:
        """Get mapping of video_id to actual file paths from metadata"""
        import json
        import os
        from pathlib import Path

        video_paths = {}
        metadata_dir = Path("data/metadata")

        if metadata_dir.exists():
            for meta_file in metadata_dir.glob("*.json"):
                try:
                    with open(meta_file) as f:
                        meta = json.load(f)
                        video_id = meta.get("video_id")
                        file_path = meta.get("file_path")
                        if video_id and file_path:
                            # Normalize path - try to find actual file
                            if os.path.exists(file_path):
                                video_paths[video_id] = file_path
                            elif os.path.exists(f"data/{file_path}"):
                                video_paths[video_id] = f"data/{file_path}"
                            elif os.path.exists(f"data/videos/{video_id}.mp4"):
                                video_paths[video_id] = f"data/videos/{video_id}.mp4"
                            else:
                                # Use the metadata path as fallback
                                video_paths[video_id] = file_path
                except Exception:
                    pass

        return video_paths

    async def _get_clip_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed info about a specific clip"""
        chunk_id = params["chunk_id"]

        # Get chunk from vector DB
        chunks = self.vector_db.get_chunks_by_ids([chunk_id])

        # Fallback: the planner may pass a video_id instead of a chunk_id.
        # Try searching for the first chunk belonging to that video.
        if not chunks:
            from qdrant_client.models import FieldCondition, Filter, MatchValue

            scroll_result = self.vector_db.client.scroll(
                collection_name=self.vector_db.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="video_id", match=MatchValue(value=chunk_id))]
                ),
                limit=1,
                with_payload=True,
            )
            if scroll_result and scroll_result[0]:
                payload = scroll_result[0][0].payload
                chunks = [payload]

        if not chunks:
            raise ValueError(f"Chunk not found: {chunk_id}")

        chunk = chunks[0]
        return {
            "chunk_id": chunk["chunk_id"],
            "video_id": chunk["video_id"],
            "start_time": chunk["start_time"],
            "end_time": chunk["end_time"],
            "duration": chunk["end_time"] - chunk["start_time"],
            "visual_description": chunk.get("visual_description", ""),
            "audio_transcript": chunk.get("audio_transcript", "")
        }

    async def _create_project(
        self,
        params: Dict[str, Any],
        session: AgentSession
    ) -> Dict[str, Any]:
        """Create a new editing project"""
        name = params["name"]
        goal = params["goal"]

        project = Project(name=name, goal=goal)
        state_manager.save_project(project)

        logger.info(f"📁 Created project: {project.id}")
        return {
            "project_id": project.id,
            "name": name,
            "goal": goal
        }

    async def _add_clip_to_timeline(
        self,
        params: Dict[str, Any],
        project: Optional[Project]
    ) -> Dict[str, Any]:
        """Add a clip to the timeline"""
        if not project:
            raise ValueError("No project created yet")

        clip = TimelineClip(
            video_id=params["video_id"],
            source_path=params["source_path"],
            cut_from=params["cut_from"],
            cut_to=params["cut_to"],
            order=len(project.clips),
            transition=params.get("transition", "fade"),
            transition_duration=params.get("transition_duration", 0.5)
        )

        project.add_clip(clip)
        state_manager.save_project(project)

        logger.info(f"➕ Added clip: {clip.cut_from:.1f}s - {clip.cut_to:.1f}s ({clip.duration:.1f}s)")
        return {
            "clip_id": clip.id,
            "order": clip.order,
            "duration": clip.duration,
            "total_clips": project.clip_count,
            "total_duration": project.total_duration
        }

    async def _remove_clip_from_timeline(
        self,
        params: Dict[str, Any],
        project: Optional[Project]
    ) -> Dict[str, Any]:
        """Remove a clip from the timeline"""
        if not project:
            raise ValueError("No project created yet")

        clip_index = params["clip_index"]
        removed = project.remove_clip(clip_index)

        if removed:
            state_manager.save_project(project)
            logger.info(f"➖ Removed clip at index {clip_index}")
            return {
                "removed": True,
                "removed_clip_id": removed.id,
                "total_clips": project.clip_count,
                "total_duration": project.total_duration
            }
        else:
            return {"removed": False, "error": f"Invalid clip index: {clip_index}"}

    async def _update_clip_trim(
        self,
        params: Dict[str, Any],
        project: Optional[Project]
    ) -> Dict[str, Any]:
        """Update clip trim points"""
        if not project:
            raise ValueError("No project created yet")

        clip_index = params["clip_index"]
        if clip_index < 0 or clip_index >= len(project.clips):
            raise ValueError(f"Invalid clip index: {clip_index}")

        clip = project.clips[clip_index]

        if "cut_from" in params:
            clip.cut_from = params["cut_from"]
        if "cut_to" in params:
            clip.cut_to = params["cut_to"]

        state_manager.save_project(project)

        logger.info(f"✂️ Updated clip {clip_index}: {clip.cut_from:.1f}s - {clip.cut_to:.1f}s")
        return {
            "clip_id": clip.id,
            "cut_from": clip.cut_from,
            "cut_to": clip.cut_to,
            "duration": clip.duration,
            "total_duration": project.total_duration
        }

    async def _reorder_clips(
        self,
        params: Dict[str, Any],
        project: Optional[Project]
    ) -> Dict[str, Any]:
        """Reorder clips in timeline"""
        if not project:
            raise ValueError("No project created yet")

        new_order = params["new_order"]
        success = project.reorder_clips(new_order)

        if success:
            state_manager.save_project(project)
            logger.info(f"🔄 Reordered clips: {new_order}")
            return {
                "success": True,
                "new_order": new_order,
                "total_clips": project.clip_count
            }
        else:
            return {"success": False, "error": "Invalid order indices"}

    async def _get_timeline_info(
        self,
        params: Dict[str, Any],
        project: Optional[Project]
    ) -> Dict[str, Any]:
        """Get current timeline state"""
        if not project:
            raise ValueError("No project created yet")

        clips_info = []
        for clip in project.clips:
            clips_info.append({
                "order": clip.order,
                "clip_id": clip.id,
                "video_id": clip.video_id,
                "cut_from": clip.cut_from,
                "cut_to": clip.cut_to,
                "duration": clip.duration,
                "transition": clip.transition
            })

        return {
            "project_id": project.id,
            "name": project.name,
            "goal": project.goal,
            "total_clips": project.clip_count,
            "total_duration": project.total_duration,
            "clips": clips_info
        }

    async def _render_preview(
        self,
        params: Dict[str, Any],
        project: Optional[Project]
    ) -> Dict[str, Any]:
        """Render a preview of the timeline"""
        if not project:
            raise ValueError("No project created yet")

        if project.clip_count == 0:
            raise ValueError("No clips in timeline to render")

        # Import here to avoid circular imports
        from src.services.video_editor import FFmpegRenderer

        renderer = FFmpegRenderer()

        # Convert clips to dict format for renderer
        clips_data = []
        for clip in project.clips:
            clips_data.append({
                "source_path": clip.source_path,
                "cut_from": clip.cut_from,
                "cut_to": clip.cut_to,
                "transition": clip.transition,
                "transition_duration": clip.transition_duration
            })

        # Generate output path
        output_path = str(settings.EXPORTS_DIR / f"{project.id}-preview.mp4")

        # Generate spec and render
        spec = renderer.generate_spec(
            clips=clips_data,
            output_path=output_path
        )

        result = await renderer.render(spec, preview_mode=True)

        if result["success"]:
            logger.info(f"🎬 Preview rendered: {result['output_path']}")
            return {
                "success": True,
                "output_path": result["output_path"],
                "duration": result.get("duration", 0)
            }
        else:
            logger.error(f"❌ Preview render failed: {result.get('error')}")
            raise ValueError(f"Render failed: {result.get('error')}")

    async def _remove_silent_parts(
        self,
        params: Dict[str, Any],
        project: Optional[Project]
    ) -> Dict[str, Any]:
        """Remove segments that are both audio-silent and visually static."""
        import asyncio

        if not project:
            raise ValueError("No project created yet")

        clip_index = params.get("clip_index")
        silence_db = params.get("silence_threshold_db", -30)
        min_silence = params.get("min_silence_duration", 1.5)
        visual_threshold = params.get("visual_activity_threshold", 5.0)

        if clip_index is not None:
            if clip_index < 0 or clip_index >= len(project.clips):
                raise ValueError(f"Invalid clip index: {clip_index}")
            indices = [clip_index]
        else:
            indices = list(range(len(project.clips)))

        total_removed = 0.0
        clips_modified = 0

        # Process in reverse order so insertions don't shift earlier indices
        for idx in sorted(indices, reverse=True):
            clip = project.clips[idx]
            logger.info(
                f"🔇 Analyzing clip {idx} for silence: "
                f"{clip.cut_from:.1f}s-{clip.cut_to:.1f}s"
            )

            # 1. Detect silent segments
            silent_ranges = await _detect_silence(
                clip.source_path, clip.cut_from, clip.cut_to,
                silence_db, min_silence,
            )

            if not silent_ranges:
                logger.info(f"  No silence detected in clip {idx}, skipping")
                continue

            # 2. Check visual activity in each silent segment
            remove_ranges = []
            for seg_start, seg_end in silent_ranges:
                activity = await asyncio.to_thread(
                    _measure_visual_activity,
                    clip.source_path, seg_start, seg_end,
                )
                logger.info(
                    f"  Silence {seg_start:.1f}-{seg_end:.1f}s "
                    f"visual_activity={activity:.2f}"
                )
                if activity < visual_threshold:
                    remove_ranges.append((seg_start, seg_end))

            if not remove_ranges:
                logger.info(f"  All silent parts have visual activity, keeping clip {idx} intact")
                continue

            # 3. Compute keep ranges
            keep_ranges = _compute_keep_ranges(
                clip.cut_from, clip.cut_to, remove_ranges,
            )

            removed_dur = sum(e - s for s, e in remove_ranges)
            total_removed += removed_dur
            clips_modified += 1

            # 4. Replace original clip with sub-clips
            original_clip = project.clips.pop(idx)

            for j, (keep_start, keep_end) in enumerate(keep_ranges):
                sub_clip = TimelineClip(
                    video_id=original_clip.video_id,
                    source_path=original_clip.source_path,
                    cut_from=keep_start,
                    cut_to=keep_end,
                    order=0,  # will be re-indexed below
                    transition=original_clip.transition if j == 0 else "dummy",
                    transition_duration=original_clip.transition_duration if j == 0 else 0.0,
                )
                project.clips.insert(idx + j, sub_clip)

            logger.info(
                f"  Clip {idx} -> {len(keep_ranges)} sub-clips, "
                f"removed {removed_dur:.1f}s of dead air"
            )

        # Re-index all clip orders
        for i, c in enumerate(project.clips):
            c.order = i

        state_manager.save_project(project)

        return {
            "success": True,
            "clips_modified": clips_modified,
            "total_removed_seconds": round(total_removed, 2),
            "total_clips": project.clip_count,
            "total_duration": round(project.total_duration, 2),
        }

    async def _denoise_audio(
        self,
        params: Dict[str, Any],
        project: Optional[Project]
    ) -> Dict[str, Any]:
        """Remove background noise from clip audio using DeepFilterNet"""
        import asyncio
        import tempfile
        from pathlib import Path

        if not project:
            raise ValueError("No project created yet")

        clip_index = params.get("clip_index")

        if clip_index is not None:
            if clip_index < 0 or clip_index >= len(project.clips):
                raise ValueError(f"Invalid clip index: {clip_index}")
            clips_to_process = [(clip_index, project.clips[clip_index])]
        else:
            clips_to_process = list(enumerate(project.clips))

        if not clips_to_process:
            return {"success": True, "processed": 0, "message": "No clips to denoise"}

        # Lazy-load DeepFilterNet model (shim needed for torchaudio compat)
        model, df_state = _load_deepfilter()

        processed = []
        for idx, clip in clips_to_process:
            input_path = clip.source_path
            output_path = str(
                settings.EXPORTS_DIR / f"{project.id}-denoised-{idx}.mp4"
            )

            logger.info(f"🔇 Denoising clip {idx}: {input_path}")

            if input_path == output_path:
                logger.info(
                    f"⚠️  Clip {idx} already denoised (input == output). Skipping."
                )
                processed.append(idx)
                continue

            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_wav_in = str(Path(tmpdir) / "audio_in.wav")
                tmp_wav_out = str(Path(tmpdir) / "audio_out.wav")

                # Step 1: Extract audio as 48 kHz mono WAV
                extract_cmd = [
                    "ffmpeg", "-y", "-i", input_path,
                    "-vn", "-ar", "48000", "-ac", "1", "-f", "wav",
                    tmp_wav_in,
                ]
                proc = await asyncio.create_subprocess_exec(
                    *extract_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await proc.communicate()
                if proc.returncode != 0:
                    raise ValueError(
                        f"Audio extraction failed for clip {idx}: "
                        f"{stderr.decode()[-500:]}"
                    )

                # Step 2: Run DeepFilterNet enhancement
                await asyncio.to_thread(
                    _enhance_audio, model, df_state, tmp_wav_in, tmp_wav_out
                )

                # Step 3: Mux cleaned audio back with original video
                mux_cmd = [
                    "ffmpeg", "-y",
                    "-i", input_path,
                    "-i", tmp_wav_out,
                    "-c:v", "copy",
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    output_path,
                ]
                proc = await asyncio.create_subprocess_exec(
                    *mux_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await proc.communicate()
                if proc.returncode != 0:
                    raise ValueError(
                        f"Audio mux failed for clip {idx}: "
                        f"{stderr.decode()[-500:]}"
                    )

            clip.source_path = output_path
            processed.append(idx)
            logger.info(f"✅ Denoised clip {idx} -> {output_path}")

        state_manager.save_project(project)

        return {
            "success": True,
            "processed": len(processed),
            "clip_indices": processed,
        }


# ---------------------------------------------------------------------------
# DeepFilterNet helpers (module-level to allow lazy singleton loading)
# ---------------------------------------------------------------------------
_df_model = None
_df_state = None


def _load_deepfilter():
    """Load DeepFilterNet model (singleton, first call downloads weights)."""
    global _df_model, _df_state

    if _df_model is not None:
        return _df_model, _df_state

    import sys
    import types

    # Shim: deepfilternet 0.5.x imports torchaudio.backend.common.AudioMetaData
    # which was removed in torchaudio >= 2.2.  Create a lightweight stand-in.
    if "torchaudio.backend" not in sys.modules:
        from dataclasses import dataclass

        @dataclass
        class _AudioMetaData:
            sample_rate: int = 0
            num_frames: int = 0
            num_channels: int = 0
            bits_per_sample: int = 0
            encoding: str = ""

        backend = types.ModuleType("torchaudio.backend")
        common = types.ModuleType("torchaudio.backend.common")
        common.AudioMetaData = _AudioMetaData
        backend.common = common
        sys.modules["torchaudio.backend"] = backend
        sys.modules["torchaudio.backend.common"] = common

    from df.enhance import init_df

    model, df_state, _ = init_df()
    _df_model, _df_state = model, df_state
    logger.info("🔇 DeepFilterNet model loaded")
    return _df_model, _df_state


def _enhance_audio(model, df_state, input_path: str, output_path: str):
    """Run DeepFilterNet on a WAV file (blocking — call via asyncio.to_thread)."""
    import wave
    import numpy as np
    import torch
    from df import enhance

    # Read WAV using stdlib (avoids torchaudio backend issues)
    with wave.open(input_path, "rb") as wf:
        sr = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
        audio_np = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

    audio = torch.from_numpy(audio_np).unsqueeze(0)  # [1, samples]

    enhanced = enhance(model, df_state, audio)

    # Write WAV using stdlib
    out_np = (enhanced.squeeze(0).numpy() * 32768.0).clip(-32768, 32767).astype(np.int16)
    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sr)
        wf.writeframes(out_np.tobytes())


async def _get_video_duration(video_path: str) -> float:
    """Get video duration using ffprobe (seconds)."""
    import asyncio
    import json

    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        video_path,
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        logger.warning(f"Failed to get duration for {video_path}: {stderr.decode()[-200:]}")
        return 0.0

    try:
        data = json.loads(stdout.decode())
        return float(data["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to parse duration for {video_path}: {e}")
        return 0.0


# ---------------------------------------------------------------------------
# Silence removal helpers
# ---------------------------------------------------------------------------

async def _detect_silence(
    video_path: str,
    start_time: float,
    end_time: float,
    threshold_db: float,
    min_duration: float,
) -> list[tuple[float, float]]:
    """Detect silent audio segments using FFmpeg silencedetect.

    Returns list of (start, end) tuples in source-video coordinates.
    """
    import asyncio
    import re

    duration = end_time - start_time
    cmd = [
        "ffmpeg",
        "-ss", str(start_time),
        "-i", video_path,
        "-t", str(duration),
        "-af", f"silencedetect=noise={threshold_db}dB:d={min_duration}",
        "-f", "null", "-",
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr_bytes = await proc.communicate()
    stderr = stderr_bytes.decode(errors="replace")

    # Parse silence_start / silence_end pairs from stderr
    starts = [float(m) for m in re.findall(r"silence_start:\s*([\d.]+)", stderr)]
    ends = [float(m) for m in re.findall(r"silence_end:\s*([\d.]+)", stderr)]

    ranges: list[tuple[float, float]] = []
    for i, s in enumerate(starts):
        # Convert relative timestamps back to source-video coordinates
        abs_start = s + start_time
        abs_end = (ends[i] + start_time) if i < len(ends) else end_time
        # Clamp to clip boundaries
        abs_start = max(abs_start, start_time)
        abs_end = min(abs_end, end_time)
        if abs_end > abs_start:
            ranges.append((abs_start, abs_end))

    return ranges


def _measure_visual_activity(
    video_path: str,
    start_time: float,
    end_time: float,
    sample_fps: float = 2.0,
) -> float:
    """Measure visual activity via frame differencing (blocking).

    Returns mean pixel difference (0 = static, 5+ = significant motion).
    """
    import cv2
    import numpy as np

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.warning(f"Cannot open video: {video_path}")
        return 0.0

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    start_frame = int(start_time * fps)
    end_frame = int(end_time * fps)
    step = max(1, int(fps / sample_fps))

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    prev_gray = None
    diffs: list[float] = []

    frame_idx = start_frame
    while frame_idx < end_frame:
        ret, frame = cap.read()
        if not ret:
            break

        if (frame_idx - start_frame) % step == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (160, 90))

            if prev_gray is not None:
                diff = cv2.absdiff(prev_gray, gray)
                diffs.append(float(np.mean(diff)))

            prev_gray = gray

        frame_idx += 1

    cap.release()
    return float(np.mean(diffs)) if diffs else 0.0


def _compute_keep_ranges(
    clip_start: float,
    clip_end: float,
    remove_ranges: list[tuple[float, float]],
    min_keep_duration: float = 0.5,
) -> list[tuple[float, float]]:
    """Invert removal ranges into keep ranges, filtering short segments.

    Pure function — sorts and merges overlapping removal ranges, then
    returns gap segments >= min_keep_duration.
    """
    if not remove_ranges:
        return [(clip_start, clip_end)]

    # Sort and merge overlapping removal ranges
    sorted_ranges = sorted(remove_ranges)
    merged: list[tuple[float, float]] = [sorted_ranges[0]]
    for s, e in sorted_ranges[1:]:
        if s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))

    # Compute gaps (keep segments)
    keeps: list[tuple[float, float]] = []
    cursor = clip_start
    for rm_start, rm_end in merged:
        if rm_start > cursor:
            keeps.append((cursor, rm_start))
        cursor = max(cursor, rm_end)
    if cursor < clip_end:
        keeps.append((cursor, clip_end))

    # Filter out segments shorter than min_keep_duration
    return [(s, e) for s, e in keeps if (e - s) >= min_keep_duration]
