const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const isDev = require('electron-is-dev');
const axios = require('axios');

let mainWindow;
let flaskProcess;
const FLASK_URL = 'http://127.0.0.1:5000';
const FLASK_PORT = 5000;
const HEALTH_CHECK_INTERVAL = 1000;
const HEALTH_CHECK_TIMEOUT = 30000;

/**
 * Check if Flask server is running
 */
async function checkFlaskHealth() {
  try {
    const response = await axios.get(`${FLASK_URL}/api/status`, { timeout: 2000 });
    return response.status === 200;
  } catch {
    return false;
  }
}

/**
 * Wait for Flask server to be ready
 */
async function waitForFlaskServer() {
  const startTime = Date.now();
  
  while (Date.now() - startTime < HEALTH_CHECK_TIMEOUT) {
    if (await checkFlaskHealth()) {
      console.log('[ELECTRON] Flask server is ready');
      return true;
    }
    await new Promise(resolve => setTimeout(resolve, HEALTH_CHECK_INTERVAL));
  }
  
  throw new Error('Flask server failed to start within timeout');
}

/**
 * Spawn Flask server process
 */
function startFlaskServer() {
  return new Promise((resolve, reject) => {
    try {
      console.log('[ELECTRON] Starting Flask server...');
      
      // Determine the path to server.py
      // In development: ./server.py
      // In production (built with PyInstaller): bundled inside app
      let serverPath;
      
      if (isDev) {
        // Development: server.py is in root of project
        serverPath = path.join(__dirname, '../../server.py');
      } else {
        // Production: PyInstaller bundle
        // Adjust this path based on how you bundle server.py
        serverPath = path.join(process.resourcesPath, 'server.py');
      }
      
      // Spawn Python process running Flask server
      flaskProcess = spawn('python', [serverPath], {
        stdio: ['ignore', 'pipe', 'pipe'],
        detached: false,
        windowsHide: true,
        env: {
          ...process.env,
          FLASK_ENV: isDev ? 'development' : 'production',
          FLASK_PORT: FLASK_PORT,
        }
      });
      
      let outputBuffer = '';
      let errorBuffer = '';
      
      // Capture output for debugging
      flaskProcess.stdout.on('data', (data) => {
        outputBuffer += data.toString();
        if (outputBuffer.includes('[FLASK]') || outputBuffer.includes('Running on')) {
          console.log('[FLASK]', data.toString().trim());
        }
      });
      
      flaskProcess.stderr.on('data', (data) => {
        errorBuffer += data.toString();
        console.error('[FLASK ERROR]', data.toString().trim());
      });
      
      flaskProcess.on('error', (err) => {
        console.error('[ELECTRON] Failed to start Flask server:', err);
        reject(err);
      });
      
      flaskProcess.on('exit', (code, signal) => {
        console.log(`[FLASK] Server exited with code ${code} (signal: ${signal})`);
      });
      
      // Wait for server to be ready
      waitForFlaskServer()
        .then(() => resolve(flaskProcess))
        .catch(reject);
      
    } catch (error) {
      console.error('[ELECTRON] Error spawning Flask:', error);
      reject(error);
    }
  });
}

/**
 * Create main application window
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 1024,
    minHeight: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js'),
      sandbox: true
    },
    icon: path.join(__dirname, '../../assets/logos/icon.ico')
  });
  
  // Load Flask app
  const url = isDev 
    ? `${FLASK_URL}` 
    : `${FLASK_URL}`;
  
  mainWindow.loadURL(url);
  
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }
  
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
  
  return mainWindow;
}

/**
 * App event handlers
 */
app.on('ready', async () => {
  try {
    console.log('[ELECTRON] App ready, starting Flask server...');
    await startFlaskServer();
    console.log('[ELECTRON] Flask server started, creating window...');
    createWindow();
  } catch (error) {
    console.error('[ELECTRON] Failed to start application:', error);
    app.quit();
  }
});

app.on('window-all-closed', () => {
  console.log('[ELECTRON] All windows closed, quitting...');
  
  // Kill Flask process
  if (flaskProcess) {
    try {
      console.log('[ELECTRON] Stopping Flask server...');
      flaskProcess.kill();
    } catch (error) {
      console.error('[ELECTRON] Error killing Flask process:', error);
    }
  }
  
  // On macOS, keep app in dock until user explicitly quits
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

/**
 * IPC handlers for Electron-to-Backend communication
 */
ipcMain.handle('app:version', () => {
  return app.getVersion();
});

ipcMain.handle('app:isDev', () => {
  return isDev;
});

/**
 * Handle any uncaught exceptions
 */
process.on('uncaughtException', (error) => {
  console.error('[ELECTRON] Uncaught exception:', error);
});
