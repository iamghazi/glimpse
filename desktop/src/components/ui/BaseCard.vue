<template>
  <div :class="cardClasses">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type Variant = 'default' | 'elevated' | 'outlined' | 'bordered'

interface Props {
  variant?: Variant
  padding?: 'none' | 'sm' | 'md' | 'lg'
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'xl'
  hover?: boolean
  clickable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  padding: 'md',
  rounded: 'xl',
  hover: false,
  clickable: false
})

const cardClasses = computed(() => {
  const base = ['bg-surface']

  const variants = {
    default: ['border border-slate-200'],
    elevated: ['shadow-lg shadow-slate-200/50'],
    outlined: ['border-2 border-slate-300'],
    bordered: ['border border-slate-200 shadow-sm']
  }

  const paddings = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6'
  }

  const rounded = {
    none: '',
    sm: 'rounded-sm',
    md: 'rounded-md',
    lg: 'rounded-lg',
    xl: 'rounded-xl'
  }

  return [
    ...base,
    ...variants[props.variant],
    paddings[props.padding],
    rounded[props.rounded],
    props.hover && 'hover:shadow-md transition-shadow',
    props.clickable && 'cursor-pointer'
  ]
})
</script>
