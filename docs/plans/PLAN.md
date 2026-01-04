# Phase 3: Video Library Search Engine - Implementation Plan

## Overview
Transform the current single-video analyzer (Phase 2) into a multi-video RAG system that indexes a library of videos, enables semantic search across all videos, and selectively caches only relevant clips for analysis.

## Architecture Comparison

### Current (Phase 2)
```
Local Video → GCS Upload → Full Video Cache → Chat
```

### Target (Phase 3)
```
Local Video Library → Chunking (60s/10s overlap) → Audio Transcription → Multimodal Embedding → Qdrant Index
                                                                                                    ↓
User Query → Embed Query → Search Qdrant → Retrieve Top-K Clips → Selective Cache → Chat
```

## Configuration (User-Specified)

✅ **Confirmed Requirements:**

1. **Project Structure**: Migrate current app (replace Phase 2)
2. **Backend Pattern**: FastAPI + Inngest (async processing)
3. **Video Chunking**: Time-based, 60 seconds per chunk, 10 seconds overlap, 1 FPS frame extraction
4. **Video Storage**: Qdrant for vectors + Local video files (no GCS)
5. **Migration Strategy**: Replace Phase 2 with Phase 3
6. **Embedding Model**: multimodal-embedding-001 (1408-dim)
7. **Audio Processing**: Extract transcripts using Whisper
8. **AI Platform**: Vertex AI (not google-genai)
9. **UI Framework**: Multi-page Streamlit app

## Tech Stack

### Following RAG App Pattern
- **Backend**: FastAPI + Uvicorn (port 8000)
- **Event System**: Inngest (port 8288)
- **Frontend**: Streamlit Multi-Page App (port 8501)
- **Vector DB**: Qdrant via Docker (port 6333)
- **Video Processing**: moviepy (chunking), opencv-python (1 FPS frame extraction)
- **Audio Transcription**: OpenAI Whisper (local or API)
- **Embeddings**: Vertex AI `multimodal-embedding-001` (1408-dim)
- **LLM**: Vertex AI Gemini 2.5 Flash/Pro with selective caching
- **Storage**: Local videos (`./videos/`) + Qdrant vectors + Local metadata (SQLite or JSON)

## Implementation Strategy (Revised for Testability)

**Key Change**: Build frontend-first with incremental backend features, allowing testing at each step.

### Iterative Development Flow:
```
1. UI Skeleton → Test navigation
2. Upload UI + API → Test file upload
3. Video Processing → Test indexing progress
4. Search UI + API → Test semantic search
5. Chat UI + Caching → Test Q&A
6. Optimization → Performance testing
```

**Why This Approach?**
- ✅ Testable after each phase
- ✅ Visual feedback during development
- ✅ Catch integration issues early
- ✅ More motivating progress tracking

---

## Implementation Phases

---

## Phase 3.1: Foundation Setup (✅ COMPLETED)
**Goal**: Set up infrastructure (Qdrant, dependencies, project structure)

### Step 3.1.1: Project Structure Migration
**Action**: Reorganize current app for Phase 3
```
video-analyser/
├── app_phase2.py.bak         # Backup of Phase 2 app
├── main.py                   # NEW: FastAPI + Inngest functions
├── pages/                    # NEW: Streamlit multi-page
│   ├── 1_📚_Library.py      # Video upload & management
│   ├── 2_🔍_Search.py       # Semantic search
│   └── 3_💬_Chat.py         # Chat with selected clips
├── Home.py                   # NEW: Streamlit home/landing
├── video_indexer.py          # NEW: Chunking + transcription + embedding
├── vector_db.py              # NEW: Qdrant wrapper
├── cache_manager.py          # NEW: Selective caching logic
├── custom_types.py           # NEW: Pydantic models
├── videos/                   # NEW: Local video storage
│   └── .gitkeep
├── metadata/                 # NEW: Video metadata (SQLite)
│   └── .gitkeep
├── frames/                   # NEW: Extracted frames
│   └── .gitkeep
├── .env                      # Update with new vars
├── pyproject.toml            # Add new dependencies
└── README.md                 # Update for Phase 3
```

**Test Checkpoint 3.1.1**:
- [ ] Phase 2 app backed up to `app_phase2.py.bak`
- [ ] New directory structure created (`pages/`, `videos/`, `metadata/`, `frames/`)
- [ ] `.env` file updated with new variables
- [ ] Streamlit multi-page structure initialized

### Step 3.1.2: Dependencies
**Action**: Add required packages to `pyproject.toml`
```toml
dependencies = [
    "fastapi>=0.115.6",
    "google-genai>=1.56.0",              # For Vertex AI multimodal embeddings
    "google-cloud-aiplatform>=1.70.0",   # For Vertex AI client
    "inngest>=0.6.1",
    "moviepy>=1.0.3",
    "opencv-python>=4.10.0",
    "openai-whisper>=20231117",          # Audio transcription
    "python-dotenv>=1.2.1",
    "qdrant-client>=1.13.1",
    "streamlit>=1.52.2",
    "uvicorn>=0.32.1",
    "pillow>=10.0.0",                    # Image processing
    "numpy>=1.24.0",                     # Array operations
]
```

**Environment Variables Update** (`.env`):
```bash
# Google Cloud Configuration (existing)
GCP_PROJECT_ID=paid-video-project
GCP_LOCATION=us-central1

# Gemini Model Configuration (existing)
GEMINI_MODEL=gemini-2.5-pro

# NEW: Vector DB Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333

# NEW: Video Processing Configuration
CHUNK_DURATION_SECONDS=60
CHUNK_OVERLAP_SECONDS=10
FRAME_EXTRACTION_FPS=1

# NEW: Storage Paths
VIDEOS_DIR=./videos
FRAMES_DIR=./frames
METADATA_DIR=./metadata
```

**Test Checkpoint 3.1.2**:
```bash
uv sync
uv run python -c "import moviepy.editor, cv2, whisper, qdrant_client, google.genai; print('✅ All imports work')"
```
- [ ] All dependencies installed
- [ ] Import test passes
- [ ] Whisper model downloads successfully

### Step 3.1.3: Qdrant Setup
**Action**: Start Qdrant via Docker
```bash
docker run -d \
  --name qdrant-video \
  -p 6333:6333 \
  -v "$(pwd)/qdrant_storage:/qdrant/storage" \
  qdrant/qdrant
```

**Test Checkpoint 3.1.3**:
```bash
curl http://localhost:6333/collections
# Should return empty list or existing collections
```
- [ ] Qdrant container running
- [ ] Port 6333 accessible
- [ ] Storage volume mounted

---

## Phase 3.2: Data Models & Vector DB
**Goal**: Define data structures and Qdrant integration

### Step 3.2.1: Custom Types
**Action**: Create `custom_types.py` with models
```python
class VideoMetadata(BaseModel):
    video_id: str              # Unique ID (UUID)
    title: str                 # Display name
    file_path: str            # Local path: ./videos/{video_id}.mp4
    duration_seconds: float
    fps: float
    resolution: tuple[int, int]  # (width, height)
    file_size_mb: float
    uploaded_at: datetime
    indexed_at: Optional[datetime]

class VideoChunk(BaseModel):
    chunk_id: str             # f"{video_id}_{start_time}_{end_time}"
    video_id: str
    start_time: float         # Seconds
    end_time: float
    duration: float           # Should be 60s (last chunk may be shorter)
    visual_description: str   # AI-generated from frames
    audio_transcript: str     # Whisper transcription
    frame_paths: list[str]   # Paths to extracted frames (1 FPS = ~60 frames)
    representative_frame: str # Middle frame for thumbnails

class VideoChunkWithEmbedding(VideoChunk):
    embedding: list[float]   # 1408-dim from multimodal-embedding-001

class SearchResult(BaseModel):
    chunk_id: str
    video_id: str
    title: str
    start_time: float
    end_time: float
    visual_description: str
    audio_transcript: str
    score: float             # Cosine similarity score
    video_path: str         # For selective cache creation
    representative_frame: str

class LibrarySearchResult(BaseModel):
    results: list[SearchResult]
    total_found: int
    query_embedding: list[float]  # For debugging
```

**Test Checkpoint 3.2.1**:
```python
# test_types.py
from custom_types import VideoMetadata, VideoChunk
meta = VideoMetadata(video_id="test", title="Test", gcs_uri="gs://...",
                     duration_seconds=120, uploaded_at=datetime.now())
chunk = VideoChunk(chunk_id="test_0_30", video_id="test", start_time=0,
                   end_time=30, duration=30, description="Test scene",
                   frame_path="/tmp/frame.jpg")
print("✅ Models validate correctly")
```
- [ ] All models defined
- [ ] Validation test passes

### Step 3.2.2: Vector DB Wrapper
**Action**: Create `vector_db.py` with Qdrant client
```python
class VideoVectorDB:
    def __init__(self, host="localhost", port=6333):
        # Connect to Qdrant
        # Create "video_chunks" collection (1408-dim, COSINE)

    def upsert_chunks(self, chunks: list[VideoChunkWithEmbedding]):
        # Batch upload with metadata

    def search(self, query_embedding: list[float], top_k=5) -> list[SearchResult]:
        # Semantic search with filters

    def delete_video(self, video_id: str):
        # Remove all chunks for a video

    def list_videos(self) -> list[str]:
        # Get unique video IDs
```

**Test Checkpoint 3.2.2**:
```python
# test_vector_db.py
from vector_db import VideoVectorDB
db = VideoVectorDB()
print("Collections:", db.client.get_collections())
# Should show "video_chunks" collection created
```
- [ ] Qdrant client connects
- [ ] Collection created with correct dimensions
- [ ] CRUD operations work

---

## Phase 3.3: Streamlit UI Skeleton (NEW PRIORITY)
**Goal**: Build multi-page Streamlit app for immediate testing

### Step 3.3.1: Create Home Page
**Action**: Create `Home.py` landing page
```python
# Home.py
import streamlit as st

st.set_page_config(page_title="Video Library", page_icon="🎥", layout="wide")

st.title("🎥 Video Library Search Engine")
st.write("Welcome to your intelligent video library!")

st.info("👈 Use the sidebar to navigate between pages")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Videos Indexed", "0", help="Total videos in library")

with col2:
    st.metric("Chunks Stored", "0", help="Video segments indexed")

with col3:
    st.metric("Search Ready", "Yes" if True else "No")

st.divider()

st.subheader("Quick Start")
st.write("1. **📚 Library**: Upload and manage videos")
st.write("2. **🔍 Search**: Find moments across all videos")
st.write("3. **💬 Chat**: Analyze selected clips with AI")
```

**Test Checkpoint 3.3.1**:
```bash
uv run streamlit run Home.py
# Navigate to http://localhost:8501
```
- [ ] Home page displays
- [ ] Metrics show (even if 0)
- [ ] Instructions visible

### Step 3.3.2: Create Library Page
**Action**: Create `pages/1_📚_Library.py`
```python
# pages/1_📚_Library.py
import streamlit as st
import os

st.set_page_config(page_title="Video Library", page_icon="📚", layout="wide")

st.title("📚 Video Library")

# Upload section
st.header("Upload Video")
uploaded_file = st.file_uploader(
    "Choose a video file",
    type=["mp4", "mov", "avi"],
    help="Upload a video to add to your library"
)

if uploaded_file:
    st.video(uploaded_file)
    col1, col2 = st.columns(2)

    with col1:
        video_title = st.text_input("Video Title", value=uploaded_file.name)

    with col2:
        st.write(f"Size: {uploaded_file.size / 1024 / 1024:.1f} MB")

    if st.button("🚀 Index Video", type="primary"):
        st.info("Backend not connected yet - coming in Phase 3.4!")

st.divider()

# Video list section
st.header("Your Videos")
st.info("No videos yet. Upload your first video above!")

# Placeholder for future video grid
# Will show: thumbnails, titles, duration, delete button
```

**Test Checkpoint 3.3.2**:
- [ ] Can navigate to Library page
- [ ] File uploader accepts videos
- [ ] Video preview works
- [ ] Upload button shows (even if non-functional)

### Step 3.3.3: Create Search Page
**Action**: Create `pages/2_🔍_Search.py`
```python
# pages/2_🔍_Search.py
import streamlit as st

st.set_page_config(page_title="Search Videos", page_icon="🔍", layout="wide")

st.title("🔍 Search Video Library")

# Search input
query = st.text_input(
    "What are you looking for?",
    placeholder="e.g., 'scenes with people cooking', 'sunset landscapes', 'dialogue about technology'",
    help="Describe what you want to find across all your videos"
)

col1, col2 = st.columns([3, 1])
with col1:
    search_mode = st.radio(
        "Search mode",
        ["Semantic (AI-powered)", "Keyword (simple)"],
        horizontal=True,
        index=0
    )

with col2:
    top_k = st.slider("Results", 1, 20, 5)

if st.button("🔍 Search", type="primary"):
    if not query:
        st.warning("Please enter a search query")
    else:
        st.info("Backend not connected yet - coming in Phase 3.8!")

st.divider()

# Results placeholder
st.subheader("Search Results")
st.info("Enter a query above to search your video library")
```

**Test Checkpoint 3.3.3**:
- [ ] Search page loads
- [ ] Input fields work
- [ ] Search button shows
- [ ] Placeholder results section visible

### Step 3.3.4: Create Chat Page
**Action**: Create `pages/3_💬_Chat.py`
```python
# pages/3_💬_Chat.py
import streamlit as st

st.set_page_config(page_title="Chat with Clips", page_icon="💬", layout="wide")

st.title("💬 Chat with Video Clips")

# Sidebar for selected clips
with st.sidebar:
    st.header("Selected Clips")

    if "selected_clips" not in st.session_state:
        st.session_state.selected_clips = []

    if not st.session_state.selected_clips:
        st.info("No clips selected.\n\nSearch for videos and select clips to analyze.")
    else:
        for i, clip in enumerate(st.session_state.selected_clips):
            with st.expander(f"Clip {i+1}"):
                st.write(f"**Video:** {clip.get('title', 'Unknown')}")
                st.write(f"**Time:** {clip.get('start_time', 0):.0f}s - {clip.get('end_time', 0):.0f}s")

# Chat interface
st.write("Ask questions about the selected video clips using AI-powered analysis.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about the selected clips..."):
    if not st.session_state.selected_clips:
        st.warning("Please select some clips from the Search page first!")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Placeholder response
        with st.chat_message("assistant"):
            st.info("Backend not connected yet - coming in Phase 3.9!")
```

**Test Checkpoint 3.3.4**:
- [ ] Chat page loads
- [ ] Sidebar shows selected clips area
- [ ] Chat input works
- [ ] Messages display correctly

---

## Phase 3.4: Basic FastAPI Backend
**Goal**: Create backend with Inngest for video upload

### Step 3.4.1: Create main.py with FastAPI
**Action**: Set up FastAPI app with Inngest
```python
# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from inngest import Inngest
import os
import shutil
import uuid
from datetime import datetime
from custom_types import IngestVideoRequest, IngestVideoResponse
from vector_db import VideoVectorDB

app = FastAPI(title="Video Library API")

# CORS for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inngest client
inngest_client = Inngest(app_id="video-library")

# Initialize DB
vector_db = VideoVectorDB()

@app.get("/")
async def root():
    return {"status": "ok", "app": "Video Library API"}

@app.get("/health")
async def health():
    db_info = vector_db.get_collection_info()
    return {
        "status": "healthy",
        "qdrant": db_info,
        "videos_dir": os.path.exists("./videos"),
    }

@app.post("/upload")
async def upload_video(file: UploadFile = File(...), title: str = None):
    """Upload video and trigger indexing"""
    # Generate video ID
    video_id = str(uuid.uuid4())

    # Save to videos directory
    file_path = f"./videos/{video_id}.mp4"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Trigger Inngest function (will implement in next phase)
    # await inngest_client.send(...)

    return {
        "video_id": video_id,
        "title": title or file.filename,
        "status": "uploaded",
        "message": "Video saved. Indexing will be added in Phase 3.5"
    }

@app.get("/videos")
async def list_videos():
    """List all indexed videos"""
    video_ids = vector_db.list_videos()
    return {"videos": video_ids, "count": len(video_ids)}
```

**Test Checkpoint 3.4.1**:
```bash
# Terminal 1: Start FastAPI
uv run fastapi dev main.py

# Terminal 2: Test health
curl http://localhost:8000/health

# Terminal 3: Test from Streamlit UI
# Update Library page to call /upload endpoint
```
- [ ] FastAPI starts on port 8000
- [ ] Health endpoint returns OK
- [ ] Can upload video from Streamlit UI
- [ ] Video file saved to ./videos/

---

## Phase 3.5: Video Processing Pipeline
**Goal**: Chunk videos and generate embeddings (backend only, triggered by upload)

[Rest of the video indexing implementation from original Phase 3.3]

---

## Phase 3.6-3.10: Continue with remaining phases...

### Step 3.3.1: Video Chunker with Frame Extraction
**Action**: Create `video_indexer.py` - chunking logic
```python
import cv2
import whisper
from moviepy.editor import VideoFileClip

class VideoChunker:
    def __init__(self,
                 chunk_duration_seconds=60,  # User-specified: 60s
                 chunk_overlap_seconds=10,   # User-specified: 10s
                 frame_extraction_fps=1):    # User-specified: 1 FPS
        self.chunk_duration = chunk_duration_seconds
        self.chunk_overlap = chunk_overlap_seconds
        self.fps = frame_extraction_fps
        self.whisper_model = whisper.load_model("base")  # or "small" for better accuracy

    def chunk_video(self, video_path: str, video_id: str) -> list[VideoChunk]:
        # 1. Load video with moviepy
        video = VideoFileClip(video_path)
        duration = video.duration

        # 2. Calculate chunks with overlap
        chunks = []
        current_time = 0
        while current_time < duration:
            start_time = current_time
            end_time = min(current_time + self.chunk_duration, duration)

            # 3. Extract frames at 1 FPS
            frame_paths = self._extract_frames(video, start_time, end_time, video_id)

            # 4. Extract audio and transcribe
            audio_transcript = self._transcribe_chunk(video, start_time, end_time)

            chunk = VideoChunk(
                chunk_id=f"{video_id}_{int(start_time)}_{int(end_time)}",
                video_id=video_id,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                visual_description="",  # Will be filled by Gemini
                audio_transcript=audio_transcript,
                frame_paths=frame_paths,
                representative_frame=frame_paths[len(frame_paths)//2] if frame_paths else ""
            )
            chunks.append(chunk)

            # Move to next chunk (with overlap)
            current_time += (self.chunk_duration - self.chunk_overlap)

        return chunks

    def _extract_frames(self, video: VideoFileClip, start_time: float,
                       end_time: float, video_id: str) -> list[str]:
        """Extract frames at 1 FPS between start_time and end_time"""
        frame_paths = []
        for t in range(int(start_time), int(end_time)):
            frame = video.get_frame(t)
            frame_filename = f"{FRAMES_DIR}/{video_id}_{t}.jpg"
            cv2.imwrite(frame_filename, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            frame_paths.append(frame_filename)
        return frame_paths

    def _transcribe_chunk(self, video: VideoFileClip, start_time: float,
                         end_time: float) -> str:
        """Extract audio segment and transcribe with Whisper"""
        # Extract audio segment
        audio_segment = video.subclip(start_time, end_time).audio
        temp_audio = f"/tmp/audio_{int(start_time)}_{int(end_time)}.wav"
        audio_segment.write_audiofile(temp_audio, verbose=False, logger=None)

        # Transcribe with Whisper
        result = self.whisper_model.transcribe(temp_audio)

        # Clean up temp file
        os.remove(temp_audio)

        return result["text"]
```

**Test Checkpoint 3.3.1**:
```python
# test_chunker.py
chunker = VideoChunker(chunk_duration_seconds=60, chunk_overlap_seconds=10, frame_extraction_fps=1)
chunks = chunker.chunk_video("./videos/test-video.mp4", "test_001")
print(f"Created {len(chunks)} chunks")
for chunk in chunks[:2]:
    print(f"  Chunk {chunk.chunk_id}:")
    print(f"    Time: {chunk.start_time}-{chunk.end_time}s")
    print(f"    Frames: {len(chunk.frame_paths)} frames")
    print(f"    Transcript: {chunk.audio_transcript[:100]}...")
```
- [ ] Video splits into 60s chunks with 10s overlap
- [ ] Frames extracted at 1 FPS (~60 frames per chunk)
- [ ] Audio transcribed with Whisper
- [ ] Metadata correctly populated

### Step 3.3.2: Scene Description Generator (Vertex AI)
**Action**: Add description generation to `video_indexer.py`
```python
from google import genai
from google.genai.types import Part, Content

class VideoIndexer:
    def __init__(self, gcp_project_id: str, gcp_location: str, model_name: str):
        self.client = genai.Client(
            vertexai=True,
            project=gcp_project_id,
            location=gcp_location
        )
        self.model = model_name  # gemini-2.5-pro
        self.chunker = VideoChunker(
            chunk_duration_seconds=60,
            chunk_overlap_seconds=10,
            frame_extraction_fps=1
        )

    def generate_scene_description(self, frame_paths: list[str],
                                   audio_transcript: str) -> str:
        """
        Generate visual description using Gemini Flash with multiple frames.
        Combines visual analysis with audio transcript for context.
        """
        # Use middle frame as primary + 2 context frames
        primary_frame = frame_paths[len(frame_paths)//2]
        context_frames = [frame_paths[0], frame_paths[-1]] if len(frame_paths) > 2 else []

        # Build multimodal prompt
        parts = [
            Part.from_text(
                "Analyze this video segment. Describe the visual scene in 2-3 sentences. "
                f"Audio context: \"{audio_transcript[:200]}...\""
            )
        ]

        # Add frames
        with open(primary_frame, 'rb') as f:
            parts.append(Part.from_bytes(data=f.read(), mime_type="image/jpeg"))

        # Generate description
        response = self.client.models.generate_content(
            model=self.model,
            contents=Content(role="user", parts=parts)
        )

        return response.text

    def index_video(self, video_path: str, video_id: str) -> list[VideoChunk]:
        # 1. Chunk video (includes frame extraction and transcription)
        chunks = self.chunker.chunk_video(video_path, video_id)

        # 2. For each chunk, generate visual description
        for chunk in chunks:
            chunk.visual_description = self.generate_scene_description(
                chunk.frame_paths,
                chunk.audio_transcript
            )

        # 3. Return enriched chunks (ready for embedding)
        return chunks
```

**Test Checkpoint 3.3.2**:
```python
indexer = VideoIndexer(gemini_client)
chunks = indexer.index_video("./test-video.mp4", "test_video_001")
for chunk in chunks[:2]:
    print(f"{chunk.start_time}s: {chunk.description}")
# Should show AI-generated descriptions
```
- [ ] Descriptions generated for frames
- [ ] Reasonable quality summaries
- [ ] No API errors

### Step 3.3.3: Multimodal Embedding (Vertex AI)
**Action**: Add embedding generation to `video_indexer.py`
```python
def embed_video_chunks(self, chunks: list[VideoChunk]) -> list[VideoChunkWithEmbedding]:
    """
    Generate multimodal embeddings using Vertex AI.
    Combines: visual (image) + text (description + transcript)
    Returns 1408-dimensional vectors.
    """
    chunks_with_embeddings = []

    for chunk in chunks:
        # Combine text context: visual description + audio transcript
        text_content = f"Visual: {chunk.visual_description}\nAudio: {chunk.audio_transcript}"

        # Create multimodal content for embedding
        parts = [
            Part.from_text(text_content),
            Part.from_uri(
                file_uri=chunk.representative_frame,  # Use representative frame
                mime_type="image/jpeg"
            )
        ]

        # Generate embedding using multimodal-embedding-001
        embedding_response = self.client.models.embed_content(
            model="multimodal-embedding-001",
            contents=Content(role="user", parts=parts)
        )

        # Extract embedding vector (1408-dim)
        embedding = embedding_response.embeddings[0].values

        # Create chunk with embedding
        chunk_with_emb = VideoChunkWithEmbedding(
            **chunk.model_dump(),
            embedding=embedding
        )
        chunks_with_embeddings.append(chunk_with_emb)

    return chunks_with_embeddings
```

**Test Checkpoint 3.3.3**:
```python
indexer = VideoIndexer(GCP_PROJECT_ID, GCP_LOCATION, GEMINI_MODEL)
chunks = indexer.index_video("./videos/test.mp4", "test_001")
chunks_with_embeddings = indexer.embed_video_chunks(chunks)

print(f"Processed {len(chunks_with_embeddings)} chunks")
print(f"Embedding dimensions: {len(chunks_with_embeddings[0].embedding)}")
print(f"Sample visual: {chunks_with_embeddings[0].visual_description}")
print(f"Sample audio: {chunks_with_embeddings[0].audio_transcript[:100]}")
# Should be 1408 dimensions
```
- [ ] Embeddings generated using Vertex AI
- [ ] Correct dimensionality (1408)
- [ ] Multimodal content includes image + text
- [ ] Both visual and audio context embedded

---

## Phase 3.4: Backend with Inngest
**Goal**: FastAPI + Inngest functions for async processing

### Step 3.4.1: Inngest Functions
**Action**: Create `main.py` with event handlers
```python
# Inngest Function 1: video_library/ingest
@inngest_client.create_function(
    fn_id="video-library-ingest",
    trigger=inngest.TriggerEvent(event="video_library/ingest")
)
async def ingest_video(ctx, step):
    # Input: {video_path, video_id, title}
    # 1. Upload to GCS (if local)
    # 2. Chunk video
    # 3. Generate descriptions
    # 4. Create embeddings
    # 5. Upsert to Qdrant
    # Output: {chunks_count, video_id}

# Inngest Function 2: video_library/search
@inngest_client.create_function(
    fn_id="video-library-search",
    trigger=inngest.TriggerEvent(event="video_library/search")
)
async def search_library(ctx, step):
    # Input: {query, top_k}
    # 1. Embed query text
    # 2. Search Qdrant
    # 3. Return top-k results
    # Output: {results: list[SearchResult]}

# Inngest Function 3: video_library/chat
@inngest_client.create_function(
    fn_id="video-library-chat",
    trigger=inngest.TriggerEvent(event="video_library/chat")
)
async def chat_with_clips(ctx, step):
    # Input: {query, clip_ids: list[str]}
    # 1. Fetch clip GCS URIs from Qdrant
    # 2. Create temporary cache with selected clips
    # 3. Generate answer using cache
    # Output: {answer, sources: list[timestamp]}
```

**Test Checkpoint 3.4.1**:
```bash
# Terminal 1: Start Inngest dev server
npx inngest-cli@latest dev

# Terminal 2: Start FastAPI
uv run fastapi dev main.py

# Terminal 3: Test event
curl -X POST http://localhost:8288/e/video_library/ingest \
  -H "Content-Type: application/json" \
  -d '{"data": {"video_path": "./test.mp4", "video_id": "test", "title": "Test"}}'
```
- [ ] Inngest dev server running (port 8288)
- [ ] FastAPI running (port 8000)
- [ ] Functions registered in Inngest dashboard
- [ ] Test event triggers successfully

### Step 3.4.2: API Endpoints
**Action**: Add FastAPI routes in `main.py`
```python
@app.get("/videos")
async def list_videos():
    # Return all indexed videos from Qdrant metadata

@app.get("/videos/{video_id}/chunks")
async def get_video_chunks(video_id: str):
    # Return all chunks for a video

@app.delete("/videos/{video_id}")
async def delete_video(video_id: str):
    # Remove video and all chunks
```

**Test Checkpoint 3.4.2**:
```bash
curl http://localhost:8000/videos
# Should return list of videos
```
- [ ] All endpoints respond
- [ ] CORS configured for Streamlit
- [ ] Error handling works

---

## Phase 3.5: Streamlit UI
**Goal**: Two-mode interface (Library Search + Chat)

### Step 3.5.1: Library Management Page
**Action**: Create `streamlit_app.py` - Upload tab
```python
# Tab 1: Video Library
st.header("📚 Video Library")

# Upload section
uploaded_file = st.file_uploader("Upload Video", type=["mp4", "mov"])
if uploaded_file:
    # Save to temp location
    # Trigger inngest: video_library/ingest
    # Poll for completion
    # Show progress

# Video list
videos = fetch_videos()  # From FastAPI /videos
for video in videos:
    col1, col2, col3 = st.columns([3, 1, 1])
    col1.write(f"**{video.title}**")
    col2.write(f"{video.duration}s")
    if col3.button("Delete", key=video.video_id):
        delete_video(video.video_id)
```

**Test Checkpoint 3.5.1**:
```bash
uv run streamlit run streamlit_app.py
# Navigate to http://localhost:8501
```
- [ ] Upload interface works
- [ ] Video list displays
- [ ] Delete button functions
- [ ] Progress indicators show

### Step 3.5.2: Search Interface
**Action**: Add search tab
```python
# Tab 2: Search Library
st.header("🔍 Search Videos")

query = st.text_input("Search across all videos...")
top_k = st.slider("Number of results", 1, 20, 5)

if st.button("Search"):
    # Trigger inngest: video_library/search
    # Poll for results
    results = get_search_results(query, top_k)

    for result in results:
        with st.expander(f"{result.title} - {result.start_time}s"):
            st.write(result.description)
            st.write(f"Similarity: {result.score:.2%}")
            if st.button("Analyze this clip", key=result.chunk_id):
                st.session_state.selected_clips = [result]
                st.switch_page("chat")
```

**Test Checkpoint 3.5.2**:
- [ ] Search box accepts text
- [ ] Results display with scores
- [ ] Timestamp links work
- [ ] Can select clips for analysis

### Step 3.5.3: Chat with Selected Clips
**Action**: Add chat tab
```python
# Tab 3: Analyze Selected Clips
st.header("💬 Chat with Video Clips")

if "selected_clips" in st.session_state:
    st.sidebar.write("**Selected Clips:**")
    for clip in st.session_state.selected_clips:
        st.sidebar.write(f"- {clip.title} ({clip.start_time}s)")

    # Create cache from selected clips (if not exists)
    if "cache_name" not in st.session_state:
        # Trigger inngest: video_library/chat (cache creation only)
        cache_name = create_clip_cache(st.session_state.selected_clips)
        st.session_state.cache_name = cache_name

    # Chat interface (similar to Phase 2)
    prompt = st.chat_input("Ask about the selected clips...")
    if prompt:
        # Use cached_content with the selective cache
        response = generate_with_cache(prompt, st.session_state.cache_name)
```

**Test Checkpoint 3.5.3**:
- [ ] Selected clips shown in sidebar
- [ ] Cache created for clips only
- [ ] Chat responds with context from clips
- [ ] Timestamps in answers are accurate

---

## Phase 3.6: Integration & Testing
**Goal**: End-to-end workflow validation

### Step 3.6.1: Full Ingestion Test
**Test Scenario**: Upload 3 videos, verify indexing
```bash
# Upload videos via UI
# Check Qdrant has chunks
curl http://localhost:6333/collections/video_chunks/points/count
# Should show chunks from all 3 videos
```
- [ ] All videos indexed
- [ ] Chunks stored in Qdrant
- [ ] Descriptions are meaningful
- [ ] Embeddings have correct dimensions

### Step 3.6.2: Search Accuracy Test
**Test Scenario**: Search for specific content
```
Query: "Where is someone cooking?"
Expected: Returns clips with kitchen/cooking scenes
```
- [ ] Relevant clips ranked highly
- [ ] Irrelevant clips ranked low
- [ ] Top-5 results are accurate

### Step 3.6.3: Selective Caching Test
**Test Scenario**: Verify cache size vs Phase 2
```python
# Phase 2: Full video cached (~500K tokens for 30min video)
# Phase 3: Only 3 clips cached (~50K tokens for 3x1min clips)
print(f"Cache token count: {cache.usage_metadata.total_token_count}")
```
- [ ] Cache size is significantly smaller
- [ ] Chat answers are still accurate
- [ ] Response time is faster

### Step 3.6.4: Multi-Video Query Test
**Test Scenario**: Query spans multiple videos
```
Query: "Show me all scenes with dogs"
Expected: Returns clips from multiple videos
```
- [ ] Results from multiple videos
- [ ] Properly labeled with video titles
- [ ] Can analyze clips from different videos together

---

## Phase 3.7: Optimization & Documentation
**Goal**: Production-ready refinements

### Step 3.7.1: Performance Optimization
- [ ] Add batch embedding (10 chunks at a time)
- [ ] Implement parallel chunking for multiple videos
- [ ] Add caching for search results (5min TTL)
- [ ] Optimize Qdrant indexing parameters

### Step 3.7.2: Error Handling
- [ ] Video format validation
- [ ] Graceful handling of embedding failures
- [ ] Retry logic for Inngest functions
- [ ] User-friendly error messages

### Step 3.7.3: Documentation
- [ ] Update README.md with Phase 3 architecture
- [ ] Add API documentation (FastAPI auto-docs)
- [ ] Create usage guide with screenshots
- [ ] Document deployment steps

---

## Migration Path from Phase 2

### Strategy: Replace Phase 2 (User-Specified)
1. **Backup Phase 2**: Copy `app.py` to `app_phase2.py.bak`
2. **Preserve `.env`**: Keep existing Vertex AI configuration
3. **New Structure**: Implement multi-page Streamlit app in `pages/`
4. **Gradual Migration**:
   - Step 1: Set up infrastructure (Qdrant, dependencies)
   - Step 2: Implement video indexing (can test independently)
   - Step 3: Implement search (can test with indexed videos)
   - Step 4: Implement chat (final integration)
5. **Rollback Plan**: If issues arise, restore from `app_phase2.py.bak`

**Key Differences from Phase 2**:
- ❌ Removed: GCS upload, single-video full caching
- ✅ Added: Local storage, video library, semantic search, selective caching, audio transcription
- ♻️ Reused: Vertex AI client, context caching logic, environment configuration

---

## Estimated Timeline

| Phase | Task | Duration | Cumulative |
|-------|------|----------|------------|
| 3.1 | Foundation Setup | 1 hour | 1 hour |
| 3.2 | Data Models & Vector DB | 2 hours | 3 hours |
| 3.3 | Video Indexing Pipeline | 4 hours | 7 hours |
| 3.4 | Backend with Inngest | 3 hours | 10 hours |
| 3.5 | Streamlit UI | 4 hours | 14 hours |
| 3.6 | Integration & Testing | 3 hours | 17 hours |
| 3.7 | Optimization & Docs | 2 hours | **19 hours** |

---

## Success Criteria

✅ Phase 3 is complete when:
1. Can upload multiple videos to library
2. Videos are chunked and indexed in Qdrant
3. Can search across entire library semantically
4. Can select top-K clips and chat with them
5. Selective caching reduces token usage by 80%+ vs Phase 2
6. Search results are contextually accurate
7. System handles 100+ videos (10+ hours total runtime)
8. Documentation is complete and clear

---

## Ready to Implement ✅

All configuration questions have been answered. The plan is ready for step-by-step implementation.

### Next Steps
1. **Review**: Confirm this plan aligns with your vision
2. **Backup**: We'll backup Phase 2 app before starting
3. **Begin**: Start with Phase 3.1.1 (project structure migration)
4. **Test Incrementally**: Validate each checkpoint before proceeding

**Questions or changes to the plan?** Let me know and I'll update accordingly before we start implementation.
