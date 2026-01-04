<template>
  <div class="p-4 border-t border-slate-200 dark:border-slate-800">
    <div class="flex items-center gap-3 px-2 py-2">
      <div
        :class="[
          'w-2 h-2 rounded-full',
          backendStore.isHealthy ? 'bg-success shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-slate-300 dark:bg-slate-600'
        ]"
      ></div>
      <p class="text-slate-500 dark:text-slate-400 text-xs font-medium">
        Backend:
        <span class="text-slate-900 dark:text-white font-semibold">
          {{ backendStore.statusText }}
        </span>
      </p>
    </div>

    <!-- Qdrant Status (if backend is healthy) -->
    <div v-if="backendStore.isHealthy" class="flex items-center gap-3 px-2 py-1 mt-1">
      <div :class="[
          'w-2 h-2 rounded-full',
          backendStore.qdrantConnected ? 'bg-success' : 'bg-error'
        ]">
      </div>
      <p class="text-slate-500 dark:text-slate-400 text-xs font-medium">
        Qdrant:
        <span class="text-slate-900 dark:text-white font-semibold">
          {{ backendStore.qdrantConnected ? 'Connected' : 'Disconnected' }}
        </span>
      </p>
    </div>

    <!-- Last checked time -->
    <div v-if="backendStore.lastChecked" class="px-2 mt-2">
      <p class="text-slate-400 dark:text-slate-500 text-[10px]">
        Last checked: {{ formatLastChecked(backendStore.lastChecked) }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useBackendStore } from '@/stores/backend'

const backendStore = useBackendStore()

let healthCheckInterval: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  // Initial health check
  backendStore.checkHealth()

  // Start periodic health checks (every 30 seconds)
  healthCheckInterval = setInterval(() => {
    backendStore.checkHealth()
  }, 30000)
})

onUnmounted(() => {
  if (healthCheckInterval) {
    clearInterval(healthCheckInterval)
  }
})

const formatLastChecked = (date: Date): string => {
  const now = new Date()
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000) // seconds

  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return date.toLocaleTimeString()
}
</script>
