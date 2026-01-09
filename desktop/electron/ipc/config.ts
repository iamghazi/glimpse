/**
 * Centralized API configuration for IPC handlers
 */

// API Base URL - can be overridden via environment variable
export const API_BASE_URL = process.env.BACKEND_URL || 'http://localhost:8000'

// Axios default configuration
export const API_DEFAULTS = {
  timeout: 30000, // 30 seconds default timeout
  headers: {
    'Content-Type': 'application/json'
  }
}

// Timeout for long operations (in milliseconds)
export const LONG_OPERATION_TIMEOUT = 300000 // 5 minutes for video upload

// Connection retry configuration
export const RETRY_CONFIG = {
  maxRetries: 3,
  retryDelay: 1000, // 1 second
  backoffMultiplier: 2 // Exponential backoff
}
