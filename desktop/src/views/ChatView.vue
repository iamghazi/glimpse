<template>
  <div class="flex h-screen bg-background">
    <AppSidebar />

    <main class="flex-1 flex flex-col h-full overflow-hidden relative">
      <!-- Header -->
      <div class="shrink-0 bg-white border-b border-slate-200 flex flex-col z-10 shadow-sm">
        <div class="px-6 py-4 flex items-center justify-between border-b border-slate-100">
          <h1 class="text-xl font-bold text-slate-900 flex items-center gap-2">
            <span class="material-symbols-outlined text-primary">forum</span>
            Clip Conversation
          </h1>
          <div class="flex items-center gap-3">
            <button
              class="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-primary bg-primary/10 hover:bg-primary/20 rounded-lg transition-colors border border-primary/10"
              @click="router.push('/search')"
            >
              <span class="material-symbols-outlined text-[18px]">add_circle</span>
              Add Context
            </button>
            <button
              v-if="chatStore.messages.length > 0"
              class="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-slate-600 hover:text-red-600 bg-slate-100 hover:bg-red-50 rounded-lg transition-colors"
              @click="handleClearChat"
            >
              <span class="material-symbols-outlined text-[18px]">delete_sweep</span>
              Clear Chat
            </button>
          </div>
        </div>

        <!-- Active Context Bar -->
        <div
          v-if="chatStore.attachedClips.length > 0"
          class="bg-slate-50/50 px-6 py-4"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Active Context ({{ chatStore.attachedClips.length }} Clips Selected)
            </span>
          </div>
          <div class="flex gap-4 overflow-x-auto pb-2 no-scrollbar">
            <!-- Clip Cards -->
            <div
              v-for="clip in chatStore.attachedClips"
              :key="clip.chunk_id"
              class="relative group flex-shrink-0 w-80 bg-white rounded-lg border border-slate-200 overflow-hidden flex shadow-sm hover:shadow-md transition-shadow cursor-pointer"
              @click="handlePlayClip(clip)"
            >
              <!-- Thumbnail -->
              <div class="w-24 bg-gradient-to-br from-slate-300 to-slate-400 relative">
                <div class="absolute inset-0 flex items-center justify-center bg-black/10">
                  <span class="material-symbols-outlined text-white/80 text-2xl">play_circle</span>
                </div>
              </div>

              <!-- Info -->
              <div class="p-3 flex-1 min-w-0 flex flex-col justify-center gap-1">
                <div class="text-sm font-medium text-slate-900 truncate" :title="clip.title">
                  {{ clip.title }}
                </div>
                <div class="flex items-center gap-2 text-xs text-slate-500">
                  <span class="bg-slate-100 px-1.5 py-0.5 rounded text-[10px] font-mono">
                    {{ formatTimeRange(clip.start_time, clip.end_time) }}
                  </span>
                  <span
                    v-if="clip.score"
                    :class="[
                      'font-medium',
                      clip.score >= 0.8 ? 'text-green-600' : 'text-yellow-600'
                    ]"
                  >
                    {{ Math.round(clip.score * 100) }}%
                  </span>
                </div>
              </div>

              <!-- Remove Button -->
              <button
                class="absolute top-1 right-1 p-1 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors opacity-0 group-hover:opacity-100"
                @click.stop="chatStore.removeClip(clip.chunk_id)"
              >
                <span class="material-symbols-outlined text-[16px]">close</span>
              </button>
            </div>

            <!-- Add More Button -->
            <button
              class="flex-shrink-0 w-24 border-2 border-dashed border-slate-200 hover:border-primary/50 hover:bg-primary/5 rounded-lg flex flex-col items-center justify-center gap-1 text-slate-400 hover:text-primary transition-all group"
              @click="router.push('/search')"
            >
              <span class="material-symbols-outlined text-2xl group-hover:scale-110 transition-transform">add</span>
              <span class="text-[10px] font-medium">Add</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Messages Area -->
      <div class="flex-1 overflow-y-auto px-6 py-6 bg-slate-50/30">
        <div class="max-w-4xl mx-auto flex flex-col gap-6 pb-4">
          <!-- Date Separator (if needed) -->
          <div v-if="chatStore.messages.length > 0" class="flex items-center justify-center">
            <span class="text-xs font-medium text-slate-400 bg-slate-100 px-3 py-1 rounded-full">
              {{ formattedDate }}
            </span>
          </div>

          <!-- Empty State -->
          <div
            v-if="chatStore.messages.length === 0"
            class="flex flex-col items-center justify-center py-20 text-center"
          >
            <span class="material-symbols-outlined text-6xl text-slate-300 mb-4">forum</span>
            <h3 class="text-lg font-semibold text-slate-700 mb-2">
              {{ chatStore.attachedClips.length > 0 ? 'Start a conversation' : 'No clips selected' }}
            </h3>
            <p class="text-sm text-slate-500 mb-6 max-w-md">
              {{ chatStore.attachedClips.length > 0
                ? 'Ask questions about your selected video clips and get AI-powered insights.'
                : 'Add video clips from Search to start a conversation with AI.'
              }}
            </p>
            <button
              v-if="chatStore.attachedClips.length === 0"
              class="bg-primary hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-semibold flex items-center gap-2 shadow-lg shadow-blue-500/20 transition-all active:scale-95"
              @click="router.push('/search')"
            >
              <span class="material-symbols-outlined text-[20px]">search</span>
              Go to Search
            </button>
          </div>

          <!-- Messages -->
          <template v-for="(message, index) in chatStore.messages" :key="index">
            <!-- User Message -->
            <div v-if="message.role === 'user'" class="flex flex-row-reverse gap-3 group">
              <div class="w-8 h-8 rounded-full bg-primary flex items-center justify-center shrink-0">
                <span class="text-white text-xs font-bold">YO</span>
              </div>
              <div class="flex flex-col items-end gap-1 max-w-[80%]">
                <div class="bg-primary text-white px-5 py-3.5 rounded-2xl rounded-tr-none shadow-sm text-sm leading-relaxed">
                  <p>{{ message.content }}</p>
                </div>
                <span class="text-[10px] text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity">
                  {{ formatTime(message.timestamp) }}
                </span>
              </div>
            </div>

            <!-- AI Message -->
            <div v-else-if="message.role === 'assistant'" class="flex flex-row gap-3 group">
              <div class="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center shrink-0 shadow-sm">
                <span class="material-symbols-outlined text-white text-sm">smart_toy</span>
              </div>
              <div class="flex flex-col items-start gap-1 max-w-[80%]">
                <div class="bg-white border border-slate-200 text-slate-800 px-5 py-4 rounded-2xl rounded-tl-none shadow-sm text-sm leading-relaxed">
                  <div v-html="formatMessage(message.content)"></div>
                </div>
                <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <span class="text-[10px] text-slate-400">{{ formatTime(message.timestamp) }}</span>
                  <button
                    class="text-slate-400 hover:text-slate-600 transition-colors"
                    title="Copy"
                    @click="copyMessage(message.content)"
                  >
                    <span class="material-symbols-outlined text-[14px]">content_copy</span>
                  </button>
                  <button
                    v-if="index === chatStore.messages.length - 1"
                    class="text-slate-400 hover:text-slate-600 transition-colors"
                    title="Regenerate"
                    @click="handleRegenerateMessage"
                  >
                    <span class="material-symbols-outlined text-[14px]">refresh</span>
                  </button>
                </div>
              </div>
            </div>
          </template>

          <!-- Thinking Indicator -->
          <div v-if="chatStore.thinking" class="flex flex-row gap-3 animate-pulse">
            <div class="w-8 h-8 rounded-full bg-indigo-600/50 flex items-center justify-center shrink-0">
              <span class="material-symbols-outlined text-white text-sm">smart_toy</span>
            </div>
            <div class="bg-white border border-slate-200 px-5 py-4 rounded-2xl rounded-tl-none shadow-sm">
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                <div class="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-100"></div>
                <div class="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-200"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="shrink-0 border-t border-slate-200 bg-white px-6 py-4">
        <form class="max-w-4xl mx-auto flex gap-3" @submit.prevent="handleSendMessage">
          <div class="relative flex-1">
            <textarea
              v-model="messageInput"
              class="w-full px-4 py-3 pr-12 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary text-slate-900 placeholder-slate-400 resize-none"
              placeholder="Ask a question about the selected clips..."
              rows="1"
              :disabled="chatStore.loading || chatStore.attachedClips.length === 0"
              @keydown.enter.exact.prevent="handleSendMessage"
              @input="autoResizeTextarea"
            ></textarea>
            <button
              v-if="messageInput.trim()"
              type="submit"
              class="absolute right-2 bottom-2 p-2 bg-primary hover:bg-blue-600 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="chatStore.loading || !messageInput.trim() || chatStore.attachedClips.length === 0"
            >
              <span class="material-symbols-outlined text-[20px]">send</span>
            </button>
          </div>
          <button
            type="button"
            class="px-4 py-2 text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors flex items-center gap-2"
            @click="handleClearInput"
          >
            <span class="material-symbols-outlined text-[18px]">restart_alt</span>
            Clear
          </button>
        </form>
        <p class="text-xs text-slate-400 text-center mt-2">
          {{ chatStore.attachedClips.length }} clip{{ chatStore.attachedClips.length !== 1 ? 's' : '' }} selected
          • Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </main>

    <!-- Video Player Modal -->
    <VideoModal />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { useVideoPlayerStore } from '@/stores/videoPlayer'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import VideoModal from '@/components/video/VideoModal.vue'
import { formatTimeRange } from '@/types/video'
import type { SearchResult } from '@/types/video'

const router = useRouter()
const chatStore = useChatStore()
const videoPlayerStore = useVideoPlayerStore()

const messageInput = ref('')

const formattedDate = computed(() => {
  const now = new Date()
  return now.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  }) + ', ' + now.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  })
})

function formatTime(timestamp?: Date): string {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  })
}

function formatMessage(content: string): string {
  // Convert markdown-style formatting to HTML
  let formatted = content
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')

  // Convert bullet points
  formatted = formatted.replace(/^- (.+)$/gm, '<li>$1</li>')
  formatted = formatted.replace(/(<li>.*<\/li>)/s, '<ul class="list-disc pl-5 space-y-2 my-3">$1</ul>')

  return formatted
}

async function handleSendMessage() {
  const message = messageInput.value.trim()
  if (!message || chatStore.loading || chatStore.attachedClips.length === 0) return

  messageInput.value = ''
  await chatStore.sendMessage(message)
}

async function handleRegenerateMessage() {
  await chatStore.regenerateLastMessage()
}

function handlePlayClip(clip: SearchResult) {
  videoPlayerStore.openVideo(clip.video_id, {
    chunkId: clip.chunk_id,
    startTime: clip.start_time,
    endTime: clip.end_time
  })
}

function handleClearChat() {
  if (confirm('Are you sure you want to clear the chat history?')) {
    chatStore.clearAll()
  }
}

function handleClearInput() {
  messageInput.value = ''
}

function copyMessage(content: string) {
  navigator.clipboard.writeText(content)
}

function autoResizeTextarea(event: Event) {
  const textarea = event.target as HTMLTextAreaElement
  textarea.style.height = 'auto'
  textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px'
}
</script>

<style scoped>
.delay-100 {
  animation-delay: 100ms;
}

.delay-200 {
  animation-delay: 200ms;
}
</style>
