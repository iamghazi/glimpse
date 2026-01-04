<template>
  <div :class="{ dark: isDark }" class="h-screen overflow-hidden">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useUIStore } from '@/stores/ui'

const uiStore = useUIStore()
const { darkMode: isDark } = storeToRefs(uiStore)

onMounted(() => {
  uiStore.initialize()
})
</script>
