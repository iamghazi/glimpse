import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { HealthCheckResponse } from '@/types/backend'

export type BackendStatus = 'healthy' | 'unhealthy' | 'unknown'

export const useBackendStore = defineStore('backend', () => {
  // State
  const status = ref<BackendStatus>('unknown')
  const qdrantConnected = ref(false)
  const gcpConnected = ref(false)
  const version = ref<string | null>(null)
  const lastChecked = ref<Date | null>(null)
  const checking = ref(false)
  const testingGCP = ref(false)
  const gcpError = ref<string | null>(null)

  // Computed
  const isHealthy = computed(() => status.value === 'healthy')
  const isUnhealthy = computed(() => status.value === 'unhealthy')
  const statusColor = computed(() => {
    switch (status.value) {
      case 'healthy':
        return 'success'
      case 'unhealthy':
        return 'error'
      default:
        return 'gray'
    }
  })

  const statusText = computed(() => {
    switch (status.value) {
      case 'healthy':
        return 'Backend Online'
      case 'unhealthy':
        return 'Backend Offline'
      default:
        return 'Checking...'
    }
  })

  const allSystemsOperational = computed(() => {
    return isHealthy.value && qdrantConnected.value
  })

  // Actions
  async function checkHealth() {
    console.log('[Store] Starting health check...')
    checking.value = true

    try {
      console.log('[Store] Calling window.electron.backend.health()...')
      const health: HealthCheckResponse = await window.electron.backend.health()
      console.log('[Store] Health check response:', health)

      status.value = 'healthy'
      qdrantConnected.value = health.qdrant_connected
      version.value = health.version
      lastChecked.value = new Date()

      return true
    } catch (err) {
      status.value = 'unhealthy'
      qdrantConnected.value = false
      version.value = null
      lastChecked.value = new Date()

      console.error('[Store] Backend health check failed:', err)
      return false
    } finally {
      checking.value = false
    }
  }

  async function testGCPConnection() {
    testingGCP.value = true
    gcpError.value = null

    try {
      const connected = await window.electron.backend.testConnection()

      gcpConnected.value = connected

      if (!connected) {
        gcpError.value = 'Failed to connect to Google Cloud. Check your credentials and project ID.'
      }

      return connected
    } catch (err) {
      gcpConnected.value = false
      gcpError.value = err instanceof Error ? err.message : 'Unknown error occurred'

      console.error('GCP connection test failed:', err)
      return false
    } finally {
      testingGCP.value = false
    }
  }

  function startPeriodicHealthCheck(intervalMs = 30000) {
    // Initial check
    checkHealth()

    // Periodic checks
    const intervalId = setInterval(() => {
      checkHealth()
    }, intervalMs)

    // Return cleanup function
    return () => clearInterval(intervalId)
  }

  function reset() {
    status.value = 'unknown'
    qdrantConnected.value = false
    gcpConnected.value = false
    version.value = null
    lastChecked.value = null
    checking.value = false
    testingGCP.value = false
    gcpError.value = null
  }

  return {
    // State
    status,
    qdrantConnected,
    gcpConnected,
    version,
    lastChecked,
    checking,
    testingGCP,
    gcpError,

    // Computed
    isHealthy,
    isUnhealthy,
    statusColor,
    statusText,
    allSystemsOperational,

    // Actions
    checkHealth,
    testGCPConnection,
    startPeriodicHealthCheck,
    reset
  }
})
