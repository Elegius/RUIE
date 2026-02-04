#!/usr/bin/env python3
"""
Quick launcher detection test script.

This script helps debug launcher detection issues by:
1. Showing all paths that will be checked
2. Printing which paths exist
3. Attempting to detect the launcher
4. Reporting the result

Run this to see why launcher detection might be failing.
"""

import os
import sys
from launcher_detector import LauncherDetector

def main():
    print("=" * 70)
    print("RSI LAUNCHER DETECTION TEST")
    print("=" * 70)
    print()
    
    # Get the list of paths to check
    print("Paths that will be checked:")
    print("-" * 70)
    paths = LauncherDetector.get_launcher_paths()
    
    print(f"\nTotal paths to check: {len(paths)}\n")
    
    existing_paths = []
    missing_paths = []
    
    for i, path in enumerate(paths, 1):
        exists = os.path.exists(path)
        status = "✓ EXISTS" if exists else "✗ MISSING"
        print(f"{i:2d}. [{status}] {path}")
        
        if exists:
            existing_paths.append(path)
        else:
            missing_paths.append(path)
    
    print()
    print("=" * 70)
    print(f"Found {len(existing_paths)} existing launcher paths:")
    if existing_paths:
        for path in existing_paths:
            print(f"  ✓ {path}")
    else:
        print("  None found")
    
    print()
    print(f"Missing {len(missing_paths)} paths:")
    if missing_paths and len(missing_paths) <= 5:
        for path in missing_paths[:5]:
            print(f"  ✗ {path}")
        if len(missing_paths) > 5:
            print(f"  ... and {len(missing_paths) - 5} more")
    print()
    
    # Attempt actual detection
    print("=" * 70)
    print("RUNNING DETECTION...")
    print("=" * 70)
    print()
    
    result = LauncherDetector.detect()
    
    print()
    print("=" * 70)
    if result:
        print("✓ DETECTION SUCCESSFUL!")
        print("=" * 70)
        print(f"Launcher executable: {result.get('exePath')}")
        print(f"App.asar path:       {result.get('asarPath')}")
        print(f"Resources dir:       {result.get('resourcesDir')}")
    else:
        print("✗ DETECTION FAILED!")
        print("=" * 70)
        print()
        print("Suggestions:")
        print("1. Verify RSI Launcher is actually installed")
        print("2. Check that the installation path matches one of the paths above")
        print("3. If installed in a custom location, use the Browse button to locate app.asar manually")
        print("4. Ensure app.asar file exists in the launcher installation directory")
        print("5. Check file permissions - the application needs read access to the launcher files")
    
    print()
    print("=" * 70)

if __name__ == '__main__':
    main()
