<template>
  <section class="flex flex-col gap-4">
    <!-- Section Header -->
    <div v-if="title || icon" class="flex items-center gap-2 pb-2 border-b border-slate-200 dark:border-slate-800">
      <span v-if="icon" class="material-symbols-outlined text-primary">{{ icon }}</span>
      <h3 class="text-lg font-bold text-slate-900 dark:text-white">{{ title }}</h3>
    </div>

    <!-- Section Content -->
    <div class="bg-surface-light dark:bg-surface-dark rounded-xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm">
      <slot />
    </div>
  </section>
</template>

<script setup lang="ts">
interface Props {
  title?: string
  icon?: string
}

defineProps<Props>()
</script>
