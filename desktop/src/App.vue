<template>
  <div class="h-screen overflow-hidden">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useUIStore } from '@/stores/ui'
import { useBackendStore } from '@/stores/backend'

const uiStore = useUIStore()
const backendStore = useBackendStore()

let stopHealthCheck: (() => void) | undefined

onMounted(() => {
  uiStore.initialize()

  // Start periodic backend health checks
  stopHealthCheck = backendStore.startPeriodicHealthCheck(30000) // Check every 30 seconds
})

onUnmounted(() => {
  // Clean up health check interval
  if (stopHealthCheck) {
    stopHealthCheck()
  }
})
</script>
