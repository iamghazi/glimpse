<template>
  <div class="flex flex-col gap-2">
    <div v-if="label" class="flex items-center justify-between">
      <label :for="inputId" class="text-sm font-semibold text-slate-700">
        {{ label }}
        <span v-if="required" class="text-error">*</span>
      </label>
      <span
        v-if="badge"
        class="text-xs text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded"
      >
        {{ badge }}
      </span>
      <span
        v-if="tooltip"
        class="material-symbols-outlined text-[16px] text-slate-400 cursor-help"
        :title="tooltip"
      >
        info
      </span>
    </div>

    <input
      :id="inputId"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :min="min"
      :max="max"
      :step="step"
      :class="inputClasses"
      @input="handleInput"
      @blur="$emit('blur')"
      @focus="$emit('focus')"
    />

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

interface Props {
  modelValue: string | number
  label?: string
  type?: 'text' | 'number' | 'email' | 'password' | 'url'
  placeholder?: string
  helperText?: string
  error?: string
  required?: boolean
  disabled?: boolean
  badge?: string
  tooltip?: string
  min?: number
  max?: number
  step?: number | string
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  placeholder: '',
  required: false,
  disabled: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | number): void
  (e: 'blur'): void
  (e: 'focus'): void
}>()

const inputId = computed(() =>
  props.label ? `input-${props.label.toLowerCase().replace(/\s+/g, '-')}` : undefined
)

const inputClasses = computed(() => [
  'h-11 px-4 rounded-lg text-sm transition-all',
  'bg-white',
  'border',
  props.error
    ? 'border-error focus:ring-error/20 focus:border-error'
    : 'border-slate-300 focus:ring-primary/20 focus:border-primary',
  'focus:ring-2 focus:outline-none',
  'text-slate-900',
  'placeholder:text-slate-400',
  props.disabled && 'opacity-50 cursor-not-allowed'
])

const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  const value = props.type === 'number' ? parseFloat(target.value) || 0 : target.value
  emit('update:modelValue', value)
}
</script>
