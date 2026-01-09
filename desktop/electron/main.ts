import { app, BrowserWindow } from 'electron'
import path from 'node:path'
import {
  registerSettingsHandlers,
  registerBackendHandlers,
  registerDialogHandlers,
  registerVideoHandlers,
  registerSearchHandlers,
  registerChatHandlers
} from './ipc'

let mainWindow: BrowserWindow | null = null

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 1024,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      nodeIntegration: false,
      contextIsolation: true
    },
    titleBarStyle: 'hiddenInset', // macOS style
    backgroundColor: '#f3f4f6'
  })

  // Load app
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'))
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

app.whenReady().then(async () => {
  // Register IPC handlers
  registerSettingsHandlers()
  registerBackendHandlers()
  registerDialogHandlers()
  registerVideoHandlers()
  registerSearchHandlers()
  registerChatHandlers()

  // Test backend connectivity on startup
  const axios = (await import('axios')).default
  console.log('[Main] Testing backend connectivity...')
  try {
    const response = await axios.get('http://localhost:8000/health', { timeout: 5000 })
    console.log('[Main] Backend is reachable:', response.data)
  } catch (error) {
    console.error('[Main] Backend is NOT reachable:', error)
  }

  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
