<template>
  <div class="flex items-center gap-4 text-sm">
    <div class="flex items-center gap-2">
      <span class="text-xs font-medium text-slate-500">Score:</span>
      <span class="text-sm font-semibold text-slate-900">
        {{ formatConfidence(score) }}
      </span>
      <ConfidenceBadge :score="score" />
    </div>

    <div class="h-4 w-px bg-slate-200"></div>

    <div class="flex items-center gap-1.5 text-slate-600">
      <span class="material-symbols-outlined text-base">
        schedule
      </span>
      <span>{{ formatTimestampRange(startTime, endTime) }}</span>
    </div>

    <div class="h-4 w-px bg-slate-200"></div>

    <div class="flex items-center gap-1.5 text-slate-600">
      <span class="material-symbols-outlined text-base">
        movie
      </span>
      <span class="truncate">{{ videoTitle }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import ConfidenceBadge from './ConfidenceBadge.vue'
import { formatTimestampRange, formatConfidence } from '@/types/search'

interface Props {
  score: number
  startTime: number
  endTime: number
  videoTitle: string
}

defineProps<Props>()
</script>
