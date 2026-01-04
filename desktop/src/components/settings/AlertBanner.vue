<template>
  <div
    v-if="!settingsStore.hasGCPConfigured"
    class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-xl border border-red-200 bg-red-50 dark:bg-red-900/10 dark:border-red-900/30"
  >
    <div class="flex gap-4">
      <div class="mt-1 sm:mt-0 p-2 bg-red-100 dark:bg-red-900/30 rounded-full text-error shrink-0">
        <span class="material-symbols-outlined">warning</span>
      </div>
      <div class="flex flex-col gap-1">
        <h3 class="text-slate-900 dark:text-white text-base font-bold">
          Configuration Required
        </h3>
        <p class="text-slate-600 dark:text-slate-400 text-sm">
          Please set up your Google Cloud Project credentials to start indexing your video library.
        </p>
      </div>
    </div>
    <button
      class="shrink-0 px-4 h-9 rounded-lg bg-white dark:bg-slate-800 border border-red-200 dark:border-red-900/30 text-error text-sm font-semibold shadow-sm hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
      @click="scrollToGCPSection"
    >
      Configure Now
    </button>
  </div>
</template>

<script setup lang="ts">
import { useSettingsStore } from '@/stores/settings'

const settingsStore = useSettingsStore()

const scrollToGCPSection = () => {
  const gcpSection = document.getElementById('google-cloud-section')
  if (gcpSection) {
    gcpSection.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}
</script>
