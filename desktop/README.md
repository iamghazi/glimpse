# VideoSearch AI Desktop

A beautiful, native desktop application for searching and analyzing your local video library with AI-powered semantic search.

## Features

### Semantic Video Search
- Natural language queries to find specific moments in your videos
- Search by what you see or what was said
- 3-tier cascaded reranking for maximum precision
- Visual confidence scores for each result

### Video Library Management
- Upload and organize videos locally
- Automatic AI-powered processing (transcription + visual analysis)
- Track processing status with real-time updates
- Manage storage and view detailed video metadata

### AI Chat with Video Clips
- Multi-turn conversations about specific video clips
- Ask questions about what happened in scenes
- Get detailed explanations and insights
- Context-aware responses using Gemini AI

### Professional UI
- Clean, modern interface with dark mode support
- Custom video player with frame-accurate seeking
- Fullscreen video modal with chunk navigation
- Real-time processing tier indicators
- Responsive layout optimized for desktop

## Prerequisites

1. **Backend Server**: The FastAPI backend must be running (see main README)
2. **Bun Runtime**: Install from [bun.sh](https://bun.sh)
3. **Node.js 18+**: For building and development

## Quick Start

### 1. Install Dependencies

```bash
bun install
```

### 2. Start Backend Server

Make sure the FastAPI backend is running on `http://localhost:8000`:

```bash
cd ..
python run.py
```

### 3. Run Desktop App

**Development mode:**
```bash
bun run dev
```

**Build for production:**
```bash
# Build for current platform
bun run dist

# Platform-specific builds
bun run dist:mac
bun run dist:win
bun run dist:linux
```

The built application will be in the `release/` directory.

## Tech Stack

- **Framework**: Electron + Vue 3 + TypeScript
- **UI**: Tailwind CSS + Material Symbols
- **State Management**: Pinia
- **Routing**: Vue Router
- **HTTP Client**: Axios
- **Build Tool**: Vite + Electron Vite

## App Structure

The desktop app has four main views:

1. **Search** - Semantic search with natural language queries
2. **Library** - Browse and manage your video collection
3. **Chat** - Have conversations about video clips
4. **Settings** - Configure processing, storage, and API settings

## Settings Configuration

The app supports configuring:
- Google Cloud credentials and project settings
- Video processing parameters (chunk duration, frame extraction)
- Search embedding models and options
- Data storage locations
- Processing quality settings

Settings are persisted locally using electron-store.

## Development

### Project Structure

```
desktop/
├── src/
│   ├── main/              # Electron main process
│   ├── renderer/          # Vue app (UI)
│   ├── components/        # Vue components
│   │   ├── chat/         # Chat view components
│   │   ├── layout/       # Layout components (sidebar, header)
│   │   ├── library/      # Library view components
│   │   ├── search/       # Search view components
│   │   ├── settings/     # Settings view components
│   │   ├── ui/           # Reusable UI components
│   │   └── video/        # Video player components
│   ├── stores/           # Pinia state stores
│   ├── types/            # TypeScript type definitions
│   ├── views/            # Main view components
│   └── router/           # Vue Router configuration
├── resources/            # App icons and resources
└── out/                  # Build output
```

### Available Scripts

- `bun run dev` - Start development server with hot reload
- `bun run build` - Build the app for production
- `bun run preview` - Preview the production build
- `bun run pack` - Package without distributing
- `bun run dist` - Build and create distributables

## Troubleshooting

**Backend connection failed**: Ensure the FastAPI server is running on port 8000

**Videos not processing**: Check backend logs and ensure Google Cloud credentials are configured

**Blank screen on launch**: Check the developer console (View > Toggle Developer Tools)

**Build errors**: Clear node_modules and reinstall dependencies

## License

MIT License - See LICENSE file for details
