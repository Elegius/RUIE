import sys
import os
import subprocess
import time
import socket
import ctypes
import threading
import logging
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtCore import QUrl, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QFont
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


class DebugEmitter(QObject):
    """Signal emitter for debug messages."""
    debug_signal = pyqtSignal(str)


class DebugWindow(QMainWindow):
    """Separate window for displaying debug information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'{APP_NAME} v{APP_VERSION} - Debug Console')
        self.setGeometry(1400, 100, 600, 700)
        self.setMinimumSize(400, 300)
        
        # Create text area
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet('''
            QTextEdit {
                background-color: #0a0e27;
                color: #00d4ff;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
                border: 1px solid #00d4ff;
                padding: 5px;
            }
        ''')
        font = QFont('Courier New', 9)
        font.setFixedPitch(True)
        self.text_area.setFont(font)
        
        layout.addWidget(self.text_area)
        
        # Add clear button
        clear_btn = QPushButton('Clear')
        clear_btn.setStyleSheet('''
            QPushButton {
                background-color: #1a3a4a;
                color: #00d4ff;
                border: 1px solid #00d4ff;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2a4a5a;
            }
        ''')
        clear_btn.clicked.connect(self.text_area.clear)
        
        layout.addWidget(clear_btn)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Create emitter for thread-safe signals
        self.emitter = DebugEmitter()
        self.emitter.debug_signal.connect(self.add_debug_message)
        
        # Set dark theme
        self.setStyleSheet('''
            QMainWindow {
                background-color: #0a0e27;
            }
        ''')
        
        logger.info('Debug window created')
    
    def add_debug_message(self, message: str):
        """Add a debug message to the display."""
        self.text_area.append(message)
        # Auto-scroll to bottom
        self.text_area.verticalScrollBar().setValue(
            self.text_area.verticalScrollBar().maximum()
        )
    
    def closeEvent(self, event):
        """Allow closing debug window without closing main app."""
        logger.info('Debug window closed')
        event.accept()


class LauncherApp(QMainWindow):
    def __init__(self, port=5000):
        super().__init__()
        self.port = port
        self.server_process = None
        self.server_thread = None
        
        # Create debug window
        self.debug_window = DebugWindow(self)
        self.debug_window.show()
        
        self.add_debug_message('[LAUNCHER] RUIE initialized')
        
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
        
        # CRITICAL: Enable JavaScript in the WebEngine
        try:
            # Try to access settings and enable JavaScript
            page = self.browser.page()
            settings = page.settings()
            # Try different attribute names depending on PyQt5 version
            try:
                from PyQt5.QtWebEngineCore import QWebEngineSettings
                settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
                logger.info("JavaScript enabled via QWebEngineSettings")
            except ImportError:
                # Fallback for older PyQt5 versions
                settings.setAttribute(32, True)  # 32 is JavascriptEnabled attribute code
                logger.info("JavaScript enabled via attribute code")
        except Exception as e:
            logger.warning(f"Could not explicitly enable JavaScript: {e}")
            logger.info("JavaScript should be enabled by default")
        
        # Show enhanced loading screen with progress
        self.show_loading_screen()
        
        # Start server
        self.start_server()
        
        # Load UI after server is ready
        self.check_and_load_ui()
    
    def add_debug_message(self, message: str):
        """Add a message to the debug window."""
        try:
            if hasattr(self, 'debug_window') and self.debug_window:
                self.debug_window.emitter.debug_signal.emit(message)
        except Exception as e:
            logger.error(f'Error sending debug message: {e}')
    
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
        
        # CRITICAL: Show the window so it's visible to the user
        self.show()
        self.activateWindow()
        logger.info("Window shown and activated")
    
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
        
        # Ensure window is visible before loading
        self.show()
        self.activateWindow()
        self.raise_()
        
        self.browser.load(url)
        logger.info('Browser load command sent, window should be visible')
        
        # Inject startApp() call after page loads
        def inject_initialization():
            logger.info('[PYTHON] Injecting initialization code')
            
            # First, fetch the launcher info from the API
            try:
                import urllib.request
                import json
                response = urllib.request.urlopen('http://127.0.0.1:5000/api/detect-launcher')
                data = json.loads(response.read().decode())
                asar_path = ''
                if data.get('success') and data.get('launcher'):
                    asar_path = data['launcher'].get('asarPath', '')
                    logger.info(f'[PYTHON] Got asarPath: {asar_path}')
                else:
                    logger.warning('[PYTHON] Failed to get launcher info')
                
                # Now inject JavaScript to fill the field and setup button handlers
                js_code = f'''
                (function() {{
                    console.log('[INJECTED] Starting initialization');
                    
                    // Set asarPath field
                    var asarField = document.getElementById('asarPath');
                    if (asarField) {{
                        asarField.value = {repr(asar_path)};
                        console.log('[INJECTED] Set asarPath to:', asarField.value);
                    }}
                    
                    // Show success indicator
                    var indicator = document.getElementById('path-success-indicator');
                    if (indicator) {{
                        indicator.style.display = 'block';
                    }}
                    
                    // Update status
                    var status = document.getElementById('init-status');
                    if (status) {{
                        status.innerHTML = '✓ Launcher detected';
                        status.className = 'status show success';
                    }}
                    
                    // Replace all button onclick handlers
                    var buttons = document.querySelectorAll('button');
                    console.log('[INJECTED] Found ' + buttons.length + ' buttons');
                    
                    // Button handler mappings - call API endpoints for all operations
                    var handlerMappings = {{
                        'extractAsar': function() {{
                            console.log('[HANDLER] extractAsar called');
                            var extractStatus = document.getElementById('extract-status');
                            var extractBtn = document.getElementById('extract-btn');
                            if (extractStatus) {{
                                extractStatus.innerHTML = '⏳ Creating backup and decompiling (this may take a moment due to Windows Defender scanning)...';
                                extractStatus.className = 'status show info';
                            }}
                            if (extractBtn) extractBtn.disabled = true;
                            var progressDiv = document.getElementById('extract-progress');
                            if (progressDiv) progressDiv.style.display = 'block';
                            
                            fetch('/api/extract', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify({{asarPath: asarField.value}})
                            }})
                                .then(r => r.json())
                                .then(data => {{
                                    console.log('[HANDLER] Extract response:', data);
                                    if (data.success) {{
                                        if (extractStatus) {{
                                            extractStatus.innerHTML = '✓ Decompilation complete! Backup created. Ready to customize.';
                                            extractStatus.className = 'status show success';
                                        }}
                                        // Reload the extracts list
                                        if (typeof window.loadExtracts === 'function') {{
                                            window.loadExtracts();
                                        }}
                                    }} else {{
                                        if (extractStatus) {{
                                            var errorMsg = data.error || 'Unknown error';
                                            if (data.details) {{
                                                errorMsg += ' (' + data.details + ')';
                                            }}
                                            extractStatus.innerHTML = '✗ Error: ' + errorMsg;
                                            extractStatus.className = 'status show error';
                                        }}
                                    }}
                                    if (progressDiv) progressDiv.style.display = 'none';
                                    if (extractBtn) extractBtn.disabled = false;
                                }})
                                .catch(e => {{
                                    console.error('[HANDLER] Extract error:', e);
                                    if (extractStatus) {{
                                        extractStatus.innerHTML = '✗ Error: ' + e.message;
                                        extractStatus.className = 'status show error';
                                    }}
                                    if (progressDiv) progressDiv.style.display = 'none';
                                }});
                        }},
                        'browseForAsar': function() {{
                            console.log('[HANDLER] browseForAsar called');
                            fetch('/api/browse-for-asar', {{method: 'POST', headers: {{'Content-Type': 'application/json'}}}})
                                .then(r => r.json())
                                .then(data => {{
                                    if (data.success && data.path) {{
                                        asarField.value = data.path;
                                        console.log('[HANDLER] Selected path:', data.path);
                                    }}
                                }})
                                .catch(e => console.error('[HANDLER] Browse error:', e));
                        }},
                        'detectLauncher': function() {{
                            console.log('[HANDLER] detectLauncher called');
                            if (status) {{
                                status.innerHTML = '✓ Already detected';
                            }}
                        }},
                        'initSession': function() {{
                            console.log('[HANDLER] initSession called');
                            if (!asarField.value) {{
                                alert('Please select or auto-detect the app.asar path first');
                                return;
                            }}
                            if (status) {{
                                status.innerHTML = 'Initializing session...';
                                status.className = 'status show info';
                            }}
                            fetch('/api/init', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify({{asarPath: asarField.value}})
                            }})
                                .then(r => r.json())
                                .then(data => {{
                                    console.log('[HANDLER] Init response:', data);
                                    if (data.success) {{
                                        if (status) {{
                                            status.innerHTML = '✓ Session initialized - ready to decompile!';
                                            status.className = 'status show success';
                                        }}
                                        // Load extracted folders and backups
                                        if (typeof window.loadExtracts === 'function') {{
                                            console.log('[HANDLER] Calling loadExtracts()');
                                            window.loadExtracts().catch(e => console.error('[HANDLER] loadExtracts error:', e));
                                        }} else {{
                                            console.warn('[HANDLER] loadExtracts function not found');
                                        }}
                                    }} else {{
                                        if (status) {{
                                            status.innerHTML = '✗ Error: ' + (data.error || 'Unknown error');
                                            status.className = 'status show error';
                                        }}
                                    }}
                                }})
                                .catch(e => {{
                                    console.error('[HANDLER] Init error:', e);
                                    if (status) {{
                                        status.innerHTML = '✗ Error: ' + e.message;
                                        status.className = 'status show error';
                                    }}
                                }});
                        }},
                        'applyColors': function() {{
                            console.log('[HANDLER] applyColors called');
                            fetch('/api/apply-colors', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify({{}})
                            }})
                                .then(r => r.json())
                                .then(data => {{
                                    console.log('[HANDLER] Apply colors response:', data);
                                    var colorStatus = document.getElementById('apply-status');
                                    if (colorStatus) {{
                                        if (data.success) {{
                                            colorStatus.innerHTML = '✓ Colors applied successfully';
                                            colorStatus.className = 'status show success';
                                        }} else {{
                                            colorStatus.innerHTML = '✗ Error: ' + (data.error || 'Unknown error');
                                            colorStatus.className = 'status show error';
                                        }}
                                    }}
                                }})
                                .catch(e => {{
                                    console.error('[HANDLER] Apply colors error:', e);
                                    var colorStatus = document.getElementById('apply-status');
                                    if (colorStatus) {{
                                        colorStatus.innerHTML = '✗ Error: ' + e.message;
                                        colorStatus.className = 'status show error';
                                    }}
                                }});
                        }},
                        'applyMedia': function() {{
                            console.log('[HANDLER] applyMedia called');
                            fetch('/api/apply-media', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify({{}})
                            }})
                                .then(r => r.json())
                                .then(data => {{
                                    console.log('[HANDLER] Apply media response:', data);
                                    var mediaStatus = document.getElementById('media-status');
                                    if (mediaStatus) {{
                                        if (data.success) {{
                                            mediaStatus.innerHTML = '✓ Media applied successfully';
                                            mediaStatus.className = 'status show success';
                                        }} else {{
                                            mediaStatus.innerHTML = '✗ Error: ' + (data.error || 'Unknown error');
                                            mediaStatus.className = 'status show error';
                                        }}
                                    }}
                                }})
                                .catch(e => {{
                                    console.error('[HANDLER] Apply media error:', e);
                                    var mediaStatus = document.getElementById('media-status');
                                    if (mediaStatus) {{
                                        mediaStatus.innerHTML = '✗ Error: ' + e.message;
                                        mediaStatus.className = 'status show error';
                                    }}
                                }});
                        }},
                        'navigateToPage': function(pageNum) {{
                            return function() {{
                                console.log('[HANDLER] navigateToPage called with page:', pageNum);
                                var pages = document.querySelectorAll('[data-page]');
                                pages.forEach(p => p.style.display = 'none');
                                var targetPage = document.querySelector('[data-page="' + pageNum + '"]');
                                if (targetPage) targetPage.style.display = 'block';
                            }};
                        }},
                        'addColorMapping': function() {{
                            console.log('[HANDLER] addColorMapping called');
                            // This would need to add a new color mapping row dynamically
                            // For now, we can show a placeholder
                            alert('Add Color Mapping - will implement dynamic form addition');
                        }},
                        'importThemeFromColors': function() {{
                            console.log('[HANDLER] importThemeFromColors called');
                            // Would open file dialog in the future
                            alert('Import Theme - will implement file selection');
                        }},
                        'exportCurrentPreset': function() {{
                            console.log('[HANDLER] exportCurrentPreset called');
                            fetch('/api/config/export', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify({{}})
                            }})
                                .then(r => r.json())
                                .then(data => {{
                                    if (data.success) {{
                                        alert('✓ Preset exported to ' + data.path);
                                    }} else {{
                                        alert('✗ Export failed: ' + (data.error || 'Unknown error'));
                                    }}
                                }})
                                .catch(e => alert('✗ Export error: ' + e.message));
                        }},
                        'saveCurrentPreset': function() {{
                            console.log('[HANDLER] saveCurrentPreset called');
                            var presetName = prompt('Enter preset name:');
                            if (presetName) {{
                                fetch('/api/save-preset', {{
                                    method: 'POST',
                                    headers: {{'Content-Type': 'application/json'}},
                                    body: JSON.stringify({{name: presetName}})
                                }})
                                    .then(r => r.json())
                                    .then(data => {{
                                        if (data.success) {{
                                            alert('✓ Preset saved');
                                        }} else {{
                                            alert('✗ Save failed: ' + (data.error || 'Unknown error'));
                                        }}
                                    }})
                                    .catch(e => alert('✗ Save error: ' + e.message));
                            }}
                        }},
                        'useSelectedExtract': function() {{
                            console.log('[HANDLER] useSelectedExtract called');
                            var selected = document.querySelector('.extract-item.selected');
                            if (selected) {{
                                var extractPath = selected.getAttribute('data-path');
                                fetch('/api/use-extract', {{
                                    method: 'POST',
                                    headers: {{'Content-Type': 'application/json'}},
                                    body: JSON.stringify({{path: extractPath}})
                                }})
                                    .then(r => r.json())
                                    .then(data => {{
                                        if (data.success) {{
                                            alert('✓ Using extraction: ' + extractPath);
                                        }} else {{
                                            alert('✗ Error: ' + (data.error || 'Unknown error'));
                                        }}
                                    }})
                                    .catch(e => alert('✗ Error: ' + e.message));
                            }} else {{
                                alert('Please select an extraction first');
                            }}
                        }},
                        'openLatestExtract': function() {{
                            console.log('[HANDLER] openLatestExtract called');
                            fetch('/api/open-latest-extract', {{method: 'POST', headers: {{'Content-Type': 'application/json'}}}})
                                .then(r => r.json())
                                .then(data => {{
                                    if (data.success) {{
                                        alert('✓ Opening latest extraction');
                                    }} else {{
                                        alert('✗ Error: ' + (data.error || 'No extractions found'));
                                    }}
                                }})
                                .catch(e => alert('✗ Error: ' + e.message));
                        }},
                        'createNewBackup': function() {{
                            console.log('[HANDLER] createNewBackup called');
                            var backupName = prompt('Enter backup name:');
                            if (backupName) {{
                                fetch('/api/backups', {{
                                    method: 'POST',
                                    headers: {{'Content-Type': 'application/json'}},
                                    body: JSON.stringify({{name: backupName}})
                                }})
                                    .then(r => r.json())
                                    .then(data => {{
                                        if (data.success) {{
                                            alert('✓ Backup created');
                                        }} else {{
                                            alert('✗ Backup failed: ' + (data.error || 'Unknown error'));
                                        }}
                                    }})
                                    .catch(e => alert('✗ Backup error: ' + e.message));
                            }}
                        }},
                        'addMusicFile': function() {{
                            console.log('[HANDLER] addMusicFile called');
                            alert('Add Music File - will implement file selection dialog');
                        }},
                        'loadDefaultMusic': function() {{
                            console.log('[HANDLER] loadDefaultMusic called');
                            fetch('/api/clear-music', {{method: 'POST', headers: {{'Content-Type': 'application/json'}}}})
                                .then(r => r.json())
                                .then(data => {{
                                    if (data.success) {{
                                        alert('✓ Music reset to default');
                                    }} else {{
                                        alert('✗ Error: ' + (data.error || 'Unknown error'));
                                    }}
                                }})
                                .catch(e => alert('✗ Error: ' + e.message));
                        }}
                    }};
                    
                    // Attach handlers to all buttons
                    for (var i = 0; i < buttons.length; i++) {{
                        var btn = buttons[i];
                        var onclickAttr = btn.getAttribute('onclick');
                        
                        if (onclickAttr) {{
                            // Extract function name and parameters from onclick
                            var match = onclickAttr.match(/^\\s*(\\w+)\\s*(\\((.*?)\\))?\\s*$/);
                            if (match) {{
                                var funcName = match[1];
                                var params = match[3] ? match[3].split(',').map(s => s.trim()) : [];
                                
                                if (handlerMappings[funcName]) {{
                                    console.log('[INJECTED] Attaching handler for', funcName);
                                    
                                    // Remove the original onclick
                                    btn.removeAttribute('onclick');
                                    
                                    // Create and attach new click handler
                                    if (params.length > 0) {{
                                        // Functions with parameters like navigateToPage(2)
                                        var pageNum = parseInt(params[0]);
                                        btn.addEventListener('click', handlerMappings[funcName](pageNum));
                                    }} else {{
                                        // Functions without parameters
                                        btn.addEventListener('click', handlerMappings[funcName]);
                                    }}
                                }}
                            }}
                        }}
                    }}
                    
                    console.log('[INJECTED] All button handlers attached');
                }})();
                '''
                logger.info('[PYTHON] Injecting field population and button handlers')
                self.browser.page().runJavaScript(js_code)
                
            except Exception as e:
                logger.error(f'[PYTHON] Error during initialization: {e}')
        
        # Schedule injection after page has time to load
        QTimer.singleShot(4000, inject_initialization)
    
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
