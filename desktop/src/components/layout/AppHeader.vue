<template>
  <header class="h-16 bg-surface border-b border-slate-200 flex items-center justify-between px-8 shrink-0 z-10">
    <div>
      <h2 class="text-xl font-bold text-slate-900 tracking-tight">{{ title }}</h2>
      <p v-if="subtitle" class="text-xs text-slate-500">
        {{ subtitle }}
      </p>
    </div>

    <div class="flex items-center gap-3">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup lang="ts">
interface Props {
  title: string
  subtitle?: string
}

defineProps<Props>()
</script>
