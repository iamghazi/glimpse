<template>
  <BaseCard
    variant="bordered"
    padding="none"
    hover
    clickable
    @click="emit('click')"
  >
    <div class="p-5">
      <!-- Metadata -->
      <ResultMetadata
        :score="result.score"
        :start-time="result.start_time"
        :end-time="result.end_time"
        :video-title="result.title"
        class="mb-4"
      />

      <!-- Frame Gallery -->
      <FrameGallery
        :frames="frameUrls"
        class="mb-4"
      />

      <!-- Content -->
      <div class="space-y-3 mb-4">
        <!-- Visual Description -->
        <div v-if="result.visual_description">
          <div class="flex items-center gap-2 mb-2">
            <span class="material-symbols-outlined text-sm text-slate-500">
              visibility
            </span>
            <span class="text-xs font-medium text-slate-500 uppercase tracking-wide">
              Visual
            </span>
          </div>
          <p class="text-sm text-slate-700 leading-relaxed">
            {{ result.visual_description }}
          </p>
        </div>

        <!-- Audio Transcript -->
        <div v-if="result.audio_transcript">
          <div class="flex items-center gap-2 mb-2">
            <span class="material-symbols-outlined text-sm text-slate-500">
              mic
            </span>
            <span class="text-xs font-medium text-slate-500 uppercase tracking-wide">
              Audio
            </span>
          </div>
          <p class="text-sm text-slate-700 leading-relaxed">
            {{ result.audio_transcript }}
          </p>
        </div>
      </div>

      <!-- Actions -->
      <ResultActions
        @add-to-chat="emit('add-to-chat', result)"
        @play-clip="emit('play-clip', result)"
      />
    </div>
  </BaseCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import ResultMetadata from './ResultMetadata.vue'
import FrameGallery from './FrameGallery.vue'
import ResultActions from './ResultActions.vue'
import type { SearchResult } from '@/types/search'

interface Props {
  result: SearchResult
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'click': []
  'add-to-chat': [result: SearchResult]
  'play-clip': [result: SearchResult]
}>()

// For now, use placeholder frame URLs
// In production, these would come from the backend
const frameUrls = computed(() => {
  // Generate 5 placeholder frames
  // In production: return actual frame URLs from result.representative_frame
  return Array(5).fill(null)
})
</script>
