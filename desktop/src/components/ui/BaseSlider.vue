<template>
  <div class="flex flex-col gap-2">
    <div class="flex justify-between mb-2">
      <label v-if="label" class="text-sm font-semibold text-slate-700">
        {{ label }}
      </label>
      <span class="text-sm font-bold text-primary">{{ modelValue }}</span>
    </div>

    <input
      type="range"
      :value="modelValue"
      :min="min"
      :max="max"
      :step="step"
      :disabled="disabled"
      :class="sliderClasses"
      @input="handleInput"
    />

    <p v-if="helperText" class="mt-1 text-xs text-slate-500">
      {{ helperText }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue: number
  min?: number
  max?: number
  step?: number
  label?: string
  helperText?: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  min: 0,
  max: 100,
  step: 1,
  disabled: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: number): void
}>()

const sliderClasses = computed(() => [
  'w-full h-2 rounded-lg appearance-none cursor-pointer accent-primary',
  'bg-slate-200',
  props.disabled && 'opacity-50 cursor-not-allowed'
])

const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', parseFloat(target.value))
}
</script>

<style scoped>
/* Custom slider styling for better cross-browser support */
input[type='range']::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #2463eb;
  cursor: pointer;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

input[type='range']::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #2463eb;
  cursor: pointer;
  border: none;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

input[type='range']:disabled::-webkit-slider-thumb {
  cursor: not-allowed;
}

input[type='range']:disabled::-moz-range-thumb {
  cursor: not-allowed;
}
</style>
