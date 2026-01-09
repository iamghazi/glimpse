// Video metadata from backend
export interface Video {
  video_id: string
  title: string
  file_path: string
  duration_seconds: number
  fps: number
  resolution: [number, number]  // [width, height]
  file_size_mb: number
  uploaded_at: string  // ISO date string
  indexed_at: string | null  // ISO date string
  original_filename: string
}

// Processing status for video
export type ProcessingStatus = 'uploading' | 'processing' | 'indexed' | 'failed' | 'ready'

// Extended video with UI state
export interface VideoWithState extends Video {
  status: ProcessingStatus
  uploadProgress?: number  // 0-100
  chunkCount?: number
  thumbnailUrl?: string  // Local file URL for thumbnail
  error?: string
}

// Video chunk from backend
export interface VideoChunk {
  chunk_id: string
  video_id: string
  start_time: number
  end_time: number
  duration: number
  visual_description: string
  audio_transcript: string
  frame_paths: string[]
  representative_frame: string
}

// Upload request
export interface VideoUploadRequest {
  file?: File  // Optional File object (for web)
  filePath?: string  // Optional file path (for Electron)
  title: string
}

// Upload response
export interface VideoUploadResponse {
  video_id: string
  title: string
  status: string
  message: string
  file_path: string
  processing?: {
    num_chunks: number
    total_frames: number
    status: string
  }
}

// Filter options
export interface VideoFilters {
  searchQuery: string
  status: ProcessingStatus | 'all'
  sortBy: 'uploaded_at' | 'title' | 'duration_seconds' | 'file_size_mb'
  sortOrder: 'asc' | 'desc'
}

// View mode
export type VideoViewMode = 'grid' | 'list'

// Helper to format duration (seconds to MM:SS)
export function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// Helper to format file size
export function formatFileSize(mb: number): string {
  if (mb < 1024) {
    return `${mb.toFixed(1)} MB`
  }
  return `${(mb / 1024).toFixed(2)} GB`
}

// Helper to format upload date
export function formatUploadDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}
