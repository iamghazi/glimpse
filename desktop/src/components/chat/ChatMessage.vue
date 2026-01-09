<template>
  <div :class="messageClasses">
    <div :class="bubbleClasses">
      <!-- Avatar for assistant -->
      <div v-if="message.role === 'assistant'" class="shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
        <span class="material-symbols-outlined text-primary text-lg">
          smart_toy
        </span>
      </div>

      <!-- Message content -->
      <div class="flex-1 min-w-0">
        <div :class="contentClasses">
          <p class="text-sm whitespace-pre-wrap break-words">
            {{ message.content }}
          </p>
        </div>

        <!-- Timestamp -->
        <div class="flex items-center gap-2 mt-1 px-1">
          <span class="text-xs text-slate-400">
            {{ formattedTime }}
          </span>
          <MessageActions
            :role="message.role"
            @regenerate="emit('regenerate')"
            @copy="handleCopy"
          />
        </div>
      </div>

      <!-- Avatar for user -->
      <div v-if="message.role === 'user'" class="shrink-0 w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center">
        <span class="material-symbols-outlined text-slate-600 text-lg">
          person
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MessageActions from './MessageActions.vue'
import type { ChatMessage } from '@/types/chat'
import { formatMessageTime } from '@/types/chat'

interface Props {
  message: ChatMessage
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'regenerate': []
}>()

const messageClasses = computed(() => [
  'group',
  props.message.role === 'user' ? 'flex justify-end' : 'flex justify-start'
])

const bubbleClasses = computed(() => [
  'flex gap-3 max-w-[80%]',
  props.message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
])

const contentClasses = computed(() => [
  'px-4 py-3 rounded-2xl',
  props.message.role === 'user'
    ? 'bg-primary text-white'
    : 'bg-slate-100 text-slate-900'
])

const formattedTime = computed(() => formatMessageTime(props.message.timestamp))

function handleCopy() {
  navigator.clipboard.writeText(props.message.content)
}
</script>
