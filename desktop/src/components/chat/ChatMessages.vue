<template>
  <div ref="messagesContainer" class="flex-1 overflow-y-auto p-6">
    <div class="max-w-4xl mx-auto space-y-4">
      <template v-for="item in items" :key="item.id">
        <!-- Date Separator -->
        <DateSeparator v-if="isDateSeparator(item)" :date="item.date" />

        <!-- Chat Message -->
        <ChatMessage
          v-else
          :message="item"
          @regenerate="emit('regenerate-message', item.id)"
        />
      </template>

      <!-- Thinking Indicator -->
      <ThinkingIndicator v-if="thinking" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import ChatMessage from './ChatMessage.vue'
import DateSeparator from './DateSeparator.vue'
import ThinkingIndicator from './ThinkingIndicator.vue'
import type { MessageOrSeparator } from '@/types/chat'
import { isDateSeparator } from '@/types/chat'

interface Props {
  items: MessageOrSeparator[]
  thinking?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  thinking: false
})

const emit = defineEmits<{
  'regenerate-message': [messageId: string]
}>()

const messagesContainer = ref<HTMLElement>()

// Auto-scroll to bottom when new messages arrive
watch(() => props.items.length, () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
})

// Auto-scroll when thinking state changes
watch(() => props.thinking, () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
})
</script>
