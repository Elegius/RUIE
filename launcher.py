import sys
import os
import subprocess
import time
import socket
import ctypes
import threading
import logging
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtGui import QIcon

# Version info
APP_VERSION = "0.2 Alpha"
APP_NAME = "RUIE"
# Development Note: This application was developed with AI assistance using GitHub Copilot (Claude Haiku 4.5)

# SECURITY: Determine if running in production (frozen exe)
PRODUCTION_BUILD = getattr(sys, 'frozen', False)

# Set up logging - INFO level in production, DEBUG in development
log_file = os.path.join(os.path.expanduser('~'), 'Documents', 'RUIE-debug.log')
log_level = logging.INFO if PRODUCTION_BUILD else logging.DEBUG
logging.basicConfig(
    level=log_level,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Copyright and Disclaimer
COPYRIGHT_TEXT = """
RUIE is an independent fan-made project and is not affiliated with Cloud Imperium Games (CIG) or Star Citizen.
Star Citizen and the RSI Launcher are registered trademarks of Cloud Imperium Games.

This tool is provided for personal customization use only and comes with no warranty.
"""

def is_frozen():
    """Check if running as compiled executable."""
    return getattr(sys, 'frozen', False)

def is_admin():
    """Check if running with admin privileges."""
    try:
        # Try using kernel32 instead of shell
        return ctypes.windll.kernel32.GetFileAttributesW('C:\\Program Files') != -1
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

def request_admin():
    """Request admin privileges if not already elevated.
    
    SECURITY NOTE: Admin privileges are required to:
    - Modify files in Program Files directory
    - Access protected system directories
    - Install themes to Star Citizen launcher
    
    Windows will display a User Account Control (UAC) prompt.
    """
    is_admin_now = is_admin()
    if not is_admin_now:
        logger.info("Requesting administrator privileges...")
        logger.info("Reason: Need access to modify Star Citizen launcher files in Program Files")
        try:
            # Re-run this script with admin privileges using ShellExecute
            script = sys.argv[0]
            ctypes.windll.shell.ShellExecuteW(
                None, 
                "runas", 
                script, 
                "", 
                None, 
                1  # SW_SHOW - display the window
            )
            sys.exit(0)
        except Exception as e:
            logger.warning(f"Could not request elevation: {e}")
            logger.warning("Running without admin privileges - some features may not work")
            # Show error in UI
            from PyQt5.QtWidgets import QMessageBox
            msg = ("Administrator Privileges Required\n\n"
                   "RUIE needs admin access to modify Star Citizen launcher files.\n\n"
                   "Please run RUIE as Administrator.")
            logger.error(msg)
    else:
        logger.info("✓ Running with admin privileges ✓")

class LauncherApp(QMainWindow):
    def __init__(self, port=5000):
        super().__init__()
        self.port = port
        self.server_process = None
        self.server_thread = None
        
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
        """Start the production Flask server as a subprocess or thread."""
        try:
            project_root = str(Path(__file__).parent)
            
            logger.info('Starting production server (Waitress WSGI)...')
            
            if is_frozen():
                # Running as compiled EXE - start Flask in a thread with Waitress
                logger.info('Running in frozen mode (production) - starting server as thread')
                
                def run_flask():
                    try:
                        # Change to the correct directory for frozen app
                        if hasattr(sys, '_MEIPASS'):
                            os.chdir(sys._MEIPASS)
                            logger.info(f'Working directory set to: {sys._MEIPASS}')
                        
                        # Import and run server with production WSGI
                        import server
                        from waitress import serve
                        logger.info('Server module imported successfully - using Waitress WSGI')
                        logger.info(f'Production server starting on port {self.port}')
                        serve(server.app, host='127.0.0.1', port=self.port, threads=4)
                    except Exception as e:
                        logger.error(f'Server error: {e}', exc_info=True)
                
                self.server_thread = threading.Thread(target=run_flask, daemon=True)
                self.server_thread.start()
                logger.info('Server thread started')
                
            else:
                # Running from source - start Flask as subprocess with Waitress
                logger.info('Running from source - starting production server as subprocess (Waitress WSGI)')
                
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
                logger.info(f'Server process started with PID: {self.server_process.pid}')
                
                # Start threads to read server output
                def read_output():
                    try:
                        while True:
                            line = self.server_process.stdout.readline()
                            if not line:
                                break
                            logger.info(f'[Server] {line.rstrip()}')
                    except:
                        pass
                
                def read_errors():
                    try:
                        while True:
                            line = self.server_process.stderr.readline()
                            if not line:
                                break
                            logger.error(f'[Server Error] {line.rstrip()}')
                    except:
                        pass
                
                output_thread = threading.Thread(target=read_output, daemon=True)
                error_thread = threading.Thread(target=read_errors, daemon=True)
                output_thread.start()
                error_thread.start()
            
        except Exception as e:
            logger.error(f'Failed to start server: {e}', exc_info=True)
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
            logger.info(f'Server is ready on port {self.port}')
            self.load_ui()
        else:
            logger.debug('Waiting for server to be ready...')
            QTimer.singleShot(1000, self.check_and_load_ui)
    
    def load_ui(self):
        """Load the web UI."""
        url = QUrl(f'http://127.0.0.1:{self.port}')
        logger.info(f'Loading UI from {url.toString()}')
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
        logger.info('Shutting down...')
        if self.server_process:
            try:
                logger.info('Terminating server process...')
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                logger.info('Server terminated')
            except Exception as e:
                logger.error(f'Error terminating server: {e}')
                try:
                    self.server_process.kill()
                except:
                    pass
        event.accept()

def main():
    # Request admin privileges if not already elevated
    request_admin()
    
    logger.info(f'Starting {APP_NAME} v{APP_VERSION}')
    logger.info(f'Log file: {log_file}')
    
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
