# Quick Start Guide - RUIE v0.2 Alpha

⚠️ **DISCLAIMER**: RUIE is a fan-made project NOT affiliated with Cloud Imperium Games or Star Citizen. Use at your own risk per CIG's Terms of Service.

✅ **SECURITY STATUS**: All vulnerabilities have been fixed. This release is safe for distribution.

💡 **DEVELOPMENT NOTE**: This application was developed with AI assistance using GitHub Copilot (Claude Haiku 4.5).

---

## 📦 Installation Options

### Option 1: Windows Installer (Recommended for Most Users)
**Easiest and most professional method**

1. Download `RUIE-0.2-Alpha-Installer.exe`
2. Double-click to run the installer
3. Click "Yes" when Windows asks for admin permission
4. Follow the wizard and choose installation location
5. Done! App will launch automatically
6. Creates Start Menu shortcuts

**Best for:** End users, professional distribution, automatic updates

---

### Option 2: Portable Executable (No Installation)
**Fastest way to get started**

1. Download `RUIE.exe` from `dist/` folder
2. Place anywhere (USB drive, Desktop, etc.)
3. Double-click `RUIE.exe`
4. Click "Yes" when UAC prompts for admin
5. Watch the progress bar as the app initializes (5-15 seconds)
6. Main application launches when progress reaches 100%

**Best for:** Quick testing, USB portability, temporary use

**What to Expect**:
- **5-15 second startup** with visual progress feedback
- **Progress bar** showing real-time initialization status
- **Status messages** indicating what's being loaded ("Loading dependencies...", "Starting server...", etc.)
- **Animated indicators** for each startup step

---

### Option 3: Run from Source Code
**For developers and advanced users**

```bash
# Navigate to project directory
cd path\to\RUIE

# Install dependencies
pip install -r requirements.txt

# Launch the app
python launcher.py

# OR use the batch file for auto-admin elevation
run.bat
```

**Best for:** Development, customization, contributing

---

### Option 4: Build Your Own Installer
**For custom builds and distribution**

```bash
# Prerequisites
pip install -r requirements-build.txt
# Install Inno Setup 6: https://jrsoftware.org/isdl.php

# Build
build_installer.bat

# Outputs:
# - dist/RUIE/RUIE.exe (portable)
# - dist/RUIE-0.2-Alpha-Installer.exe (installer)
```

**Best for:** Custom branding, local distribution, internal use

## ⚠️ Administrator Privileges

The app requires Administrator access because:
- 🔐 RSI Launcher files are in `Program Files` (Windows-protected directory)
- 🎨 Deploying themes requires write access to protected locations
- 🧪 Testing requires temporary file modifications
- 💾 Backups need full file system access

**How it works:**
- `launch.bat` requests admin automatically via UAC prompt
- `RUIE.exe` shows UAC prompt when launched
- If running Python directly, right-click → "Run as administrator"

---

## 🎨 6-Step Wizard Workflow

Once RUIE launches, you'll see a guided 6-step wizard:

### Step 1: Initialize ⚙️
- **Auto-detection**: Finds your RSI Launcher automatically
- **Manual override**: Select `app.asar` manually if needed
- **Confirmation**: Click Initialize button to proceed
- **Result**: Launcher path and version detected

### Step 2: Extract 📦
- **Choose source**: 
  - New extraction (fresh copy of app.asar)
  - Reuse existing extraction (faster, previous work)
- **Progress**: Watch extraction complete
- **Backup**: Automatic backup created before modifications
- **Result**: Ready to customize

### Step 3: Colors 🎨
- **17 Professional Presets**: Click to apply instant themes
  - RSI Original, Midnight Purple, Emerald Green, Crimson Fire, Arctic Frost, Amber Gold, C3RB, and more
- **127+ Color Variables**: Fine-tune every color individually
- **Color Picker**: Use wheel or RGB sliders
- **Live Preview**: See changes in real-time
- **Persistence**: Colors saved across navigation steps
- **Result**: Your custom color scheme ready

### Step 4: Media 🖼️
- **9 Default Assets**: Images, logos, videos for replacement
- **Grid Picker**: Visual preview of all media
- **Custom Upload**: Replace with your own files
- **Live Preview**: See media changes immediately
- **Types Supported**: PNG, JPG, GIF, MP4, WebM, etc.
- **Result**: Custom media applied

### Step 5: Music 🎵
- **Add Tracks**: Upload OGG or MP3 files
- **Reorder**: Drag to rearrange playlist
- **Remove**: Delete tracks you don't want
- **Preview**: HTML5 player with native controls
- **Defaults**: GrimHex.ogg, StarMarine.ogg (replaceable)
- **Result**: Custom soundtrack ready

### Step 6: Finalize 🚀
- **Test Launcher**: 
  - Applies theme temporarily
  - Auto-restores when you close launcher
  - Perfect for previewing before permanent install
- **Deploy Theme**:
  - Permanently installs to your RSI Launcher
  - Creates backup automatically
  - Can be reverted from backup section
- **Result**: Custom launcher ready to use!

---

## 💾 Backup & Recovery

RUIE automatically manages backups:

- **Automatic Backups**: Created before every deployment
- **Backup Location**: `~/Documents/RUIE/backup-*/`
- **Restore**: Click "Restore" button next to any backup
- **Delete**: Remove old backups to save space
- **Extraction Reuse**: Keep extractions for quick re-modifications

---

## 🆘 Troubleshooting

### Installation Issues

**Problem**: "Windows protected your PC" warning
- **Solution**: Click "More info" → "Run anyway" (normal for unsigned executables)

**Problem**: "Access Denied" or "Permission Denied"
- **Solution**: 
  1. Right-click the exe or batch file
  2. Select "Run as Administrator"
  3. Allow the UAC prompt
  4. Or reinstall with admin rights

### Runtime Issues

**Problem**: "RSI Launcher Not Found"
- **Cause**: Launcher not installed or in unexpected location
- **Solution**: 
  1. Check: `C:\Program Files\Roberts Space Industries\RSI Launcher\`
  2. Use manual path selection in Step 1

**Problem**: "Cannot Extract ASAR"
- **Cause**: Node.js not installed
- **Solution**: 
  1. Install Node.js from https://nodejs.org (LTS)
  2. Verify: `node --version` in Command Prompt
  3. Restart RUIE

**Problem**: Can't delete extraction or backup
- **Cause**: Currently in use or active
- **Solution**: Switch to a different extraction first, then delete

### Build Issues

See [BUILD_TROUBLESHOOTING.md](BUILD_TROUBLESHOOTING.md) for detailed help.

---

## 📁 File Locations

**User Data**:
```
C:\Users\[YourUsername]\Documents\RUIE\
├── app-extracted-*/              # Extracted ASAR
├── backup-*/                     # Automatic backups
└── compiled/                     # Compiled ASAR files
```

**Original Launcher**:
```
C:\Program Files\Roberts Space Industries\RSI Launcher\resources\app.asar
```

**Debug Log**:
```
C:\Users\[YourUsername]\Documents\RUIE-debug.log
```

---

## 📚 More Documentation

- **[README.md](README.md)** - Full documentation
- **[INSTALL_GUIDE.md](INSTALL_GUIDE.md)** - Installation guide
- **[BUILD_TROUBLESHOOTING.md](BUILD_TROUBLESHOOTING.md)** - Build help
- **[SECURITY_AUDIT.md](SECURITY_AUDIT.md)** - Security info
- **[CHANGELOG.md](CHANGELOG.md)** - Version history

---

## 📄 License

GNU General Public License v3.0 - See [LICENSE](LICENSE)

⚠️ **DISCLAIMER**: Fan-made project NOT affiliated with Cloud Imperium Games or Star Citizen.

---

**Version**: 0.2 Alpha  
**Last Updated**: February 1, 2026  
**Ready to customize? Start with Option 1, 2, or 3 above! 🚀**
