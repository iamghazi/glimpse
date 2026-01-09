// Search options
export interface SearchOptions {
  top_k: number  // max results (1-50)
  use_cascaded_reranking: boolean
  confidence_threshold: number  // 0-1
}

// Search result from backend
export interface SearchResult {
  chunk_id: string
  video_id: string
  title: string
  start_time: number
  end_time: number
  score: number  // confidence score 0-1
  visual_description: string
  audio_transcript: string
  video_path: string
  representative_frame: string
}

// Search request
export interface SearchRequest {
  query: string
  top_k: number
  use_cascaded_reranking: boolean
  confidence_threshold: number
  video_id_filter?: string | null  // Optional filter to specific video
  score_threshold?: number  // Minimum similarity score for Tier 1
  tier1_candidates?: number  // Number of candidates for Tier 1 retrieval
}

// Search response
export interface SearchResponse {
  query: string
  num_results: number
  results: SearchResult[]
  config: {
    score_threshold: number
    confidence_threshold: number
    cascaded_reranking: boolean
  }
}

// Processing tier status
export type ProcessingTier = 'embedding' | 'initial-ranking' | 'reranking'

export interface ProcessingStatus {
  currentTier: ProcessingTier | null
  completed: ProcessingTier[]
  isProcessing: boolean
}

// Confidence level for badge coloring
export type ConfidenceLevel = 'high' | 'medium' | 'low'

export function getConfidenceLevel(score: number): ConfidenceLevel {
  if (score >= 0.8) return 'high'
  if (score >= 0.5) return 'medium'
  return 'low'
}

export function getConfidenceBadgeVariant(level: ConfidenceLevel): 'success' | 'warning' | 'error' {
  switch (level) {
    case 'high': return 'success'
    case 'medium': return 'warning'
    case 'low': return 'error'
  }
}

// Helper to format timestamp range
export function formatTimestampRange(startTime: number, endTime: number): string {
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  return `${formatTime(startTime)} - ${formatTime(endTime)}`
}

// Helper to format confidence percentage
export function formatConfidence(score: number): string {
  return `${Math.round(score * 100)}%`
}
