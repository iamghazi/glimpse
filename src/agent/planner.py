"""
Agent Planner
Uses Gemini to create execution plans for video editing
"""
import json
import logging
from typing import Optional, Dict, Any

from google import genai
from google.genai import types

from src.core.config import settings
from src.models.agent import AgentPlan, PlanStep, EvaluationResult
from src.agent.tools import format_tools_for_prompt

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are an autonomous video editing assistant that creates execution plans.

Given a user's request for video editing, create a step-by-step plan using the available tools.
Your goal is to search for relevant clips, assemble them into a timeline, and render a preview.

## Available Tools

{tools}

## Guidelines

1. **Always search first**: Use search_clips to find relevant content before adding to timeline
2. **Create project before clips**: Must call create_project before add_clip_to_timeline
3. **Consider duration carefully**:
   - Extract the target duration from the user's request
   - Calculate total duration as you add clips
   - Trim clips to fit the target duration
4. **Use appropriate transitions**: Match transition style to content (fade for calm, directional for dynamic)
5. **Always render preview**: Call render_preview at the end to evaluate the result

## Output Format

Return a JSON object with this structure:
{{
  "reasoning": "Brief explanation of your approach",
  "steps": [
    {{
      "tool": "tool_name",
      "params": {{"param1": "value1", ...}},
      "description": "What this step does"
    }},
    ...
  ]
}}

## Variable Substitution

You can reference results from previous steps using this syntax:
- {{search_clips.clips[0].video_id}} - First clip's video ID from search
- {{search_clips.clips[0].video_path}} - First clip's source file path
- {{create_project.project_id}} - The created project ID

The search_clips tool returns:
- clips[N].video_id, clips[N].video_path, clips[N].start_time, clips[N].end_time, clips[N].duration

## Example Plan

For request: "Create a 30-second highlight of product demos"

{{
  "reasoning": "Search for product demo clips, select best 2-3 clips totaling ~30s, add with smooth transitions",
  "steps": [
    {{"tool": "search_clips", "params": {{"query": "product demo", "top_k": 10}}, "description": "Find product demo clips"}},
    {{"tool": "create_project", "params": {{"name": "Product Highlights", "goal": "30-second demo reel"}}, "description": "Initialize project"}},
    {{"tool": "add_clip_to_timeline", "params": {{"project_id": "{{create_project.project_id}}", "video_id": "{{search_clips.clips[0].video_id}}", "source_path": "{{search_clips.clips[0].video_path}}", "cut_from": 0, "cut_to": 10, "transition": "fade"}}, "description": "Add first demo clip (10s)"}},
    {{"tool": "add_clip_to_timeline", "params": {{"project_id": "{{create_project.project_id}}", "video_id": "{{search_clips.clips[1].video_id}}", "source_path": "{{search_clips.clips[1].video_path}}", "cut_from": 0, "cut_to": 10, "transition": "fade"}}, "description": "Add second demo clip (10s)"}},
    {{"tool": "add_clip_to_timeline", "params": {{"project_id": "{{create_project.project_id}}", "video_id": "{{search_clips.clips[2].video_id}}", "source_path": "{{search_clips.clips[2].video_path}}", "cut_from": 0, "cut_to": 10, "transition": "fade"}}, "description": "Add third demo clip (10s)"}},
    {{"tool": "render_preview", "params": {{"project_id": "{{create_project.project_id}}"}}, "description": "Render 480p preview"}}
  ]
}}

IMPORTANT: Always use the exact variable syntax shown above. Use {{search_clips.clips[N]}} to reference search results.
"""

REFINEMENT_PROMPT = """The previous attempt needs refinement.

## Previous Evaluation Results
- Target duration: {target_duration}s
- Actual duration: {actual_duration}s
- Duration OK: {duration_ok}
- Render success: {render_success}
- Clip count: {clip_count}

## Issues to Address
{refinements}

## Current Timeline State
{timeline_state}

Please create a new plan that addresses these issues. Focus on:
1. If too long: trim clips or remove content
2. If too short: add more clips
3. If render failed: check clip paths

Return the updated plan in the same JSON format.
"""


class AgentPlanner:
    """Creates execution plans using Gemini"""

    def __init__(self):
        self.client = genai.Client(
            vertexai=True,
            project=settings.GCP_PROJECT_ID,
            location=settings.GCP_LOCATION,
        )
        self.model = settings.GEMINI_MODEL

    async def create_plan(
        self,
        user_request: str,
        iteration: int,
        previous_evaluation: Optional[EvaluationResult] = None,
        timeline_state: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None
    ) -> AgentPlan:
        """
        Create an execution plan using Gemini

        Args:
            user_request: Original user request
            iteration: Current iteration number (1-indexed)
            previous_evaluation: Results from previous iteration (if any)
            timeline_state: Current timeline info (if refining)
            project_id: Existing project ID (if refining)

        Returns:
            AgentPlan with steps to execute
        """
        logger.info(f"🧠 Creating plan (iteration {iteration})")

        # Build system prompt with tools
        system_prompt = PLANNER_SYSTEM_PROMPT.format(
            tools=format_tools_for_prompt()
        )

        # Build user prompt
        if iteration == 1 or previous_evaluation is None:
            # First iteration: just the request
            prompt = f"User request: {user_request}\n\nCreate an execution plan to fulfill this request."
        else:
            # Refinement iteration
            refinements_str = "\n".join(f"- {r}" for r in previous_evaluation.refinements)
            timeline_str = json.dumps(timeline_state, indent=2) if timeline_state else "No timeline yet"

            prompt = REFINEMENT_PROMPT.format(
                target_duration=previous_evaluation.target_duration,
                actual_duration=previous_evaluation.actual_duration,
                duration_ok=previous_evaluation.duration_ok,
                render_success=previous_evaluation.render_success,
                clip_count=previous_evaluation.clip_count,
                refinements=refinements_str,
                timeline_state=timeline_str
            )

            prompt += f"\n\nOriginal request: {user_request}"
            if project_id:
                prompt += f"\nExisting project_id: {project_id}"

        logger.debug(f"Prompt: {prompt[:500]}...")

        # Call Gemini
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.7,  # Some creativity for varied approaches
            )
        )

        # Parse response
        try:
            plan_data = json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse plan JSON: {e}")
            logger.error(f"Response text: {response.text[:500]}")
            raise ValueError(f"Failed to parse planner response: {e}")

        # Convert to AgentPlan
        steps = []
        for step_data in plan_data.get("steps", []):
            steps.append(PlanStep(
                tool=step_data["tool"],
                params=step_data.get("params", {}),
                description=step_data.get("description")
            ))

        plan = AgentPlan(
            steps=steps,
            reasoning=plan_data.get("reasoning")
        )

        logger.info(f"📋 Plan created with {len(plan.steps)} steps")
        if plan.reasoning:
            logger.info(f"   Reasoning: {plan.reasoning}")

        return plan
