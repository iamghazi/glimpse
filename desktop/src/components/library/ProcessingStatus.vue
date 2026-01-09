<template>
  <div class="flex items-center gap-2">
    <BaseBadge :variant="statusVariant" :icon="statusIcon" size="sm">
      {{ statusLabel }}
    </BaseBadge>

    <BaseProgress
      v-if="status === 'processing' && progress !== undefined"
      :percentage="progress"
      variant="primary"
      size="sm"
      class="flex-1"
      animated
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import BaseBadge from '@/components/ui/BaseBadge.vue'
import BaseProgress from '@/components/ui/BaseProgress.vue'
import type { ProcessingStatus as Status } from '@/types/video'

interface Props {
  status: Status
  progress?: number
}

const props = defineProps<Props>()

const statusVariant = computed(() => {
  const variants: Record<Status, 'default' | 'success' | 'error' | 'warning' | 'info'> = {
    uploading: 'info',
    processing: 'warning',
    indexed: 'success',
    failed: 'error',
    ready: 'success'
  }
  return variants[props.status]
})

const statusIcon = computed(() => {
  const icons: Record<Status, string> = {
    uploading: 'upload',
    processing: 'sync',
    indexed: 'check_circle',
    failed: 'error',
    ready: 'check_circle'
  }
  return icons[props.status]
})

const statusLabel = computed(() => {
  const labels: Record<Status, string> = {
    uploading: 'Uploading',
    processing: 'Processing',
    indexed: 'Indexed',
    failed: 'Failed',
    ready: 'Ready'
  }
  return labels[props.status]
})
</script>
