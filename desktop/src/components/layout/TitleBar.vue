<template>
  <div class="title-bar fixed top-0 left-0 right-0 h-10 bg-slate-50/80 backdrop-blur-sm border-b border-slate-200/60 flex items-center justify-center z-50" style="-webkit-app-region: drag;">
    <!-- Left spacer for macOS traffic lights (80px to account for the 3 buttons + spacing) -->
    <div class="absolute left-0 w-20 h-full" style="-webkit-app-region: no-drag;"></div>

    <!-- Dynamic Title -->
    <div class="text-xs font-semibold text-slate-600 select-none tracking-wide">
      {{ pageTitle }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    'library': 'My Library',
    'search': 'Search',
    'chat': 'Chat',
    'settings': 'Settings'
  }

  return titles[route.name as string] || 'VideoSearch AI'
})
</script>

<style scoped>
.title-bar {
  -webkit-user-select: none;
  user-select: none;
}
</style>
