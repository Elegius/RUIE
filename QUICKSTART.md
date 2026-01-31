# Quick Start Guide - RUIE v0.1 Alpha

## ⚡ Quick Start

### Option 1: Run Compiled Executable (Recommended)
1. Download `RUIE.exe` from `dist/` folder
2. Double-click to launch
3. UAC will prompt for admin privileges - click "Yes"
4. App will open with no console windows

### Option 2: Run from Source
```bash
# Install dependencies
pip install -r requirements.txt

# Launch the app
python launcher.py
# OR simply run:
run.bat
```

### Option 3: Build Your Own EXE
```bash
build.bat
# Creates: dist\RUIE.exe
```

## ⚠️ Administrator Privileges

The app requires Administrator access to:
- 🔐 Access Program Files (RSI Launcher location)
- 🎨 Deploy themes permanently
- 🧪 Test launcher with temporary modifications

**How it Works:**
- `launch.bat` requests admin automatically via UAC
- Run compiled `.exe` directly (also requests admin)
- If running Python directly, use "Run as administrator"

## 🎨 6-Step Wizard Workflow

The app guides you through theme customization in 6 steps:

### Step 1: Initialize
- Auto-detect RSI Launcher installation
- Or manually select app.asar file
- Click **Initialize** to confirm

### Step 2: Extract
- Extracts app.asar to temporary location
- Shows progress bar during extraction
- Can reuse previous extractions from dropdown

### Step 3: Customize Colors
Choose from 6 professional presets:
1. **RSI Original** - Official RSI colors
2. **Midnight Purple** - Dark purple theme
3. **Emerald Green** - Green accent theme
4. **Crimson Fire** - Red accent theme
5. **Arctic Frost** - Light blue theme
6. **Amber Gold** - Gold accent theme

Or customize manually with:
- Hex color input fields
- RGB sliders for fine-tuning
- Live preview shows changes in real-time
- Colors persist across all steps
- Colors organized in **collapsible sections** (Primary, Neutral, Accent, Interactive, Status, etc.)
  - Primary Colors expanded by default
### Step 4: Replace Media
- Grid view of available images and videos
- Click "Select" button to choose replacement file
- Changes preview in real-time

### Step 5: Manage Music
- Add/remove/reorder background music tracks
- Supported formats: OGG (preferred), MP3
- Default music loads from launcher config

### Step 6: Finalize
- **Test Launcher**: Temporarily apply changes and run launcher
- **Deploy Theme**: Permanently install to RSI Launcher
- **Save Theme**: Export as `.theme.json` for sharing

## 🆘 Troubleshooting

### "Permission Denied" Error
- Run as Administrator (UAC prompt should appear automatically)
- Use `launch.bat` which handles elevation

### "Launcher Not Found"
- Ensure RSI Launcher is installed
- Check: `C:\Program Files\Roberts Space Industries\RSI Launcher\`
- Use manual path selection in Step 1

### Build Fails (PyInstaller)
- Delete `build/` and `dist/` folders
- Run `build.bat` again
- Ensure Python 3.10+ is installed

### Server Won't Start
- Ensure Node.js is installed (for `npx asar`)
- Check: `node --version` and `npm --version`
- Delete `__pycache__/` folder and try again

## 📁 File Locations

**Theme Files & Backups**:
```
C:\Users\[Username]\Documents\RSI-Launcher-Theme-Creator\
├── themes/                    # Saved themes
├── app-extracted-*/           # Extracted files
└── backup-*/                  # Automatic backups
```

**Original Launcher**:
```
C:\Program Files\Roberts Space Industries\RSI Launcher\resources\app.asar
```

## License

GNU General Public License v3.0

This project is free software. See [LICENSE](LICENSE) for details.

---

**Ready to get started? Run `launch.bat` now! 🚀**
