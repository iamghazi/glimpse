import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { AppSettings, ValidationError } from '@/types/settings'

export const useSettingsStore = defineStore('settings', () => {
  // State
  const settings = ref<AppSettings | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const validationErrors = ref<ValidationError[]>([])
  const originalSettings = ref<AppSettings | null>(null)

  // Computed
  const isDirty = computed(() => {
    if (!settings.value || !originalSettings.value) return false
    return JSON.stringify(settings.value) !== JSON.stringify(originalSettings.value)
  })

  const isValid = computed(() => validationErrors.value.length === 0)

  const hasGCPConfigured = computed(() => {
    return settings.value?.googleCloud.GCP_PROJECT_ID?.trim() !== ''
  })

  // Actions
  async function loadSettings() {
    loading.value = true
    error.value = null

    try {
      // Try to load from local electron-store first
      const localSettings = await window.electron.settings.get()
      settings.value = localSettings
      originalSettings.value = JSON.parse(JSON.stringify(localSettings))

      // Then sync with backend (if available)
      try {
        const backendSettings = await window.electron.backend.getSettings()
        settings.value = backendSettings
        originalSettings.value = JSON.parse(JSON.stringify(backendSettings))

        // Save to local store
        await window.electron.settings.save(backendSettings)
      } catch (backendError) {
        console.warn('Backend unavailable, using local settings:', backendError)
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load settings'
      console.error('Error loading settings:', err)
    } finally {
      loading.value = false
    }
  }

  async function saveSettings() {
    if (!settings.value) {
      error.value = 'No settings to save'
      return
    }

    // Validate before saving
    if (!validate()) {
      error.value = 'Please fix validation errors before saving'
      return
    }

    loading.value = true
    error.value = null

    try {
      // Save to backend first
      await window.electron.backend.saveSettings(settings.value)

      // Then save to local store
      await window.electron.settings.save(settings.value)

      // Update original settings
      originalSettings.value = JSON.parse(JSON.stringify(settings.value))

      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to save settings'
      console.error('Error saving settings:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  async function resetToDefaults() {
    loading.value = true
    error.value = null

    try {
      const defaultSettings = await window.electron.settings.reset()
      settings.value = defaultSettings
      originalSettings.value = JSON.parse(JSON.stringify(defaultSettings))
      validationErrors.value = []
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to reset settings'
      console.error('Error resetting settings:', err)
    } finally {
      loading.value = false
    }
  }

  function updateField(section: keyof AppSettings, field: string, value: any) {
    if (!settings.value) return

    const settingsSection = settings.value[section] as any
    if (settingsSection) {
      settingsSection[field] = value
    }

    // Clear validation error for this field
    validationErrors.value = validationErrors.value.filter(
      (err) => err.field !== `${section}.${field}`
    )
  }

  function validate(): boolean {
    validationErrors.value = []

    if (!settings.value) {
      validationErrors.value.push({
        field: 'general',
        message: 'Settings not loaded'
      })
      return false
    }

    // Google Cloud validation
    if (!settings.value.googleCloud.GCP_PROJECT_ID?.trim()) {
      validationErrors.value.push({
        field: 'googleCloud.GCP_PROJECT_ID',
        message: 'GCP Project ID is required'
      })
    }

    if (!settings.value.googleCloud.GCP_LOCATION?.trim()) {
      validationErrors.value.push({
        field: 'googleCloud.GCP_LOCATION',
        message: 'GCP Location is required'
      })
    }

    if (!settings.value.googleCloud.GEMINI_MODEL?.trim()) {
      validationErrors.value.push({
        field: 'googleCloud.GEMINI_MODEL',
        message: 'Gemini Model is required'
      })
    }

    // Video Processing validation
    if (settings.value.videoProcessing.CHUNK_DURATION_SECONDS <= 0) {
      validationErrors.value.push({
        field: 'videoProcessing.CHUNK_DURATION_SECONDS',
        message: 'Chunk duration must be greater than 0'
      })
    }

    if (settings.value.videoProcessing.CHUNK_OVERLAP_SECONDS < 0) {
      validationErrors.value.push({
        field: 'videoProcessing.CHUNK_OVERLAP_SECONDS',
        message: 'Chunk overlap cannot be negative'
      })
    }

    if (
      settings.value.videoProcessing.CHUNK_OVERLAP_SECONDS >=
      settings.value.videoProcessing.CHUNK_DURATION_SECONDS
    ) {
      validationErrors.value.push({
        field: 'videoProcessing.CHUNK_OVERLAP_SECONDS',
        message: 'Overlap must be less than chunk duration'
      })
    }

    if (settings.value.videoProcessing.FRAME_EXTRACTION_FPS <= 0) {
      validationErrors.value.push({
        field: 'videoProcessing.FRAME_EXTRACTION_FPS',
        message: 'Frame extraction FPS must be greater than 0'
      })
    }

    // Search & Embedding validation
    if (settings.value.searchEmbedding.EMBEDDING_MAX_WORKERS <= 0) {
      validationErrors.value.push({
        field: 'searchEmbedding.EMBEDDING_MAX_WORKERS',
        message: 'Max workers must be greater than 0'
      })
    }

    if (settings.value.searchEmbedding.TIER1_CANDIDATES <= 0) {
      validationErrors.value.push({
        field: 'searchEmbedding.TIER1_CANDIDATES',
        message: 'Tier 1 candidates must be greater than 0'
      })
    }

    if (
      settings.value.searchEmbedding.CONFIDENCE_THRESHOLD < 0 ||
      settings.value.searchEmbedding.CONFIDENCE_THRESHOLD > 1
    ) {
      validationErrors.value.push({
        field: 'searchEmbedding.CONFIDENCE_THRESHOLD',
        message: 'Confidence threshold must be between 0 and 1'
      })
    }

    // Data Storage validation
    if (!settings.value.dataStorage.DATA_DIR?.trim()) {
      validationErrors.value.push({
        field: 'dataStorage.DATA_DIR',
        message: 'Data directory is required'
      })
    }

    if (!settings.value.dataStorage.VIDEOS_DIR?.trim()) {
      validationErrors.value.push({
        field: 'dataStorage.VIDEOS_DIR',
        message: 'Videos directory is required'
      })
    }

    if (!settings.value.dataStorage.FRAMES_DIR?.trim()) {
      validationErrors.value.push({
        field: 'dataStorage.FRAMES_DIR',
        message: 'Frames directory is required'
      })
    }

    if (!settings.value.dataStorage.METADATA_DIR?.trim()) {
      validationErrors.value.push({
        field: 'dataStorage.METADATA_DIR',
        message: 'Metadata directory is required'
      })
    }

    if (!settings.value.dataStorage.QDRANT_STORAGE_DIR?.trim()) {
      validationErrors.value.push({
        field: 'dataStorage.QDRANT_STORAGE_DIR',
        message: 'Qdrant storage directory is required'
      })
    }

    return validationErrors.value.length === 0
  }

  function getValidationError(field: string): string | undefined {
    return validationErrors.value.find((err) => err.field === field)?.message
  }

  function discardChanges() {
    if (originalSettings.value) {
      settings.value = JSON.parse(JSON.stringify(originalSettings.value))
      validationErrors.value = []
      error.value = null
    }
  }

  return {
    // State
    settings,
    loading,
    error,
    validationErrors,

    // Computed
    isDirty,
    isValid,
    hasGCPConfigured,

    // Actions
    loadSettings,
    saveSettings,
    resetToDefaults,
    updateField,
    validate,
    getValidationError,
    discardChanges
  }
})
