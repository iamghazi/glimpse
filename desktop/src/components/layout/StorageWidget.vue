<template>
  <div class="p-4 border-t border-slate-200">
    <div class="flex items-center justify-between mb-2">
      <span class="text-xs font-semibold text-slate-700">Storage</span>
      <span class="text-xs text-slate-500">{{ usedGB }} / {{ totalGB }} GB</span>
    </div>

    <div class="h-2 bg-slate-200 rounded-full overflow-hidden">
      <div
        class="h-full bg-primary rounded-full transition-all duration-300"
        :style="{ width: `${percentage}%` }"
      ></div>
    </div>

    <p class="mt-2 text-[10px] text-slate-400">
      {{ availableGB }} GB available
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  usedBytes: number
  totalBytes: number
}

const props = defineProps<Props>()

const usedGB = computed(() => (props.usedBytes / (1024 ** 3)).toFixed(1))
const totalGB = computed(() => (props.totalBytes / (1024 ** 3)).toFixed(1))
const availableGB = computed(() => ((props.totalBytes - props.usedBytes) / (1024 ** 3)).toFixed(1))
const percentage = computed(() => (props.usedBytes / props.totalBytes) * 100)
</script>
