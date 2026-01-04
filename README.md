# Video Library Search Engine

A professional video semantic search engine with AI-powered analysis, chat, and 3-tier cascaded reranking for maximum precision.

## 🎯 Features

### Core Capabilities
- **Semantic Video Search**: Natural language queries with dual embeddings (text + visual)
- **3-Tier Cascaded Reranking**:
  - Tier 1: Hybrid RRF retrieval (text + visual)
  - Tier 2: Text-only LLM reranking
  - Tier 3: Multimodal LLM reranking with frames
- **AI-Powered Analysis**: Automatic transcription (Whisper) + visual descriptions (Gemini)
- **Chat with Clips**: Multi-turn conversations using Gemini with context caching
- **FastAPI Backend**: Production-ready REST API with async support
- **Modular Architecture**: Clean separation of concerns, easy to extend

### Technical Highlights
- Dual embeddings: Text (gemini-embedding-001, 3072-dim) + Visual (multimodalembedding@001, 1408-dim)
- Reciprocal Rank Fusion (RRF) for hybrid search
- Intelligent query weight analysis (text-heavy vs visual-heavy)
- Parallel embedding generation with configurable workers
- Context caching for efficient chat sessions
- Vector database: Qdrant with dual named vectors

## 📋 Prerequisites

1. **Python 3.10+** with `uv` package manager
2. **Google Cloud Project** with Vertex AI API enabled
3. **GCP Authentication**: Application Default Credentials
4. **Qdrant**: Vector database (runs locally or via Docker)
5. **FFmpeg**: For video processing

## 🚀 Quick Start

### 1. Authenticate with Google Cloud

```bash
gcloud auth application-default login
```

### 2. Configure Environment

Create `.env` file in project root:

```env
# Google Cloud Configuration
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1
GEMINI_MODEL=gemini-2.0-flash-exp

# Qdrant Vector Database
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Video Processing
CHUNK_DURATION_SECONDS=30
CHUNK_OVERLAP_SECONDS=5
FRAME_EXTRACTION_FPS=1

# Parallel Processing
EMBEDDING_MAX_WORKERS=5

# Cascaded Reranking
RERANKING_ENABLED=true
TIER1_CANDIDATES=50
TIER2_MODEL=gemini-2.0-flash-exp
TIER3_FRAMES_PER_CLIP=5
CONFIDENCE_THRESHOLD=0.8

# Storage Paths (auto-created)
VIDEOS_DIR=./data/videos
FRAMES_DIR=./data/frames
METADATA_DIR=./data/metadata
```

### 3. Install Dependencies

```bash
# Install all dependencies
uv pip install -e .

# Or install from requirements
uv pip install -r requirements.txt
```

### 4. Start Qdrant

**Option A: Docker (Recommended)**
```bash
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/data/qdrant_storage:/qdrant/storage \
    qdrant/qdrant
```

**Option B: Local Installation**
```bash
# Follow Qdrant installation guide
# https://qdrant.tech/documentation/quick-start/
```

### 5. Start the API Server

**Development mode (with hot-reload):**
```bash
python run.py
```

**Production mode:**
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## 📚 API Usage

### Upload a Video

```bash
curl -X POST "http://localhost:8000/videos/upload" \
  -F "file=@/path/to/video.mp4" \
  -F "title=My Video"
```

This automatically:
1. Chunks the video into 30-second segments
2. Extracts frames at 1 FPS
3. Generates AI analysis (transcription + visual descriptions)
4. Creates dual embeddings (text + visual)
5. Indexes in Qdrant

### Search Videos

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "man flirts with a woman",
    "top_k": 5,
    "use_cascaded_reranking": true,
    "confidence_threshold": 0.8
  }'
```

### Chat with Clips

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "clip_ids": ["vid_123_0_30", "vid_123_30_60"],
    "query": "What happens in these clips?"
  }'
```

### List Videos

```bash
curl "http://localhost:8000/videos"
```

## 🏗️ Project Structure

```
video-analyser/
├── src/                          # Source code
│   ├── main.py                  # FastAPI application
│   ├── core/                    # Core infrastructure
│   │   ├── config.py           # Settings & configuration
│   │   ├── constants.py        # Application constants
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── logging.py          # Logging setup
│   ├── models/                  # Pydantic models
│   │   ├── video.py            # Video metadata models
│   │   ├── search.py           # Search request/response
│   │   ├── chat.py             # Chat request/response
│   │   └── common.py           # Shared models
│   ├── api/                     # API layer
│   │   └── routes/
│   │       ├── health.py       # Health check
│   │       ├── videos.py       # Video CRUD
│   │       ├── search.py       # Search endpoint
│   │       └── chat.py         # Chat endpoint
│   ├── video_processing/        # Video processing
│   │   └── service.py          # VideoProcessor
│   ├── ai_analysis/            # AI analysis
│   │   └── service.py          # Whisper + Gemini
│   ├── embeddings/             # Embedding generation
│   │   └── service.py          # Dual embeddings
│   ├── search/                 # Search & ranking
│   │   ├── vector_db.py        # Qdrant wrapper
│   │   ├── reranker.py         # Text + Multimodal
│   │   └── service.py          # 3-tier search
│   ├── chat/                   # Chat with clips
│   │   └── service.py          # Context caching
│   └── utils/                  # Utilities
│       ├── retry.py            # Retry logic
│       └── prompts.py          # Prompt templates
├── data/                        # User data (gitignored)
│   ├── videos/                 # Uploaded videos
│   ├── frames/                 # Extracted frames
│   ├── metadata/               # Video metadata
│   └── qdrant_storage/         # Vector database
├── tests/                       # Tests
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── conftest.py             # Pytest fixtures
├── docs/                        # Documentation
│   ├── plans/                  # Planning documents
│   ├── architecture/           # Architecture docs
│   └── api/                    # API documentation
├── prompts/                     # Prompt templates
│   ├── text_rerank_prompt.txt
│   └── multimodal_rerank_prompt.txt
├── run.py                       # Dev server launcher
├── verify_imports.py            # Import verification
└── pyproject.toml              # Project configuration
```

## 🔬 How It Works

### Video Processing Pipeline

1. **Upload**: Video file saved to `data/videos/`
2. **Chunking**: Split into 30-second chunks with 5-second overlap
3. **Frame Extraction**: Extract frames at 1 FPS
4. **AI Analysis**:
   - Audio transcription using Whisper (base model)
   - Visual description using Gemini vision
   - Enhanced transcript with conversation context
5. **Embedding Generation** (parallel):
   - Text embeddings from descriptions + transcripts
   - Visual embeddings from video chunks
6. **Indexing**: Store in Qdrant with dual named vectors

### 3-Tier Cascaded Search

**Tier 1: Hybrid RRF Retrieval**
- Generate dual query embeddings (text + visual)
- Analyze query to determine optimal weights
- Search text and visual vectors separately
- Combine with Reciprocal Rank Fusion (RRF)
- Return Top 50 candidates

**Tier 2: Text-Only Reranking**
- Use Gemini Flash for LLM-based reranking
- Filter based on text metadata only
- Return Top 5 high-confidence candidates

**Tier 3: Multimodal Reranking**
- Load representative frames for each candidate
- Use Gemini with visual verification
- Generate confidence scores (0.0-1.0)
- Return final ranked results

**Result**: 90%+ precision with best match ranked #1

## 🧪 Testing

```bash
# Verify all imports
python verify_imports.py

# Run unit tests
pytest tests/unit/

# Run integration tests (requires data)
pytest tests/integration/

# Run all tests
pytest tests/
```

## 🐳 Docker Deployment

```bash
# Start Qdrant + API
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

## 📖 Documentation

- **Planning**: `docs/plans/` - Project plans and roadmaps
- **Architecture**: `docs/architecture/` - System design and overview
- **API Docs**: Available at `/docs` when server is running

## 🔧 Development

### Import Verification
```bash
python verify_imports.py
```

### Code Structure
- Follow feature-based module organization
- Use dependency injection via FastAPI
- Centralize configuration in `src/core/config.py`
- Add logging instead of print statements
- Write tests alongside features

### Adding a New Feature

1. Create module in appropriate `src/` directory
2. Add models to `src/models/`
3. Create API route in `src/api/routes/`
4. Register router in `src/main.py`
5. Add tests in `tests/`
6. Update documentation

## 🎯 Performance

- **Embedding Generation**: Parallel processing (5 workers default)
- **Search Latency**: <2s for Tier 1, ~5s for full 3-tier
- **Accuracy**: 90%+ precision with cascaded reranking
- **Scalability**: Handles 100+ videos with Qdrant

## 🔐 Security Notes

- `.env` file is gitignored - never commit credentials
- Use Application Default Credentials for GCP auth
- Qdrant runs on localhost by default
- CORS configured for localhost origins only

## 🐛 Troubleshooting

**Import errors**: Run `python verify_imports.py` to check all modules

**Qdrant connection failed**: Ensure Qdrant is running on port 6333

**Slow embedding generation**: Increase `EMBEDDING_MAX_WORKERS` in `.env`

**Low search precision**: Enable cascaded reranking and adjust `CONFIDENCE_THRESHOLD`

**FFmpeg not found**: Install with `brew install ffmpeg` (macOS) or `apt-get install ffmpeg` (Linux)

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **Google Vertex AI**: Gemini models and multimodal embeddings
- **OpenAI Whisper**: Audio transcription
- **Qdrant**: Vector database
- **FastAPI**: Web framework

---

**Ready to search your video library? Start the server with `python run.py`!**
