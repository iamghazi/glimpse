"""
Pytest configuration and shared fixtures
"""
import pytest
import sys
from pathlib import Path

# Add src directory to Python path for imports
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))


@pytest.fixture
def sample_query():
    """Sample search query for testing"""
    return "man flirts with a woman"


@pytest.fixture
def mock_video_metadata():
    """Mock video metadata for testing"""
    return {
        "video_id": "test_vid_123",
        "title": "Test Video",
        "file_path": "/path/to/test_video.mp4",
        "duration_seconds": 120.0,
        "fps": 30.0,
        "resolution": [1920, 1080],
        "file_size_mb": 50.0,
        "uploaded_at": "2024-01-01T00:00:00",
        "indexed_at": "2024-01-01T00:05:00",
    }


@pytest.fixture
def mock_chunk_data():
    """Mock chunk data for testing"""
    return {
        "chunk_id": "test_vid_123_0_30",
        "video_id": "test_vid_123",
        "start_time": 0.0,
        "end_time": 30.0,
        "duration": 30.0,
        "visual_description": "A man and woman having a conversation",
        "audio_transcript": "Hi, how are you today?",
        "representative_frame": "/path/to/frame.jpg",
        "frame_paths": ["/path/to/frame1.jpg", "/path/to/frame2.jpg"],
    }
