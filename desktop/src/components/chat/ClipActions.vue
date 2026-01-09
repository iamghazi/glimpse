<template>
  <div class="flex items-center gap-1">
    <BaseButton
      variant="ghost"
      size="sm"
      icon="play_arrow"
      @click="emit('play')"
      class="opacity-0 group-hover:opacity-100 transition-opacity"
    />
    <BaseButton
      variant="ghost"
      size="sm"
      icon="close"
      @click="emit('remove')"
      class="opacity-0 group-hover:opacity-100 transition-opacity text-error hover:text-error hover:bg-error/10"
    />
  </div>
</template>

<script setup lang="ts">
import BaseButton from '@/components/ui/BaseButton.vue'

const emit = defineEmits<{
  'play': []
  'remove': []
}>()
</script>
