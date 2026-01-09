import { ipcMain, dialog } from 'electron'
import axios from 'axios'
import FormData from 'form-data'
import fs from 'fs'
import { API_BASE_URL, LONG_OPERATION_TIMEOUT } from './config'

export function registerVideoHandlers() {
  // Get all videos
  ipcMain.handle('videos:get-all', async () => {
    try {
      console.log('[IPC] videos:get-all - requesting:', `${API_BASE_URL}/videos`)
      const response = await axios.get(`${API_BASE_URL}/videos`)
      console.log('[IPC] videos:get-all - success:', response.data)
      return response.data
    } catch (error) {
      console.error('[IPC] videos:get-all - failed:', error)
      throw new Error(`Failed to fetch videos: ${error}`)
    }
  })

  // Get single video
  ipcMain.handle('videos:get', async (_, videoId: string) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/videos/${videoId}`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch video:', error)
      throw new Error(`Failed to fetch video: ${error}`)
    }
  })

  // Upload video with progress
  ipcMain.handle('videos:upload', async (event, filePath: string, title: string) => {
    try {
      const formData = new FormData()

      // Read file from path
      const fileBuffer = fs.readFileSync(filePath)
      const fileName = filePath.split('/').pop() || 'video.mp4'
      formData.append('file', fileBuffer, fileName)
      formData.append('title', title)

      const response = await axios.post(`${API_BASE_URL}/videos/upload`, formData, {
        headers: formData.getHeaders(),
        maxContentLength: Infinity,
        maxBodyLength: Infinity,
        timeout: LONG_OPERATION_TIMEOUT, // 5 minutes for large uploads
        onUploadProgress: (progressEvent) => {
          const progress = progressEvent.total
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0

          // Send progress to renderer
          event.sender.send('videos:upload-progress', { progress })
        }
      })

      return response.data
    } catch (error) {
      console.error('Failed to upload video:', error)
      throw new Error(`Failed to upload video: ${error}`)
    }
  })

  // Delete video
  ipcMain.handle('videos:delete', async (_, videoId: string) => {
    try {
      await axios.delete(`${API_BASE_URL}/videos/${videoId}`)
    } catch (error) {
      console.error('Failed to delete video:', error)
      throw new Error(`Failed to delete video: ${error}`)
    }
  })

  // Get video chunks
  ipcMain.handle('videos:get-chunks', async (_, videoId: string) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/videos/${videoId}/chunks`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch video chunks:', error)
      throw new Error(`Failed to fetch video chunks: ${error}`)
    }
  })

  // Select video file
  ipcMain.handle('dialog:select-video-file', async () => {
    const result = await dialog.showOpenDialog({
      properties: ['openFile'],
      filters: [
        { name: 'Videos', extensions: ['mp4', 'mov', 'avi', 'mkv', 'webm'] },
        { name: 'All Files', extensions: ['*'] }
      ]
    })

    if (result.canceled) {
      return null
    }

    return result.filePaths[0]
  })
}
