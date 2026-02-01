# Installation System Quick Reference

## For Users

### Using the Installer (Recommended)
```
Download: RUIE-0.2-Alpha-Installer.exe
Run: Double-click → Install → Done
Location: C:\Program Files\RUIE
```

### Using Portable EXE
```
Download: RUIE.exe
Run: Double-click
No installation needed
```

---

## For Developers

### Building the Installer

**Requirements:**
1. Install Inno Setup 6: https://jrsoftware.org/isdl.php
2. Install dependencies: `pip install -r requirements-build.txt`
3. Ensure `icon.ico` is in root directory

**Build Command:**
```bash
build_installer.bat
```

**Output:**
```
dist/RUIE-0.2-Alpha-Installer.exe (~500MB)
dist/RUIE/RUIE.exe (~300MB)
```

---

## Documentation

- **[INSTALL_GUIDE.md](INSTALL_GUIDE.md)** - Complete installation guide for all methods
- **[INSTALLER_SETUP.md](INSTALLER_SETUP.md)** - Technical setup details and configuration
- **[README.md](README.md#-quick-start)** - Quick start section with all options

---

## Installer Features

✅ Professional Windows installer
✅ Installs to Program Files
✅ Creates Start Menu shortcuts
✅ Optional desktop shortcut
✅ Clean uninstallation
✅ 64-bit Windows only
✅ Admin privileges required
✅ License agreement display

---

## File Structure

```
RUIE Installation Files:
├── RUIE_Installer.iss    (Inno Setup config)
├── build_installer.bat   (Build automation)
├── INSTALL_GUIDE.md      (User documentation)
├── INSTALLER_SETUP.md    (Technical docs)
└── icon.ico              (Application icon)

After Building:
dist/
├── RUIE-0.2-Alpha-Installer.exe
└── RUIE/
    ├── RUIE.exe
    ├── icon.ico
    ├── LICENSE
    ├── README.md
    └── _internal/        (PyInstaller deps)
```

---

## Quick Commands

```bash
# Build installer
build_installer.bat

# Build exe only (old method)
build.bat

# Build exe with installer
build_installer.bat

# Run from source
python launcher.py
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Inno Setup not found" | Install from https://jrsoftware.org/isdl.php |
| "PyInstaller failed" | Run `pip install -r requirements-build.txt` |
| "Icon not found" | Ensure `icon.ico` is in root directory |
| "App won't launch" | Check `~/Documents/RUIE-debug.log` |
| "Can't uninstall" | Use Settings → Apps → Apps & Features |

---

## Version Info

- **App Version:** 0.2 Alpha
- **Installer Version:** 1.0
- **Target OS:** Windows 10/11 (64-bit)
- **Created:** February 1, 2026

---

## Distribution

**For End Users:**
- Share: `RUIE-0.2-Alpha-Installer.exe`
- Or: `RUIE.exe` (portable)

**For Developers:**
- Share: GitHub repository
- Link: https://github.com/Elegius/RUIE

---

See [INSTALL_GUIDE.md](INSTALL_GUIDE.md) for detailed information.
