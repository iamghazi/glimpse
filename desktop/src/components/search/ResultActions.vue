<template>
  <div class="flex items-center gap-2">
    <BaseButton
      variant="primary"
      size="sm"
      icon="add_comment"
      @click="emit('add-to-chat')"
    >
      Add to Chat
    </BaseButton>

    <BaseButton
      variant="ghost"
      size="sm"
      icon="play_arrow"
      @click="emit('play-clip')"
    >
      Play Clip
    </BaseButton>
  </div>
</template>

<script setup lang="ts">
import BaseButton from '@/components/ui/BaseButton.vue'

const emit = defineEmits<{
  'add-to-chat': []
  'play-clip': []
}>()
</script>
