"""
Retry Utilities with Exponential Backoff
"""
import time
import logging
from google.api_core import exceptions as google_exceptions

from src.core.constants import MAX_RETRIES, INITIAL_RETRY_DELAY, RETRY_EXPONENTIAL_BASE

logger = logging.getLogger(__name__)


def retry_with_backoff(
    func,
    max_retries: int = MAX_RETRIES,
    initial_delay: float = INITIAL_RETRY_DELAY,
    exponential_base: float = RETRY_EXPONENTIAL_BASE,
):
    """
    Retry a function with exponential backoff for quota/rate limit errors

    Args:
        func: Function to retry (should be a lambda/callable)
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        exponential_base: Base for exponential backoff (default: 2.0)

    Returns:
        The result of the successful function call

    Raises:
        google_exceptions.ResourceExhausted: If max retries exceeded
        google_exceptions.InvalidArgument: For non-retryable errors
        Exception: For other errors

    Example:
        result = retry_with_backoff(
            lambda: api_client.generate_embedding(data)
        )
    """
    delay = initial_delay

    for attempt in range(max_retries + 1):
        try:
            return func()

        except google_exceptions.ResourceExhausted as e:
            # Quota exceeded error - retry with backoff
            if attempt < max_retries:
                logger.warning(
                    f"Quota exceeded, retrying in {delay}s... "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)
                delay *= exponential_base  # Exponential backoff
            else:
                logger.error(f"Max retries reached. Quota error: {e}")
                raise

        except google_exceptions.InvalidArgument as e:
            # Invalid argument errors - check if retryable
            error_msg = str(e)
            if "excceeds allowed maximum" in error_msg or "exceeds allowed maximum" in error_msg:
                logger.warning(f"Video size exceeds limit: {e}")
                raise
            else:
                logger.error(f"Invalid argument error: {e}")
                raise

        except Exception as e:
            # Other errors - don't retry
            logger.error(f"Unexpected error in retry_with_backoff: {e}")
            raise

    return None
