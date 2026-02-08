import { ipcMain } from 'electron'
import axios from 'axios'
import { API_BASE_URL } from './config'

// Longer timeout for agent operations
const AGENT_TIMEOUT = 300000 // 5 minutes

export function registerAgentHandlers() {
  // Start an edit session
  ipcMain.handle('agent:start-edit', async (_, request: { request: string }) => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/agent/edit`,
        { request: request.request },
        { timeout: AGENT_TIMEOUT }
      )
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(`Agent edit failed: ${error.response.data?.detail || error.message}`)
      }
      throw new Error(`Agent edit failed: ${error}`)
    }
  })

  // Get session status
  ipcMain.handle('agent:get-session', async (_, sessionId: string) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/agent/sessions/${sessionId}`)
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(`Get session failed: ${error.response.data?.detail || error.message}`)
      }
      throw new Error(`Get session failed: ${error}`)
    }
  })

  // Approve session and render final video
  ipcMain.handle('agent:approve-session', async (_, sessionId: string) => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/agent/sessions/${sessionId}/approve`,
        {},
        { timeout: AGENT_TIMEOUT }
      )
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(`Approve session failed: ${error.response.data?.detail || error.message}`)
      }
      throw new Error(`Approve session failed: ${error}`)
    }
  })

  // Provide feedback for refinement
  ipcMain.handle('agent:provide-feedback', async (_, sessionId: string, feedback: string) => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/agent/sessions/${sessionId}/feedback`,
        { feedback },
        { timeout: AGENT_TIMEOUT }
      )
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(`Feedback failed: ${error.response.data?.detail || error.message}`)
      }
      throw new Error(`Feedback failed: ${error}`)
    }
  })
}
