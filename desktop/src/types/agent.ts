// Agent session status
export type AgentStatus = 'idle' | 'planning' | 'executing' | 'evaluating' | 'complete' | 'failed'

// Evaluation result from backend
export interface EvaluationResult {
  duration_ok: boolean
  target_duration: number
  actual_duration: number
  render_success: boolean
  clip_count: number
  satisfied: boolean
  refinements: string[]
}

// Timeline clip in project
export interface TimelineClip {
  id: string
  video_id: string
  source_path: string
  cut_from: number
  cut_to: number
  order: number
  transition?: string
  transition_duration?: number
}

// Agent session
export interface AgentSession {
  id: string
  project_id: string
  user_request: string
  iteration: number
  max_iterations: number
  status: AgentStatus
  current_plan?: AgentPlan
  execution_results: ExecutionResult[]
  evaluation_results: EvaluationResult[]
  preview_path?: string
  final_output_path?: string
  created_at: string
  completed_at?: string
}

// Agent plan from planner
export interface AgentPlan {
  steps: PlanStep[]
  reasoning?: string
}

// Single step in plan
export interface PlanStep {
  tool: string
  params: Record<string, unknown>
  description?: string
}

// Execution result
export interface ExecutionResult {
  success: boolean
  project_id?: string
  preview_path?: string
  duration?: number
  clip_count?: number
  error?: string
}

// Edit request to backend
export interface EditRequest {
  request: string
}

// Edit response from backend
export interface EditResponse {
  session_id: string
  status: AgentStatus
  preview_path?: string
  iterations: number
  message: string
}

// SSE event types for real-time updates
export type AgentEventType =
  | 'status_change'
  | 'iteration_start'
  | 'plan_created'
  | 'tool_executing'
  | 'tool_completed'
  | 'evaluation_complete'
  | 'session_complete'
  | 'error'

export interface AgentEvent {
  type: AgentEventType
  session_id: string
  data: AgentEventData
  timestamp: string
}

export interface AgentEventData {
  status?: AgentStatus
  iteration?: number
  plan?: AgentPlan
  tool_name?: string
  tool_result?: unknown
  evaluation?: EvaluationResult
  preview_path?: string
  error?: string
  message?: string
}

// Activity log entry for UI
export interface ActivityLogEntry {
  id: string
  type: 'info' | 'success' | 'warning' | 'error' | 'tool'
  message: string
  timestamp: Date
  details?: string
}

// Helper to format status for display
export function formatAgentStatus(status: AgentStatus): string {
  const statusMap: Record<AgentStatus, string> = {
    idle: 'Ready',
    planning: 'Planning...',
    executing: 'Executing...',
    evaluating: 'Evaluating...',
    complete: 'Complete',
    failed: 'Failed'
  }
  return statusMap[status]
}

// Helper to get status color
export function getStatusColor(status: AgentStatus): string {
  const colorMap: Record<AgentStatus, string> = {
    idle: 'text-slate-500',
    planning: 'text-blue-500',
    executing: 'text-amber-500',
    evaluating: 'text-purple-500',
    complete: 'text-green-500',
    failed: 'text-red-500'
  }
  return colorMap[status]
}

// Helper to get status icon
export function getStatusIcon(status: AgentStatus): string {
  const iconMap: Record<AgentStatus, string> = {
    idle: 'hourglass_empty',
    planning: 'psychology',
    executing: 'play_circle',
    evaluating: 'fact_check',
    complete: 'check_circle',
    failed: 'error'
  }
  return iconMap[status]
}

// Helper to format duration
export function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
