from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
import os
import json
import shutil
import subprocess
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

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)

# Configuration
DOCS_DIR = os.path.expanduser('~/Documents/RSI-Launcher-Theme-Creator')
os.makedirs(DOCS_DIR, exist_ok=True)

class ThemeManager:
    """Manage theme extraction, backup, and repacking."""
    
    def __init__(self):
        self.launcher_info = None
        self.extracted_dir = None
        self.backup_dir = None
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
        self.extracted_dir = os.path.join(DOCS_DIR, f'app-extracted-{timestamp}')
        
        try:
            self.set_status('extract', 'running', 'Extracting app.asar...', progress=10, last_error=None)
            print(f"[ThemeManager] Extracting from: {asar_path}")
            print(f"[ThemeManager] Extracting to: {self.extracted_dir}")
            
            # Use npx asar to extract (with shell=True to find npx in PATH)
            os.makedirs(self.extracted_dir, exist_ok=True)
            result = subprocess.run(
                f'npx asar extract "{asar_path}" "{self.extracted_dir}"',
                capture_output=True,
                text=True,
                check=False,
                shell=True
            )
            
            print(f"[ThemeManager] Extract return code: {result.returncode}")
            if result.stdout:
                print(f"[ThemeManager] Stdout: {result.stdout}")
            if result.stderr:
                print(f"[ThemeManager] Stderr: {result.stderr}")
            
            if result.returncode != 0:
                print(f"[ThemeManager] Error extracting asar: {result.stderr}")
                self.set_status('extract', 'error', 'Extraction failed', progress=0, last_error=result.stderr.strip() or 'Extraction failed')
                return False
            
            # Save metadata about original state
            self._save_extraction_metadata()
            
            print(f"[ThemeManager] Extract successful")
            self.set_status('extract', 'done', 'Extraction complete', progress=100, last_error=None)
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
            return False
        
        asar_path = self.launcher_info['asarPath']
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        self.backup_dir = os.path.join(DOCS_DIR, f'backup-{timestamp}')
        
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
            shutil.copy2(asar_path, os.path.join(self.backup_dir, 'app.asar'))
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def apply_colors(self, color_mappings):
        """Apply color replacements."""
        if not self.extracted_dir or not os.path.exists(self.extracted_dir):
            return 0
        
        return ColorReplacer.apply_colors(self.extracted_dir, color_mappings)
    
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
            
            # Repack (with shell=True for npx)
            result = subprocess.run(
                f'npx asar pack "{self.extracted_dir}" "{asar_path}"',
                capture_output=True,
                text=True,
                check=False,
                shell=True
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

    def _save_extraction_metadata(self):
        """Save metadata about the original extraction state."""
        if not self.extracted_dir or not os.path.exists(self.extracted_dir):
            return
        
        try:
            metadata = {
                'extracted_at': datetime.now().isoformat(),
                'original_colors': {},
                'media_files': {}
            }
            
            # Extract original colors from main.*.js
            extracted_root = Path(self.extracted_dir)
            main_files = list(extracted_root.glob('**/main.*.js'))
            
            for main_file in main_files:
                try:
                    content = main_file.read_text(encoding='utf-8', errors='ignore')
                    # Extract --sol-color-* variables
                    pattern = re.compile(r'(--sol-color-[a-z0-9-]+)\s*:\s*([^;]+)', re.IGNORECASE)
                    for match in pattern.finditer(content):
                        key, value = match.groups()
                        metadata['original_colors'][key] = value.strip()
                except:
                    pass
            
            # Store original media file sizes as baseline
            for root, dirs, files in os.walk(self.extracted_dir):
                for file in files:
                    ext = Path(file).suffix.lower()
                    if ext in {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.mp4', '.webm', '.mkv', '.avi', '.mov', '.m4v', '.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac'}:
                        file_path = os.path.join(root, file)
                        try:
                            file_size = os.path.getsize(file_path)
                            rel_path = os.path.relpath(file_path, self.extracted_dir)
                            metadata['media_files'][rel_path] = {'size': file_size}
                        except:
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
                except:
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
                        except:
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
    success = theme_manager.init()
    
    if success:
        return jsonify({
            'success': True,
            'launcher': theme_manager.launcher_info
        })
    else:
        return jsonify({
            'success': False,
            'error': 'RSI Launcher not found'
        }), 404

@app.route('/api/detect-launcher', methods=['GET', 'POST'])
def api_detect_launcher():
    """Alias for /api/init"""
    return api_init()

@app.route('/api/extract', methods=['POST'])
def api_extract():
    """Extract app.asar."""
    try:
        if not theme_manager.launcher_info:
            return jsonify({'success': False, 'error': 'Launcher not initialized'}), 400
        
        # Create backup
        if not theme_manager.create_backup():
            return jsonify({'success': False, 'error': 'Failed to create backup'}), 500
        
        # Extract
        if not theme_manager.extract_asar():
            return jsonify({
                'success': False,
                'error': 'Failed to extract app.asar',
                'details': theme_manager.status.get('lastError')
            }), 500
        
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
        if not base.exists():
            return jsonify({'success': True, 'extracts': []})
        
        extracts = sorted(
            [p for p in base.iterdir() if p.is_dir() and p.name.startswith('app-extracted-')],
            key=lambda p: p.name,
            reverse=True
        )
        return jsonify({
            'success': True,
            'extracts': [
                {
                    'name': p.name,
                    'path': str(p),
                    'date': p.name.replace('app-extracted-', '')
                } for p in extracts
            ]
        })
    except Exception as e:
        print(f'[API Error] Failed to list extracts: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/use-extract', methods=['POST'])
def api_use_extract():
    """Set an existing extracted folder as active."""
    data = request.json or {}
    selected_path = data.get('path', '').strip()
    if not selected_path:
        return jsonify({'success': False, 'error': 'Missing path'}), 400

    path = Path(selected_path)
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
        'status': theme_manager.status
    })

@app.route('/api/apply-colors', methods=['POST'])
def api_apply_colors():
    """Apply color replacements."""
    data = request.json
    color_mappings = data.get('colors', {})
    
    count = theme_manager.apply_colors(color_mappings)
    
    return jsonify({
        'success': True,
        'filesModified': count
    })

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

    base = Path(theme_manager.extracted_dir).resolve()
    target = (base / target_path).resolve()

    if not str(target).startswith(str(base)):
        return jsonify({'success': False, 'error': 'Invalid target path'}), 403

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        upload.save(str(target))
        return jsonify({'success': True, 'message': 'File replaced', 'targetPath': target_path})
    except Exception as e:
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
        static_js_dir = base / 'static' / 'js'
        
        if not static_js_dir.exists():
            return jsonify({'success': False, 'error': 'static/js directory not found'}), 404

        # Find main.*.js file
        main_js_files = list(static_js_dir.glob('main.*.js'))
        if not main_js_files:
            return jsonify({'success': False, 'error': 'main.*.js file not found'}), 404

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
    if not theme_manager.extracted_dir or not theme_manager.launcher_info:
        return jsonify({'success': False, 'error': 'Nothing extracted yet'}), 400
    
    try:
        # Create temp asar
        with tempfile.NamedTemporaryFile(suffix='.asar', delete=False) as tmp:
            temp_asar = tmp.name
        
        # Pack the extracted dir to temp location
        result = subprocess.run(
            f'npx asar pack "{theme_manager.extracted_dir}" "{temp_asar}"',
            capture_output=True,
            text=True,
            check=False,
            shell=True
        )
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'error': f'Failed to pack asar: {result.stderr}'
            }), 500
        
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
            except:
                pass
            return jsonify({
                'success': False,
                'error': 'Permission denied: Unable to access launcher in Program Files. Try running this application as Administrator.'
            }), 403
        except Exception as e:
            try:
                os.remove(temp_asar)
            except:
                pass
            return jsonify({
                'success': False,
                'error': f'Failed to replace app.asar: {str(e)}'
            }), 500
        
        try:
            # Launch and wait for user to close it
            launcher_process = subprocess.Popen(launcher_exe)
            
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
                    except:
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
                    os.remove(backup_asar)
            except:
                pass
            raise e
    
    except Exception as e:
        print(f'[API Error] Test launcher failed: {str(e)}')
        import traceback
        traceback.print_exc()
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
                    except:
                        pass
    except:
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

@app.route('/api/backups', methods=['GET'])
def api_backups():
    """List backups."""
    backup_dir = os.path.expanduser('~/Documents/RSI-Launcher-Theme-Creator')
    backups = []
    
    try:
        for item in os.listdir(backup_dir):
            if item.startswith('backup-'):
                path = os.path.join(backup_dir, item)
                if os.path.isdir(path):
                    backups.append({
                        'name': item,
                        'path': path,
                        'date': item.replace('backup-', '')
                    })
    except:
        pass
    
    return jsonify({
        'success': True,
        'backups': sorted(backups, key=lambda x: x['date'], reverse=True)
    })

@app.route('/api/restore', methods=['POST'])
def api_restore():
    """Restore from backup."""
    data = request.json
    backup_name = data.get('backup')
    
    if not backup_name or not theme_manager.launcher_info:
        return jsonify({'success': False, 'error': 'Invalid backup or launcher'}), 400
    
    try:
        backup_path = os.path.expanduser(f'~/Documents/RSI-Launcher-Theme-Creator/{backup_name}/app.asar')
        target_path = theme_manager.launcher_info['asarPath']
        
        if not os.path.exists(backup_path):
            return jsonify({'success': False, 'error': 'Backup not found'}), 404
        
        # Copy backup to target
        shutil.copy2(backup_path, target_path)
        
        return jsonify({
            'success': True,
            'message': 'Launcher restored from backup'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Catch-all route for static files (must be AFTER all API routes)
@app.route('/<path:path>')
def serve_static(path):
    """Serve static files from public directory."""
    return send_from_directory('public', path)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
