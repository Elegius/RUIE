# DEVELOPMENT.md - Architecture & Developer Guide

**For developers building, extending, or understanding RUIE.**

## Architecture Overview

RUIE uses a hybrid architecture combining Electron and Python:

```
┌─────────────────────────────────────────────────────┐
│           User System (Windows 10/11)                │
└─────────────────────────────────────────────────────┘
              │
              ├─ RUIE.exe (Electron app)
              └─ npm start (Development mode)
                      │
    ┌───────────────────┴─────────────────┐
    │                                       │
┌─────────────────────────┐      ┌──────────────────┐
│  Electron Main Process   │      │  Flask Server    │
│  (Native Desktop Window) │      │  (HTTP REST API) │
│  - Window management     │      │  - 46 endpoints  │
│  - Spawns Flask server   │◄────►│  - File I/O      │
│  - Admin elevation       │      │  - Business logic│
│  - IPC bridge            │      │  - Error handling│
└─────────────────────────┘      └──────────────────┘
    │                                       │
    │                    ┌──────────────────┘
    │                    │
    └────────────────────┼────────────────┐
                         │                 │
                   ┌─────────────┐    ┌─────────────┐
                   │ app.js SPA  │    │  Public Folder
                   │ (localhost) │    │  (HTML/CSS) │
                   └─────────────┘    └─────────────┘
                         │
                         ├─ Color Replacement
                         ├─ Media Management
                         ├─ ASAR Extraction
                         ├─ Theme Backup/Restore
                         └─ Live Preview
```

### Execution Modes

**Production Mode** (Built Executable)
- Electron app packaged with electron-builder
- Flask server runs as spawned Python process
- All dependencies bundled
- No Node.js/Python installation needed

**Development Mode**
- Run with `npm start`
- Electron spawns Flask automatically
- Hot-reload enabled for frontend
- Full access to source code
- Requires Node.js 16+ and Python 3.11+

---

## Project Structure

```
RUIE/
├── electron/                    # Electron desktop app
│   ├── src/
│   │   ├── main.js             # Main process (spawns Flask)
│   │   └── preload.js          # IPC security bridge
│   └── scripts/
│       └── check-server.js     # Server validation
│
├── server.py                    # Flask REST API (46 endpoints)
├── launcher_detector.py         # Auto-detect RSI Launcher
├── color_replacer.py            # Color replacement engine
├── media_replacer.py            # Media file handler
├── asar_extractor.py            # ASAR archive extraction
│
├── public/                      # Web UI assets
│   ├── app.js                  # Single-page app (5-step wizard)
│   ├── index.html              # Main HTML page
│   ├── preview.html            # Live preview template
│   ├── styles.css              # Primary stylesheet
│   ├── assets/                 # Images, logos, videos
│   └── presets/                # Color mapping JSON files (17 manufacturers)
│
├── dist/                        # electron-builder output
│   ├── RUIE Setup 1.0.0.exe   # Installer
│   └── RUIE 1.0.0.exe         # Portable
│
├── node_modules/                # Node.js dependencies
├── package.json                 # Node.js configuration
├── requirements.txt             # Python dependencies
└── [documentation files]
```

---

## Core Modules

### electron/src/main.js - Electron Main Process

**Purpose**: Desktop application entry point and Flask server lifecycle

**Key Functions**
```javascript
function startFlaskServer()         # Spawn Python Flask server
function checkFlaskHealth()         # Health check Flask API
function waitForFlaskServer()       # Wait for server ready
function isRunningAsAdminWindows()  # Check admin privileges
function relaunchAsAdminWindows()   # Request UAC elevation
function createWindow()             # Create Electron window
```

**Key Features**
- Spawns Flask server as child process
- Admin privilege elevation via PowerShell
- Health check polling for Flask readiness
- IPC bridge for secure communication
- Graceful shutdown handling
- Development vs production mode detection

**Entry Point**
```javascript
app.whenReady().then(async () => {
    await startFlaskServer();
    await waitForFlaskServer();
    createWindow();
});
```

---

### server.py - Flask REST API

**Purpose**: Backend REST API with 46 endpoints for all operations

**Key Classes**
```python
class FlaskServer:
    """Flask application factory"""
```

**API Endpoints** (Organized by function)

**Session & Initialization** (4 endpoints)
```
GET  /api/init                      Initialize session
POST /api/init                      Save session config
GET  /api/config/save               Save theme configuration
GET  /api/config/export             Export theme as JSON
```

**Launcher Detection** (2 endpoints)
```
GET  /api/detect-launcher           Auto-detect RSI Launcher
POST /api/detect-launcher           Set custom launcher path
```

**ASAR Operations** (7 endpoints)
```
POST /api/extract                   Extract app.asar
POST /api/repack                    Repack modified ASAR
POST /api/compile-asar              Compile without installing
POST /api/install-asar              Compile and install (requires extractedPath)
GET  /api/extracted-list            List previous extractions
POST /api/use-extract               Load previous extraction
POST /api/delete-extract            Delete extraction folder
```

**Color Modifications** (4 endpoints)
```
GET  /api/colors                    Get available colors
POST /api/apply-colors              Apply color replacements
POST /api/preview-colors            Preview colors
GET  /api/color-schemes             List color schemes
```

**Media Management** (6 endpoints)
```
POST /api/apply-media               Apply media replacements
GET  /api/media-assets              Scan for media files
GET  /api/extracted-asset           Serve asset previews
POST /api/validate-media            Validate media files
GET  /api/media-formats             List supported formats
GET  /api/media-defaults            Get default media
```

**Backup & Restore** (5 endpoints)
```
GET  /api/backups                   List all backups
POST /api/backup                    Create backup
POST /api/restore                   Restore from backup
POST /api/delete-backup             Delete backup
GET  /api/backup-info               Get backup metadata
```

**Testing & Deployment** (9 endpoints)
```
POST /api/test-launcher             Test with temp ASAR (requires extractedPath)
POST /api/deploy-theme              Deploy theme permanently
GET  /api/test-status               Check test status
POST /api/test-rollback             Rollback test
GET  /api/extraction-changes        Detect changes
POST /api/validate-extraction       Validate extraction
POST /api/check-compatibility       Check launcher version
POST /api/clear-session             Clear all extractions
POST /api/open-extractions-folder   Open extractions directory
POST /api/open-backups-folder       Open backups directory
```

**Asset Routes** (8 endpoints)
```
GET  /assets/images/<path>          Serve image files
GET  /assets/videos/<path>          Serve video files
GET  /assets/musics/<path>          Serve audio files
GET  /assets/logos/<path>           Serve logo files
GET  /files/<path>                  Serve extracted files
GET  /presets/<path>                Serve color presets
GET  /health                        Health check
GET  /version                       Get API version
```

**Security Functions**
```python
def validate_path_safety(path)          # Prevent path traversal
def validate_file_upload(filename)      # Validate uploads
def validate_color_mapping(data)        # Validate color data
```

---

### launcher_detector.py - Launcher Detection

**Purpose**: Auto-detect RSI Launcher installation on Windows

**Key Class**
```python
class LauncherDetector:
    """Detect RSI Launcher installation"""
    
    def detect(self)                    # Auto-detect installation
    def get_launcher_paths(self)        # List detection paths
    def find_asar(path)                 # Recursive ASAR search
    def is_launcher_running()           # Check if launcher active
```

**Detection Strategy**
1. Check hardcoded common paths
2. Query Windows Registry
3. Breadth-first file search
4. Return first valid app.asar found

**Common Paths Checked**
```
C:\Program Files\Roberts Space Industries\StarCitizen\LIVE\data\p.k01
C:\Program Files (x86)\Roberts Space Industries\
C:\Users\[username]\AppData\Local\Roberts Space Industries\
...and 4 more registry-based paths
```

---

### color_replacer.py - Color Replacement Engine

**Purpose**: Find and replace color values in launcher theme

**Key Class**
```python
class ColorReplacer:
    """Color replacement in launcher files"""
    
    def apply_colors(colors)            # Apply color replacements
    def hex_to_rgb(hex_color)           # Convert hex to RGB
    def rgb_to_hex(rgb_color)           # Convert RGB to hex
```

**Supported Formats**
- Hex: `#FF5733`
- RGB: `(255, 87, 51)`
- CSS function: `rgb(255, 87, 51)`

**Process**
1. Extract default color values from JavaScript
2. Build color replacement map
3. Replace in all extracted files
4. Verify replacements successful

---

### media_replacer.py - Media File Management

**Purpose**: Replace media files (images, videos, audio) in launcher

**Key Class**
```python
class MediaReplacer:
    """Media file replacement"""
    
    def copy_media(source, dest)        # Copy media files
    def apply_media(media_data)         # Apply media replacements
    def validate_media(file_path)       # Validate media files
```

**Supported Formats**
- Images: PNG, JPG, WebP
- Videos: MP4, OGG, WebM
- Audio: OGG, MP3, WAV

---

### asar_extractor.py - ASAR Archive Extraction

**Purpose**: Extract and repack ASAR archives (pure Python, no Node.js)

**Key Class**
```python
class ASARExtractor:
    """ASAR archive handling"""
    
    def extract(asar_path, output_dir)  # Extract archive
    def repack(input_dir, output_path)  # Repack archive
```

**ASAR Format**
- Binary archive format used by Electron apps
- Header: metadata (paths, offsets)
- Data: concatenated file contents

**Pure Python Implementation**
- No external dependencies
- No Node.js required
- Standalone executable compatible

---

## API Documentation

### Request Format

**Headers**
```
Content-Type: application/json
X-CSRF-Token: [token]  # For state-changing operations
```

**Response Format**
```json
{
  "success": true,
  "data": { /* operation-specific data */ },
  "error": null,
  "timestamp": "2026-02-04T12:34:56Z"
}
```

### Example Endpoints

**Detect Launcher**
```
GET /api/detect-launcher

Response:
{
  "success": true,
  "data": {
    "asar_path": "C:\\...\\app.asar",
    "version": "1.0.0",
    "status": "ready"
  }
}
```

**Apply Colors**
```
POST /api/apply-colors

Request:
{
  "colors": {
    "#original_color": "#new_color",
    "#FF5733": "#00FF00"
  }
}

Response:
{
  "success": true,
  "data": {
    "replaced": 47,
    "files_modified": 12
  }
}
```

---

## Frontend Architecture

### app.js - Single-Page Application

**Purpose**: 5-step customization wizard interface

**Key Components**
```javascript
// Step navigation
currentPage                 // Track current step (1-5)
navigateToPage(step)        // Navigate between steps
state.extractedPath         // Currently loaded extraction path

// Color management
collectColorMappings()      // Collect from manual and preset grids
applyColors()              // Send colors to API
renderColorSections()       // Render color grid layout
selectColorForEditing()     // Open color editor

// Media management
updateMediaPreview()        // Update media preview
applyMedia()               // Send media to API

// Backup/Restore
createBackup()             // Save current state
restoreBackup()            // Load previous state
deleteBackup()             // Remove backup
loadBackupsList()          // Real-time backup list

// Extraction management
loadExtractedASARList()    // Load extraction list
useSelectedExtract()       // Load previous extraction
deleteExtractedASAR()      // Remove extraction

// Cache management
setupCacheClearingOnExit() // Clear localStorage, sessionStorage, IndexedDB on exit

// Loading screen
updateLoadingStatus()      // Update progress bar and status text
hideLoadingScreen()        // Hide loading screen after initialization

// Utility functions
formatFileSize()           # Human-readable sizes
showStatus()               # User feedback
fetchAPI()                 # API wrapper
```

**Wizard Steps**
1. **Prepare & Extract** - Launcher detection, ASAR extraction, backup/extraction management
2. **Customize Colors** - 17 manufacturer presets in grid layout, manual color mapping, live preview
3. **Replace Media** - Images, videos, backgrounds with validation
4. **Customize Music** - Audio playback configuration
5. **Test, Export & Install** - 3 action cards: Test launcher, Export JSON, Install theme

**State Management**
```javascript
state = {
  initialized: false,       // Whether ASAR has been extracted
  extracted: false,         // Whether extract directory is available
  colors: {},               // Current color selections
  media: {},                // User-selected media files
  music: [],                // Array of music files
  config: {},               // Theme configuration
  currentPage: 1,           // Current step (1-5)
  selectedExtractPath: null,// Track selected extraction
  extractedPath: null       // Currently loaded extraction path
}
```

---

## UI Features & Implementation

### Color Grid Layout

**Implementation**: Step 2 displays color presets in a responsive CSS Grid

**CSS Structure**
```css
.color-section-content {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 15px;
    padding: 15px;
}

.color-grid-item {
    display: flex;
    flex-direction: column;
    padding: 12px;
    background: rgba(22, 33, 62, 0.4);
    border: 1px solid rgba(0, 200, 255, 0.3);
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
}
```

**Features**
- Responsive grid adapts to panel width (40% of screen)
- Minimum column width: 120px
- Collapsible sections (Primary Colors, Neutral Colors, etc.)
- Color editor opens inline when clicking color preview
- Supports both preset and manual color mappings

### Loading Screen with Progress

**Implementation**: Inline script in index.html with progress tracking in app.js

**Progress Stages** (25 status messages, 0%-100%)
```
5%  - DOM ready
15% - Dependencies verified
25% - Starting initialization
26-34% - Loading presets
45% - Launcher detection complete
60% - Initialization complete
62-68% - Loading backups
74-80% - Loading extractions
90% - All data loaded
95% - Application ready
100% - Ready!
```

**Key Functions**
```javascript
updateLoadingStatus(message, percentage)  // Update progress bar
hideLoadingScreen()                       // Hide after init
setupCacheClearingOnExit()               // Clear cache on close
```

**Timeout Safety**
- 8-second timeout in promise chain
- 10-second absolute timeout fallback
- Ensures loading screen never hangs indefinitely

### Cache Management

**Auto-clearing on app exit**
```javascript
window.addEventListener('beforeunload', () => {
    localStorage.clear();           // Clear local storage
    sessionStorage.clear();         // Clear session storage
    // Clear IndexedDB databases
    // Clear service worker caches
});
```

**Server-side cache control**
```python
@app.after_request
def add_security_headers(response):
    # Prevent caching of HTML/JS
    if request.path.endswith(('.html', '.js')):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response
```

### Backup & Extraction Management

**Real-time polling**
```javascript
// Poll every 2 seconds for updates
setInterval(() => {
    if (!backupsPollInFlight) {
        loadBackupsList();
    }
}, 2000);
```

**Features**
- List updates automatically as files change
- Buttons below lists for "Open folder" actions
- Delete buttons with confirmation dialogs
- Metadata display (date, size, version)

---

## Building & Deployment

### Build Requirements
```
Python 3.11+
PyInstaller 6.18.0
Flask 2.3+
PyQt5 5.15+
Windows 10/11
```

Node.js 16+
Python 3.11+
Electron 29.0.0
electron-builder 24.6.0
Flask 2.3+
Windows 10/11
```

### Development Mode

**Install dependencies**
```powershell
npm install
pip install -r requirements.txt
```

**Run development server**
```powershell
npm start
```

This will:
1. Spawn Flask server on localhost:5000
2. Open Electron window
3. Load UI with hot-reload
4. Open DevTools (F12)

### Build Windows Installer

```powershell
npm run build:win
```

**Output**: `dist/RUIE Setup 1.0.0.exe` (NSIS installer)

### Build Portable Executable

```powershell
npm run build:win-portable
```

**Output**: `dist/RUIE 1.0.0.exe` (Standalone portable)

**electron-builder Configuration**
```json
{
  "appId": "com.elegius.ruie",
  "productName": "RUIE",
  "files": [
    "electron/src/**/*",
    "public/**/*",
    "server.py",
    "requirements.txt"
  ],
  "win": {
    "target": ["nsis", "portable"]
  }
}
```l wizard UI
- Start menu shortcuts
- Registry integration
- Uninstall support

---

## Security Implementation

### Security Controls Implemented

1. **XSS Protection**
   - HTML sanitization function
   - Escaped user input in DOM
   - CSP headers configured

2. **Path Traversal Prevention**
   - `validate_path_safety()` checks all paths
   - Prevents `../` navigation
   - Restricts to allowed directories

3. **Input Validation**
   - `validate_file_upload()` for files
   - `validate_color_mapping()` for colors
   - Type checking on all inputs

4. **CSRF Protection**
   - CSRF tokens on state-changing operations
   - Token validation before processing

5. **Debug Mode Disabled**
   - `debug=False` in production
   - Disabled Flask reloader in frozen mode
   - No stack traces exposed

6. **CORS Restricted**
   - Localhost only
   - `127.0.0.1:5000` only
   - No cross-origin requests

7. **File Upload Validation**
   - Size limits enforced
   - Type whitelist check
   - Safe filename validation

8. **Process Isolation**
   - Flask runs in separate thread/process
   - Limited subprocess execution
   - Safe subprocess argument lists

---

## Testing

### Test Coverage

✅ **Module Tests**
- All 5 core modules import successfully
- Zero syntax errors
- All functions present and callable

✅ **Functionality Tests**
- Color conversions: 7/7 passing
- Launcher detection: 7 paths found
- ASAR extraction: Extract method verified
- Flask configuration: Production verified
- Security functions: 3/3 active

✅ **Integration Tests**
- API endpoints responding
- Database operations working
- File I/O operations safe
- Error handling functional

### Running Tests

**From command line**
```powershell
python -m pytest tests/
```

**Manual testing**
```powershell
python launcher.py
# Test each step manually
```

---

## Troubleshooting

### Build Issues

**PyInstaller not found**
```powershell
pip install pyinstaller
```

**Missing dependencies**
```powershell
pip install -r requirements.txt
```

**ASAR extraction fails**
- Ensure Node.js installed (only for source mode)
- Check file permissions
- Verify ASAR file integrity

### Runtime Issues

**App won't start**
1. Run as Administrator
2. Check Windows Defender (may need allowlist)
3. Verify all dependencies installed
4. Check event viewer for errors

**Launcher not detected**
1. Ensure RSI Launcher installed
2. Launch RSI Launcher at least once
3. Try manual path in app UI
4. Check permissions on launcher folder

**Colors not applying**
1. Verify admin privileges
2. Restart RSI Launcher
3. Check color format (hex or RGB)
4. Review server logs for errors

### Performance Issues

**App runs slow**
1. Close other applications
2. Check available RAM (256 MB minimum)
3. Verify SSD has space for extractions
4. Consider Optimize settings in app

---

## Contributing

### Setup Development Environment

```powershell
# Clone repository
git clone https://github.com/Elegius/RUIE.git
cd RUIE

# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run development mode
python launcher.py
```

### Code Style

- Python: PEP 8
- JavaScript: Standard JS style
- Comments: Detailed docstrings
- Commit messages: Descriptive

### Pull Request Process

1. Fork repository
2. Create feature branch
3. Make changes with tests
4. Submit PR with description
5. Address review feedback

---

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [PyQt5 Documentation](https://doc.qt.io/qt-5/)
- [PyInstaller Documentation](https://pyinstaller.readthedocs.io/)
- [Python Documentation](https://docs.python.org/3/)

---

**Last Updated**: February 4, 2026  
**Version**: 0.2 Alpha  
**Maintainer**: Elegius