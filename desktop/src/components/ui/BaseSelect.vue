<template>
  <div class="flex flex-col gap-2">
    <label v-if="label" :for="selectId" class="text-sm font-semibold text-slate-700">
      {{ label }}
      <span v-if="required" class="text-error">*</span>
    </label>

    <div class="relative">
      <select
        :id="selectId"
        :value="modelValue"
        :disabled="disabled"
        :class="selectClasses"
        @change="handleChange"
      >
        <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
        <option
          v-for="option in options"
          :key="getOptionValue(option)"
          :value="getOptionValue(option)"
        >
          {{ getOptionLabel(option) }}
        </option>
      </select>

      <div class="absolute inset-y-0 right-0 flex items-center px-3 pointer-events-none text-slate-500">
        <span class="material-symbols-outlined text-[20px]">expand_more</span>
      </div>
    </div>

    <p v-if="helperText && !error" class="text-xs text-slate-500">
      {{ helperText }}
    </p>
    <p v-if="error" class="text-xs text-error">
      {{ error }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type Option = string | { value: string | number; label: string }

interface Props {
  modelValue: string | number
  options: Option[]
  label?: string
  placeholder?: string
  helperText?: string
  error?: string
  required?: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  required: false,
  disabled: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | number): void
}>()

const selectId = computed(() =>
  props.label ? `select-${props.label.toLowerCase().replace(/\s+/g, '-')}` : undefined
)

const selectClasses = computed(() => [
  'h-11 w-full px-4 pr-10 rounded-lg text-sm appearance-none transition-all',
  'bg-white',
  'border',
  props.error
    ? 'border-error focus:ring-error/20 focus:border-error'
    : 'border-slate-300 focus:ring-primary/20 focus:border-primary',
  'focus:ring-2 focus:outline-none',
  'text-slate-900',
  props.disabled && 'opacity-50 cursor-not-allowed'
])

const getOptionValue = (option: Option): string | number => {
  return typeof option === 'string' ? option : option.value
}

const getOptionLabel = (option: Option): string => {
  return typeof option === 'string' ? option : option.label
}

const handleChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  emit('update:modelValue', target.value)
}
</script>
