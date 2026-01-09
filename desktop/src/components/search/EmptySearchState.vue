<template>
  <div class="flex flex-col items-center justify-center py-16 px-4 text-center">
    <span class="material-symbols-outlined text-6xl text-slate-300 mb-4">
      {{ icon }}
    </span>

    <h3 class="text-lg font-semibold text-slate-900 mb-2">
      {{ title }}
    </h3>

    <p class="text-sm text-slate-500 max-w-md">
      {{ description }}
    </p>
  </div>
</template>

<script setup lang="ts">
interface Props {
  hasSearched: boolean
}

const props = defineProps<Props>()

const icon = props.hasSearched ? 'search_off' : 'image_search'
const title = props.hasSearched ? 'No results found' : 'Ready to search'
const description = props.hasSearched
  ? 'Try adjusting your search query or confidence threshold to find more results.'
  : 'Enter a search query to find relevant video clips using semantic search.'
</script>
