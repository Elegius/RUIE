# Changelog

## Version 0.1 Alpha - Initial Release (January 2026)

**Status**: 🔬 Alpha Release - Active Development  
**Latest Update**: Complete UI/UX overhaul with music management & preview improvements (January 31, 2026)

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
