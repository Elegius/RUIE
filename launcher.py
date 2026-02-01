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
import waitress  # Required for production WSGI server - must be at module level for PyInstaller

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
    
    NOTE: In frozen (compiled) mode, the UAC prompt happens at startup,
    so this function will detect admin status and skip re-execution.
    """
    is_admin_now = is_admin()
    if not is_admin_now:
        logger.info("Requesting administrator privileges...")
        logger.info("Reason: Need access to modify Star Citizen launcher files in Program Files")
        
        # In frozen/compiled mode, we can't reliably re-execute, so just warn the user
        if is_frozen():
            logger.warning("Running without admin privileges - some features may not work")
            logger.warning("Note: Right-click the exe and choose 'Run as administrator' for full functionality")
            from PyQt5.QtWidgets import QMessageBox
            msg = ("Administrator Privileges Recommended\n\n"
                   "RUIE works best when run as Administrator to modify Star Citizen launcher files.\n\n"
                   "Tip: Right-click RUIE.exe and select 'Run as administrator'")
            logger.info(msg)
            return  # Don't try to re-execute in frozen mode
        
        try:
            # Re-run this script with admin privileges using ShellExecute (source mode only)
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
        
        # Show enhanced loading screen with progress
        self.show_loading_screen()
        
        # Start server
        self.start_server()
        
        # Load UI after server is ready
        self.check_and_load_ui()
    
    def show_loading_screen(self):
        """Display an enhanced loading screen with progress bar and status messages."""
        loading_html = '''
        <html>
        <head>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    background: linear-gradient(135deg, #0a0e27 0%, #0a1d29 100%);
                    color: #c0c8d0;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    overflow: hidden;
                }
                
                .loading-container {
                    text-align: center;
                    padding: 40px;
                    max-width: 500px;
                }
                
                .loading-logo {
                    font-size: 3em;
                    margin-bottom: 20px;
                    font-weight: bold;
                    color: #00d4ff;
                    text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
                    letter-spacing: 2px;
                }
                
                .loading-title {
                    font-size: 1.8em;
                    margin-bottom: 30px;
                    color: #00d4ff;
                    font-weight: 600;
                    letter-spacing: 1px;
                }
                
                .progress-section {
                    margin-top: 40px;
                }
                
                .progress-bar-container {
                    width: 100%;
                    height: 8px;
                    background: rgba(0, 212, 255, 0.1);
                    border-radius: 4px;
                    overflow: hidden;
                    margin-bottom: 15px;
                    border: 1px solid rgba(0, 212, 255, 0.3);
                }
                
                .progress-bar {
                    height: 100%;
                    background: linear-gradient(90deg, #00d4ff, #00a8cc);
                    border-radius: 4px;
                    width: 0%;
                    transition: width 0.3s ease;
                    box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
                }
                
                .progress-text {
                    font-size: 0.9em;
                    color: #a0b0c0;
                    margin-bottom: 8px;
                    min-height: 20px;
                }
                
                .progress-percentage {
                    font-size: 1.2em;
                    color: #00d4ff;
                    font-weight: bold;
                    margin-top: 10px;
                }
                
                .status-item {
                    font-size: 0.85em;
                    color: #7a8a9a;
                    margin-top: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: flex-start;
                    gap: 10px;
                    padding: 6px 0;
                    min-height: 24px;
                }
                
                .status-item.active {
                    color: #00d4ff;
                    font-weight: 500;
                }
                
                .status-icon {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 16px;
                    height: 16px;
                    flex-shrink: 0;
                }
                
                .status-icon.complete {
                    color: #64c864;
                }
                
                .spinner {
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    border: 2px solid rgba(0, 212, 255, 0.3);
                    border-top-color: #00d4ff;
                    border-radius: 50%;
                    animation: spin 0.8s linear infinite;
                }
                
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
                
                .footer-text {
                    font-size: 0.8em;
                    color: #5a6a7a;
                    margin-top: 30px;
                }
            </style>
        </head>
        <body>
            <div class="loading-container">
                <div class="loading-logo">◇ RUIE ◇</div>
                <div class="loading-title">RSI Launcher UI Editor</div>
                
                <div class="progress-section">
                    <div class="progress-text" id="statusText">Initializing...</div>
                    <div class="progress-bar-container">
                        <div class="progress-bar" id="progressBar"></div>
                    </div>
                    <div class="progress-percentage" id="percentage">0%</div>
                    
                    <div style="margin-top: 25px; text-align: left; padding: 0 10px;">
                        <div class="status-item" id="status1">
                            <span class="status-icon"><span class="spinner" id="spinner1"></span></span>
                            <span>Loading Python dependencies...</span>
                        </div>
                        <div class="status-item" id="status2">
                            <span class="status-icon">○</span>
                            <span>Starting Flask server...</span>
                        </div>
                        <div class="status-item" id="status3">
                            <span class="status-icon">○</span>
                            <span>Initializing user interface...</span>
                        </div>
                    </div>
                </div>
                
                <div class="footer-text">
                    v0.2 Alpha • Do not close this window
                </div>
            </div>
            
            <script>
                let currentProgress = 0;
                let currentStep = 1;
                
                function updateProgress(progress, step, statusText) {
                    currentProgress = Math.min(progress, 99);
                    currentStep = step || currentStep;
                    
                    // Update progress bar
                    document.getElementById('progressBar').style.width = currentProgress + '%';
                    document.getElementById('percentage').textContent = currentProgress + '%';
                    document.getElementById('statusText').textContent = statusText || 'Loading...';
                    
                    // Update status indicators
                    for (let i = 1; i <= 3; i++) {
                        const statusEl = document.getElementById('status' + i);
                        const iconEl = statusEl.querySelector('.status-icon');
                        
                        if (i < currentStep) {
                            // Complete
                            statusEl.classList.remove('active');
                            iconEl.innerHTML = '✓';
                            iconEl.classList.add('complete');
                        } else if (i === currentStep) {
                            // Active
                            statusEl.classList.add('active');
                            iconEl.innerHTML = '<span class="spinner"></span>';
                            iconEl.classList.remove('complete');
                        } else {
                            // Pending
                            statusEl.classList.remove('active');
                            iconEl.innerHTML = '○';
                            iconEl.classList.remove('complete');
                        }
                    }
                }
                
                // Expose function to Python/WebEngine
                window.updateProgress = updateProgress;
                
                // Initial state
                updateProgress(5, 1, 'Loading Python dependencies...');
            </script>
        </body>
        </html>
        '''
        self.browser.setHtml(loading_html)
        logger.info("Enhanced loading screen displayed")
    
    def start_server(self):
        """Start the production Flask server as a subprocess or thread."""
        try:
            project_root = str(Path(__file__).parent)
            
            logger.info('Starting production server (Waitress WSGI)...')
            self.update_loading_progress(15, 1, 'Starting Flask server...')
            
            if is_frozen():
                # Running as compiled EXE - start Flask in a thread with Waitress
                logger.info('Running in frozen mode (production) - starting server as thread')
                self.update_loading_progress(25, 1, 'Importing server modules...')
                
                def run_flask():
                    try:
                        # Change to the correct directory for frozen app
                        if hasattr(sys, '_MEIPASS'):
                            os.chdir(sys._MEIPASS)
                            logger.info(f'Working directory set to: {sys._MEIPASS}')
                        
                        # Add the frozen app path to sys.path to ensure imports work
                        if sys._MEIPASS not in sys.path:
                            sys.path.insert(0, sys._MEIPASS)
                        
                        # Import and run server with production WSGI
                        logger.info('Attempting to import server module...')
                        import server
                        logger.info('Server module imported successfully')
                        
                        logger.info('Attempting to import waitress...')
                        from waitress import serve
                        logger.info('Waitress WSGI server imported successfully')
                        
                        logger.info(f'Production server starting on port {self.port}')
                        self.update_loading_progress(50, 2, 'Initializing Flask application...')
                        
                        # Start the server with timeout configuration
                        logger.info('Starting Waitress server...')
                        serve(server.app, host='127.0.0.1', port=self.port, threads=4, _quiet=False)
                    except ImportError as e:
                        logger.error(f'Import error - missing module: {e}', exc_info=True)
                        logger.error(f'sys.path: {sys.path}')
                        logger.error(f'sys._MEIPASS: {getattr(sys, "_MEIPASS", "NOT SET")}')
                        logger.error('CRITICAL: Server thread failed at import stage')
                    except Exception as e:
                        logger.error(f'Server thread exception: {e}', exc_info=True)
                        logger.error('CRITICAL: Server thread crashed with exception')
                
                self.server_thread = threading.Thread(target=run_flask, daemon=True)
                self.server_thread.start()
                logger.info('Server thread started')
                self.update_loading_progress(45, 2, 'Server starting...')
                
                # Give the thread a moment to start
                time.sleep(0.5)
                
            else:
                # Running from source - start Flask as subprocess with Waitress
                logger.info('Running from source - starting production server as subprocess (Waitress WSGI)')
                self.update_loading_progress(30, 1, 'Starting Flask subprocess...')
                
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
                self.update_loading_progress(45, 2, 'Flask server initializing...')
                
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
    
    
    def update_loading_progress(self, progress, step, status_text):
        """Update the loading screen progress bar and status."""
        try:
            # Use JavaScript to update progress UI
            script = f'''
            if (typeof window.updateProgress === 'function') {{
                window.updateProgress({progress}, {step}, "{status_text}");
            }}
            '''
            self.browser.page().runJavaScript(script)
        except Exception as e:
            logger.debug(f'Could not update progress UI: {e}')
    
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
        """Check if server is ready and load UI with progress feedback."""
        if not hasattr(self, 'check_attempts'):
            self.check_attempts = 0
        
        if self.is_server_ready():
            logger.info(f'Server is ready on port {self.port}')
            self.update_loading_progress(75, 3, 'Loading user interface...')
            time.sleep(0.5)  # Brief pause for visual feedback
            self.load_ui()
        else:
            self.check_attempts += 1
            
            # Update progress based on attempts (0-35 attempts = 0-70% progress)
            progress = min(45 + (self.check_attempts * 0.7), 70)
            elapsed_text = f'({self.check_attempts}s)'
            self.update_loading_progress(progress, 2, f'Waiting for server... {elapsed_text}')
            
            logger.debug(f'Waiting for server to be ready... attempt {self.check_attempts}/35')
            
            # Timeout after 35 seconds with detailed error logging
            if self.check_attempts > 35:
                logger.error(f'Server did not respond within 35 seconds ({self.check_attempts} attempts)')
                logger.error(f'Checking if server process is running...')
                
                # Log server thread status
                if hasattr(self, 'server_thread') and self.server_thread:
                    logger.error(f'Server thread alive: {self.server_thread.is_alive()}')
                
                # Try one more connection attempt with extended timeout
                try:
                    logger.info('Attempting final connection with 5-second timeout...')
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex(('127.0.0.1', self.port))
                    sock.close()
                    if result == 0:
                        logger.info('Connection successful on final attempt!')
                        self.update_loading_progress(75, 3, 'Loading user interface...')
                        time.sleep(0.5)
                        self.load_ui()
                        return
                except Exception as e:
                    logger.error(f'Final connection attempt failed: {e}')
                
                # Show detailed error message
                self.show_error(
                    'Server Startup Timeout<br><br>'
                    'The application server failed to start within 35 seconds.<br><br>'
                    '<b>Solutions:</b><br>'
                    '• Restart the application<br>'
                    '• Check RUIE-debug.log in your Documents folder<br>'
                    '• Close other applications using port 5000<br>'
                    '• Try running as Administrator<br><br>'
                    'If the problem persists, your system may be slow or have resource constraints.'
                )
                return
            
            # Schedule next check
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
