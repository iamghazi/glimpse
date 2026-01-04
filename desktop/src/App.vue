<template>
  <div :class="{ dark: isDark }" class="h-screen overflow-hidden">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

const isDark = ref(false)

onMounted(() => {
  // Check for saved dark mode preference or system preference
  const savedDarkMode = localStorage.getItem('darkMode')
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches

  isDark.value = savedDarkMode === 'true' || (savedDarkMode === null && prefersDark)

  // Apply dark class
  if (isDark.value) {
    document.documentElement.classList.add('dark')
  }
})
</script>
