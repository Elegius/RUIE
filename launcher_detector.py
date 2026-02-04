"""
Launcher Detector Module
========================

This module is responsible for automatically detecting the RSI Launcher installation
on Windows systems. It provides utilities for:

1. Finding RSI Launcher.exe in common installation locations
2. Locating the app.asar file (the main launcher application)
3. Checking if the launcher is currently running
4. Using Windows Registry to find custom installation paths

The module uses multiple detection strategies:
- Hardcoded common installation paths (Program Files, alternate locations)
- Windows Registry queries for installed applications
- Recursive directory searching for app.asar

This ensures the application can work even with custom installation paths.
"""

import os
import winreg  # Windows Registry module
import subprocess
from pathlib import Path

class LauncherDetector:
    """Detect RSI Launcher installation on Windows systems.
    
    This class handles all detection logic for finding the RSI Launcher
    and its associated app.asar file which contains the launcher UI.
    """
    
    @staticmethod
    def is_launcher_running():
        """Check if RSI Launcher process is currently running.
        
        Uses Windows tasklist to check for running processes.
        
        Returns:
            bool: True if RSI Launcher.exe is running, False otherwise
        """
        try:
            # Use tasklist command to check for running processes
            result = subprocess.run(
                ['tasklist'],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Check if "RSI Launcher.exe" appears in the task list
            if 'RSI Launcher.exe' in result.stdout:
                return True
            
            return False
        except Exception as e:
            print(f"Error checking launcher process: {e}")
            return False
    
    @staticmethod
    def get_launcher_paths():
        """Return list of common RSI Launcher installation paths to check.
        
        The detection strategy is:
        1. Program Files (64-bit and 32-bit)
        2. Registry-based locations (custom installs)
        3. Alternative manual installation paths
        
        Returns:
            list: List of potential launcher paths to check
        """
        # Default installation locations - Program Files is always checked first
        # These are the most common installation paths for RSI Launcher
        paths = [
            r'C:\Program Files\Roberts Space Industries\RSI Launcher\RSI Launcher.exe',
            r'C:\Program Files (x86)\Roberts Space Industries\RSI Launcher\RSI Launcher.exe',
        ]
        
        # Check these alternative locations only as fallback
        # Some users may install in custom locations
        alternative_paths = [
            r'C:\Games\Roberts Space Industries\RSI Launcher\RSI Launcher.exe',
            r'C:\Games\RSI\RSI Launcher\RSI Launcher.exe',
        ]
        
        # Check Windows Registry for installation location
        # The registry contains information about installed applications
        registry_paths = []
        for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            for subpath in [r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
                           r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall']:
                try:
                    with winreg.OpenKey(hive, subpath) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            subkey_name = winreg.EnumKey(key, i)
                            try:
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    try:
                                        display_name, _ = winreg.QueryValueEx(subkey, 'DisplayName')
                                        # Look for RSI or Launcher in the application name
                                        if 'RSI' in display_name or 'Launcher' in display_name:
                                            try:
                                                install_location, _ = winreg.QueryValueEx(subkey, 'InstallLocation')
                                                if install_location:
                                                    exe_path = os.path.join(install_location, 'RSI Launcher.exe')
                                                    registry_paths.append(exe_path)
                                            except:
                                                pass
                                    except:
                                        pass
                            except:
                                pass
                except:
                    pass
        
        # Combine paths: Program Files first, then registry paths, then alternatives
        # This preserves detection priority while avoiding duplicates
        all_paths = paths + registry_paths + alternative_paths
        return list(dict.fromkeys(all_paths))  # Remove duplicates while preserving order
    
    @staticmethod
    def find_asar(launcher_path, max_depth=8):
        """Find app.asar file near the launcher executable.
        
        Uses breadth-first search to find app.asar up to max_depth directories
        from the launcher location. This is more robust than relying on fixed
        directory structures which may change between launcher versions.
        
        Args:
            launcher_path (str): Path to RSI Launcher.exe
            max_depth (int): Maximum directory depth to search (default: 8)
            
        Returns:
            str: Path to app.asar if found, None otherwise
        """
        if not launcher_path or not os.path.exists(launcher_path):
            print(f"[find_asar] Invalid path: {launcher_path}")
            return None
        
        # Start search from the directory containing the launcher
        start_dir = os.path.dirname(launcher_path)
        print(f"[find_asar] Starting search from: {start_dir}")
        
        # Use a queue for breadth-first search
        # Tuple format: (directory_path, current_depth)
        queue = [(start_dir, 0)]
        visited = set()  # Track visited directories to avoid loops
        dirs_checked = 0
        
        while queue:
            current_dir, depth = queue.pop(0)
            
            # Stop if we've gone too deep or already visited this directory
            if depth > max_depth or current_dir in visited:
                continue
            
            visited.add(current_dir)
            dirs_checked += 1
            
            try:
                # Search for app.asar in current directory
                for entry in os.listdir(current_dir):
                    if entry.lower() == 'app.asar':
                        # Found it!
                        print(f"[find_asar] Found app.asar at: {os.path.join(current_dir, entry)}")
                        return os.path.join(current_dir, entry)
                    
                    # Queue subdirectories for search (but skip common non-useful dirs)
                    full_path = os.path.join(current_dir, entry)
                    if os.path.isdir(full_path) and entry.lower() not in ['node_modules', '.git', '__pycache__']:
                        queue.append((full_path, depth + 1))
            except (PermissionError, OSError) as e:
                # Skip directories we can't access
                pass
        
        # If we get here, app.asar was not found
        print(f"[find_asar] Searched {dirs_checked} directories, no app.asar found")
        return None
    
    @staticmethod
    def detect():
        """Auto-detect RSI Launcher installation on the system.
        
        This is the main entry point for launcher detection. It:
        1. Gets all potential launcher paths
        2. Checks each path for existence
        3. Searches for app.asar near each launcher
        4. Returns complete information about the launcher
        
        Returns:
            dict: Dictionary with launcher info if found:
                {
                    'exePath': path_to_launcher_exe,
                    'launcherPath': path_to_launcher_exe,
                    'asarPath': path_to_app_asar,
                    'directory': launcher_directory,
                    'resourcesDir': directory_containing_asar
                }
            None: If launcher installation is not found
        """
        paths = LauncherDetector.get_launcher_paths()
        print(f"[LauncherDetector] Checking {len(paths)} potential paths for launcher...")
        
        for path in paths:
            print(f"[LauncherDetector] Checking path: {path}")
            if os.path.exists(path):
                print(f"[LauncherDetector] Path exists: {path}")
                asar_path = LauncherDetector.find_asar(path)
                if asar_path and os.path.exists(asar_path):
                    # Found a complete launcher installation
                    print(f"[LauncherDetector] Found app.asar at: {asar_path}")
                    return {
                        'exePath': path,
                        'launcherPath': path,
                        'asarPath': asar_path,
                        'directory': os.path.dirname(path),
                        'resourcesDir': os.path.dirname(asar_path)
                    }
                else:
                    print(f"[LauncherDetector] No app.asar found near {path}")
            else:
                print(f"[LauncherDetector] Path does not exist: {path}")
        
        # No launcher found
        print("[LauncherDetector] No launcher installation detected")
        return None
