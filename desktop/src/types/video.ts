/**
 * Video-related TypeScript types
 * Mirrors backend models from src/models/video.py and src/models/search.py
 */

/**
 * Metadata for a video in the library
 */
export interface VideoMetadata {
  video_id: string
  title: string
  file_path: string
  duration_seconds: number
  fps: number
  resolution: [number, number]
  file_size_mb: number
  uploaded_at: string // ISO datetime string
  indexed_at: string | null // ISO datetime string
  original_filename?: string
}

/**
 * A time-based segment of a video with extracted content
 */
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

/**
 * Search result from video library search
 */
export interface SearchResult {
  chunk_id: string
  video_id: string
  title: string
  start_time: number
  end_time: number
  visual_description: string
  audio_transcript: string
  score: number
  video_path: string
  representative_frame: string
}

/**
 * Complete search response
 */
export interface SearchResponse {
  query: string
  num_results: number
  results: SearchResult[]
  config: {
    score_threshold?: number
    confidence_threshold: number
    cascaded_reranking: boolean
  }
}

/**
 * Video list response
 */
export interface VideoListResponse {
  count: number
  videos: VideoMetadata[]
}

/**
 * Video chunks response
 */
export interface VideoChunksResponse {
  video_id: string
  num_chunks: number
  chunks: VideoChunk[]
  message?: string
}

/**
 * Search options
 */
export interface SearchOptions {
  topK?: number
  useCascadedReranking?: boolean
  confidenceThreshold?: number
  videoIdFilter?: string
  scoreThreshold?: number
  tier1Candidates?: number
}

/**
 * Upload progress state
 */
export interface UploadProgress {
  videoId?: string
  fileName: string
  progress: number // 0-100
  status: 'uploading' | 'processing' | 'complete' | 'error'
  message?: string
}

/**
 * Video processing status
 */
export type VideoStatus = 'uploading' | 'processing' | 'indexed' | 'failed' | 'unknown'

/**
 * Helper to get video status from metadata
 */
export function getVideoStatus(metadata: VideoMetadata): VideoStatus {
  if (metadata.indexed_at) {
    return 'indexed'
  }
  if (metadata.duration_seconds > 0) {
    return 'processing'
  }
  return 'unknown'
}

/**
 * Helper to format video duration (seconds to MM:SS or HH:MM:SS)
 */
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

/**
 * Helper to format timestamp range
 */
export function formatTimeRange(startTime: number, endTime: number): string {
  return `${formatDuration(startTime)} - ${formatDuration(endTime)}`
}

/**
 * Helper to convert file path to file:// URL for Electron
 */
export function getVideoUrl(filePath: string): string {
  // Remove leading ./ if present
  let cleanPath = filePath.startsWith('./') ? filePath.slice(2) : filePath

  // If it's already an absolute path (starts with /), use it as-is
  if (cleanPath.startsWith('/')) {
    return `file://${cleanPath}`
  }

  // If it's a relative path like "data/videos/...", construct absolute path
  // Assuming backend is running from project root
  const projectRoot = '/Users/gs/ai-engineer/video-analyser'
  const absolutePath = `${projectRoot}/${cleanPath}`

  return `file://${absolutePath}`
}

/**
 * Format file size in MB to human readable string
 */
export function formatFileSize(sizeMB: number): string {
  if (sizeMB < 1) {
    return `${Math.round(sizeMB * 1024)} KB`
  }
  if (sizeMB < 1024) {
    return `${sizeMB.toFixed(1)} MB`
  }
  return `${(sizeMB / 1024).toFixed(2)} GB`
}

/**
 * Format upload date to human readable string
 */
export function formatUploadDate(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) {
    return 'Today'
  } else if (diffDays === 1) {
    return 'Yesterday'
  } else if (diffDays < 7) {
    return `${diffDays} days ago`
  } else {
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    })
  }
}
