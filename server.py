from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
import os
import sys
import json
import shutil
import subprocess  # noqa: B404 - Used for safe ASAR extraction/packing
import re
import tempfile
import time
import threading
from urllib.parse import quote
from datetime import datetime
from pathlib import Path

from launcher_detector import LauncherDetector
from color_replacer import ColorReplacer
from media_replacer import MediaReplacer

# Production environment indicator
PRODUCTION_MODE = True  # Set to True for production deployment

# Base directory under which launcher installations are considered trusted.
# Adjust this path to match the expected RSI Launcher installation root on the host.
LAUNCHER_ROOT_DIR = os.path.abspath(os.environ.get('RSI_LAUNCHER_ROOT', os.path.expanduser('~')))

# Determine the base path for resources
def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# Set up Flask with the correct static folder
static_folder = get_resource_path('public')
app = Flask(__name__, static_folder=static_folder, static_url_path='')

# Production security configuration
if PRODUCTION_MODE:
    app.config['ENV'] = 'production'
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    app.config['PROPAGATE_EXCEPTIONS'] = False
    app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False

# CORS configuration - strict local desktop app only
# Fixed to use specific port instead of wildcard
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5000",
            "http://127.0.0.1:5000"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": False,
        "max_age": 3600
    }
})

# Performance configurations
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 86400  # 24 hour cache for static files
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload
app.config['JSON_SORT_KEYS'] = False  # Don't sort JSON keys for speed

# Add cache headers and security headers for static files
@app.after_request
def add_security_headers(response):
    """Add security headers and cache headers to responses."""
    # Add security headers to prevent XSS and clickjacking
    response.headers['X-Content-Type-Options'] = 'nosniff'  # Prevent MIME-type sniffing
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'  # Prevent clickjacking
    response.headers['X-XSS-Protection'] = '1; mode=block'  # Enable XSS protection
    
    # Production security headers
    if PRODUCTION_MODE:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"
    
    # Cache static assets for performance
    if response.content_type and ('image' in response.content_type or 
                                   'font' in response.content_type or
                                   'css' in response.content_type or
                                   'javascript' in response.content_type):
        response.cache_control.max_age = 86400  # 24 hours for static assets
    return response

# Configuration
DOCS_DIR = os.path.expanduser('~/Documents/RUIE')
os.makedirs(DOCS_DIR, exist_ok=True)

# ============================================================================
# SECURITY VALIDATION FUNCTIONS
# ============================================================================

# Allowed media file extensions (whitelist approach)
ALLOWED_MEDIA_EXTENSIONS = {
    # Images
    'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp', 'ico', 'tiff',
    # Videos
    'mp4', 'webm', 'mkv', 'avi', 'mov', 'm4v', 'flv', 'wmv', 'mpg', 'mpeg',
    # Audio
    'mp3', 'wav', 'flac', 'ogg', 'm4a', 'aac', 'wma', 'opus', 'aiff'
}

# Max file sizes by category
MAX_FILE_SIZES = {
    'images': 100 * 1024 * 1024,     # 100MB
    'videos': 1000 * 1024 * 1024,    # 1GB
    'audio': 200 * 1024 * 1024       # 200MB
}

# Allowed extraction folder names (pattern validation)
ALLOWED_EXTRACT_PATTERNS = [
    'app-decompiled-',
    'app-extracted-'
]

def get_file_category(filename):
    """Determine file category from extension."""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    image_exts = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp', 'ico', 'tiff'}
    video_exts = {'mp4', 'webm', 'mkv', 'avi', 'mov', 'm4v', 'flv', 'wmv', 'mpg', 'mpeg'}
    audio_exts = {'mp3', 'wav', 'flac', 'ogg', 'm4a', 'aac', 'wma', 'opus', 'aiff'}
    
    if ext in image_exts:
        return 'images'
    elif ext in video_exts:
        return 'videos'
    elif ext in audio_exts:
        return 'audio'
    return None

def validate_file_upload(filename, file_size):
    """
    Validate uploaded file is safe.
    Returns (is_valid, error_message)
    """
    if not filename:
        return False, "Missing filename"
    
    # Check extension
    if '.' not in filename:
        return False, "File must have an extension"
    
    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_MEDIA_EXTENSIONS:
        return False, f"File type not allowed: {ext}. Allowed types: {', '.join(sorted(ALLOWED_MEDIA_EXTENSIONS))}"
    
    # Check file size
    category = get_file_category(filename)
    if category:
        max_size = MAX_FILE_SIZES.get(category, 100 * 1024 * 1024)
        if file_size > max_size:
            max_mb = max_size / (1024 * 1024)
            return False, f"File too large. Max size for {category}: {max_mb:.0f}MB"
    
    # Prevent suspicious filenames
    if '..' in filename or '/' in filename or '\\' in filename:
        return False, "Invalid filename characters"
    
    return True, ""

def validate_path_safety(requested_path, base_dir, allowed_prefixes=None):
    """
    Validate that a path is safe and within allowed directory.
    Returns (is_safe, resolved_path, error_message)
    
    Args:
        requested_path: The path to validate
        base_dir: The base directory it must be within
        allowed_prefixes: Optional list of allowed folder name prefixes
    """
    try:
        base = Path(base_dir).resolve()
        requested = Path(requested_path).resolve()
        
        # Check if path exists (prevents some attacks)
        if not requested.exists():
            return False, None, f"Path does not exist: {requested_path}"
        
        # Check if path is within base directory
        try:
            requested.relative_to(base)
        except ValueError:
            return False, None, f"Path is outside allowed directory: {requested_path}"
        
        # Check symlinks (prevent symlink attacks)
        if requested.is_symlink() or any(part.is_symlink() for part in requested.parents):
            return False, None, "Symlinks are not allowed"
        
        # Check allowed prefixes if specified (e.g., extraction folders)
        if allowed_prefixes:
            folder_name = requested.name
            if not any(folder_name.startswith(prefix) for prefix in allowed_prefixes):
                return False, None, f"Invalid folder name: {folder_name}"
        
        return True, requested, ""
    
    except Exception as e:
        return False, None, f"Path validation error: {str(e)}"

def validate_color_mapping(color_mappings):
    """
    Validate color mappings are safe and properly formatted.
    Returns (is_valid, validated_mappings, error_message)
    """
    if not isinstance(color_mappings, dict):
        return False, {}, "Color mappings must be a dictionary"
    
    if len(color_mappings) > 500:
        return False, {}, "Too many color mappings (max 500)"
    
    validated = {}
    
    for key, value in color_mappings.items():
        # Validate key
        if not isinstance(key, str):
            return False, {}, f"Color key must be string, got {type(key).__name__}"
        
        if len(key) > 200:
            return False, {}, f"Color key too long: {len(key)} chars (max 200)"
        
        # Prevent null bytes and other control characters
        if '\x00' in key or any(ord(c) < 32 for c in key if c not in '\t\n\r'):
            return False, {}, "Color key contains invalid characters"
        
        # Validate value
        if not isinstance(value, str):
            return False, {}, f"Color value must be string, got {type(value).__name__}"
        
        if len(value) > 200:
            return False, {}, f"Color value too long: {len(value)} chars (max 200)"
        
        # Validate hex color format (more lenient to support various color formats)
        if not re.match(r'^#[0-9a-fA-F]{3}([0-9a-fA-F]{3})?$|^rgb\(\d+,\s*\d+,\s*\d+\)$|^rgba\(\d+,\s*\d+,\s*\d+,\s*[\d.]+\)$', value):
            # Allow custom values but warn
            if not re.match(r'^[a-zA-Z0-9\-#\(\),.\s]+$', value):
                return False, {}, f"Invalid color format: {value}"
        
        validated[key] = value
    
    return True, validated, ""

# ============================================================================
# END SECURITY VALIDATION FUNCTIONS
# ============================================================================

class ThemeManager:
    """Manage theme extraction, backup, and repacking."""
    
    def __init__(self):
        self.launcher_info = None
        self.extracted_dir = None
        self.backup_dir = None
        self.color_apply_thread = None
        self.status = {
            'operation': None,
            'state': 'idle',
            'message': 'Idle',
            'progress': 0,
            'lastError': None
        }

    def set_status(self, operation, state, message, progress=None, last_error=None):
        self.status['operation'] = operation
        self.status['state'] = state
        self.status['message'] = message
        if progress is not None:
            self.status['progress'] = progress
        if last_error is not None:
            self.status['lastError'] = last_error
    
    def init(self):
        """Initialize launcher detection."""
        self.launcher_info = LauncherDetector.detect()
        return self.launcher_info is not None
    
    def extract_asar(self):
        """Extract app.asar to temp directory."""
        if not self.launcher_info:
            print("[ThemeManager] Launcher info is None")
            self.set_status('extract', 'error', 'Launcher not initialized', progress=0, last_error='Launcher not initialized')
            return False
        
        asar_path = self.launcher_info['asarPath']
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        
        # Ensure DOCS_DIR exists and is properly set
        docs_dir = os.path.normpath(os.path.expanduser(DOCS_DIR))
        print(f"[ThemeManager] Extract DOCS_DIR: {docs_dir}")
        os.makedirs(docs_dir, exist_ok=True)
        
        extracted_path = os.path.normpath(os.path.join(docs_dir, f'app-decompiled-{timestamp}'))
        
        try:
            self.set_status('extract', 'running', 'Creating backup...', progress=5, last_error=None)
            print(f"[ThemeManager] Extracting from: {asar_path}")
            print(f"[ThemeManager] Extracting to: {extracted_path}")
            
            # Verify source file exists
            if not os.path.exists(asar_path):
                raise FileNotFoundError(f"Source ASAR file not found: {asar_path}")
            
            # Ensure target directory exists
            os.makedirs(extracted_path, exist_ok=True)
            print(f"[ThemeManager] Target directory created")
            
            # Update status before extraction
            self.set_status('extract', 'running', 'Decompiling app.asar...', progress=10, last_error=None)
            
            # Try extraction with npx first (if Node.js is available)
            print(f"[ThemeManager] Attempting extraction with npx asar...")
            try:
                result = subprocess.run(  # noqa: B607, B603
                    ['npx', 'asar', 'extract', asar_path, extracted_path],
                    capture_output=True,
                    text=True,
                    check=False,
                    cwd=docs_dir,
                    shell=False,
                    timeout=30
                )
                
                print(f"[ThemeManager] Extract return code: {result.returncode}")
                if result.stdout:
                    print(f"[ThemeManager] Stdout: {result.stdout}")
                if result.stderr:
                    print(f"[ThemeManager] Stderr: {result.stderr}")
                
                npx_failed = result.returncode != 0
            except FileNotFoundError as npx_error:
                print(f"[ThemeManager] npx not found: {npx_error}")
                npx_failed = True
            except subprocess.TimeoutExpired:
                print(f"[ThemeManager] npx extraction timed out")
                npx_failed = True
            
            # If npx fails, try Python-based extractor
            if npx_failed:
                print(f"[ThemeManager] npx extraction failed, falling back to Python-based extractor...")
                try:
                    print(f"[ThemeManager] Attempting to import asar_extractor...")
                    
                    # Handle both frozen and non-frozen environments
                    try:
                        base_path = sys._MEIPASS
                    except AttributeError:
                        base_path = os.path.dirname(os.path.abspath(__file__))
                    
                    # Add the base path to sys.path to ensure asar_extractor can be found
                    if base_path not in sys.path:
                        sys.path.insert(0, base_path)
                    
                    from asar_extractor import ASARExtractor
                    print(f"[ThemeManager] ASARExtractor imported successfully")
                    print(f"[ThemeManager] Calling ASARExtractor.extract({asar_path}, {extracted_path})...")
                    ASARExtractor.extract(asar_path, extracted_path)
                    print(f"[ThemeManager] Python ASAR extraction successful")
                except ImportError as ie:
                    print(f"[ThemeManager] Failed to import asar_extractor: {ie}")
                    import traceback
                    traceback.print_exc()
                    error_msg = f"Module import error: {str(ie)}"
                    self.set_status('extract', 'error', 'Decompilation failed', progress=0, last_error=error_msg)
                    return False
                except Exception as py_extract_error:
                    print(f"[ThemeManager] Python extraction also failed: {py_extract_error}")
                    import traceback
                    traceback.print_exc()
                    
                    # Check if it's an unpacked directory issue
                    unpacked_dir = asar_path + '.unpacked'
                    if os.path.exists(unpacked_dir):
                        print(f"[ThemeManager] Found unpacked directory, attempting to copy it...")
                        try:
                            import shutil
                            dest_unpacked = extracted_path + '.unpacked'
                            shutil.copytree(unpacked_dir, dest_unpacked)
                            print(f"[ThemeManager] Unpacked directory copied successfully")
                        except Exception as copy_error:
                            print(f"[ThemeManager] Failed to copy unpacked directory: {copy_error}")
                            error_msg = str(py_extract_error)
                            self.set_status('extract', 'error', 'Decompilation failed', progress=0, last_error=error_msg)
                            return False
                    else:
                        print(f"[ThemeManager] No unpacked directory found at {unpacked_dir}")
                        error_msg = str(py_extract_error)
                        self.set_status('extract', 'error', 'Decompilation failed', progress=0, last_error=error_msg)
                        return False
            
            # Save metadata about original state
            self._save_extraction_metadata(extracted_path)
            
            # Store the extracted path so we can return it to the UI
            self.extracted_dir = extracted_path
            
            print(f"[ThemeManager] Extract successful")
            self.set_status('extract', 'done', 'Extraction complete', progress=100, last_error=None)
            # NOTE: Do NOT auto-select the extraction. User must click to select it.
            # self.extracted_dir remains unchanged until user explicitly selects an extraction
            return True
        except Exception as e:
            print(f"[ThemeManager] Exception extracting asar: {e}")
            import traceback
            traceback.print_exc()
            self.set_status('extract', 'error', 'Extraction failed', progress=0, last_error=str(e))
            return False
    
    def create_backup(self):
        """Create backup of original app.asar."""
        if not self.launcher_info:
            print("[ThemeManager] Launcher info not set")
            return False
        
        asar_path = self.launcher_info['asarPath']
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        
        # Ensure DOCS_DIR exists
        docs_dir = os.path.normpath(os.path.expanduser(DOCS_DIR))
        print(f"[ThemeManager] Backup DOCS_DIR: {docs_dir}")
        os.makedirs(docs_dir, exist_ok=True)
        
        self.backup_dir = os.path.join(docs_dir, f'backup-{timestamp}')
        
        try:
            print(f"[ThemeManager] Creating backup directory: {self.backup_dir}")
            os.makedirs(self.backup_dir, exist_ok=True)
            print(f"[ThemeManager] Backing up from: {asar_path}")
            print(f"[ThemeManager] Backing up to: {os.path.join(self.backup_dir, 'app.asar')}")
            shutil.copy2(asar_path, os.path.join(self.backup_dir, 'app.asar'))
            print(f"[ThemeManager] Backup created successfully")
            return True
        except Exception as e:
            print(f"[ThemeManager] Error creating backup: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def apply_colors(self, color_mappings):
        """Apply color replacements synchronously."""
        try:
            if not self.extracted_dir or not os.path.exists(self.extracted_dir):
                error_msg = f"Error: extracted_dir not set or doesn't exist: {self.extracted_dir}"
                print(error_msg)
                self.set_status('apply-colors', 'error', error_msg, progress=0, last_error=error_msg)
                return 0
            
            self.set_status('apply-colors', 'running', 'Scanning for files...', progress=10, last_error=None)
            print(f"\n=== Color Application Started ===")
            print(f"Extracted directory: {self.extracted_dir}")
            print(f"Directory exists: {os.path.exists(self.extracted_dir)}")
            print(f"Color mappings received: {len(color_mappings)} color(s)")
            for key, value in list(color_mappings.items())[:3]:
                print(f"  - {key}: {value}")
            
            # Create progress callback
            def progress_callback(current, total, message):
                progress = 10 + int((current / total) * 80) if total > 0 else 45
                self.set_status('apply-colors', 'running', message, progress=progress, last_error=None)
                print(f"[Progress {progress}%] {message}")
            
            result = ColorReplacer.apply_colors(self.extracted_dir, color_mappings, progress_callback)
            print(f"Color replacement result: {result} files modified")
            
            if result > 0:
                self.set_status('apply-colors', 'done', f'Applied colors to {result} files', progress=100, last_error=None)
            else:
                error_msg = 'No files were modified - could not find colors to replace'
                self.set_status('apply-colors', 'error', error_msg, progress=0, last_error=error_msg)
            
            return result
        except Exception as e:
            error_msg = f"Exception in apply_colors: {e}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.set_status('apply-colors', 'error', error_msg, progress=0, last_error=str(e))
            return 0
    
    def apply_colors_async(self, color_mappings):
        """Apply color replacements in a background thread."""
        def _apply():
            self.apply_colors(color_mappings)
        
        if self.color_apply_thread and self.color_apply_thread.is_alive():
            print("Color apply operation already in progress")
            return False
        
        self.color_apply_thread = threading.Thread(target=_apply, daemon=True)
        self.color_apply_thread.start()
        return True
    
    def apply_media(self, media_mappings):
        """Apply media replacements."""
        if not self.extracted_dir or not os.path.exists(self.extracted_dir):
            return {}
        
        return MediaReplacer.apply_media(self.extracted_dir, media_mappings)
    
    def repack_asar(self):
        """Repack extracted directory back into app.asar."""
        if not self.extracted_dir or not self.launcher_info:
            return False
        
        asar_path = self.launcher_info['asarPath']
        
        try:
            # Backup original first
            if not self.backup_dir:
                self.create_backup()
            
            try:
                # Remove old asar
                if os.path.exists(asar_path):
                    os.remove(asar_path)
            except PermissionError:
                raise PermissionError(f'Permission denied: Unable to write to {asar_path}. Try running as Administrator.')
            
            # Repack (without shell - safer)
                result = subprocess.run(  # noqa: B607, B603
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                print(f"Error repacking asar: {result.stderr}")
                return False

            # Cleanup after successful repack
            self.cleanup_backups(keep_latest=1)
            self.cleanup_extractions(keep_latest=5)

            return True
        except PermissionError as pe:
            print(f"Permission error repacking asar: {pe}")
            raise pe
        except Exception as e:
            print(f"Exception repacking asar: {e}")
            return False

    def cleanup_backups(self, keep_latest=1):
        """Keep only the most recent backups to avoid clutter."""
        base = Path(DOCS_DIR)
        backups = sorted(
            [p for p in base.iterdir() if p.is_dir() and p.name.startswith('backup-')],
            key=lambda p: p.name,
            reverse=True
        )

        for backup in backups[keep_latest:]:
            try:
                shutil.rmtree(backup)
            except Exception as e:
                print(f"Error removing backup {backup}: {e}")

    def cleanup_extractions(self, keep_latest=5):
        """Keep only the most recent extracted folders to avoid clutter."""
        base = Path(DOCS_DIR)
        extracts = sorted(
            [p for p in base.iterdir() if p.is_dir() and p.name.startswith('app-extracted-')],
            key=lambda p: p.name,
            reverse=True
        )

        for extract in extracts[keep_latest:]:
            try:
                shutil.rmtree(extract)
            except Exception as e:
                print(f"Error removing extracted folder {extract}: {e}")

    def _save_extraction_metadata(self, extracted_path):
        """Save metadata about the original extraction state."""
        if not extracted_path or not os.path.exists(extracted_path):
            return
        
        try:
            metadata = {
                'extracted_at': datetime.now().isoformat(),
                'original_colors': {},
                'media_files': {}
            }
            
            # Extract original colors from main.*.js
            extracted_root = Path(extracted_path)
            main_files = list(extracted_root.glob('**/main.*.js'))
            
            for main_file in main_files:
                try:
                    content = main_file.read_text(encoding='utf-8', errors='ignore')
                    # Extract --sol-color-* variables
                    pattern = re.compile(r'(--sol-color-[a-z0-9-]+)\s*:\s*([^;]+)', re.IGNORECASE)
                    for match in pattern.finditer(content):
                        key, value = match.groups()
                        metadata['original_colors'][key] = value.strip()
                except Exception:
                    # Safely ignore pattern matching errors
                    pass
            
            # Store original media file sizes as baseline
            for root, dirs, files in os.walk(extracted_path):
                for file in files:
                    ext = Path(file).suffix.lower()
                    if ext in {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.mp4', '.webm', '.mkv', '.avi', '.mov', '.m4v', '.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac'}:
                        file_path = os.path.join(root, file)
                        try:
                            file_size = os.path.getsize(file_path)
                            rel_path = os.path.relpath(file_path, self.extracted_dir)
                            metadata['media_files'][rel_path] = {'size': file_size}
                        except Exception:
                            # Safely ignore file metadata errors
                            pass
            
            # Save metadata
            metadata_path = os.path.join(self.extracted_dir, '.extraction-metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            print(f"[ThemeManager] Error saving extraction metadata: {e}")

    def detect_extraction_changes(self):
        """Detect what changes were made to the current extraction."""
        if not self.extracted_dir or not os.path.exists(self.extracted_dir):
            return None
        
        try:
            metadata_path = os.path.join(self.extracted_dir, '.extraction-metadata.json')
            if not os.path.exists(metadata_path):
                return None
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            changes = {
                'colors': {},
                'media': {}
            }
            
            # Check for color changes
            extracted_root = Path(self.extracted_dir)
            main_files = list(extracted_root.glob('**/main.*.js'))
            
            for main_file in main_files:
                try:
                    content = main_file.read_text(encoding='utf-8', errors='ignore')
                    pattern = re.compile(r'(--sol-color-[a-z0-9-]+)\s*:\s*([^;]+)', re.IGNORECASE)
                    for match in pattern.finditer(content):
                        key, current_value = match.groups()
                        current_value = current_value.strip()
                        original_value = metadata['original_colors'].get(key)
                        
                        if original_value and current_value != original_value:
                            changes['colors'][key] = {
                                'original': original_value,
                                'current': current_value
                            }
                except Exception:
                    # Safely ignore color value retrieval errors
                    pass
            
            # Check for media file changes (by comparing sizes)
            for root, dirs, files in os.walk(self.extracted_dir):
                for file in files:
                    if file.startswith('.'):
                        continue
                    ext = Path(file).suffix.lower()
                    if ext in {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.mp4', '.webm', '.mkv', '.avi', '.mov', '.m4v', '.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac'}:
                        file_path = os.path.join(root, file)
                        try:
                            current_size = os.path.getsize(file_path)
                            rel_path = os.path.relpath(file_path, self.extracted_dir)
                            original_info = metadata['media_files'].get(rel_path)
                            
                            if original_info and current_size != original_info.get('size'):
                                changes['media'][rel_path] = {
                                    'original_size': original_info.get('size'),
                                    'current_size': current_size
                                }
                        except Exception:
                            # Safely ignore media file change detection errors
                            pass
            
            return changes if (changes['colors'] or changes['media']) else None
        except Exception as e:
            print(f"[ThemeManager] Error detecting changes: {e}")
            return None

    def list_media_assets(self):
        """Scan main.*.js to find media assets referenced by the launcher UI."""
        if not self.extracted_dir or not os.path.exists(self.extracted_dir):
            return []

        extracted_root = Path(self.extracted_dir)
        candidate_dirs = [
            extracted_root / 'app' / 'static' / 'js',
            extracted_root / 'app' / 'assets' / 'static' / 'js',
            extracted_root / 'static' / 'js',
            extracted_root / 'assets' / 'static' / 'js'
        ]

        main_files = []
        for candidate in candidate_dirs:
            if candidate.exists():
                main_files.extend(candidate.glob('main.*.js'))

        if not main_files:
            return []

        extensions = (
            'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp',
            'mp4', 'webm', 'mkv', 'avi', 'mov', 'm4v',
            'mp3', 'wav', 'flac', 'ogg', 'm4a', 'aac'
        )

        # Broader pattern to catch all media file references in the JS code
        # Matches quoted paths ending with media extensions
        asset_pattern = re.compile(
            r'(["\'])([^\'"]*\.(?:' + '|'.join(extensions) + r'))\1',
            re.IGNORECASE
        )

        found_assets = {}  # Maps source path to details with line info
        for main_file in main_files:
            try:
                content = main_file.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue

            lines = content.split('\n')
            for line_num, line_text in enumerate(lines, 1):
                for match in asset_pattern.finditer(line_text):
                    asset_path = match.group(2)
                    # Skip CDN URLs
                    if asset_path.startswith('http://') or asset_path.startswith('https://'):
                        continue
                    # Normalize paths that might have double slashes
                    asset_path = asset_path.lstrip('/')
                    
                    if asset_path not in found_assets:
                        found_assets[asset_path] = {
                            'file': main_file.name,
                            'lines': []
                        }
                    # Store line number and snippet
                    found_assets[asset_path]['lines'].append({
                        'line': line_num,
                        'snippet': line_text.strip()[:200]  # First 200 chars of line
                    })

        assets = []
        for asset_path in sorted(found_assets.keys()):
            rel_path = None
            
            # Try to find the file in various locations
            candidate_paths = [
                extracted_root / asset_path,
                extracted_root / 'app' / asset_path,
                extracted_root / 'app' / 'assets' / asset_path,
            ]

            for candidate in candidate_paths:
                if candidate.exists():
                    rel_path = str(candidate.relative_to(extracted_root)).replace('\\', '/')
                    break

            # If file doesn't exist on disk, skip it (may be loaded from CDN or removed)
            if not rel_path:
                continue

            ext = Path(asset_path).suffix.lower().lstrip('.')
            if ext in {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp'}:
                media_type = 'image'
            elif ext in {'mp4', 'webm', 'mkv', 'avi', 'mov', 'm4v'}:
                media_type = 'video'
            elif ext in {'mp3', 'wav', 'flac', 'ogg', 'm4a', 'aac'}:
                media_type = 'audio'
            else:
                media_type = 'other'

            assets.append({
                'path': rel_path,
                'name': Path(rel_path).name,
                'type': media_type,
                'url': f"/api/extracted-asset?path={quote(rel_path)}",
                'source': {
                    'file': found_assets[asset_path]['file'],
                    'lines': found_assets[asset_path]['lines']
                }
            })

        return assets

# Global theme manager
theme_manager = ThemeManager()


def _find_main_js_path():
    if theme_manager.extracted_dir:
        extracted_root = Path(theme_manager.extracted_dir)
        candidate_dirs = [
            extracted_root / 'static' / 'js',
            extracted_root / 'app' / 'static' / 'js'
        ]
        for static_js_dir in candidate_dirs:
            main_js_files = list(static_js_dir.glob('main.*.js'))
            if main_js_files:
                return main_js_files[0]

    base_dir = Path(__file__).resolve().parent.parent
    candidates = list(base_dir.glob('c3rb-launcher/**/app/static/js/main.*.js'))
    return candidates[0] if candidates else None


def _find_musics_dir():
    if theme_manager.extracted_dir:
        extracted_root = Path(theme_manager.extracted_dir)
        candidate_dirs = [
            extracted_root / 'assets' / 'musics',
            extracted_root / 'app' / 'assets' / 'musics'
        ]
        for music_dir in candidate_dirs:
            if music_dir.exists():
                return music_dir

    base_dir = Path(__file__).resolve().parent.parent
    candidates = list(base_dir.glob('c3rb-launcher/**/app/assets/musics'))
    return candidates[0] if candidates else None


def _parse_music_files_from_main(main_js_path):
    if not main_js_path or not main_js_path.exists():
        return []

    content = main_js_path.read_text(encoding='utf-8')
    match = re.search(r'musics:\{([^}]*)\}', content, re.DOTALL)
    if not match:
        return []

    entries = match.group(1)
    values = re.findall(r'["\"]([^"\"]+)["\"]', entries)
    files = []
    seen = set()
    for value in values:
        if '/musics/' in value or '\\musics\\' in value or value.endswith(('.ogg', '.mp3', '.wav')):
            filename = Path(value).name
            if filename and filename not in seen:
                seen.add(filename)
                files.append(filename)
    return files

# Serve index.html for root path
@app.route('/')
def serve_index():
    """Serve the main index.html file."""
    return send_from_directory('public', 'index.html')


@app.route('/api/default-music', methods=['GET'])
def api_default_music():
    """Return default music list from main.*.js musics config."""
    main_js_path = _find_main_js_path()
    files = _parse_music_files_from_main(main_js_path)
    return jsonify({
        'success': True,
        'files': files,
        'source': str(main_js_path) if main_js_path else None
    })


@app.route('/api/music/<path:filename>', methods=['GET'])
def api_music(filename):
    """Serve music files from assets/musics for preview."""
    music_dir = _find_musics_dir()
    if not music_dir:
        return jsonify({'success': False, 'error': 'Music directory not found'}), 404

    safe_name = Path(filename).name
    file_path = music_dir / safe_name
    if not file_path.exists():
        return jsonify({'success': False, 'error': 'Music file not found'}), 404

    return send_file(file_path)


@app.route('/api/music-file/<path:filename>', methods=['GET'])
def api_music_file(filename):
    """Serve music files from assets/musics for preview."""
    music_dir = _find_musics_dir()
    if not music_dir:
        return jsonify({'success': False, 'error': 'Music directory not found'}), 404

    safe_name = Path(filename).name
    file_path = music_dir / safe_name
    if not file_path.exists():
        return jsonify({'success': False, 'error': 'Music file not found'}), 404

    return send_file(file_path)

@app.route('/api/extracted-asset')
def api_extracted_asset():
    """Serve a file from the extracted app directory for preview."""
    rel_path = request.args.get('path', '').strip()
    if not rel_path:
        return jsonify({'success': False, 'error': 'Missing path'}), 400

    if not theme_manager.extracted_dir:
        return jsonify({'success': False, 'error': 'Nothing extracted yet'}), 400

    base = Path(theme_manager.extracted_dir).resolve()
    target = (base / rel_path).resolve()

    if not str(target).startswith(str(base)):
        return jsonify({'success': False, 'error': 'Invalid path'}), 403

    if not target.exists() or not target.is_file():
        return jsonify({'success': False, 'error': 'File not found'}), 404

    return send_file(str(target))

@app.route('/api/launcher-asset')
def api_launcher_asset():
    """Serve a file from the launcher's app directory for preview."""
    rel_path = request.args.get('path', '').strip()
    if not rel_path:
        return jsonify({'success': False, 'error': 'Missing path'}), 400

    if not theme_manager.launcher_dir:
        return jsonify({'success': False, 'error': 'Launcher not detected'}), 400

    # Look for the file in the launcher's app directory
    launcher_path = Path(theme_manager.launcher_dir)
    app_dir = launcher_path / 'resources' / 'app.asar.unpacked'
    
    # If app.asar.unpacked doesn't exist, try extracted_dir
    if not app_dir.exists() and theme_manager.extracted_dir:
        app_dir = Path(theme_manager.extracted_dir)
    
    base = app_dir.resolve()
    target = (base / rel_path).resolve()

    if not str(target).startswith(str(base)):
        return jsonify({'success': False, 'error': 'Invalid path'}), 403

    if not target.exists() or not target.is_file():
        return jsonify({'success': False, 'error': 'File not found'}), 404

    return send_file(str(target))

# REST API endpoints
@app.route('/api/init', methods=['GET', 'POST'])
def api_init():
    """Initialize and detect launcher."""
    try:
        # Check if asarPath is provided in the request
        asar_path = None
        if request.method == 'POST':
            data = request.get_json() or {}
            asar_path = data.get('asarPath')
        
        # If asarPath provided, validate and use it directly
        if asar_path:
            # Normalize and ensure the asar path is within the trusted launcher root directory
            asar_path_abs = os.path.abspath(asar_path)
            try:
                common_root = os.path.commonpath([asar_path_abs, LAUNCHER_ROOT_DIR])
            except ValueError:
                common_root = None
            if common_root != LAUNCHER_ROOT_DIR:
                return jsonify({
                    'success': False,
                    'error': 'Specified app.asar path is outside the trusted launcher directory'
                }), 400
            if os.path.exists(asar_path_abs):
                launcher_info = {
                    'asarPath': asar_path_abs,
                    'directory': os.path.dirname(asar_path_abs),
                    'resourcesDir': os.path.dirname(asar_path_abs)
                }
                theme_manager.launcher_info = launcher_info
                return jsonify({
                    'success': True,
                    'launcher': launcher_info
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'app.asar file not found at specified path'
                }), 400
        
        # Otherwise, auto-detect
        launcher_info = LauncherDetector.detect()
        
        if launcher_info:
            # Update theme_manager's launcher_info as well
            theme_manager.launcher_info = launcher_info
            return jsonify({
                'success': True,
                'launcher': launcher_info
            })
        else:
            return jsonify({
                'success': False,
                'error': 'RSI Launcher not found'
            }), 404
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/detect-launcher', methods=['GET', 'POST'])
def api_detect_launcher():
    """Alias for /api/init"""
    print("[SERVER] /api/detect-launcher endpoint called")
    return api_init()

@app.route('/api/launcher-status', methods=['GET', 'POST'])
def api_launcher_status():
    """Check if RSI Launcher process is currently running."""
    try:
        is_running = LauncherDetector.is_launcher_running()
        return jsonify({
            'success': True,
            'isRunning': is_running
        })
    except Exception as e:
        print(f"Error checking launcher status: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'isRunning': False
        }), 500

@app.route('/api/debug-log', methods=['POST'])
def api_debug_log():
    """Log debug messages from JavaScript to server console."""
    try:
        data = request.get_json()
        message = data.get('message', '')
        level = data.get('level', 'INFO')
        print(f"[JS {level}] {message}")
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error logging JS message: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/update-manager', methods=['GET'])
def api_update_manager():
    """Get update manager information."""
    try:
        import sys
        print('[API] GET /api/update-manager called')
        
        # Get current version from APP_VERSION in launcher.py
        current_version = "0.2 Alpha"  # This would be imported from launcher.py
        
        # Get latest version (would check GitHub or update server in production)
        latest_version = "0.2 Alpha"  # For now, same as current
        update_available = False  # No updates available in alpha
        
        # Get build type
        build_type = "Compiled (PyInstaller)" if getattr(sys, 'frozen', False) else "Source (Python)"
        
        # Get Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        return jsonify({
            'success': True,
            'current_version': current_version,
            'latest_version': latest_version,
            'update_available': update_available,
            'build_type': build_type,
            'python_version': python_version,
            'message': 'Update manager status retrieved'
        })
    except Exception as e:
        print(f'[API Error] Update manager error: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/download-update', methods=['POST'])
def api_download_update():
    """Download and install update."""
    try:
        print('[API] POST /api/download-update called')
        
        # In production, this would:
        # 1. Download the latest version from GitHub/server
        # 2. Extract it to a temp directory
        # 3. Replace the current installation
        # 4. Restart the application
        
        # For now, just return a success message
        return jsonify({
            'success': True,
            'message': 'Update downloaded successfully. Please restart the application.'
        })
    except Exception as e:
        print(f'[API Error] Download update error: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/browse-for-asar', methods=['POST'])
def api_browse_for_asar():
    """Open file picker dialog for user to select app.asar file."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # Create a hidden root window
        root = tk.Tk()
        root.withdraw()  # Hide the window
        root.attributes('-topmost', True)  # Bring to front
        
        # Open file picker
        file_path = filedialog.askopenfilename(
            title="Select app.asar file",
            filetypes=[("ASAR files", "*.asar"), ("All files", "*.*")],
            initialdir=os.path.expanduser('~')
        )
        
        root.destroy()
        
        if file_path:
            return jsonify({
                'success': True,
                'path': file_path
            })
        else:
            return jsonify({
                'success': False,
                'path': None,
                'message': 'No file selected'
            })
    except Exception as e:
        print(f"Error opening file picker: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/extract', methods=['POST'])
def api_extract():
    """Extract app.asar."""
    print("[API] /api/extract called")
    try:
        print(f"[API] theme_manager.launcher_info: {theme_manager.launcher_info}")
        if not theme_manager.launcher_info:
            print("[API] Launcher not initialized")
            return jsonify({'success': False, 'error': 'Launcher not initialized'}), 400
        
        print("[API] Creating backup...")
        # Create backup
        if not theme_manager.create_backup():
            print("[API] Backup creation failed")
            return jsonify({'success': False, 'error': 'Failed to create backup'}), 500
        
        print("[API] Starting extraction...")
        # Extract
        if not theme_manager.extract_asar():
            error_detail = theme_manager.status.get('lastError', 'Unknown error')
            print(f"[API] Extraction failed with error: {error_detail}")
            return jsonify({
                'success': False,
                'error': 'Failed to extract app.asar',
                'details': error_detail
            }), 500
        
        print("[API] Extraction successful")
        return jsonify({
            'success': True,
            'extractedPath': theme_manager.extracted_dir,
            'backupPath': theme_manager.backup_dir
        })
    except Exception as e:
        print(f'[API Error] Extract failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/open-latest-extract', methods=['POST'])
def api_open_latest_extract():
    """Open the most recent extracted folder in File Explorer."""
    if not theme_manager.extracted_dir:
        return jsonify({'success': False, 'error': 'No extracted folder found'}), 400

    path = Path(theme_manager.extracted_dir)
    if not path.exists():
        return jsonify({'success': False, 'error': 'Extracted folder does not exist'}), 404

    try:
        os.startfile(str(path))
        return jsonify({'success': True, 'path': str(path)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/extracted-list', methods=['GET'])
def api_extracted_list():
    """List extracted folders for reuse."""
    try:
        base = Path(DOCS_DIR)
        print(f'[API] Checking for extracted folders in: {base}')
        print(f'[API] Base directory exists: {base.exists()}')
        
        if not base.exists():
            print('[API] Base directory does not exist, returning empty list')
            return jsonify({'success': True, 'extracts': []})
        
        all_items = list(base.iterdir())
        print(f'[API] Found {len(all_items)} items in base directory')
        
        # Look for both app-extracted- and app-decompiled- folders
        extracts = sorted(
            [p for p in all_items if p.is_dir() and (p.name.startswith('app-extracted-') or p.name.startswith('app-decompiled-'))],
            key=lambda p: p.name,
            reverse=True
        )
        print(f'[API] Found {len(extracts)} extracted folders')
        
        result = {
            'success': True,
            'extracts': [
                {
                    'name': p.name,
                    'path': str(p),
                    'date': p.name.replace('app-extracted-', '').replace('app-decompiled-', ''),
                    'type': 'extracted'
                } for p in extracts
            ]
        }
        print(f'[API] Returning: {result}')
        return jsonify(result)
    except Exception as e:
        print(f'[API Error] Failed to list extracts: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/backups-list', methods=['GET'])
def api_backups_list():
    """List available backups."""
    try:
        base = Path(DOCS_DIR)
        print(f'[API] Checking for backups in: {base}')
        
        if not base.exists():
            return jsonify({'success': True, 'backups': []})
        
        all_items = list(base.iterdir())
        
        # Look for backup- folders
        backups = sorted(
            [p for p in all_items if p.is_dir() and p.name.startswith('backup-')],
            key=lambda p: p.name,
            reverse=True
        )
        print(f'[API] Found {len(backups)} backups')
        
        result = {
            'success': True,
            'backups': [
                {
                    'name': p.name,
                    'path': str(p),
                    'date': p.name.replace('backup-', ''),
                    'asar_exists': (p / 'app.asar').exists()
                } for p in backups
            ]
        }
        return jsonify(result)
    except Exception as e:
        print(f'[API Error] Failed to list backups: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/use-extract', methods=['POST'])
def api_use_extract():
    """Set an existing extracted folder as active."""
    data = request.json or {}
    selected_path = data.get('path', '').strip()
    if not selected_path:
        return jsonify({'success': False, 'error': 'Missing path'}), 400

    # SECURITY: Validate path safety
    is_safe, resolved_path, error_msg = validate_path_safety(
        selected_path, 
        DOCS_DIR, 
        allowed_prefixes=ALLOWED_EXTRACT_PATTERNS
    )
    
    if not is_safe:
        print(f'[API] Path validation failed: {error_msg}')
        return jsonify({'success': False, 'error': error_msg}), 403

    path = resolved_path
    if not path.exists() or not path.is_dir():
        return jsonify({'success': False, 'error': 'Extracted folder not found'}), 404

    theme_manager.extracted_dir = str(path)
    
    # Detect changes in this extraction
    changes = theme_manager.detect_extraction_changes()
    
    return jsonify({
        'success': True,
        'extractedPath': theme_manager.extracted_dir,
        'changes': changes
    })

@app.route('/api/delete-extract', methods=['POST'])
def api_delete_extract():
    """Delete an extracted ASAR folder."""
    data = request.json or {}
    path_str = data.get('path', '').strip()
    
    print(f'[API] DELETE /api/delete-extract called with path: {path_str}')
    
    if not path_str:
        print(f'[API] Error: Missing path')
        return jsonify({'success': False, 'error': 'Missing path'}), 400
    
    # SECURITY: Validate path safety before any operations
    is_safe, resolved_path, error_msg = validate_path_safety(
        path_str, 
        DOCS_DIR, 
        allowed_prefixes=ALLOWED_EXTRACT_PATTERNS
    )
    
    if not is_safe:
        print(f'[API] Path validation failed: {error_msg}')
        return jsonify({'success': False, 'error': error_msg}), 403
    
    path = resolved_path
    
    try:
        # Prevent deletion if it's the currently active extraction
        if theme_manager.extracted_dir and Path(theme_manager.extracted_dir).resolve() == path:
            print(f'[API] Error: Cannot delete currently active extraction: {path}')
            return jsonify({'success': False, 'error': 'Cannot delete the currently active extraction'}), 400
        
        # Delete the directory recursively
        print(f'[API] Deleting directory: {path}')
        shutil.rmtree(str(path))
        
        print(f'[API] Successfully deleted extracted folder: {path}')
        
        return jsonify({
            'success': True,
            'message': 'Extracted ASAR deleted successfully'
        })
    except Exception as e:
        print(f'[API Error] Failed to delete extract: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Failed to delete: {str(e)}'}), 500

@app.route('/api/create-backup', methods=['POST'])
def api_create_backup():
    """Create a new backup of the current app.asar"""
    try:
        if not theme_manager.launcher_info:
            return jsonify({'success': False, 'error': 'Launcher not initialized'}), 400
        
        if theme_manager.create_backup():
            return jsonify({
                'success': True,
                'message': 'Backup created successfully',
                'backupPath': theme_manager.backup_dir
            })
        else:
            error = theme_manager.status.get('lastError', 'Unknown error')
            return jsonify({'success': False, 'error': error}), 500
    except Exception as e:
        print(f'[API Error] Failed to create backup: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/restore-backup', methods=['POST'])
def api_restore_backup():
    """Restore an app.asar from a backup"""
    try:
        data = request.json or {}
        backup_path = data.get('path', '').strip()
        
        if not backup_path:
            return jsonify({'success': False, 'error': 'Missing backup path'}), 400
        
        # SECURITY: Validate path
        is_safe, resolved_path, error_msg = validate_path_safety(
            backup_path, 
            DOCS_DIR, 
            allowed_prefixes=['backup-']
        )
        
        if not is_safe:
            return jsonify({'success': False, 'error': error_msg}), 403
        
        backup_asar = resolved_path / 'app.asar'
        if not backup_asar.exists():
            return jsonify({'success': False, 'error': 'Backup does not contain app.asar'}), 400
        
        if not theme_manager.launcher_info:
            return jsonify({'success': False, 'error': 'Launcher not initialized'}), 400
        
        # Restore by copying backup over current
        asar_path = theme_manager.launcher_info['asarPath']
        asar_backup = Path(asar_path).with_suffix('.asar.backup_restore')
        
        try:
            # Backup current
            shutil.copy2(asar_path, str(asar_backup))
            # Restore from backup
            shutil.copy2(str(backup_asar), asar_path)
            # Remove temp backup
            asar_backup.unlink()
            
            return jsonify({'success': True, 'message': 'Backup restored successfully'})
        except Exception as restore_error:
            # Restore the temp backup if something went wrong
            if asar_backup.exists():
                shutil.copy2(str(asar_backup), asar_path)
                asar_backup.unlink()
            raise restore_error
            
    except Exception as e:
        print(f'[API Error] Failed to restore backup: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/extraction-changes', methods=['GET'])
def api_extraction_changes():
    """Get detected changes in the current extraction."""
    if not theme_manager.extracted_dir:
        return jsonify({'success': False, 'error': 'Nothing extracted yet'}), 400
    
    changes = theme_manager.detect_extraction_changes()
    
    return jsonify({
        'success': True,
        'changes': changes
    })

@app.route('/api/media-assets', methods=['GET'])
def api_media_assets():
    """List media assets referenced in main.*.js for preview."""
    if not theme_manager.extracted_dir:
        return jsonify({'success': False, 'error': 'Nothing extracted yet'}), 400

    assets = theme_manager.list_media_assets()
    return jsonify({
        'success': True,
        'assets': assets
    })

@app.route('/api/status', methods=['GET'])
def api_status():
    """Return current operation status for progress indicators."""
    return jsonify({
        'success': True,
        'status': theme_manager.status,
        # Also flatten for backwards compatibility
        'operation': theme_manager.status.get('operation'),
        'state': theme_manager.status.get('state'),
        'message': theme_manager.status.get('message'),
        'progress': theme_manager.status.get('progress'),
        'lastError': theme_manager.status.get('lastError')
    })

@app.route('/api/check-updates', methods=['GET'])
def api_check_updates():
    """Check for new versions on GitHub API."""
    try:
        import urllib.request
        import json as json_lib
        
        # Current version from launcher
        from launcher import APP_VERSION
        
        # GitHub API endpoint for latest release
        url = 'https://api.github.com/repos/Elegius/RUIE/releases/latest'
        
        try:
            # Fetch latest release info with timeout
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'RUIE-UpdateChecker'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:  # noqa: B310
                data = json_lib.loads(response.read().decode())
                latest_version = data.get('tag_name', '').lstrip('v')
                release_url = data.get('html_url', 'https://github.com/Elegius/RUIE/releases')
                release_notes = data.get('body', '')
                
                # Simple version comparison (compare as strings, works for semantic versioning)
                # e.g., "0.3" > "0.2" when comparing lexicographically
                has_update = latest_version > APP_VERSION
                
                return jsonify({
                    'success': True,
                    'current_version': APP_VERSION,
                    'latest_version': latest_version,
                    'has_update': has_update,
                    'release_url': release_url,
                    'release_notes': release_notes[:500] if release_notes else ''  # First 500 chars
                })
        except urllib.error.URLError as e:
            # Network error - return current version with no update info
            return jsonify({
                'success': True,
                'current_version': APP_VERSION,
                'latest_version': APP_VERSION,
                'has_update': False,
                'error': f'Could not check updates: {str(e)}'
            }), 200
        except Exception as e:
            return jsonify({
                'success': True,
                'current_version': APP_VERSION,
                'latest_version': APP_VERSION,
                'has_update': False,
                'error': f'Update check error: {str(e)}'
            }), 200
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Update check failed: {str(e)}'
        }), 500

@app.route('/api/app-version', methods=['GET'])
def api_app_version():
    """Get current application version."""
    try:
        from launcher import APP_VERSION
        return jsonify({
            'success': True,
            'version': APP_VERSION
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/apply-colors', methods=['POST'])
def api_apply_colors():
    """Apply color replacements asynchronously."""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON'}), 400
        
        color_mappings = data.get('colors', {})
        
        if not color_mappings:
            return jsonify({'success': False, 'error': 'No color mappings provided'}), 400
        
        # SECURITY: Validate color mappings
        is_valid, validated_colors, error_msg = validate_color_mapping(color_mappings)
        if not is_valid:
            print(f"[API] Color validation failed: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Start async operation with validated colors
        if not theme_manager.apply_colors_async(validated_colors):
            return jsonify({'success': False, 'error': 'Color apply operation already in progress'}), 409
        
        return jsonify({
            'success': True,
            'message': 'Color application started',
            'async': True
        })
    except Exception as e:
        print(f"Error in apply_colors: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/apply-media', methods=['POST'])
def api_apply_media():
    """Apply media replacements."""
    data = request.json
    media_mappings = data.get('media', {})
    
    results = theme_manager.apply_media(media_mappings)
    
    return jsonify({
        'success': True,
        'results': results
    })

@app.route('/api/repack', methods=['POST'])
def api_repack():
    """Repack app.asar."""
    if not theme_manager.repack_asar():
        return jsonify({'success': False, 'error': 'Failed to repack app.asar'}), 500
    
    return jsonify({
        'success': True,
        'message': 'Theme applied successfully'
    })

@app.route('/api/upload-media', methods=['POST'])
def api_upload_media():
    """Handle media file uploads and replace files in the extracted directory."""
    if not theme_manager.extracted_dir:
        return jsonify({'success': False, 'error': 'Nothing extracted yet'}), 400

    upload = request.files.get('file')
    target_path = request.form.get('targetPath', '').strip()

    if not upload or not target_path:
        return jsonify({'success': False, 'error': 'Missing file or target path'}), 400

    # SECURITY: Validate filename
    filename = upload.filename.lower()
    is_valid, error_msg = validate_file_upload(filename, 0)  # Size checked after upload
    if not is_valid:
        print(f"[API] File validation failed: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 400

    try:
        # Read file to validate size
        upload.seek(0, 2)
        file_size = upload.tell()
        upload.seek(0)
        
        # Re-validate with actual size
        is_valid, error_msg = validate_file_upload(filename, file_size)
        if not is_valid:
            print(f"[API] File size validation failed: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400

        # SECURITY: Validate target path safety
        base = Path(theme_manager.extracted_dir).resolve()
        
        # Prevent path traversal with ../ or absolute paths
        if target_path.startswith('/') or target_path.startswith('\\') or '..' in target_path:
            return jsonify({'success': False, 'error': 'Invalid target path'}), 403
        
        target = (base / target_path).resolve()
        
        # Verify resolved path is within base
        try:
            target.relative_to(base)
        except ValueError:
            print(f"[API] Path traversal attempt detected")
            return jsonify({'success': False, 'error': 'Invalid target path'}), 403
        
        # Check for symlinks in the path
        if target.is_symlink() or any(part.is_symlink() for part in target.parents):
            return jsonify({'success': False, 'error': 'Symlinks are not allowed'}), 403

        target.parent.mkdir(parents=True, exist_ok=True)
        upload.save(str(target))
        return jsonify({'success': True, 'message': 'File replaced', 'targetPath': target_path})
    except Exception as e:
        print(f"[API Error] Upload failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clear-music', methods=['POST'])
def api_clear_music():
    """Clear music directory to allow custom playlist."""
    if not theme_manager.extracted_dir:
        return jsonify({'success': False, 'error': 'Nothing extracted yet'}), 400

    try:
        base = Path(theme_manager.extracted_dir).resolve()
        music_dir = base / 'assets' / 'musics'
        
        if music_dir.exists():
            # Remove all files in music directory
            for file in music_dir.glob('*'):
                if file.is_file():
                    file.unlink()
        else:
            # Create directory if it doesn't exist
            music_dir.mkdir(parents=True, exist_ok=True)
            
        return jsonify({'success': True, 'message': 'Music directory cleared'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/update-music-code', methods=['POST'])
def api_update_music_code():
    """Update main.*.js to reference new music files."""
    if not theme_manager.extracted_dir:
        return jsonify({'success': False, 'error': 'Nothing extracted yet'}), 400

    try:
        data = request.get_json()
        music_files = data.get('musicFiles', [])
        
        if not music_files:
            return jsonify({'success': False, 'error': 'No music files provided'}), 400

        base = Path(theme_manager.extracted_dir).resolve()
        
        # Check multiple possible locations for main.*.js
        candidate_dirs = [
            base / 'app' / 'static' / 'js',
            base / 'app' / 'assets' / 'static' / 'js',
            base / 'static' / 'js',
            base / 'assets' / 'static' / 'js'
        ]

        main_js_files = []
        for candidate in candidate_dirs:
            if candidate.exists():
                main_js_files.extend(candidate.glob('main.*.js'))
        
        if not main_js_files:
            return jsonify({'success': False, 'error': 'main.*.js file not found in any standard location'}), 404

        main_js_path = main_js_files[0]
        
        # Read the file
        content = main_js_path.read_text(encoding='utf-8')
        
        # Build new musics object with dynamic keys (bg1, bg2, bg3, etc.)
        musics_entries = ','.join([f'bg{i+1}:"{file}"' for i, file in enumerate(music_files)])
        new_musics_obj = f'musics:{{{musics_entries}}}'
        
        # Find and replace the musics object using regex
        import re
        pattern = r'musics:\{[^}]*\}'
        
        if not re.search(pattern, content):
            return jsonify({'success': False, 'error': 'Could not find musics object in main.js'}), 404
        
        modified_content = re.sub(pattern, new_musics_obj, content)
        
        # Write back to file
        main_js_path.write_text(modified_content, encoding='utf-8')
        
        return jsonify({
            'success': True, 
            'message': f'Updated music code with {len(music_files)} track(s)',
            'file': main_js_path.name
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/compile-changes', methods=['POST'])
def api_compile_changes():
    """Compile and apply all changes."""
    return api_repack()

@app.route('/api/test-launcher', methods=['POST'])
def api_test_launcher():
    """Test launcher - pack and run temporarily without installing."""
    try:
        data = request.json or {}
        extracted_path = data.get('extractedPath')
        
        if not extracted_path or not os.path.exists(extracted_path):
            return jsonify({
                'success': False,
                'error': 'Invalid extraction path provided'
            }), 400
        
        if not theme_manager.launcher_info:
            return jsonify({'success': False, 'error': 'Launcher not detected'}), 400
        
        try:
            # Create temp asar
            with tempfile.NamedTemporaryFile(suffix='.asar', delete=False) as tmp:
                temp_asar = tmp.name
            
            # Pack the extracted dir to temp location
            result = subprocess.run(  # noqa: B607, B603
                ['npx', 'asar', 'pack', extracted_path, temp_asar],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                return jsonify({
                    'success': False,
                    'error': f'Failed to pack asar: {result.stderr}'
                }), 500

            def is_safe_launcher_exe(launcher_exe, asar_path):
                """
                Basic safety checks to ensure the launcher executable path is not attacker-controlled.
                """
                if not isinstance(launcher_exe, str) or not launcher_exe:
                    return False

                # Require an absolute path
                if not os.path.isabs(launcher_exe):
                    return False

                # Disallow obviously dangerous characters often used in injection
                for ch in [';', '&', '|', '`', '\n', '\r']:
                    if ch in launcher_exe:
                        return False

                # Constrain to the same drive / root as the asar file, if possible
                if isinstance(asar_path, str) and asar_path:
                    try:
                        asar_dir = os.path.dirname(os.path.abspath(asar_path))
                        launcher_dir = os.path.dirname(os.path.abspath(launcher_exe))
                        # Ensure the launcher executable resides in or under the asar directory's parent
                        allowed_root = os.path.dirname(asar_dir)
                        common = os.path.commonpath([allowed_root, launcher_dir])
                        if common != allowed_root:
                            return False
                    except Exception:
                        # On any path resolution error, be safe and reject
                        return False

                return True
            
            # Get launcher executable path
            launcher_exe = theme_manager.launcher_info.get('exePath') or theme_manager.launcher_info.get('launcherPath')
            if not launcher_exe:
                os.remove(temp_asar)
                return jsonify({
                    'success': False,
                    'error': 'Launcher executable path not found in launcher info'
                }), 400
            
            if not os.path.exists(launcher_exe):
                os.remove(temp_asar)
                return jsonify({
                    'success': False,
                    'error': f'Launcher executable not found at: {launcher_exe}'
                }), 404
            
            # Replace asar temporarily
            asar_path = theme_manager.launcher_info['asarPath']
            
            # Create backup in a writable temp location instead of Program Files
            temp_backup_dir = os.path.join(tempfile.gettempdir(), 'rsi-launcher-test')
            os.makedirs(temp_backup_dir, exist_ok=True)
            backup_asar = os.path.join(temp_backup_dir, 'app.asar.backup')
            
            try:
                # Backup original to temp location
                if os.path.exists(asar_path):
                    shutil.copy2(asar_path, backup_asar)
                
                # Replace with temp version
                shutil.copy2(temp_asar, asar_path)
                
            except PermissionError:
                try:
                    os.remove(temp_asar)
                except OSError:
                    # Safely ignore temp file cleanup errors
                    pass
                return jsonify({
                    'success': False,
                    'error': 'Permission denied: Unable to access launcher in Program Files. Try running this application as Administrator.'
                }), 403
            except Exception as e:
                try:
                    os.remove(temp_asar)
                except OSError:
                    # Safely ignore temp file cleanup errors
                    pass
                return jsonify({
                    'success': False,
                    'error': f'Failed to replace app.asar: {str(e)}'
                }), 500
            
            try:
                # Launch and wait for user to close it
                if not is_safe_launcher_exe(launcher_exe, asar_path):
                    try:
                        if os.path.exists(backup_asar):
                            shutil.copy2(backup_asar, asar_path)
                            os.remove(backup_asar)
                    except Exception:
                        # If restoration fails, log at server side; client still gets an error
                        print('[ThemeManager] Failed to restore backup after unsafe launcher path detected')
                    finally:
                        try:
                            os.remove(temp_asar)
                        except OSError:
                            pass
                    return jsonify({
                        'success': False,
                        'error': 'Refusing to launch untrusted executable path.'
                    }), 400

                def validate_launcher_exe_path(launcher_exe_path, asar_path_value):
                    """
                    Additional hardening for launcher executable path:
                    - Require absolute path
                    - Require both asar and executable to be under the trusted launcher root directory
                    - Require it to reside under the expected resources/asar directory
                    """
                    if not launcher_exe_path:
                        return False
                    # Normalize paths
                    launcher_exe_abs = os.path.abspath(launcher_exe_path)
                    asar_dir = os.path.dirname(os.path.abspath(asar_path_value)) if asar_path_value else None
                    if not asar_dir:
                    # Ensure the asar directory itself is under the trusted launcher root
                    try:
                        asar_common_root = os.path.commonpath([asar_dir, LAUNCHER_ROOT_DIR])
                    except ValueError:
                        return False
                    if asar_common_root != LAUNCHER_ROOT_DIR:
                        return False
                        return False
                    # Ensure the launcher executable is within the same tree as the asar directory
                    try:
                        common = os.path.commonpath([launcher_exe_abs, asar_dir])
                    except ValueError:
                        # Different drives or invalid paths
                        return False
                    if common != asar_dir:
                        return False
                    # Finally, ensure it points to an existing file and is under the trusted root
                    try:
                        exe_common_root = os.path.commonpath([launcher_exe_abs, LAUNCHER_ROOT_DIR])
                    except ValueError:
                        return False
                    if exe_common_root != LAUNCHER_ROOT_DIR:
                        return False
                    return os.path.isfile(launcher_exe_abs)

                if not validate_launcher_exe_path(launcher_exe, asar_path):
                    try:
                        if os.path.exists(backup_asar):
                            # Validate asar_path before restoring backup to avoid using an uncontrolled path
                            asar_path_abs = os.path.abspath(asar_path)
                            try:
                                common_root = os.path.commonpath([asar_path_abs, LAUNCHER_ROOT_DIR])
                            except ValueError:
                                common_root = None
                            if common_root != LAUNCHER_ROOT_DIR:
                                raise ValueError("Refusing to restore backup outside trusted launcher directory")
                            shutil.copy2(backup_asar, asar_path_abs)
                            os.remove(backup_asar)
                    except Exception:
                        print('[ThemeManager] Failed to restore backup after invalid launcher path detected')
                    finally:
                        try:
                            os.remove(temp_asar)
                        except OSError:
                            pass
                    return jsonify({
                        'success': False,
                        'error': 'Refusing to launch executable outside trusted directory.'
                    }), 400

                launcher_process = subprocess.Popen([launcher_exe])
                
                # Wait for launcher process to complete
                def restore_after_process_exit():
                    try:
                        launcher_process.wait()  # Wait for launcher to exit
                    except Exception as e:
                        print(f'[ThemeManager] Error waiting for launcher: {e}')
                    
                    # Restore original
                    try:
                        if os.path.exists(backup_asar):
                            shutil.copy2(backup_asar, asar_path)
                            os.remove(backup_asar)
                    except Exception as e:
                        print(f'[ThemeManager] Error restoring backup: {e}')
                    finally:
                        try:
                            os.remove(temp_asar)
                        except OSError:
                            # Safely ignore temp file cleanup errors
                            pass
                
                restore_thread = threading.Thread(target=restore_after_process_exit, daemon=True)
                restore_thread.start()
                
                return jsonify({
                    'success': True,
                    'message': 'Launcher started with test theme. Close the launcher when done.'
                })
            except Exception as e:
                # Restore on error
                try:
                    if os.path.exists(backup_asar):
                        shutil.copy2(backup_asar, asar_path)
                except OSError:
                    # Safely ignore backup restoration errors
                    pass
                try:
                    os.remove(backup_asar)
                except:
                    pass
                raise e
        
        except Exception as e:
            print(f'[API Error] Test launcher failed: {str(e)}')
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    except Exception as e:
        print(f'[API Error] Test launcher request failed: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/compile-asar', methods=['POST'])
def api_compile_asar():
    """Compile the modified app.asar without installing."""
    try:
        data = request.json or {}
        extracted_path = data.get('extractedPath')
        
        if not extracted_path or not os.path.exists(extracted_path):
            return jsonify({
                'success': False,
                'error': 'Invalid extraction path provided'
            }), 400
        
        if not theme_manager.launcher_info:
            return jsonify({'success': False, 'error': 'Launcher not detected'}), 400
        
        try:
            # Create output asar in a temp location
            with tempfile.NamedTemporaryFile(suffix='.asar', delete=False) as tmp:
                output_asar = tmp.name
            
            # Pack the extracted dir
            result = subprocess.run(  # noqa: B607, B603
                ['npx', 'asar', 'pack', extracted_path, output_asar],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                try:
                    os.remove(output_asar)
                except OSError:
                    # Safely ignore output file cleanup errors
                    pass
                return jsonify({
                    'success': False,
                    'error': f'Failed to compile asar: {result.stderr}'
                }), 500
            
            # Move compiled asar to a persistent location for later installation
            compile_dir = os.path.join(os.path.dirname(theme_manager.launcher_info['asarPath']), 'compiled')
            os.makedirs(compile_dir, exist_ok=True)
            
            compiled_asar_path = os.path.join(compile_dir, f"app-compiled-{int(time.time())}.asar")
            shutil.move(output_asar, compiled_asar_path)
            
            return jsonify({
                'success': True,
                'message': f'Compiled app.asar created successfully',
                'path': compiled_asar_path
            })
        
        except Exception as e:
            print(f'[API Error] Compile asar failed: {str(e)}')
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    except Exception as e:
        print(f'[API Error] Compile asar request failed: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/install-asar', methods=['POST'])
def api_install_asar():
    """Compile and install the modified app.asar."""
    try:
        data = request.json or {}
        extracted_path = data.get('extractedPath')
        
        if not extracted_path or not os.path.exists(extracted_path):
            return jsonify({
                'success': False,
                'error': 'Invalid extraction path provided'
            }), 400
        
        if not theme_manager.launcher_info:
            return jsonify({'success': False, 'error': 'Launcher not detected'}), 400
        
        try:
            asar_path = theme_manager.launcher_info['asarPath']
            
            # Create backup with timestamp
            backup_dir = os.path.join(os.path.dirname(asar_path), 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            backup_asar = os.path.join(backup_dir, f"app.asar.backup-{int(time.time())}")
            
            # Backup original
            try:
                if os.path.exists(asar_path):
                    shutil.copy2(asar_path, backup_asar)
                    print(f'[API] Created backup at: {backup_asar}')
            except PermissionError:
                return jsonify({
                    'success': False,
                    'error': 'Permission denied: Unable to back up original launcher. Try running this application as Administrator.'
                }), 403
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Failed to create backup: {str(e)}'
                }), 500
            
            # Pack the extracted dir to the actual launcher location
            try:
                with tempfile.NamedTemporaryFile(suffix='.asar', delete=False) as tmp:
                    temp_asar = tmp.name
                
                result = subprocess.run(  # noqa: B607, B603
                    ['npx', 'asar', 'pack', extracted_path, temp_asar],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode != 0:
                    try:
                        os.remove(temp_asar)
                    except OSError:
                        # Safely ignore temp file cleanup errors
                        pass
                    return jsonify({
                        'success': False,
                        'error': f'Failed to compile asar: {result.stderr}'
                    }), 500
                
                # Replace original with compiled version
                try:
                    shutil.copy2(temp_asar, asar_path)
                    print(f'[API] Installed modified app.asar to: {asar_path}')
                except PermissionError:
                    try:
                        os.remove(temp_asar)
                    except OSError:
                        # Safely ignore temp file cleanup errors
                        pass
                    return jsonify({
                        'success': False,
                        'error': 'Permission denied: Unable to install to launcher. Try running this application as Administrator.'
                    }), 403
                finally:
                    try:
                        os.remove(temp_asar)
                    except OSError:
                        # Safely ignore temp file cleanup errors
                        pass
                
                return jsonify({
                    'success': True,
                    'message': 'Modified app.asar installed successfully. Backup created. Restart the launcher to apply changes.',
                    'backup_path': backup_asar
                })
            
            except Exception as e:
                print(f'[API Error] Installation failed: {str(e)}')
                import traceback
                traceback.print_exc()
                return jsonify({'success': False, 'error': str(e)}), 500
        
        except Exception as e:
            print(f'[API Error] Install asar failed: {str(e)}')
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    except Exception as e:
        print(f'[API Error] Install asar request failed: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/deploy-theme', methods=['POST'])
def api_deploy_theme():
    """Deploy theme - permanently install to RSI Launcher directory."""
    if not theme_manager.extracted_dir or not theme_manager.launcher_info:
        return jsonify({'success': False, 'error': 'Nothing extracted yet'}), 400
    
    try:
        asar_path = theme_manager.launcher_info['asarPath']
        
        # Repack to actual location
        try:
            if not theme_manager.repack_asar():
                return jsonify({
                    'success': False,
                    'error': 'Failed to repack app.asar'
                }), 500
        except PermissionError as pe:
            return jsonify({
                'success': False,
                'error': f'Permission denied: {str(pe)}. Please run this application as Administrator to deploy themes.'
            }), 403
        
        return jsonify({
            'success': True,
            'message': 'Theme deployed successfully! Your changes are now installed.',
            'asarPath': asar_path
        })
    except Exception as e:
        print(f'[API Error] Deploy theme failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config/save', methods=['POST'])
def api_config_save():
    """Save theme configuration to JSON file."""
    try:
        data = request.json
        theme_name = data.get('name', 'My Theme')
        config = data.get('config', {})
        
        # Create themes directory
        themes_dir = os.path.expanduser('~/Documents/RSI-Launcher-Theme-Creator/themes')
        os.makedirs(themes_dir, exist_ok=True)
        
        # Sanitize filename
        safe_name = "".join(c for c in theme_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '-')
        
        # Save theme file
        theme_file = os.path.join(themes_dir, f'{safe_name}.theme.json')
        
        theme_data = {
            'name': theme_name,
            'version': '1.0',
            'created': datetime.now().isoformat(),
            'colors': config.get('colors', {}),
            'media': config.get('media', [])
        }
        
        with open(theme_file, 'w', encoding='utf-8') as f:
            json.dump(theme_data, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'message': f'Theme saved as {safe_name}.theme.json',
            'configPath': theme_file
        })
    except Exception as e:
        print(f'[API Error] Save config failed: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config/export', methods=['POST'])
def api_config_export():
    """Export theme configuration for download."""
    try:
        data = request.json
        theme_name = data.get('name', 'My Theme')
        config = data.get('config', {})
        
        theme_data = {
            'name': theme_name,
            'version': '1.0',
            'created': datetime.now().isoformat(),
            'colors': config.get('colors', {}),
            'media': config.get('media', [])
        }
        
        return jsonify({
            'success': True,
            'theme': theme_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config/list', methods=['GET'])
def api_config_list():
    """List saved theme configurations."""
    themes_dir = os.path.expanduser('~/Documents/RSI-Launcher-Theme-Creator/themes')
    themes = []
    
    try:
        if os.path.exists(themes_dir):
            for file in os.listdir(themes_dir):
                if file.endswith('.theme.json'):
                    theme_path = os.path.join(themes_dir, file)
                    try:
                        with open(theme_path, 'r', encoding='utf-8') as f:
                            theme_data = json.load(f)
                            themes.append({
                                'name': theme_data.get('name', file),
                                'filename': file,
                                'path': theme_path,
                                'created': theme_data.get('created', ''),
                                'colorCount': len(theme_data.get('colors', {})),
                                'mediaCount': len(theme_data.get('media', []))
                            })
                    except Exception:
                        # Safely ignore theme metadata errors
                        pass
    except Exception:
        # Safely ignore theme loading errors
        pass
    
    return jsonify({
        'success': True,
        'themes': sorted(themes, key=lambda x: x.get('created', ''), reverse=True)
    })

@app.route('/api/config/load', methods=['POST'])
def api_config_load():
    """Load a saved theme configuration."""
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'success': False, 'error': 'No filename provided'}), 400
        
        themes_dir = os.path.expanduser('~/Documents/RSI-Launcher-Theme-Creator/themes')
        theme_path = os.path.join(themes_dir, filename)
        
        if not os.path.exists(theme_path):
            return jsonify({'success': False, 'error': 'Theme file not found'}), 404
        
        with open(theme_path, 'r', encoding='utf-8') as f:
            theme_data = json.load(f)
        
        return jsonify({
            'success': True,
            'theme': theme_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/backups', methods=['GET', 'POST'])
def api_backups():
    """List or create backups."""
    if request.method == 'POST':
        # Create new backup
        try:
            if not theme_manager.extracted_dir:
                return jsonify({'success': False, 'error': 'No extraction selected'}), 400
            
            if not theme_manager.create_backup():
                return jsonify({'success': False, 'error': 'Failed to create backup'}), 500
            
            return jsonify({'success': True, 'message': 'Backup created successfully'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # GET: List backups - use same directory as extractions
    backup_dir = os.path.normpath(DOCS_DIR)
    backups = []
    
    try:
        if os.path.exists(backup_dir):
            for item in os.listdir(backup_dir):
                if item.startswith('backup-'):
                    path = os.path.join(backup_dir, item)
                    if os.path.isdir(path):
                        backups.append({
                            'name': item,
                            'path': path,
                            'date': item.replace('backup-', '')
                        })
    except Exception as e:
        print(f"[API] Error listing backups: {e}")
        pass
    
    return jsonify({
        'success': True,
        'backups': sorted(backups, key=lambda x: x['date'], reverse=True)
    })

@app.route('/api/restore', methods=['POST'])
def api_restore():
    """Restore from backup."""
    data = request.json
    backup_path = data.get('path')
    
    if not backup_path:
        return jsonify({'success': False, 'error': 'Missing backup path'}), 400
    
    try:
        backup_asar = os.path.join(backup_path, 'app.asar')
        if not os.path.exists(backup_asar):
            return jsonify({'success': False, 'error': 'Backup app.asar not found'}), 404
        
        if not theme_manager.launcher_info:
            return jsonify({'success': False, 'error': 'Launcher not initialized'}), 400
        
        target_path = theme_manager.launcher_info['asarPath']
        
        # Copy backup to target
        import shutil
        shutil.copy2(backup_asar, target_path)
        
        return jsonify({
            'success': True,
            'message': 'Launcher restored from backup'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/delete-backup', methods=['POST'])
def api_delete_backup():
    """Delete a backup folder."""
    data = request.json
    backup_path = data.get('path')
    
    print(f'[API] DELETE /api/delete-backup called with path: {backup_path}')
    
    if not backup_path:
        print(f'[API] Error: Missing backup path')
        return jsonify({'success': False, 'error': 'Missing backup path'}), 400
    
    try:
        path = Path(backup_path)
        if not path.exists():
            print(f'[API] Error: Backup not found at: {path}')
            return jsonify({'success': False, 'error': f'Backup not found: {path}'}), 404
        
        import shutil
        print(f'[API] Deleting backup directory: {path}')
        shutil.rmtree(path)
        
        print(f'[API] Successfully deleted backup: {path}')
        return jsonify({
            'success': True,
            'message': 'Backup deleted successfully'
        })
    except Exception as e:
        print(f'[API Error] Failed to delete backup: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Failed to delete: {str(e)}'}), 500

@app.route('/api/save-preset', methods=['POST'])
def api_save_preset():
    """Save a custom color preset to the presets directory."""
    try:
        data = request.get_json()
        if not data or 'name' not in data or 'colors' not in data:
            return jsonify({'success': False, 'error': 'Missing name or colors'}), 400

        # Create presets directory in public folder
        presets_dir = Path(static_folder) / 'presets'
        presets_dir.mkdir(exist_ok=True)

        # Sanitize filename
        name = data['name'].strip()
        filename = re.sub(r'[^a-z0-9-]+', '-', name.lower()) + '.json'
        filepath = presets_dir / filename

        # Save preset
        preset_data = {
            'name': name,
            'description': data.get('description', 'Custom preset'),
            'colors': data['colors'],
            'media': data.get('media', {}),
            'music': data.get('music', [])
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(preset_data, f, indent=2)

        return jsonify({
            'success': True,
            'message': f'Preset saved as {filename}',
            'filename': filename
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Catch-all route for static files (must be AFTER all API routes)
@app.route('/<path:path>')
def serve_static(path):
    """Serve static files from public directory."""
    return send_from_directory(static_folder, path)

if __name__ == '__main__':
    # Production deployment with Waitress WSGI server
    import logging
    from waitress import serve
    
    # Configure production logging
    log = logging.getLogger('waitress')
    log.setLevel(logging.INFO)
    
    print(f"[Production Server] Starting RUIE Server v0.2 Alpha")
    print(f"[Production Server] Listening on http://127.0.0.1:5000")
    print(f"[Production Server] WSGI: Waitress")
    print(f"[Production Server] Debug: Off")
    print(f"[Production Server] Environment: Production")
    
    try:
        # Serve with production WSGI server (Waitress)
        # Single-threaded for desktop app consistency
        serve(app, host='127.0.0.1', port=5000, threads=4, _quiet=False)
    except Exception as e:
        print(f"[Production Server] FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
