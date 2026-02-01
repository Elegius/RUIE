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

### Issue 6.5: Inno Setup Compilation Failed

**Error Message:**
```
Error: Inno Setup compilation failed!
[Error in RUIE_Installer.iss at line X: ...]
```

**Common Causes & Solutions:**

#### **Missing Files Referenced in .iss**
The Inno Setup script tries to include files that don't exist yet.

**Solution:**
1. Make sure PyInstaller build succeeded first:
   ```bash
   python -m PyInstaller RUIE.spec --clean
   ```

2. Verify these files exist:
   ```bash
   dir dist\RUIE\RUIE.exe
   dir icon.ico
   dir LICENSE
   dir README.md
   ```

3. If files are missing, build the exe first, then run:
   ```bash
   build_installer.bat
   ```

#### **Pascal Code Syntax Errors**
The Pascal code in the `[Code]` section has syntax errors.

**Fixed in RUIE_Installer.iss (February 1, 2026):**
- Changed `#13#13` (incorrect line breaks) to `#13#10` (proper CRLF)
- Added variable declarations for message strings
- Improved message formatting

If you see Pascal compilation errors:
1. The latest version of RUIE_Installer.iss should fix these
2. If still broken, simplify the Code section:
   ```pascal
   [Code]
   procedure InitializeWizard();
   begin
     // Removed for debugging
   end;
   ```

#### **Invalid File Paths**
Inno Setup uses backslashes and expects relative paths from the .iss location.

**Example Fix:**
```ini
[Files]
; WRONG: Source: "c:\full\path\dist\RUIE\*"
; RIGHT: Relative path from RUIE_Installer.iss location
Source: "dist\RUIE\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
```

#### **OutputDir Permission Denied**
Inno Setup can't write to the output directory.

**Solution:**
1. Make sure `dist\` folder exists and is writable:
   ```bash
   mkdir dist
   ```

2. Close any file explorer windows showing dist/
3. Check permissions aren't read-only:
   - Right-click `dist` folder → Properties
   - Uncheck "Read-only" if checked
4. Retry compilation

#### **Duplicate File Sources**
Multiple sources pointing to same destination.

**Check in RUIE_Installer.iss:**
```ini
[Files]
Source: "dist\RUIE\RUIE.exe"; DestDir: "{app}"; ...  ; Line 1
Source: "dist\RUIE\*"; DestDir: "{app}"; ...          ; Line 2 - includes exe again!
```

**Fix:** Remove duplicate entries. The wildcard `*` already includes RUIE.exe.

---

### Troubleshooting Inno Setup Compilation Directly

If `build_installer.bat` fails, try running Inno Setup compiler directly for better error messages:

```batch
REM Compile the installer script
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" RUIE_Installer.iss

REM With quiet mode (less verbose output)
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" /Q RUIE_Installer.iss
```

The error messages will be more detailed and show exactly which line is problematic.

#### **Common ISCC.exe Flags**
| Flag | Purpose |
|------|---------|
| (none) | Normal compilation with console output |
| `/Q` | Quiet mode - minimal output |
| `/O directory` | Specify output directory |
| `/Qp` | Quiet + progress bar |

**Note:** The `/cc` flag mentioned in older documentation is **not valid** for ISCC.exe and should not be used.

---

### Issue 6.6: Unknown Option "/cc"

**Error Message:**
```
Unknown option: /cc
Error: Inno Setup compilation failed
```

**Cause:**
The `/cc` flag is not a valid option for ISCC.exe compiler. This flag was incorrectly specified in older build scripts.

**Solution:**
Use the correct syntax without the `/cc` flag:

```batch
REM WRONG (old script)
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" /cc RUIE_Installer.iss

REM CORRECT (current script)
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" RUIE_Installer.iss
```

**Why it was wrong:**
- The Inno Setup ISCC.exe compiler doesn't have a `/cc` option
- Valid flags are: `/Q`, `/O`, `/Qp`, `/Qr`, `/Qi`
- The script file should be the only required argument
- The `.iss` script file specifies compilation settings (OutputDir, etc.)

**How to fix:**
- If using `build_installer.bat`: It's already fixed (updated Feb 1, 2026)
- If using manual command: Just omit the `/cc` flag

The latest version of `build_installer.bat` has been corrected to use the proper syntax.

---

### Issue 6.7: Missing Wizard Image Files

**Error Message:**
```
Error on line 25: Could not read "C:\Program Files (x86)\Inno Setup 6\wizmodernimage-is.bmp".
Error: The system cannot find the file specified.
Compile aborted.
```

**Cause:**
The `.iss` script file was referencing custom wizard image files that don't exist in the Inno Setup installation:
```ini
WizardImageFile=compiler:wizmodernimage-is.bmp
WizardSmallImageFile=compiler:wizmodernsmallimage-is.bmp
```

These files may be missing or have different names in your Inno Setup version.

**Solution:**
Remove the wizard image file references and let Inno Setup use its default modern wizard design.

**In RUIE_Installer.iss:**
```ini
[Setup]
; ... other settings ...
WizardStyle=modern
UninstallDisplayIcon={app}\RUIE.exe
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64

; REMOVE these lines:
; WizardImageFile=compiler:wizmodernimage-is.bmp
; WizardSmallImageFile=compiler:wizmodernsmallimage-is.bmp
```

**Why it was fixed:**
- The `compiler:` prefix doesn't work reliably with custom image paths
- The modern wizard style has built-in default images
- Removing these lines maintains a professional appearance
- The installer will use Inno Setup's default modern wizard theme

**Result:**
The installer will compile successfully and display the professional modern wizard interface with Inno Setup's default images.

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
