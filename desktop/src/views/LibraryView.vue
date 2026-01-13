<template>
  <div class="flex h-full bg-background">
    <AppSidebar />

    <main class="flex-1 flex flex-col h-full overflow-hidden relative">
      <!-- Integrated Header with Search & Controls -->
      <header class="bg-white shrink-0 px-8 py-6 z-10 border-b border-slate-200">
        <div class="flex flex-col xl:flex-row xl:items-center justify-between gap-6">
          <!-- Title Block -->
          <div class="flex flex-col gap-1 min-w-[200px]">
            <h2 class="text-3xl font-bold tracking-tight text-slate-900">My Library</h2>
            <p class="text-sm text-slate-500">Manage and search your local video index</p>
          </div>

          <!-- Controls Block -->
          <div class="flex flex-1 items-center gap-3 justify-end flex-wrap">
            <!-- Search -->
            <div class="relative flex-1 max-w-lg min-w-[280px] group">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <span class="material-symbols-outlined text-slate-400 group-focus-within:text-primary transition-colors">search</span>
              </div>
              <input
                v-model="searchQuery"
                class="block w-full pl-10 pr-12 py-2.5 text-sm bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary text-slate-900 placeholder-slate-400 shadow-sm transition-all"
                placeholder="Search by keyword or transcript content..."
                type="text"
              />
              <button
                class="absolute inset-y-0 right-1 px-2 flex items-center text-slate-400 hover:text-primary transition-colors"
                title="Advanced Filters"
              >
                <span class="material-symbols-outlined text-[20px]">tune</span>
              </button>
            </div>

            <!-- View Toggle -->
            <div class="bg-slate-200 p-1 rounded-lg flex items-center shrink-0">
              <button
                :class="[
                  'p-1.5 rounded-md transition-all',
                  viewMode === 'grid'
                    ? 'bg-white shadow-sm text-primary'
                    : 'text-slate-500 hover:text-slate-700'
                ]"
                @click="viewMode = 'grid'"
              >
                <span class="material-symbols-outlined text-[20px] block">grid_view</span>
              </button>
              <button
                :class="[
                  'p-1.5 rounded-md transition-all',
                  viewMode === 'list'
                    ? 'bg-white shadow-sm text-primary'
                    : 'text-slate-500 hover:text-slate-700'
                ]"
                @click="viewMode = 'list'"
              >
                <span class="material-symbols-outlined text-[20px] block">view_list</span>
              </button>
            </div>

            <!-- Upload Button -->
            <button
              :disabled="uploading"
              class="bg-primary hover:bg-blue-600 text-white px-4 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-2 shadow-lg shadow-blue-500/20 transition-all active:scale-95 shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
              @click="triggerFileSelect"
            >
              <span class="material-symbols-outlined text-[20px]">upload_file</span>
              Upload Video
            </button>
          </div>
        </div>

        <!-- Filters Bar -->
        <div
          v-if="activeFilters.length > 0"
          class="flex items-center gap-2 mt-4 overflow-x-auto pb-1 no-scrollbar"
        >
          <span class="text-xs font-semibold text-slate-500 mr-2 uppercase tracking-wider">Filters:</span>
          <button
            v-for="filter in activeFilters"
            :key="filter.key"
            class="flex items-center gap-1.5 bg-white border border-slate-200 rounded-full px-3 py-1 text-xs font-medium text-slate-700 hover:border-slate-300 transition-colors"
            @click="removeFilter(filter.key)"
          >
            <span>{{ filter.label }}</span>
            <span class="material-symbols-outlined text-[14px]">close</span>
          </button>
          <button
            class="flex items-center gap-1 text-xs text-primary font-medium px-2 hover:underline"
            @click="clearAllFilters"
          >
            Clear all
          </button>
        </div>
      </header>

      <!-- Scrollable Content -->
      <div class="flex-1 overflow-y-auto px-8 pb-10">
        <!-- Processing Status Card -->
        <div
          v-if="activeUploads.length > 0"
          class="mb-8 mt-8 bg-white rounded-xl border border-blue-100 p-5 shadow-sm relative overflow-hidden group"
        >
          <div class="absolute top-0 left-0 w-1 h-full bg-primary"></div>
          <div class="absolute right-0 top-0 bottom-0 w-64 bg-gradient-to-l from-blue-50/50 to-transparent pointer-events-none"></div>

          <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 relative z-10">
            <div class="flex items-start gap-4">
              <div class="w-12 h-12 rounded-lg bg-blue-50 flex items-center justify-center shrink-0">
                <span class="material-symbols-outlined text-primary text-2xl animate-pulse">auto_awesome</span>
              </div>
              <div>
                <h3 class="text-base font-bold text-slate-900">Processing: {{ activeUploads[0].fileName }}</h3>
                <p class="text-sm text-slate-500">AI analysis in progress. Search will be available shortly.</p>
              </div>
            </div>

            <div class="w-full md:w-1/3 flex flex-col gap-2">
              <div class="flex justify-between text-xs font-semibold uppercase tracking-wider text-slate-500">
                <span>Analyzing</span>
                <span>{{ activeUploads[0].progress }}%</span>
              </div>
              <div class="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                <div
                  class="h-full bg-primary rounded-full relative transition-all duration-300"
                  :style="{ width: `${activeUploads[0].progress}%` }"
                >
                  <div class="absolute inset-0 bg-white/20 animate-[shimmer_2s_infinite] w-full h-full"></div>
                </div>
              </div>
              <div class="flex justify-between text-[10px] text-slate-400 mt-1">
                <span class="text-green-600 flex items-center gap-1">
                  <span class="material-symbols-outlined text-[10px]">check_circle</span> Uploaded
                </span>
                <span :class="activeUploads[0].progress > 50 ? 'text-green-600' : 'text-primary font-bold'">
                  {{ activeUploads[0].progress > 50 ? '✓ Chunked' : 'Analyzing' }}
                </span>
                <span :class="activeUploads[0].progress === 100 ? 'text-green-600' : 'text-slate-300'">
                  {{ activeUploads[0].progress === 100 ? '✓ Indexing' : 'Indexing' }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="libraryStore.loading" class="flex items-center justify-center py-16 mt-8">
          <span class="material-symbols-outlined text-4xl text-primary animate-spin">
            sync
          </span>
        </div>

        <!-- Error State -->
        <div v-else-if="libraryStore.error" class="p-6 bg-red-50 border border-red-200 rounded-xl mt-8">
          <div class="flex items-start gap-3">
            <span class="material-symbols-outlined text-red-600">
              error
            </span>
            <div>
              <p class="text-sm font-medium text-red-600 mb-1">Failed to load videos</p>
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
        <div
          v-else
          :class="[
            'grid gap-6 mt-8',
            viewMode === 'grid'
              ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5'
              : 'grid-cols-1'
          ]"
        >
          <VideoCard
            v-for="video in libraryStore.filteredVideos"
            :key="video.video_id"
            :video="video"
            @click="handleVideoClick(video.video_id)"
            @view-chunks="handleViewChunks(video.video_id)"
            @view-details="handleViewDetails(video.video_id)"
            @delete="handleDeleteRequest(video.video_id)"
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

    <!-- Video Player Modal -->
    <VideoModal />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useLibraryStore } from '@/stores/library'
import { useVideoPlayerStore } from '@/stores/videoPlayer'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import VideoCard from '@/components/library/VideoCard.vue'
import EmptyState from '@/components/library/EmptyState.vue'
import VideoDetailModal from '@/components/library/VideoDetailModal.vue'
import DeleteConfirmation from '@/components/library/DeleteConfirmation.vue'
import VideoModal from '@/components/video/VideoModal.vue'
import type { VideoWithState } from '@/types/video'

const router = useRouter()
const libraryStore = useLibraryStore()
const videoPlayerStore = useVideoPlayerStore()

const searchQuery = ref('')
const viewMode = ref<'grid' | 'list'>('grid')
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

interface FilterItem {
  key: string
  label: string
}

const activeFilters = ref<FilterItem[]>([])

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
  // Open video player with playback
  videoPlayerStore.openVideo(videoId, { sourceView: 'library' })
}

function handleViewDetails(videoId: string) {
  const video = libraryStore.videos.find(v => v.video_id === videoId)
  if (video) {
    selectedVideo.value = video
    showDetailModal.value = true
  }
}

function handleViewChunks(videoId: string) {
  // Open video player to view chunks
  videoPlayerStore.openVideo(videoId, { sourceView: 'library' })
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

async function triggerFileSelect() {
  try {
    uploading.value = true

    // For Electron, we need to use the file dialog to get the actual file path
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
      filePath: filePath,
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

function removeFilter(key: string) {
  activeFilters.value = activeFilters.value.filter(f => f.key !== key)
  // TODO: Update library store filters
}

function clearAllFilters() {
  activeFilters.value = []
  searchQuery.value = ''
  // TODO: Clear library store filters
}
</script>
