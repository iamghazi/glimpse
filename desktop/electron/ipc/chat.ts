import { ipcMain } from 'electron'
import axios from 'axios'
import { API_BASE_URL } from './config'

export function registerChatHandlers() {
  // Send chat message
  ipcMain.handle('chat:send-message', async (_, request: {
    query: string
    clip_ids: string[]
  }) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        query: request.query,
        clip_ids: request.clip_ids
      })

      return response.data
    } catch (error) {
      console.error('Chat request failed:', error)
      throw new Error(`Chat request failed: ${error}`)
    }
  })
}
