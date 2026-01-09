<template>
  <div :class="gridClasses">
    <VideoCard
      v-for="video in videos"
      :key="video.video_id"
      :video="video"
      @click="emit('video-click', video.video_id)"
      @view-chunks="emit('view-chunks', $event)"
      @view-details="emit('view-details', $event)"
      @delete="emit('delete', $event)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VideoCard from './VideoCard.vue'
import type { VideoWithState } from '@/types/video'

type Columns = 1 | 2 | 3 | 4 | 5

interface Props {
  videos: VideoWithState[]
  columns?: Columns
}

const props = withDefaults(defineProps<Props>(), {
  columns: 3
})

const emit = defineEmits<{
  'video-click': [videoId: string]
  'view-chunks': [videoId: string]
  'view-details': [videoId: string]
  'delete': [videoId: string]
}>()

const gridClasses = computed(() => {
  const columnClasses: Record<Columns, string> = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 lg:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4',
    5: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5'
  }

  return ['grid gap-4', columnClasses[props.columns]]
})
</script>
