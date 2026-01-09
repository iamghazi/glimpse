import { ipcMain } from 'electron'
import axios from 'axios'
import { API_BASE_URL } from './config'

export function registerSearchHandlers() {
  // Semantic search
  ipcMain.handle('search:search', async (_, params: {
    query: string
    top_k: number
    use_cascaded_reranking: boolean
    confidence_threshold: number
    video_id_filter?: string | null
    score_threshold?: number
    tier1_candidates?: number
  }) => {
    try {
      // Build request body with all parameters including optional ones
      const requestBody: any = {
        query: params.query,
        top_k: params.top_k,
        use_cascaded_reranking: params.use_cascaded_reranking,
        confidence_threshold: params.confidence_threshold
      }

      // Add optional parameters if provided
      if (params.video_id_filter !== undefined) {
        requestBody.video_id_filter = params.video_id_filter
      }
      if (params.score_threshold !== undefined) {
        requestBody.score_threshold = params.score_threshold
      }
      if (params.tier1_candidates !== undefined) {
        requestBody.tier1_candidates = params.tier1_candidates
      }

      const response = await axios.post(`${API_BASE_URL}/search`, requestBody)

      return response.data
    } catch (error) {
      console.error('Search failed:', error)
      throw new Error(`Search failed: ${error}`)
    }
  })
}
