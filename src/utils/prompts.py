"""
Prompt Template Loading Utilities
"""
from pathlib import Path
import logging

from src.core.config import settings

logger = logging.getLogger(__name__)


def load_prompt_template(template_name: str) -> str:
    """
    Load a prompt template from the prompts directory

    Args:
        template_name: Name of the template file (e.g., "text_rerank_prompt.txt")

    Returns:
        The prompt template as a string

    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    template_path = settings.PROMPTS_DIR / template_name

    if not template_path.exists():
        logger.error(f"Prompt template not found: {template_path}")
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    try:
        with open(template_path, "r") as f:
            template = f.read()

        logger.debug(f"Loaded prompt template: {template_name}")
        return template

    except Exception as e:
        logger.error(f"Error loading prompt template {template_name}: {e}")
        raise


def get_text_rerank_prompt() -> str:
    """Load the text-only reranking prompt template"""
    return load_prompt_template("text_rerank_prompt.txt")


def get_multimodal_rerank_prompt() -> str:
    """Load the multimodal reranking prompt template"""
    return load_prompt_template("multimodal_rerank_prompt.txt")
