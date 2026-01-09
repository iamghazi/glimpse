<template>
  <BaseCard
    variant="bordered"
    padding="none"
    hover
    clickable
    @click="emit('click')"
  >
    <!-- Thumbnail -->
    <div class="relative aspect-video bg-slate-100 rounded-t-xl overflow-hidden">
      <img
        v-if="video.thumbnailUrl"
        :src="video.thumbnailUrl"
        :alt="video.title"
        class="w-full h-full object-cover"
      />
      <div v-else class="w-full h-full flex items-center justify-center">
        <span class="material-symbols-outlined text-4xl text-slate-300">
          movie
        </span>
      </div>

      <!-- Duration badge -->
      <div class="absolute bottom-2 right-2 px-2 py-1 bg-black/70 text-white text-xs font-medium rounded">
        {{ formattedDuration }}
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

    <!-- Content -->
    <div class="p-4">
      <div class="flex items-start justify-between gap-3 mb-3">
        <div class="flex-1 min-w-0">
          <h3 class="text-sm font-semibold text-slate-900 truncate mb-1">
            {{ video.title }}
          </h3>
          <p class="text-xs text-slate-500">
            {{ formattedDate }}
          </p>
        </div>

        <ProcessingStatus :status="video.status" :progress="video.uploadProgress" />
      </div>

      <!-- Metadata -->
      <div class="flex items-center gap-4 text-xs text-slate-500 mb-3">
        <span class="flex items-center gap-1">
          <span class="material-symbols-outlined text-sm">photo_size_select_large</span>
          {{ video.resolution[0] }}×{{ video.resolution[1] }}
        </span>
        <span class="flex items-center gap-1">
          <span class="material-symbols-outlined text-sm">storage</span>
          {{ formattedSize }}
        </span>
        <span v-if="video.chunkCount" class="flex items-center gap-1">
          <span class="material-symbols-outlined text-sm">split_scene</span>
          {{ video.chunkCount }} chunks
        </span>
      </div>

      <!-- Actions -->
      <VideoActions
        :status="video.status"
        @view-chunks="emit('view-chunks', video.video_id)"
        @view-details="emit('view-details', video.video_id)"
        @delete="emit('delete', video.video_id)"
        @click.stop
      />
    </div>
  </BaseCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import ProcessingStatus from './ProcessingStatus.vue'
import VideoActions from './VideoActions.vue'
import type { VideoWithState } from '@/types/video'
import { formatDuration, formatFileSize, formatUploadDate } from '@/types/video'

interface Props {
  video: VideoWithState
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'click': []
  'view-chunks': [videoId: string]
  'view-details': [videoId: string]
  'delete': [videoId: string]
}>()

const formattedDuration = computed(() => formatDuration(props.video.duration_seconds))
const formattedSize = computed(() => formatFileSize(props.video.file_size_mb))
const formattedDate = computed(() => formatUploadDate(props.video.uploaded_at))
</script>
