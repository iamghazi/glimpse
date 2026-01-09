// Chat message role
export type MessageRole = 'user' | 'assistant'

// Chat message
export interface ChatMessage {
  id: string  // unique ID for key in v-for
  role: MessageRole
  content: string
  timestamp: Date
  isThinking?: boolean  // For showing loading state
}

// Active clip in context
export interface ActiveClip {
  clip_id: string
  video_id: string
  title: string
  start_time: number
  end_time: number
  thumbnail: string
  confidence_score?: number  // If added from search results
}

// Chat request to backend
export interface ChatRequest {
  query: string
  clip_ids: string[]
}

// Chat response from backend
export interface ChatResponse {
  answer: string
  sources: string[]  // chunk_ids used
  cache_info?: {
    cache_hit: boolean
    cache_name?: string
    cached_clips?: number
  }
  timestamp: string
}

// Date separator for message timeline
export interface DateSeparator {
  id: string
  date: string
  isDateSeparator: true
}

export type MessageOrSeparator = ChatMessage | DateSeparator

// Helper to check if item is date separator
export function isDateSeparator(item: MessageOrSeparator): item is DateSeparator {
  return 'isDateSeparator' in item && item.isDateSeparator === true
}

// Helper to format timestamp for date separators
export function formatMessageDate(date: Date): string {
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)

  if (date.toDateString() === today.toDateString()) {
    return 'Today'
  } else if (date.toDateString() === yesterday.toDateString()) {
    return 'Yesterday'
  } else {
    return date.toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    })
  }
}

// Helper to format message time
export function formatMessageTime(date: Date): string {
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  })
}

// Helper to format clip timestamp
export function formatClipTimestamp(startTime: number, endTime: number): string {
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  return `${formatTime(startTime)} - ${formatTime(endTime)}`
}
