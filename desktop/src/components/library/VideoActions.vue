<template>
  <div class="flex items-center gap-2">
    <BaseButton
      v-if="showViewChunks"
      variant="ghost"
      size="sm"
      icon="split_scene"
      @click="emit('view-chunks')"
    >
      Chunks
    </BaseButton>

    <BaseButton
      v-if="showViewDetails"
      variant="ghost"
      size="sm"
      icon="info"
      @click="emit('view-details')"
    >
      Details
    </BaseButton>

    <BaseButton
      variant="ghost"
      size="sm"
      icon="delete"
      @click="emit('delete')"
      class="text-error hover:text-error hover:bg-error/10"
    >
      Delete
    </BaseButton>
  </div>
</template>

<script setup lang="ts">
import BaseButton from '@/components/ui/BaseButton.vue'
import type { ProcessingStatus } from '@/types/video'

interface Props {
  status: ProcessingStatus
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'view-chunks': []
  'view-details': []
  'delete': []
}>()

const showViewChunks = props.status === 'indexed' || props.status === 'ready'
const showViewDetails = true
</script>
