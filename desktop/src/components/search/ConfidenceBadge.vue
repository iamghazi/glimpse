<template>
  <BaseBadge :variant="variant" size="sm">
    {{ label }}
  </BaseBadge>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import BaseBadge from '@/components/ui/BaseBadge.vue'
import { getConfidenceLevel, getConfidenceBadgeVariant } from '@/types/search'

interface Props {
  score: number
}

const props = defineProps<Props>()

const variant = computed(() => getConfidenceBadgeVariant(props.score))
const label = computed(() => getConfidenceLevel(props.score))
</script>
