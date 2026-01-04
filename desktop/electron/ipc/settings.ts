import { ipcMain } from 'electron'
import { configStore, defaultSettings } from '../store/config'
import type { AppSettings } from '../../src/types/settings'

export function registerSettingsHandlers() {
  // Get settings from electron-store
  ipcMain.handle('settings:get', async () => {
    return configStore.get('settings')
  })

  // Save settings to electron-store
  ipcMain.handle('settings:save', async (_, settings: AppSettings) => {
    configStore.set('settings', settings)
  })

  // Reset settings to defaults
  ipcMain.handle('settings:reset', async () => {
    configStore.set('settings', defaultSettings)
    return defaultSettings
  })
}
