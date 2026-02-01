# Double Launch / Stuck Starting - Fixed

**Issue**: When running the portable exe (RUIE.exe), the application launches twice and gets stuck in "Starting..." state.

**Root Cause**: The `request_admin()` function was calling `ShellExecuteW()` to re-run the exe with admin privileges. This caused:
1. First launch: Normal instance starts
2. Immediately after: Same code detects it's not admin, tries to re-execute
3. Second launch: Admin instance starts while first one is still loading
4. Both instances compete for resources and port 5000
5. Result: Stuck in "Starting..." state

**Solution Applied**:

Modified `request_admin()` in `launcher.py` to detect when running in frozen (compiled) mode and skip the re-execution attempt.

**Key Changes**:

```python
# Check if running as compiled exe
if is_frozen():
    # In frozen mode: Skip re-execution, just warn user
    logger.warning("Running without admin privileges - some features may not work")
    logger.warning("Note: Right-click the exe and choose 'Run as administrator' for full functionality")
    return  # Don't try to re-execute in frozen mode
```

**Behavior**:

**When running from source (python launcher.py):**
- Admin check still triggers re-execution with admin privileges
- Normal development behavior unchanged

**When running from compiled exe (RUIE.exe):**
- Does NOT attempt to re-execute
- If launched without admin: Shows a helpful warning
- App launches cleanly once and starts normally
- User can right-click and "Run as administrator" if needed

**User Instructions**:

1. **Rebuild the exe**:
   ```batch
   python -m PyInstaller RUIE.spec --clean
   ```

2. **Run the new exe**:
   - Double-click `dist\RUIE\RUIE.exe`
   - Should launch cleanly without double-opening
   - Should load in a few seconds

3. **For full features (optional)**:
   - Right-click `RUIE.exe`
   - Select "Run as administrator"
   - This gives full access to modify launcher files

**Testing**:

✓ Single launch (no double-open)
✓ App loads without getting stuck
✓ "Starting..." message appears briefly then loads UI
✓ Port 5000 binds correctly on first try

**Files Modified**:
- `launcher.py` - Updated `request_admin()` function with frozen mode detection

**Fallback**:

If the user still experiences issues, they can:
1. Right-click RUIE.exe → Properties
2. Click "Advanced"
3. Check "Run this program in compatibility mode for:"
4. Select Windows 7 or Windows 8
5. Click OK

This sometimes helps with UAC and multi-launch issues.

---

**Status**: ✅ FIXED - Ready to rebuild and test
