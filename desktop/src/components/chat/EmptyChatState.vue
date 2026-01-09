<template>
  <div class="flex flex-col items-center justify-center py-16 px-4 text-center">
    <span class="material-symbols-outlined text-6xl text-slate-300 mb-4">
      {{ icon }}
    </span>

    <h3 class="text-lg font-semibold text-slate-900 mb-2">
      {{ title }}
    </h3>

    <p class="text-sm text-slate-500 max-w-md mb-6">
      {{ description }}
    </p>

    <slot name="action" />
  </div>
</template>

<script setup lang="ts">
interface Props {
  hasClips: boolean
}

const props = defineProps<Props>()

const icon = props.hasClips ? 'chat' : 'video_library'
const title = props.hasClips ? 'Start a conversation' : 'No clips selected'
const description = props.hasClips
  ? 'Ask questions about the selected video clips to get AI-powered insights.'
  : 'Add clips from the Search screen to start chatting about your videos.'
</script>
