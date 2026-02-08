<template>
  <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
    <!-- Header -->
    <div class="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div
          :class="[
            'w-10 h-10 rounded-lg flex items-center justify-center',
            statusBgColor
          ]"
        >
          <span
            :class="['material-symbols-outlined text-xl', statusColor, isActive ? 'animate-pulse' : '']"
          >
            {{ statusIcon }}
          </span>
        </div>
        <div>
          <h3 class="text-sm font-semibold text-slate-900">{{ statusText }}</h3>
          <p class="text-xs text-slate-500">
            Iteration {{ currentIteration }} of {{ maxIterations }}
          </p>
        </div>
      </div>
      <div v-if="isActive" class="flex items-center gap-2">
        <div class="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></div>
        <span class="text-xs font-medium text-amber-600">Processing</span>
      </div>
    </div>

    <!-- Progress Bar -->
    <div class="px-5 py-3 bg-slate-50/50">
      <div class="flex items-center justify-between text-xs text-slate-500 mb-2">
        <span>Progress</span>
        <span>{{ Math.round(progressPercent) }}%</span>
      </div>
      <div class="h-2 bg-slate-200 rounded-full overflow-hidden">
        <div
          class="h-full bg-gradient-to-r from-primary to-blue-400 rounded-full transition-all duration-500"
          :style="{ width: `${progressPercent}%` }"
        ></div>
      </div>
    </div>

    <!-- Evaluation Summary (if available) -->
    <div v-if="evaluation" class="px-5 py-3 border-t border-slate-100">
      <div class="flex items-center gap-2 mb-2">
        <span class="material-symbols-outlined text-sm text-slate-400">analytics</span>
        <span class="text-xs font-semibold text-slate-600 uppercase tracking-wider">
          Evaluation
        </span>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div class="flex items-center gap-2">
          <span
            :class="[
              'material-symbols-outlined text-sm',
              evaluation.duration_ok ? 'text-green-500' : 'text-red-500'
            ]"
          >
            {{ evaluation.duration_ok ? 'check_circle' : 'cancel' }}
          </span>
          <span class="text-xs text-slate-600">
            Duration: {{ formatDuration(evaluation.actual_duration) }}
            <span class="text-slate-400">/ {{ formatDuration(evaluation.target_duration) }}</span>
          </span>
        </div>
        <div class="flex items-center gap-2">
          <span
            :class="[
              'material-symbols-outlined text-sm',
              evaluation.render_success ? 'text-green-500' : 'text-red-500'
            ]"
          >
            {{ evaluation.render_success ? 'check_circle' : 'cancel' }}
          </span>
          <span class="text-xs text-slate-600">
            Render: {{ evaluation.render_success ? 'Success' : 'Failed' }}
          </span>
        </div>
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-sm text-blue-500">movie</span>
          <span class="text-xs text-slate-600">
            Clips: {{ evaluation.clip_count }}
          </span>
        </div>
        <div class="flex items-center gap-2">
          <span
            :class="[
              'material-symbols-outlined text-sm',
              evaluation.satisfied ? 'text-green-500' : 'text-amber-500'
            ]"
          >
            {{ evaluation.satisfied ? 'thumb_up' : 'pending' }}
          </span>
          <span class="text-xs text-slate-600">
            {{ evaluation.satisfied ? 'Satisfied' : 'Needs Refinement' }}
          </span>
        </div>
      </div>

      <!-- Refinements (if any) -->
      <div v-if="evaluation.refinements.length > 0" class="mt-3">
        <div class="text-xs font-medium text-slate-500 mb-1">Refinements needed:</div>
        <ul class="text-xs text-slate-600 space-y-1">
          <li
            v-for="(refinement, idx) in evaluation.refinements"
            :key="idx"
            class="flex items-start gap-1.5"
          >
            <span class="material-symbols-outlined text-amber-500 text-xs mt-0.5">arrow_right</span>
            {{ refinement }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { EvaluationResult, AgentStatus } from '@/types/agent'
import { formatDuration, getStatusIcon, getStatusColor, formatAgentStatus } from '@/types/agent'

interface Props {
  status: AgentStatus
  currentIteration: number
  maxIterations: number
  progressPercent: number
  evaluation?: EvaluationResult | null
}

const props = defineProps<Props>()

const isActive = computed(() =>
  ['planning', 'executing', 'evaluating'].includes(props.status)
)

const statusText = computed(() => formatAgentStatus(props.status))
const statusIcon = computed(() => getStatusIcon(props.status))
const statusColor = computed(() => getStatusColor(props.status))

const statusBgColor = computed(() => {
  const bgMap: Record<AgentStatus, string> = {
    idle: 'bg-slate-100',
    planning: 'bg-blue-50',
    executing: 'bg-amber-50',
    evaluating: 'bg-purple-50',
    complete: 'bg-green-50',
    failed: 'bg-red-50'
  }
  return bgMap[props.status]
})
</script>
