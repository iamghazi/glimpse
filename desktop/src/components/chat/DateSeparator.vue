<template>
  <div class="flex items-center gap-3 my-6">
    <div class="flex-1 h-px bg-slate-200"></div>
    <span class="text-xs font-medium text-slate-500 uppercase tracking-wide">
      {{ date }}
    </span>
    <div class="flex-1 h-px bg-slate-200"></div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  date: string
}

defineProps<Props>()
</script>
