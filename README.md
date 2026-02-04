# RUIE - RSI Launcher Customizer

Custom launcher theme editor for Roberts Space Industries Launcher. Change colors, add media, and personalize your launcher.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![Electron](https://img.shields.io/badge/Electron-29.0.0-blue)](https://www.electronjs.org/)
[![Flask](https://img.shields.io/badge/Flask-✓-green)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![CodeQL](https://github.com/Elegius/RUIE/actions/workflows/github-code-scanning/codeql/badge.svg?branch=main)](https://github.com/Elegius/RUIE/actions/workflows/github-code-scanning/codeql)
[![Security Scanning](https://github.com/Elegius/RUIE/actions/workflows/security-scan.yml/badge.svg?branch=main)](https://github.com/Elegius/RUIE/actions/workflows/security-scan.yml)

## Features

✨ **Customization**
- 🎨 Change launcher colors (unlimited combinations)
- 🖼️ Add custom images and videos  
- 🎵 Custom music and sounds
- 💾 Backup and restore themes

🎯 **User Experience**
- 5-step wizard with live preview
- 17 manufacturer presets with color grid layout
- Auto-detect RSI Launcher installation
- Backup and restore system
- Loading screen with detailed progress feedback
- Browser cache auto-clears on exit for fresh loads

🔒 **Security**
- XSS protection (sanitized HTML)
- Path traversal prevention
- Input validation on all endpoints
- No debug mode in production

## Quick Start

### Option 1: Portable Executable (Recommended)
```powershell
# Download RUIE Setup.exe or RUIE.exe and run
RUIE.exe
```
No Python installation needed. Works offline.

### Option 2: From Source
```powershell
git clone https://github.com/Elegius/RUIE.git
cd RUIE
npm install
pip install -r requirements.txt
npm start
```
Requires: Node.js 16+, Python 3.11+, Windows 10/11

## Documentation

| Document | Purpose |
|----------|---------|
| [CHANGELOG.md](CHANGELOG.md) | Version history, features, and known issues |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Architecture guide, module documentation, API reference |
| [SECURITY.md](SECURITY.md) | Security controls, vulnerability fixes, threat model |

## System Requirements

| Requirement | Version |
|-------------|---------|
| Windows | 10 or 11 |
| Node.js | 16+ (only for source mode) |
| Python | 3.11+ (only for source mode) |
| Memory | 256 MB minimum |
| Disk Space | ~500 MB for RSI Launcher |

## How to Use

1. **Launch the app**npm start
   - Run `RUIE.exe` (portable) or `python launcher.py` (source)
   
2. **Step 1: Detect & Extract Launcher**
   - App auto-detects RSI Launcher installation
   - Extract and decompile app.asar files
   - Manage multiple extractions

3. **Step 2: Customize Colors**
   - Choose from 17 manufacturer presets (displayed in compact grid), or
   - Pick custom colors from color picker
   - Live preview shows changes in real-time

4. **Step 3: Replace Media Files**
   - Upload custom images, videos, and backgrounds
   - Preview media before applying

5. **Step 4: Customize Music**
   - Add custom music tracks
   - Configure audio playback

6. **Step 5: Test, Export & Install**
   - **Test**: Launch modified launcher to preview theme
   - **Export**: Download theme configuration as JSON
   - **Install**: Apply theme to actual launcher (automatic backup created)

## Deployment Options

### Portable Executable
- No installation required
- Works from USB drive
- All dependencies bundled
- Single executable file
- **Download**: Get latest from [Releases](https://github.com/Elegius/RUIE/releases)

### Windows Installer (NSIS)
- Professional setup wizard
- Start menu integration
- Uninstall support
- Recommended for standard installation

### Source Code
- Full transparency
- Ideal for developers
- Requires Node.js 16+ and Python 3.11+
- Build your own executable

## Project Status

| Aspect | Status |
|--------|--------|
| **Version** | 0.2 Alpha |
| **Development** | Active |
| **Testing** | 21/21 tests passing ✅ |
| **Security** | Audited & secured ✅ |
| **Stability** | Production ready ✅ |

## Support

- 📖 **Issues?** Check [Troubleshooting](#troubleshooting) section
- 🐛 **Found a bug?** Open an [Issue](https://github.com/Elegius/RUIE/issues)
- 💡 **Have ideas?** [Discussions](https://github.com/Elegius/RUIE/discussions)

## Troubleshooting

### App won't start
- ✅ Run as Administrator
- ✅ Check Windows Defender/Antivirus (may require allowlist)
- ✅ Verify Node.js 16+ and Python 3.11+ installed (source mode only)

### Can't detect launcher
- ✅ Ensure RSI Launcher is installed (Star Citizen)
- ✅ Launch RSI Launcher once to initialize
- ✅ Try manual path selection in app

### Changes not appearing
- ✅ Restart RSI Launcher completely
- ✅ Clear launcher cache: `%appdata%/Roaming/RSI Launcher/`
- ✅ Verify admin privileges

See [DEVELOPMENT.md](DEVELOPMENT.md) for troubleshooting advanced issues.

## Architecture

```
RUIE
├── electron/
│   └── src/
│       ├── main.js          # Electron main process (spawns Flask)
│       └── preload.js       # IPC bridge for security
├── server.py                # Flask REST API (46 endpoints)
├── launcher_detector.py      # Auto-detect installations
├── color_replacer.py         # Color replacement engine
├── media_replacer.py         # Media file handler
├── asar_extractor.py         # ASAR archive extraction
├── public/
│   ├── app.js               # Single-page app (5-step wizard)
│   ├── index.html           # HTML template
│   └── styles.css           # CSS styling
├── package.json             # Node.js configuration
└── requirements.txt         # Python dependencies
```

**Architecture Flow:**
1. Electron (main.js) spawns Python Flask server
2. Flask serves REST API on localhost:5000
3. Electron window loads web UI from Flask
4. JavaScript app communicates with Flask API
5. Python backend handles file operations

See [DEVELOPMENT.md](DEVELOPMENT.md) for complete architecture documentation.

## Security

RUIE includes comprehensive security controls:
- ✅ XSS protection (HTML sanitization)
- ✅ Path traversal prevention
- ✅ Development Mode
```powershell
npm install
pip install -r requirements.txt
npm start
```

### Create Windows Installer
```powershell
npm run build:win
# Output: dist/RUIE Setup 1.0.0.exe
```

### Create Portable Executable
```powershell
npm run build:win-portable
# Output: dist/RUIE 1.0.0.exe
```powershell
pip install pyinstaller
pyinstaller RUIE.spec -y
# Output: dist/RUIE/RUIE.exe (5.99 MB)
```

### Create Windows Installer
```powershell
# Install Inno Setup 6
iscc setup.iss
# Output: RUIE-Setup.exe (~50 MB)
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for complete build instructions.

## LElectron** - Desktop application framework
- **Python** - Backend language
- **Flask** - REST API server
- **Node.js** - JavaScript runtime
- **electron-builder** - Application packag

⚠️ **RUIE is a fan-made, community project.** It is not affiliated with, endorsed by, or associated with Cloud Imperium Games, Roberts Space Industries, or Star Citizen.

- **For personal use only**
- Modify RSI Launcher at your own risk
- No warranty is provided
- Always keep backups of your launcher files

## Credits

Built with:
- **Python** - Core language
- **PyQt5** - Desktop UI framework
- **Flask** - REST API server
- **Waitress** - Production WSGI server
- **PyInstaller** - Executable building

---

**[⬆ Back to Top](#ruie---rsi-launcher-customizer)**
