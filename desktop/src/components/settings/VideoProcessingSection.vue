<template>
  <SectionContainer title="Video Processing" icon="movie_filter">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Chunk Duration -->
      <BaseInput
        :model-value="settings?.videoProcessing.CHUNK_DURATION_SECONDS || 0"
        type="number"
        label="Chunk Duration"
        badge="Seconds"
        :min="10"
        :max="600"
        :error="settingsStore.getValidationError('videoProcessing.CHUNK_DURATION_SECONDS')"
        @update:model-value="updateField('CHUNK_DURATION_SECONDS', $event)"
      />

      <!-- Overlap -->
      <BaseInput
        :model-value="settings?.videoProcessing.CHUNK_OVERLAP_SECONDS || 0"
        type="number"
        label="Overlap"
        badge="Seconds"
        :min="0"
        :max="60"
        :error="settingsStore.getValidationError('videoProcessing.CHUNK_OVERLAP_SECONDS')"
        @update:model-value="updateField('CHUNK_OVERLAP_SECONDS', $event)"
      />

      <!-- Analysis FPS -->
      <BaseInput
        :model-value="settings?.videoProcessing.FRAME_EXTRACTION_FPS || 0"
        type="number"
        label="Analysis FPS"
        tooltip="Higher FPS means more detailed analysis but slower processing."
        :min="0.5"
        :max="5"
        :step="0.5"
        :error="settingsStore.getValidationError('videoProcessing.FRAME_EXTRACTION_FPS')"
        @update:model-value="updateField('FRAME_EXTRACTION_FPS', $event)"
      />
    </div>
  </SectionContainer>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SectionContainer from '@/components/ui/SectionContainer.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import { useSettingsStore } from '@/stores/settings'

const settingsStore = useSettingsStore()

const settings = computed(() => settingsStore.settings)

const updateField = (field: string, value: string | number) => {
  settingsStore.updateField('videoProcessing', field, value)
}
</script>
