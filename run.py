#!/usr/bin/env python3
"""
Development Server Launcher
Starts the FastAPI application with hot-reload enabled
"""
import os
import sys
from pathlib import Path

# Add src to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))


def main():
    """Launch the development server"""
    print("=" * 80)
    print("🚀 Video Library Search Engine - Development Server")
    print("=" * 80)
    print()
    print("Starting FastAPI server with hot-reload...")
    print("API will be available at: http://localhost:8000")
    print("Interactive docs at: http://localhost:8000/docs")
    print("Alternative docs at: http://localhost:8000/redoc")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 80)
    print()

    # Import and run uvicorn
    try:
        import uvicorn
    except ImportError:
        print("❌ Error: uvicorn not installed")
        print("Install with: uv pip install uvicorn")
        sys.exit(1)

    # Run the server
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src"],
        log_level="info",
    )


if __name__ == "__main__":
    main()
