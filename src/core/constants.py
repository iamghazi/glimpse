"""
Application Constants
"""

# Vector Database
QDRANT_COLLECTION_NAME = "video_chunks"

# RRF (Reciprocal Rank Fusion)
RRF_K_CONSTANT = 60  # Standard RRF constant

# Default Query Weights
DEFAULT_TEXT_WEIGHT = 0.6
DEFAULT_VISUAL_WEIGHT = 0.4

# Retry Configuration
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0  # seconds
RETRY_EXPONENTIAL_BASE = 2.0

# Video Processing
SUPPORTED_VIDEO_FORMATS = [".mp4", ".avi", ".mov", ".mkv", ".webm"]
MAX_VIDEO_SIZE_MB = 500.0

# API Limits
MAX_SEARCH_RESULTS = 50
DEFAULT_SEARCH_RESULTS = 5
MAX_CHAT_CLIPS = 10
