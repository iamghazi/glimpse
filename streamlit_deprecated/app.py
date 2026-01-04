import os
import mimetypes
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai.types import (
    Content,
    Part,
    CreateCachedContentConfig,
    GenerateContentConfig,
)
from google.cloud import storage

load_dotenv()

# Load configuration from environment variables
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
GCS_BLOB_NAME = os.getenv("GCS_BLOB_NAME")
VIDEO_PATH = os.getenv("VIDEO_PATH")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")

# Validate required environment variables
required_vars = {
    "GCP_PROJECT_ID": GCP_PROJECT_ID,
    "GCP_LOCATION": GCP_LOCATION,
    "GCS_BUCKET_NAME": GCS_BUCKET_NAME,
    "GCS_BLOB_NAME": GCS_BLOB_NAME,
    "VIDEO_PATH": VIDEO_PATH,
    "GEMINI_MODEL": GEMINI_MODEL,
}

missing_vars = [var for var, value in required_vars.items() if not value]
if missing_vars:
    st.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    st.info("Please create a .env file based on .env.example and configure all required variables.")
    st.stop()

client = genai.Client(
    vertexai=True,
    project=GCP_PROJECT_ID,
    location=GCP_LOCATION,
)


def upload_to_gcs(local_path: str, bucket_name: str, blob_name: str) -> tuple[str, str]:
    """Upload video to Google Cloud Storage and return the GCS URI."""
    storage_client = storage.Client(project=GCP_PROJECT_ID)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # Check if blob already exists
    if blob.exists():
        st.info(f"✅ Video already exists in GCS: gs://{bucket_name}/{blob_name}")
    else:
        st.info(f"Uploading video to GCS: gs://{bucket_name}/{blob_name}")
        with st.spinner("Uploading video to Google Cloud Storage..."):
            blob.upload_from_filename(local_path)
        st.success(f"Video uploaded to GCS!")

    gcs_uri = f"gs://{bucket_name}/{blob_name}"
    mime_type, _ = mimetypes.guess_type(local_path)
    if not mime_type:
        mime_type = "video/mp4"

    return gcs_uri, mime_type


def get_or_create_cache(gcs_uri: str, mime_type: str) -> tuple[str, int]:
    """Create context cache from GCS video URI or return existing cache."""

    cache_display_name = f"video_cache_{os.path.basename(VIDEO_PATH)}"

    # Check for existing caches
    st.info("🔍 Checking for existing cache...")
    try:
        for existing_cache in client.caches.list():
            if hasattr(existing_cache, 'display_name') and existing_cache.display_name == cache_display_name:
                # Found existing cache - verify it's still valid
                st.success(f"✅ Found existing cache: {cache_display_name}")
                token_count = existing_cache.usage_metadata.total_token_count if hasattr(existing_cache, 'usage_metadata') else 0
                return existing_cache.name, token_count
    except Exception as e:
        st.warning(f"Could not check existing caches: {e}")

    # No existing cache found - create new one
    st.info("No existing cache found. Creating new cache...")

    # System instruction for forensic analyst persona
    system_instruction = (
        "You are a multimodal forensic analyst. You have been provided with a "
        "medium-length video. Use both visual cues and audio transcripts to provide "
        "evidence-based answers. Always include [MM:SS] timestamps when referencing "
        "specific moments in the video. If the user asks for a summary, provide a "
        "bulleted 'Scene Breakdown' with key events and their timestamps."
    )

    # Build contents with GCS URI
    contents = [
        Content(
            role="user",
            parts=[
                Part.from_uri(
                    file_uri=gcs_uri,
                    mime_type=mime_type,
                )
            ],
        )
    ]

    # Create cache with progress indicator
    with st.status("Creating context cache (this may take 60-120 seconds for longer videos)...", expanded=True) as status:
        st.write("📦 Tokenizing video content...")
        st.write("🔄 Building context index...")

        cache = client.caches.create(
            model=GEMINI_MODEL,
            config=CreateCachedContentConfig(
                contents=contents,
                system_instruction=system_instruction,
                display_name=cache_display_name,
                ttl="3600s",  # 1 hour
            ),
        )

        st.write("✅ Cache created successfully!")
        status.update(label="Context cache ready!", state="complete")

    # Extract token count from usage metadata
    token_count = cache.usage_metadata.total_token_count if hasattr(cache, 'usage_metadata') else 0

    return cache.name, token_count


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "cache_name" not in st.session_state:
        if not os.path.exists(VIDEO_PATH):
            st.error(f"Video file not found at: {VIDEO_PATH}")
            st.info("Please update the VIDEO_PATH in your .env file to point to a valid video file.")
            st.stop()

        # Construct blob name using original filename
        video_filename = os.path.basename(VIDEO_PATH)
        # Keep folder structure from GCS_BLOB_NAME (e.g., "videos/") and append actual filename
        folder_path = os.path.dirname(GCS_BLOB_NAME)
        blob_name = f"{folder_path}/{video_filename}" if folder_path else video_filename

        # Step 1: Upload to GCS (existing)
        gcs_uri, mime_type = upload_to_gcs(VIDEO_PATH, GCS_BUCKET_NAME, blob_name)
        st.session_state.video_uri = gcs_uri
        st.session_state.video_mime_type = mime_type

        # Step 2: Create context cache (new)
        cache_name, token_count = get_or_create_cache(gcs_uri, mime_type)
        st.session_state.cache_name = cache_name
        st.session_state.cache_tokens = token_count


def main():
    st.set_page_config(page_title="Video Analyzer", page_icon="🎥", layout="wide")
    st.title("🎥 Video Analyzer - Phase 2")
    st.caption(f"Chat with your video using {GEMINI_MODEL} with Context Caching")

    initialize_session_state()

    st.sidebar.header("Video Information")
    st.sidebar.write(f"**File:** {os.path.basename(VIDEO_PATH)}")
    st.sidebar.write(f"**GCS URI:** {st.session_state.video_uri}")
    st.sidebar.write(f"**MIME Type:** {st.session_state.video_mime_type}")
    st.sidebar.write(f"**Model:** {GEMINI_MODEL}")

    st.sidebar.header("Context Cache")
    st.sidebar.write(f"**Status:** 🟢 Active (1 hour TTL)")
    st.sidebar.write(f"**Cached Tokens:** {st.session_state.cache_tokens:,}")
    st.sidebar.caption(f"Cache ID: {st.session_state.cache_name.split('/')[-1]}")
    st.sidebar.info("💡 Subsequent queries use cached context for 3x faster responses!")

    # Clear cache button
    if st.sidebar.button("🗑️ Clear Cache", help="Delete the current cache and create a new one on next query"):
        try:
            # Delete cache from Vertex AI
            client.caches.delete(name=st.session_state.cache_name)

            # Clear session state to force recreation
            del st.session_state.cache_name
            del st.session_state.cache_tokens

            st.sidebar.success("✅ Cache cleared! Refresh the page to create a new cache.")
            st.balloons()
        except Exception as e:
            st.sidebar.error(f"Failed to delete cache: {e}")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question about the video..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing video..."):
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config=GenerateContentConfig(
                        cached_content=st.session_state.cache_name
                    ),
                )

                assistant_message = response.text
                st.markdown(assistant_message)
                st.session_state.messages.append({"role": "assistant", "content": assistant_message})

                # Display token usage if available
                if hasattr(response, 'usage_metadata'):
                    usage = response.usage_metadata
                    with st.expander("📊 Token Usage"):
                        st.write(f"Cached tokens: {usage.cached_content_token_count:,}")
                        st.write(f"Prompt tokens: {usage.prompt_token_count:,}")
                        st.write(f"Response tokens: {usage.candidates_token_count:,}")


if __name__ == "__main__":
    main()
