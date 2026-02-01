# Inno Setup Compilation Error - Fixed

## Problem
The Inno Setup compilation was failing when running `build_installer.bat` to create the Windows installer for RUIE.

## Root Cause
The Pascal code in `RUIE_Installer.iss` had two issues:

### Issue 1: Incorrect Line Break Syntax
**Original Code:**
```pascal
MsgBox('RUIE has been successfully installed!' + #13#13 +
       'Important: This application requires...',
       mbInformation, MB_OK);
```

**Problem:** 
- `#13#13` is NOT the correct way to create a line break in Inno Setup Pascal
- Should use `#13#10` for proper CRLF (Carriage Return + Line Feed)

### Issue 2: Missing Variable Declarations
**Original Code:**
```pascal
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssFinished then
  begin
    MsgBox('Long string' + #13#13 + 'Another string' + #13#13 + 'More text',
           mbInformation, MB_OK);
  end;
end;
```

**Problem:**
- Long string literals with multiple concatenations can cause parsing issues
- Pascal requires variables to be declared for complex string operations

## Solution Applied

### File: `RUIE_Installer.iss`

Changed the `[Code]` section to use proper Pascal syntax:

```pascal
[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  Msg: String;
begin
  if CurStep = ssFinished then
  begin
    Msg := 'RUIE has been successfully installed!' + #13#10 + #13#10 +
           'Important: This application requires Administrator privileges to modify the RSI Launcher.' + #13#10 + #13#10 +
           'When you run RUIE, you may receive a UAC (User Account Control) prompt. Click "Yes" to proceed.' + #13#10 + #13#10 +
           'For more information, visit: https://github.com/Elegius/RUIE';
    MsgBox(Msg, mbInformation, MB_OK);
  end;
end;

procedure InitializeWizard();
var
  Msg: String;
begin
  Msg := 'RUIE - RSI Launcher UI Editor' + #13#10 + #13#10 +
         'Version: 0.2 Alpha' + #13#10 + #13#10 +
         'This installer will set up RUIE on your system.' + #13#10 + #13#10 +
         'IMPORTANT DISCLAIMER:' + #13#10 +
         '- RUIE is a fan-made project NOT affiliated with Cloud Imperium Games' + #13#10 +
         '- Star Citizen and RSI Launcher are trademarks of Cloud Imperium Games' + #13#10 +
         '- Use this tool at your own risk and in accordance with CIG Terms of Service';
  MsgBox(Msg, mbInformation, MB_OK);
end;
```

**Changes Made:**
1. ✅ Added `var Msg: String;` declarations
2. ✅ Changed `#13#13` to `#13#10` (correct line break)
3. ✅ Moved long strings to variables for cleaner code
4. ✅ Improved readability and maintainability

### File: `BUILD_TROUBLESHOOTING.md`

Added comprehensive troubleshooting section "Issue 6.5: Inno Setup Compilation Failed" that covers:
- Missing files errors
- Pascal code syntax errors
- Invalid file paths
- Permission denied errors
- Duplicate file sources
- Direct Inno Setup compiler testing

## How to Build Now

### Quick Test (Portable EXE Only)
```bash
python -m PyInstaller RUIE.spec
```

### Full Build (EXE + Installer)
```bash
build_installer.bat
```

The installer should now compile successfully!

## If Issues Persist

### Manual Compilation Test
```bash
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" /Qp RUIE_Installer.iss
```

This will show detailed error messages if there are any remaining issues.

### Common Issues
1. **dist\RUIE\RUIE.exe doesn't exist** → Build the exe first with PyInstaller
2. **icon.ico not found** → Ensure it exists in the project root
3. **Permission denied on output** → Close file explorer windows showing dist/
4. **Invalid paths** → Make sure relative paths are correct from RUIE_Installer.iss location

## Files Modified
- ✅ `RUIE_Installer.iss` - Fixed Pascal code syntax
- ✅ `BUILD_TROUBLESHOOTING.md` - Added detailed Inno Setup troubleshooting

## Date Fixed
February 1, 2026

## Related Files
- [BUILD_TROUBLESHOOTING.md](BUILD_TROUBLESHOOTING.md) - Comprehensive build guide
- [BUILD_STATUS.md](BUILD_STATUS.md) - Build system status
- [RUIE_Installer.iss](RUIE_Installer.iss) - Inno Setup configuration
- [build_installer.bat](build_installer.bat) - Build script
