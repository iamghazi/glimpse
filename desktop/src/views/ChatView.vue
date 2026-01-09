<template>
  <div class="flex h-screen bg-background">
    <AppSidebar />

    <main class="flex-1 flex flex-col h-full overflow-hidden relative">
      <AppHeader title="Chat" subtitle="Conversation with your video clips">
        <template #actions>
          <ClearChatButton
            v-if="chatStore.messages.length > 0"
            @clear="chatStore.clearAll"
          />
        </template>
      </AppHeader>

      <div class="flex-1 flex flex-col overflow-hidden">
        <!-- Chat Context Bar -->
        <ChatContextBar
          :clips="chatStore.activeClips"
          @play-clip="handlePlayClip"
          @remove-clip="chatStore.removeClip"
          @clear-all="chatStore.clearClips"
        />

        <!-- Messages Area -->
        <div class="flex-1 flex flex-col overflow-hidden">
          <!-- Empty State -->
          <EmptyChatState
            v-if="chatStore.messages.length === 0"
            :has-clips="chatStore.hasActiveClips"
          >
            <template #action>
              <BaseButton
                v-if="!chatStore.hasActiveClips"
                variant="primary"
                icon="search"
                @click="router.push('/search')"
              >
                Go to Search
              </BaseButton>
            </template>
          </EmptyChatState>

          <!-- Chat Messages -->
          <ChatMessages
            v-else
            :items="chatStore.messagesWithSeparators"
            :thinking="chatStore.thinking"
            @regenerate-message="handleRegenerateMessage"
          />
        </div>

        <!-- Chat Input -->
        <ChatInput
          :loading="chatStore.loading"
          :disabled="!chatStore.canSendMessage"
          :has-clips="chatStore.hasActiveClips"
          @send="handleSendMessage"
        />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import ChatContextBar from '@/components/chat/ChatContextBar.vue'
import ChatMessages from '@/components/chat/ChatMessages.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import EmptyChatState from '@/components/chat/EmptyChatState.vue'
import ClearChatButton from '@/components/chat/ClearChatButton.vue'

const router = useRouter()
const chatStore = useChatStore()

async function handleSendMessage(message: string) {
  await chatStore.sendMessage(message)
}

async function handleRegenerateMessage(messageId: string) {
  await chatStore.regenerateLastMessage()
}

function handlePlayClip(clipId: string) {
  // TODO: Open video player with the specific clip
  console.log('Play clip:', clipId)
}
</script>
