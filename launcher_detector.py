import os
import winreg
from pathlib import Path

class LauncherDetector:
    """Detect RSI Launcher installation on Windows."""
    
    @staticmethod
    def get_launcher_paths():
        """Return common RSI Launcher installation paths."""
        paths = [
            r'C:\Program Files\Roberts Space Industries\RSI Launcher\RSI Launcher.exe',
            r'C:\Program Files (x86)\Roberts Space Industries\RSI Launcher\RSI Launcher.exe',
        ]
        
        # Check registry
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall') as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    subkey_name = winreg.EnumKey(key, i)
                    try:
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            display_name, _ = winreg.QueryValueEx(subkey, 'DisplayName')
                            if 'RSI' in display_name or 'Launcher' in display_name:
                                install_location, _ = winreg.QueryValueEx(subkey, 'InstallLocation')
                                exe_path = os.path.join(install_location, 'RSI Launcher.exe')
                                if os.path.exists(exe_path):
                                    paths.append(exe_path)
                    except:
                        pass
        except:
            pass
        
        return list(set(paths))
    
    @staticmethod
    def find_asar(launcher_path, max_depth=6):
        """Find app.asar near the launcher path."""
        if not launcher_path or not os.path.exists(launcher_path):
            return None
        
        start_dir = os.path.dirname(launcher_path)
        queue = [(start_dir, 0)]
        visited = set()
        
        while queue:
            current_dir, depth = queue.pop(0)
            
            if depth > max_depth or current_dir in visited:
                continue
            
            visited.add(current_dir)
            
            try:
                for entry in os.listdir(current_dir):
                    if entry.lower() == 'app.asar':
                        return os.path.join(current_dir, entry)
                    
                    full_path = os.path.join(current_dir, entry)
                    if os.path.isdir(full_path) and entry.lower() not in ['node_modules', '.git']:
                        queue.append((full_path, depth + 1))
            except PermissionError:
                pass
        
        return None
    
    @staticmethod
    def detect():
        """Detect RSI Launcher installation."""
        for path in LauncherDetector.get_launcher_paths():
            if os.path.exists(path):
                asar_path = LauncherDetector.find_asar(path)
                if asar_path and os.path.exists(asar_path):
                    return {
                        'exePath': path,
                        'launcherPath': path,
                        'asarPath': asar_path,
                        'directory': os.path.dirname(path),
                        'resourcesDir': os.path.dirname(asar_path)
                    }
        
        return None
