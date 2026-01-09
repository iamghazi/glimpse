<template>
  <div class="flex flex-col items-center justify-center py-16 px-4 text-center">
    <span class="material-symbols-outlined text-6xl text-slate-300 mb-4">
      {{ icon }}
    </span>

    <h3 class="text-lg font-semibold text-slate-900 mb-2">
      {{ title }}
    </h3>

    <p class="text-sm text-slate-500 mb-6 max-w-md">
      {{ description }}
    </p>

    <slot name="action" />
  </div>
</template>

<script setup lang="ts">
interface Props {
  icon?: string
  title: string
  description: string
}

withDefaults(defineProps<Props>(), {
  icon: 'video_library'
})
</script>
