<template>
  <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col h-full">
    <!-- Header -->
    <div class="px-5 py-4 border-b border-slate-100 flex items-center justify-between shrink-0">
      <div class="flex items-center gap-2">
        <span class="material-symbols-outlined text-slate-400">terminal</span>
        <h3 class="text-sm font-semibold text-slate-900">Activity Log</h3>
      </div>
      <span class="text-xs text-slate-400">{{ entries.length }} entries</span>
    </div>

    <!-- Log Entries -->
    <div ref="logContainer" class="flex-1 overflow-y-auto p-4 space-y-2 bg-slate-50/50">
      <div
        v-for="entry in entries"
        :key="entry.id"
        :class="[
          'flex items-start gap-2 px-3 py-2 rounded-lg text-xs',
          entryBgColor(entry.type)
        ]"
      >
        <span
          :class="[
            'material-symbols-outlined text-sm mt-0.5 shrink-0',
            entryIconColor(entry.type)
          ]"
        >
          {{ entryIcon(entry.type) }}
        </span>
        <div class="flex-1 min-w-0">
          <p :class="['font-medium', entryTextColor(entry.type)]">
            {{ entry.message }}
          </p>
          <p v-if="entry.details" class="text-slate-400 mt-1 font-mono text-[10px] truncate">
            {{ entry.details }}
          </p>
          <p class="text-slate-400 mt-0.5">
            {{ formatTime(entry.timestamp) }}
          </p>
        </div>
      </div>

      <!-- Empty State -->
      <div
        v-if="entries.length === 0"
        class="flex flex-col items-center justify-center py-8 text-slate-400"
      >
        <span class="material-symbols-outlined text-3xl mb-2">history</span>
        <p class="text-sm">No activity yet</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { ActivityLogEntry } from '@/types/agent'

interface Props {
  entries: ActivityLogEntry[]
}

const props = defineProps<Props>()

const logContainer = ref<HTMLElement | null>(null)

// Auto-scroll to bottom when new entries are added
watch(
  () => props.entries.length,
  async () => {
    await nextTick()
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  }
)

function entryIcon(type: ActivityLogEntry['type']): string {
  const iconMap: Record<ActivityLogEntry['type'], string> = {
    info: 'info',
    success: 'check_circle',
    warning: 'warning',
    error: 'error',
    tool: 'build'
  }
  return iconMap[type]
}

function entryIconColor(type: ActivityLogEntry['type']): string {
  const colorMap: Record<ActivityLogEntry['type'], string> = {
    info: 'text-blue-500',
    success: 'text-green-500',
    warning: 'text-amber-500',
    error: 'text-red-500',
    tool: 'text-purple-500'
  }
  return colorMap[type]
}

function entryTextColor(type: ActivityLogEntry['type']): string {
  const colorMap: Record<ActivityLogEntry['type'], string> = {
    info: 'text-slate-700',
    success: 'text-green-700',
    warning: 'text-amber-700',
    error: 'text-red-700',
    tool: 'text-purple-700'
  }
  return colorMap[type]
}

function entryBgColor(type: ActivityLogEntry['type']): string {
  const colorMap: Record<ActivityLogEntry['type'], string> = {
    info: 'bg-white border border-slate-100',
    success: 'bg-green-50 border border-green-100',
    warning: 'bg-amber-50 border border-amber-100',
    error: 'bg-red-50 border border-red-100',
    tool: 'bg-purple-50 border border-purple-100'
  }
  return colorMap[type]
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  })
}
</script>
