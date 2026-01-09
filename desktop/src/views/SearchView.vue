<template>
  <div class="flex h-screen bg-background">
    <AppSidebar />

    <main class="flex-1 flex flex-col h-full overflow-hidden relative">
      <AppHeader title="Search" subtitle="Semantic search across your video library" />

      <div class="flex-1 overflow-y-auto p-8">
        <div class="max-w-7xl mx-auto space-y-6">
          <!-- Search Input -->
          <SearchInput
            :loading="searchStore.loading"
            :initial-query="searchStore.query"
            @search="handleSearch"
          />

          <!-- Search Options -->
          <SearchOptions
            :options="searchStore.options"
            @update="searchStore.updateOptions"
            @reset="handleResetOptions"
          />

          <!-- Processing Tier Indicator -->
          <div v-if="searchStore.processingStatus.isProcessing" class="flex justify-center">
            <ProcessingTierIndicator :status="searchStore.processingStatus" />
          </div>

          <!-- Search Stats -->
          <div v-if="searchStore.hasSearched && !searchStore.loading">
            <SearchStats
              :num-results="searchStore.totalResults"
              :search-time="searchStore.searchTime"
              :cascaded-reranking="searchStore.options.use_cascaded_reranking"
            />
          </div>

          <!-- Loading State -->
          <div v-if="searchStore.loading && !searchStore.processingStatus.isProcessing" class="flex items-center justify-center py-16">
            <span class="material-symbols-outlined text-4xl text-primary animate-spin">
              sync
            </span>
          </div>

          <!-- Error State -->
          <div v-else-if="searchStore.error" class="p-6 bg-error/5 border border-error/20 rounded-xl">
            <div class="flex items-start gap-3">
              <span class="material-symbols-outlined text-error">
                error
              </span>
              <div>
                <p class="text-sm font-medium text-error mb-1">Search Failed</p>
                <p class="text-sm text-slate-600">{{ searchStore.error }}</p>
              </div>
            </div>
          </div>

          <!-- Empty State -->
          <EmptySearchState
            v-else-if="!searchStore.hasResults && !searchStore.loading"
            :has-searched="searchStore.hasSearched"
          />

          <!-- Search Results -->
          <div v-else class="space-y-4">
            <SearchResultCard
              v-for="result in searchStore.filteredResults"
              :key="result.chunk_id"
              :result="result"
              @click="handleResultClick(result)"
              @add-to-chat="handleAddToChat"
              @play-clip="handlePlayClip"
            />
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useSearchStore } from '@/stores/search'
import { useChatStore } from '@/stores/chat'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import SearchInput from '@/components/search/SearchInput.vue'
import SearchOptions from '@/components/search/SearchOptions.vue'
import ProcessingTierIndicator from '@/components/search/ProcessingTierIndicator.vue'
import SearchStats from '@/components/search/SearchStats.vue'
import EmptySearchState from '@/components/search/EmptySearchState.vue'
import SearchResultCard from '@/components/search/SearchResultCard.vue'
import type { SearchResult } from '@/types/search'
import type { ActiveClip } from '@/types/chat'

const router = useRouter()
const searchStore = useSearchStore()
const chatStore = useChatStore()

async function handleSearch(query: string) {
  await searchStore.search(query)
}

function handleResetOptions() {
  searchStore.updateOptions({
    top_k: 10,
    use_cascaded_reranking: true,
    confidence_threshold: 0.0
  })
}

function handleResultClick(result: SearchResult) {
  // TODO: Open result detail modal or navigate to video
  console.log('Result clicked:', result)
}

function handleAddToChat(result: SearchResult) {
  const clip: ActiveClip = {
    clip_id: result.chunk_id,
    video_id: result.video_id,
    title: result.title,
    start_time: result.start_time,
    end_time: result.end_time,
    thumbnail: result.representative_frame,
    confidence_score: result.score
  }

  chatStore.addClip(clip)

  // Navigate to chat
  router.push('/chat')
}

function handlePlayClip(result: SearchResult) {
  // TODO: Open video player with the specific clip
  console.log('Play clip:', result)
}
</script>
