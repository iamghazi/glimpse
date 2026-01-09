<template>
  <header class="h-16 bg-surface border-b border-slate-200 flex items-center justify-between px-8 shrink-0 z-10">
    <div class="flex flex-col">
      <h2 class="text-xl font-bold text-slate-900 tracking-tight">Settings</h2>
      <p class="text-xs text-slate-500">
        Manage system configuration and API connections
      </p>
    </div>

    <div class="flex gap-3">
      <BaseButton
        variant="outline"
        icon="history"
        :disabled="!settingsStore.isDirty"
        @click="handleReset"
      >
        Reset to Defaults
      </BaseButton>

      <BaseButton
        variant="primary"
        icon="save"
        :loading="settingsStore.loading"
        :disabled="!settingsStore.isDirty || !settingsStore.isValid"
        @click="handleSave"
      >
        Save Changes
      </BaseButton>
    </div>
  </header>
</template>

<script setup lang="ts">
import BaseButton from '@/components/ui/BaseButton.vue'
import { useSettingsStore } from '@/stores/settings'

const settingsStore = useSettingsStore()

const handleSave = async () => {
  const success = await settingsStore.saveSettings()
  if (success) {
    console.log('Settings saved successfully')
  }
}

const handleReset = async () => {
  if (confirm('Are you sure you want to reset all settings to defaults? This cannot be undone.')) {
    await settingsStore.resetToDefaults()
  }
}
</script>
