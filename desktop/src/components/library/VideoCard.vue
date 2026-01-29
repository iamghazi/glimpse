<template>
  <div
    class="group bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer overflow-hidden flex flex-col"
    @click="emit('click')"
  >
    <!-- Thumbnail with Gradient & Hover Overlay -->
    <div class="relative aspect-video bg-slate-100 overflow-hidden">
      <!-- Gradient Thumbnail (fallback if no actual thumbnail) -->
      <div
        v-if="!thumbnailUrl"
        :class="[
          'w-full h-full opacity-90 group-hover:scale-105 transition-transform duration-500',
          gradientClass
        ]"
      ></div>

      <!-- Actual Thumbnail (if available) -->
      <img
        v-else
        :src="thumbnailUrl"
        :alt="video.title"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
      />

      <!-- Duration Badge -->
      <div class="absolute bottom-2 right-2 bg-black/70 backdrop-blur-sm text-white text-xs font-medium px-1.5 py-0.5 rounded">
        {{ formattedDuration }}
      </div>

      <!-- Hover Overlay with Play Button -->
      <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
        <button
          class="w-10 h-10 rounded-full bg-white/20 hover:bg-white backdrop-blur-sm flex items-center justify-center text-white hover:text-primary transition-colors"
          @click.stop="emit('click')"
        >
          <span class="material-symbols-outlined text-[24px] ml-0.5">play_arrow</span>
        </button>
      </div>

      <!-- Processing overlay -->
      <div
        v-if="video.status === 'uploading' || video.status === 'processing'"
        class="absolute inset-0 bg-black/50 flex items-center justify-center"
      >
        <span class="material-symbols-outlined text-white text-4xl animate-spin">
          sync
        </span>
      </div>
    </div>

    <!-- Card Content -->
    <div class="p-4 flex flex-col flex-1">
      <div class="flex justify-between items-start mb-2">
        <h3 class="text-sm font-bold text-slate-900 line-clamp-2 leading-tight group-hover:text-primary transition-colors">
          {{ video.title }}
        </h3>
        <button
          class="text-slate-400 hover:text-slate-600"
          @click.stop="showMenu = !showMenu"
        >
          <span class="material-symbols-outlined text-[18px]">more_vert</span>
        </button>
      </div>

      <div class="mt-auto space-y-2">
        <!-- Date -->
        <div class="flex items-center gap-2 text-xs text-slate-500">
          <span class="material-symbols-outlined text-[14px]">calendar_today</span>
          <span>{{ formattedDate }}</span>
        </div>

        <!-- Status & Chunks -->
        <div class="flex items-center justify-between pt-2 border-t border-slate-100">
          <div class="flex items-center gap-1.5">
            <div
              :class="[
                'w-2 h-2 rounded-full',
                statusColor
              ]"
            ></div>
            <span class="text-xs font-medium text-slate-600">{{ statusLabel }}</span>
          </div>
          <span
            v-if="video.chunkCount"
            class="text-[10px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded"
          >
            {{ video.chunkCount }} Chunks
          </span>
          <span
            v-else-if="video.status === 'failed'"
            class="text-[10px] text-red-500 bg-red-50 px-1.5 py-0.5 rounded font-medium cursor-pointer hover:bg-red-100"
            @click.stop="emit('retry', video.video_id)"
          >
            Retry
          </span>
        </div>
      </div>
    </div>

    <!-- Context Menu (shown on more_vert click) -->
    <div
      v-if="showMenu"
      class="absolute top-12 right-4 bg-white border border-slate-200 rounded-lg shadow-lg py-1 z-20"
      @click.stop
    >
      <button
        class="w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-50 flex items-center gap-2"
        @click="handleViewChunks"
      >
        <span class="material-symbols-outlined text-[18px]">segment</span>
        View Chunks
      </button>
      <button
        class="w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-50 flex items-center gap-2"
        @click="handleViewDetails"
      >
        <span class="material-symbols-outlined text-[18px]">info</span>
        View Details
      </button>
      <div class="border-t border-slate-100 my-1"></div>
      <button
        class="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
        @click="handleDelete"
      >
        <span class="material-symbols-outlined text-[18px]">delete</span>
        Delete Video
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { VideoWithState } from '@/types/video'
import { formatDuration, formatUploadDate, getThumbnailUrl } from '@/types/video'

interface Props {
  video: VideoWithState
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'click': []
  'view-chunks': [videoId: string]
  'view-details': [videoId: string]
  'delete': [videoId: string]
  'retry': [videoId: string]
}>()

const showMenu = ref(false)

// Gradient classes for thumbnails (cycling through different gradients)
const gradientClasses = [
  'bg-gradient-to-br from-indigo-500 to-purple-600',
  'bg-gradient-to-tr from-emerald-500 to-teal-700',
  'bg-gradient-to-bl from-orange-400 to-rose-500',
  'bg-gradient-to-r from-blue-600 to-cyan-500',
  'bg-gradient-to-br from-slate-600 to-slate-800',
  'bg-gradient-to-tr from-pink-500 to-rose-600',
  'bg-gradient-to-bl from-violet-500 to-purple-700',
  'bg-gradient-to-r from-amber-500 to-orange-600'
]

const gradientClass = computed(() => {
  // Use video_id to determine gradient (consistent per video)
  const index = props.video.video_id.charCodeAt(props.video.video_id.length - 1) % gradientClasses.length
  return gradientClasses[index]
})

const formattedDuration = computed(() => formatDuration(props.video.duration_seconds))
const formattedDate = computed(() => formatUploadDate(props.video.uploaded_at))

// Generate thumbnail URL from representative_frame
const thumbnailUrl = computed(() => {
  return getThumbnailUrl(props.video.representative_frame)
})

const statusColor = computed(() => {
  switch (props.video.status) {
    case 'indexed':
      return 'bg-green-500'
    case 'processing':
      return 'bg-yellow-500'
    case 'uploading':
      return 'bg-blue-500'
    case 'failed':
      return 'bg-red-500'
    default:
      return 'bg-slate-400'
  }
})

const statusLabel = computed(() => {
  switch (props.video.status) {
    case 'indexed':
      return 'Indexed'
    case 'processing':
      return 'Processing'
    case 'uploading':
      return 'Uploading'
    case 'failed':
      return 'Failed'
    default:
      return 'Unknown'
  }
})

function handleViewChunks() {
  showMenu.value = false
  emit('view-chunks', props.video.video_id)
}

function handleViewDetails() {
  showMenu.value = false
  emit('view-details', props.video.video_id)
}

function handleDelete() {
  showMenu.value = false
  emit('delete', props.video.video_id)
}
</script>
