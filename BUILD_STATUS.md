# RUIE Build System - Setup Complete ✅

## What Was Fixed

The missing `RUIE.spec` file has been created and all build infrastructure is now in place.

---

## Files Created/Updated

### New Files:
1. ✅ **`RUIE.spec`** - PyInstaller configuration file
   - Defines how to package Python code into Windows exe
   - Includes all necessary dependencies and assets
   - Configured for no-console GUI application

2. ✅ **`BUILD_TROUBLESHOOTING.md`** - Comprehensive build guide
   - Troubleshoots common build issues
   - Provides step-by-step solutions
   - Advanced build options

### Updated Files:
1. ✅ **`build_installer.bat`** - Enhanced build script
   - Better error handling
   - Works without Inno Setup (builds portable exe first)
   - Clear status messages

---

## Building RUIE Now

### Quick Build (Portable EXE)
```bash
python -m PyInstaller RUIE.spec
```
**Output:** `dist/RUIE/RUIE.exe` (~300MB)  
**Time:** ~5-15 minutes

### Full Build (EXE + Installer)
```bash
build_installer.bat
```
**Outputs:**
- `dist/RUIE/RUIE.exe` (~300MB)
- `dist/RUIE-0.2-Alpha-Installer.exe` (~500MB)

**Time:** ~10-20 minutes

**Requirements:**
- Inno Setup 6 installed (https://jrsoftware.org/isdl.php)

---

## What the Spec File Does

The `RUIE.spec` file tells PyInstaller to:

1. **Analyze** `launcher.py` as the entry point
2. **Include** all Python dependencies (flask, PyQt5, etc.)
3. **Bundle** resources:
   - `public/` folder (web UI)
   - `assets/` folder (images, videos, music)
   - `icon.ico` (application icon)
4. **Create** a standalone Windows executable
5. **Configure** it as a GUI app (no console window)
6. **Compress** with UPX for smaller file size

---

## Build Output Structure

After building, you'll have:

```
dist/
├── RUIE/                          # Portable folder
│   ├── RUIE.exe                   # Runnable executable
│   ├── icon.ico
│   ├── _internal/                 # PyInstaller dependencies
│   └── [other runtime files]
│
└── RUIE-0.2-Alpha-Installer.exe   # Windows installer (if Inno Setup available)

build/
└── [PyInstaller build artifacts]
```

---

## System Requirements for Building

| Component | Required |
|-----------|----------|
| Python | 3.10+ |
| PyInstaller | 6.0.0+ |
| PyQt5 | 5.15.0+ |
| PyQtWebEngine | 5.15.0+ |
| Node.js | (Not needed for building, only runtime) |
| Inno Setup 6 | (Optional, for installer) |

---

## Step-by-Step Build Guide

### 1. Verify Prerequisites
```bash
python --version              # Should be 3.10+
python -m pip --version       # Should be recent
```

### 2. Install Build Dependencies
```bash
pip install -r requirements-build.txt
```

### 3. Build the EXE
```bash
python -m PyInstaller RUIE.spec
```

### 4. Test the EXE
```bash
cd dist\RUIE
RUIE.exe
```

### 5. (Optional) Build the Installer
Install Inno Setup 6, then:
```bash
build_installer.bat
```

### 6. Distribute
- **For users:** Share `RUIE-0.2-Alpha-Installer.exe` or `dist/RUIE/RUIE.exe`
- **For developers:** Share the GitHub repository

---

## Troubleshooting Quick Links

- **PyInstaller not found?** → See [BUILD_TROUBLESHOOTING.md](BUILD_TROUBLESHOOTING.md#issue-1-pyinstaller-not-found)
- **Spec file missing?** → Already created, in root directory
- **Build fails?** → Check [BUILD_TROUBLESHOOTING.md](BUILD_TROUBLESHOOTING.md)
- **EXE won't run?** → See [Issue 9](BUILD_TROUBLESHOOTING.md#issue-9-app-wont-run-after-build)
- **Build too slow?** → See [Performance Tips](BUILD_TROUBLESHOOTING.md#build-performance-tips)

---

## What's Next

1. ✅ Build dependencies installed
2. ✅ RUIE.spec created
3. ✅ build_installer.bat updated
4. ✅ Build troubleshooting guide added
5. 📦 **Ready to build!** Run: `python -m PyInstaller RUIE.spec`

---

## Build Verification Checklist

After successful build, verify:

- [ ] `dist/RUIE/RUIE.exe` exists and is ~300MB
- [ ] `dist/RUIE/RUIE.exe` runs without errors
- [ ] All UI elements load correctly
- [ ] Can detect RSI Launcher
- [ ] Can extract ASAR (requires Node.js)
- [ ] (Optional) Installer exe created at `dist/RUIE-0.2-Alpha-Installer.exe`

---

## Important Notes

### About the Build

- **First build is slow:** ~15 minutes (PyInstaller analyzes all dependencies)
- **Subsequent builds are faster:** ~5-10 minutes
- **Uses UPX compression:** Already configured in spec file
- **No-console mode:** EXE doesn't show command prompt window

### About Distribution

- **Portable EXE:** Just `dist/RUIE/RUIE.exe` + dependencies folder
- **Installer:** Standalone `dist/RUIE-0.2-Alpha-Installer.exe`
- **Source:** Full GitHub repository for developers

### About Runtime

- **Node.js required:** For asar packing/unpacking features
- **Admin privileges required:** To modify launcher files
- **Windows 10/11 only:** 64-bit preferred

---

## File Manifest

### Build Configuration Files:
- ✅ `RUIE.spec` - PyInstaller spec file
- ✅ `build_installer.bat` - Build automation script
- ✅ `RUIE_Installer.iss` - Inno Setup config

### Documentation:
- ✅ `BUILD_TROUBLESHOOTING.md` - Build troubleshooting guide
- ✅ `INSTALLATION_QUICKREF.md` - Quick reference
- ✅ `INSTALL_GUIDE.md` - Full installation guide
- ✅ `INSTALLER_SETUP.md` - Technical details

---

## Status

✅ **Build System Ready**
- PyInstaller spec file created
- Build scripts configured
- Documentation complete
- Ready for compilation

**Next Step:** Run `python -m PyInstaller RUIE.spec` to build the executable

---

**Version:** 0.2 Alpha  
**Build System Version:** 1.0  
**Last Updated:** February 1, 2026
