<template>
  <BaseCard variant="bordered" padding="md">
    <div class="flex items-start gap-3">
      <span class="material-symbols-outlined text-primary text-2xl">
        upload_file
      </span>

      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium text-slate-900 truncate mb-1">
          {{ fileName }}
        </p>

        <BaseProgress
          :percentage="progress"
          variant="primary"
          size="md"
          :show-percentage="true"
          :animated="progress < 100"
          class="mb-1"
        />

        <p class="text-xs text-slate-500">
          {{ statusText }}
        </p>
      </div>

      <BaseButton
        v-if="progress < 100"
        variant="ghost"
        size="sm"
        icon="close"
        @click="emit('cancel')"
        class="shrink-0"
      />
    </div>
  </BaseCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseProgress from '@/components/ui/BaseProgress.vue'
import BaseButton from '@/components/ui/BaseButton.vue'

interface Props {
  fileName: string
  progress: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'cancel': []
}>()

const statusText = computed(() => {
  if (props.progress >= 100) {
    return 'Upload complete - Processing video...'
  }
  return `Uploading... ${Math.round(props.progress)}%`
})
</script>
