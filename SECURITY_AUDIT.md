# Security Vulnerability Audit Report

**Date:** February 1, 2026  
**Application:** RUIE (RSI UI Editor)  
**Type:** Security Analysis

---

## Executive Summary

The RUIE application has **several moderate to high-severity security vulnerabilities** that should be addressed before production use. The primary concerns are:

1. **Path Traversal Vulnerabilities** - Critical
2. **Missing Input Validation** - High
3. **Unrestricted File Operations** - High
4. **Command Injection Risks** - Medium
5. **Privilege Escalation** - Medium

---

## Detailed Findings

### 1. **Path Traversal Vulnerability** ⚠️ CRITICAL

**Location:** [server.py](server.py#L1046-L1055) in `/api/upload-media` endpoint

**Issue:**
```python
@app.route('/api/upload-media', methods=['POST'])
def api_upload_media():
    target_path = request.form.get('targetPath', '').strip()
    base = Path(theme_manager.extracted_dir).resolve()
    target = (base / target_path).resolve()
    if not str(target).startswith(str(base)):
        return jsonify({'success': False, 'error': 'Invalid target path'}), 403
```

**Problem:** Although there's path validation, the check can be bypassed with symlinks or race conditions. A malicious user could potentially write files outside the intended directory.

**Severity:** CRITICAL

**Recommendation:**
```python
# Better approach - only allow specific subdirectories
ALLOWED_DIRS = {'assets', 'app/assets', 'static', 'public'}

def is_safe_path(target, base, allowed_dirs):
    rel_path = target.relative_to(base)
    for allowed in allowed_dirs:
        if str(rel_path).startswith(allowed):
            return True
    return False

# Use whitelist approach instead of blacklist
if not is_safe_path(target, base, ALLOWED_DIRS):
    return jsonify({'success': False, 'error': 'Invalid target path'}), 403
```

---

### 2. **Missing Input Validation on File Paths** ⚠️ HIGH

**Locations:** Multiple API endpoints
- [/api/delete-extract](server.py#L939-L990)
- [/api/use-extract](server.py#L905-L927)

**Issue:**
```python
@app.route('/api/delete-extract', methods=['POST'])
def api_delete_extract():
    path_str = data.get('path', '').strip()
    path = Path(path_str)
    # No validation that path_str is actually in DOCS_DIR
    shutil.rmtree(str(path))
```

**Problem:** User can provide ANY path from the request, potentially deleting arbitrary directories on the system.

**Severity:** HIGH

**Recommendation:**
```python
@app.route('/api/delete-extract', methods=['POST'])
def api_delete_extract():
    path_str = data.get('path', '').strip()
    if not path_str:
        return jsonify({'success': False, 'error': 'Missing path'}), 400
    
    path = Path(path_str).resolve()
    base = Path(DOCS_DIR).resolve()
    
    # Verify path is within DOCS_DIR
    try:
        path.relative_to(base)
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid path'}), 403
    
    # Verify it's actually an extracted folder
    if not path.name.startswith('app-extracted-') and not path.name.startswith('app-decompiled-'):
        return jsonify({'success': False, 'error': 'Invalid folder'}), 403
    
    shutil.rmtree(str(path))
```

---

### 3. **Subprocess Command Injection Risk** ⚠️ MEDIUM

**Location:** [server.py](server.py#L127-L134) in `extract_asar()` and multiple other subprocess calls

**Issue:**
```python
result = subprocess.run(
    ['npx', 'asar', 'pack', self.extracted_dir, asar_path],
    capture_output=True,
    text=True,
    check=False
)
```

**Problem:** While using a list (good!) prevents shell injection, paths from `self.extracted_dir` are not validated. If extracted_dir can be controlled by user input, this could be exploited.

**Severity:** MEDIUM

**Recommendation:**
```python
# Validate extracted_dir before using in subprocess
extracted_path = Path(self.extracted_dir).resolve()
base = Path(DOCS_DIR).resolve()

try:
    extracted_path.relative_to(base)
except ValueError:
    raise ValueError(f'Invalid extracted path: {self.extracted_dir}')

# Now safe to use
result = subprocess.run(
    ['npx', 'asar', 'pack', str(extracted_path), asar_path],
    capture_output=True,
    text=True,
    check=False
)
```

---

### 4. **Unvalidated JSON Input** ⚠️ MEDIUM

**Location:** [server.py](server.py#L1008-L1038) in `/api/apply-colors`

**Issue:**
```python
@app.route('/api/apply-colors', methods=['POST'])
def api_apply_colors():
    data = request.json
    color_mappings = data.get('colors', {})
    # No validation that color_mappings contains safe data
    theme_manager.apply_colors_async(color_mappings)
```

**Problem:** Color mappings from client are applied directly without validation. Could contain malicious patterns.

**Severity:** MEDIUM

**Recommendation:**
```python
def validate_color_mapping(color_mappings):
    """Validate color mappings are safe."""
    if not isinstance(color_mappings, dict):
        raise ValueError('Color mappings must be a dictionary')
    
    for key, value in color_mappings.items():
        # Validate key is a reasonable color value
        if not isinstance(key, str) or len(key) > 100:
            raise ValueError(f'Invalid color key: {key}')
        # Validate value is a hex color or similar
        if not isinstance(value, str) or len(value) > 100:
            raise ValueError(f'Invalid color value: {value}')
        # Add regex check for valid hex colors
        if not re.match(r'^#[0-9a-fA-F]{6}$', value):
            raise ValueError(f'Invalid color format: {value}')
    
    return color_mappings

@app.route('/api/apply-colors', methods=['POST'])
def api_apply_colors():
    try:
        data = request.json
        color_mappings = validate_color_mapping(data.get('colors', {}))
        # ... rest of code
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
```

---

### 5. **Missing CORS Validation** ⚠️ MEDIUM

**Location:** [server.py](server.py#L35-L42)

**Issue:**
```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:*", "http://127.0.0.1:*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})
```

**Problem:** The wildcard port matching (`localhost:*`) could allow requests from any local port. Also, no credentials validation.

**Severity:** MEDIUM

**Recommendation:**
```python
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
```

---

### 6. **Insufficient File Type Validation** ⚠️ MEDIUM

**Location:** [server.py](server.py#L1046-L1055) in `/api/upload-media`

**Issue:**
```python
def api_upload_media():
    upload = request.files.get('file')
    target_path = request.form.get('targetPath', '').strip()
    # No validation of file type or size beyond the general MAX_CONTENT_LENGTH
```

**Problem:** No specific validation of uploaded file extensions or MIME types for media uploads.

**Severity:** MEDIUM

**Recommendation:**
```python
ALLOWED_MEDIA_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg',
    'mp4', 'webm', 'mkv', 'avi', 'mov', 'm4v',
    'mp3', 'wav', 'flac', 'ogg', 'm4a', 'aac'
}

MAX_FILE_SIZES = {
    'images': 50 * 1024 * 1024,  # 50MB
    'videos': 500 * 1024 * 1024,  # 500MB
    'audio': 100 * 1024 * 1024    # 100MB
}

def api_upload_media():
    upload = request.files.get('file')
    target_path = request.form.get('targetPath', '').strip()
    
    if not upload or not target_path:
        return jsonify({'success': False, 'error': 'Missing file or target path'}), 400
    
    # Validate file extension
    filename = upload.filename.lower()
    ext = filename.rsplit('.', 1)[1] if '.' in filename else ''
    
    if ext not in ALLOWED_MEDIA_EXTENSIONS:
        return jsonify({'success': False, 'error': f'File type not allowed: {ext}'}), 400
    
    # Validate file size
    upload.seek(0, 2)  # Seek to end
    file_size = upload.tell()
    upload.seek(0)  # Reset to beginning
    
    if file_size > MAX_CONTENT_LENGTH:
        return jsonify({'success': False, 'error': 'File too large'}), 400
    
    # ... rest of code
```

---

### 7. **Privilege Escalation Risk** ⚠️ MEDIUM

**Location:** [launcher.py](launcher.py#L42-L54)

**Issue:**
```python
def request_admin():
    """Request admin privileges if not already elevated."""
    is_admin_now = is_admin()
    if not is_admin_now:
        logger.info("Requesting administrator privileges...")
        try:
            ctypes.windll.shell.ShellExecuteW(None, "runas", script, "", None, 0)
```

**Problem:** The application requests admin privileges automatically without explicit user consent dialog. While it does use Windows' standard UAC prompt, there's no clear documentation of why admin access is needed.

**Severity:** MEDIUM

**Recommendation:**
```python
def request_admin():
    """Request admin privileges with explicit explanation."""
    if is_admin():
        return True
    
    logger.info("Admin privileges required to modify launcher files")
    # The UAC prompt will appear - this is the Windows standard security mechanism
    try:
        ctypes.windll.shell.ShellExecuteW(
            None, 
            "runas", 
            sys.executable, 
            " ".join(sys.argv), 
            None, 
            1  # SW_SHOW
        )
        return True
    except Exception as e:
        logger.error(f"Failed to elevate privileges: {e}")
        return False
```

---

### 8. **Information Disclosure - Debug Logs** ⚠️ LOW

**Location:** [launcher.py](launcher.py#L16-L22)

**Issue:**
```python
log_file = os.path.join(os.path.expanduser('~'), 'Documents', 'RUIE-debug.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)
```

**Problem:** Debug logs may contain sensitive information about file paths, user actions, and system configuration.

**Severity:** LOW

**Recommendation:**
```python
# Set different log level for production builds
if is_frozen():  # Production build
    log_level = logging.INFO
else:  # Development
    log_level = logging.DEBUG

logging.basicConfig(
    level=log_level,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a'),  # Use append, not overwrite
        logging.StreamHandler(sys.stdout)
    ]
)

# Rotate logs
from logging.handlers import RotatingFileHandler
handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=3)
```

---

### 9. **Symlink Following** ⚠️ MEDIUM

**Location:** [server.py](server.py#L107-L119) - `extract_asar()`

**Issue:**
```python
extracted_path = os.path.normpath(os.path.join(docs_dir, f'app-decompiled-{timestamp}'))
# Later...
shutil.copytree(unpacked_dir, dest_unpacked)
```

**Problem:** `shutil.copytree` and file operations don't check for symlinks, which could allow directory traversal through symlink attacks.

**Severity:** MEDIUM

**Recommendation:**
```python
def safe_copytree(src, dst, symlinks=False):
    """Copy tree safely without following symlinks."""
    for item in os.listdir(src):
        src_item = os.path.join(src, item)
        dst_item = os.path.join(dst, item)
        
        if os.path.islink(src_item):
            # Skip symlinks
            logger.warning(f'Skipping symlink: {src_item}')
            continue
        elif os.path.isdir(src_item):
            os.makedirs(dst_item, exist_ok=True)
            safe_copytree(src_item, dst_item)
        else:
            shutil.copy2(src_item, dst_item)

# Use in code:
safe_copytree(unpacked_dir, dest_unpacked)
```

---

### 10. **No Rate Limiting** ⚠️ LOW

**Location:** All API endpoints

**Issue:** No rate limiting on API endpoints, which could allow abuse through repeated requests.

**Severity:** LOW

**Recommendation:**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Apply to specific endpoints
@app.route('/api/upload-media', methods=['POST'])
@limiter.limit("10 per minute")
def api_upload_media():
    # ...
```

---

## Summary Table

| # | Issue | Severity | Location | Impact |
|---|-------|----------|----------|--------|
| 1 | Path Traversal | CRITICAL | `/api/upload-media` | Arbitrary file write |
| 2 | Missing Path Validation | HIGH | `/api/delete-extract`, `/api/use-extract` | Arbitrary file deletion |
| 3 | Subprocess Injection | MEDIUM | `extract_asar()`, multiple endpoints | Command execution |
| 4 | Unvalidated JSON Input | MEDIUM | `/api/apply-colors` | Injection attacks |
| 5 | CORS Wildcard Port | MEDIUM | CORS Configuration | Unauthorized access |
| 6 | No File Type Validation | MEDIUM | `/api/upload-media` | Malicious file upload |
| 7 | Privilege Escalation | MEDIUM | `request_admin()` | System compromise |
| 8 | Debug Log Exposure | LOW | `launcher.py` | Information disclosure |
| 9 | Symlink Following | MEDIUM | `extract_asar()`, file ops | Directory traversal |
| 10 | No Rate Limiting | LOW | All endpoints | DoS potential |

---

## Recommendations (Priority Order)

### Immediate (CRITICAL)
1. ✅ Fix path traversal in `/api/upload-media` with whitelist validation
2. ✅ Add path validation to `/api/delete-extract` and `/api/use-extract`

### High Priority
3. Validate all file paths against DOCS_DIR before operations
4. Add file type and size validation to upload endpoints
5. Implement proper CORS configuration with specific ports

### Medium Priority
6. Add input validation for color mappings and JSON data
7. Implement safe file operations that check for symlinks
8. Fix subprocess calls with path validation
9. Add rate limiting to API endpoints

### Low Priority
10. Adjust log levels based on build type
11. Implement log rotation
12. Add documentation about privilege requirements

---

## Testing Recommendations

1. **Fuzzing Tests** - Test API endpoints with malicious paths and invalid JSON
2. **Path Traversal Tests** - Try uploading files to parent directories
3. **Symlink Tests** - Create symlinks in DOCS_DIR and test operations
4. **Permission Tests** - Run without admin and verify error handling
5. **Integration Tests** - Test entire workflow with validation in place

---

## Compliance Notes

- ✅ Uses HTTPS-compatible patterns (local app)
- ✅ Implements basic CORS
- ⚠️ Missing comprehensive input validation
- ⚠️ Insufficient logging for security events
- ❌ No authentication/authorization (not applicable for local app)

---

**Report Generated:** 2026-02-01  
**Recommendation:** Address CRITICAL and HIGH priority items before public release.
