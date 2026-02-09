"""
Agent Tools
Tool definitions for the video editing agent
"""
from typing import Any, Dict, List

# Tool definitions for Gemini function calling
AGENT_TOOLS = [
    {
        "name": "search_clips",
        "description": "Search the video library for clips matching a natural language query. Returns clips with timestamps, descriptions, and relevance scores. Use this to find relevant content for the edit.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query describing the content you're looking for"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 10)",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_clip_info",
        "description": "Get detailed information about a specific video clip including full duration, transcript, and visual description. Use this to understand clip content before adding to timeline.",
        "parameters": {
            "type": "object",
            "properties": {
                "chunk_id": {
                    "type": "string",
                    "description": "The chunk/clip ID to get information about"
                }
            },
            "required": ["chunk_id"]
        }
    },
    {
        "name": "create_project",
        "description": "Create a new editing project to hold the timeline. Must be called before adding clips.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Project name (short, descriptive)"
                },
                "goal": {
                    "type": "string",
                    "description": "What this edit aims to achieve (for tracking)"
                }
            },
            "required": ["name", "goal"]
        }
    },
    {
        "name": "add_clip_to_timeline",
        "description": "Add a clip to the project timeline. Clips are added in order. You can specify trim points to use only part of the source clip.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID to add clip to"
                },
                "video_id": {
                    "type": "string",
                    "description": "Source video ID"
                },
                "source_path": {
                    "type": "string",
                    "description": "Path to source video file"
                },
                "cut_from": {
                    "type": "number",
                    "description": "Start time in source video (seconds)"
                },
                "cut_to": {
                    "type": "number",
                    "description": "End time in source video (seconds)"
                },
                "transition": {
                    "type": "string",
                    "description": "Transition type: fade, directional-left, directional-right, directional-up, directional-down, random, dummy",
                    "default": "fade"
                }
            },
            "required": ["project_id", "video_id", "source_path", "cut_from", "cut_to"]
        }
    },
    {
        "name": "remove_clip_from_timeline",
        "description": "Remove a clip from the timeline by its index (0-indexed). Remaining clips are automatically reordered.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID"
                },
                "clip_index": {
                    "type": "integer",
                    "description": "Index of clip to remove (0-indexed)"
                }
            },
            "required": ["project_id", "clip_index"]
        }
    },
    {
        "name": "update_clip_trim",
        "description": "Update the trim points (cut_from, cut_to) of a clip in the timeline. Use this to adjust clip duration.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID"
                },
                "clip_index": {
                    "type": "integer",
                    "description": "Index of clip to update (0-indexed)"
                },
                "cut_from": {
                    "type": "number",
                    "description": "New start time in source video (seconds)"
                },
                "cut_to": {
                    "type": "number",
                    "description": "New end time in source video (seconds)"
                }
            },
            "required": ["project_id", "clip_index"]
        }
    },
    {
        "name": "reorder_clips",
        "description": "Reorder clips in the timeline by specifying new positions.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID"
                },
                "new_order": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "New order of clip indices, e.g., [2, 0, 1] moves clip 2 to first position"
                }
            },
            "required": ["project_id", "new_order"]
        }
    },
    {
        "name": "get_timeline_info",
        "description": "Get current timeline state including all clips and total duration. Use this to check progress and plan adjustments.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID"
                }
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "render_preview",
        "description": "Render a low-resolution 480p preview of the current timeline. This must be called after adding all clips to see the result.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID to render"
                }
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "denoise_audio",
        "description": "Remove background noise from clip audio using AI-based noise suppression (RNNoise). Processes one or all clips in the project timeline.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID containing the clips to denoise"
                },
                "clip_index": {
                    "type": "integer",
                    "description": "Index of a specific clip to denoise (0-indexed). If omitted, all clips are denoised."
                }
            },
            "required": ["project_id"]
        }
    }
]


def get_tool_by_name(name: str) -> Dict[str, Any] | None:
    """Get a tool definition by name"""
    for tool in AGENT_TOOLS:
        if tool["name"] == name:
            return tool
    return None


def get_tool_names() -> List[str]:
    """Get list of all tool names"""
    return [tool["name"] for tool in AGENT_TOOLS]


def format_tools_for_prompt() -> str:
    """Format tools as a string for inclusion in prompts"""
    lines = []
    for tool in AGENT_TOOLS:
        params = tool["parameters"]["properties"]
        required = tool["parameters"].get("required", [])

        param_strs = []
        for name, info in params.items():
            req = " (required)" if name in required else ""
            param_strs.append(f"    - {name}: {info['description']}{req}")

        lines.append(f"- {tool['name']}: {tool['description']}")
        lines.extend(param_strs)
        lines.append("")

    return "\n".join(lines)
