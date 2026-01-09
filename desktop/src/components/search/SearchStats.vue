<template>
  <div class="flex items-center gap-6 text-sm text-slate-500">
    <span class="flex items-center gap-1.5">
      <span class="material-symbols-outlined text-base">
        description
      </span>
      <span>
        <strong class="text-slate-900">{{ numResults }}</strong>
        {{ numResults === 1 ? 'result' : 'results' }}
      </span>
    </span>

    <span class="flex items-center gap-1.5">
      <span class="material-symbols-outlined text-base">
        schedule
      </span>
      <span>{{ formattedSearchTime }}</span>
    </span>

    <span v-if="cascadedReranking" class="flex items-center gap-1.5">
      <span class="material-symbols-outlined text-base">
        auto_awesome
      </span>
      <span>Cascaded Reranking</span>
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  numResults: number
  searchTime: number // in ms
  cascadedReranking?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  cascadedReranking: false
})

const formattedSearchTime = computed(() => {
  if (props.searchTime < 1000) {
    return `${props.searchTime}ms`
  }
  return `${(props.searchTime / 1000).toFixed(2)}s`
})
</script>
