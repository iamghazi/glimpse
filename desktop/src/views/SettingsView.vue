<template>
  <div class="flex h-screen bg-background">
    <!-- Sidebar -->
    <AppSidebar />

    <!-- Main Content Area -->
    <main class="flex-1 flex flex-col h-full overflow-hidden relative">
      <!-- Settings Header -->
      <SettingsHeader />

      <!-- Scrollable Content -->
      <div class="flex-1 overflow-y-auto p-8 pb-24">
        <div class="max-w-4xl mx-auto flex flex-col gap-8">
          <!-- Alert Banner -->
          <AlertBanner />

          <!-- Google Cloud API Section -->
          <GoogleCloudSection />

          <!-- Video Processing Section -->
          <VideoProcessingSection />

          <!-- Search & Embedding Section -->
          <SearchEmbeddingSection />

          <!-- Data Storage Section -->
          <DataStorageSection />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import SettingsHeader from '@/components/settings/SettingsHeader.vue'
import AlertBanner from '@/components/settings/AlertBanner.vue'
import GoogleCloudSection from '@/components/settings/GoogleCloudSection.vue'
import VideoProcessingSection from '@/components/settings/VideoProcessingSection.vue'
import SearchEmbeddingSection from '@/components/settings/SearchEmbeddingSection.vue'
import DataStorageSection from '@/components/settings/DataStorageSection.vue'
import { useSettingsStore } from '@/stores/settings'
import { useBackendStore } from '@/stores/backend'

const settingsStore = useSettingsStore()
const backendStore = useBackendStore()

onMounted(async () => {
  // Load settings on mount
  await settingsStore.loadSettings()

  // Check backend health
  await backendStore.checkHealth()
})
</script>
