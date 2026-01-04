# Google Stitch Prompt: Video Library Search Engine Desktop UI

## Project Overview

Create a modern desktop application UI for a **Video Library Search Engine** - an open-source tool that uses AI to analyze, search, and chat with video content. The app connects to a local FastAPI backend running on `http://localhost:8000`.

**Key Characteristics:**
- Local-first architecture (no cloud, no user accounts)
- Users provide their own Google Vertex AI credentials
- All video processing happens on the user's machine
- Open-source project for personal video library management

---

## Technical Requirements

### Backend Integration
- **API Base URL**: `http://localhost:8000`
- **API Documentation**: Available at `http://localhost:8000/docs`
- **Connection Check**: Use `/health` endpoint to verify backend is running
- **No Authentication**: Direct API calls (backend runs locally)

### Configuration Management
Users must configure these settings (stored locally in app config):
- **GCP Project ID** (required)
- **GCP Location** (default: `us-central1`)
- **Gemini Model** (default: `gemini-2.0-flash-exp`)
- **Optional Settings**:
  - Chunk duration (default: 30 seconds)
  - Chunk overlap (default: 5 seconds)
  - Frame extraction FPS (default: 1)
  - Embedding workers (default: 5)
  - Reranking settings (Tier1 candidates: 50, Confidence threshold: 0.8)

### Data Storage
- Videos stored in: `./data/videos/`
- Frames stored in: `./data/frames/`
- Metadata stored in: `./data/metadata/`
- Vector DB: Qdrant running on `localhost:6333`

---

## UI Architecture

### Layout Structure
```
┌─────────────────────────────────────────────────────────┐
│  [App Icon] Video Library Search Engine      [- □ ×]   │
├───────────┬─────────────────────────────────────────────┤
│           │                                             │
│  Sidebar  │           Main Content Area                │
│           │                                             │
│  - Home   │                                             │
│  - Library│                                             │
│  - Search │                                             │
│  - Chat   │                                             │
│  - Settings│                                            │
│           │                                             │
│           │                                             │
│  [Status] │                                             │
│  ● API    │                                             │
│  ● Qdrant │                                             │
└───────────┴─────────────────────────────────────────────┘
```

---

## Screens & Features

### 1. **Home/Dashboard**

**Purpose**: Welcome screen with quick stats and status

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│  Welcome to Video Library Search Engine                │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Videos    │  │  Total Time │  │   Chunks    │    │
│  │     42      │  │   2h 15m    │  │     168     │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                         │
│  System Status:                                         │
│  ✓ FastAPI Backend (http://localhost:8000)            │
│  ✓ Qdrant Vector DB (localhost:6333)                  │
│  ✓ Google Vertex AI (Configured)                      │
│                                                         │
│  Quick Actions:                                         │
│  [Upload Video]  [Search Library]  [View Recent]       │
│                                                         │
│  Recent Activity:                                       │
│  • "beach sunset.mp4" uploaded 2 hours ago            │
│  • Searched for "man flirts with woman"               │
│  • Chat session with 3 clips                          │
└─────────────────────────────────────────────────────────┘
```

**Features**:
- Display total videos, total duration, total chunks
- System status indicators (green = connected, red = error)
- Quick action buttons
- Recent activity feed
- Welcome message for first-time users prompting settings configuration

---

### 2. **Library**

**Purpose**: Browse and manage uploaded videos

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│  Video Library                    [Upload Video] [⚙️]   │
│                                                         │
│  Search/Filter: [________________]  Sort: [Recent ▼]   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 📹 beach_sunset.mp4                    [🗑️] [▶️] │  │
│  │ Duration: 1:23:45  |  Chunks: 168  |  2 hours ago│  │
│  │ ───────────────────────────────────────────────  │  │
│  │ [Thumbnail Preview]                              │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 📹 conference_talk.mp4                 [🗑️] [▶️] │  │
│  │ Duration: 45:30  |  Chunks: 89  |  1 day ago    │  │
│  │ ───────────────────────────────────────────────  │  │
│  │ [Thumbnail Preview]                              │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Showing 10 of 42 videos        [← 1 2 3 4 5 →]       │
└─────────────────────────────────────────────────────────┘
```

**Features**:
- Video cards with thumbnails, title, duration, chunk count, upload date
- Upload video button (opens file picker, shows progress during processing)
- Delete video (with confirmation dialog)
- Play video (opens in default player or embedded player)
- Search/filter by title
- Sort options: Recent, Oldest, Title A-Z, Duration
- Pagination for large libraries
- Click on video card to see detailed view with all chunks

**Upload Flow**:
1. Click "Upload Video" → File picker
2. Select video file → Show modal with:
   - File name
   - Video title input (pre-filled with filename)
   - [Cancel] [Upload] buttons
3. During upload/processing:
   - Progress bar showing: "Uploading... Chunking... Extracting frames... Analyzing... Generating embeddings... Indexing..."
   - Percentage complete
4. Success: "Video processed successfully! Found 168 chunks."

---

### 3. **Search**

**Purpose**: Semantic search across video library with 3-tier cascaded reranking

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│  Search Videos                                          │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Enter search query...                           │🔍│
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─ Advanced Options ────────────────────────────┐     │
│  │ Results to show: [5 ▼]                        │     │
│  │ ☑ Use Cascaded Reranking (3-tier)            │     │
│  │ Confidence threshold: [0.8  ──●────────]      │     │
│  │                                                │     │
│  │ If unchecked: Use basic hybrid search only    │     │
│  └────────────────────────────────────────────────┘     │
│                                                         │
│  Search Results:                                        │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 🎬 Clip from: beach_sunset.mp4                  │  │
│  │ Confidence: 92%  |  Time: 01:23 - 01:53        │  │
│  │ ───────────────────────────────────────────────  │  │
│  │ [Frame Preview Grid: 5 frames]                  │  │
│  │                                                  │  │
│  │ Transcript: "The man walks over to the woman..." │  │
│  │ Description: "A beach scene with golden sunset..."│  │
│  │                                                  │  │
│  │ [▶️ Play Clip]  [💬 Chat]  [⭐ Bookmark]        │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Found 5 high-confidence matches in 4.2s               │
└─────────────────────────────────────────────────────────┘
```

**Features**:
- Large search input field with search icon
- Advanced options panel (collapsible):
  - Number of results slider/dropdown (1-10)
  - Cascaded reranking toggle (on by default)
  - Confidence threshold slider (0.0-1.0)
  - Info tooltip explaining 3-tier search
- Search results as cards showing:
  - Source video name
  - Confidence score (as percentage with color: green >80%, yellow 60-80%, red <60%)
  - Time range in video
  - Frame preview grid (5 representative frames)
  - Transcript excerpt
  - Visual description
  - Action buttons: Play, Chat, Bookmark
- Loading state during search with tier indicators:
  - "🔍 Tier 1: Hybrid retrieval... (50 candidates)"
  - "🎯 Tier 2: Text reranking... (5 candidates)"
  - "🎨 Tier 3: Multimodal verification..."
- Empty state: "Enter a query to search your video library"
- No results state: "No matches found. Try a different query."

**Info Tooltip for 3-Tier Search**:
```
3-Tier Cascaded Reranking:
• Tier 1: Fast hybrid search (text + visual)
• Tier 2: LLM reranking (text metadata)
• Tier 3: Multimodal verification (with frames)
Result: 90%+ precision, best match ranked #1
```

---

### 4. **Chat**

**Purpose**: Multi-turn conversations with selected video clips

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│  Chat with Video Clips                     [Clear Chat] │
│                                                         │
│  Active Clips: ┌───────────────────────────────────┐   │
│  ┌────────────┐│ beach_sunset.mp4 (01:23-01:53)   │[×]│
│  │[Thumbnail] ││ conference_talk.mp4 (12:30-13:00)│[×]│
│  └────────────┘└───────────────────────────────────┘   │
│                 [+ Add Clips from Search]              │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 💬 Chat History                                 │   │
│  │                                                 │   │
│  │ You: What happens in these clips?              │   │
│  │                                                 │   │
│  │ Assistant: In the first clip from beach_sunset,│   │
│  │ a man approaches a woman on the beach during   │   │
│  │ sunset. In the second clip from conference...  │   │
│  │                                                 │   │
│  │ You: What are they talking about?              │   │
│  │                                                 │   │
│  │ Assistant: Based on the transcripts...         │   │
│  │                                                 │   │
│  │                                                 │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Type your question...                           │ ➤ │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Features**:
- Active clips panel:
  - Shows selected clips with thumbnails
  - Display source video and time range
  - Remove button (×) for each clip
  - "Add Clips" button to open clip selector modal
- Chat history:
  - User messages aligned right
  - Assistant messages aligned left
  - Timestamps for each message
  - Markdown rendering support
  - Auto-scroll to latest message
- Message input:
  - Text area that expands with content
  - Send button (or Enter to send)
  - Disabled if no clips selected
- Clear chat button (with confirmation)
- Loading state: "Thinking..." with animated dots
- Context caching indicator: "Using cached context (faster responses)"

**Add Clips Modal**:
- Search interface to find clips
- OR select from recent search results
- Checkboxes to select multiple clips
- [Cancel] [Add Selected] buttons

---

### 5. **Settings**

**Purpose**: Configure Google Vertex AI credentials and processing parameters

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│  Settings                                               │
│                                                         │
│  ┌─ Google Cloud Configuration ─────────────────────┐  │
│  │                                                   │  │
│  │ GCP Project ID: *                                │  │
│  │ [_______________________________________]        │  │
│  │                                                   │  │
│  │ GCP Location:                                    │  │
│  │ [us-central1                              ▼]     │  │
│  │                                                   │  │
│  │ Gemini Model:                                    │  │
│  │ [gemini-2.0-flash-exp                     ▼]     │  │
│  │ Options: gemini-2.0-flash-exp, gemini-1.5-pro   │  │
│  │                                                   │  │
│  │ [Test Connection]  Status: ● Connected          │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─ Video Processing ───────────────────────────────┐  │
│  │                                                   │  │
│  │ Chunk Duration: [30___] seconds                  │  │
│  │ Chunk Overlap: [5____] seconds                   │  │
│  │ Frame Extraction FPS: [1____] frame/second       │  │
│  │                                                   │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─ Search & Embedding ─────────────────────────────┐  │
│  │                                                   │  │
│  │ Parallel Workers: [5____] (for embeddings)       │  │
│  │ Tier 1 Candidates: [50___]                       │  │
│  │ Confidence Threshold: [0.8  ──●────────]         │  │
│  │                                                   │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─ Data Directories ───────────────────────────────┐  │
│  │                                                   │  │
│  │ Videos: ./data/videos/        [Change...]        │  │
│  │ Frames: ./data/frames/        [Change...]        │  │
│  │ Metadata: ./data/metadata/    [Change...]        │  │
│  │                                                   │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│              [Reset to Defaults]  [Save Settings]       │
│                                                         │
│  Note: Settings are saved locally. You need Google     │
│  Cloud credentials to use this application.            │
└─────────────────────────────────────────────────────────┘
```

**Features**:
- **Google Cloud Configuration**:
  - Project ID input (required, validated)
  - Location dropdown (common regions)
  - Gemini model dropdown (available models)
  - "Test Connection" button → calls `/health` endpoint
  - Status indicator (green = connected, red = error with message)
- **Video Processing**:
  - Number inputs for chunk duration, overlap, FPS
  - Tooltips explaining each setting
- **Search & Embedding**:
  - Workers: 1-10 slider
  - Tier 1 candidates: 10-100
  - Confidence threshold: 0.0-1.0 slider
- **Data Directories**:
  - Display current paths
  - "Change" button to pick new directory
  - Validation: must be writable
- **Actions**:
  - "Reset to Defaults" → restore default values
  - "Save Settings" → save to local config + update backend .env
- **First Run**:
  - If no GCP Project ID, show prominent warning:
    ```
    ⚠️  Configuration Required

    This is an open-source application that requires your own
    Google Cloud credentials. Please configure:

    1. Create a Google Cloud project
    2. Enable Vertex AI API
    3. Enter your project ID above

    [Learn More] [Configure Now]
    ```

---

## API Integration

### Endpoints to Implement

#### 1. Health Check
```
GET /health
Response: {
  "status": "healthy",
  "version": "4.0.0",
  "qdrant_connected": true
}
```

#### 2. Upload Video
```
POST /videos/upload
Content-Type: multipart/form-data
Body:
  - file: video file
  - title: string

Response: {
  "video_id": "vid_123",
  "title": "beach_sunset",
  "status": "processing"
}
```
**Note**: This is a long-running operation. Show progress bar.

#### 3. List Videos
```
GET /videos
Response: {
  "videos": [
    {
      "video_id": "vid_123",
      "title": "beach_sunset",
      "duration": 5025.5,
      "chunk_count": 168,
      "created_at": "2026-01-04T10:30:00Z"
    }
  ]
}
```

#### 4. Get Video Details
```
GET /videos/{video_id}
Response: {
  "video_id": "vid_123",
  "title": "beach_sunset",
  "duration": 5025.5,
  "chunks": [
    {
      "chunk_id": "vid_123_0_30",
      "start_time": 0,
      "end_time": 30,
      "transcript": "...",
      "description": "..."
    }
  ]
}
```

#### 5. Search
```
POST /search
Content-Type: application/json
Body: {
  "query": "man flirts with a woman",
  "top_k": 5,
  "use_cascaded_reranking": true,
  "confidence_threshold": 0.8
}

Response: {
  "results": [
    {
      "chunk_id": "vid_123_83_113",
      "video_id": "vid_123",
      "video_title": "beach_sunset",
      "start_time": 83.0,
      "end_time": 113.0,
      "score": 0.92,
      "transcript": "...",
      "description": "...",
      "frame_paths": ["path1.jpg", "path2.jpg", ...]
    }
  ],
  "search_time": 4.2
}
```

#### 6. Chat with Clips
```
POST /chat
Content-Type: application/json
Body: {
  "clip_ids": ["vid_123_0_30", "vid_123_30_60"],
  "query": "What happens in these clips?"
}

Response: {
  "response": "In these clips, ...",
  "cache_used": true
}
```

#### 7. Delete Video
```
DELETE /videos/{video_id}
Response: {
  "message": "Video deleted successfully"
}
```

---

## Visual Design Guidelines

### Color Scheme
- **Primary**: Deep blue (#2563eb) - for main actions, highlights
- **Secondary**: Purple (#7c3aed) - for AI/smart features
- **Success**: Green (#10b981) - for status indicators, successful actions
- **Warning**: Yellow (#f59e0b) - for medium confidence results
- **Error**: Red (#ef4444) - for errors, low confidence
- **Background**: Light gray (#f9fafb) - main background
- **Surface**: White (#ffffff) - cards, panels
- **Text**: Dark gray (#1f2937) - primary text
- **Text Secondary**: Medium gray (#6b7280) - secondary text

### Typography
- **Headings**: Bold, Sans-serif (e.g., Inter, SF Pro)
- **Body**: Regular, Sans-serif
- **Code/Paths**: Monospace (e.g., JetBrains Mono)

### Components
- **Buttons**: Rounded corners (8px), shadow on hover
- **Cards**: Subtle shadow, rounded corners (12px), border
- **Inputs**: Border, rounded corners (6px), focus ring
- **Modals**: Center screen, overlay backdrop, smooth animation
- **Loading**: Skeleton screens or spinners with text

### Icons
Use a consistent icon set (e.g., Lucide, Heroicons, or Material Icons):
- 📹 Video
- 🔍 Search
- 💬 Chat
- ⚙️ Settings
- ✓ Success
- ⚠️ Warning
- ✕ Error/Close
- ▶️ Play
- 🗑️ Delete
- ⭐ Bookmark

### Spacing
- **Small**: 8px
- **Medium**: 16px
- **Large**: 24px
- **XL**: 32px

---

## Error Handling

### Backend Not Running
```
⚠️ Cannot connect to backend

The FastAPI server is not running.
Please start it with: python run.py

[Retry Connection] [Open Logs]
```

### Qdrant Not Running
```
⚠️ Vector database not available

Qdrant is not running on localhost:6333.
Start it with Docker:
docker run -p 6333:6333 qdrant/qdrant

[Retry Connection] [View Instructions]
```

### Invalid API Key
```
❌ Invalid Google Cloud credentials

Your GCP Project ID or credentials are invalid.
Please check your settings.

[Go to Settings] [View Setup Guide]
```

### Upload Failed
```
❌ Video upload failed

Error: [specific error message]

[Try Again] [Cancel]
```

### Search Error
```
❌ Search failed

Error: [specific error message]

[Try Again] [Report Issue]
```

---

## First-Time User Experience

### Onboarding Flow
1. **Welcome Screen**:
   ```
   Welcome to Video Library Search Engine! 🎬

   This application helps you search and chat with your
   video library using AI.

   Before we start, you'll need:
   ✓ A Google Cloud account
   ✓ Vertex AI API enabled
   ✓ Your GCP Project ID

   [Get Started] [Learn More]
   ```

2. **Setup Screen** (same as Settings, but required):
   - GCP Project ID input (validated on blur)
   - Test connection button
   - Can't proceed until valid credentials

3. **Backend Check**:
   ```
   Checking system requirements...

   ✓ FastAPI backend (running)
   ✓ Qdrant vector DB (running)
   ⚠️ Google Cloud (needs configuration)

   [Configure Google Cloud]
   ```

4. **Ready Screen**:
   ```
   All set! 🚀

   Your video library is ready to use.

   [Upload First Video] [Explore Features]
   ```

---

## Performance Considerations

### Loading States
- **Video List**: Skeleton cards while loading
- **Search**: Progressive disclosure (Tier 1 → Tier 2 → Tier 3)
- **Upload**: Progress bar with step indicators
- **Chat**: Typing indicator with "Thinking..." text

### Optimizations
- Lazy load video thumbnails
- Paginate video list (10-20 per page)
- Cache search results locally (session-based)
- Debounce search input (300ms)
- Virtual scrolling for large chat histories

### Offline Behavior
- Show warning if backend disconnects
- Cache settings locally
- Queue actions when offline (if applicable)

---

## Accessibility

- **Keyboard Navigation**: All features accessible via keyboard
- **Screen Reader Support**: ARIA labels on all interactive elements
- **Focus Indicators**: Visible focus states
- **Color Contrast**: WCAG AA compliant (4.5:1 for text)
- **Text Scaling**: Support up to 200% zoom
- **Alt Text**: All images and icons have alt text

---

## Additional Features (Nice to Have)

### Bookmarks
- Star/bookmark favorite clips
- Dedicated bookmarks view in sidebar

### Export
- Export search results as JSON/CSV
- Export chat conversations as text

### Video Player
- Embedded video player (instead of external)
- Jump to specific timestamp from search results
- Play multiple clips in sequence

### Themes
- Light/Dark mode toggle
- System theme detection

### Keyboard Shortcuts
- Cmd/Ctrl+K: Quick search
- Cmd/Ctrl+U: Upload video
- Cmd/Ctrl+,: Settings
- Esc: Close modals

---

## Technical Stack Recommendations

### Desktop Framework
- **Electron** (cross-platform, large community)
- **Tauri** (smaller bundle, Rust-based, better performance)

### Frontend Framework
- **React** + TypeScript (component-based, type-safe)
- **Svelte** (smaller bundle, simpler syntax)
- **Vue 3** (progressive framework, good docs)

### UI Component Library
- **shadcn/ui** (Tailwind-based, customizable)
- **Radix UI** (accessible primitives)
- **Chakra UI** (batteries-included)

### State Management
- **Zustand** (simple, no boilerplate)
- **TanStack Query** (for API state)

### Styling
- **Tailwind CSS** (utility-first, fast)
- **CSS Modules** (scoped styles)

---

## Configuration File Format

Save settings in a local JSON file (e.g., `~/.video-analyser/config.json`):

```json
{
  "gcp": {
    "project_id": "your-project-id",
    "location": "us-central1",
    "gemini_model": "gemini-2.0-flash-exp"
  },
  "processing": {
    "chunk_duration": 30,
    "chunk_overlap": 5,
    "frame_fps": 1,
    "embedding_workers": 5
  },
  "search": {
    "tier1_candidates": 50,
    "confidence_threshold": 0.8
  },
  "paths": {
    "videos_dir": "./data/videos",
    "frames_dir": "./data/frames",
    "metadata_dir": "./data/metadata"
  },
  "api": {
    "base_url": "http://localhost:8000"
  }
}
```

---

## Summary

Create a **clean, modern desktop application** for the Video Library Search Engine with:

1. ✅ **5 main screens**: Home, Library, Search, Chat, Settings
2. ✅ **Local-first design**: No login, user provides own API keys
3. ✅ **Full feature parity** with the FastAPI backend
4. ✅ **Excellent UX**: Clear feedback, loading states, error handling
5. ✅ **Professional design**: Modern UI, consistent styling, accessible
6. ✅ **Easy setup**: Guided onboarding for first-time users

**Target Users**: Researchers, content creators, video enthusiasts who want to organize and search their personal video libraries using AI.

**Key Differentiator**: Open-source, local-first, privacy-focused alternative to cloud video search services.

---

**End of Prompt**
