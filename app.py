import os
import mimetypes
import streamlit as st
from dotenv import load_dotenv
from google import genai
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
    st.info(f"Uploading video to GCS: gs://{bucket_name}/{blob_name}")

    with st.spinner("Uploading video to Google Cloud Storage..."):
        storage_client = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_path)

    gcs_uri = f"gs://{bucket_name}/{blob_name}"
    mime_type, _ = mimetypes.guess_type(local_path)
    if not mime_type:
        mime_type = "video/mp4"

    st.success(f"Video uploaded to GCS: {gcs_uri}")
    return gcs_uri, mime_type


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "video_uri" not in st.session_state:
        if not os.path.exists(VIDEO_PATH):
            st.error(f"Video file not found at: {VIDEO_PATH}")
            st.info("Please update the VIDEO_PATH in your .env file to point to a valid video file.")
            st.stop()

        gcs_uri, mime_type = upload_to_gcs(VIDEO_PATH, GCS_BUCKET_NAME, GCS_BLOB_NAME)
        st.session_state.video_uri = gcs_uri
        st.session_state.video_mime_type = mime_type


def main():
    st.set_page_config(page_title="Video Analyzer", page_icon="🎥", layout="wide")
    st.title("🎥 Video Analyzer")
    st.caption(f"Chat with your video using {GEMINI_MODEL}")

    initialize_session_state()

    st.sidebar.header("Video Information")
    st.sidebar.write(f"**File:** {os.path.basename(VIDEO_PATH)}")
    st.sidebar.write(f"**GCS URI:** {st.session_state.video_uri}")
    st.sidebar.write(f"**MIME Type:** {st.session_state.video_mime_type}")
    st.sidebar.write(f"**Model:** {GEMINI_MODEL}")

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
                    contents=[
                        {
                            "role": "user",
                            "parts": [
                                {
                                    "file_data": {
                                        "file_uri": st.session_state.video_uri,
                                        "mime_type": st.session_state.video_mime_type,
                                    }
                                },
                                {
                                    "text": prompt
                                },
                            ],
                        }
                    ],
                )

                assistant_message = response.text
                st.markdown(assistant_message)
                st.session_state.messages.append({"role": "assistant", "content": assistant_message})


if __name__ == "__main__":
    main()
