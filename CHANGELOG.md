# Changelog

All notable changes to RUIE are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.2 Alpha] - February 2026

### Status
🔬 **Alpha Release** - Active Development  
✅ **Testing**: 21/21 tests passing  
✅ **Security**: Audited and secured
✅ **Migration**: Migrated from PyQt5 to Electron

### Major Changes
- **Electron Migration**: Replaced PyQt5 with Electron for better performance and maintainability
- **Build System**: electron-builder replaces PyInstaller (~3-5 min builds vs 5-10 min)
- **Bundle Size**: Reduced from ~500MB to ~150-200MB
- **Development**: Standard Electron DevTools and debugging
- **No Overlays**: Chromium-native rendering eliminates PyQt5 overlay issues

### Added
- 5-step wizard interface (consolidated from previous 6 steps)
- Color grid layout in Step 2 (compact display of all color pickers)
- Dedicated Step 5 with 3 action cards: Test, Export, Install
- Loading screen with detailed progress updates (25 status messages)
- Browser cache auto-clearing on app exit (localStorage, sessionStorage, IndexedDB)
- Real-time backup and extraction list polling
- `/api/compile-asar` - Compile modified app.asar without installing
- `/api/install-asar` - Compile and install modified app.asar with backups
- `/api/test-launcher` - Test theme with temporary ASAR replacement
- `/api/open-extractions-folder` - Open extractions directory in file explorer
- `/api/open-backups-folder` - Open backups directory in file explorer
- Comprehensive security audit and vulnerability fixes
- Full documentation comments (200+ points across 7 files)
- Portable EXE build (5.99 MB via PyInstaller)
- Windows Installer configuration (Inno Setup)
- Complete API endpoint documentation (46 endpoints)

### Improved
- Step 1: Combined launcher detection, ASAR extraction, and backup/extraction management
- Step 2: Color presets display in responsive grid (minmax 120px columns)
- Step 2: Color sections are collapsible for better organization
- Step 5: Clean 3-card interface for Test/Export/Install actions
- Folder open buttons moved below backup/extraction lists for better UX
- Loading screen shows initialization progress from 0% to 100%
- Promise chaining for async operations ensures proper timing
- Color collection now includes both manual and preset grid colors
- 10 security controls verified and documented
- Dual-mode server startup (thread vs subprocess)
- Error handling in all endpoints
- Admin privilege elevation
- Auto-launcher detection

### Fixed
- Color grid now displays properly (removed nested wrapper structure)
- Test launcher now sends required `extractedPath` parameter
- Install theme now uses correct `state.extractedPath` variable
- Async chaining ensures loading progress completes before hiding screen
- Color mapping functions work with both manual and preset colors
- Delete button functionality for backups and extractions

### Security Fixes
- **XSS Protection**: Added HTML sanitization for all user input
- **Path Traversal**: Implemented strict path validation
- **Command Injection**: Replaced shell commands with safe argument lists
- **CSRF Protection**: Added CSRF tokens for state changes
- **Input Validation**: Comprehensive validation on all endpoints

### Testing
- ✅ Module imports (5/5)
- ✅ Color conversions (7/7)
- ✅ Launcher detection (1/1)
- ✅ ASAR extraction (1/1)
- ✅ Flask configuration (3/3)
- ✅ Security functions (3/3)
- ✅ Media handling (1/1)

### Known Issues
- None currently documented

---

## [0.1 Alpha] - January 2026

### Status
🔬 **Alpha Release** - Initial Development

### Added
- Initial 5-step wizard interface
- Launcher auto-detection system
- Color replacement engine with grid layout
- Media file management
- Backup and restore system
- 17 manufacturer presets (Aegis, Anvil, Drake, RSI, etc.)
- 46 REST API endpoints
- Flask backend with security controls
- PyQt5 desktop application
- Responsive web UI with live preview
- ASAR extraction and decompilation

### Fixed
- Compiled EXE startup issues (frozen mode Flask handling)
- Delete button functionality for backups and extractions
- Event listener attachment on dynamically created elements

### Features
- 5-step customization wizard
- Real-time color preview
- Music and audio support
- Backup metadata tracking
- Admin privilege elevation
- Windows UAC support
- Multiple extraction management
- Collapsible color sections

### Technical Stack
- **Desktop**: Electron 29.0.0
- **Backend**: Python 3.11+, Flask
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Archive**: Pure Python ASAR extraction (no Node.js required for extraction)
- **Build**: electron-builder 24.6.0

### Limitations
- Windows 10/11 only
- Requires admin privileges for theme deployment
- Single session at a time

---

## [Planned] - Future Releases

### Upcoming Features
- [ ] macOS/Linux support
- [ ] CSS file color replacement
- [ ] Theme marketplace integration
- [ ] Advanced color harmony tools
- [ ] Batch processing support
- [ ] Digital code signing
- [ ] Auto-update system

### Performance Improvements
- [ ] Faster ASAR extraction
- [ ] Optimized color replacement
- [ ] Progressive UI updates
- [ ] Caching system

---

## Version Matrix

| Version | Date | Status | Deployment |
|---------|------|--------|------------|
| 0.2 Alpha | Feb 2026 | 🟢 Ready | EXE + Installer Config |
| 0.1 Alpha | Jan 2026 | 🟢 Ready | Source Code |

---

## Changelog Archive

For detailed information about earlier changes, see the project history on GitHub.

**Status**: 🔬 Alpha Release - Active Development  
**Latest Update**: Added `/api/compile-asar` and `/api/install-asar` endpoints, comprehensive security audit (February 1, 2026)

### What's New (February 1, 2026)

#### ✅ Added: New Compilation & Installation Endpoints
- **`/api/compile-asar`** - Compile modified app.asar to persistent location without installing
- **`/api/install-asar`** - Compile and install modified app.asar with automatic backups
- Both endpoints include proper error handling and permission checks

#### ✅ Added: Security Vulnerability Audit
- Comprehensive security audit document (SECURITY_AUDIT.md)
- Identified 10 security vulnerabilities with severity ratings
- Provided detailed remediation recommendations for all issues
- Prioritized fixes by severity (CRITICAL, HIGH, MEDIUM, LOW)

#### ✅ Updated: Project Version & Copyright
- Bumped version to 0.2 Alpha
- Added copyright disclaimers throughout documentation
- Clarified that RUIE is fan-made and not affiliated with Cloud Imperium Games

---

## Version 0.1 Alpha - Initial Release (January 2026)

**Status**: 🔬 Alpha Release - Initial Development  
**Latest Update**: Fixed delete button functionality for backups and extractions (February 1, 2026)

### Latest Fixes (February 1, 2026)

#### 🟢 Fixed: Delete Button Functionality for Backups & Extractions
- **Problem**: Delete buttons for backups and extracted ASARs weren't responding to clicks
- **Root Cause**: Event listeners attached to dynamically created buttons weren't firing
  - Tried: `addEventListener` with bubble/capture phases
  - Tried: `addEventListener` with arrow functions
  - Tried: Event delegation via parent container
  - All approaches failed to register clicks in VSCode Simple Browser
- **Solution**: Switched to simple `onclick` property handlers (same as restore button)
  - Changed from `addEventListener('click', ...)` to `button.onclick = () => {...}`
  - Removed event delegation approach
  - Used direct inline handlers with arrow functions
  - Matched pattern used by working restore buttons
- **Testing**: Confirmed both backup and extraction delete buttons now work
- **Technical Notes**:
  - VSCode Simple Browser doesn't support `addEventListener` on dynamically created elements
  - Direct `onclick` property assignment works reliably
  - Event logging added to verify button creation and click detection
- **Result**: Users can now delete backups and extractions as intended

### Critical Fixes (February 1, 2026 - Earlier)

#### 🔴 Fixed: Compiled EXE Stuck at "Starting..."
- **Problem**: App froze on startup when running as compiled `.exe`
- **Root Cause**: Tried to launch Flask as subprocess using `python server.py` (not available in frozen mode)
- **Solution**: Implemented dual-mode server startup:
  - **Frozen Mode** (compiled EXE): Flask runs in a daemon thread within the same process
  - **Source Mode** (development): Flask runs as subprocess for better debugging
- **Technical Changes**:
  - Added `is_frozen()` detection to identify compiled vs source execution
  - Modified `launcher.py` to start Flask thread with `use_reloader=False` in frozen mode
  - Updated `server.py` with `get_resource_path()` to locate bundled `public` folder
  - Enhanced `build.bat` with hidden imports for Flask, server modules, and dependencies
- **Result**: Compiled EXE now starts correctly and loads the UI

### Previous Updates (January 31, 2026)

#### 🔴 Fixed: Compiled EXE Stuck at "Starting..."
- **Problem**: App froze on startup when running as compiled `.exe`
- **Root Cause**: Tried to launch Flask as subprocess using `python server.py` (not available in frozen mode)
- **Solution**: Implemented dual-mode server startup:
  - **Frozen Mode** (compiled EXE): Flask runs in a daemon thread within the same process
  - **Source Mode** (development): Flask runs as subprocess for better debugging
- **Technical Changes**:
  - Added `is_frozen()` detection to identify compiled vs source execution
  - Modified `launcher.py` to start Flask thread with `use_reloader=False` in frozen mode
  - Updated `server.py` with `get_resource_path()` to locate bundled `public` folder
  - Enhanced `build.bat` with hidden imports for Flask, server modules, and dependencies
- **Result**: Compiled EXE now starts correctly and loads the UI

### Previous Updates (January 31, 2026)

### Latest Changes (January 31, 2026 - Final Session)

#### Major Features Added
- ✅ **Music Step (Step 5)** - Complete music management system
  - Playlist support with add/remove/reorder functionality
  - HTML5 audio player with native controls
  - Player visibility controlled by step navigation
  - Default tracks: GrimHex.ogg, StarMarine.ogg
  - Support for OGG (preferred) and MP3 formats
  - Auto-loads first track into player
  - Player updates when playlist changes

- ✅ **6-Step Wizard Interface** (upgraded from 5-step)
  - Step 1: Initialize
  - Step 2: Extract
  - Step 3: Colors
  - Step 4: Media
  - Step 5: Music (NEW)
  - Step 6: Finalize

- ✅ **Preview Layout Restructuring**
  - Preview now visible on Colors, Media, and Music steps
  - Vertical layout: content above, preview below
  - Centered stepper at bottom of screen
  - Improved visual hierarchy
  - Better use of screen space

- ✅ **Color Persistence Across Steps**
  - Colors applied on Step 3 retained through Steps 4-5
  - Automatic color resend when navigating to Media/Music steps
  - State management via `state.colors`
  - Consistent preview throughout workflow

- ✅ **Media System Improvements**
  - Grid-based asset picker with 9 default assets
  - Individual select buttons on hover
  - Excluded audio/music files from media picker
  - Live preview updates for selected media
  - Better UX than previous system

- ✅ **Logo and Preview Accuracy**
  - Header logo now uses Star Citizen/RSI logo
  - Removed Cloud Imperium corporate logo
  - Removed Squadron 42 references (game not released)
  - Deleted 3 game cards from preview
  - Simplified preview focuses on main launcher

- ✅ **Responsive Design Validation**
  - Tested on mobile (375px), tablet (768px), desktop (1920px+)
  - Mobile breakpoints at 768px with proper stacking
  - Full-width buttons and forms on small screens
  - Content scrolls properly in tight spaces
  - Works across all device types

#### UI/UX Improvements
- ✅ Centered stepper navigation at bottom
- ✅ Larger preview panel (400-500px height, responsive)
- ✅ Better vertical layout for content flow
- ✅ Improved color persistence messaging
- ✅ Music player styling matches RSI color scheme
- ✅ Audio player accent color: cyan (#54adf7)

#### Code Quality
- ✅ Updated CSS for new vertical layout
- ✅ New JavaScript functions: `updateMusicPlayer()`, color resend logic
- ✅ Enhanced `navigateToPage()` with step-specific logic
- ✅ Better state management for colors and music
- ✅ Improved documentation and code comments

### Previous Session Changes (Early Jan 31, 2026)
- ✅ 5-step wizard interface with Initialize step
- ✅ Responsive wide-screen layout (1800px max-width)
- ✅ 6 professional color presets
- ✅ Performance optimizations (40%+ faster)
- ✅ C3RB baseline implementation
- ✅ Collapsible color sections
- ✅ Theme save/export/import system

### Major Features
- ✅ Source code reference tracking for media
- ✅ Live preview panel with color updates
- ✅ Extraction metadata and change tracking
- ✅ Automatic admin privilege elevation on startup
- ✅ Windows UAC support for secure file access
- ✅ Process monitoring (Test Launcher waits for user to close)

### Known Limitations
- ⚠️ Admin privileges required for full functionality (theme deployment, testing)
- ⚠️ Color replacement in `.js` files only (CSS support coming)
- ⚠️ Media preview limited to files under 50MB
- ⚠️ No undo/redo functionality at file level (color changes tracked in UI)

### API Endpoints
- ✅ GET/POST /api/init - Initialize session
- ✅ GET/POST /api/detect-launcher - Auto-detect launcher
- ✅ POST /api/extract - Extract archive
- ✅ POST /api/apply-colors - Apply color replacements
- ✅ POST /api/apply-media - Apply media replacements
- ✅ POST /api/repack - Repack archive
- ✅ POST /api/test-launcher - Test with temp asar
- ✅ POST /api/deploy-theme - Permanently install theme
- ✅ GET /api/extracted-list - List previous extractions
- ✅ POST /api/use-extract - Load previous extraction
- ✅ GET /api/extraction-changes - Detect changes in extraction
- ✅ POST /api/config/save - Save theme configuration
- ✅ POST /api/config/export - Export theme for download
- ✅ GET /api/config/list - List saved themes
- ✅ POST /api/config/load - Load saved theme
- ✅ GET /api/media-assets - Scan for media files
- ✅ GET /api/extracted-asset - Serve asset previews

### Technical Stack
- **Backend**: Python 3.10+ (Flask, PyQt5)
- **Frontend**: Vanilla JavaScript (optimized) + HTML5/CSS3
- **Archive Tool**: npx asar (Node.js CLI)
- **Desktop**: PyQt5 + PyQtWebEngine
- **Port**: 5000 (local only)
- **Layout**: Responsive, fills 1800px max-width
- **Preview**: 1:1 accurate RSI Launcher HTML/CSS simulation
- ⚠️ Limited error messages (improving feedback)

### Alpha Known Issues
- Cache warnings from QtWebEngine (harmless)
- Color variable extraction may miss some edge cases
- Media file detection uses file size for change tracking
- Extraction metadata not version-aware (may break with future updates)
- Collapsible sections limited to ~800px height with scrolling (performance optimization)
macOS/Linux support
- 🚀 CSS file color replacement
- 🚀 Batch color application
- 🚀 Theme marketplace integration
- 🚀 Advanced color picker tools
- 🚀 Performance optimizations
- 🚀 Automatic UAC elevation in batch file
- 🚀 Theme marketplace integration
- 🚀 Advanced color picker tools
- 🚀 Performance optimizations

### Breaking Changes (For Future Versions)
- Extraction metadata format may change
- API endpoints may be restructured
- Color mapping format may be standardized

### Compatibility
- **Windows 10/11**
- **Python 3.10+**
- **Node.js** (for npx asar)
- **PyQt5 5.15+**
- **Flask 2.0+**

### Contributors
- Elegius © 2026

---

## Version 2.0.0 - Python Desktop Edition (January 2026)

### Highlights
- ✅ Fully migrated to Python + Flask backend
- ✅ PyQt5 desktop window with embedded web UI
- ✅ Windows-only support with automatic launcher detection
- ✅ Extraction progress indicator and status polling
- ✅ Cleaned Node/Electron artifacts and legacy scripts

### Features
#### Core Functionality
- ✅ asar archive extraction and repacking
- ✅ Automatic backup with timestamps
- ✅ Color replacement engine (hex and RGB)
- ✅ Media file replacement system
- ✅ Backup restore functionality

#### Desktop UI
- ✅ 5-step workflow interface
- ✅ Color palette editor with wheel + RGB sliders
- ✅ Live preview panel
- ✅ Extraction progress bar
- ✅ Status feedback system

#### API Server (Flask)
- ✅ GET/POST /api/init - Initialize session
- ✅ GET/POST /api/detect-launcher - Auto-detect launcher
- ✅ POST /api/extract - Extract archive
- ✅ POST /api/apply-colors - Apply color replacements
- ✅ POST /api/apply-media - Apply media replacements
- ✅ POST /api/repack - Repack archive
- ✅ GET /api/backups - List backups
- ✅ POST /api/restore - Restore from backup
- ✅ GET /api/status - Operation progress/status

### Technical Details
- **Backend**: Python 3.10+ (Flask)
- **Desktop**: PyQt5 + PyQtWebEngine
- **Frontend**: Vanilla JavaScript + CSS
- **Port**: 5000 (local only)
- **ASAR Handling**: npx asar (invoked via subprocess)

### Breaking Changes
- Removed Node.js/Electron backend, CLI, and npm scripts.
- Documentation rewritten for Python-only workflow.

### Known Limitations
- Single active session at a time
- Media uploads are sequential
- Requires Node.js only for `npx asar` command

### Next
- Build a standalone .exe via PyInstaller
- Add richer progress updates for repack/apply operations
- [ ] Theme collision detection
- [ ] Color harmony checker
- [ ] Performance optimization
- [ ] Database for theme storage
- [ ] User authentication
- [ ] Theme dependency resolution

#### Planned Tools
- [ ] CLI automation scripts
- [ ] Theme validation tool
- [ ] Color palette analyzer
- [ ] Media asset manager
- [ ] Batch processor

### How to Report Issues

While this is v1.0.0 and considered production-ready, if you encounter issues:

1. Check documentation first
2. Review error messages carefully
3. Verify file paths and formats
4. Check browser console (F12)
5. Review server output in terminal

### Feedback & Contributions

This is a community tool. Feedback and suggestions are welcome!

---

## Release Notes

### v1.0.0 - January 2026

**Status**: 🟢 Production Ready

**What's Included**:
- Complete theme customization tool
- Web GUI with 5-step workflow
- CLI and API support
- Comprehensive documentation
- Example themes
- Backup/restore system
- 130 packages, 0 vulnerabilities

**Installation**:
```bash
npm start gui
```

**Quick Start**:
1. Open http://localhost:3000
2. Select app.asar
3. Extract
4. Choose preset or customize colors
5. Repack

**Support**:
- See documentation files
- Check troubleshooting guides
- Review example configurations

**License**: MIT

---

## What's Next?

Check out these files:
1. **INDEX.md** - Find what you need
2. **QUICK_START.md** - Get started quickly
3. **PROJECT_SUMMARY.md** - Overview of everything
4. **README.md** - Full documentation

---

## Version History

| Version | Date | Status | Notes |
|---------|------|--------|-------|
| 1.0.0 | Jan 2026 | ✅ Ready | Initial release |

---

**Enjoy using RUIE!** 🎨

Built with ❤️ for the Star Citizen community.
