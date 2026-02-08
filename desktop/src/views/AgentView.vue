<template>
  <div class="flex h-full bg-background">
    <AppSidebar />

    <main class="flex-1 flex flex-col h-full overflow-hidden">
      <!-- Header -->
      <div class="shrink-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-sm z-10">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <span class="material-symbols-outlined text-white">smart_toy</span>
          </div>
          <div>
            <h1 class="text-lg font-bold text-slate-900">AI Video Editor</h1>
            <p class="text-xs text-slate-500">Autonomous video editing agent</p>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <button
            v-if="agentStore.session"
            class="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
            @click="showRequestModal = true"
          >
            <span class="material-symbols-outlined text-[18px]">history</span>
            View Request
          </button>
        </div>
      </div>

      <!-- Main Content -->
      <div class="flex-1 overflow-y-auto">
        <div class="max-w-7xl mx-auto px-8 py-6">
          <!-- Empty State / Input -->
          <div v-if="agentStore.status === 'idle'" class="max-w-2xl mx-auto">
            <div class="bg-white rounded-2xl border border-slate-200 shadow-lg overflow-hidden">
              <!-- Hero Section -->
              <div class="bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 px-8 py-12 text-center text-white">
                <div class="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center mx-auto mb-4">
                  <span class="material-symbols-outlined text-4xl">movie_edit</span>
                </div>
                <h2 class="text-2xl font-bold mb-2">AI Video Editor</h2>
                <p class="text-white/80 max-w-md mx-auto">
                  Describe what you want to create and the AI will search, edit, and assemble clips automatically.
                </p>
              </div>

              <!-- Input Section -->
              <div class="p-8">
                <form @submit.prevent="handleStartEdit">
                  <div class="space-y-4">
                    <div>
                      <label class="block text-sm font-medium text-slate-700 mb-2">
                        What would you like to create?
                      </label>
                      <textarea
                        v-model="editRequest"
                        class="w-full px-4 py-3 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary text-slate-900 placeholder-slate-400 resize-none"
                        placeholder="e.g., Create a 60-second highlight reel of product demos with upbeat transitions"
                        rows="4"
                        :disabled="agentStore.loading"
                      ></textarea>
                    </div>

                    <!-- Example Prompts -->
                    <div class="flex flex-wrap gap-2">
                      <button
                        v-for="example in examplePrompts"
                        :key="example"
                        type="button"
                        class="px-3 py-1.5 text-xs font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-full transition-colors"
                        @click="editRequest = example"
                      >
                        {{ example }}
                      </button>
                    </div>

                    <button
                      type="submit"
                      class="w-full flex items-center justify-center gap-2 px-6 py-3.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-semibold rounded-xl transition-all shadow-lg shadow-indigo-500/25"
                      :disabled="!editRequest.trim() || agentStore.loading"
                    >
                      <span class="material-symbols-outlined">auto_awesome</span>
                      {{ agentStore.loading ? 'Starting...' : 'Start AI Edit' }}
                    </button>
                  </div>
                </form>

                <!-- Tips -->
                <div class="mt-6 p-4 bg-slate-50 rounded-xl">
                  <h4 class="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">
                    Tips for better results
                  </h4>
                  <ul class="text-xs text-slate-500 space-y-1.5">
                    <li class="flex items-start gap-2">
                      <span class="material-symbols-outlined text-sm text-primary">lightbulb</span>
                      Specify target duration (e.g., "60 seconds", "2 minutes")
                    </li>
                    <li class="flex items-start gap-2">
                      <span class="material-symbols-outlined text-sm text-primary">lightbulb</span>
                      Describe the content type you want (demos, testimonials, etc.)
                    </li>
                    <li class="flex items-start gap-2">
                      <span class="material-symbols-outlined text-sm text-primary">lightbulb</span>
                      Mention transition preferences (fade, cut, dynamic)
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <!-- Active Session -->
          <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Left Column: Preview & Controls -->
            <div class="lg:col-span-2 space-y-6">
              <!-- Preview -->
              <AgentPreview
                :preview-url="agentStore.previewUrl"
                :loading="agentStore.isActive"
              />

              <!-- Controls -->
              <AgentControls
                :status="agentStore.status"
                :loading="agentStore.loading"
                :error="agentStore.error"
                :has-preview="agentStore.hasPreview"
                @approve="handleApprove"
                @feedback="handleFeedback"
                @cancel="handleCancel"
                @reset="handleReset"
              />
            </div>

            <!-- Right Column: Status & Activity -->
            <div class="space-y-6">
              <!-- Status -->
              <AgentStatus
                :status="agentStore.status"
                :current-iteration="agentStore.currentIteration"
                :max-iterations="agentStore.maxIterations"
                :progress-percent="agentStore.progressPercent"
                :evaluation="agentStore.latestEvaluation"
              />

              <!-- Activity Log -->
              <div class="h-80">
                <AgentActivityLog :entries="agentStore.activityLog" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Request Modal -->
    <div
      v-if="showRequestModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showRequestModal = false"
    >
      <div class="bg-white rounded-xl shadow-2xl max-w-lg w-full mx-4 overflow-hidden">
        <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h3 class="font-semibold text-slate-900">Edit Request</h3>
          <button
            class="p-1 hover:bg-slate-100 rounded-lg transition-colors"
            @click="showRequestModal = false"
          >
            <span class="material-symbols-outlined text-slate-400">close</span>
          </button>
        </div>
        <div class="p-6">
          <p class="text-sm text-slate-700 whitespace-pre-wrap">
            {{ agentStore.session?.user_request }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAgentStore } from '@/stores/agent'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AgentStatus from '@/components/agent/AgentStatus.vue'
import AgentPreview from '@/components/agent/AgentPreview.vue'
import AgentControls from '@/components/agent/AgentControls.vue'
import AgentActivityLog from '@/components/agent/AgentActivityLog.vue'

const agentStore = useAgentStore()

const editRequest = ref('')
const showRequestModal = ref(false)

const examplePrompts = [
  'Create a 60-second product demo highlight',
  'Compile all testimonial clips into a 2-minute video',
  'Make a quick 30-second teaser from the best moments'
]

async function handleStartEdit() {
  if (!editRequest.value.trim()) return
  await agentStore.startEdit(editRequest.value.trim())
  editRequest.value = ''
}

async function handleApprove() {
  await agentStore.approveSession()
}

async function handleFeedback(feedback: string) {
  await agentStore.provideFeedback(feedback)
}

function handleCancel() {
  agentStore.cancelSession()
}

function handleReset() {
  agentStore.reset()
}
</script>
