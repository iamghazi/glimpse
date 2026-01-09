import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  ChatMessage,
  ActiveClip,
  ChatRequest,
  MessageOrSeparator,
  DateSeparator
} from '@/types/chat'
import { formatMessageDate } from '@/types/chat'

export const useChatStore = defineStore('chat', () => {
  // State
  const messages = ref<ChatMessage[]>([])
  const activeClips = ref<ActiveClip[]>([])
  const loading = ref(false)
  const thinking = ref(false)
  const error = ref<string | null>(null)
  const currentInput = ref('')

  // Computed
  const messagesWithSeparators = computed(() => {
    const result: MessageOrSeparator[] = []
    let lastDate: string | null = null

    messages.value.forEach(msg => {
      const dateStr = formatMessageDate(msg.timestamp)

      if (dateStr !== lastDate) {
        result.push({
          id: `separator-${msg.id}`,
          date: dateStr,
          isDateSeparator: true
        } as DateSeparator)
        lastDate = dateStr
      }

      result.push(msg)
    })

    return result
  })

  const hasActiveClips = computed(() => activeClips.value.length > 0)
  const canSendMessage = computed(() =>
    !loading.value && !thinking.value && hasActiveClips.value
  )

  // Actions
  async function sendMessage(content: string) {
    if (!content.trim() || !hasActiveClips.value) return

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date()
    }

    messages.value.push(userMessage)
    currentInput.value = ''
    thinking.value = true
    error.value = null

    try {
      const request: ChatRequest = {
        query: content.trim(),
        clip_ids: activeClips.value.map(c => c.clip_id)
      }

      const response = await window.electron.chat.sendMessage(request)

      const assistantMessage: ChatMessage = {
        id: `msg-${Date.now()}-ai`,
        role: 'assistant',
        content: response.answer,
        timestamp: new Date()
      }

      messages.value.push(assistantMessage)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to send message'
      console.error('Chat error:', err)

      // Add error message
      const errorMessage: ChatMessage = {
        id: `msg-${Date.now()}-error`,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      }
      messages.value.push(errorMessage)
    } finally {
      thinking.value = false
    }
  }

  function addClip(clip: ActiveClip) {
    // Prevent duplicates
    if (!activeClips.value.find(c => c.clip_id === clip.clip_id)) {
      activeClips.value.push(clip)
    }
  }

  function addClips(clips: ActiveClip[]) {
    clips.forEach(clip => addClip(clip))
  }

  function removeClip(clipId: string) {
    activeClips.value = activeClips.value.filter(c => c.clip_id !== clipId)
  }

  function clearClips() {
    activeClips.value = []
  }

  function clearChat() {
    messages.value = []
    error.value = null
  }

  function clearAll() {
    clearChat()
    clearClips()
    currentInput.value = ''
  }

  async function regenerateLastMessage() {
    if (messages.value.length < 2) return

    // Find last user message
    const lastUserMessageIdx = messages.value
      .slice()
      .reverse()
      .findIndex(m => m.role === 'user')

    if (lastUserMessageIdx === -1) return

    const actualIdx = messages.value.length - 1 - lastUserMessageIdx
    const lastUserMessage = messages.value[actualIdx]

    // Remove all messages after the last user message
    messages.value = messages.value.slice(0, actualIdx + 1)

    // Resend the message
    await sendMessage(lastUserMessage.content)
  }

  return {
    // State
    messages,
    activeClips,
    loading,
    thinking,
    error,
    currentInput,

    // Computed
    messagesWithSeparators,
    hasActiveClips,
    canSendMessage,

    // Actions
    sendMessage,
    addClip,
    addClips,
    removeClip,
    clearClips,
    clearChat,
    clearAll,
    regenerateLastMessage
  }
})
