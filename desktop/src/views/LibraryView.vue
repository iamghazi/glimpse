<template>
  <div class="flex h-screen bg-background">
    <AppSidebar />

    <main class="flex-1 flex flex-col h-full overflow-hidden relative">
      <AppHeader title="Library" subtitle="Manage your video collection" />

      <div class="flex-1 overflow-y-auto p-8">
        <div class="max-w-7xl mx-auto space-y-6">
          <!-- Upload Area & Storage Info -->
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="lg:col-span-2">
              <VideoUpload
                :disabled="uploading"
                @file-selected="handleFileSelected"
              />
            </div>
            <StorageInfo
              :total-videos="libraryStore.totalVideos"
              :used-storage="totalStorageUsed"
            />
          </div>

          <!-- Active Uploads -->
          <div v-if="activeUploads.length > 0" class="space-y-3">
            <h3 class="text-sm font-semibold text-slate-900">Active Uploads</h3>
            <UploadProgress
              v-for="upload in activeUploads"
              :key="upload.fileName"
              :file-name="upload.fileName"
              :progress="upload.progress"
              @cancel="handleCancelUpload(upload.fileName)"
            />
          </div>

          <!-- Filters -->
          <VideoFilters
            :filters="libraryStore.filters"
            :columns="gridColumns"
            @update:filters="libraryStore.updateFilters"
            @update:columns="gridColumns = $event"
          />

          <!-- Loading State -->
          <div v-if="libraryStore.loading" class="flex items-center justify-center py-16">
            <span class="material-symbols-outlined text-4xl text-primary animate-spin">
              sync
            </span>
          </div>

          <!-- Error State -->
          <div v-else-if="libraryStore.error" class="p-6 bg-error/5 border border-error/20 rounded-xl">
            <div class="flex items-start gap-3">
              <span class="material-symbols-outlined text-error">
                error
              </span>
              <div>
                <p class="text-sm font-medium text-error mb-1">Failed to load videos</p>
                <p class="text-sm text-slate-600">{{ libraryStore.error }}</p>
              </div>
            </div>
          </div>

          <!-- Empty State -->
          <EmptyState
            v-else-if="libraryStore.filteredVideos.length === 0 && !libraryStore.loading"
            :title="emptyStateTitle"
            :description="emptyStateDescription"
            :icon="emptyStateIcon"
          >
            <template #action>
              <BaseButton
                v-if="libraryStore.totalVideos === 0"
                variant="primary"
                icon="upload"
                @click="triggerFileSelect"
              >
                Upload Your First Video
              </BaseButton>
            </template>
          </EmptyState>

          <!-- Video Grid -->
          <VideoGrid
            v-else
            :videos="libraryStore.filteredVideos"
            :columns="gridColumns"
            @video-click="handleVideoClick"
            @view-chunks="handleViewChunks"
            @view-details="handleViewDetails"
            @delete="handleDeleteRequest"
          />
        </div>
      </div>
    </main>

    <!-- Video Detail Modal -->
    <VideoDetailModal
      :show="showDetailModal"
      :video="selectedVideo"
      @close="showDetailModal = false"
      @view-chunks="handleViewChunks(selectedVideo?.video_id || '')"
    />

    <!-- Delete Confirmation -->
    <DeleteConfirmation
      :show="showDeleteConfirm"
      :video-title="videoToDelete?.title || ''"
      :loading="deleting"
      @confirm="handleDeleteConfirm"
      @cancel="showDeleteConfirm = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useLibraryStore } from '@/stores/library'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import VideoUpload from '@/components/library/VideoUpload.vue'
import StorageInfo from '@/components/library/StorageInfo.vue'
import VideoFilters from '@/components/library/VideoFilters.vue'
import VideoGrid from '@/components/library/VideoGrid.vue'
import EmptyState from '@/components/library/EmptyState.vue'
import UploadProgress from '@/components/library/UploadProgress.vue'
import VideoDetailModal from '@/components/library/VideoDetailModal.vue'
import DeleteConfirmation from '@/components/library/DeleteConfirmation.vue'
import type { VideoWithState } from '@/types/video'

const router = useRouter()
const libraryStore = useLibraryStore()

const gridColumns = ref(3)
const uploading = ref(false)
const showDetailModal = ref(false)
const showDeleteConfirm = ref(false)
const selectedVideo = ref<VideoWithState | null>(null)
const videoToDelete = ref<VideoWithState | null>(null)
const deleting = ref(false)

interface ActiveUpload {
  fileName: string
  progress: number
}

const activeUploads = ref<ActiveUpload[]>([])

const totalStorageUsed = computed(() => {
  return libraryStore.videos.reduce((sum, video) => sum + video.file_size_mb, 0)
})

const emptyStateTitle = computed(() => {
  if (libraryStore.totalVideos === 0) {
    return 'No videos yet'
  }
  return 'No videos found'
})

const emptyStateDescription = computed(() => {
  if (libraryStore.totalVideos === 0) {
    return 'Upload your first video to get started with semantic search and AI chat.'
  }
  return 'Try adjusting your filters or search query.'
})

const emptyStateIcon = computed(() => {
  if (libraryStore.totalVideos === 0) {
    return 'video_library'
  }
  return 'search_off'
})

onMounted(async () => {
  await libraryStore.loadVideos()

  // Set up upload progress listener
  window.electron.videos.onUploadProgress((data) => {
    if (activeUploads.value.length > 0) {
      activeUploads.value[0].progress = data.progress
    }
  })
})

async function handleFileSelected(file: File) {
  try {
    uploading.value = true

    // For Electron, we need to use the file dialog to get the actual file path
    // The File object from the browser doesn't have the full path
    const filePath = await window.electron.dialog.selectVideoFile()

    if (!filePath) {
      uploading.value = false
      return
    }

    const fileName = filePath.split(/[/\\]/).pop() || 'video'

    // Add to active uploads
    activeUploads.value.push({
      fileName,
      progress: 0
    })

    // Upload video using file path
    await libraryStore.uploadVideo({
      filePath: filePath,  // Pass the full file path
      title: fileName.replace(/\.[^/.]+$/, '') // Remove extension
    })

    // Remove from active uploads
    activeUploads.value = activeUploads.value.filter(u => u.fileName !== fileName)
  } catch (error) {
    console.error('Upload failed:', error)
  } finally {
    uploading.value = false
  }
}

function handleCancelUpload(fileName: string) {
  // TODO: Implement upload cancellation
  activeUploads.value = activeUploads.value.filter(u => u.fileName !== fileName)
}

function handleVideoClick(videoId: string) {
  const video = libraryStore.videos.find(v => v.video_id === videoId)
  if (video) {
    selectedVideo.value = video
    showDetailModal.value = true
  }
}

function handleViewDetails(videoId: string) {
  const video = libraryStore.videos.find(v => v.video_id === videoId)
  if (video) {
    selectedVideo.value = video
    showDetailModal.value = true
  }
}

function handleViewChunks(videoId: string) {
  // TODO: Navigate to chunk view or open chunks modal
  console.log('View chunks for video:', videoId)
}

function handleDeleteRequest(videoId: string) {
  const video = libraryStore.videos.find(v => v.video_id === videoId)
  if (video) {
    videoToDelete.value = video
    showDeleteConfirm.value = true
  }
}

async function handleDeleteConfirm() {
  if (!videoToDelete.value) return

  try {
    deleting.value = true
    await libraryStore.deleteVideo(videoToDelete.value.video_id)
    showDeleteConfirm.value = false
    videoToDelete.value = null
  } catch (error) {
    console.error('Delete failed:', error)
  } finally {
    deleting.value = false
  }
}

function triggerFileSelect() {
  // Trigger file input click
  const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
  fileInput?.click()
}
</script>
