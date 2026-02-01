# RUIE Installation System Setup Summary

## Overview

RUIE is now a fully installable Windows application with multiple distribution options. Users can choose between:

1. **Windows Installer** (recommended for end users)
2. **Portable Executable** (no installation required)
3. **Source Code** (for developers)

---

## What Was Added

### 1. Inno Setup Installer Script
**File:** `RUIE_Installer.iss`

A professional Windows installer configuration that:
- ✅ Installs to `C:\Program Files\RUIE` (customizable)
- ✅ Creates Start Menu shortcuts
- ✅ Optional: Desktop shortcut
- ✅ Optional: Quick Launch icon
- ✅ Optional: File type association for .json presets
- ✅ Displays license and disclaimer
- ✅ Handles uninstallation cleanly
- ✅ Launches app automatically after installation
- ✅ 64-bit Windows only
- ✅ Requires Administrator privileges

### 2. Installer Build Batch Script
**File:** `build_installer.bat`

Automates the complete build process:
1. Checks for Inno Setup 6 installation
2. Cleans previous builds
3. Runs PyInstaller to create exe
4. Runs Inno Setup to create installer
5. Places final installer in `dist/` folder

**Usage:**
```bash
build_installer.bat
```

### 3. Comprehensive Installation Guide
**File:** `INSTALL_GUIDE.md`

Complete documentation covering:
- Installation options (installer, portable, source)
- System requirements
- Post-installation setup
- Building your own installer
- Troubleshooting common issues
- Update and maintenance procedures
- Distribution guidelines

---

## Installation Process

### For End Users

**Using the Installer (Recommended):**
```
1. Download: RUIE-0.2-Alpha-Installer.exe
2. Double-click the installer
3. Follow the wizard
4. Click Install
5. App launches automatically
```

**Disk Usage:**
- Installation: ~500MB total
- Backups/Extractions: Variable (additional space needed)

**Registry Impact:**
- Creates entry in: `HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Uninstall\RUIE`
- Allows Windows to manage installation
- Clean uninstall available

### For Developers

**Building the Installer:**
```bash
# Prerequisites
# 1. Install Inno Setup 6: https://jrsoftware.org/isdl.php
# 2. Install Python dependencies: pip install -r requirements-build.txt

# Then build
build_installer.bat

# Output: dist/RUIE-0.2-Alpha-Installer.exe
```

---

## Technical Details

### Inno Setup Features Used

| Feature | Configuration |
|---------|----------------|
| **Architecture** | 64-bit only (ArchitecturesAllowed=x64) |
| **Compression** | LZMA (solid compression) |
| **UI Style** | Modern (WizardStyle=modern) |
| **License** | GPL v3 with custom disclaimer |
| **Privileges** | Admin required (PrivilegesRequired=admin) |
| **Icons** | Custom app icon + wizards |
| **Uninstall** | Full clean removal |

### Installation Folders

```
Installation Root: C:\Program Files\RUIE\

Contents:
├── RUIE.exe              (Main application)
├── _internal/            (PyInstaller dependencies)
├── icon.ico              (Application icon)
├── LICENSE               (GPL v3 license)
└── README.md             (Documentation)

User Data (Preserved):
└── ~/Documents/RUIE/
    ├── app-extracted-*/  (Extracted ASAR files)
    ├── app-decompiled-*/ (Decompiled assets)
    ├── backup-*/         (Backup archives)
    └── compiled/         (Compiled ASAR files)
```

### Shortcuts Created

**Start Menu:**
- `Start Menu → All Apps → RUIE → RUIE`
- `Start Menu → All Apps → RUIE → Uninstall RUIE`

**Desktop (Optional):**
- Desktop shortcut to RUIE.exe

**Quick Launch (Optional):**
- Quick Launch toolbar entry (Windows 7 compatibility)

---

## Distribution Options

### Option A: Installer (Professional Distribution)
**File:** `RUIE-0.2-Alpha-Installer.exe`

**Best for:**
- End users
- Professional distribution
- GitHub releases
- Wider audience reach

**Advantages:**
- Professional appearance
- Automatic updates capability
- Easy uninstallation
- Start Menu integration
- ~500MB file size

**Disadvantages:**
- Requires Windows 10/11 64-bit
- Requires admin privileges to install
- Can't run from USB without installation

### Option B: Portable Executable
**File:** `RUIE.exe` + dependencies

**Best for:**
- Quick testing
- USB/portable use
- Users who want no installation
- Temporary use

**Advantages:**
- No installation needed
- Can run from USB
- Easy to remove
- ~300MB total

**Disadvantages:**
- No Start Menu shortcuts
- No uninstall option
- Must keep files together

### Option C: Source Code Distribution
**Location:** GitHub repository

**Best for:**
- Developers
- Open source community
- Customization needs
- Contributing changes

**Advantages:**
- Full transparency
- Customizable
- Easy to contribute to
- Community-driven

**Disadvantages:**
- Requires Python/Node.js setup
- Slower startup
- More complex for users

---

## Building Process Flowchart

```
User runs: build_installer.bat
    ↓
Script checks for Inno Setup 6
    ↓
Cleans dist/ and build/ folders
    ↓
Runs: pyinstaller RUIE.spec
    ↓ (Creates dist/RUIE/RUIE.exe + dependencies)
    ↓
Runs: ISCC.exe RUIE_Installer.iss
    ↓ (Packages files into installer)
    ↓
Output: dist/RUIE-0.2-Alpha-Installer.exe (~500MB)
    ↓
Success message with path to installer
```

---

## Files Added/Modified

### New Files Created:
- ✅ `RUIE_Installer.iss` - Inno Setup configuration
- ✅ `build_installer.bat` - Automated build script
- ✅ `INSTALL_GUIDE.md` - Comprehensive installation guide

### Modified Files:
- ✅ `README.md` - Updated with new installation options

### Existing Files (No changes):
- `RUIE.spec` - PyInstaller spec (still used)
- `build.bat` - Old build script (still available)
- All source code files

---

## Post-Installation Behavior

When user installs via the installer:

1. **Installation Phase**
   - Files copied to `C:\Program Files\RUIE`
   - Shortcuts created
   - Registry entries added

2. **Post-Install Phase**
   - App launches automatically
   - User sees intro dialog
   - User grants admin privileges
   - Launcher is auto-detected
   - Ready to use

3. **Uninstallation Phase**
   - User runs uninstaller
   - All files removed from `C:\Program Files\RUIE`
   - Shortcuts deleted
   - Registry entries removed
   - User data in `~/Documents/RUIE` preserved

---

## Requirements for Building

To build the installer yourself, you need:

1. **Inno Setup 6**
   - Download: https://jrsoftware.org/isdl.php
   - Free and open source
   - Installs to `Program Files (x86)`

2. **Python 3.10+**
   - Already needed for development

3. **PyInstaller**
   - Install: `pip install pyinstaller`
   - Compiles Python to standalone exe

4. **Build Requirements**
   - Install: `pip install -r requirements-build.txt`
   - Includes all dev dependencies

---

## Future Enhancements

Possible improvements to the installation system:

1. **Auto-Update System**
   - Check GitHub for new versions
   - Download and install updates
   - Preserve user preferences

2. **Custom Installation**
   - Portable mode option during install
   - Per-user vs system-wide installation
   - Custom directory selection

3. **MSI Package**
   - Create .msi installer (Windows native)
   - GPO deployment support
   - Enterprise distribution

4. **Codesigning**
   - Sign installer with certificate
   - Remove "Unknown Publisher" warning
   - Trusted distribution

5. **GitHub Actions**
   - Automated installer builds
   - Release automation
   - Binary distribution

---

## Troubleshooting Build Issues

**Problem:** "Inno Setup not found"
- **Solution:** Install Inno Setup 6 from https://jrsoftware.org/isdl.php

**Problem:** "PyInstaller not installed"
- **Solution:** Run `pip install pyinstaller`

**Problem:** "Build fails at PyInstaller step"
- **Solution:** Check `RUIE.spec` file, ensure all paths are correct

**Problem:** "Icon not found"
- **Solution:** Ensure `icon.ico` exists in root directory

**Problem:** "installer is too large"
- **Solution:** Use LZMA compression (already enabled)

---

## Version Information

- **RUIE Version:** 0.2 Alpha
- **Installer Version:** 1.0
- **Inno Setup:** 6.x
- **Windows Target:** 10/11 (64-bit)
- **Created:** February 1, 2026

---

## License & Disclaimer

RUIE is released under GNU General Public License v3.0.

⚠️ **Important:**
- RUIE is fan-made and NOT affiliated with Cloud Imperium Games
- Star Citizen and RSI Launcher are trademarks of Cloud Imperium Games
- Use at your own risk per Cloud Imperium Games' Terms of Service

---

## Support

For installation issues:
1. Check `INSTALL_GUIDE.md`
2. Review debug log: `~/Documents/RUIE-debug.log`
3. Open GitHub issue: https://github.com/Elegius/RUIE/issues

---

**Status:** ✅ Installation system fully implemented  
**Ready for:** Distribution and user installation
