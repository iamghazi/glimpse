<template>
  <div class="flex items-center gap-3">
    <div
      v-for="tier in tiers"
      :key="tier"
      :class="tierClasses(tier)"
    >
      <span class="material-symbols-outlined text-sm">
        {{ tierIcon(tier) }}
      </span>
      <span class="text-xs font-medium">
        {{ tierLabel(tier) }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ProcessingStatus, ProcessingTier } from '@/types/search'

interface Props {
  status: ProcessingStatus
}

const props = defineProps<Props>()

const tiers: ProcessingTier[] = ['embedding', 'initial-ranking', 'reranking']

const tierClasses = (tier: ProcessingTier) => {
  const base = 'flex items-center gap-1.5 px-3 py-2 rounded-lg transition-all'

  if (props.status.completed.includes(tier)) {
    return [base, 'bg-success/10 text-success']
  }

  if (props.status.currentTier === tier) {
    return [base, 'bg-primary/10 text-primary animate-pulse']
  }

  return [base, 'bg-slate-100 text-slate-400']
}

const tierIcon = (tier: ProcessingTier) => {
  const icons: Record<ProcessingTier, string> = {
    'embedding': 'auto_awesome',
    'initial-ranking': 'filter_list',
    'reranking': 'sort'
  }
  return icons[tier]
}

const tierLabel = (tier: ProcessingTier) => {
  const labels: Record<ProcessingTier, string> = {
    'embedding': 'Embedding',
    'initial-ranking': 'Ranking',
    'reranking': 'Reranking'
  }
  return labels[tier]
}
</script>
