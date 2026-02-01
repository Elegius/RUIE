# Build Troubleshooting Guide

## Common Build Issues & Solutions

### Issue: PyInstaller Compilation Fails

**Error**: `Failed to execute script launcher`

**Causes**:
- Missing dependencies in `requirements-build.txt`
- Incompatible Python version (requires Python 3.8+)
- Corrupted `__pycache__` directory

**Solutions**:
1. Clean the build directory:
   ```bash
   rmdir /s build
   rmdir /s dist
   del RUIE.spec
   ```

2. Reinstall dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements-build.txt
   ```

3. Rebuild:
   ```bash
   build_installer.bat
   ```

---

### Issue: "Access Denied" When Building

**Error**: `Permission denied` or `Access is denied`

**Causes**:
- Antivirus blocking file operations
- Running script without administrator privileges
- Files locked by other processes

**Solutions**:
1. Run Command Prompt as Administrator
2. Close all instances of RUIE.exe and any text editors
3. Temporarily disable antivirus during build
4. Try building again:
   ```bash
   build_installer.bat
   ```

---

### Issue: Inno Setup Installer Build Fails

**Error**: `Error compiling installation script`

**Causes**:
- Inno Setup 6 not installed
- Invalid path in `RUIE.iss`
- Missing `dist/RUIE/` directory from PyInstaller step

**Solutions**:
1. Install Inno Setup 6 (free from https://jrsoftware.org/isdl.php)
2. Ensure PyInstaller completed successfully (check `dist/` folder exists)
3. Verify paths in `RUIE.iss` match your installation
4. Rebuild:
   ```bash
   build_installer.bat
   ```

---

### Issue: Output Files Are Too Large

**Causes**:
- Including unnecessary dependencies
- Debug symbols not stripped
- Bundling all assets multiple times

**Solutions**:
1. Review `RUIE.spec` and remove unnecessary hidden imports
2. Use PyInstaller's `--strip` flag (already configured in build script)
3. Verify only needed assets are in `assets/` directory

---

### Issue: "ModuleNotFoundError" When Running Built Executable

**Error**: `ModuleNotFoundError: No module named 'flask'` (or other module)

**Causes**:
- Missing entry in `requirements.txt`
- Module not included in PyInstaller hidden imports
- Spelling error in module name

**Solutions**:
1. Add missing module to `requirements-build.txt`:
   ```bash
   pip install module_name
   ```

2. Add to `RUIE.spec` hidden imports section:
   ```python
   hiddenimports=['module_name']
   ```

3. Rebuild:
   ```bash
   build_installer.bat
   ```

---

### Issue: Server Port Already in Use

**Error**: `Address already in use` or `Port 5000 already in use`

**Causes**:
- Previous RUIE instance still running
- Another application using port 5000
- Port not properly released after crash

**Solutions**:
1. Kill the process using the port:
   ```powershell
   netstat -ano | findstr :5000
   taskkill /PID <PID> /F
   ```

2. Alternatively, modify the port in `launcher.py`:
   ```python
   app.run(port=5001)  # Use different port
   ```

3. Restart the application

---

### Issue: ASAR Extraction Fails

**Error**: `Failed to extract ASAR` or file corrupted

**Causes**:
- Original `app.asar` is locked or being modified
- RSI Launcher still running
- Insufficient disk space

**Solutions**:
1. Close RSI Launcher completely
2. Close File Explorer windows accessing `Program Files`
3. Check available disk space (need ~500MB free)
4. Verify original ASAR location:
   ```
   C:\Program Files\Roberts Space Industries\RSI Launcher\resources\app.asar
   ```
5. Try extraction again

---

### Issue: Installer Won't Run on Target Machine

**Causes**:
- Target machine missing Visual C++ Redistributable
- UAC (User Account Control) blocking installation
- Installer corrupted during transfer

**Solutions**:
1. Install Visual C++ Runtime:
   - Download from: https://support.microsoft.com/en-us/help/2977003
   - Or use: `https://aka.ms/vs/17/release/vc_redist.x64.exe`

2. Disable UAC temporarily during installation
3. Re-download and verify installer integrity (check file size matches build output)

---

### Issue: Build Script Returns "Command Not Found"

**Error**: `build_installer.bat: command not found` or similar

**Causes**:
- Running on non-Windows system
- Script not in current directory
- Using wrong shell (Bash instead of CMD/PowerShell)

**Solutions**:
1. Ensure you're in the RUIE project root:
   ```bash
   cd path\to\RUIE
   ```

2. Run from Command Prompt or PowerShell (not Git Bash):
   ```bash
   build_installer.bat
   ```

3. On Linux/Mac, modify the build script to bash format

---

## Build Prerequisites Checklist

- [ ] Python 3.8+ installed (`python --version`)
- [ ] All dependencies installed (`pip install -r requirements-build.txt`)
- [ ] Inno Setup 6 installed
- [ ] Administrator access/UAC enabled
- [ ] ~1GB free disk space
- [ ] No antivirus blocking file operations
- [ ] Internet connection (for downloading dependencies)

---

## Getting Help

If you encounter an issue not listed here:

1. **Check the debug log**:
   ```
   C:\Users\[YourUsername]\Documents\RUIE-debug.log
   ```

2. **Enable verbose output**:
   Edit `build_installer.bat` and add debug flags to PyInstaller command

3. **Test the Python version directly**:
   ```bash
   python launcher.py
   ```

4. **Review the build output carefully** for the exact error message

---

**Version**: 0.2 Alpha  
**Last Updated**: February 1, 2026
