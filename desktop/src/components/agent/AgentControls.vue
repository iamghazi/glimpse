<template>
  <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
    <!-- Header -->
    <div class="px-5 py-4 border-b border-slate-100">
      <h3 class="text-sm font-semibold text-slate-900">Actions</h3>
    </div>

    <div class="p-5 space-y-4">
      <!-- Approve Button (when complete) -->
      <button
        v-if="status === 'complete' && hasPreview"
        class="w-full flex items-center justify-center gap-2 px-4 py-3 bg-green-500 hover:bg-green-600 text-white font-semibold rounded-lg transition-colors shadow-lg shadow-green-500/20"
        :disabled="loading"
        @click="$emit('approve')"
      >
        <span class="material-symbols-outlined">check_circle</span>
        {{ loading ? 'Rendering...' : 'Approve & Export' }}
      </button>

      <!-- Feedback Section (when complete) -->
      <div v-if="status === 'complete'" class="space-y-3">
        <div class="relative">
          <textarea
            v-model="feedbackText"
            class="w-full px-4 py-3 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary text-slate-900 placeholder-slate-400 resize-none"
            placeholder="Not happy? Provide feedback for another iteration..."
            rows="2"
            :disabled="loading"
          ></textarea>
        </div>
        <button
          class="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-lg transition-colors"
          :disabled="loading || !feedbackText.trim()"
          @click="handleFeedback"
        >
          <span class="material-symbols-outlined text-sm">refresh</span>
          Refine with Feedback
        </button>
      </div>

      <!-- Cancel Button (when active) -->
      <button
        v-if="isActive"
        class="w-full flex items-center justify-center gap-2 px-4 py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-600 font-medium rounded-lg transition-colors"
        @click="$emit('cancel')"
      >
        <span class="material-symbols-outlined text-sm">close</span>
        Cancel
      </button>

      <!-- Reset Button (when failed or complete) -->
      <button
        v-if="status === 'failed' || status === 'complete'"
        class="w-full flex items-center justify-center gap-2 px-4 py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-600 font-medium rounded-lg transition-colors"
        @click="$emit('reset')"
      >
        <span class="material-symbols-outlined text-sm">restart_alt</span>
        Start New Edit
      </button>

      <!-- Error Message -->
      <div
        v-if="error"
        class="flex items-start gap-2 p-3 bg-red-50 border border-red-100 rounded-lg"
      >
        <span class="material-symbols-outlined text-red-500 text-sm mt-0.5">error</span>
        <p class="text-xs text-red-700">{{ error }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { AgentStatus } from '@/types/agent'

interface Props {
  status: AgentStatus
  loading?: boolean
  error?: string | null
  hasPreview?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  hasPreview: false
})

const emit = defineEmits<{
  approve: []
  feedback: [feedback: string]
  cancel: []
  reset: []
}>()

const feedbackText = ref('')

const isActive = computed(() =>
  ['planning', 'executing', 'evaluating'].includes(props.status)
)

function handleFeedback() {
  if (feedbackText.value.trim()) {
    emit('feedback', feedbackText.value.trim())
    feedbackText.value = ''
  }
}
</script>
