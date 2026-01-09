<template>
  <div class="flex flex-col gap-4">
    <!-- Search and Status Filter -->
    <div class="flex flex-col sm:flex-row gap-3">
      <BaseInput
        v-model="searchQuery"
        placeholder="Search videos..."
        icon="search"
        class="flex-1"
        @update:model-value="emit('update:filters', currentFilters)"
      />

      <BaseSelect
        v-model="statusFilter"
        :options="statusOptions"
        class="sm:w-48"
        @update:model-value="emit('update:filters', currentFilters)"
      />
    </div>

    <!-- Sort and View Controls -->
    <div class="flex items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <BaseSelect
          v-model="sortBy"
          :options="sortByOptions"
          class="w-48"
          @update:model-value="emit('update:filters', currentFilters)"
        />

        <BaseButton
          variant="ghost"
          size="sm"
          :icon="sortOrder === 'asc' ? 'arrow_upward' : 'arrow_downward'"
          @click="toggleSortOrder"
        />
      </div>

      <div class="flex items-center gap-1 border border-slate-200 rounded-lg p-1">
        <BaseButton
          v-for="col in gridColumns"
          :key="col"
          :variant="columns === col ? 'primary' : 'ghost'"
          size="sm"
          @click="emit('update:columns', col)"
          class="min-w-[32px]"
        >
          {{ col }}
        </BaseButton>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseSelect from '@/components/ui/BaseSelect.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import type { VideoFilters } from '@/types/video'

interface Props {
  filters: VideoFilters
  columns: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:filters': [filters: VideoFilters]
  'update:columns': [columns: number]
}>()

const searchQuery = ref(props.filters.searchQuery)
const statusFilter = ref(props.filters.status)
const sortBy = ref(props.filters.sortBy)
const sortOrder = ref(props.filters.sortOrder)

const gridColumns = [1, 2, 3, 4, 5]

const statusOptions = [
  { value: 'all', label: 'All Videos' },
  { value: 'ready', label: 'Ready' },
  { value: 'indexed', label: 'Indexed' },
  { value: 'processing', label: 'Processing' },
  { value: 'uploading', label: 'Uploading' },
  { value: 'failed', label: 'Failed' }
]

const sortByOptions = [
  { value: 'uploaded_at', label: 'Upload Date' },
  { value: 'title', label: 'Title' },
  { value: 'duration_seconds', label: 'Duration' },
  { value: 'file_size_mb', label: 'File Size' }
]

const currentFilters = computed((): VideoFilters => ({
  searchQuery: searchQuery.value,
  status: statusFilter.value,
  sortBy: sortBy.value,
  sortOrder: sortOrder.value
}))

function toggleSortOrder() {
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  emit('update:filters', currentFilters.value)
}
</script>
