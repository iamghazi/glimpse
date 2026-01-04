<template>
  <SectionContainer title="Search & Embedding" icon="manage_search">
    <!-- Parallel Workers Slider -->
    <div class="mb-6">
      <BaseSlider
        :model-value="settings?.searchEmbedding.EMBEDDING_MAX_WORKERS || 0"
        label="Parallel Workers"
        helper-text="Number of simultaneous indexing processes. Depends on your CPU cores."
        :min="1"
        :max="16"
        :step="1"
        @update:model-value="updateField('EMBEDDING_MAX_WORKERS', $event)"
      />
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Tier 1 Candidates -->
      <BaseInput
        :model-value="settings?.searchEmbedding.TIER1_CANDIDATES || 0"
        type="number"
        label="Tier 1 Candidates"
        tooltip="Number of preliminary results to fetch before re-ranking"
        :min="10"
        :max="200"
        :error="settingsStore.getValidationError('searchEmbedding.TIER1_CANDIDATES')"
        @update:model-value="updateField('TIER1_CANDIDATES', $event)"
      />

      <!-- Confidence Threshold Slider -->
      <div class="flex flex-col gap-2">
        <label class="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">
          Confidence Threshold
          <span
            class="material-symbols-outlined text-[16px] text-slate-400 cursor-help"
            title="Minimum confidence score (0-1) required for search results"
          >
            info
          </span>
        </label>
        <div class="flex items-center gap-4">
          <input
            type="range"
            :value="settings?.searchEmbedding.CONFIDENCE_THRESHOLD || 0"
            min="0"
            max="1"
            step="0.05"
            class="flex-1 h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-primary"
            @input="updateConfidenceThreshold"
          />
          <span class="text-sm font-bold text-primary min-w-[3rem] text-right">
            {{ (settings?.searchEmbedding.CONFIDENCE_THRESHOLD || 0).toFixed(2) }}
          </span>
        </div>
        <p v-if="settingsStore.getValidationError('searchEmbedding.CONFIDENCE_THRESHOLD')" class="text-xs text-error">
          {{ settingsStore.getValidationError('searchEmbedding.CONFIDENCE_THRESHOLD') }}
        </p>
      </div>
    </div>
  </SectionContainer>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SectionContainer from '@/components/ui/SectionContainer.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseSlider from '@/components/ui/BaseSlider.vue'
import { useSettingsStore } from '@/stores/settings'

const settingsStore = useSettingsStore()

const settings = computed(() => settingsStore.settings)

const updateField = (field: string, value: string | number) => {
  settingsStore.updateField('searchEmbedding', field, value)
}

const updateConfidenceThreshold = (event: Event) => {
  const target = event.target as HTMLInputElement
  updateField('CONFIDENCE_THRESHOLD', parseFloat(target.value))
}
</script>
