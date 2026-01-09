<template>
  <BaseCard variant="bordered" padding="md">
    <div class="flex items-start gap-3">
      <div class="shrink-0 w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
        <span class="material-symbols-outlined text-primary text-xl">
          storage
        </span>
      </div>

      <div class="flex-1 min-w-0">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-medium text-slate-900">
            Video Storage
          </span>
          <span class="text-sm font-semibold text-slate-900">
            {{ formattedUsed }} / {{ formattedTotal }}
          </span>
        </div>

        <BaseProgress
          :percentage="usagePercentage"
          :variant="progressVariant"
          size="md"
          class="mb-2"
        />

        <div class="flex items-center justify-between text-xs text-slate-500">
          <span>{{ totalVideos }} {{ totalVideos === 1 ? 'video' : 'videos' }}</span>
          <span>{{ usagePercentage.toFixed(1) }}% used</span>
        </div>
      </div>
    </div>
  </BaseCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseProgress from '@/components/ui/BaseProgress.vue'
import { formatFileSize } from '@/types/video'

interface Props {
  totalVideos: number
  usedStorage: number // in MB
  totalStorage?: number // in MB
}

const props = withDefaults(defineProps<Props>(), {
  totalStorage: 10240 // Default 10GB
})

const usagePercentage = computed(() => {
  return (props.usedStorage / props.totalStorage) * 100
})

const progressVariant = computed(() => {
  if (usagePercentage.value >= 90) return 'error'
  if (usagePercentage.value >= 75) return 'warning'
  return 'primary'
})

const formattedUsed = computed(() => formatFileSize(props.usedStorage))
const formattedTotal = computed(() => formatFileSize(props.totalStorage))
</script>
