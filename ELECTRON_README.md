# RUIE - Electron Version

This is the Electron desktop wrapper for RUIE (RSI Launcher UI Editor).

## Architecture

```
RUIE (Electron)
├─ Electron Main Process (electron/src/main.js)
│  └─ Spawns & manages Flask server (server.py)
│     └─ REST API endpoints + security
├─ Electron Renderer (HTML/CSS/JS from public/)
│  └─ Single Page Application
│     └─ Communicates with Flask API
└─ IPC Bridge (electron/src/preload.js)
   └─ Secure communication between main & renderer
```

## Development

### Prerequisites
- Node.js 16+ (for Electron)
- Python 3.10+ (for Flask server)
- npm or yarn

### Setup

```bash
# Install Node dependencies
npm install

# Start development (Electron will spawn Flask automatically)
npm start
```

The app will:
1. Start the Flask server (python server.py)
2. Open Electron window loading http://127.0.0.1:5000
3. Open DevTools for debugging

### Project Structure

```
electron/
├─ src/
│  ├─ main.js          # Electron main process (spawns Flask)
│  ├─ preload.js       # IPC security bridge
│  └─ renderer/        # Renderer process files (if needed)
├─ scripts/
│  └─ check-server.js  # Validates server.py exists
└─ build/              # Compiled app (after build)

public/                # HTML/CSS/JS UI (unchanged from before)
server.py              # Flask backend (unchanged from before)
```

## Building for Distribution

### Windows Installer & Portable

```bash
# Build both NSIS installer and portable EXE
npm run build:win

# Build only portable EXE
npm run build:win-portable
```

Output will be in `dist/` folder:
- `RUIE Setup x.y.z.exe` - Installer version
- `RUIE x.y.z.exe` - Portable version

## Flask Server Management

The Flask server is automatically:
- Started when Electron app launches
- Stopped when Electron app closes
- Health-checked every 1 second (30 second startup timeout)

### Troubleshooting Flask Startup

If Flask fails to start:
1. Check `python --version` (must be 3.10+)
2. Check `requirements.txt` dependencies are installed
3. Check port 5000 is not in use
4. Check `server.py` exists and is valid Python

## Key Improvements Over PyQt5 Version

✓ **No overlay/rendering issues** - Uses native Chromium without PyQt5 complexity
✓ **Cleaner separation** - Main process (Node.js) vs Renderer process (Chromium)
✓ **Proven stack** - Electron used by Discord, VS Code, Slack
✓ **Better debugging** - Standard DevTools available in development
✓ **Smaller surface area** - Less code, less to debug
✓ **Standard practices** - Follows Electron security guidelines

## Security

- Context isolation enabled
- Node integration disabled
- Preload script validates all IPC
- Flask server uses existing security validation
- Sandbox enabled for renderer

## Notes

- Ensure `server.py` has all required dependencies in `requirements.txt`
- The Flask app runs on `http://127.0.0.1:5000` (localhost only)
- Electron automatically closes the Flask process on exit
- No PyQt5 or launcher.py - those files are deprecated
