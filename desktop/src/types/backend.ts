export interface HealthCheckResponse {
  status: string
  version: string
  qdrant_connected: boolean
}

export interface GCPConnectionStatus {
  connected: boolean
  error?: string
}
