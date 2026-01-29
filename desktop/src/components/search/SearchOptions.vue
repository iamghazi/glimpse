<template>
  <BaseCard variant="bordered" padding="md">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-slate-900">Advanced Options</h3>
      <BaseButton
        variant="ghost"
        size="sm"
        @click="emit('reset')"
      >
        Reset to Defaults
      </BaseButton>
    </div>

    <div class="space-y-4">
      <!-- Top K Results -->
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-2">
          Number of Results
        </label>
        <div class="flex items-center gap-4">
          <BaseSlider
            v-model="topK"
            :min="1"
            :max="50"
            :step="1"
            class="flex-1"
            @update:model-value="handleUpdate"
          />
          <span class="text-sm font-semibold text-slate-900 min-w-[2rem] text-right">
            {{ topK }}
          </span>
        </div>
      </div>

      <!-- Confidence Threshold -->
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-2">
          Confidence Threshold
        </label>
        <div class="flex items-center gap-4">
          <BaseSlider
            v-model="confidenceThreshold"
            :min="0"
            :max="1"
            :step="0.05"
            class="flex-1"
            @update:model-value="handleUpdate"
          />
          <span class="text-sm font-semibold text-slate-900 min-w-[2rem] text-right">
            {{ confidenceThreshold.toFixed(2) }}
          </span>
        </div>
        <p class="text-xs text-slate-500 mt-1">
          Filter results below this confidence score
        </p>
      </div>

      <!-- Cascaded Reranking -->
      <div class="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
        <div>
          <label class="text-sm font-medium text-slate-900 block mb-1">
            Cascaded Reranking
          </label>
          <p class="text-xs text-slate-500">
            Use multi-stage reranking for better results (slower)
          </p>
        </div>
        <label class="relative inline-flex items-center cursor-pointer">
          <input
            v-model="useCascadedReranking"
            type="checkbox"
            class="sr-only peer"
            @change="handleUpdate"
          />
          <div class="w-11 h-6 bg-slate-300 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
        </label>
      </div>
    </div>
  </BaseCard>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseSlider from '@/components/ui/BaseSlider.vue'
import type { SearchOptions } from '@/types/search'

interface Props {
  options: SearchOptions
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update': [options: SearchOptions]
  'reset': []
}>()

const topK = ref(props.options.top_k)
const confidenceThreshold = ref(props.options.confidence_threshold)
const useCascadedReranking = ref(props.options.use_cascaded_reranking)

// Watch for prop changes and update local refs
watch(() => props.options, (newOptions) => {
  topK.value = newOptions.top_k
  confidenceThreshold.value = newOptions.confidence_threshold
  useCascadedReranking.value = newOptions.use_cascaded_reranking
}, { deep: true })

function handleUpdate() {
  emit('update', {
    top_k: topK.value,
    confidence_threshold: confidenceThreshold.value,
    use_cascaded_reranking: useCascadedReranking.value
  })
}
</script>
