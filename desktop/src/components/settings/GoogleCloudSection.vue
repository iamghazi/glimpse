<template>
  <SectionContainer id="google-cloud-section" title="Google Cloud API" icon="cloud_circle">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      <!-- Project ID -->
      <BaseInput
        :model-value="settings?.googleCloud.GCP_PROJECT_ID || ''"
        label="Project ID"
        placeholder="e.g., video-search-app-2024"
        helper-text="The ID of your GCP project with Vertex AI API enabled."
        :error="settingsStore.getValidationError('googleCloud.GCP_PROJECT_ID')"
        required
        @update:model-value="updateField('GCP_PROJECT_ID', $event)"
      />

      <!-- Location -->
      <BaseSelect
        :model-value="settings?.googleCloud.GCP_LOCATION || ''"
        label="Location"
        :options="locationOptions"
        :error="settingsStore.getValidationError('googleCloud.GCP_LOCATION')"
        required
        @update:model-value="updateField('GCP_LOCATION', $event)"
      />

      <!-- Model Selection -->
      <div class="md:col-span-2">
        <BaseSelect
          :model-value="settings?.googleCloud.GEMINI_MODEL || ''"
          label="Gemini Model"
          :options="modelOptions"
          :error="settingsStore.getValidationError('googleCloud.GEMINI_MODEL')"
          @update:model-value="updateField('GEMINI_MODEL', $event)"
        />
      </div>
    </div>

    <!-- Test Connection Action -->
    <div class="flex items-center justify-between pt-4 border-t border-slate-100 dark:border-slate-800">
      <div class="flex items-center gap-2">
        <span
          :class="[
            'flex h-2 w-2 rounded-full',
            backendStore.gcpConnected ? 'bg-success' : 'bg-slate-300 dark:bg-slate-600'
          ]"
        ></span>
        <span class="text-xs font-medium text-slate-500 dark:text-slate-400">
          Status: {{ backendStore.gcpConnected ? 'Connected' : 'Not Connected' }}
        </span>
      </div>

      <BaseButton
        variant="secondary"
        icon="bolt"
        :loading="backendStore.testingGCP"
        @click="testConnection"
      >
        Test Connection
      </BaseButton>
    </div>

    <!-- Error Message -->
    <div v-if="backendStore.gcpError" class="mt-4 p-3 bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-900/30 rounded-lg">
      <p class="text-sm text-error">{{ backendStore.gcpError }}</p>
    </div>
  </SectionContainer>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SectionContainer from '@/components/ui/SectionContainer.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseSelect from '@/components/ui/BaseSelect.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import { useSettingsStore } from '@/stores/settings'
import { useBackendStore } from '@/stores/backend'

const settingsStore = useSettingsStore()
const backendStore = useBackendStore()

const settings = computed(() => settingsStore.settings)

const locationOptions = [
  { value: 'us-central1', label: 'us-central1 (Iowa)' },
  { value: 'us-east1', label: 'us-east1 (South Carolina)' },
  { value: 'us-west1', label: 'us-west1 (Oregon)' },
  { value: 'europe-west4', label: 'europe-west4 (Netherlands)' },
  { value: 'asia-east1', label: 'asia-east1 (Taiwan)' },
  { value: 'asia-northeast1', label: 'asia-northeast1 (Tokyo)' }
]

const modelOptions = [
  { value: 'gemini-2.0-flash-exp', label: 'gemini-2.0-flash-exp (Recommended)' },
  { value: 'gemini-1.5-pro-latest', label: 'gemini-1.5-pro-latest' },
  { value: 'gemini-1.5-flash-latest', label: 'gemini-1.5-flash-latest' },
  { value: 'gemini-1.0-pro-vision', label: 'gemini-1.0-pro-vision' }
]

const updateField = (field: string, value: string | number) => {
  settingsStore.updateField('googleCloud', field, value)
}

const testConnection = async () => {
  await backendStore.testGCPConnection()
}
</script>
