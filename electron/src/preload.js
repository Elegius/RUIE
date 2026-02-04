const { contextBridge, ipcRenderer } = require('electron');

/**
 * Preload script for Electron security
 * Exposes a limited API to the renderer process
 */

contextBridge.exposeInMainWorld('electronAPI', {
  // App info
  getVersion: () => ipcRenderer.invoke('app:version'),
  isDev: () => ipcRenderer.invoke('app:isDev'),
  
  // Logging
  log: (message) => console.log('[RENDERER]', message),
  error: (message) => console.error('[RENDERER]', message),
});
