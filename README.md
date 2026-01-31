# RUIE

A Windows desktop application for customizing the RSI Launcher UI. Built with Python (Flask backend) and PyQt5 (native GUI), the app provides a complete 6-step wizard for theme creation with live preview.

## Features

- ✅ **6-Step Wizard Interface** - Initialize → Extract → Colors → Media → Music → Finalize
- ✅ **Live Theme Preview** - Real-time preview on Colors, Media, and Music steps
- ✅ **Color Customization** - Hex/RGB input with 6 professional presets
- ✅ **Media Replacement** - Replace images and videos with grid picker
- ✅ **Music Playlist** - Add/remove/reorder background music tracks
- ✅ **Auto-Detection** - Automatically finds RSI Launcher installation
- ✅ **Theme Management** - Save, export, and import themes
- ✅ **Admin Support** - Automatic UAC elevation for Program Files access
- ✅ **Responsive Design** - Works on various screen sizes
- ✅ **Single Executable** - Compiled to standalone .exe file
- ✅ **No Console** - Clean GUI-only interface

## System Requirements

- **Windows 10/11** with Administrator privileges (for deployment)
- **Python 3.10+** (if running from source)
- **Node.js** (for app.asar extraction/repacking - installed via npx)

## Quick Start

### Option 1: Run Compiled Executable
1. Download the `.exe`
2. Double-click to launch (UAC will request admin privileges)
3. Follow the 6-step wizard

### Option 2: Run from Source
```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python launcher.py
# OR
run.bat
```

### Option 3: Build Standalone EXE
```bash
build.bat
# Creates: dist\RUIE.exe
```

## Usage Workflow

1. **Step 1: Initialize** - Auto-detect or manually select RSI Launcher path
2. **Step 2: Extract** - Extract app.asar to temporary location
3. **Step 3: Colors** - Customize 127+ CSS color variables
4. **Step 4: Media** - Replace images and videos
5. **Step 5: Music** - Manage background music playlist
6. **Step 6: Finalize** - Test or deploy theme to launcher

## File Structure

```
RUIE/
├── launcher.py           # PyQt5 GUI entry point
├── server.py             # Flask API server
├── launch.bat            # Clean launcher with UAC elevation
├── run.bat               # Development launcher
├── build.bat             # Build standalone exe
├── icon.ico              # Application icon
├── public/               # Web assets for preview
│   ├── app.js            # Main application logic
│   ├── preview.html      # Live preview iframe
│   ├── styles.css        # UI styling
│   └── ...
├── dist/                 # Built executables (after running build.bat)
└── requirements.txt      # Python dependencies
```

## Architecture

### Dual-Mode Server Design
The application uses an intelligent server startup mechanism:

- **Development Mode** (running from source):
  - Flask server launches as a separate subprocess
  - Allows live reloading and debugging
  - Output streams captured for logging

- **Production Mode** (compiled EXE):
  - Flask server runs in a daemon thread within the main process
  - No external Python interpreter required
  - Resources loaded from PyInstaller's `_MEIPASS` temp directory
  - Reloader disabled to prevent threading conflicts

### Resource Path Resolution
The app automatically detects execution mode and resolves paths:
- **Frozen**: Uses `sys._MEIPASS` for bundled resources
- **Source**: Uses script directory for local files

This ensures the `public` folder and all assets load correctly in both modes.

## Color Customization

The app provides 6 professional color presets:
1. **RSI Original** - Official RSI color scheme
2. **Midnight Purple** - Dark purple theme
3. **Emerald Green** - Green accent theme
4. **Crimson Fire** - Red accent theme
5. **Arctic Frost** - Light blue theme
6. **Amber Gold** - Gold accent theme

Each color can be fine-tuned with Hex or RGB input fields.

## API Endpoints

The Flask server provides 25+ endpoints for:
- Launcher detection and info
- asar extraction and repacking
- Color and media application
- Music management
- Theme save/load/export

## License

GNU General Public License v3.0

This project is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

See [LICENSE](LICENSE) for details.

## Troubleshooting

### "Permission Denied" Error
- Run the application as Administrator
- Use `launch.bat` which automatically requests elevation

### "Launcher Not Found" Error
- Ensure RSI Launcher is installed in default location
- Use the manual path selection in Step 1

### Build Fails with PyInstaller Errors
- Ensure Python 3.10+ is installed
- Run `build.bat` from the project directory
- Delete `build/` and `dist/` folders and try again

## Development

To modify the source code:
1. Edit `launcher.py` (GUI), `server.py` (API), or `public/` (web assets)
2. Run `python launcher.py` to test changes
3. Build with `build.bat` when ready to distribute

## Support

For issues, questions, or feature requests, please check the project documentation or create an issue in the repository.

**⚠️ Admin Privileges Note**: The app requires Administrator permissions for:
- ✅ Writing to `Program Files\Roberts Space Industries\RSI Launcher\`
- ✅ Deploying themes permanently to the launcher
- ✅ Test launcher functionality (temporary file modifications)

**To run with admin**: Right-click `run.bat` → "Run as administrator"

## Workflow

1. **Initialize** RSI Launcher path (auto-detects if installed)
2. **Extract** app.asar (with progress indicator)
3. **Customize Colors** with 6 presets or manual editing
4. **Apply Media** (optional - replace images, videos, audio)
5. **Deploy** theme permanently or test temporarily
6. **Save & Share** themes via export/import system

### Step Details
- **Step 1 (Initialize)**: Auto-detects RSI Launcher location, displays confirmation message, requires manual confirmation
- **Step 2 (Extract)**: Unpacks app.asar with progress tracking, option to reuse existing extractions
- **Step 3 (Colors)**: Edit 127+ CSS variables with presets or manual controls, live preview updates
- **Step 4 (Media)**: Replace launcher media assets (images, videos, audio)
- **Step 5 (Finalize)**: Test or deploy the custom theme

## File Locations

- **Extracted files**: `C:\Users\<You>\Documents\RSI-Launcher-Theme-Creator\app-extracted-YYYYMMDD-HHMMSS\`
- **Backups**: `C:\Users\<You>\Documents\RSI-Launcher-Theme-Creator\backup-YYYYMMDD-HHMMSS\`
- **Saved themes**: `C:\Users\<You>\Documents\RSI-Launcher-Theme-Creator\themes\`

## Theme Management

### Save & Share Themes
- **💾 Save Theme**: Save your custom theme locally for later use
- **📤 Export Theme**: Download `.theme.json` file to share with others
- **📥 Import Theme**: Load theme files from the community
- **📂 Load Saved Theme**: Browse and load any previously saved theme

Theme files (`.theme.json`) are portable and can be shared via Discord, Reddit, or any file sharing platform.

## Troubleshooting

### Admin Privileges Required
- **Error**: "Permission denied" when deploying theme or testing launcher
- **Solution**: Run the app as Administrator. The app will automatically request elevation via Windows UAC on startup.
- **Alternative**: Right-click `run.bat` → "Run as administrator"

### "Failed to fetch" during Extract
- The local Flask server likely stopped.
- Close the app and re-run `python launcher.py`.
- Check terminal output for the detailed error.

### "Launcher not found"
- Verify RSI Launcher is installed in:
  - `C:\Program Files\Roberts Space Industries\RSI Launcher\`

### Server won't start
- Confirm Python and Flask are installed.
- Ensure port 5000 is free.
- Ensure Node.js is installed for `npx asar`.
- Try running with administrator privileges.

## Documentation

- [QUICKSTART.md](QUICKSTART.md)
- [PYTHON_MIGRATION.md](PYTHON_MIGRATION.md)
- [MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md)
- [CHANGELOG.md](CHANGELOG.md)

## License

GNU General Public License v3.0

This project is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

See [LICENSE](LICENSE) for details.
