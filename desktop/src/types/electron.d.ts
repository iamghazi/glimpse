import type { AppSettings } from './settings'
import type { HealthCheckResponse } from './backend'
import type { Video, VideoChunk } from './video'
import type { SearchResult } from './search'
import type { ChatRequest } from './chat'

declare global {
  interface Window {
    electron: {
      settings: {
        get: () => Promise<AppSettings>
        save: (settings: AppSettings) => Promise<void>
        reset: () => Promise<AppSettings>
      }
      backend: {
        health: () => Promise<HealthCheckResponse>
        testConnection: () => Promise<boolean>
        getSettings: () => Promise<AppSettings>
        saveSettings: (settings: AppSettings) => Promise<void>
      }
      dialog: {
        selectDirectory: () => Promise<string | null>
        selectVideoFile: () => Promise<string | null>
      }
      videos: {
        getAll: () => Promise<{count: number, videos: Video[]}>
        get: (videoId: string) => Promise<Video>
        upload: (filePath: string, title: string) => Promise<Video>
        delete: (videoId: string) => Promise<void>
        getChunks: (videoId: string) => Promise<{video_id: string, num_chunks: number, chunks: VideoChunk[]}>
        onUploadProgress: (callback: (data: { progress: number }) => void) => void
      }
      search: {
        search: (params: {
          query: string
          top_k: number
          use_cascaded_reranking: boolean
          confidence_threshold: number
        }) => Promise<{
          query: string
          num_results: number
          results: SearchResult[]
          config: {
            score_threshold: number
            confidence_threshold: number
            cascaded_reranking: boolean
          }
        }>
      }
      chat: {
        sendMessage: (request: ChatRequest) => Promise<{ answer: string }>
      }
    }
  }
}

export {}
