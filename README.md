# Video Analyser - Phase 2 (Context Caching Enhancement)

A video analysis application that leverages Gemini's context caching for fast, efficient analysis of medium-length videos (up to 60 minutes) via Vertex AI.

## Phase 2 Features ✨

- **Context Caching**: Videos are tokenized once and cached for 1 hour, enabling 3x faster response times
- **Medium Video Support**: Handles videos up to 60 minutes using Gemini 2.5 Flash's 1M+ token window
- **Session Persistence**: The video context stays "warm" for subsequent queries within the cache TTL
- **Forensic Analysis Mode**: System instruction optimized for detailed video analysis with timestamps
- **Token Usage Tracking**: Real-time visibility into cached vs. new token consumption

## Prerequisites
1.  **Authentication:** Authenticate with Google Cloud using Application Default Credentials
2.  **GCS Bucket:** A Google Cloud Storage bucket to store video files
3.  **Video File:** A local `.mp4` or `.mov` file (5-60 minutes recommended)
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
- `GCS_BLOB_NAME`: The folder path in GCS (e.g., `videos/`). The actual filename will match your `VIDEO_PATH` filename
- `VIDEO_PATH`: Path to your local video file (e.g., `./video.mp4`). This filename will be used in GCS
- `GEMINI_MODEL`: The Gemini model to use (e.g., `gemini-2.5-flash`, `gemini-1.5-pro`)

**Example:** If `VIDEO_PATH=./my-video.mp4` and `GCS_BLOB_NAME=videos/`, the file will be uploaded to `gs://your-bucket/videos/my-video.mp4`

### 3. Run the App
Using `uv`, you can run the app directly:
```bash
uv run streamlit run app.py
```

**Initial Load Time:** The first run may take 60-120 seconds for cache creation (depending on video length). Subsequent queries within the 1-hour cache window will be nearly instant.

## How it Works

### Phase 2 Architecture with Context Caching
```
Local Video → Upload to GCS → Create Context Cache → Fast Multi-turn Chat
                                      ↓
                              (Cache valid for 1 hour)
                                      ↓
                         All queries use cached context
```

### Detailed Flow
1. **Upload**: Video uploaded to Google Cloud Storage
2. **Tokenization**: Video content tokenized and indexed (one-time operation)
3. **Cache Creation**: Context cache created with 1-hour TTL and forensic analyst system instruction
4. **Query Processing**: User questions reference the cached context instead of re-processing the video
5. **Token Efficiency**: Only new prompt and response tokens are charged; cached tokens are discounted

## System Instruction

The cached context includes a forensic analyst persona that:
- Provides evidence-based answers using visual and audio cues
- Always includes `[MM:SS]` timestamps when referencing specific moments
- Generates structured "Scene Breakdown" summaries when requested
- Focuses on factual, observable content from the video

## Token Usage

Example for a 30-minute video:
- **Cached tokens**: ~500,000 (video content, tokenized once)
- **Prompt tokens**: ~50 per query (your question)
- **Response tokens**: ~200-500 per answer

With caching, you only pay full price for the first query. Subsequent queries use cached content at a significant discount.

## Performance Benefits

| Metric | Phase 1 (No Cache) | Phase 2 (Cached) |
|--------|-------------------|------------------|
| First query | 15-30s | 60-120s (includes cache creation) |
| Follow-up queries | 15-30s each | 2-5s each |
| Token cost per query | Full price | Discounted (cached tokens) |
| Video re-processing | Every query | Once per hour |

## Cache Management

- **TTL**: 1 hour (3600 seconds)
- **Auto-refresh**: Cache persists across page refreshes within the same session
- **Display Name**: `video_cache_{filename}` for easy identification
- **Monitoring**: Sidebar shows cache status and token count

## Security Notes
- Never commit your `.env` file to version control (it's in `.gitignore`)
- The `.env.example` file contains only placeholder values for reference
- Keep your GCP project ID and bucket names private
- Cached content is automatically deleted after TTL expiration

## Troubleshooting

**Cache creation takes too long**:
- Normal for videos >30 minutes
- First-time tokenization is a one-time cost

**"Cache not found" errors**:
- Cache may have expired (1 hour TTL)
- Refresh the page to create a new cache

**Token count shows 0**:
- Some model versions may not return usage metadata
- Functionality is not affected
