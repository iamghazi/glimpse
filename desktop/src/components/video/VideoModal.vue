<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useVideoPlayerStore } from '@/stores/videoPlayer'
import { getVideoUrl, formatTimeRange } from '@/types/video'
import VideoPlayer from './VideoPlayer.vue'

const playerStore = useVideoPlayerStore()

const playerRef = ref<InstanceType<typeof VideoPlayer> | null>(null)
const chunkFilter = ref('')

// Compute back button text based on source view
const backButtonText = computed(() => {
  switch (playerStore.sourceView) {
    case 'search':
      return 'Back to Search'
    case 'chat':
      return 'Back to Chat'
    case 'library':
    default:
      return 'Back to Library'
  }
})

// Computed
const videoSrc = computed(() => {
  if (!playerStore.videoMetadata?.file_path) return ''
  return getVideoUrl(playerStore.videoMetadata.file_path)
})

const filteredChunks = computed(() => {
  if (!chunkFilter.value) return playerStore.chunks

  const query = chunkFilter.value.toLowerCase()
  return playerStore.chunks.filter(chunk => {
    return (
      chunk.visual_description.toLowerCase().includes(query) ||
      chunk.audio_transcript.toLowerCase().includes(query) ||
      formatTimeRange(chunk.start_time, chunk.end_time).includes(query)
    )
  })
})

const currentlyPlayingChunk = computed(() => {
  // TODO: Track current time from video player and match to chunk
  return playerStore.currentChunkId
})

// Handle ESC key
const handleEscape = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && playerStore.isModalOpen) {
    closeModal()
  }
}

const closeModal = () => {
  playerStore.closeVideo()
}

const playChunk = (chunkId: string) => {
  const chunk = playerStore.chunks.find(c => c.chunk_id === chunkId)
  if (chunk && playerRef.value) {
    playerRef.value.seekTo(chunk.start_time)
    playerRef.value.play()
    playerStore.setCurrentChunk(chunkId)
  }
}

// Lifecycle
onMounted(() => {
  document.addEventListener('keydown', handleEscape)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscape)
})

// Watch for modal open/close to handle body scroll
watch(
  () => playerStore.isModalOpen,
  (isOpen) => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  }
)
</script>

<template>
  <Transition name="modal-fade">
    <div
      v-if="playerStore.isModalOpen"
      class="fixed inset-0 z-[60] bg-white flex flex-col h-screen overflow-hidden"
    >
      <!-- Header -->
      <header class="bg-white shrink-0 px-6 py-4 border-b border-slate-200 z-10 flex items-center justify-between">
        <div class="flex items-center gap-4">
          <button
            class="flex items-center gap-2 text-slate-500 hover:text-primary transition-colors"
            @click="closeModal"
          >
            <span class="material-symbols-outlined">arrow_back</span>
            <span class="text-sm font-medium hidden sm:inline">{{ backButtonText }}</span>
          </button>
          <div class="h-6 w-px bg-slate-200"></div>
          <div class="flex flex-col">
            <h2 class="text-sm font-bold text-slate-900 truncate max-w-md">
              {{ playerStore.videoMetadata?.title || 'Loading...' }}
            </h2>
            <span class="text-xs text-slate-500">
              {{ playerStore.videoMetadata?.indexed_at ? 'Indexed • Ready for Search' : 'Processing...' }}
            </span>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <button
            class="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors border border-slate-200"
          >
            <span class="material-symbols-outlined text-[16px]">search</span>
            Search within
          </button>
          <button
            class="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors border border-red-100"
          >
            <span class="material-symbols-outlined text-[16px]">delete</span>
            Delete
          </button>
        </div>
      </header>

      <!-- Main Content -->
      <main class="flex-1 flex overflow-hidden">
        <!-- Video Player Section -->
        <div class="flex-1 overflow-y-auto bg-background p-6 lg:p-10 flex flex-col items-center">
          <div class="w-full max-w-5xl flex flex-col gap-6">
            <!-- Video Player -->
            <div v-if="playerStore.loading" class="w-full aspect-video bg-black rounded-xl flex items-center justify-center">
              <div class="flex flex-col items-center gap-3">
                <div class="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-primary"></div>
                <p class="text-sm text-white">Loading video...</p>
              </div>
            </div>

            <div v-else-if="playerStore.error" class="w-full aspect-video bg-black rounded-xl flex items-center justify-center">
              <div class="text-red-500">{{ playerStore.error }}</div>
            </div>

            <div
              v-else-if="videoSrc"
              class="w-full aspect-video bg-black rounded-xl overflow-hidden shadow-2xl ring-1 ring-slate-900/5 relative group"
            >
              <VideoPlayer
                ref="playerRef"
                :src="videoSrc"
                :start-time="playerStore.startTime"
                :autoplay="true"
              />
            </div>

            <!-- Video Info -->
            <div v-if="playerStore.videoMetadata" class="flex flex-col gap-4">
              <div>
                <h1 class="text-2xl font-bold text-slate-900 mb-2">
                  {{ playerStore.videoMetadata.title }}
                </h1>
                <div class="flex flex-wrap items-center gap-4 text-sm text-slate-500">
                  <div class="flex items-center gap-1.5">
                    <span class="material-symbols-outlined text-[18px]">calendar_today</span>
                    <span>{{ new Date(playerStore.videoMetadata.uploaded_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) }}</span>
                  </div>
                  <div class="flex items-center gap-1.5">
                    <span class="material-symbols-outlined text-[18px]">schedule</span>
                    <span>{{ Math.floor(playerStore.videoMetadata.duration_seconds / 60) }}m {{ Math.floor(playerStore.videoMetadata.duration_seconds % 60) }}s</span>
                  </div>
                  <div class="flex items-center gap-1.5">
                    <span class="material-symbols-outlined text-[18px]">view_agenda</span>
                    <span>{{ playerStore.chunks.length }} Chunks</span>
                  </div>
                  <span
                    v-if="playerStore.videoMetadata.indexed_at"
                    class="px-2 py-0.5 rounded-full bg-green-100 text-green-700 text-xs font-semibold"
                  >
                    Indexed
                  </span>
                </div>
              </div>

              <!-- AI Summary (placeholder) -->
              <div class="p-4 rounded-lg bg-white border border-slate-200">
                <h3 class="text-sm font-semibold text-slate-900 mb-1">AI Summary</h3>
                <p class="text-sm text-slate-600 leading-relaxed">
                  This video contains {{ playerStore.chunks.length }} segments covering various topics.
                  Use the chunks panel to explore specific sections and their content.
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Chunks Sidebar -->
        <div class="w-96 bg-white border-l border-slate-200 flex flex-col shrink-0 z-10 shadow-xl">
          <!-- Sidebar Header -->
          <div class="p-4 border-b border-slate-200 flex flex-col gap-3">
            <div class="flex items-center justify-between">
              <h3 class="font-bold text-slate-900 flex items-center gap-2">
                <span class="material-symbols-outlined text-primary">segment</span>
                Video Chunks
              </h3>
              <div class="flex gap-1">
                <button
                  class="p-1.5 text-slate-400 hover:text-slate-600 rounded hover:bg-slate-100"
                  title="Filter Chunks"
                >
                  <span class="material-symbols-outlined text-[20px]">filter_list</span>
                </button>
                <button
                  class="p-1.5 text-slate-400 hover:text-slate-600 rounded hover:bg-slate-100"
                  title="Export Data"
                >
                  <span class="material-symbols-outlined text-[20px]">download</span>
                </button>
              </div>
            </div>

            <!-- Search Input -->
            <div class="relative">
              <span class="absolute inset-y-0 left-2.5 flex items-center text-slate-400">
                <span class="material-symbols-outlined text-[18px]">search</span>
              </span>
              <input
                v-model="chunkFilter"
                class="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-md text-sm focus:ring-1 focus:ring-primary focus:border-primary placeholder-slate-400 text-slate-900"
                placeholder="Filter chunks..."
                type="text"
              />
            </div>
          </div>

          <!-- Chunks List -->
          <div class="flex-1 overflow-y-auto p-2 space-y-2">
            <div
              v-for="chunk in filteredChunks"
              :key="chunk.chunk_id"
              :class="[
                'p-3 rounded-lg cursor-pointer group transition-all',
                chunk.chunk_id === currentlyPlayingChunk
                  ? 'bg-blue-50 border border-blue-200'
                  : 'hover:bg-slate-50 border border-transparent hover:border-slate-200'
              ]"
              @click="playChunk(chunk.chunk_id)"
            >
              <div class="flex justify-between items-start mb-1">
                <span
                  :class="[
                    'text-xs font-semibold px-1.5 py-0.5 rounded font-mono',
                    chunk.chunk_id === currentlyPlayingChunk
                      ? 'text-primary bg-white border border-blue-100'
                      : 'text-slate-500 bg-slate-100 group-hover:text-slate-700'
                  ]"
                >
                  {{ formatTimeRange(chunk.start_time, chunk.end_time) }}
                </span>

                <span
                  v-if="chunk.chunk_id === currentlyPlayingChunk"
                  class="text-[10px] text-blue-600 font-medium flex items-center gap-1"
                >
                  <span class="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></span>
                  Playing
                </span>

                <div
                  v-else
                  class="opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <button class="text-slate-400 hover:text-primary">
                    <span class="material-symbols-outlined text-[16px]">play_circle</span>
                  </button>
                </div>
              </div>

              <p
                :class="[
                  'text-xs leading-snug',
                  chunk.chunk_id === currentlyPlayingChunk
                    ? 'text-slate-700 font-medium'
                    : 'text-slate-600'
                ]"
              >
                {{ chunk.visual_description || chunk.audio_transcript || 'No description available' }}
              </p>
            </div>

            <!-- Empty State -->
            <div
              v-if="filteredChunks.length === 0"
              class="flex flex-col items-center justify-center py-16 text-center"
            >
              <span class="material-symbols-outlined text-4xl text-slate-300 mb-3">search_off</span>
              <p class="text-sm text-slate-500">No chunks match your filter</p>
            </div>
          </div>

          <!-- Footer -->
          <div class="p-3 border-t border-slate-200 text-center">
            <span class="text-[10px] text-slate-400">
              Showing {{ filteredChunks.length }} of {{ playerStore.chunks.length }} chunks
            </span>
          </div>
        </div>
      </main>
    </div>
  </Transition>
</template>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
