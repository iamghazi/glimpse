<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'

interface TimeSegment {
  start: number
  end: number
}

interface Props {
  src: string
  startTime?: number
  highlightSegments?: TimeSegment[]
  autoplay?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  startTime: 0,
  highlightSegments: () => [],
  autoplay: false
})

const emit = defineEmits<{
  play: []
  pause: []
  ended: []
  timeUpdate: [currentTime: number]
  error: [error: Error]
  ready: []
}>()

const videoRef = ref<HTMLVideoElement | null>(null)
const containerRef = ref<HTMLDivElement | null>(null)
const progressBarRef = ref<HTMLDivElement | null>(null)

const isReady = ref(false)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(1)
const isMuted = ref(false)
const isFullscreen = ref(false)
const showControls = ref(true)
const isDraggingProgress = ref(false)

let hideControlsTimeout: ReturnType<typeof setTimeout> | null = null

// Computed
const progress = computed(() => {
  if (duration.value === 0) return 0
  return (currentTime.value / duration.value) * 100
})

const formattedCurrentTime = computed(() => formatTime(currentTime.value))
const formattedDuration = computed(() => formatTime(duration.value))

const volumeIcon = computed(() => {
  if (isMuted.value || volume.value === 0) return 'volume_off'
  if (volume.value < 0.5) return 'volume_down'
  return 'volume_up'
})

// Methods
function formatTime(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

function togglePlay() {
  if (!videoRef.value) return

  if (isPlaying.value) {
    videoRef.value.pause()
  } else {
    videoRef.value.play()
  }
}

function seekTo(time: number) {
  if (!videoRef.value) return
  videoRef.value.currentTime = time
  currentTime.value = time
}

function play() {
  videoRef.value?.play()
}

function pause() {
  videoRef.value?.pause()
}

function toggleMute() {
  if (!videoRef.value) return
  isMuted.value = !isMuted.value
  videoRef.value.muted = isMuted.value
}

function changeVolume(newVolume: number) {
  if (!videoRef.value) return
  volume.value = Math.max(0, Math.min(1, newVolume))
  videoRef.value.volume = volume.value
  if (volume.value > 0) {
    isMuted.value = false
    videoRef.value.muted = false
  }
}

function toggleFullscreen() {
  if (!containerRef.value) return

  if (!isFullscreen.value) {
    if (containerRef.value.requestFullscreen) {
      containerRef.value.requestFullscreen()
    }
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen()
    }
  }
}

function handleProgressClick(event: MouseEvent) {
  if (!progressBarRef.value || !videoRef.value) return

  const rect = progressBarRef.value.getBoundingClientRect()
  const clickX = event.clientX - rect.left
  const percentage = clickX / rect.width
  const newTime = percentage * duration.value

  seekTo(newTime)
}

function handleProgressDragStart(event: MouseEvent) {
  isDraggingProgress.value = true
  handleProgressDrag(event)
}

function handleProgressDrag(event: MouseEvent) {
  if (!isDraggingProgress.value || !progressBarRef.value) return

  const rect = progressBarRef.value.getBoundingClientRect()
  const clickX = Math.max(0, Math.min(event.clientX - rect.left, rect.width))
  const percentage = clickX / rect.width
  const newTime = percentage * duration.value

  seekTo(newTime)
}

function handleProgressDragEnd() {
  isDraggingProgress.value = false
}

function handleMouseMove() {
  showControls.value = true
  resetHideControlsTimeout()
}

function handleMouseLeave() {
  if (isPlaying.value) {
    showControls.value = false
  }
}

function resetHideControlsTimeout() {
  if (hideControlsTimeout) {
    clearTimeout(hideControlsTimeout)
  }

  if (isPlaying.value) {
    hideControlsTimeout = setTimeout(() => {
      if (isPlaying.value && !isDraggingProgress.value) {
        showControls.value = false
      }
    }, 3000)
  }
}

// Video event handlers
function onLoadedMetadata() {
  if (!videoRef.value) return
  duration.value = videoRef.value.duration
  isReady.value = true
  emit('ready')

  // Seek to start time if specified
  if (props.startTime > 0) {
    nextTick(() => {
      seekTo(props.startTime)
    })
  }

  // Autoplay if specified
  if (props.autoplay) {
    nextTick(() => {
      play()
    })
  }
}

function onPlay() {
  isPlaying.value = true
  emit('play')
  resetHideControlsTimeout()
}

function onPause() {
  isPlaying.value = false
  emit('pause')
  showControls.value = true
  if (hideControlsTimeout) {
    clearTimeout(hideControlsTimeout)
  }
}

function onEnded() {
  isPlaying.value = false
  emit('ended')
  showControls.value = true
}

function onTimeUpdate() {
  if (!videoRef.value) return
  currentTime.value = videoRef.value.currentTime
  emit('timeUpdate', currentTime.value)
}

function onError(event: Event) {
  const error = new Error('Video playback error')
  emit('error', error)
  console.error('Video playback error:', event)
}

function onFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}

// Lifecycle
onMounted(() => {
  document.addEventListener('fullscreenchange', onFullscreenChange)
  document.addEventListener('mousemove', handleProgressDrag)
  document.addEventListener('mouseup', handleProgressDragEnd)
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', onFullscreenChange)
  document.removeEventListener('mousemove', handleProgressDrag)
  document.removeEventListener('mouseup', handleProgressDragEnd)
  if (hideControlsTimeout) {
    clearTimeout(hideControlsTimeout)
  }
})

// Watch for src changes
watch(
  () => props.src,
  (newSrc) => {
    console.log('🎥 Video source changed:', newSrc)
    isReady.value = false
    isPlaying.value = false
    currentTime.value = 0
    duration.value = 0
  },
  { immediate: true }
)

// Expose methods to parent components
defineExpose({
  seekTo,
  play,
  pause,
  getPlayer: () => videoRef.value
})
</script>

<template>
  <div
    ref="containerRef"
    class="video-player-container relative w-full h-full bg-black rounded-xl overflow-hidden group"
    @mousemove="handleMouseMove"
    @mouseleave="handleMouseLeave"
  >
    <!-- Video Element -->
    <video
      ref="videoRef"
      :src="src"
      class="w-full h-full object-contain"
      @loadedmetadata="onLoadedMetadata"
      @play="onPlay"
      @pause="onPause"
      @ended="onEnded"
      @timeupdate="onTimeUpdate"
      @error="onError"
    ></video>

    <!-- Gradient Background (shown before playing) -->
    <div
      v-if="!isPlaying && currentTime === 0"
      class="absolute inset-0 bg-gradient-to-br from-indigo-900 to-slate-900 flex items-center justify-center"
    >
      <button
        class="w-20 h-20 rounded-full bg-white/10 hover:bg-white/20 backdrop-blur-md flex items-center justify-center text-white transition-all scale-100 hover:scale-110"
        @click="togglePlay"
      >
        <span class="material-symbols-outlined text-5xl ml-2">play_arrow</span>
      </button>
    </div>

    <!-- Custom Controls Overlay -->
    <div
      :class="[
        'absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/60 to-transparent pt-12 pb-4 px-6 transition-opacity duration-300',
        showControls || !isPlaying ? 'opacity-100' : 'opacity-0'
      ]"
    >
      <!-- Progress Bar -->
      <div
        ref="progressBarRef"
        class="w-full h-1 bg-white/20 rounded-full mb-4 cursor-pointer hover:h-1.5 transition-all relative group/progress"
        @click="handleProgressClick"
        @mousedown="handleProgressDragStart"
      >
        <!-- Progress Fill -->
        <div
          class="absolute left-0 top-0 h-full bg-primary rounded-full"
          :style="{ width: `${progress}%` }"
        ></div>

        <!-- Progress Scrubber -->
        <div
          class="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-lg scale-0 group-hover/progress:scale-100 transition-transform"
          :style="{ left: `${progress}%`, transform: `translate(-50%, -50%)` }"
        ></div>

        <!-- Highlight Segments -->
        <div
          v-for="(segment, index) in highlightSegments"
          :key="index"
          class="absolute top-0 h-full bg-yellow-400/30 rounded-full"
          :style="{
            left: `${(segment.start / duration) * 100}%`,
            width: `${((segment.end - segment.start) / duration) * 100}%`
          }"
        ></div>
      </div>

      <!-- Controls -->
      <div class="flex items-center justify-between text-white">
        <!-- Left Controls -->
        <div class="flex items-center gap-4">
          <button
            class="hover:text-primary transition-colors"
            @click="togglePlay"
          >
            <span class="material-symbols-outlined">
              {{ isPlaying ? 'pause' : 'play_arrow' }}
            </span>
          </button>

          <button
            class="hover:text-primary transition-colors"
            @click="toggleMute"
          >
            <span class="material-symbols-outlined">{{ volumeIcon }}</span>
          </button>

          <span class="text-xs font-medium font-mono">
            {{ formattedCurrentTime }} / {{ formattedDuration }}
          </span>
        </div>

        <!-- Right Controls -->
        <div class="flex items-center gap-4">
          <button class="hover:text-primary transition-colors">
            <span class="material-symbols-outlined">closed_caption</span>
          </button>

          <button class="hover:text-primary transition-colors">
            <span class="material-symbols-outlined">settings</span>
          </button>

          <button
            class="hover:text-primary transition-colors"
            @click="toggleFullscreen"
          >
            <span class="material-symbols-outlined">
              {{ isFullscreen ? 'fullscreen_exit' : 'fullscreen' }}
            </span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.video-player-container {
  user-select: none;
}

video {
  display: block;
}
</style>
