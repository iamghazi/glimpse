import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  Video,
  VideoWithState,
  VideoFilters,
  VideoViewMode,
  VideoUploadRequest,
  VideoChunk,
  ProcessingStatus
} from '@/types/video'

export const useLibraryStore = defineStore('library', () => {
  // State
  const videos = ref<VideoWithState[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const uploadProgress = ref<Record<string, number>>({})  // video_id -> progress
  const filters = ref<VideoFilters>({
    searchQuery: '',
    status: 'all',
    sortBy: 'uploaded_at',
    sortOrder: 'desc'
  })
  const viewMode = ref<VideoViewMode>('grid')
  const selectedVideoId = ref<string | null>(null)

  // Computed
  const filteredVideos = computed(() => {
    let result = [...videos.value]

    // Apply search query filter
    if (filters.value.searchQuery.trim()) {
      const query = filters.value.searchQuery.toLowerCase()
      result = result.filter(v =>
        v.title.toLowerCase().includes(query) ||
        v.original_filename.toLowerCase().includes(query)
      )
    }

    // Apply status filter
    if (filters.value.status !== 'all') {
      result = result.filter(v => v.status === filters.value.status)
    }

    // Apply sorting
    result.sort((a, b) => {
      const field = filters.value.sortBy
      const order = filters.value.sortOrder === 'asc' ? 1 : -1

      if (field === 'title') {
        return a.title.localeCompare(b.title) * order
      } else if (field === 'uploaded_at') {
        return (new Date(a.uploaded_at).getTime() - new Date(b.uploaded_at).getTime()) * order
      } else {
        const aValue = a[field as keyof Pick<VideoWithState, 'duration_seconds' | 'file_size_mb'>]
        const bValue = b[field as keyof Pick<VideoWithState, 'duration_seconds' | 'file_size_mb'>]
        return (aValue - bValue) * order
      }
    })

    return result
  })

  const totalVideos = computed(() => videos.value.length)
  const processingVideos = computed(() =>
    videos.value.filter(v => v.status === 'processing' || v.status === 'uploading')
  )
  const indexedVideos = computed(() =>
    videos.value.filter(v => v.status === 'indexed' || v.status === 'ready')
  )

  // Actions
  async function loadVideos() {
    console.log('[Library] Loading videos...')
    loading.value = true
    error.value = null

    try {
      console.log('[Library] Calling window.electron.videos.getAll()...')
      const response = await window.electron.videos.getAll()
      console.log('[Library] Response:', response)

      // Transform to VideoWithState
      videos.value = response.videos.map(v => ({
        ...v,
        status: determineStatus(v),
        chunkCount: undefined  // Will be loaded separately if needed
      }))
      console.log('[Library] Loaded', videos.value.length, 'videos')
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load videos'
      console.error('[Library] Error loading videos:', err)
    } finally {
      loading.value = false
    }
  }

  async function uploadVideo(request: VideoUploadRequest) {
    const tempId = `temp-${Date.now()}`

    try {
      // Get file size estimate (0 if not available from File object)
      const fileSize = request.file?.size ? request.file.size / (1024 * 1024) : 0
      const fileName = request.file?.name || request.filePath?.split(/[/\\]/).pop() || 'video'

      // Add placeholder video
      const placeholderVideo: VideoWithState = {
        video_id: tempId,
        title: request.title,
        file_path: '',
        duration_seconds: 0,
        fps: 0,
        resolution: [0, 0],
        file_size_mb: fileSize,
        uploaded_at: new Date().toISOString(),
        indexed_at: null,
        original_filename: fileName,
        status: 'uploading',
        uploadProgress: 0
      }
      videos.value.unshift(placeholderVideo)
      uploadProgress.value[tempId] = 0

      // Use the provided filePath, or try to get it from the File object (won't work in Electron)
      const filePath = request.filePath || (request.file as any).path || request.file?.name

      if (!filePath) {
        throw new Error('No file path provided')
      }

      // Upload via IPC
      const response = await window.electron.videos.upload(filePath, request.title)

      // Replace placeholder with actual video
      const idx = videos.value.findIndex(v => v.video_id === tempId)
      if (idx >= 0) {
        videos.value[idx] = {
          ...response,
          status: 'processing',
          uploadProgress: 100
        }
      }

      delete uploadProgress.value[tempId]

      return response.video_id
    } catch (err) {
      // Mark as failed
      const idx = videos.value.findIndex(v => v.video_id === tempId)
      if (idx >= 0) {
        videos.value[idx].status = 'failed'
        videos.value[idx].error = err instanceof Error ? err.message : 'Upload failed'
      }
      delete uploadProgress.value[tempId]
      throw err
    }
  }

  async function deleteVideo(videoId: string) {
    try {
      await window.electron.videos.delete(videoId)
      videos.value = videos.value.filter(v => v.video_id !== videoId)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete video'
      throw err
    }
  }

  async function loadVideoChunks(videoId: string): Promise<VideoChunk[]> {
    try {
      const response = await window.electron.videos.getChunks(videoId)

      // Update chunk count
      const idx = videos.value.findIndex(v => v.video_id === videoId)
      if (idx >= 0) {
        videos.value[idx].chunkCount = response.chunks.length
      }

      return response.chunks
    } catch (err) {
      console.error('Error loading chunks:', err)
      return []
    }
  }

  function updateFilters(newFilters: Partial<VideoFilters>) {
    filters.value = { ...filters.value, ...newFilters }
  }

  function setViewMode(mode: VideoViewMode) {
    viewMode.value = mode
  }

  function selectVideo(videoId: string | null) {
    selectedVideoId.value = videoId
  }

  function determineStatus(video: Video): ProcessingStatus {
    if (video.indexed_at) return 'indexed'
    if (video.uploaded_at) return 'processing'
    return 'ready'
  }

  return {
    // State
    videos,
    loading,
    error,
    uploadProgress,
    filters,
    viewMode,
    selectedVideoId,

    // Computed
    filteredVideos,
    totalVideos,
    processingVideos,
    indexedVideos,

    // Actions
    loadVideos,
    uploadVideo,
    deleteVideo,
    loadVideoChunks,
    updateFilters,
    setViewMode,
    selectVideo
  }
})
