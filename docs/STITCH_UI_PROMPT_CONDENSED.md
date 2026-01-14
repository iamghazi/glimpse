# Video Library Search Engine - Desktop UI (Condensed Prompt)

## Overview
Build a modern desktop app for an **AI-powered video search engine**. Local-first, open-source tool that connects to FastAPI backend at `http://localhost:8000`. Users provide their own Google Vertex AI credentials.

## Tech Stack
- Desktop: Electron or Tauri
- Frontend: React + TypeScript + Tailwind CSS
- API: REST API at localhost:8000 (no auth)
- Config: Stored locally in JSON file

## Core Screens

### 1. Home/Dashboard
- Quick stats: total videos, duration, chunks
- System status: API (localhost:8000), Qdrant (localhost:6333), GCP
- Quick actions: Upload, Search, Recent activity

### 2. Library
- Video grid with thumbnails, title, duration, chunks
- Upload button → file picker → progress bar (chunking, analyzing, indexing)
- Delete, play, filter/search, pagination
- Click video → view all chunks with details

### 3. Search
- Large search input
- Advanced options: top_k (1-10), cascaded reranking toggle, confidence threshold (0-1)
- Results: cards with confidence %, time range, 5 frame previews, transcript, description
- Actions: Play, Chat, Bookmark
- Loading: show 3 tiers (Hybrid → Text rerank → Multimodal)

### 4. Chat
- Selected clips panel (thumbnails + time ranges, removable)
- Chat history (user right, assistant left, markdown support)
- Message input (disabled if no clips)
- Add clips from search or clip selector

### 5. Settings
**Required - First Run:**
- GCP Project ID (required, validated)
- GCP Location (default: us-central1)
- Gemini Model (default: gemini-2.0-flash-exp)
- Test Connection button → /health endpoint

**Optional:**
- Video: chunk duration (30s), overlap (5s), FPS (1)
- Search: workers (5), tier1 candidates (50), confidence (0.8)
- Paths: videos, frames, metadata directories

**First-time flow:**
```
⚠️ Configuration Required
Enter your GCP Project ID to continue.
Need help? [Setup Guide]
```

## API Endpoints

```
GET  /health                      → system status
GET  /videos                      → list all videos
POST /videos/upload               → upload + process (multipart/form-data)
GET  /videos/{id}                 → video details + chunks
DELETE /videos/{id}               → delete video
POST /search                      → semantic search with 3-tier reranking
  Body: {query, top_k, use_cascaded_reranking, confidence_threshold}
POST /chat                        → chat with clips
  Body: {clip_ids: [], query}
```

## Design
- **Colors**: Blue primary (#2563eb), Purple for AI (#7c3aed), Green success, Yellow warning, Red error
- **Components**: Rounded cards (12px), shadows, smooth animations
- **Icons**: Lucide or Heroicons (consistent set)
- **Layout**: Sidebar navigation (Home, Library, Search, Chat, Settings) + main content area

## Error Handling
- Backend not running → "Start with: python run.py" + [Retry]
- Qdrant not running → "Start Qdrant on port 6333" + [Instructions]
- Invalid credentials → "Check GCP settings" + [Go to Settings]
- Upload/Search errors → Show message + [Retry]

## Key Features
✅ No login/signup (local-only)
✅ Users provide own GCP credentials (stored locally)
✅ All processing on local machine
✅ 3-tier cascaded search visualization
✅ Multi-turn chat with context caching
✅ Video upload with progress tracking
✅ Responsive, accessible, keyboard navigation
✅ Light/dark mode (optional)

## Data Flow
1. User configures GCP credentials in Settings → saved to local config.json
2. Upload video → FastAPI processes → chunks + embeddings + Qdrant
3. Search → FastAPI 3-tier pipeline → ranked results
4. Chat → FastAPI with Gemini + context caching → responses

## Priority
1. Settings (must work first - blocks everything)
2. Library + Upload (core workflow)
3. Search (main feature)
4. Chat (secondary feature)
5. Home/Dashboard (nice to have stats)

**Build a clean, modern, local-first desktop app for AI-powered video search.**
