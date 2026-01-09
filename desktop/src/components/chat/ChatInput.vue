<template>
  <div class="border-t border-slate-200 bg-surface p-4">
    <div class="max-w-4xl mx-auto">
      <div class="flex gap-3">
        <div class="flex-1 relative">
          <textarea
            ref="textareaRef"
            v-model="input"
            placeholder="Ask a question about the active clips..."
            rows="1"
            class="w-full px-4 py-3 pr-24 text-sm border-2 border-slate-300 rounded-xl focus:border-primary focus:outline-none resize-none transition-colors"
            :disabled="disabled"
            @keydown="handleKeyDown"
            @input="adjustHeight"
          />
          <div class="absolute right-3 bottom-3 flex items-center gap-2">
            <span class="text-xs text-slate-400">
              Shift+Enter
            </span>
            <BaseButton
              variant="primary"
              size="sm"
              icon="send"
              :loading="loading"
              :disabled="!canSend"
              @click="handleSubmit"
            />
          </div>
        </div>
      </div>

      <p v-if="!hasClips" class="text-xs text-slate-500 mt-2">
        Add clips from the Search screen to start chatting
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import BaseButton from '@/components/ui/BaseButton.vue'

interface Props {
  loading?: boolean
  disabled?: boolean
  hasClips?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  disabled: false,
  hasClips: false
})

const emit = defineEmits<{
  'send': [message: string]
}>()

const textareaRef = ref<HTMLTextAreaElement>()
const input = ref('')

const canSend = computed(() =>
  !props.loading && !props.disabled && input.value.trim() !== '' && props.hasClips
)

function handleKeyDown(event: KeyboardEvent) {
  // Submit on Shift+Enter
  if (event.key === 'Enter' && event.shiftKey) {
    event.preventDefault()
    handleSubmit()
  }
}

function handleSubmit() {
  if (!canSend.value) return

  emit('send', input.value.trim())
  input.value = ''

  nextTick(() => {
    adjustHeight()
  })
}

function adjustHeight() {
  if (!textareaRef.value) return

  textareaRef.value.style.height = 'auto'
  textareaRef.value.style.height = `${textareaRef.value.scrollHeight}px`
}
</script>
