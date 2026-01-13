<template>
  <div class="h-screen overflow-hidden flex flex-col">
    <TitleBar />
    <div class="flex-1 overflow-hidden pt-10">
      <router-view />
    </div>
    <Toast />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useUIStore } from '@/stores/ui'
import { useBackendStore } from '@/stores/backend'
import TitleBar from '@/components/layout/TitleBar.vue'
import Toast from '@/components/ui/Toast.vue'

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
