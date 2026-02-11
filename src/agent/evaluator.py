"""
Agent Evaluator
Evaluates execution results against user goals using metadata
"""
import re
import logging
from typing import Dict, Any, Optional

from src.models.agent import AgentSession, EvaluationResult, ExecutionResult

logger = logging.getLogger(__name__)


class AgentEvaluator:
    """Evaluates execution results against user goals"""

    def __init__(self, duration_tolerance: float = 0.1):
        """
        Initialize evaluator

        Args:
            duration_tolerance: Allowed deviation from target duration (default 10%)
        """
        self.duration_tolerance = duration_tolerance

    def extract_duration_target(self, user_request: str) -> tuple[float, bool]:
        """
        Extract target duration from user request

        Looks for patterns like:
        - "60 seconds", "60s", "60 sec"
        - "1 minute", "1 min", "1m"
        - "1:30" (minute:second format)

        Returns (target_seconds, has_target). If no duration found, target is 0.
        """
        request_lower = user_request.lower()

        # Pattern: minute:second format (e.g., "1:30")
        mm_ss_match = re.search(r'(\d+):(\d{2})', user_request)
        if mm_ss_match:
            minutes = int(mm_ss_match.group(1))
            seconds = int(mm_ss_match.group(2))
            return minutes * 60 + seconds, True

        # Pattern: X minutes (and Y seconds)
        # Also handles hyphenated forms like "30-second", "2-minute"
        min_match = re.search(r'(\d+(?:\.\d+)?)[- ]?(?:minute|min|m\b)', request_lower)
        sec_match = re.search(r'(\d+(?:\.\d+)?)[- ]?(?:second|sec|s\b)', request_lower)

        total = 0.0
        if min_match:
            total += float(min_match.group(1)) * 60
        if sec_match:
            total += float(sec_match.group(1))

        if total > 0:
            return total, True

        # No explicit duration target
        logger.info("No explicit duration target found in request")
        return 0.0, False

    async def evaluate(
        self,
        user_request: str,
        execution_result: ExecutionResult,
        session: AgentSession
    ) -> EvaluationResult:
        """
        Evaluate an execution result against user goals

        Args:
            user_request: Original user request
            execution_result: Result from executor
            session: Current agent session

        Returns:
            EvaluationResult with satisfaction status and refinements
        """
        logger.info("📊 Evaluating execution result")

        # Extract target duration
        target_duration, has_target = self.extract_duration_target(user_request)
        actual_duration = execution_result.duration or 0
        clip_count = execution_result.clip_count
        render_success = execution_result.success and execution_result.preview_path is not None

        # Calculate duration tolerance
        if has_target:
            tolerance = target_duration * self.duration_tolerance
            duration_diff = abs(actual_duration - target_duration)
            duration_ok = duration_diff <= tolerance
        else:
            duration_ok = True

        # Determine if satisfied
        satisfied = render_success and duration_ok and clip_count > 0

        # Generate refinements if not satisfied
        refinements = []

        if not render_success:
            if execution_result.error:
                refinements.append(f"Render failed: {execution_result.error}")
            else:
                refinements.append("Render failed - check clip paths and FFmpeg")

        if clip_count == 0:
            refinements.append("No clips added - search for and add relevant clips")

        if has_target:
            tolerance = target_duration * self.duration_tolerance
            if actual_duration > target_duration + tolerance:
                excess = actual_duration - target_duration
                refinements.append(
                    f"Video too long by {excess:.1f}s - trim clips or remove content"
                )

            if actual_duration < target_duration - tolerance:
                deficit = target_duration - actual_duration
                refinements.append(
                    f"Video too short by {deficit:.1f}s - add more clips"
                )

        # Log evaluation summary
        logger.info(f"📊 Evaluation Results:")
        if has_target:
            logger.info(f"   Target duration: {target_duration:.1f}s")
        else:
            logger.info("   Target duration: (none specified)")
        logger.info(f"   Actual duration: {actual_duration:.1f}s")
        logger.info(f"   Duration OK: {'✅' if duration_ok else '❌'}")
        logger.info(f"   Render success: {'✅' if render_success else '❌'}")
        logger.info(f"   Clip count: {clip_count}")
        logger.info(f"   Satisfied: {'✅' if satisfied else '❌'}")

        if refinements:
            logger.info(f"   Refinements needed:")
            for r in refinements:
                logger.info(f"     - {r}")

        return EvaluationResult(
            duration_ok=duration_ok,
            target_duration=target_duration,
            actual_duration=actual_duration,
            render_success=render_success,
            clip_count=clip_count,
            satisfied=satisfied,
            refinements=refinements
        )
