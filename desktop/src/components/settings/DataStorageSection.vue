<template>
  <SectionContainer title="Data Storage" icon="folder">
    <div class="grid grid-cols-1 gap-6">
      <!-- Data Directory -->
      <PathInput
        :model-value="settings?.dataStorage.DATA_DIR || ''"
        label="Data Directory"
        placeholder="e.g., ./data"
        helper-text="Root directory for all video search data"
        :error="settingsStore.getValidationError('dataStorage.DATA_DIR')"
        required
        @update:model-value="updateField('DATA_DIR', $event)"
      />

      <!-- Videos Directory -->
      <PathInput
        :model-value="settings?.dataStorage.VIDEOS_DIR || ''"
        label="Videos Directory"
        placeholder="e.g., ./data/videos"
        helper-text="Directory where uploaded videos are stored"
        :error="settingsStore.getValidationError('dataStorage.VIDEOS_DIR')"
        required
        @update:model-value="updateField('VIDEOS_DIR', $event)"
      />

      <!-- Frames Directory -->
      <PathInput
        :model-value="settings?.dataStorage.FRAMES_DIR || ''"
        label="Frames Directory"
        placeholder="e.g., ./data/frames"
        helper-text="Directory for extracted video frames"
        :error="settingsStore.getValidationError('dataStorage.FRAMES_DIR')"
        required
        @update:model-value="updateField('FRAMES_DIR', $event)"
      />

      <!-- Metadata Directory -->
      <PathInput
        :model-value="settings?.dataStorage.METADATA_DIR || ''"
        label="Metadata Directory"
        placeholder="e.g., ./data/metadata"
        helper-text="Directory for video metadata JSON files"
        :error="settingsStore.getValidationError('dataStorage.METADATA_DIR')"
        required
        @update:model-value="updateField('METADATA_DIR', $event)"
      />

      <!-- Qdrant Storage Directory -->
      <PathInput
        :model-value="settings?.dataStorage.QDRANT_STORAGE_DIR || ''"
        label="Vector Index Path"
        placeholder="e.g., ./data/qdrant_storage"
        helper-text="Directory for Qdrant vector database storage"
        :error="settingsStore.getValidationError('dataStorage.QDRANT_STORAGE_DIR')"
        required
        @update:model-value="updateField('QDRANT_STORAGE_DIR', $event)"
      />
    </div>
  </SectionContainer>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SectionContainer from '@/components/ui/SectionContainer.vue'
import PathInput from '@/components/ui/PathInput.vue'
import { useSettingsStore } from '@/stores/settings'

const settingsStore = useSettingsStore()

const settings = computed(() => settingsStore.settings)

const updateField = (field: string, value: string | number) => {
  settingsStore.updateField('dataStorage', field, value)
}
</script>
