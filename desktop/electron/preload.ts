import { contextBridge, ipcRenderer } from 'electron'
import type { AppSettings } from '../src/types/settings'
import type { HealthCheckResponse } from '../src/types/backend'
import type { Video, VideoChunk, VideoUploadRequest } from '../src/types/video'
import type { SearchOptions, SearchResult } from '../src/types/search'
import type { ChatRequest } from '../src/types/chat'

contextBridge.exposeInMainWorld('electron', {
  settings: {
    get: () => ipcRenderer.invoke('settings:get') as Promise<AppSettings>,
    save: (settings: AppSettings) => ipcRenderer.invoke('settings:save', settings) as Promise<void>,
    reset: () => ipcRenderer.invoke('settings:reset') as Promise<AppSettings>
  },
  backend: {
    health: () => ipcRenderer.invoke('backend:health') as Promise<HealthCheckResponse>,
    testConnection: () => ipcRenderer.invoke('backend:test-connection') as Promise<boolean>,
    getSettings: () => ipcRenderer.invoke('backend:get-settings') as Promise<AppSettings>,
    saveSettings: (settings: AppSettings) => ipcRenderer.invoke('backend:save-settings', settings) as Promise<void>
  },
  dialog: {
    selectDirectory: () => ipcRenderer.invoke('dialog:select-directory') as Promise<string | null>,
    selectVideoFile: () => ipcRenderer.invoke('dialog:select-video-file') as Promise<string | null>
  },
  videos: {
    getAll: () => ipcRenderer.invoke('videos:get-all') as Promise<{count: number, videos: Video[]}>,
    get: (videoId: string) => ipcRenderer.invoke('videos:get', videoId) as Promise<Video>,
    upload: (filePath: string, title: string) => ipcRenderer.invoke('videos:upload', filePath, title) as Promise<Video>,
    delete: (videoId: string) => ipcRenderer.invoke('videos:delete', videoId) as Promise<void>,
    getChunks: (videoId: string) => ipcRenderer.invoke('videos:get-chunks', videoId) as Promise<{video_id: string, num_chunks: number, chunks: VideoChunk[]}>,
    onUploadProgress: (callback: (data: { progress: number }) => void) => {
      ipcRenderer.on('videos:upload-progress', (_, data) => callback(data))
    }
  },
  search: {
    search: (params: {
      query: string
      top_k: number
      use_cascaded_reranking: boolean
      confidence_threshold: number
    }) => ipcRenderer.invoke('search:search', params) as Promise<{
      query: string
      num_results: number
      results: SearchResult[]
      config: {
        score_threshold: number
        confidence_threshold: number
        cascaded_reranking: boolean
      }
    }>
  },
  chat: {
    sendMessage: (request: ChatRequest) => ipcRenderer.invoke('chat:send-message', request) as Promise<{ answer: string }>
  }
})
