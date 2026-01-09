<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="buttonClasses"
    @click="handleClick"
  >
    <span v-if="loading" class="material-symbols-outlined text-[18px] animate-spin">
      progress_activity
    </span>
    <span v-else-if="icon" class="material-symbols-outlined text-[18px]" :class="{ 'fill-1': iconFilled }">
      {{ icon }}
    </span>
    <slot />
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type Variant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
type Size = 'sm' | 'md' | 'lg'

interface Props {
  variant?: Variant
  size?: Size
  icon?: string
  iconFilled?: boolean
  loading?: boolean
  disabled?: boolean
  type?: 'button' | 'submit' | 'reset'
  fullWidth?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  type: 'button',
  loading: false,
  disabled: false,
  iconFilled: false,
  fullWidth: false
})

const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void
}>()

const buttonClasses = computed(() => {
  const base = [
    'flex items-center justify-center gap-2 rounded-lg font-medium transition-colors',
    'focus:outline-none focus:ring-2 focus:ring-offset-2',
    props.fullWidth && 'w-full'
  ]

  // Size classes
  const sizeClasses = {
    sm: 'px-3 h-8 text-xs',
    md: 'px-4 h-9 text-sm',
    lg: 'px-5 h-11 text-base'
  }

  // Variant classes
  const variantClasses = {
    primary: [
      'bg-primary text-white shadow-sm shadow-primary/30',
      'hover:bg-primary-hover',
      'focus:ring-primary/20',
      'disabled:opacity-50 disabled:cursor-not-allowed'
    ],
    secondary: [
      'border border-secondary text-secondary',
      'hover:bg-secondary/5',
      'focus:ring-secondary/20',
      'disabled:opacity-50 disabled:cursor-not-allowed'
    ],
    outline: [
      'border border-slate-200',
      'text-slate-700',
      'hover:bg-slate-50',
      'focus:ring-slate-200',
      'disabled:opacity-50 disabled:cursor-not-allowed'
    ],
    ghost: [
      'text-slate-600',
      'hover:bg-slate-50',
      'focus:ring-slate-200',
      'disabled:opacity-50 disabled:cursor-not-allowed'
    ],
    danger: [
      'bg-error text-white shadow-sm shadow-error/30',
      'hover:bg-red-600',
      'focus:ring-error/20',
      'disabled:opacity-50 disabled:cursor-not-allowed'
    ]
  }

  return [...base, sizeClasses[props.size], ...variantClasses[props.variant]]
})

const handleClick = (event: MouseEvent) => {
  if (!props.disabled && !props.loading) {
    emit('click', event)
  }
}
</script>
