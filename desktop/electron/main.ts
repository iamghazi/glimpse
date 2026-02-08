import { app, BrowserWindow } from 'electron'
import path from 'node:path'
import {
  registerSettingsHandlers,
  registerBackendHandlers,
  registerDialogHandlers,
  registerVideoHandlers,
  registerSearchHandlers,
  registerChatHandlers,
  registerAgentHandlers
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
      contextIsolation: true,
      webSecurity: false // Allow file:// protocol for local video playback
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
  registerAgentHandlers()

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
