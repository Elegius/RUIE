# Known Issues & Fixes

## Recently Fixed ✅

### Server Connection Timeout - FIXED & VERIFIED ✅ (February 1, 2026)
- **Issue**: App times out when trying to connect to Flask server in portable exe mode
- **Status**: ✅ **FULLY FIXED AND TESTED**
- **Root Causes Identified & Fixed**:
  - Missing sys.path configuration in frozen mode → ✅ FIXED: Added `sys.path.insert(0, sys._MEIPASS)`
  - Insufficient error logging for import failures → ✅ FIXED: Added detailed logging for each import
  - **Waitress not bundled** → ✅ FIXED: Added module-level `import waitress` to force PyInstaller inclusion
  - No timeout retry logic → ✅ FIXED: Added final 5-second timeout check
  - Generic error messages → ✅ FIXED: Added detailed troubleshooting suggestions
- **Solutions Implemented**:
  - Added sys.path setup to ensure modules can be imported in frozen mode
  - Enhanced logging for import errors with sys.path and _MEIPASS debug info
  - Added separate try/catch blocks for server and waitress imports
  - **CRITICAL:** Added module-level `import waitress` in launcher.py so PyInstaller bundles it
  - Added final connection attempt with 5-second timeout before giving up
  - Improved error message with specific solutions
  - Enhanced thread startup with 0.5s delay to allow server initialization
  - Updated requirements-build.txt to include `waitress>=2.1.0` dependency
- **Test Results**: ✅ VERIFIED
  - Server imports waitress successfully: "Waitress WSGI server imported successfully"
  - Server starts: "Production server starting on port 5000"
  - Server serves: "Serving on http://127.0.0.1:5000"
  - UI loads: "Loading UI from http://127.0.0.1:5000"
  - No timeouts or import failures observed
- **Implementation**: Enhanced `run_flask()` function and `check_and_load_ui()` method in launcher.py, plus module-level imports
- **Why This Was Tricky**: Even though waitress was in hiddenimports, PyInstaller marked it as "optional" because it was in a try/except block. Moving import to module level forced bundling.

### Loading Screen Layout Polish - Improved UI Spacing (February 1, 2026)
- **Issue**: Loading indicator icons were overlapping with status text
- **Status**: ✅ **FIXED**
- **Details**:
  - Adjusted icon and text spacing to prevent overlaps
  - Improved icon sizing and alignment (16px centered icons)
  - Enhanced gap between icons and text (10px separation)
  - Better vertical spacing between status items (8px margins)
  - Added padding to status container for breathing room
  - Changed alignment from center to left-aligned for cleaner appearance
- **Result**: Clean, professional loading screen with properly spaced indicators and text
- **Implementation**: CSS refinements in launcher.py loading screen HTML

### Startup Progress UI - Enhanced User Experience (February 1, 2026)
- **Issue**: Portable app appeared frozen on static "Starting" screen with no feedback
- **Status**: ✅ **FIXED**
- **Details**:
  - Implemented professional progress UI with progress bar and percentage display
  - Added real-time status messages ("Loading dependencies...", "Starting server...")
  - Created 3-step progress indicators with animated spinners
  - Added 35-second timeout protection with user-friendly error message
  - Embedded entire UI in launcher.py (~150 lines of HTML/CSS/JavaScript)
  - Progress updates at key checkpoints: 15%, 25%, 30%, 45%, 50%, then 50-100% during server wait
- **Result**: Users now see constant visual feedback during 5-15 second startup sequence
- **Reference**: See [STARTUP_PROGRESS_UI.md](STARTUP_PROGRESS_UI.md) for complete documentation

### Delete Button Functionality (February 1, 2026)
- **Issue**: Delete buttons for backups and extracted ASARs didn't respond to clicks
- **Status**: ✅ **FIXED**
- **Details**:
  - Delete buttons appeared in the UI but clicking them had no effect
  - Restore buttons worked fine, so the issue was specific to delete buttons
  - Root cause: Event listeners on dynamically created elements weren't firing in VSCode Simple Browser
  - Solution: Switched to direct `onclick` property handlers instead of `addEventListener`
  - Both backup and extraction deletion now work properly
  - Safety feature preserved: Cannot delete currently active extraction

---

## Current Known Limitations

### 1. Active Extraction Cannot Be Deleted
- **Status**: ℹ️ **EXPECTED BEHAVIOR**
- **Details**: The system prevents deletion of the currently loaded/active extraction
- **Reason**: Safety measure to prevent losing working extraction in the middle of editing
- **Workaround**: Select a different extraction first, then delete the original one
- **Impact**: Minor - only affects power users with multiple extractions

### 2. Windows Only
- **Status**: ⚠️ **LIMITATION**
- **Details**: RUIE only works on Windows 10/11
- **Reason**: Requires `asar` CLI and Windows-specific file paths
- **Workaround**: None currently available
- **Impact**: Mac/Linux users cannot use this tool

### 3. Admin Privileges Required
- **Status**: ℹ️ **EXPECTED REQUIREMENT**
- **Details**: App requires administrator permissions to modify launcher files
- **Reason**: RSI Launcher is installed in protected `Program Files` directory
- **Workaround**: App auto-requests UAC elevation on Windows
- **Impact**: Minimal - auto-handled by application

---

## Troubleshooting Guide

### "Cannot Delete" Extraction Error
**Symptom**: Trying to delete an extraction shows error "Cannot delete the currently active extraction"

**Solution**:
1. Click on a different extraction to select it
2. Try deleting the original extraction again
3. Or extract a fresh ASAR and work with that instead

**Technical Details**:
- Backend checks if the extraction path matches `theme_manager.extracted_dir`
- Only allows deletion if it's not the active one
- This is a safety feature to prevent losing work

### Delete Button Doesn't Respond
**Symptom**: Click delete button but nothing happens

**Solution**:
1. Open browser console (F12) to check for JavaScript errors
2. Restart the application
3. Try refreshing the page (F5)

**What to Check**:
- Console should show logs like `[Delete Button] Clicked, deleting: [path]`
- Server should return JSON response with success or error message
- Check `Documents\RUIE-debug.log` for server-side issues

---

## Fixed Issues Archive

### Issue: Compiled EXE Stuck at "Starting..." (February 1, 2026)
- **Status**: ✅ **FIXED**
- **Root Cause**: Flask server couldn't run as subprocess in frozen/compiled mode
- **Solution**: Implemented dual-mode startup with Flask running as daemon thread in frozen mode
- **Files Modified**: `launcher.py`, `server.py`, `build.bat`
- **Result**: Compiled EXE now starts and runs correctly

---

## Reporting New Issues

If you encounter a bug or issue:

1. **Check this file** - your issue might be listed here
2. **Check the logs** - review `Documents\RUIE-debug.log`
3. **Describe the issue** including:
   - Exact steps to reproduce
   - What you expected to happen
   - What actually happened
   - Your Windows version and Python version (if running from source)
4. **Include relevant logs** from debug file

---

## Future Improvements Planned

- [ ] Support for macOS and Linux
- [ ] Backup/extraction cloud sync
- [ ] Theme sharing marketplace
- [ ] Undo/redo for color changes
- [ ] Advanced color picker with hex/RGB input
- [ ] Batch media replacement
- [ ] Theme preview before applying
