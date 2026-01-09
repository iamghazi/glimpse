import { ipcMain } from 'electron'
import axios from 'axios'
import type { AppSettings } from '../../src/types/settings'
import type { HealthCheckResponse } from '../../src/types/backend'
import { API_BASE_URL } from './config'

export function registerBackendHandlers() {
  // Health check
  ipcMain.handle('backend:health', async () => {
    try {
      console.log('[IPC] Health check - requesting:', `${API_BASE_URL}/health`)
      const response = await axios.get<HealthCheckResponse>(`${API_BASE_URL}/health`)
      console.log('[IPC] Health check - success:', response.data)
      return response.data
    } catch (error) {
      console.error('[IPC] Health check - failed:', error)
      throw new Error(`Backend health check failed: ${error}`)
    }
  })

  // Test GCP connection
  ipcMain.handle('backend:test-connection', async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/settings/test-connection`)
      return response.data.connected
    } catch (error) {
      return false
    }
  })

  // Get settings from backend
  ipcMain.handle('backend:get-settings', async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/settings`)

      // Transform flat backend response to nested frontend structure
      const backendSettings = response.data
      const frontendSettings: AppSettings = {
        googleCloud: {
          GCP_PROJECT_ID: backendSettings.GCP_PROJECT_ID,
          GCP_LOCATION: backendSettings.GCP_LOCATION,
          GEMINI_MODEL: backendSettings.GEMINI_MODEL
        },
        videoProcessing: {
          CHUNK_DURATION_SECONDS: backendSettings.CHUNK_DURATION_SECONDS,
          CHUNK_OVERLAP_SECONDS: backendSettings.CHUNK_OVERLAP_SECONDS,
          FRAME_EXTRACTION_FPS: backendSettings.FRAME_EXTRACTION_FPS
        },
        searchEmbedding: {
          EMBEDDING_MAX_WORKERS: backendSettings.EMBEDDING_MAX_WORKERS,
          TIER1_CANDIDATES: backendSettings.TIER1_CANDIDATES,
          CONFIDENCE_THRESHOLD: backendSettings.CONFIDENCE_THRESHOLD
        },
        dataStorage: {
          DATA_DIR: backendSettings.DATA_DIR,
          VIDEOS_DIR: backendSettings.VIDEOS_DIR,
          FRAMES_DIR: backendSettings.FRAMES_DIR,
          METADATA_DIR: backendSettings.METADATA_DIR,
          QDRANT_STORAGE_DIR: backendSettings.QDRANT_STORAGE_DIR
        }
      }

      return frontendSettings
    } catch (error) {
      throw new Error(`Failed to get settings from backend: ${error}`)
    }
  })

  // Save settings to backend
  ipcMain.handle('backend:save-settings', async (_, settings: AppSettings) => {
    try {
      // Transform nested frontend structure to flat backend structure
      const backendPayload = {
        GCP_PROJECT_ID: settings.googleCloud.GCP_PROJECT_ID,
        GCP_LOCATION: settings.googleCloud.GCP_LOCATION,
        GEMINI_MODEL: settings.googleCloud.GEMINI_MODEL,
        CHUNK_DURATION_SECONDS: settings.videoProcessing.CHUNK_DURATION_SECONDS,
        CHUNK_OVERLAP_SECONDS: settings.videoProcessing.CHUNK_OVERLAP_SECONDS,
        FRAME_EXTRACTION_FPS: settings.videoProcessing.FRAME_EXTRACTION_FPS,
        EMBEDDING_MAX_WORKERS: settings.searchEmbedding.EMBEDDING_MAX_WORKERS,
        TIER1_CANDIDATES: settings.searchEmbedding.TIER1_CANDIDATES,
        CONFIDENCE_THRESHOLD: settings.searchEmbedding.CONFIDENCE_THRESHOLD,
        DATA_DIR: settings.dataStorage.DATA_DIR,
        VIDEOS_DIR: settings.dataStorage.VIDEOS_DIR,
        FRAMES_DIR: settings.dataStorage.FRAMES_DIR,
        METADATA_DIR: settings.dataStorage.METADATA_DIR,
        QDRANT_STORAGE_DIR: settings.dataStorage.QDRANT_STORAGE_DIR
      }

      await axios.put(`${API_BASE_URL}/settings`, backendPayload)
    } catch (error) {
      throw new Error(`Failed to save settings to backend: ${error}`)
    }
  })
}
