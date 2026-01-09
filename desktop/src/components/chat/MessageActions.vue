<template>
  <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
    <BaseButton
      v-if="role === 'assistant'"
      variant="ghost"
      size="sm"
      icon="refresh"
      @click="emit('regenerate')"
      title="Regenerate response"
    />
    <BaseButton
      variant="ghost"
      size="sm"
      icon="content_copy"
      @click="emit('copy')"
      title="Copy message"
    />
  </div>
</template>

<script setup lang="ts">
import BaseButton from '@/components/ui/BaseButton.vue'

interface Props {
  role: 'user' | 'assistant'
}

defineProps<Props>()
const emit = defineEmits<{
  'regenerate': []
  'copy': []
}>()
</script>
