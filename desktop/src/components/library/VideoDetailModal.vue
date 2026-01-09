<template>
  <Teleport to="body">
    <div
      v-if="show && video"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto"
      @click.self="emit('close')"
    >
      <BaseCard variant="elevated" padding="none" class="max-w-3xl w-full my-8">
        <!-- Header -->
        <div class="p-6 border-b border-slate-200 flex items-start justify-between">
          <div class="flex-1 min-w-0">
            <h2 class="text-xl font-semibold text-slate-900 mb-2">
              {{ video.title }}
            </h2>
            <ProcessingStatus :status="video.status" />
          </div>
          <BaseButton
            variant="ghost"
            size="sm"
            icon="close"
            @click="emit('close')"
          />
        </div>

        <!-- Content -->
        <div class="p-6 space-y-6">
          <!-- Video Info -->
          <div class="grid grid-cols-2 gap-4">
            <InfoItem label="Original Filename" :value="video.original_filename" />
            <InfoItem label="Duration" :value="formatDuration(video.duration_seconds)" />
            <InfoItem label="Resolution" :value="`${video.resolution[0]}×${video.resolution[1]}`" />
            <InfoItem label="Frame Rate" :value="`${video.fps} fps`" />
            <InfoItem label="File Size" :value="formatFileSize(video.file_size_mb)" />
            <InfoItem label="Upload Date" :value="formatUploadDate(video.uploaded_at)" />
            <InfoItem
              label="Indexed Date"
              :value="video.indexed_at ? formatUploadDate(video.indexed_at) : 'Not indexed'"
            />
            <InfoItem label="Video ID" :value="video.video_id" monospace />
          </div>

          <!-- File Path -->
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">
              File Path
            </label>
            <code class="block px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700 break-all">
              {{ video.file_path }}
            </code>
          </div>

          <!-- Chunks Info -->
          <div v-if="video.chunkCount">
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-slate-700">
                Video Chunks
              </label>
              <BaseBadge variant="primary">
                {{ video.chunkCount }} chunks
              </BaseBadge>
            </div>
            <p class="text-sm text-slate-500">
              This video has been split into {{ video.chunkCount }} searchable chunks for semantic search.
            </p>
          </div>

          <!-- Error Message -->
          <div v-if="video.error" class="p-4 bg-error/5 border border-error/20 rounded-lg">
            <div class="flex items-start gap-3">
              <span class="material-symbols-outlined text-error">
                error
              </span>
              <div>
                <p class="text-sm font-medium text-error mb-1">Processing Error</p>
                <p class="text-sm text-slate-600">{{ video.error }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="border-t border-slate-200 p-4 flex justify-end gap-3">
          <BaseButton
            v-if="video.status === 'indexed' || video.status === 'ready'"
            variant="ghost"
            icon="split_scene"
            @click="emit('view-chunks')"
          >
            View Chunks
          </BaseButton>
          <BaseButton
            variant="ghost"
            @click="emit('close')"
          >
            Close
          </BaseButton>
        </div>
      </BaseCard>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseBadge from '@/components/ui/BaseBadge.vue'
import ProcessingStatus from './ProcessingStatus.vue'
import type { VideoWithState } from '@/types/video'
import { formatDuration, formatFileSize, formatUploadDate } from '@/types/video'

interface Props {
  show: boolean
  video: VideoWithState | null
}

defineProps<Props>()
const emit = defineEmits<{
  'close': []
  'view-chunks': []
}>()
</script>

<script lang="ts">
// Helper component for displaying info items
import { defineComponent, h } from 'vue'

const InfoItem = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: String, required: true },
    monospace: { type: Boolean, default: false }
  },
  setup(props) {
    return () => h('div', [
      h('label', { class: 'block text-xs font-medium text-slate-500 mb-1' }, props.label),
      h('p', {
        class: [
          'text-sm text-slate-900',
          props.monospace && 'font-mono text-xs truncate'
        ]
      }, props.value)
    ])
  }
})

export { InfoItem }
</script>
