# RUIE Installation Guide

## Installation Options

RUIE offers three ways to use the application:

### Option 1: Install from Windows Installer (Recommended)

This is the easiest method for end users. The installer handles all setup automatically.

**Requirements:**
- Windows 10 or 11
- Administrator privileges (for installation)
- ~500MB disk space

**Steps:**
1. Download `RUIE-0.2-Alpha-Installer.exe` from the Releases page
2. Double-click to run the installer
3. Follow the installation wizard
4. Click "Yes" when Windows asks for administrator permission
5. Choose installation location (default: `C:\Program Files\RUIE`)
6. Select additional options (desktop shortcut, quick launch icon, etc.)
7. Click "Install"
8. The app will launch automatically when installation completes

**What the installer does:**
- Copies application files to `C:\Program Files\RUIE`
- Creates Start Menu shortcuts
- Creates optional Desktop shortcut
- Registers application for uninstallation
- Handles updates and uninstallation

**To Uninstall:**
- Open Settings → Apps → Apps & Features
- Find "RUIE" in the list
- Click "Uninstall"
- Or: Control Panel → Programs → Programs and Features → RUIE → Uninstall

---

### Option 2: Run Portable Executable

For portable use without installation.

**Requirements:**
- Windows 10 or 11
- Administrator privileges (optional - to modify launcher)
- ~300MB disk space

**Steps:**
1. Download `RUIE.exe` from Releases
2. Place in any folder
3. Double-click `RUIE.exe`
4. Watch the progress bar during startup (5-15 seconds)
   - Progress bar shows real-time initialization status
   - Status messages indicate what's being loaded
   - Three animated step indicators show progress
5. Main application opens when progress reaches 100%
6. If you want to use launcher theme modification features, ensure admin privileges are granted when prompted

**⚠️ Important - What You'll See:**
- **Progress Screen** (5-15 seconds):
  - Progress bar with percentage display (0-100%)
  - Status messages: "Loading dependencies...", "Starting server...", "Initializing UI..."
  - Three-step indicators with animated spinners showing progress
  - Do not close the window during this phase
- **UAC Prompt**: May show Windows asking "Do you want to allow this app to make changes to your device?"
  - Click "Yes" if you want full theme modification features
  - Click "No" to run in read-only mode (can preview themes but not apply them)
- **Subsequent launches**: Should load cleanly with faster initialization

**Advantages:**
- No installation required
- Can run from USB drive
- Easy to remove (just delete the exe)
- Fast to test themes

**Disadvantages:**
- No Start Menu shortcuts
- No easy uninstall option
- Must keep .exe and dependencies together
- Needs admin privileges for theme application

**Troubleshooting:**
- **Progress bar stuck**: If progress bar doesn't move for more than 35 seconds, the server failed to start. Restart the application or check `RUIE-debug.log` for errors.
- **"Address already in use" error**: Close any other RUIE instances running on port 5000
- **Themes won't apply**: Ensure you clicked "Yes" when UAC prompted for admin privileges
- **App doesn't open**: Wait 15 seconds - progress bar will show the server is still initializing
- **See error dialog**: Check `RUIE-debug.log` in your Documents folder for technical details

---

### Option 3: Run from Source Code

For developers or advanced users.

**Requirements:**
- Python 3.10+
- Node.js (for asar packing/unpacking)
- Administrator privileges
- All Python dependencies from `requirements.txt`

**Steps:**
```bash
# Clone or download the repository
cd RUIE

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (if building)
npm install -g asar

# Run the application
python launcher.py
```

**Advantages:**
- Full source code access
- Easy to modify and customize
- Good for development

**Disadvantages:**
- Requires Python and Node.js installation
- Slower startup than compiled exe
- Need to manually manage dependencies

---

## Building Your Own Installer

If you want to build the installer yourself from source:

### Prerequisites

1. **Install Inno Setup 6**
   - Download from: https://jrsoftware.org/isdl.php
   - Run the installer
   - Use default installation location

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements-build.txt
   ```

3. **Prepare Your Icon** (optional)
   - Replace `icon.ico` with your custom icon
   - Icon should be 256x256 pixels or larger

### Building Process

**Method 1: Using build_installer.bat**
```bash
build_installer.bat
```
This automatically:
- Compiles the Python code to exe using PyInstaller
- Creates the Windows installer using Inno Setup
- Places the installer in the `dist` folder

**Method 2: Manual Steps**
```bash
# Step 1: Build exe with PyInstaller
pyinstaller RUIE.spec

# Step 2: Build installer with Inno Setup
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" RUIE_Installer.iss
```

**Output:**
- Installer: `dist/RUIE-0.2-Alpha-Installer.exe`
- Standalone exe: `dist/RUIE/RUIE.exe`

---

## System Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 10/11 (64-bit) |
| **RAM** | 2GB minimum, 4GB recommended |
| **Disk Space** | 500MB for installation + backups |
| **Privileges** | Administrator (to modify launcher) |
| **Dependencies** | Node.js (for asar operations) |

---

## Post-Installation

### First Run

When you run RUIE for the first time:
1. You'll see a UAC (User Account Control) prompt
2. Click "Yes" to grant administrator privileges
3. The app will detect your RSI Launcher installation automatically
4. You're ready to customize your launcher theme!

### Node.js Requirement

RUIE uses Node.js to extract and pack app.asar files:
- If Node.js is installed globally, RUIE will find it automatically
- If you get an "asar not found" error, install Node.js:
  - Download from: https://nodejs.org
  - Use LTS version
  - Run installer and complete setup
  - Restart RUIE

### Administrator Privileges

RUIE requires administrator privileges because:
- The RSI Launcher files are in `Program Files` directory
- Windows protects system program files
- Administrator access is needed to create backups and install themes

This is normal and required for the app to function properly.

---

## Troubleshooting Installation

**Problem: "Inno Setup not found" when building installer**
- Solution: Install Inno Setup 6 from https://jrsoftware.org/isdl.php

**Problem: Installer won't run on older Windows 10 versions**
- Solution: Use the portable exe instead, or update to latest Windows 10/11

**Problem: "Administrator privileges required" error during installation**
- Solution: Right-click installer → Run as Administrator

**Problem: App won't launch after installation**
- Solution: 
  - Check if Node.js is installed: `node --version` in Command Prompt
  - Try running from source code to isolate the issue
  - Check debug log at: `~/Documents/RUIE-debug.log`

**Problem: Can't uninstall properly**
- Solution:
  1. Use Windows Settings → Apps → Apps & Features
  2. Or try the Uninstall option in Start Menu → RUIE
  3. If still stuck, run `dist/RUIE/unins000.exe` directly

---

## Updates and Maintenance

### Automatic Update Checking
RUIE automatically checks for updates on GitHub when the application starts and periodically (every 24 hours). If a new version is available, you'll see a notification banner at the top of the application with a download link.

**Update Check Details:**
- GitHub API is queried for the latest release
- Checks occur automatically in the background
- No network requests are blocked by the system
- Update notification includes release notes
- Can be dismissed without affecting functionality

### Manual Update Checking
Visit the GitHub repository to check for new versions manually:
https://github.com/Elegius/RUIE

### Updating from Previous Version

**If using installer:**
1. Download and run the new installer
2. It will upgrade automatically
3. Your existing settings are preserved

**If using portable exe:**
1. Download the new exe
2. Replace the old one
3. All your saved themes are preserved (stored in ~/Documents/RUIE)

**If building from source:**
1. Pull the latest changes: `git pull`
2. Update dependencies: `pip install -r requirements.txt`
3. Run as usual: `python launcher.py`

---

## Distribution and Sharing

**For End Users:**
- Share the installer: `RUIE-0.2-Alpha-Installer.exe`
- Or the portable exe: `RUIE.exe`
- Include the LICENSE file
- Link to GitHub for latest version

**For Developers:**
- Share the source code
- Point to: https://github.com/Elegius/RUIE
- Include installation instructions from Option 3

---

## Technical Details

### Installer Features

The Inno Setup installer includes:
- ✅ Silent installation option (for automation)
- ✅ Custom installation path
- ✅ Optional desktop/start menu shortcuts
- ✅ File type association (optional)
- ✅ Clean uninstallation
- ✅ 64-bit Windows support
- ✅ Admin privilege verification
- ✅ License agreement display

### Registry Information

The installer stores information in:
- `HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Uninstall\RUIE`

This allows Windows to properly manage the installation.

### Portable vs Installed

| Feature | Installer | Portable |
|---------|-----------|----------|
| Installation | Required | Not needed |
| Disk Space | ~500MB | ~300MB |
| Start Menu | Yes | No |
| Uninstall Option | Yes | No |
| Portability | Windows only | Can move files |
| Update Handling | Automatic | Manual |
| Admin Required | For install | For launcher mod |

---

## Support

If you encounter issues during installation:
1. Check this guide's Troubleshooting section
2. Check the debug log: `~/Documents/RUIE-debug.log`
3. Open an issue on GitHub: https://github.com/Elegius/RUIE/issues
4. Include:
   - Your Windows version
   - The error message
   - Steps to reproduce the issue
   - Your debug log

---

## License & Disclaimer

RUIE is provided under the GNU General Public License v3.0. See LICENSE file for full details.

⚠️ **IMPORTANT DISCLAIMER:**
- RUIE is a fan-made project NOT affiliated with Cloud Imperium Games
- Star Citizen and RSI Launcher are trademarks of Cloud Imperium Games
- Use at your own risk and in accordance with CIG's Terms of Service
- The authors assume no responsibility for any issues

---

**Version:** 0.2 Alpha  
**Last Updated:** February 1, 2026
