import sys
import os
import subprocess
import time
import socket
import ctypes
import threading
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtGui import QIcon

# Version info
APP_VERSION = "0.1 Alpha"
APP_NAME = "RUIE"

def is_admin():
    """Check if running with admin privileges."""
    try:
        # Try using kernel32 instead of shell
        return ctypes.windll.kernel32.GetFileAttributesW('C:\\Program Files') != -1
    except Exception as e:
        return False

def request_admin():
    """Request admin privileges if not already elevated."""
    is_admin_now = is_admin()
    if not is_admin_now:
        print("[App] Requesting administrator privileges...")
        try:
            # Re-run this script with admin privileges
            script = sys.argv[0]
            ctypes.windll.shell.ShellExecuteW(None, "runas", script, "", None, 0)
            sys.exit(0)
        except Exception as e:
            print(f"[App] Could not request elevation: {e}")
            print("[App] Running without admin privileges - some features may not work")
    else:
        print("[App] ✓ Running with admin privileges ✓")

class LauncherApp(QMainWindow):
    def __init__(self, port=5000):
        super().__init__()
        self.port = port
        self.server_process = None
        
        self.setWindowTitle(f'{APP_NAME} v{APP_VERSION}')
        self.setGeometry(100, 100, 1280, 820)
        self.setMinimumSize(1024, 700)
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Create web view
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)
        
        # Show loading message
        self.browser.setHtml('<html><body style="background:#0a1d29; color:#e0e0e0; font-family:Segoe UI; display:flex; align-items:center; justify-content:center;"><h2>Starting...</h2></body></html>')
        
        # Start server
        self.start_server()
        
        # Load UI after server is ready
        self.check_and_load_ui()
    
    def start_server(self):
        """Start the Flask server as a subprocess."""
        try:
            project_root = str(Path(__file__).parent)
            
            print(f'[App] Starting Flask server...')
            
            # On Windows, hide the subprocess window
            startupinfo = None
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            self.server_process = subprocess.Popen(
                ['python', 'server.py'],
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                startupinfo=startupinfo
            )
            print(f'[App] Server process started with PID: {self.server_process.pid}')
            
            # Start threads to read server output
            import threading
            def read_output():
                try:
                    while True:
                        line = self.server_process.stdout.readline()
                        if not line:
                            break
                        print(f'[Server] {line.rstrip()}')
                except:
                    pass
            
            def read_errors():
                try:
                    while True:
                        line = self.server_process.stderr.readline()
                        if not line:
                            break
                        print(f'[Server Error] {line.rstrip()}')
                except:
                    pass
            
            output_thread = threading.Thread(target=read_output, daemon=True)
            error_thread = threading.Thread(target=read_errors, daemon=True)
            output_thread.start()
            error_thread.start()
            
        except Exception as e:
            print(f'[App Error] Failed to start server: {e}')
            self.show_error(f'Failed to start server: {e}')
    
    def is_server_ready(self):
        """Check if the server is responding on the configured port."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', self.port))
            sock.close()
            return result == 0
        except:
            return False
    
    def check_and_load_ui(self):
        """Check if server is ready and load UI."""
        if self.is_server_ready():
            print(f'[App] Server is ready on port {self.port}')
            self.load_ui()
        else:
            print(f'[App] Waiting for server to be ready...')
            QTimer.singleShot(1000, self.check_and_load_ui)
    
    def load_ui(self):
        """Load the web UI."""
        url = QUrl(f'http://127.0.0.1:{self.port}')
        print(f'[App] Loading UI from {url.toString()}')
        self.browser.load(url)
    
    def show_error(self, message):
        """Show an error message in the browser."""
        html = f'''<html><body style="background:#0a1d29; color:#ff6b6b; font-family:Segoe UI; padding:20px;">
        <h2>Error</h2>
        <p>{message}</p>
        </body></html>'''
        self.browser.setHtml(html)
    
    def closeEvent(self, event):
        """Handle application close."""
        print('[App] Shutting down...')
        if self.server_process:
            try:
                print('[App] Terminating server process...')
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print('[App] Server terminated')
            except Exception as e:
                print(f'[App] Error terminating server: {e}')
                try:
                    self.server_process.kill()
                except:
                    pass
        event.accept()

def main():
    # Request admin privileges if not already elevated
    request_admin()
    
    app = QApplication(sys.argv)
    
    # Set app-level icon for taskbar
    icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    launcher = LauncherApp()
    launcher.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
