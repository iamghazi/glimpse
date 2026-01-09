<template>
  <div class="flex flex-col gap-2">
    <div v-if="label || showPercentage" class="flex items-center justify-between">
      <span v-if="label" class="text-sm font-medium text-slate-700">
        {{ label }}
      </span>
      <span v-if="showPercentage" class="text-xs font-medium text-slate-500">
        {{ Math.round(percentage) }}%
      </span>
    </div>

    <div :class="trackClasses">
      <div
        :class="barClasses"
        :style="{ width: `${Math.min(100, Math.max(0, percentage))}%` }"
      >
        <div v-if="animated" class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse"></div>
      </div>
    </div>

    <p v-if="helperText" class="text-xs text-slate-500">
      {{ helperText }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type Variant = 'default' | 'success' | 'error' | 'warning' | 'info' | 'primary'
type Size = 'sm' | 'md' | 'lg'

interface Props {
  percentage: number
  variant?: Variant
  size?: Size
  label?: string
  helperText?: string
  showPercentage?: boolean
  animated?: boolean
  striped?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  showPercentage: false,
  animated: false,
  striped: false
})

const trackClasses = computed(() => {
  const sizes = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4'
  }

  return [
    'w-full bg-slate-200 rounded-full overflow-hidden',
    sizes[props.size]
  ]
})

const barClasses = computed(() => {
  const variants = {
    default: 'bg-slate-500',
    success: 'bg-success',
    error: 'bg-error',
    warning: 'bg-yellow-500',
    info: 'bg-blue-500',
    primary: 'bg-primary'
  }

  return [
    'h-full rounded-full transition-all duration-300 relative',
    variants[props.variant],
    props.striped && 'bg-gradient-to-r from-current to-current bg-[length:20px_20px]'
  ]
})
</script>
