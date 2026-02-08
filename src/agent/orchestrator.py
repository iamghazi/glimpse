"""
Agent Orchestrator
Main agent loop: Plan → Execute → Evaluate → Iterate
"""
import logging
from datetime import datetime
from typing import Optional

from src.core.config import settings
from src.models.agent import AgentSession, EvaluationResult
from src.agent.planner import AgentPlanner
from src.agent.executor import AgentExecutor
from src.agent.evaluator import AgentEvaluator
from src.agent.state import state_manager

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Main agent loop that coordinates planning, execution, and evaluation

    The agent follows a plan-execute-evaluate cycle:
    1. PLAN: Use Gemini to create an execution plan
    2. EXECUTE: Run tool calls to search, build timeline, render
    3. EVALUATE: Check if result meets user goals
    4. ITERATE: If not satisfied and iterations remain, refine and repeat
    """

    def __init__(self):
        self.planner = AgentPlanner()
        self.executor = AgentExecutor()
        self.evaluator = AgentEvaluator()
        self.max_iterations = settings.AGENT_MAX_ITERATIONS

    async def run(self, user_request: str) -> AgentSession:
        """
        Run the autonomous agent loop

        Args:
            user_request: Natural language editing request

        Returns:
            AgentSession with final state and outputs
        """
        logger.info("=" * 60)
        logger.info(f"🤖 Starting Agent Session")
        logger.info(f"📝 Request: {user_request}")
        logger.info("=" * 60)

        # Initialize session
        session = AgentSession(
            user_request=user_request,
            status="planning",
            max_iterations=self.max_iterations
        )
        state_manager.save_session(session)

        try:
            while session.iteration < session.max_iterations:
                session.iteration += 1
                logger.info(f"\n{'─' * 40}")
                logger.info(f"🔄 Iteration {session.iteration}/{session.max_iterations}")
                logger.info(f"{'─' * 40}")

                # 1. PLAN
                session.status = "planning"
                state_manager.save_session(session)

                previous_eval = session.latest_evaluation
                timeline_state = None

                # Get current timeline state if we have a project
                if session.project_id:
                    project = state_manager.get_project(session.project_id)
                    if project:
                        timeline_state = {
                            "total_clips": project.clip_count,
                            "total_duration": project.total_duration,
                            "clips": [
                                {
                                    "order": c.order,
                                    "video_id": c.video_id,
                                    "cut_from": c.cut_from,
                                    "cut_to": c.cut_to,
                                    "duration": c.duration
                                }
                                for c in project.clips
                            ]
                        }

                plan = await self.planner.create_plan(
                    user_request=user_request,
                    iteration=session.iteration,
                    previous_evaluation=previous_eval,
                    timeline_state=timeline_state,
                    project_id=session.project_id if session.project_id else None
                )
                session.current_plan = plan

                # 2. EXECUTE
                session.status = "executing"
                state_manager.save_session(session)

                execution_result = await self.executor.execute_plan(plan, session)
                session.execution_results.append(execution_result)

                if not execution_result.success:
                    logger.error(f"❌ Execution failed: {execution_result.error}")
                    session.status = "failed"
                    break

                # Update project_id if created
                if execution_result.project_id:
                    session.project_id = execution_result.project_id

                # Update preview path
                if execution_result.preview_path:
                    session.preview_path = execution_result.preview_path

                # 3. EVALUATE
                session.status = "evaluating"
                state_manager.save_session(session)

                evaluation = await self.evaluator.evaluate(
                    user_request=user_request,
                    execution_result=execution_result,
                    session=session
                )
                session.evaluation_results.append(evaluation)

                # 4. CHECK IF DONE
                if evaluation.satisfied:
                    logger.info("✅ Goals satisfied!")
                    session.status = "complete"
                    session.completed_at = datetime.utcnow()
                    break

                logger.info(f"⚠️ Not satisfied, will refine...")

            # Max iterations reached without satisfaction
            if session.status not in ("complete", "failed"):
                logger.warning(f"⚠️ Max iterations ({self.max_iterations}) reached")
                session.status = "complete"  # Best effort
                session.completed_at = datetime.utcnow()

        except Exception as e:
            logger.exception(f"❌ Agent session failed: {e}")
            session.status = "failed"
            session.completed_at = datetime.utcnow()

        # Save final state
        state_manager.save_session(session)

        logger.info("\n" + "=" * 60)
        logger.info(f"🏁 Session Complete: {session.status}")
        logger.info(f"   Iterations: {session.iteration}")
        logger.info(f"   Preview: {session.preview_path or 'None'}")
        logger.info("=" * 60)

        return session

    async def continue_with_feedback(
        self,
        session_id: str,
        feedback: str
    ) -> AgentSession:
        """
        Continue a session with user feedback

        Args:
            session_id: Existing session ID
            feedback: User feedback for refinement

        Returns:
            Updated AgentSession
        """
        session = state_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if session.iteration >= session.max_iterations:
            raise ValueError("Maximum iterations already reached")

        logger.info(f"\n{'─' * 40}")
        logger.info(f"📝 Continuing with feedback: {feedback}")
        logger.info(f"{'─' * 40}")

        # Append feedback to request for planner context
        augmented_request = f"{session.user_request}\n\nUser feedback: {feedback}"

        # Run one more iteration
        session.iteration += 1
        session.status = "planning"
        state_manager.save_session(session)

        try:
            # Get timeline state
            timeline_state = None
            if session.project_id:
                project = state_manager.get_project(session.project_id)
                if project:
                    timeline_state = {
                        "total_clips": project.clip_count,
                        "total_duration": project.total_duration,
                        "clips": [
                            {
                                "order": c.order,
                                "video_id": c.video_id,
                                "cut_from": c.cut_from,
                                "cut_to": c.cut_to,
                                "duration": c.duration
                            }
                            for c in project.clips
                        ]
                    }

            # Create new plan with feedback context
            plan = await self.planner.create_plan(
                user_request=augmented_request,
                iteration=session.iteration,
                previous_evaluation=session.latest_evaluation,
                timeline_state=timeline_state,
                project_id=session.project_id
            )
            session.current_plan = plan

            # Execute
            session.status = "executing"
            state_manager.save_session(session)

            execution_result = await self.executor.execute_plan(plan, session)
            session.execution_results.append(execution_result)

            if execution_result.preview_path:
                session.preview_path = execution_result.preview_path

            # Evaluate
            session.status = "evaluating"
            state_manager.save_session(session)

            evaluation = await self.evaluator.evaluate(
                user_request=session.user_request,
                execution_result=execution_result,
                session=session
            )
            session.evaluation_results.append(evaluation)

            # Update status
            session.status = "complete" if evaluation.satisfied else "complete"
            session.completed_at = datetime.utcnow()

        except Exception as e:
            logger.exception(f"❌ Feedback iteration failed: {e}")
            session.status = "failed"
            session.completed_at = datetime.utcnow()

        state_manager.save_session(session)
        return session

    async def render_final(self, session_id: str) -> str:
        """
        Render the final full-quality video

        Args:
            session_id: Session to render

        Returns:
            Path to final output file
        """
        session = state_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if not session.project_id:
            raise ValueError("No project in session")

        project = state_manager.get_project(session.project_id)
        if not project:
            raise ValueError(f"Project not found: {session.project_id}")

        if project.clip_count == 0:
            raise ValueError("No clips in timeline")

        logger.info(f"🎬 Rendering final video for session {session_id}")

        from src.services.video_editor import FFmpegRenderer

        renderer = FFmpegRenderer()

        # Convert clips to dict format
        clips_data = []
        for clip in project.clips:
            clips_data.append({
                "source_path": clip.source_path,
                "cut_from": clip.cut_from,
                "cut_to": clip.cut_to,
                "transition": clip.transition,
                "transition_duration": clip.transition_duration
            })

        # Generate output path (full quality)
        output_path = str(settings.EXPORTS_DIR / f"{project.id}-final.mp4")

        # Generate spec and render at full quality
        spec = renderer.generate_spec(
            clips=clips_data,
            output_path=output_path
        )

        result = await renderer.render(spec, preview_mode=False)

        if result["success"]:
            session.final_output_path = result["output_path"]
            state_manager.save_session(session)
            logger.info(f"✅ Final video rendered: {result['output_path']}")
            return result["output_path"]
        else:
            raise ValueError(f"Final render failed: {result.get('error')}")
