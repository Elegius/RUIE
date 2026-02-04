# RUIE - RSI Launcher Customizer

Custom launcher theme editor for Roberts Space Industries Launcher. Change colors, add media, and personalize your launcher.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/PyQt5-✓-green)](https://pypi.org/project/PyQt5/)
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
- 6-step wizard with live preview
- 17 manufacturer presets
- Auto-detect RSI Launcher installation
- Backup and restore system

🔒 **Security**
- XSS protection (sanitized HTML)
- Path traversal prevention
- Input validation on all endpoints
- No debug mode in production

## Quick Start

### Option 1: Portable Executable (Recommended)
```powershell
# Download RUIE.exe and run
RUIE.exe
```
No installation needed. Works offline. ~6 MB file.

### Option 2: From Source
```powershell
git clone https://github.com/Elegius/RUIE.git
cd RUIE
pip install -r requirements.txt
python launcher.py
```
Requires: Python 3.11+, Windows 10/11

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
| Python | 3.11+ (only for source mode) |
| Memory | 256 MB minimum |
| Disk Space | ~500 MB for RSI Launcher |

## How to Use

1. **Launch the app**
   - Run `RUIE.exe` (portable) or `python launcher.py` (source)
   
2. **Step 1: Detect Launcher**
   - App auto-detects RSI Launcher installation
   - Select custom path if needed

3. **Step 2: Extract & Backup**
   - Extract launcher theme from app.asar
   - Creates automatic backup

4. **Step 3: Select Preset or Customize**
   - Choose from 17 manufacturer presets, or
   - Pick custom colors from color picker

5. **Step 4: Preview Changes**
   - Live preview shows how launcher will look
   - Adjust colors as needed

6. **Step 5: Apply & Test**
   - Apply changes to launcher
   - Restart RSI Launcher to see changes

7. **Step 6: Backup & Restore**
   - Manage theme backups
   - Restore previous themes anytime

## Deployment Options

### Portable EXE (5.99 MB)
- No installation required
- Works from USB drive
- All dependencies included
- Single executable file
- **Download**: Get latest from [Releases](https://github.com/Elegius/RUIE/releases)

### Windows Installer
- Professional setup wizard
- Start menu integration
- Uninstall support
- Recommended for corporate deployment

### Source Code
- Full transparency
- Ideal for developers
- Requires Python 3.11+
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
- ✅ Verify Python 3.11+ installed (source mode only)

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
├── launcher.py              # PyQt5 desktop window + Flask server
├── server.py                # REST API (44 endpoints)
├── launcher_detector.py      # Auto-detect installations
├── color_replacer.py         # Color replacement engine
├── media_replacer.py         # Media file handler
├── asar_extractor.py         # ASAR archive extraction
├── public/
│   ├── app.js               # Single-page app (6-step wizard)
│   ├── index.html           # HTML template
│   └── styles-modern.css    # CSS styling
└── setup.iss                # Windows installer config
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for complete architecture documentation.

## Security

RUIE includes comprehensive security controls:
- ✅ XSS protection (HTML sanitization)
- ✅ Path traversal prevention
- ✅ Input validation on all endpoints
- ✅ CSRF tokens for state changes
- ✅ Debug mode disabled in production
- ✅ CORS restricted to localhost
- ✅ File upload validation
- ✅ Process isolation

See [SECURITY.md](SECURITY.md) for detailed security documentation.

## Building from Source

### Create Portable EXE
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

## License

MIT License - See [LICENSE](LICENSE) for details

## Disclaimer

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
