# Building RUIE - Troubleshooting Guide

## Prerequisites

Before building RUIE, ensure you have:

1. **Python 3.10+**
   ```bash
   python --version
   ```
   Should show Python 3.10.x or higher

2. **Node.js** (for runtime use, not building)
   ```bash
   node --version
   ```

3. **Build Dependencies**
   ```bash
   pip install -r requirements-build.txt
   ```

---

## Build Methods

### Method 1: Quick Build (Portable EXE Only)

If you only want the standalone executable without an installer:

```bash
python -m PyInstaller RUIE.spec
```

**Output:** `dist/RUIE/RUIE.exe`

**Time:** ~5-15 minutes

---

### Method 2: Full Build (EXE + Installer)

For a professional installer experience:

1. **Install Inno Setup 6** (if not already installed)
   - Download: https://jrsoftware.org/isdl.php
   - Run installer with default settings
   - Install to: `C:\Program Files (x86)\Inno Setup 6`

2. **Run the build script**
   ```bash
   build_installer.bat
   ```

**Output:**
- `dist/RUIE/RUIE.exe` (portable executable)
- `dist/RUIE-0.2-Alpha-Installer.exe` (Windows installer)

**Time:** ~10-20 minutes total

---

## Common Build Issues & Solutions

### Issue 1: PyInstaller Not Found

**Error Message:**
```
'pyinstaller' is not recognized as a cmdlet, function, script file, or operable program.
```

**Solution:**
```bash
pip install -r requirements-build.txt
# or specifically:
pip install pyinstaller>=6.0.0
```

Then try again:
```bash
python -m PyInstaller RUIE.spec
```

---

### Issue 2: RUIE.spec Not Found

**Error Message:**
```
ERROR: Spec file "RUIE.spec" not found!
```

**Solution:**
1. Check you're in the correct directory:
   ```bash
   cd "c:\Users\Eloy\Documents\CERBERUS STUFF\CUSTOM LAUNCHER THEME\RUIE"
   ```

2. Verify RUIE.spec exists:
   ```bash
   dir RUIE.spec
   ```

3. If not, check it wasn't deleted:
   - The file should have been created with the latest update
   - If missing, re-create it or download from GitHub

---

### Issue 3: icon.ico Not Found

**Error Message:**
```
Error: Cannot find icon.ico
```

**Solution:**
1. Verify `icon.ico` exists in the project root:
   ```bash
   dir icon.ico
   ```

2. If missing, check if it's in a subdirectory:
   ```bash
   dir /s icon.ico
   ```

3. Update `RUIE.spec` to use the correct path:
   ```python
   datas=[
       ('public', 'public'),
       ('assets', 'assets'),
       ('path/to/icon.ico', '.'),  # Update this path
   ],
   ```

---

### Issue 4: Missing Python Dependencies

**Error Message:**
```
ModuleNotFoundError: No module named 'flask' (or PyQt5, etc.)
```

**Solution:**
```bash
pip install -r requirements.txt
pip install -r requirements-build.txt
```

---

### Issue 5: Permission Denied Error

**Error Message:**
```
PermissionError: [Errno 13] Permission denied: 'dist'
```

**Solution:**
1. Close any open Python processes:
   ```bash
   taskkill /F /IM python.exe
   ```

2. Delete the dist folder manually:
   ```bash
   rmdir /s /q dist
   rmdir /s /q build
   ```

3. Try building again:
   ```bash
   python -m PyInstaller RUIE.spec --clean
   ```

---

### Issue 6: Inno Setup Not Found (When Building Installer)

**Error Message:**
```
Error: Inno Setup 6 is not installed
```

**Solution:**
1. Download Inno Setup 6:
   - https://jrsoftware.org/isdl.php

2. Run the installer
   - Choose: "Full Installation"
   - Accept default location: `C:\Program Files (x86)\Inno Setup 6`

3. Verify installation:
   ```bash
   dir "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
   ```

4. Try building again:
   ```bash
   build_installer.bat
   ```

---

### Issue 7: Build Takes Too Long or Hangs

**Possible Causes:**
- Slow disk I/O
- Antivirus scanning during build
- Low disk space
- System resources exhausted

**Solutions:**
1. **Free up disk space:**
   ```bash
   # Check available space
   wmic logicaldisk get name,freespace
   ```
   Need at least 2GB free

2. **Disable antivirus temporarily:**
   - Pause Windows Defender
   - Pause any other antivirus software
   - Re-enable after build completes

3. **Close other applications:**
   - Close browsers, IDEs, heavy applications
   - Reduces system load

4. **Try with verbose output:**
   ```bash
   python -m PyInstaller RUIE.spec --log-level=DEBUG
   ```

5. **Use the `--clean` flag:**
   ```bash
   python -m PyInstaller RUIE.spec --clean
   ```

---

### Issue 8: EXE File is Too Large

**Problem:** Built exe is larger than expected (>500MB)

**Solutions:**
1. **Use UPX compression** (already enabled in spec):
   - Install UPX: https://upx.github.io/
   - Add to PATH
   - Build should automatically use it

2. **Check for duplicate dependencies:**
   ```bash
   # Look at what PyInstaller included
   python -m PyInstaller RUIE.spec -v
   ```

3. **Minimize included files:**
   - Review `datas` section in RUIE.spec
   - Only include necessary directories

---

### Issue 9: App Won't Run After Build

**Problem:** Built exe launches but immediately crashes

**Solutions:**
1. **Check the debug log:**
   ```bash
   type "%USERPROFILE%\Documents\RUIE-debug.log"
   ```

2. **Run with console window to see errors:**
   - Modify `RUIE.spec`:
   ```python
   exe = EXE(
       ...
       console=True,  # Show console for errors
       ...
   )
   ```
   - Rebuild
   - Run and check for error messages

3. **Verify all dependencies:**
   ```bash
   python -c "import flask; import PyQt5; print('OK')"
   ```

4. **Check if Node.js is installed** (needed at runtime):
   ```bash
   node --version
   npm --version
   ```

---

### Issue 10: Windows SmartScreen Warning

**Problem:** Windows shows "Unknown Publisher" warning

**This is normal for unsigned executables.**

**Solution for distribution:**
- Users can click "More info" → "Run anyway"
- Or: Obtain a code signing certificate and sign the exe

**To sign the executable:**
```bash
# Requires a code signing certificate
signtool sign /f certificate.pfx /p password /t http://timestamp.server.com RUIE.exe
```

---

## Build Verification

After a successful build, verify the output:

### Check for EXE
```bash
dir dist\RUIE\RUIE.exe
```
Should show a file ~300MB in size

### Test the EXE
```bash
# Navigate to dist\RUIE
cd dist\RUIE

# Run the executable
RUIE.exe
```

### Check for Installer (if built)
```bash
dir dist\RUIE-*.exe
```
Should show the installer file

---

## Advanced Build Options

### Clean Build
```bash
python -m PyInstaller RUIE.spec --clean
```
Removes old build artifacts before building

### Debug Build
```bash
python -m PyInstaller RUIE.spec --debug=all
```
Creates debug version with console window

### Verbose Output
```bash
python -m PyInstaller RUIE.spec --log-level=DEBUG
```
Shows detailed build information

### Onefile Distribution
To make a single .exe file (slower, larger):
1. Edit `RUIE.spec`
2. Change `exclude_binaries=True` to `exclude_binaries=False`
3. Rebuild

---

## Build Performance Tips

1. **Use SSD:** Building to SSD is much faster than HDD
2. **Disable antivirus:** Temporarily disable during build
3. **Close unnecessary apps:** Frees up system resources
4. **Use admin terminal:** Avoids permission issues
5. **Check disk space:** Ensure 2GB+ free space

---

## Getting Help

If you still have issues:

1. **Check the debug log:**
   ```bash
   type "%USERPROFILE%\Documents\RUIE-debug.log"
   ```

2. **Check PyInstaller output:**
   - Look for the "ERROR:" lines in the build output

3. **Search GitHub Issues:**
   - https://github.com/Elegius/RUIE/issues

4. **Try a clean rebuild:**
   ```bash
   rmdir /s /q dist build
   python -m PyInstaller RUIE.spec --clean
   ```

---

## Build Environment Variables

You can customize the build with environment variables:

```bash
# Set Python path explicitly
set PYTHONPATH=C:\Python314

# Run with specific logging level
set PYINSTALLER_LOGLEVEL=DEBUG

# Then build
python -m PyInstaller RUIE.spec
```

---

**Version:** 0.2 Alpha  
**Last Updated:** February 1, 2026  
**Python Version Required:** 3.10+  
**PyInstaller Version:** 6.0.0+
