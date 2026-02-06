<script setup lang="ts">
import { computed } from 'vue'
import type { VideoChunk } from '@/types/video'
import { formatTimeRange, getVideoUrl } from '@/types/video'
import { useChatStore } from '@/stores/chat'
import type { ActiveClip } from '@/types/chat'
import { getThumbnailUrl } from '@/types/video'

interface Props {
  chunk: VideoChunk
  videoTitle: string
  showAddToChat?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showAddToChat: true
})

const chatStore = useChatStore()

// Computed
const thumbnailUrl = computed(() => {
  if (!props.chunk.representative_frame) return ''
  return getVideoUrl(props.chunk.representative_frame)
})

const timeRange = computed(() => {
  return formatTimeRange(props.chunk.start_time, props.chunk.end_time)
})

const isAddedToChat = computed(() => {
  return chatStore.activeClips.some((c) => c.clip_id === props.chunk.chunk_id)
})

// Actions
const addToChat = () => {
  // Convert VideoChunk to ActiveClip format
  const activeClip: ActiveClip = {
    clip_id: props.chunk.chunk_id,
    video_id: props.chunk.video_id,
    title: props.videoTitle,
    start_time: props.chunk.start_time,
    end_time: props.chunk.end_time,
    thumbnail: getThumbnailUrl(props.chunk.representative_frame) || ''
  }

  chatStore.addClip(activeClip)
}
</script>

<template>
  <div class="space-y-4">
    <!-- Thumbnail -->
    <div v-if="thumbnailUrl" class="overflow-hidden rounded-lg border border-slate-200">
      <img
        :src="thumbnailUrl"
        :alt="`Frame from ${timeRange}`"
        class="h-auto w-full object-cover"
      />
    </div>

    <!-- Video Title -->
    <div>
      <h3 class="text-xl font-bold text-slate-900">{{ videoTitle }}</h3>
      <p class="text-sm text-slate-500 mt-1">{{ timeRange }}</p>
    </div>

    <!-- Visual Description -->
    <div class="bg-slate-50 rounded-lg p-4 border border-slate-200">
      <h4 class="mb-2 text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-2">
        <span class="material-symbols-outlined text-[16px]">visibility</span>
        Visual Description
      </h4>
      <p class="text-sm text-slate-600 leading-relaxed">
        {{ chunk.visual_description || 'No description available' }}
      </p>
    </div>

    <!-- Audio Transcript -->
    <div class="bg-slate-50 rounded-lg p-4 border border-slate-200">
      <h4 class="mb-2 text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-2">
        <span class="material-symbols-outlined text-[16px]">mic</span>
        Audio Transcript
      </h4>
      <p class="text-sm text-slate-600 leading-relaxed">
        {{ chunk.audio_transcript || 'No transcript available' }}
      </p>
    </div>

    <!-- Chunk Details -->
    <div class="space-y-2 border-t border-slate-200 pt-4 text-sm text-slate-600">
      <p class="flex justify-between">
        <span class="font-medium text-slate-700">Duration:</span>
        <span>{{ chunk.duration.toFixed(1) }}s</span>
      </p>
      <p class="flex justify-between">
        <span class="font-medium text-slate-700">Chunk ID:</span>
        <span class="font-mono text-xs text-slate-500">{{ chunk.chunk_id.slice(0, 8) }}...</span>
      </p>
      <p v-if="chunk.frame_paths.length > 0" class="flex justify-between">
        <span class="font-medium text-slate-700">Frames:</span>
        <span>{{ chunk.frame_paths.length }}</span>
      </p>
    </div>

    <!-- Add to Chat Button -->
    <button
      v-if="showAddToChat"
      class="w-full rounded-lg px-4 py-2.5 text-sm font-semibold transition-all flex items-center justify-center gap-2"
      :class="
        isAddedToChat
          ? 'bg-green-50 text-green-700 border-2 border-green-200 cursor-default'
          : 'bg-primary text-white hover:bg-blue-600 shadow-lg shadow-blue-500/20 active:scale-95'
      "
      @click="addToChat"
      :disabled="isAddedToChat"
    >
      <span class="material-symbols-outlined text-[20px]">
        {{ isAddedToChat ? 'check_circle' : 'add_circle' }}
      </span>
      {{ isAddedToChat ? 'Added to Chat' : 'Add to Chat' }}
    </button>
  </div>
</template>

<style scoped>
/* Styling handled via Tailwind classes in template */
</style>
