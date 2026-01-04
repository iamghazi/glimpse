"""
Library Management Page
Upload, view, and manage videos in the library
"""
import streamlit as st
from pathlib import Path
import os
import requests

st.set_page_config(
    page_title="Library - Video Search",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Video Library")

# Upload Section
st.markdown("## Upload Video")

with st.form("upload_form"):
    st.markdown("Upload a new video to your library")

    video_title = st.text_input(
        "Video Title",
        placeholder="Enter a descriptive title for your video",
        help="This will help you identify the video in search results"
    )

    uploaded_file = st.file_uploader(
        "Choose a video file",
        type=["mp4", "mov", "avi"],
        help="Supported formats: MP4, MOV, AVI"
    )

    submit_button = st.form_submit_button("Upload and Process", type="primary")

    if submit_button:
        if not video_title:
            st.error("Please enter a video title")
        elif not uploaded_file:
            st.error("Please select a video file")
        else:
            # Backend processing
            backend_url = "http://localhost:8000/upload"
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            data = {"title": video_title}

            with st.spinner("Uploading video to backend..."):
                try:
                    response = requests.post(backend_url, files=files, data=data)
                    response.raise_for_status()

                    result = response.json()
                    st.success(f"✅ Video uploaded successfully! Video ID: {result.get('video_id')}")
                    st.info(f"Backend message: {result.get('message')}")

                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to connect to backend: {e}")
                    st.warning("Please ensure the backend server is running at http://localhost:8000")


st.divider()

# Library View Section
st.markdown("## Video Library")

# Fetch videos from backend
backend_url = "http://localhost:8000/videos"

try:
    response = requests.get(backend_url, timeout=2)
    response.raise_for_status()
    videos_data = response.json()

    videos = videos_data.get("videos", [])

    if not videos:
        st.info("No videos in library yet. Upload your first video above!")
    else:
        st.markdown(f"**{len(videos)} video(s) in library**")

        # Display video list
        for video in videos:
            video_id = video.get("video_id", "unknown")
            title = video.get("title", "Untitled")
            file_size_mb = video.get("file_size_mb", 0)
            uploaded_at = video.get("uploaded_at", "")
            original_filename = video.get("original_filename", "")

            with st.expander(f"📹 {title}"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**Title:** {title}")
                    st.markdown(f"**Video ID:** `{video_id}`")
                    st.markdown(f"**Original File:** {original_filename}")
                    st.markdown(f"**Size:** {file_size_mb:.2f} MB")
                    st.markdown(f"**Uploaded:** {uploaded_at}")

                    # Video metadata
                    duration = video.get("duration_seconds", 0)
                    fps = video.get("fps", 0)
                    resolution = video.get("resolution", [0, 0])

                    if duration > 0:
                        st.markdown(f"**Duration:** {duration:.2f}s")
                        st.markdown(f"**FPS:** {fps:.2f}")
                        st.markdown(f"**Resolution:** {resolution[0]}x{resolution[1]}")

                    # Fetch chunk information
                    try:
                        chunks_url = f"http://localhost:8000/videos/{video_id}/chunks"
                        chunks_response = requests.get(chunks_url, timeout=2)
                        chunks_response.raise_for_status()
                        chunks_data = chunks_response.json()

                        num_chunks = chunks_data.get("num_chunks", 0)
                        chunks = chunks_data.get("chunks", [])

                        if num_chunks > 0:
                            total_frames = sum(chunk.get("num_frames", 0) for chunk in chunks)
                            st.markdown(f"**Chunks:** {num_chunks}")
                            st.markdown(f"**Frames Extracted:** {total_frames}")
                            st.markdown("**Status:** ✅ Processed (chunks + frames)")
                        else:
                            st.markdown("**Status:** ⚠️ Not processed yet")

                    except:
                        st.markdown("**Status:** ⚠️ Chunk info unavailable")

                with col2:
                    if st.button("Delete", key=f"delete_{video_id}"):
                        try:
                            delete_url = f"http://localhost:8000/videos/{video_id}"
                            delete_response = requests.delete(delete_url)
                            delete_response.raise_for_status()
                            st.success(f"Deleted {title}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting video: {e}")

except requests.exceptions.RequestException as e:
    st.warning(f"Could not connect to backend: {e}")
    st.info("Please ensure the backend server is running at http://localhost:8000")

    # Fallback: show local files
    st.markdown("### Local Videos (Fallback View)")
    videos_dir = Path("./videos")

    if videos_dir.exists():
        video_files = list(videos_dir.glob("*.mp4")) + list(videos_dir.glob("*.mov")) + list(videos_dir.glob("*.avi"))

        if video_files:
            for video_file in sorted(video_files):
                file_size_mb = video_file.stat().st_size / (1024 * 1024)
                st.markdown(f"- {video_file.name} ({file_size_mb:.2f} MB)")

st.divider()

st.markdown("### 📋 Processing Status")
st.info("""
**✅ Implemented:**
- Video upload and storage
- Automatic chunking (60s duration, 10s overlap)
- Frame extraction at 1 FPS
- Video metadata extraction (duration, FPS, resolution)

**⏳ Coming Next (Phase 3.6+):**
- Audio transcription with faster-whisper
- Visual descriptions with Gemini
- Embeddings generation and Qdrant indexing
""")
