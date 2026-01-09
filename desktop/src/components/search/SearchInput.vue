<template>
  <div class="flex gap-3">
    <div class="flex-1 relative">
      <input
        v-model="query"
        type="text"
        placeholder="Search for specific moments in your videos..."
        class="w-full px-5 py-4 pr-12 text-base border-2 border-slate-300 rounded-xl focus:border-primary focus:outline-none transition-colors"
        @keydown.enter="handleSearch"
      />
      <span class="material-symbols-outlined absolute right-4 top-1/2 -translate-y-1/2 text-slate-400">
        search
      </span>
    </div>

    <BaseButton
      variant="primary"
      size="lg"
      icon="search"
      :loading="loading"
      :disabled="!query.trim()"
      @click="handleSearch"
    >
      Search
    </BaseButton>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import BaseButton from '@/components/ui/BaseButton.vue'

interface Props {
  loading?: boolean
  initialQuery?: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  initialQuery: ''
})

const emit = defineEmits<{
  'search': [query: string]
}>()

const query = ref(props.initialQuery)

function handleSearch() {
  if (query.value.trim()) {
    emit('search', query.value.trim())
  }
}
</script>
