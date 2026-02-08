<template>
  <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
    <!-- Header -->
    <div class="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="material-symbols-outlined text-slate-400">smart_display</span>
        <h3 class="text-sm font-semibold text-slate-900">Preview</h3>
      </div>
      <span
        v-if="hasPreview"
        class="text-xs font-medium text-green-600 bg-green-50 px-2 py-0.5 rounded-full"
      >
        480p Preview
      </span>
    </div>

    <!-- Video Container -->
    <div class="aspect-video bg-slate-900 relative">
      <!-- Video Player -->
      <video
        v-if="previewUrl"
        ref="videoRef"
        class="w-full h-full object-contain"
        :src="previewUrl"
        controls
        @play="isPlaying = true"
        @pause="isPlaying = false"
        @ended="isPlaying = false"
      ></video>

      <!-- Empty State -->
      <div
        v-else
        class="absolute inset-0 flex flex-col items-center justify-center text-slate-400"
      >
        <span class="material-symbols-outlined text-5xl mb-2">movie</span>
        <p class="text-sm font-medium">No preview available</p>
        <p class="text-xs text-slate-500 mt-1">Preview will appear after rendering</p>
      </div>

      <!-- Loading Overlay -->
      <div
        v-if="loading"
        class="absolute inset-0 bg-black/60 flex flex-col items-center justify-center"
      >
        <div class="w-10 h-10 border-3 border-white/20 border-t-white rounded-full animate-spin mb-3"></div>
        <p class="text-white text-sm font-medium">Rendering preview...</p>
      </div>
    </div>

    <!-- Controls -->
    <div v-if="hasPreview" class="px-5 py-3 bg-slate-50/50 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <button
          class="p-1.5 hover:bg-slate-200 rounded-lg transition-colors"
          @click="togglePlay"
        >
          <span class="material-symbols-outlined text-slate-600">
            {{ isPlaying ? 'pause' : 'play_arrow' }}
          </span>
        </button>
        <button
          class="p-1.5 hover:bg-slate-200 rounded-lg transition-colors"
          @click="restart"
        >
          <span class="material-symbols-outlined text-slate-600">replay</span>
        </button>
      </div>
      <button
        class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-200 rounded-lg transition-colors"
        @click="openFullscreen"
      >
        <span class="material-symbols-outlined text-sm">fullscreen</span>
        Fullscreen
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  previewUrl?: string | null
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const videoRef = ref<HTMLVideoElement | null>(null)
const isPlaying = ref(false)

const hasPreview = computed(() => !!props.previewUrl)

function togglePlay() {
  if (!videoRef.value) return

  if (isPlaying.value) {
    videoRef.value.pause()
  } else {
    videoRef.value.play()
  }
}

function restart() {
  if (!videoRef.value) return
  videoRef.value.currentTime = 0
  videoRef.value.play()
}

function openFullscreen() {
  if (!videoRef.value) return
  videoRef.value.requestFullscreen()
}
</script>
