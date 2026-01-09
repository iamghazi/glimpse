<template>
  <span :class="badgeClasses">
    <span v-if="icon" class="material-symbols-outlined text-[14px]">
      {{ icon }}
    </span>
    <slot />
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type Variant = 'default' | 'success' | 'error' | 'warning' | 'info' | 'primary' | 'secondary'
type Size = 'sm' | 'md' | 'lg'

interface Props {
  variant?: Variant
  size?: Size
  icon?: string
  dot?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  size: 'md',
  dot: false
})

const badgeClasses = computed(() => {
  const base = [
    'inline-flex items-center gap-1 font-medium rounded-full',
    'transition-colors'
  ]

  const sizes = {
    sm: 'px-2 py-0.5 text-[10px]',
    md: 'px-2.5 py-1 text-xs',
    lg: 'px-3 py-1.5 text-sm'
  }

  const variants = {
    default: 'bg-slate-100 text-slate-700',
    success: 'bg-green-100 text-green-700',
    error: 'bg-red-100 text-red-700',
    warning: 'bg-yellow-100 text-yellow-700',
    info: 'bg-blue-100 text-blue-700',
    primary: 'bg-primary/10 text-primary',
    secondary: 'bg-secondary/10 text-secondary'
  }

  return [
    ...base,
    sizes[props.size],
    variants[props.variant]
  ]
})
</script>
