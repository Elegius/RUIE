import os
import winreg
import subprocess
from pathlib import Path

class LauncherDetector:
    """Detect RSI Launcher installation on Windows."""
    
    @staticmethod
    def is_launcher_running():
        """Check if RSI Launcher process is currently running."""
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
        """Return common RSI Launcher installation paths, with Program Files first."""
        # Default installation locations - Program Files is always checked first
        paths = [
            r'C:\Program Files\Roberts Space Industries\RSI Launcher\RSI Launcher.exe',
            r'C:\Program Files (x86)\Roberts Space Industries\RSI Launcher\RSI Launcher.exe',
        ]
        
        # Check these alternative locations only as fallback
        alternative_paths = [
            r'C:\Games\Roberts Space Industries\RSI Launcher\RSI Launcher.exe',
            r'C:\Games\RSI\RSI Launcher\RSI Launcher.exe',
        ]
        
        # Check registry for installation location
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
        all_paths = paths + registry_paths + alternative_paths
        return list(dict.fromkeys(all_paths))  # Remove duplicates while preserving order
    
    @staticmethod
    def find_asar(launcher_path, max_depth=8):
        """Find app.asar near the launcher path."""
        if not launcher_path or not os.path.exists(launcher_path):
            print(f"[find_asar] Invalid path: {launcher_path}")
            return None
        
        start_dir = os.path.dirname(launcher_path)
        print(f"[find_asar] Starting search from: {start_dir}")
        queue = [(start_dir, 0)]
        visited = set()
        dirs_checked = 0
        
        while queue:
            current_dir, depth = queue.pop(0)
            
            if depth > max_depth or current_dir in visited:
                continue
            
            visited.add(current_dir)
            dirs_checked += 1
            
            try:
                for entry in os.listdir(current_dir):
                    if entry.lower() == 'app.asar':
                        print(f"[find_asar] Found app.asar at: {os.path.join(current_dir, entry)}")
                        return os.path.join(current_dir, entry)
                    
                    full_path = os.path.join(current_dir, entry)
                    if os.path.isdir(full_path) and entry.lower() not in ['node_modules', '.git', '__pycache__']:
                        queue.append((full_path, depth + 1))
            except (PermissionError, OSError) as e:
                pass
        
        print(f"[find_asar] Searched {dirs_checked} directories, no app.asar found")
        return None
    
    @staticmethod
    def detect():
        """Detect RSI Launcher installation."""
        paths = LauncherDetector.get_launcher_paths()
        print(f"[LauncherDetector] Checking {len(paths)} potential paths for launcher...")
        
        for path in paths:
            print(f"[LauncherDetector] Checking path: {path}")
            if os.path.exists(path):
                print(f"[LauncherDetector] Path exists: {path}")
                asar_path = LauncherDetector.find_asar(path)
                if asar_path and os.path.exists(asar_path):
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
        
        print("[LauncherDetector] No launcher installation detected")
        return None
