import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  SearchOptions,
  SearchResult,
  ProcessingStatus,
  ProcessingTier
} from '@/types/search'

export const useSearchStore = defineStore('search', () => {
  // State
  const query = ref('')
  const results = ref<SearchResult[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const searchTime = ref<number>(0)  // in ms
  const totalResults = ref<number>(0)

  const options = ref<SearchOptions>({
    top_k: 10,
    use_cascaded_reranking: false,  // Disabled by default - LLM reranker can be too aggressive
    confidence_threshold: 0.0
  })

  const processingStatus = ref<ProcessingStatus>({
    currentTier: null,
    completed: [],
    isProcessing: false
  })

  // Computed
  const hasResults = computed(() => results.value.length > 0)
  const hasSearched = computed(() => query.value.trim() !== '' || results.value.length > 0)

  const filteredResults = computed(() => {
    return results.value.filter(r => r.score >= options.value.confidence_threshold)
  })

  // Actions
  async function search(searchQuery: string) {
    if (!searchQuery.trim()) {
      error.value = 'Please enter a search query'
      return
    }

    query.value = searchQuery
    loading.value = true
    error.value = null
    processingStatus.value = {
      currentTier: 'embedding',
      completed: [],
      isProcessing: true
    }

    try {
      // Simulate processing tiers for UI feedback
      await simulateProcessingTier('embedding')

      processingStatus.value.completed.push('embedding')
      processingStatus.value.currentTier = 'initial-ranking'
      await simulateProcessingTier('initial-ranking')

      if (options.value.use_cascaded_reranking) {
        processingStatus.value.completed.push('initial-ranking')
        processingStatus.value.currentTier = 'reranking'
        await simulateProcessingTier('reranking')
      }

      // Actual search
      const startTime = Date.now()
      const response = await window.electron.search.search({
        query: searchQuery,
        top_k: options.value.top_k,
        use_cascaded_reranking: options.value.use_cascaded_reranking,
        confidence_threshold: options.value.confidence_threshold
      })

      results.value = response.results
      totalResults.value = response.num_results
      searchTime.value = Date.now() - startTime

      processingStatus.value.completed.push('reranking')
      processingStatus.value.currentTier = null
      processingStatus.value.isProcessing = false
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Search failed'
      console.error('Search error:', err)
      processingStatus.value.isProcessing = false
    } finally {
      loading.value = false
    }
  }

  async function simulateProcessingTier(tier: ProcessingTier) {
    // Small delay for UI feedback
    await new Promise(resolve => setTimeout(resolve, 300))
  }

  function updateOptions(newOptions: Partial<SearchOptions>) {
    options.value = { ...options.value, ...newOptions }
  }

  function clearResults() {
    results.value = []
    query.value = ''
    error.value = null
    totalResults.value = 0
    searchTime.value = 0
    processingStatus.value = {
      currentTier: null,
      completed: [],
      isProcessing: false
    }
  }

  return {
    // State
    query,
    results,
    loading,
    error,
    searchTime,
    totalResults,
    options,
    processingStatus,

    // Computed
    hasResults,
    hasSearched,
    filteredResults,

    // Actions
    search,
    updateOptions,
    clearResults
  }
})
