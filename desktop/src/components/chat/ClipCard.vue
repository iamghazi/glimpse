<template>
  <BaseCard
    variant="bordered"
    padding="none"
    class="w-48 shrink-0 group"
  >
    <!-- Thumbnail -->
    <div class="relative aspect-video bg-slate-100 rounded-t-xl overflow-hidden">
      <img
        v-if="clip.thumbnail"
        :src="clip.thumbnail"
        :alt="clip.title"
        class="w-full h-full object-cover"
      />
      <div v-else class="w-full h-full flex items-center justify-center">
        <span class="material-symbols-outlined text-2xl text-slate-300">
          movie
        </span>
      </div>

      <!-- Duration badge -->
      <div class="absolute bottom-1 right-1 px-1.5 py-0.5 bg-black/70 text-white text-[10px] font-medium rounded">
        {{ formattedTimeRange }}
      </div>

      <!-- Actions overlay -->
      <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
        <ClipActions
          @play="emit('play')"
          @remove="emit('remove')"
        />
      </div>
    </div>

    <!-- Content -->
    <div class="p-2">
      <p class="text-xs font-medium text-slate-900 truncate mb-1">
        {{ clip.title }}
      </p>
      <div v-if="clip.confidence_score !== undefined" class="flex items-center gap-1">
        <span class="material-symbols-outlined text-[10px] text-slate-400">
          star
        </span>
        <span class="text-[10px] text-slate-500">
          {{ (clip.confidence_score * 100).toFixed(0) }}%
        </span>
      </div>
    </div>
  </BaseCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import ClipActions from './ClipActions.vue'
import type { ActiveClip } from '@/types/chat'
import { formatClipTimestamp } from '@/types/chat'

interface Props {
  clip: ActiveClip
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'play': []
  'remove': []
}>()

const formattedTimeRange = computed(() =>
  formatClipTimestamp(props.clip.start_time, props.clip.end_time)
)
</script>
