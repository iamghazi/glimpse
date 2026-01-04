import type { AppSettings } from './settings'
import type { HealthCheckResponse } from './backend'

declare global {
  interface Window {
    electron: {
      settings: {
        get: () => Promise<AppSettings>
        save: (settings: AppSettings) => Promise<void>
        reset: () => Promise<AppSettings>
      }
      backend: {
        health: () => Promise<HealthCheckResponse>
        testConnection: () => Promise<boolean>
        getSettings: () => Promise<AppSettings>
        saveSettings: (settings: AppSettings) => Promise<void>
      }
      dialog: {
        selectDirectory: () => Promise<string | null>
      }
    }
  }
}

export {}
