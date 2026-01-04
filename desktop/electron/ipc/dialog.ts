import { ipcMain, dialog } from 'electron'

export function registerDialogHandlers() {
  // Open directory picker
  ipcMain.handle('dialog:select-directory', async () => {
    const result = await dialog.showOpenDialog({
      properties: ['openDirectory', 'createDirectory']
    })

    if (result.canceled) {
      return null
    }

    return result.filePaths[0]
  })
}
