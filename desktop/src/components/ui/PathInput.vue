<template>
  <div class="flex flex-col gap-2">
    <label v-if="label" class="text-sm font-semibold text-slate-700">
      {{ label }}
      <span v-if="required" class="text-error">*</span>
    </label>

    <div class="flex gap-2">
      <input
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :class="inputClasses"
        @input="handleInput"
        class="flex-1"
      />

      <button
        type="button"
        :disabled="disabled"
        class="flex items-center justify-center gap-2 px-4 h-11 rounded-lg border border-slate-300 hover:bg-slate-50 text-slate-700 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
        @click="handleBrowse"
      >
        <span class="material-symbols-outlined text-[18px]">folder_open</span>
        Browse
      </button>
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

interface Props {
  modelValue: string
  label?: string
  placeholder?: string
  helperText?: string
  error?: string
  required?: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'e.g., ./data',
  required: false,
  disabled: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

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
  emit('update:modelValue', target.value)
}

const handleBrowse = async () => {
  try {
    const path = await window.electron.dialog.selectDirectory()
    if (path) {
      emit('update:modelValue', path)
    }
  } catch (error) {
    console.error('Failed to open directory picker:', error)
  }
}
</script>
