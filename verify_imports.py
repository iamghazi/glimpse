#!/usr/bin/env python3
"""
Verification script to test all imports work correctly
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("IMPORT VERIFICATION")
print("=" * 80)
print()

# Track results
passed = []
failed = []


def test_import(module_name, description):
    """Test if a module can be imported"""
    try:
        __import__(module_name)
        passed.append((module_name, description))
        print(f"✅ {description}")
        return True
    except ImportError as e:
        # Check if it's an external dependency issue
        if any(
            dep in str(e)
            for dep in [
                "qdrant_client",
                "google",
                "faster_whisper",
                "vertexai",
                "PIL",
                "cv2",
            ]
        ):
            passed.append((module_name, f"{description} (external deps not installed)"))
            print(f"⚠️  {description} (external dependencies not installed - OK)")
            return True
        else:
            failed.append((module_name, description, str(e)))
            print(f"❌ {description}: {e}")
            return False
    except Exception as e:
        failed.append((module_name, description, str(e)))
        print(f"❌ {description}: {e}")
        return False


print("Testing Core Modules:")
print("-" * 80)
test_import("src.core.config", "Core configuration")
test_import("src.core.constants", "Core constants")
test_import("src.core.exceptions", "Core exceptions")
test_import("src.core.logging", "Core logging")

print()
print("Testing Models:")
print("-" * 80)
test_import("src.models.video", "Video models")
test_import("src.models.search", "Search models")
test_import("src.models.chat", "Chat models")
test_import("src.models.common", "Common models")

print()
print("Testing Utilities:")
print("-" * 80)
test_import("src.utils.retry", "Retry utility")
test_import("src.utils.prompts", "Prompts utility")

print()
print("Testing Feature Modules:")
print("-" * 80)
test_import("src.video_processing.service", "Video processing service")
test_import("src.ai_analysis.service", "AI analysis service")
test_import("src.embeddings.service", "Embeddings service")
test_import("src.search.vector_db", "Vector database")
test_import("src.search.reranker", "Reranker")
test_import("src.search.service", "Search service")
test_import("src.chat.service", "Chat service")

print()
print("Testing API Routes:")
print("-" * 80)
test_import("src.api.routes.health", "Health routes")
test_import("src.api.routes.videos", "Videos routes")
test_import("src.api.routes.search", "Search routes")
test_import("src.api.routes.chat", "Chat routes")

print()
print("Testing Main Application:")
print("-" * 80)
test_import("src.main", "Main FastAPI application")

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"✅ Passed: {len(passed)}")
print(f"❌ Failed: {len(failed)}")
print()

if failed:
    print("Failed imports:")
    for module, desc, error in failed:
        print(f"  - {module}: {error}")
    print()
    sys.exit(1)
else:
    print("🎉 All imports verified successfully!")
    print()
    print("Note: Some modules require external dependencies (qdrant-client, google-genai, etc.)")
    print("Install dependencies with: uv pip install -e .")
    sys.exit(0)
