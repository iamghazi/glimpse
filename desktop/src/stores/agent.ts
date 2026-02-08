import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  AgentSession,
  AgentStatus,
  AgentEvent,
  ActivityLogEntry,
  EvaluationResult
} from '@/types/agent'

export const useAgentStore = defineStore('agent', () => {
  // State
  const session = ref<AgentSession | null>(null)
  const status = ref<AgentStatus>('idle')
  const loading = ref(false)
  const error = ref<string | null>(null)
  const activityLog = ref<ActivityLogEntry[]>([])
  const previewUrl = ref<string | null>(null)

  // SSE connection
  let eventSource: EventSource | null = null

  // Computed
  const isActive = computed(() =>
    ['planning', 'executing', 'evaluating'].includes(status.value)
  )

  const currentIteration = computed(() => session.value?.iteration ?? 0)
  const maxIterations = computed(() => session.value?.max_iterations ?? 5)

  const progressPercent = computed(() => {
    if (!session.value) return 0
    // If complete, always show 100%
    if (status.value === 'complete') return 100
    if (status.value === 'failed') return 0

    const iterationProgress = (currentIteration.value / maxIterations.value) * 100
    // Add sub-progress based on status within iteration
    const statusProgress: Record<AgentStatus, number> = {
      idle: 0,
      planning: 10,
      executing: 50,
      evaluating: 80,
      complete: 100,
      failed: 0
    }
    const subProgress = (statusProgress[status.value] / 100) * (100 / maxIterations.value)
    return Math.min(iterationProgress + subProgress, 100)
  })

  const latestEvaluation = computed((): EvaluationResult | null => {
    if (!session.value || session.value.evaluation_results.length === 0) {
      return null
    }
    return session.value.evaluation_results[session.value.evaluation_results.length - 1]
  })

  const hasPreview = computed(() => !!previewUrl.value)

  // Actions
  function addLogEntry(
    type: ActivityLogEntry['type'],
    message: string,
    details?: string
  ) {
    activityLog.value.push({
      id: `log-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type,
      message,
      timestamp: new Date(),
      details
    })
  }

  async function startEdit(request: string) {
    if (isActive.value) {
      error.value = 'An edit session is already in progress'
      return
    }

    // Reset state
    session.value = null
    status.value = 'planning'
    loading.value = true
    error.value = null
    activityLog.value = []
    previewUrl.value = null

    addLogEntry('info', `Starting edit: "${request}"`)

    try {
      const response = await window.electron.agent.startEdit({ request })

      session.value = {
        id: response.session_id,
        project_id: '',
        user_request: request,
        iteration: response.iterations || 1,
        max_iterations: 5,
        status: response.status,
        execution_results: [],
        evaluation_results: [],
        preview_path: response.preview_path,
        created_at: new Date().toISOString()
      }

      status.value = response.status

      if (response.preview_path) {
        previewUrl.value = getVideoUrl(response.preview_path)
        addLogEntry('success', 'Preview generated')
      }

      if (response.status === 'complete') {
        addLogEntry('success', response.message)
      } else if (response.status === 'failed') {
        addLogEntry('error', response.message)
        error.value = response.message
      }

      // Start SSE for real-time updates if session is still active
      if (isActive.value) {
        connectToSSE(response.session_id)
      }
    } catch (err) {
      status.value = 'failed'
      error.value = err instanceof Error ? err.message : 'Failed to start edit session'
      addLogEntry('error', error.value)
    } finally {
      loading.value = false
    }
  }

  function connectToSSE(sessionId: string) {
    // Close existing connection
    if (eventSource) {
      eventSource.close()
    }

    // Connect to SSE endpoint
    const baseUrl = 'http://localhost:8000'
    eventSource = new EventSource(`${baseUrl}/agent/sessions/${sessionId}/events`)

    eventSource.onmessage = (event) => {
      try {
        const agentEvent: AgentEvent = JSON.parse(event.data)
        handleAgentEvent(agentEvent)
      } catch (err) {
        console.error('Failed to parse SSE event:', err)
      }
    }

    eventSource.onerror = () => {
      console.error('SSE connection error')
      eventSource?.close()
      eventSource = null
    }
  }

  function handleAgentEvent(event: AgentEvent) {
    const { type, data } = event

    switch (type) {
      case 'status_change':
        if (data.status) {
          status.value = data.status
          addLogEntry('info', `Status: ${data.status}`)
        }
        break

      case 'iteration_start':
        if (session.value && data.iteration) {
          session.value.iteration = data.iteration
          addLogEntry('info', `Starting iteration ${data.iteration}`)
        }
        break

      case 'plan_created':
        addLogEntry('info', 'Plan created', JSON.stringify(data.plan, null, 2))
        if (session.value && data.plan) {
          session.value.current_plan = data.plan
        }
        break

      case 'tool_executing':
        addLogEntry('tool', `Executing: ${data.tool_name}`)
        break

      case 'tool_completed':
        addLogEntry('success', `Completed: ${data.tool_name}`)
        break

      case 'evaluation_complete':
        if (data.evaluation) {
          if (session.value) {
            session.value.evaluation_results.push(data.evaluation)
          }
          const evalMsg = data.evaluation.satisfied
            ? 'Evaluation passed'
            : `Evaluation needs refinement: ${data.evaluation.refinements.join(', ')}`
          addLogEntry(data.evaluation.satisfied ? 'success' : 'warning', evalMsg)
        }
        break

      case 'session_complete':
        status.value = 'complete'
        if (data.preview_path) {
          previewUrl.value = getVideoUrl(data.preview_path)
        }
        addLogEntry('success', data.message || 'Edit complete')
        disconnectSSE()
        break

      case 'error':
        status.value = 'failed'
        error.value = data.error || 'Unknown error'
        addLogEntry('error', error.value)
        disconnectSSE()
        break
    }
  }

  function disconnectSSE() {
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
  }

  async function approveSession() {
    if (!session.value) return

    loading.value = true
    addLogEntry('info', 'Rendering final video...')

    try {
      const response = await window.electron.agent.approveSession(session.value.id)
      if (response.output_path) {
        session.value.final_output_path = response.output_path
        addLogEntry('success', `Final video saved: ${response.output_path}`)
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to render final video'
      addLogEntry('error', error.value)
    } finally {
      loading.value = false
    }
  }

  async function provideFeedback(feedback: string) {
    if (!session.value) return

    loading.value = true
    status.value = 'planning'
    addLogEntry('info', `Feedback: "${feedback}"`)

    try {
      const response = await window.electron.agent.provideFeedback(
        session.value.id,
        feedback
      )

      status.value = response.status
      if (response.preview_path) {
        previewUrl.value = getVideoUrl(response.preview_path)
      }

      if (response.status === 'complete') {
        addLogEntry('success', response.message)
      }

      // Reconnect SSE if still active
      if (isActive.value) {
        connectToSSE(session.value.id)
      }
    } catch (err) {
      status.value = 'failed'
      error.value = err instanceof Error ? err.message : 'Failed to process feedback'
      addLogEntry('error', error.value)
    } finally {
      loading.value = false
    }
  }

  function cancelSession() {
    disconnectSSE()
    status.value = 'idle'
    addLogEntry('warning', 'Session cancelled')
  }

  function reset() {
    disconnectSSE()
    session.value = null
    status.value = 'idle'
    loading.value = false
    error.value = null
    activityLog.value = []
    previewUrl.value = null
  }

  // Helper to get video URL
  function getVideoUrl(filePath: string): string {
    if (filePath.startsWith('http')) {
      return filePath
    }
    // Backend serves exports at /exports/ - extract filename from path like "data/exports/xxx.mp4"
    if (filePath.includes('/exports/')) {
      const filename = filePath.split('/exports/').pop()
      return `http://localhost:8000/exports/${filename}`
    }
    // Fallback to exports endpoint with just the filename
    const filename = filePath.split('/').pop()
    return `http://localhost:8000/exports/${filename}`
  }

  return {
    // State
    session,
    status,
    loading,
    error,
    activityLog,
    previewUrl,

    // Computed
    isActive,
    currentIteration,
    maxIterations,
    progressPercent,
    latestEvaluation,
    hasPreview,

    // Actions
    startEdit,
    approveSession,
    provideFeedback,
    cancelSession,
    reset,
    addLogEntry
  }
})
