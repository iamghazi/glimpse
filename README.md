# Video Analyser Prototype

A simple application to chat with a video file using Gemini via Vertex AI.

## Prerequisites
1.  **Authentication:** Authenticate with Google Cloud using Application Default Credentials
2.  **GCS Bucket:** A Google Cloud Storage bucket to store video files
3.  **Video File:** A local `.mp4` or `.mov` file to analyze
4.  **GCP Project:** A Google Cloud project with Vertex AI API enabled

## Setup Instructions

### 1. Authenticate with Google Cloud
```bash
gcloud auth application-default login
```
This creates credentials at `~/.config/gcloud/application_default_credentials.json`

### 2. Configure Environment Variables
Create a `.env` file in the root directory by copying the example:
```bash
cp .env.example .env
```

Then edit `.env` and configure the following variables:

- `GCP_PROJECT_ID`: Your Google Cloud project ID
- `GCP_LOCATION`: The region for Vertex AI (e.g., `us-central1`, `asia-south1`)
- `GCS_BUCKET_NAME`: Your GCS bucket name for storing videos
- `GCS_BLOB_NAME`: The destination path in GCS (e.g., `videos/uploaded_video.mp4`)
- `VIDEO_PATH`: Path to your local video file (e.g., `./video.mp4`)
- `GEMINI_MODEL`: The Gemini model to use (e.g., `gemini-2.5-flash`, `gemini-1.5-pro`)

### 3. Run the App
Using `uv`, you can run the app directly:
```bash
uv run streamlit run app.py
```

## How it Works
1. The app loads configuration from your `.env` file
2. It uploads the video at `VIDEO_PATH` to Google Cloud Storage
3. The GCS URI is then passed to Gemini via Vertex AI for analysis
4. You can ask questions in the chat interface to analyze visual or auditory content

## Architecture
```
Local Video → Upload to GCS → Pass GCS URI to Gemini (Vertex AI) → Chat Interface
```

## Security Notes
- Never commit your `.env` file to version control (it's in `.gitignore`)
- The `.env.example` file contains only placeholder values for reference
- Keep your GCP project ID and bucket names private
