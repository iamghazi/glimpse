import { contextBridge, ipcRenderer } from 'electron'
import type { AppSettings } from '../src/types/settings'
import type { HealthCheckResponse } from '../src/types/backend'

contextBridge.exposeInMainWorld('electron', {
  settings: {
    get: () => ipcRenderer.invoke('settings:get') as Promise<AppSettings>,
    save: (settings: AppSettings) => ipcRenderer.invoke('settings:save', settings) as Promise<void>,
    reset: () => ipcRenderer.invoke('settings:reset') as Promise<AppSettings>
  },
  backend: {
    health: () => ipcRenderer.invoke('backend:health') as Promise<HealthCheckResponse>,
    testConnection: () => ipcRenderer.invoke('backend:test-connection') as Promise<boolean>,
    getSettings: () => ipcRenderer.invoke('backend:get-settings') as Promise<AppSettings>,
    saveSettings: (settings: AppSettings) => ipcRenderer.invoke('backend:save-settings', settings) as Promise<void>
  },
  dialog: {
    selectDirectory: () => ipcRenderer.invoke('dialog:select-directory') as Promise<string | null>
  }
})
