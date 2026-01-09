<template>
  <div v-if="clips.length > 0" class="border-b border-slate-200 bg-slate-50 p-4">
    <div class="flex items-center gap-3 mb-3">
      <span class="material-symbols-outlined text-slate-500">
        video_library
      </span>
      <span class="text-sm font-semibold text-slate-900">
        Active Clips ({{ clips.length }})
      </span>
      <BaseButton
        variant="ghost"
        size="sm"
        icon="clear_all"
        @click="emit('clear-all')"
        class="ml-auto"
      >
        Clear All
      </BaseButton>
    </div>

    <div class="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1">
      <ClipCard
        v-for="clip in clips"
        :key="clip.clip_id"
        :clip="clip"
        @play="emit('play-clip', clip.clip_id)"
        @remove="emit('remove-clip', clip.clip_id)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import BaseButton from '@/components/ui/BaseButton.vue'
import ClipCard from './ClipCard.vue'
import type { ActiveClip } from '@/types/chat'

interface Props {
  clips: ActiveClip[]
}

defineProps<Props>()
const emit = defineEmits<{
  'play-clip': [clipId: string]
  'remove-clip': [clipId: string]
  'clear-all': []
}>()
</script>
