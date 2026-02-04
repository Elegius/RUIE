// CRITICAL: app.js has loaded
console.log('[app.js] FILE LOADED - ready to execute');

/**
 * RUIE Main Application JavaScript
 * ================================
 * 
 * This is the main client-side JavaScript for the RUIE web application.
 * 
 * Architecture:
 * - Single-page application (SPA) with 6 steps
 * - Communicates with Flask backend via REST API
 * - Uses HTML5 FileReader API for file handling
 * - iFrame-based live preview system
 * - State management for form data
 * 
 * The 6 Steps:
 * 1. Launcher Detection & ASAR Selection
 * 2. Color Customization (17 presets + manual colors)
 * 3. Media Replacement (images, videos, audio)
 * 4. Music / Audio Management
 * 5. Backup & Recovery
 * 6. Review & Deploy
 * 
 * Key Features:
 * - Live preview of theme changes
 * - Color format conversion (hex/RGB)
 * - Media file validation
 * - Backup/restore functionality
 * - Multi-format color support
 */

// Initialize early to check if script is loading
console.log('[app.js] Script loaded at', new Date().toISOString());

/**
 * Send debug logs to the backend server
 * 
 * Useful for tracking user actions and debugging client-side issues
 * on the server side. Logs are stored in ~/Documents/RUIE-debug.log
 * 
 * @param {string} message - Log message to send
 * @param {string} level - Log level: 'INFO', 'ERROR', 'WARNING', 'DEBUG'
 */
function sendDebugToServer(message, level = 'INFO') {
    try {
        fetch('/api/debug-log', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, level })
        }).catch(err => console.error('[sendDebugToServer] fetch error:', err));
    } catch (err) {
        console.error('[sendDebugToServer] error:', err);
    }
}

// Send initial load message to server
sendDebugToServer('app.js loaded successfully');

/**
 * Global error handler for uncaught exceptions
 * 
 * Logs errors to server debug console and browser console
 * All debug output goes to the separate debug console window
 */
window.addEventListener('error', function(event) {
    console.error('[GLOBAL ERROR]', event.filename, event.lineno, event.message);
    sendDebugToServer(`ERROR at ${event.filename}:${event.lineno} - ${event.message}`, 'ERROR');
});

/**
 * Global handler for unhandled promise rejections
 * 
 * Catches promises that reject without a .catch() handler
 * and logs them to server debug console
 */
window.addEventListener('unhandledrejection', function(event) {
    console.error('[UNHANDLED REJECTION]', event.reason);
    sendDebugToServer(`UNHANDLED REJECTION: ${event.reason?.message || String(event.reason)}`, 'ERROR');
});

/**
 * Global application state object
 * 
 * Stores all form data, selections, and configuration
 * that persists across page navigations
 */
const state = {
    // Extraction and initialization state
    initialized: false,       // Whether ASAR has been extracted
    extracted: false,         // Whether extract directory is available
    
    // Color customization
    colors: {},               // Current color selections (will be populated from presets)
    
    // Media files
    media: {},                // User-selected media files
    music: [],                // Array of music files: [{ name: 'track1.ogg', file: File }, ...]
    
    // Current configuration
    config: {
        name: 'My Theme',     // Theme name
        colors: {},           // Color overrides
        media: {},            // Media selections
        music: []             // Music files
    },
    
    // Navigation state
    currentPage: 1,           // Current step (1-6)
    selectedExtractPath: null // Track selected extraction for "Use Selected" button
};

// ============================================================================
// REAL-TIME LIST POLLING
// ============================================================================
let backupsPollTimer = null;
let extractsPollTimer = null;
let backupsPollInFlight = false;
let extractsPollInFlight = false;

function stopListPolling() {
    if (backupsPollTimer) {
        clearInterval(backupsPollTimer);
        backupsPollTimer = null;
    }
    if (extractsPollTimer) {
        clearInterval(extractsPollTimer);
        extractsPollTimer = null;
    }
}

function startListPolling(intervalMs = 5000) {
    stopListPolling();

    backupsPollTimer = setInterval(async () => {
        if (backupsPollInFlight) return;
        backupsPollInFlight = true;
        try {
            await loadBackupsList();
        } catch (e) {
            console.warn('[poll] Error refreshing backups list:', e);
        } finally {
            backupsPollInFlight = false;
        }
    }, intervalMs);

    extractsPollTimer = setInterval(async () => {
        if (extractsPollInFlight) return;
        extractsPollInFlight = true;
        try {
            await loadExtractedASARList();
        } catch (e) {
            console.warn('[poll] Error refreshing extracts list:', e);
        } finally {
            extractsPollInFlight = false;
        }
    }, intervalMs);
}

/**
 * Persisted preview state
 * 
 * This state syncs between all preview iframes so they all show
 * the same theme even when the user navigates between steps
 */
const previewState = {
    colors: {},  // Current color settings
    media: {}    // Current media settings
};

/**
 * DOM element cache for performance
 * 
 * Instead of repeatedly querying the DOM, we cache references to
 * frequently accessed elements. This is initialized by calling DOM.init()
 * once the page is ready.
 */
const DOM = {
    // Page navigation
    pages: null,
    stepperSteps: null,
    
    // Preview iframes
    previewFrame: null,
    previewFrames: null,
    
    // Step 1 - Launcher/ASAR selection
    asarPath: null,
    extractProgress: null,
    extractProgressBar: null,
    extractProgressText: null,
    extractBtn: null,
    extractStatus: null,
    extractSelect: null,
    initStatus: null,
    
    // Step 2 - Colors
    colorList: null,
    
    // Step 4 - Music
    musicList: null,
    
    // Step 3 - Media
    mediaAssetPicker: null,
    mediaFilter: null,
    
    // Navigation buttons
    backBtn: null,
    nextBtn: null,
    
    /**
     * Initialize DOM element cache
     * 
     * Call this once after the DOM is ready to populate the cache.
     * This reduces repeated DOM queries for better performance.
     */
    init() {
        console.log('[DOM.init] Starting DOM initialization, document.readyState:', document.readyState);
        console.log('[DOM.init] document.body exists:', !!document.body);
        console.log('[DOM.init] asarPath element found:', !!document.getElementById('asarPath'));
        
        // Cache all page and step elements
        this.pages = document.querySelectorAll('.page');
        this.stepperSteps = document.querySelectorAll('.stepper-step');
        
        // Cache preview iframes
        this.previewFrame = document.getElementById('previewFrame');
        this.previewFrames = document.querySelectorAll('.preview-frame');
        
        // Cache step-specific elements
        this.asarPath = document.getElementById('asarPath');
        this.extractProgress = document.getElementById('extract-progress');
        this.extractProgressBar = document.getElementById('extract-progress-bar');
        this.extractProgressText = document.getElementById('extract-progress-text');
        this.extractBtn = document.getElementById('extract-btn');
        this.extractStatus = document.getElementById('extract-status');
        this.extractSelect = document.getElementById('extractSelect');
        this.initStatus = document.getElementById('init-status');
        this.colorList = document.getElementById('colorList');
        this.backBtn = document.getElementById('backBtn');
        this.nextBtn = document.getElementById('nextBtn');
        this.musicList = document.getElementById('musicList');
        this.mediaAssetPicker = document.getElementById('mediaAssetPicker');
        this.mediaFilter = document.getElementById('mediaFilter');

        console.log('[DOM.init] DOM elements cached - asarPath:', !!this.asarPath, 'initStatus:', !!this.initStatus);

        // Setup preview frame sync: when any preview iframe loads, send current state to it
        this.previewFrames.forEach((frame) => {
            frame.addEventListener('load', () => {
                sendPreviewStateToFrame(frame);
            });
        });
    }
};

/**
 * Debounce helper for performance optimization
 * 
 * Delays function execution until the user stops performing an action,
 * reducing the number of times the function is called. Useful for
 * expensive operations like preview updates while the user types.
 * 
 * @param {Function} func - Function to debounce
 * @param {number} wait - Milliseconds to wait before executing
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Debounce preview updates to reduce reflows during rapid input
const debouncedUpdatePreview = debounce(updatePreviewFromUi, 150);

/**
 * Navigate to a specific step in the wizard
 * 
 * Handles:
 * - Showing/hiding pages
 * - Updating stepper UI
 * - Loading step-specific data
 * - Syncing preview state
 * 
 * @param {number} pageNumber - Step number (1-6)
 */
function navigateToPage(pageNumber) {
    // Hide all pages using cached elements
    DOM.pages.forEach(page => page.style.display = 'none');
    
    // Show requested page
    const targetPage = document.getElementById(`step-${pageNumber}`);
    if (targetPage) {
        targetPage.style.display = 'block';
        state.currentPage = pageNumber;
        updateStepperUI(pageNumber);
        updateNavigationButtons(pageNumber);

        // Sync preview state to the active iframe on step change
        sendPreviewStateToFrame(getActivePreviewFrame());
        
        // Load data specific to each step
        if (pageNumber === 1) {
            // Step 1: Load list of extracted ASAR files and backups
            setTimeout(() => {
                console.log('[navigateToPage] Loading ASAR and Backup lists for page 1');
                loadExtractedASARList().catch(e => console.error('Error loading extracts on page 1:', e));
                loadBackupsList().catch(e => console.error('Error loading backups on page 1:', e));
            }, 100);
        }
        
        if (pageNumber === 2) {
            // Step 2: Render color selection interface
            if (DOM.colorList) {
                DOM.colorList.innerHTML = '<div style="padding: 20px; text-align: center; color: #888;">Loading color palette...</div>';
            }
            setTimeout(() => {
                renderColorMappings();
                // Update preview with current colors from UI
                const colors = collectColorMappings();
                if (Object.keys(colors).length > 0) {
                    updatePreviewFromColors(colors);
                }
            }, 50);
        }
        
        if (pageNumber === 3) {
            // Step 3: Load media assets (images, videos, audio)
            if (lastMediaAssets.length === 0) {
                loadDefaultMediaAssets();
            }
            // Colors already synced via sendPreviewStateToFrame at top of function
        }
        
        if (pageNumber === 4) {
            // Step 4: Initialize music playlist
            if (state.music.length === 0) {
                loadDefaultMusic();
            } else {
                renderMusicList();
            }
            // Resend current colors to preview
            if (state.colors && Object.keys(state.colors).length > 0) {
                updatePreviewFromColors(state.colors);
            }
        }
    }
}

function updateStepperUI(currentStep) {
    // Use cached stepper steps
    DOM.stepperSteps.forEach(step => {
        step.classList.remove('active', 'completed');
    });
    
    // Mark current and completed steps (for steps 1-6)
    for (let i = 1; i <= 6; i++) {
        const stepElement = document.getElementById(`stepper-${i}`);
        if (stepElement) {
            if (i < currentStep) {
                stepElement.classList.add('completed');
            } else if (i === currentStep) {
                stepElement.classList.add('active');
            }
        }
    }
}

function updateNavigationButtons(currentPage) {
    if (!DOM.backBtn || !DOM.nextBtn) return;
    
    // Show/hide back button
    DOM.backBtn.style.display = currentPage > 1 ? 'block' : 'none';
    
    // Show/hide next button
    DOM.nextBtn.style.display = currentPage < 5 ? 'block' : 'none';
}

const previewDefaults = {
    primary: '#54adf7',
    accent: '#6db9f8',
    background: '#0a1d29',
    surface: '#112534',
    text: '#e0e0e0',
    muted: '#9fb1bf'
};

function normalizeColorToHex(value) {
    if (!value) return null;
    const trimmed = value.trim();

    if (trimmed.startsWith('#')) {
        return trimmed.length === 4
            ? `#${trimmed[1]}${trimmed[1]}${trimmed[2]}${trimmed[2]}${trimmed[3]}${trimmed[3]}`
            : trimmed;
    }

    const rgbMatch = trimmed.match(/^(\d{1,3})\s*[ ,]\s*(\d{1,3})\s*[ ,]\s*(\d{1,3})$/) ||
        trimmed.match(/^rgb\((\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\)$/i);

    if (!rgbMatch) return null;

    const [r, g, b] = rgbMatch.slice(1).map((v) => Math.min(255, Math.max(0, Number(v))));
    return `#${[r, g, b].map((v) => v.toString(16).padStart(2, '0')).join('')}`;
}

function buildPreviewPalette(colors) {
    const values = Object.values(colors || {});
    const parsed = values.map(normalizeColorToHex).filter(Boolean);

    return {
        primary: parsed[0] || previewDefaults.primary,
        accent: parsed[1] || parsed[0] || previewDefaults.accent,
        background: previewDefaults.background,
        surface: previewDefaults.surface,
        text: previewDefaults.text,
        muted: previewDefaults.muted
    };
}

function getActivePreviewFrame() {
    const pages = document.querySelectorAll('.page');
    for (let i = 0; i < pages.length; i++) {
        const page = pages[i];
        if (page.style.display !== 'none') {
            const frame = page.querySelector('.preview-frame');
            if (frame) return frame;
        }
    }

    return document.querySelector('.preview-frame');
}

function sendPreviewStateToFrame(frame) {
    if (!frame || !frame.contentWindow) return;
    frame.contentWindow.postMessage({ type: 'preview-colors', colors: previewState.colors || {} }, '*');
    frame.contentWindow.postMessage({ type: 'preview-media', media: previewState.media || {} }, '*');
}

function updatePreviewFromColors(colors) {
    previewState.colors = colors || {};
    const frame = getActivePreviewFrame();
    sendPreviewStateToFrame(frame);
}

function updatePreviewMedia(media) {
    previewState.media = { ...previewState.media, ...(media || {}) };
    const frame = getActivePreviewFrame();
    sendPreviewStateToFrame(frame);
}

// Debounced version for frequent updates
const updatePreviewFromUiDebounced = debounce(function() {
    updatePreviewFromColors(collectColorMappings());
}, 100);

function updatePreviewFromUi() {
    updatePreviewFromUiDebounced();
}

function parseHexToRgb(hex) {
    if (!hex) return null;
    const normalized = normalizeColorToHex(hex);
    if (!normalized) return null;

    const clean = normalized.replace('#', '');
    const r = parseInt(clean.slice(0, 2), 16);
    const g = parseInt(clean.slice(2, 4), 16);
    const b = parseInt(clean.slice(4, 6), 16);

    return { r, g, b, hex: normalized };
}

function setColorControls(item, hex) {
    const parsed = parseHexToRgb(hex) || { r: 136, g: 136, b: 136, hex: '#888888' };
    
    // Batch DOM queries
    const wheelHidden = item.querySelector('.color-wheel-hidden');
    const newInput = item.querySelector('.new-color');
    const preview = item.querySelector('.color-preview');
    const hexInput = item.querySelector('.hex-input');
    const rgbInput = item.querySelector('.rgb-input');

    // Batch DOM updates
    if (wheelHidden) wheelHidden.value = parsed.hex;
    if (newInput) newInput.value = parsed.hex;
    if (preview) preview.style.background = parsed.hex;
    if (hexInput) hexInput.value = parsed.hex;
    if (rgbInput) rgbInput.value = `${parsed.r}, ${parsed.g}, ${parsed.b}`;
}

function attachColorControlListeners(item) {
    const colorWheel = item.querySelector('.color-wheel');
    const hexInput = item.querySelector('.hex-input');
    const rgbR = item.querySelector('.rgb-r');
    const rgbG = item.querySelector('.rgb-g');
    const rgbB = item.querySelector('.rgb-b');
    const newColorHidden = item.querySelector('.new-color');
    const colorPreview = item.querySelector('.color-preview');

    const updateAllFields = (hex) => {
        if (!hex || !hex.startsWith('#')) return;
        
        // Update hex input
        if (hexInput) hexInput.value = hex.toUpperCase();
        
        // Update RGB inputs
        const rgb = hexToRGB(hex);
        if (rgb) {
            const [r, g, b] = rgb.split(',').map(v => parseInt(v.trim()));
            if (rgbR) rgbR.value = r;
            if (rgbG) rgbG.value = g;
            if (rgbB) rgbB.value = b;
        }
        
        // Update color wheel
        if (colorWheel) colorWheel.value = hex;
        
        // Update hidden new color value
        if (newColorHidden) newColorHidden.value = hex;
        
        // Update preview
        if (colorPreview) colorPreview.style.background = hex;
        
        updatePreviewFromUi();
    };

    // Handle color wheel changes
    if (colorWheel) {
        colorWheel.addEventListener('input', (event) => {
            updateAllFields(event.target.value);
        });
    }

    // Handle hex input changes
    if (hexInput) {
        hexInput.addEventListener('input', () => {
            let hex = hexInput.value.trim();
            if (hex && !hex.startsWith('#')) {
                hex = '#' + hex;
                hexInput.value = hex;
            }
            if (hex.length === 7 && /^#[0-9A-Fa-f]{6}$/.test(hex)) {
                updateAllFields(hex.toUpperCase());
            }
        });
    }

    // Handle RGB input changes
    const updateFromRGB = () => {
        const r = parseInt(rgbR?.value || 0);
        const g = parseInt(rgbG?.value || 0);
        const b = parseInt(rgbB?.value || 0);
        
        if (r >= 0 && r <= 255 && g >= 0 && g <= 255 && b >= 0 && b <= 255) {
            const hex = rgbToHex(`${r}, ${g}, ${b}`);
            if (hex) {
                updateAllFields(hex);
            }
        }
    };

    if (rgbR) rgbR.addEventListener('input', updateFromRGB);
    if (rgbG) rgbG.addEventListener('input', updateFromRGB);
    if (rgbB) rgbB.addEventListener('input', updateFromRGB);
}

let colorPresets = {};

const presetFiles = [
    'rsi',
    'aegis-dynamics',
    'anvil-aerospace',
    'origin-jumpworks',
    'drake-interplanetary',
    'crusader-industries',
    'misc',
    'consolidated-outland',
    'banu',
    'esperia',
    'kruger',
    'argo',
    'aopoa',
    'tumbril',
    'greycat',
    'vanduul',
    'gatac',
    'c3rb'
];

async function loadPresetFiles() {
    const loaded = {};

    for (let i = 0; i < presetFiles.length; i++) {
        const presetId = presetFiles[i];
        try {
            const response = await fetch(`/presets/color-mapping-${presetId}.json`);
            if (!response.ok) {
                console.warn(`Preset file not found: ${presetId}`);
                continue;
            }
            const preset = await response.json();
            loaded[presetId] = preset;
        } catch (error) {
            console.warn(`Failed to load preset ${presetId}:`, error);
        }
    }

    // Merge presets with base inheritance and pad with RSI colors
    const rsiColors = loaded.rsi && loaded.rsi.colors ? loaded.rsi.colors : {};

    Object.keys(loaded).forEach((presetId) => {
        const preset = loaded[presetId];
        const baseId = preset.base || (presetId !== 'rsi' ? 'rsi' : null);
        const basePreset = baseId ? loaded[baseId] : null;
        const baseColors = basePreset && basePreset.colors ? basePreset.colors : {};
        const mergedColors = { ...rsiColors, ...baseColors, ...(preset.colors || {}) };

        colorPresets[presetId] = {
            colors: mergedColors,
            media: preset.media || {
                logo: 'assets/logos/cig-logo.svg',
                background: 'assets/images/sc_bg_fallback.jpg'
            }
        };
    });

    if (!colorPresets.rsi && loaded.rsi) {
        colorPresets.rsi = { colors: loaded.rsi.colors || {}, media: loaded.rsi.media || {} };
    }

    // Initialize defaults if available
    if (colorPresets.rsi && colorPresets.rsi.colors) {
        state.colors = { ...colorPresets.rsi.colors };
    }
    if (colorPresets.rsi && colorPresets.rsi.media) {
        state.media = { ...colorPresets.rsi.media };
    }
}

/**
 * Handle file selection from HTML5 file input
 */
function handleAsarFileSelection(event) {
    const file = event.target.files[0];
    if (file) {
        // For browser environment, we display the file name
        // In production with file API backend, this would handle the actual file
        DOM.asarPath.value = file.name;
        
        // Show success indicator
        const pathIndicator = document.getElementById('path-success-indicator');
        if (pathIndicator) pathIndicator.style.display = 'block';
        
        // Clear any previous status messages
        const statusEl = document.getElementById('init-status');
        if (statusEl) {
            statusEl.textContent = '';
            statusEl.style.display = 'none';
        }
        
        // Auto-initialize after path is set
        setTimeout(() => initSession(), 100);
    }
}

/**
 * Open file picker dialog for user to select app.asar file
 */
function browseForAsar() {
    console.log('[browseForAsar] Opening file picker');
    showStatus('init-status', 'Opening file browser...', 'info');
    
    // Use API endpoint for file picker dialog (works better in frozen PyQt5 mode)
    fetch('/api/browse-for-asar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.path) {
            console.log('[browseForAsar] Selected path:', data.path);
            DOM.asarPath.value = data.path;
            
            // Show success indicator
            const pathIndicator = document.getElementById('path-success-indicator');
            if (pathIndicator) {
                pathIndicator.style.display = 'block';
            }
            
            // Auto-initialize after path is selected
            showStatus('init-status', 'Initializing...', 'info');
            setTimeout(() => initSession(), 100);
        } else {
            // User cancelled or no file selected
            console.log('[browseForAsar] No file selected or cancelled');
            showStatus('init-status', 'No file selected', 'warning');
        }
    })
    .catch(error => {
        console.error('[browseForAsar] Error:', error);
        showStatus('init-status', 'Error opening file browser: ' + error.message, 'error');
    });
}

/**
 * Show full path tooltip on hover
 */
function showFullPath(inputElement) {
    const fullPath = inputElement.value;
    if (fullPath) {
        const tooltip = document.getElementById('path-tooltip');
        if (tooltip) {
            tooltip.textContent = fullPath;
            tooltip.style.display = 'block';
        }
    }
}

/**
 * Hide full path tooltip
 */
function hideFullPath(inputElement) {
    const tooltip = document.getElementById('path-tooltip');
    if (tooltip) {
        tooltip.style.display = 'none';
    }
}

/**
 * Open the backups folder in system file explorer
 */
function openBackupsFolder() {
    fetch('/api/open-backups-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showStatus('init-status', '📂 Opening backups folder...', 'info');
            setTimeout(() => {
                const statusEl = document.getElementById('init-status');
                if (statusEl) statusEl.style.display = 'none';
            }, 1500);
        } else {
            showStatus('init-status', 'Error: ' + (data.error || 'Failed to open folder'), 'error');
        }
    })
    .catch(error => {
        console.error('[openBackupsFolder] Error:', error);
        showStatus('init-status', 'Error opening folder: ' + error.message, 'error');
    });
}

/**
 * Open the extractions folder in system file explorer
 */
function openExtractionsFolder() {
    fetch('/api/open-extractions-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showStatus('extract-status', '📂 Opening extractions folder...', 'info');
            setTimeout(() => {
                const statusEl = document.getElementById('extract-status');
                if (statusEl) statusEl.style.display = 'none';
            }, 1500);
        } else {
            showStatus('extract-status', 'Error: ' + (data.error || 'Failed to open folder'), 'error');
        }
    })
    .catch(error => {
        console.error('[openExtractionsFolder] Error:', error);
        showStatus('extract-status', 'Error opening folder: ' + error.message, 'error');
    });
}

/**
 * Auto-detect RSI Launcher installation
 */
async function detectLauncher(options = {}) {
    const { autoInit = false, silentFailure = false } = options;

    try {
        console.log('[detectLauncher] Starting auto-detect...');
        
        // Show loading feedback
        showStatus('init-status', 'Auto-detecting RSI Launcher...', 'info');
        
        console.log('[detectLauncher] Fetching /api/detect-launcher');
        const response = await fetch('/api/detect-launcher');
        const data = await response.json();

        console.log('[detectLauncher] Response:', data);

        if (!response.ok) {
            throw new Error(data.error || data.message || 'Launcher not found');
        }

        if (!data.launcher || !data.launcher.asarPath) {
            throw new Error('Launcher detected but asar path is missing');
        }

        console.log('[detectLauncher] Setting path to:', data.launcher.asarPath);
        
        // Ensure DOM is initialized
        if (!DOM.asarPath) {
            console.warn('[detectLauncher] DOM.asarPath not found, calling DOM.init()');
            DOM.init();
            console.log('[detectLauncher] After DOM.init(), DOM.asarPath:', !!DOM.asarPath);
        }
        
        if (!DOM.asarPath) {
            throw new Error('CRITICAL: asarPath input element not found in DOM');
        }
        
        console.log('[detectLauncher] About to set DOM.asarPath.value');
        DOM.asarPath.value = data.launcher.asarPath;
        console.log('[detectLauncher] Value set to:', DOM.asarPath.value);
        
        // Also set a data attribute so we can verify via HTTP
        DOM.asarPath.setAttribute('data-path-set', 'true');
        console.log('[detectLauncher] data-path-set attribute added');
        
        // Show success indicator next to path field
        const pathIndicator = document.getElementById('path-success-indicator');
        if (pathIndicator) {
            pathIndicator.style.display = 'block';
        }
        
        // Show success message and green indicator
        showStatus('init-status', '✓ Launcher detected', 'success');
        
        // If autoInit is true, initialize session after showing the path
        if (autoInit) {
            console.log('[detectLauncher] Auto-initializing session');
            setTimeout(() => initSession(), 500);
        } else {
            // Hide the status message after a brief moment when not auto-initializing
            setTimeout(() => {
                const statusEl = document.getElementById('init-status');
                if (statusEl) {
                    statusEl.style.display = 'none';
                }
            }, 1500);
        }

    } catch (error) {
        console.error('[detectLauncher] Error:', error.message);
        if (!silentFailure) {
            showStatus('init-status', '✗ Error: ' + error.message, 'error');
        }
        // Hide error message after 3 seconds on silentFailure
        if (silentFailure) {
            setTimeout(() => {
                const statusEl = document.getElementById('init-status');
                if (statusEl) {
                    statusEl.style.display = 'none';
                }
            }, 3000);
        }
    }
}

/**
 * Check if RSI Launcher is currently running
 */
async function checkLauncherRunning() {
    try {
        const response = await fetch('/api/launcher-status');
        const data = await response.json();
        return data.isRunning || false;
    } catch (error) {
        console.error('Error checking launcher status:', error);
        return false;
    }
}

/**
 * Initialize session with asar path
 */
async function initSession() {
    const asarPath = DOM.asarPath.value.trim();
    
    if (!asarPath) {
        showStatus('init-status', 'Please enter asar path', 'error');
        return;
    }

    // Check if RSI Launcher is running
    showStatus('init-status', 'Checking launcher status...', 'info');
    const launcherRunning = await checkLauncherRunning();
    
    if (launcherRunning) {
        showStatus('init-status', '⚠️ RSI Launcher is currently running. Please close it before proceeding, then try again.', 'error');
        return;
    }

    showStatus('init-status', 'Initializing...', 'info');

    try {
        const response = await fetch('/api/init', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ asarPath })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to initialize');
        }

        state.initialized = true;
        
        // Turn initialize button green with success icon
        const initBtn = document.getElementById('init-btn');
        if (initBtn) {
            initBtn.style.background = 'linear-gradient(135deg, rgba(100, 200, 100, 0.3), rgba(80, 180, 80, 0.2))';
            initBtn.style.borderColor = '#64c864';
            initBtn.style.color = '#64c864';
            initBtn.style.boxShadow = '0 0 15px rgba(100, 200, 100, 0.4)';
            initBtn.innerHTML = '✓';
        }
        
        // Hide the initializing status message after a brief moment
        setTimeout(() => {
            const statusEl = document.getElementById('init-status');
            if (statusEl) {
                statusEl.style.display = 'none';
            }
        }, 500);
        
        // Load extracted list but don't auto-navigate
        loadExtractedList();

    } catch (error) {
        showStatus('init-status', error.message, 'error');
    }
}

let extractPollTimer = null;
let lastMediaAssets = [];

function setExtractProgress(visible, percent = 0, message = 'Preparing extraction...') {
    if (!DOM.extractProgress || !DOM.extractProgressBar || !DOM.extractProgressText) return;

    DOM.extractProgress.style.display = visible ? 'block' : 'none';
    DOM.extractProgressBar.style.width = `${Math.max(0, Math.min(100, percent))}%`;
    DOM.extractProgressText.textContent = message;
}

function startExtractPolling() {
    if (extractPollTimer) {
        clearInterval(extractPollTimer);
    }

    extractPollTimer = setInterval(async () => {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            if (!response.ok || !data.success) {
                return;
            }

            const status = data.status || {};

            if (status.operation === 'extract') {
                setExtractProgress(true, status.progress ?? 0, status.message || 'Extracting...');

                if (status.state === 'done') {
                    clearInterval(extractPollTimer);
                    extractPollTimer = null;
                }

                if (status.state === 'error') {
                    clearInterval(extractPollTimer);
                    extractPollTimer = null;
                }
            }
        } catch (error) {
            // Ignore polling errors
        }
    }, 500);
}

/**
 * Extract asar
 */
async function extractAsar() {
    console.log('[extractAsar] CALLED - starting ASAR extraction');
    const extractButton = document.getElementById('extract-btn');
    if (extractButton) {
        extractButton.disabled = true;
        console.log('[extractAsar] Extract button disabled');
    }

    // Hide status, only show progress bar
    const statusEl = document.getElementById('extract-status');
    if (statusEl) statusEl.style.display = 'none';
    
    setExtractProgress(true, 5, '📦 Starting extraction...');
    console.log('[extractAsar] Progress bar shown, starting polling');
    startExtractPolling();

    try {
        console.log('[extractAsar] Sending POST to /api/extract');
        const response = await fetch('/api/extract', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        console.log('[extractAsar] Response received:', response.status);

        let data = {};
        try {
            data = await response.json();
            console.log('[extractAsar] Response parsed:', data);
        } catch (parseError) {
            console.error('[extractAsar] Failed to parse response:', parseError);
            data = { error: 'Server returned an unexpected response.' };
        }

        if (!response.ok) {
            const details = data.details ? ` (${data.details})` : '';
            throw new Error((data.error || 'Failed to extract') + details);
        }

        state.extracted = true;
        setExtractProgress(true, 100, 'Extraction complete');
        showStatus('extract-status', '✓ Extracted successfully', 'success');
        console.log('[extractAsar] Extraction successful, loading list');
        
        // Reload the extracted ASAR list to show the new extraction
        await loadExtractedASARList();
        
        // Navigate to Colors page (page 2)
        setTimeout(() => {
            navigateToPage(2);
            document.getElementById('extract-status').style.display = 'none';
        }, 500);

    } catch (error) {
        console.error('[extractAsar] Error:', error.message);
        const message = error?.message?.includes('Failed to fetch')
            ? 'Failed to fetch. The local server may have stopped. Please restart the app.'
            : error.message;
        showStatus('extract-status', message, 'error');
        setExtractProgress(true, 0, 'Extraction failed');
    } finally {
        if (extractButton) {
            extractButton.disabled = false;
            console.log('[extractAsar] Extract button re-enabled');
        }
    }
}

/**
 * Open the latest extracted folder
 */
async function openLatestExtract() {
    showStatus('extract-status', 'Opening latest extracted folder...', 'info');

    try {
        const response = await fetch('/api/open-latest-extract', {
            method: 'POST'
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to open extracted folder');
        }

        showStatus('extract-status', `✓ Opened: ${data.path}`, 'success');
    } catch (error) {
        showStatus('extract-status', error.message, 'error');
    }
}

/**
 * Load and display extracted ASAR folders
 */
async function loadExtractedAsars() {
    const extractsList = document.getElementById('extractsList');
    if (!extractsList) return;
    
    try {
        const response = await fetch('/api/extracted-list');
        const data = await response.json();
        
        if (!data.success || !data.extracts || data.extracts.length === 0) {
            extractsList.innerHTML = '<div class="extract-item-empty" style="text-align: center; padding: 20px; color: #7a8a9a;">No extracted ASAR folders found. Decompile app.asar to get started.</div>';
            return;
        }
        
        extractsList.innerHTML = '';
        data.extracts.forEach(extract => {
            const item = document.createElement('div');
            item.className = 'extract-item';
            item.style.cssText = 'background: #2a3a4a; border: 1px solid #3a4a5a; border-radius: 4px; padding: 10px; margin-bottom: 8px; cursor: pointer;';
            item.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div style="color: #8db4d0; font-weight: bold; font-size: 0.9em;">${extract.name}</div>
                        <div style="color: #7a8a9a; font-size: 0.85em;">${extract.date}</div>
                    </div>
                    <div style="display: flex; gap: 5px;">
                        <button class="btn btn-small" style="padding: 4px 8px; font-size: 0.75em;" onclick="useExtractFolder('${extract.path}')">Use</button>
                        <button class="btn btn-danger" style="padding: 4px 8px; font-size: 0.75em;" onclick="deleteExtractFolder('${extract.path}')">Delete</button>
                    </div>
                </div>
            `;
            extractsList.appendChild(item);
        });
    } catch (error) {
        console.error('Error loading extracted folders:', error);
        extractsList.innerHTML = '<div class="extract-item-empty" style="color: red;">Error loading extracts</div>';
    }
}

/**
 * Load and display backups
 */
async function loadBackups() {
    const backupsList = document.getElementById('backupsList');
    if (!backupsList) return;
    
    try {
        const response = await fetch('/api/backups-list');
        const data = await response.json();
        
        if (!data.success || !data.backups || data.backups.length === 0) {
            backupsList.innerHTML = '<div class="backup-item-empty" style="text-align: center; padding: 20px; color: #7a8a9a;">No backups found. Click "Create New Backup" to get started.</div>';
            return;
        }
        
        backupsList.innerHTML = '';
        data.backups.forEach(backup => {
            const item = document.createElement('div');
            item.className = 'backup-item';
            item.style.cssText = 'background: #2a3a4a; border: 1px solid #3a4a5a; border-radius: 4px; padding: 10px; margin-bottom: 8px;';
            item.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div style="color: #8db4d0; font-weight: bold; font-size: 0.9em;">${backup.name}</div>
                        <div style="color: #7a8a9a; font-size: 0.85em;">${backup.date}</div>
                        ${backup.asar_exists ? '<div style="color: #7fb3d5; font-size: 0.8em;">✓ Contains app.asar</div>' : '<div style="color: #d07a7a; font-size: 0.8em;">⚠ Missing app.asar</div>'}
                    </div>
                    <div style="display: flex; gap: 5px;">
                        <button class="btn btn-primary" style="padding: 4px 8px; font-size: 0.75em;" onclick="restoreBackup('${backup.path}')">Restore</button>
                        <button class="btn btn-danger" style="padding: 4px 8px; font-size: 0.75em;" onclick="deleteBackup('${backup.path}')">Delete</button>
                    </div>
                </div>
            `;
            backupsList.appendChild(item);
        });
    } catch (error) {
        console.error('Error loading backups:', error);
        backupsList.innerHTML = '<div class="backup-item-empty" style="color: red;">Error loading backups</div>';
    }
}

/**
 * Use an extracted folder
 */
async function useExtractFolder(path) {
    try {
        const response = await fetch('/api/use-extract', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: path })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('extract-status', '✓ Using selected extraction', 'success');
            loadExtractedAsars();
        } else {
            showStatus('extract-status', 'Error: ' + (data.error || 'Failed to use extraction'), 'error');
        }
    } catch (error) {
        showStatus('extract-status', 'Error: ' + error.message, 'error');
    }
}

/**
 * Delete an extracted folder
 */
async function deleteExtractFolder(path) {
    if (!confirm('Are you sure you want to delete this extracted folder? This cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/delete-extract', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: path })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('extract-status', '✓ Extraction deleted', 'success');
            loadExtractedAsars();
        } else {
            showStatus('extract-status', 'Error: ' + (data.error || 'Failed to delete'), 'error');
        }
    } catch (error) {
        showStatus('extract-status', 'Error: ' + error.message, 'error');
    }
}

/**
 * Create a new backup
 */
async function createNewBackup() {
    try {
        const response = await fetch('/api/create-backup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('extract-status', '✓ Backup created successfully', 'success');
            loadBackups();
        } else {
            showStatus('extract-status', 'Error: ' + (data.error || 'Failed to create backup'), 'error');
        }
    } catch (error) {
        showStatus('extract-status', 'Error: ' + error.message, 'error');
    }
}

/**
 * Restore a backup
 */
async function restoreBackup(path) {
    if (!confirm('Are you sure you want to restore this backup? This will overwrite the current app.asar.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/restore-backup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: path })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('extract-status', '✓ Backup restored successfully', 'success');
        } else {
            showStatus('extract-status', 'Error: ' + (data.error || 'Failed to restore backup'), 'error');
        }
    } catch (error) {
        showStatus('extract-status', 'Error: ' + error.message, 'error');
    }
}

/**
 * Delete a backup
 */
async function deleteBackup(path) {
    if (!confirm('Are you sure you want to delete this backup? This cannot be undone.')) {
        return;
    }
    
    // Show progress indicator
    showStatus('init-status', '🗑️ Deleting backup...', 'info');
    
    try {
        const response = await fetch('/api/delete-backup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: path })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('init-status', '✓ Backup deleted successfully', 'success');
            setTimeout(() => {
                const statusEl = document.getElementById('init-status');
                if (statusEl) statusEl.style.display = 'none';
            }, 2000);
            loadBackupsList();
        } else {
            showStatus('init-status', 'Error: ' + (data.error || 'Failed to delete backup'), 'error');
        }
    } catch (error) {
        showStatus('init-status', 'Error: ' + error.message, 'error');
    }
}

/**
 * Load both extracts and backups when initializing
 */
async function loadExtracts() {
    console.log('loadExtracts called');
    await loadExtractedAsars();
    await loadBackups();
}

async function loadExtractedList() {
    const select = document.getElementById('extractSelect');
    if (!select) {
        console.log('extractSelect element not found');
        return;
    }

    try {
        console.log('Fetching /api/extracted-list...');
        const response = await fetch('/api/extracted-list');
        console.log('Response status:', response.status, 'Content-Type:', response.headers.get('Content-Type'));
        
        if (!response.ok) {
            console.error('Response not OK:', response.status, response.statusText);
            const text = await response.text();
            console.error('Response body:', text.substring(0, 200));
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log('Extracted list data:', data);

        const extracts = data.extracts || [];
        select.innerHTML = '';
        
        if (!extracts.length) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No extracted folders found';
            select.appendChild(option);
            console.log('No extracted folders found');
            return;
        }

        const optionDefault = document.createElement('option');
        optionDefault.value = '';
        optionDefault.textContent = 'Select a previous extraction...';
        select.appendChild(optionDefault);

        extracts.forEach((item) => {
            const option = document.createElement('option');
            option.value = item.path;
            option.textContent = `${item.name} (${item.date})`;
            select.appendChild(option);
        });
        
        console.log(`Loaded ${extracts.length} extracted folders`);
    } catch (error) {
        console.error('Error loading extracted list:', error);
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'Error: ' + error.message;
        select.innerHTML = '';
        select.appendChild(option);
    }
}

async function useSelectedExtract() {
    const select = document.getElementById('extractSelect');
    const selected = select?.value || '';

    if (!selected) {
        showStatus('extract-status', 'No extracted folder selected', 'error');
        return;
    }

    showStatus('extract-status', 'Using selected extracted folder...', 'info');

    try {
        const response = await fetch('/api/use-extract', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: selected })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to use extracted folder');
        }

        state.extracted = true;
        
        // Show what changes were made to this extraction
        if (data.changes && (data.changes.colors || data.changes.media)) {
            let changesText = '✓ Using selected extracted folder\n\nDetected changes:\n';
            if (data.changes.colors && Object.keys(data.changes.colors).length > 0) {
                changesText += `\n🎨 ${Object.keys(data.changes.colors).length} color(s) changed`;
            }
            if (data.changes.media && Object.keys(data.changes.media).length > 0) {
                changesText += `\n🎬 ${Object.keys(data.changes.media).length} media file(s) replaced`;
            }
            showStatus('extract-status', changesText, 'success');
        } else {
            showStatus('extract-status', '✓ Using selected extracted folder (no changes detected)', 'success');
        }

        setTimeout(() => {
            navigateToPage(2);
            document.getElementById('extract-status').style.display = 'none';
        }, 500);
    } catch (error) {
        showStatus('extract-status', error.message, 'error');
    }
}

/**
 * Select an extract item and highlight it
 */
function selectExtract(path, element) {
    // Remove previous selection
    const extractsList = document.getElementById('extractsList');
    if (extractsList) {
        const previousSelected = extractsList.querySelector('.extract-item.selected');
        if (previousSelected) {
            previousSelected.classList.remove('selected');
            previousSelected.style.borderColor = '';
            previousSelected.style.background = '';
        }
    }
    
    // Add selection to current item
    state.selectedExtractPath = path;
    element.classList.add('selected');
    element.style.borderColor = 'rgba(0, 212, 255, 0.5)';
    element.style.background = 'rgba(0, 212, 255, 0.1)';
}

/**
 * Use the selected extract from the list
 */
async function useSelectedExtract() {
    if (!state.selectedExtractPath) {
        showStatus('extract-status', 'Please select an extraction first', 'error');
        return;
    }

    await useExtractedASAR(state.selectedExtractPath);
}

/**
 * Load and display backups list
 */
async function loadBackupsList() {
    const backupsList = document.getElementById('backupsList');
    if (!backupsList) return;

    try {
        const response = await fetch('/api/backups');
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to load backups');
        }

        const backups = data.backups || [];

        if (backups.length === 0) {
            backupsList.innerHTML = '<div class="backup-item-empty">No backups yet. Create one to get started.</div>';
            return;
        }

        backupsList.innerHTML = '';
        backups.forEach((backup) => {
            const backupDiv = document.createElement('div');
            backupDiv.className = 'backup-item';
            
            const infoDiv = document.createElement('div');
            infoDiv.className = 'backup-item-info';
            
            const nameDiv = document.createElement('div');
            nameDiv.className = 'backup-item-name';
            nameDiv.textContent = backup.name || 'Backup';
            
            const dateDiv = document.createElement('div');
            dateDiv.className = 'backup-item-date';
            dateDiv.textContent = new Date(backup.date).toLocaleString();
            
            infoDiv.appendChild(nameDiv);
            infoDiv.appendChild(dateDiv);
            
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'backup-item-actions';
            
            const restoreBtn = document.createElement('button');
            restoreBtn.className = 'btn btn-secondary';
            restoreBtn.textContent = '↻ Restore';
            restoreBtn.onclick = () => restoreBackup(backup.path || backup.name);
            
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'btn btn-secondary';
            deleteBtn.textContent = '✕ Delete';
            deleteBtn.onclick = () => deleteBackup(backup.path || backup.name);
            
            actionsDiv.appendChild(restoreBtn);
            actionsDiv.appendChild(deleteBtn);
            
            backupDiv.appendChild(infoDiv);
            backupDiv.appendChild(actionsDiv);
            backupsList.appendChild(backupDiv);
        });
    } catch (error) {
        console.error('Error loading backups:', error);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'backup-item-empty';
        errorDiv.textContent = `Error: ${error.message}`;
        backupsList.innerHTML = '';
        backupsList.appendChild(errorDiv);
    }
}

/**
 * Create a new backup
 */
async function createNewBackup() {
    if (!state.initialized) {
        showStatus('init-status', 'Please initialize a session first', 'error');
        return;
    }

    // Show progress indicator
    showStatus('init-status', '📦 Creating backup...', 'info');

    try {
        const response = await fetch('/api/backups', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: `Backup - ${new Date().toLocaleString()}`
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to create backup');
        }

        showStatus('init-status', '✓ Backup created successfully', 'success');
        setTimeout(() => {
            const statusEl = document.getElementById('init-status');
            if (statusEl) statusEl.style.display = 'none';
        }, 2000);
        await loadBackupsList();
    } catch (error) {
        showStatus('init-status', error.message, 'error');
    }
}

/**
 * Restore a backup
 */

/**
 * Load and display extracted ASAR list
 */
async function loadExtractedASARList() {
    const extractsList = document.getElementById('extractsList');
    if (!extractsList) {
        console.log('extractsList element not found');
        return;
    }

    try {
        const response = await fetch('/api/extracted-list');
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to load extractions');
        }

        const extracts = data.extracts || [];

        if (extracts.length === 0) {
            extractsList.innerHTML = '<div class="extract-item-empty">No extracted ASARs yet. Extract one to get started.</div>';
            return;
        }

        extractsList.innerHTML = '';
        extracts.forEach((extract) => {
            const extractDiv = document.createElement('div');
            extractDiv.className = 'extract-item';
            extractDiv.id = 'extract-' + extract.path.replace(/[\\/:]/g, '_');
            
            // Make the entire item clickable to select it
            extractDiv.style.cursor = 'pointer';
            extractDiv.onclick = () => selectExtract(extract.path, extractDiv);
            
            const infoDiv = document.createElement('div');
            infoDiv.className = 'extract-item-info';
            
            const nameDiv = document.createElement('div');
            nameDiv.className = 'extract-item-name';
            nameDiv.textContent = extract.name || 'Extraction';
            
            const dateDiv = document.createElement('div');
            dateDiv.className = 'extract-item-date';
            dateDiv.textContent = `Extracted: ${extract.date}`;
            
            infoDiv.appendChild(nameDiv);
            infoDiv.appendChild(dateDiv);
            
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'extract-item-actions';
            
            const useBtn = document.createElement('button');
            useBtn.className = 'btn btn-secondary';
            useBtn.textContent = '↻ Use';
            useBtn.title = 'Load this extraction';
            useBtn.onclick = (e) => {
                e.stopPropagation();
                useExtractedASAR(extract.path);
            };
            
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'btn btn-secondary';
            deleteBtn.textContent = '✕ Delete';
            deleteBtn.title = 'Delete this extraction';
            deleteBtn.onclick = (e) => {
                e.stopPropagation();
                deleteExtractedASAR(extract.path, extract.name);
            };
            
            actionsDiv.appendChild(useBtn);
            actionsDiv.appendChild(deleteBtn);
            
            extractDiv.appendChild(infoDiv);
            extractDiv.appendChild(actionsDiv);
            extractsList.appendChild(extractDiv);
        });
    } catch (error) {
        console.error('Error loading extracted ASAR list:', error);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'extract-item-empty';
        errorDiv.textContent = `Error: ${error.message}`;
        extractsList.innerHTML = '';
        extractsList.appendChild(errorDiv);
    }
}

/**
 * Use an extracted ASAR folder
 */
async function useExtractedASAR(path) {
    showStatus('init-status', 'Loading extracted ASAR...', 'info');

    try {
        const response = await fetch('/api/use-extract', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to load extraction');
        }

        state.initialized = true;
        state.extractedPath = data.extractedPath;
        
        showStatus('init-status', '✓ Extracted ASAR loaded successfully. Click "Next" to continue.', 'success');
        
        // Reload the list to show current selection
        await loadExtractedASARList();
    } catch (error) {
        showStatus('init-status', error.message, 'error');
    }
}

/**
 * Delete an extracted ASAR folder
 */
async function deleteExtractedASAR(path, name) {
    if (!confirm(`Are you sure you want to delete the extracted ASAR "${name}"? This will remove all files in this extraction. This cannot be undone.`)) {
        return;
    }

    showStatus('extract-status', '🗑️ Deleting extraction...', 'info');

    try {
        const response = await fetch('/api/delete-extract', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to delete extraction');
        }

        showStatus('extract-status', '✓ Extracted ASAR deleted successfully', 'success');
        setTimeout(() => {
            const statusEl = document.getElementById('extract-status');
            if (statusEl) statusEl.style.display = 'none';
        }, 2000);
        await loadExtractedASARList();
    } catch (error) {
        showStatus('extract-status', error.message, 'error');
    }
}

/**
 * Apply color preset
 */
function handlePresetChange(presetName) {
    if (!presetName) return; // Ignore empty selection
    applyPreset(presetName);
}

function applyPreset(presetName) {
    try {
        const preset = colorPresets[presetName];
        
        if (!preset) {
            showStatus('colors-status', 'Preset not found', 'error');
            return;
        }

        showStatus('colors-status', `Applying ${presetName} preset...`, 'info');

        const presetColors = preset.colors && typeof preset.colors === 'object'
            ? preset.colors
            : (typeof preset === 'object' ? preset : {});

        state.colors = { ...presetColors };
        
        // Update media if preset includes it
        if (preset.media && typeof preset.media === 'object') {
            state.media = { ...preset.media };
            updatePreviewMedia(preset.media);
        }
        
        // Defer rendering to avoid blocking
        setTimeout(() => {
            renderColorMappings();
        }, 0);
    } catch (error) {
        console.error('Preset apply failed:', error);
        showStatus('colors-status', 'Failed to apply preset. Please try again.', 'error');
    }
}

/**
 * Add color mapping
 */
function addColorMapping() {
    const colorList = document.getElementById('colorList');
    const id = 'color-' + Date.now();
    
    const item = document.createElement('div');
    item.className = 'color-mapping-item';
    item.id = id;
    item.innerHTML = `
        <input type="text" class="old-color" placeholder="Old color (e.g., #54adf7, 84 173 247, or --sol-color-primary-1)">
        <div class="color-preview" style="background: #888;" onclick="pickColor(this)"></div>
        <input type="text" class="new-color" placeholder="New color (e.g., #ff0000 or 255 0 0)">
        <div class="color-tuning">
            <input type="color" class="color-wheel" value="#888888" aria-label="Color wheel">
            <div class="color-sliders">
                <label>R
                    <input type="range" min="0" max="255" value="136" class="color-range" data-channel="r">
                    <input type="number" min="0" max="255" value="136" class="color-number" data-channel="r">
                </label>
                <label>G
                    <input type="range" min="0" max="255" value="136" class="color-range" data-channel="g">
                    <input type="number" min="0" max="255" value="136" class="color-number" data-channel="g">
                </label>
                <label>B
                    <input type="range" min="0" max="255" value="136" class="color-range" data-channel="b">
                    <input type="number" min="0" max="255" value="136" class="color-number" data-channel="b">
                </label>
            </div>
        </div>
        <button class="remove-btn" onclick="removeColorMapping('${id}')">Remove</button>
    `;
    
    colorList.appendChild(item);

    attachColorControlListeners(item);
    item.querySelectorAll('.old-color').forEach((input) => {
        input.addEventListener('input', debouncedUpdatePreview);
    });
    setColorControls(item, '#888888');
}

/**
 * Remove color mapping
 */
function removeColorMapping(id) {
    document.getElementById(id).remove();
    updatePreviewFromUi();
}

/**
 * Get color section name
 */
function getColorSection(colorName) {
    if (colorName.includes('primary')) return 'Primary Colors';
    if (colorName.includes('neutral')) return 'Neutral Colors';
    if (colorName.includes('accent')) return 'Accent Colors';
    if (colorName.includes('positive')) return 'Positive (Success)';
    if (colorName.includes('notice')) return 'Notice (Warning)';
    if (colorName.includes('negative')) return 'Negative (Error)';
    if (colorName.includes('highlight')) return 'Highlight Colors';
    if (colorName.includes('interactive')) return 'Interactive States';
    if (colorName.includes('status')) return 'Status Indicators';
    if (colorName.includes('foreground') || colorName.includes('surface') || colorName.includes('background')) return 'UI Surfaces';
    return 'Other Colors';
}

/**
 * Render color mappings with collapsible sections
 */
function renderColorMappings() {
    if (!DOM.colorList) return;
    DOM.colorList.innerHTML = '';

    if (!state.colors || typeof state.colors !== 'object') {
        showStatus('colors-status', 'No color data available', 'error');
        return;
    }

    // Group colors by section
    const sections = {};
    Object.entries(state.colors).forEach(([oldColor, newColor]) => {
        const section = getColorSection(oldColor);
        if (!sections[section]) sections[section] = [];
        sections[section].push([oldColor, newColor]);
    });

    // Define section order
    const sectionOrder = [
        'Primary Colors',
        'Neutral Colors',
        'Accent Colors',
        'Positive (Success)',
        'Notice (Warning)',
        'Negative (Error)',
        'Highlight Colors',
        'UI Surfaces',
        'Interactive States',
        'Status Indicators',
        'Other Colors'
    ];

    // Batch all sections in a single fragment
    const mainFragment = document.createDocumentFragment();
    const itemsToSetup = []; // Track items for later setup

    // Render each section
    sectionOrder.forEach(sectionName => {
        if (!sections[sectionName]) return;
        
        const colors = sections[sectionName];
        const sectionId = 'section-' + sectionName.replace(/\s+/g, '-').toLowerCase();
        const isExpanded = sectionName === 'Primary Colors'; // Expand primary colors by default

        // Create section container
        const sectionDiv = document.createElement('div');
        sectionDiv.className = 'color-section';
        sectionDiv.id = sectionId;

        // Create collapsible header
        const headerDiv = document.createElement('div');
        headerDiv.className = 'color-section-header';
        headerDiv.innerHTML = `
            <button class="color-section-toggle" onclick="toggleColorSection('${sectionId}')">
                <span class="toggle-arrow">${isExpanded ? '▼' : '▶'}</span>
                <span class="section-title">${sectionName}</span>
                <span class="color-count">(${colors.length})</span>
            </button>
        `;
        sectionDiv.appendChild(headerDiv);

        // Create collapsible content
        const contentDiv = document.createElement('div');
        contentDiv.className = 'color-section-content';
        contentDiv.style.display = isExpanded ? 'block' : 'none';

        // Render colors in this section using DocumentFragment for better performance
        const fragment = document.createDocumentFragment();
        for (let i = 0; i < colors.length; i++) {
            const [oldColor, newColor] = colors[i];
            const id = 'color-' + Date.now() + Math.random();
            
            // Determine if this is a background or accent color
            let category = '';
            if (oldColor.includes('primary-1') || oldColor.includes('primary-2')) {
                category = 'background';
            } else if (oldColor.includes('primary-3') || oldColor.includes('primary-4') || 
                       oldColor.includes('primary-5') || oldColor.includes('primary-6') ||
                       oldColor.includes('primary-7') || oldColor.includes('primary-8')) {
                category = 'accent';
            }
            
            const item = document.createElement('div');
            item.className = 'color-mapping-item' + (category ? ` color-${category}` : '');
            item.id = id;
            
            // Build the item structure using DOM methods to prevent XSS
            // Show category label for main colors
            if (category) {
                const catSpan = document.createElement('span');
                catSpan.className = 'color-category';
                catSpan.textContent = category.toUpperCase();
                item.appendChild(catSpan);
            }
            
            // Create color grid item
            const gridItem = document.createElement('div');
            gridItem.className = 'color-grid-item';
            
            const label = document.createElement('div');
            label.className = 'color-label';
            label.textContent = oldColor;
            
            const preview = document.createElement('div');
            preview.className = 'color-preview';
            preview.style.background = newColor;
            preview.onclick = () => selectColorForEditing(preview, id);
            preview.setAttribute('data-color-id', id);
            
            gridItem.appendChild(label);
            gridItem.appendChild(preview);
            item.appendChild(gridItem);
            
            // Create color editor section using innerHTML (no user input here)
            const editorDiv = document.createElement('div');
            editorDiv.className = 'color-editor';
            editorDiv.id = `editor-${id}`;
            editorDiv.style.display = 'none';
            
            const normalizedNewColor = normalizeColorToHex(newColor) || '#888888';
            editorDiv.innerHTML = `
                <div class="color-controls-layout">
                    <div class="color-text-fields">
                        <div class="color-input-group">
                            <label>HEX</label>
                            <input type="text" class="hex-input" placeholder="#000000" maxlength="7" value="${normalizedNewColor}">
                        </div>
                        <div class="color-input-group">
                            <label>R</label>
                            <input type="number" class="rgb-r" min="0" max="255" value="136">
                        </div>
                        <div class="color-input-group">
                            <label>G</label>
                            <input type="number" class="rgb-g" min="0" max="255" value="136">
                        </div>
                        <div class="color-input-group">
                            <label>B</label>
                            <input type="number" class="rgb-b" min="0" max="255" value="136">
                        </div>
                    </div>
                    <div class="color-wheel-container">
                        <input type="color" class="color-wheel" value="${normalizedNewColor}" aria-label="Color wheel">
                    </div>
                </div>
                <button class="btn btn-secondary btn-sm" onclick="closeColorEditor('${id}')">Done</button>
                <button class="remove-btn" onclick="removeColorMapping('${id}')">Remove</button>
            `;
            
            // Create hidden inputs using DOM methods
            const oldColorInput = document.createElement('input');
            oldColorInput.type = 'hidden';
            oldColorInput.className = 'old-color';
            oldColorInput.value = oldColor;
            editorDiv.appendChild(oldColorInput);
            
            const newColorInput = document.createElement('input');
            newColorInput.type = 'hidden';
            newColorInput.className = 'new-color';
            newColorInput.value = newColor;
            editorDiv.appendChild(newColorInput);
            
            item.appendChild(editorDiv);
            
            fragment.appendChild(item);
            
            // Track item for deferred setup
            itemsToSetup.push({
                item: item,
                newColor: newColor
            });
        }

        contentDiv.appendChild(fragment);
        sectionDiv.appendChild(contentDiv);
        mainFragment.appendChild(sectionDiv);
    });

    // Single append for all sections
    DOM.colorList.appendChild(mainFragment);

    // Defer heavy operations to avoid blocking UI - process in chunks
    let setupIndex = 0;
    const CHUNK_SIZE = 10; // Process 10 items per frame
    const totalItems = itemsToSetup.length;

    if (totalItems === 0) {
        showStatus('colors-status', 'No colors to display', 'error');
        return;
    }
    
    function setupNextChunk() {
        const endIndex = Math.min(setupIndex + CHUNK_SIZE, totalItems);
        
        // Update progress
        const progress = Math.round((setupIndex / totalItems) * 100);
        showStatus('colors-status', `Loading colors... ${progress}%`, 'info');
        
        // Process chunk of items
        for (let i = setupIndex; i < endIndex; i++) {
            const { item, newColor } = itemsToSetup[i];
            attachColorControlListeners(item);
            const oldColorInputs = item.querySelectorAll('.old-color');
            for (let j = 0; j < oldColorInputs.length; j++) {
                oldColorInputs[j].addEventListener('input', debouncedUpdatePreview);
            }
            setColorControls(item, normalizeColorToHex(newColor) || '#888888');
        }
        
        setupIndex = endIndex;
        
        // Schedule next chunk or finalize
        if (setupIndex < totalItems) {
            requestAnimationFrame(setupNextChunk);
        } else {
            // All setup done, update preview and show success
            updatePreviewFromColors(state.colors);
            showStatus('colors-status', `✓ Colors loaded successfully`, 'success');
        }
    }
    
    // Start setup process with initial message
    showStatus('colors-status', 'Loading colors... 0%', 'info');
    requestAnimationFrame(setupNextChunk);
}

/**
 * Toggle color section visibility
 */
function toggleColorSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (!section) return;
    const content = section.querySelector('.color-section-content');
    const toggle = section.querySelector('.color-section-toggle');
    if (!content || !toggle) return;
    const arrow = toggle.querySelector('.toggle-arrow');
    
    const isExpanded = content.style.display !== 'none';
    content.style.display = isExpanded ? 'none' : 'block';
    arrow.textContent = isExpanded ? '▶' : '▼';
}

/**
 * Pick color (opens color picker)
 */
function pickColor(element) {
    const item = element.closest('.color-mapping-item');
    const wheel = item?.querySelector('.color-wheel-hidden');
    if (wheel) {
        wheel.click();
        return;
    }
}

/**
 * Convert hex color to RGB string format
 * @param {string} hex - Hex color (e.g., "#888888")
 * @returns {string} - RGB string (e.g., "136, 136, 136")
 */
function hexToRGB(hex) {
    if (!hex || !hex.startsWith('#') || hex.length !== 7) {
        return '';
    }
    
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    
    if (isNaN(r) || isNaN(g) || isNaN(b)) {
        return '';
    }
    
    return `${r}, ${g}, ${b}`;
}

/**
 * Convert RGB string to hex color
 * @param {string} rgb - RGB string (e.g., "136, 136, 136" or "136 136 136")
 * @returns {string} - Hex color (e.g., "#888888")
 */
function rgbToHex(rgb) {
    if (!rgb || typeof rgb !== 'string') {
        return '';
    }
    
    // Parse RGB values - handle both comma and space separators
    const values = rgb.split(/[\s,]+/).filter(v => v.trim());
    
    if (values.length !== 3) {
        return '';
    }
    
    const r = parseInt(values[0].trim());
    const g = parseInt(values[1].trim());
    const b = parseInt(values[2].trim());
    
    if (isNaN(r) || isNaN(g) || isNaN(b) || r < 0 || r > 255 || g < 0 || g > 255 || b < 0 || b > 255) {
        return '';
    }
    
    const toHex = (n) => {
        const hex = n.toString(16);
        return hex.length === 1 ? '0' + hex : hex;
    };
    
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`.toUpperCase();
}

/**
 * Select a color for editing - show the color editor
 */
function selectColorForEditing(previewElement, colorId) {
    // Close all other open editors
    document.querySelectorAll('.color-editor').forEach(editor => {
        if (editor.id !== `editor-${colorId}`) {
            editor.style.display = 'none';
        }
    });
    
    // Toggle this editor
    const editor = document.getElementById(`editor-${colorId}`);
    if (editor) {
        const isVisible = editor.style.display === 'flex';
        editor.style.display = isVisible ? 'none' : 'flex';
        
        if (!isVisible) {
            // Initialize RGB inputs from hex value
            const hexInput = editor.querySelector('.hex-input');
            if (hexInput && hexInput.value) {
                updateRGBFromHex(editor, hexInput.value);
            }
        }
    }
}

/**
 * Close the color editor
 */
function closeColorEditor(colorId) {
    const editor = document.getElementById(`editor-${colorId}`);
    if (editor) {
        editor.style.display = 'none';
    }
}

/**
 * Update RGB inputs from hex value
 */
function updateRGBFromHex(editor, hexValue) {
    const hex = hexValue.replace('#', '');
    if (hex.length === 6) {
        const r = parseInt(hex.substring(0, 2), 16);
        const g = parseInt(hex.substring(2, 4), 16);
        const b = parseInt(hex.substring(4, 6), 16);
        
        const rInput = editor.querySelector('.rgb-r');
        const gInput = editor.querySelector('.rgb-g');
        const bInput = editor.querySelector('.rgb-b');
        
        if (rInput) rInput.value = r;
        if (gInput) gInput.value = g;
        if (bInput) bInput.value = b;
    }
}

/**
 * Update hex from RGB values
 */
function updateHexFromRGB(editor) {
    const r = parseInt(editor.querySelector('.rgb-r')?.value || 0);
    const g = parseInt(editor.querySelector('.rgb-g')?.value || 0);
    const b = parseInt(editor.querySelector('.rgb-b')?.value || 0);
    
    const hexInput = editor.querySelector('.hex-input');
    if (hexInput) {
        hexInput.value = rgbToHex(r, g, b);
    }
}

/**
 * Open color wheel picker
 */
function openColorPicker(event) {
    event.preventDefault();
    const button = event.target;
    const item = button.closest('.color-mapping-item');
    const wheel = item?.querySelector('.color-wheel-hidden');
    if (wheel) {
        wheel.click();
    }
}

/**
 * Collect color mappings from UI
 */
function collectColorMappings() {
    const colors = {};
    const items = document.querySelectorAll('.color-mapping-item');

    items.forEach(item => {
        const oldColor = item.querySelector('.old-color').value.trim();
        const newColor = item.querySelector('.new-color').value.trim();

        if (oldColor && newColor) {
            colors[oldColor] = newColor;
        }
    });

    return colors;
}

/**
 * Apply colors
 */
async function applyColors() {
    const colors = collectColorMappings();

    if (Object.keys(colors).length === 0) {
        showStatus('colors-status', 'Please add at least one color mapping', 'error');
        return;
    }

    console.log('Applying colors:', colors);

    // Show progress bar
    const statusEl = document.getElementById('colors-status');
    if (statusEl && !statusEl.querySelector('.progress-bar-wrapper')) {
        const wrapper = document.createElement('div');
        wrapper.className = 'progress-bar-wrapper';
        wrapper.innerHTML = `
            <div class="progress-bar-container">
                <div class="progress-bar" id="colors-progress-bar" style="width: 0%;"></div>
            </div>
            <div class="progress-text" id="colors-progress-text" style="text-align: center; margin-top: 8px; font-size: 0.9em; color: #8db4d0;">Starting color application...</div>
        `;
        statusEl.innerHTML = '';
        statusEl.appendChild(wrapper);
        statusEl.style.display = 'block';
    }

    try {
        // Start the async operation
        const response = await fetch('/api/apply-colors', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ colors })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to apply colors');
        }

        console.log('Color application response:', data);

        // If it's async, poll for status
        if (data.async) {
            await pollOperationStatus('apply-colors', 'colors-status', (status) => {
                if (status.state === 'done') {
                    state.config.colors = colors;
                    updatePreviewFromColors(colors);
                }
            });
        } else {
            // Synchronous response (legacy)
            state.config.colors = colors;
            showStatus('colors-status', '✓ Colors applied successfully', 'success');
            updatePreviewFromColors(colors);
        }

    } catch (error) {
        console.error('Color application error:', error);
        showStatus('colors-status', error.message, 'error');
    }
}

/**
 * Poll for operation status
 */
async function pollOperationStatus(operation, statusElementId, onComplete) {
    const maxAttempts = 600; // 10 minutes max (600 * 1s) - increased for color operations
    let attempts = 0;
    
    const poll = async () => {
        if (attempts++ >= maxAttempts) {
            showStatus(statusElementId, 'Operation timed out after 10 minutes', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            // Handle nested status structure: { success: true, status: {...} }
            const status = data.status || data;
            
            if (status.operation === operation) {
                if (status.state === 'running') {
                    // Update progress bar if it exists
                    const progressBar = document.getElementById(statusElementId)?.querySelector('.progress-bar');
                    const progressText = document.getElementById(statusElementId)?.querySelector('.progress-text');
                    
                    if (progressBar && status.progress !== undefined) {
                        progressBar.style.width = `${Math.min(status.progress, 99)}%`;
                    }
                    if (progressText && status.progress !== undefined) {
                        progressText.textContent = `${Math.min(status.progress, 99)}% - ${status.message}`;
                    } else {
                        showStatus(statusElementId, status.message, 'info');
                    }
                    
                    // Poll more frequently at the start, then less frequently
                    const delay = attempts < 5 ? 500 : 1000;
                    setTimeout(poll, delay);
                } else if (status.state === 'done') {
                    const progressBar = document.getElementById(statusElementId)?.querySelector('.progress-bar');
                    if (progressBar) {
                        progressBar.style.width = '100%';
                        const progressText = document.getElementById(statusElementId)?.querySelector('.progress-text');
                        if (progressText) {
                            progressText.textContent = `100% - ${status.message}`;
                        }
                    }
                    showStatus(statusElementId, `✓ ${status.message}`, 'success');
                    if (onComplete) onComplete(status);
                } else if (status.state === 'error') {
                    showStatus(statusElementId, status.lastError || status.message, 'error');
                }
            } else {
                // Still waiting for operation to start or wrong operation
                setTimeout(poll, 500);
            }
        } catch (error) {
            console.error('Status check error:', error);
            showStatus(statusElementId, `Status check failed: ${error.message}`, 'error');
        }
    };
    
    setTimeout(poll, 100); // Start polling immediately
}

/**
 * Add media replacement
 */
function addMediaReplacement() {
    const mediaList = document.getElementById('mediaList');
    const id = 'media-' + Date.now();
    
    const item = document.createElement('div');
    item.className = 'media-replacement-item';
    item.id = id;
    item.innerHTML = `
        <input type="text" class="target-path" placeholder="Target path in launcher (e.g., assets/images/logo.png)">
        <div class="file-input-wrapper">
            <input type="file" id="file-${id}" class="file-input">
            <label for="file-${id}" class="file-input-label">Choose File</label>
            <span class="file-name" style="color: #b0bac0; margin-left: 10px;">No file selected</span>
        </div>
        <button class="remove-btn" onclick="removeMediaReplacement('${id}')">Remove</button>
    `;
    
    mediaList.appendChild(item);

    // Update file name display and preserve original filename in target path
    document.getElementById(`file-${id}`).addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) {
            item.querySelector('.file-name').textContent = 'No file selected';
            return;
        }
        
        const fileName = file.name;
        item.querySelector('.file-name').textContent = fileName;
        
        // Auto-populate target path if empty or update filename while preserving directory
        const targetPathInput = item.querySelector('.target-path');
        const currentPath = targetPathInput.value.trim();
        
        if (!currentPath) {
            // If empty, suggest a path based on file type
            const ext = fileName.split('.').pop().toLowerCase();
            if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(ext)) {
                targetPathInput.value = `assets/images/${fileName}`;
            } else if (['mp4', 'webm', 'mov'].includes(ext)) {
                targetPathInput.value = `assets/videos/${fileName}`;
            } else if (['ogg', 'mp3', 'wav'].includes(ext)) {
                targetPathInput.value = `assets/sounds/${fileName}`;
            } else {
                targetPathInput.value = `assets/${fileName}`;
            }
        } else {
            // If path exists, replace only the filename part while preserving directory
            const pathParts = currentPath.split('/');
            pathParts[pathParts.length - 1] = fileName;
            targetPathInput.value = pathParts.join('/');
        }
    });
}

/**
 * Load default media assets from public/assets/
 */
function loadDefaultMediaAssets() {
    const defaultAssets = [
        // Images
        { path: 'assets/images/sc_bg_fallback.jpg', type: 'image', name: 'Star Citizen Background', url: 'assets/images/sc_bg_fallback.jpg' },
        { path: 'assets/images/sc_bg_fallback_stanton.jpg', type: 'image', name: 'Stanton Background', url: 'assets/images/sc_bg_fallback_stanton.jpg' },
        { path: 'assets/images/sc_bg_fallback_pyro.jpg', type: 'image', name: 'Pyro Background', url: 'assets/images/sc_bg_fallback_pyro.jpg' },
        { path: 'assets/images/avatar_default.jpg', type: 'image', name: 'Default Avatar', url: 'assets/images/avatar_default.jpg' },
        // Logos
        { path: 'assets/logos/cig-logo.svg', type: 'image', name: 'CIG Logo', url: 'assets/logos/cig-logo.svg' },
        { path: 'assets/logos/sc-game-logo-small.svg', type: 'image', name: 'SC Logo Small', url: 'assets/logos/sc-game-logo-small.svg' },
        { path: 'assets/logos/sc-game-logo-wide.svg', type: 'image', name: 'SC Logo Wide', url: 'assets/logos/sc-game-logo-wide.svg' },
        { path: 'assets/logos/sq42-game-logo-small.svg', type: 'image', name: 'SQ42 Logo', url: 'assets/logos/sq42-game-logo-small.svg' },
        { path: 'assets/logos/star_engine.svg', type: 'image', name: 'Star Engine Logo', url: 'assets/logos/star_engine.svg' },
        // Videos
        { path: 'assets/videos/sc_bg_video.webm', type: 'video', name: 'Default Background Video', url: 'assets/videos/sc_bg_video.webm' },
        { path: 'assets/videos/sc_bg_video_stanton.webm', type: 'video', name: 'Stanton Background Video', url: 'assets/videos/sc_bg_video_stanton.webm' },
        { path: 'assets/videos/sc_bg_video_pyro.webm', type: 'video', name: 'Pyro Background Video', url: 'assets/videos/sc_bg_video_pyro.webm' }
    ];

    lastMediaAssets = defaultAssets;
    renderMediaAssetPicker(defaultAssets);
    showStatus('media-status', `✓ Loaded ${defaultAssets.length} default assets`, 'success');
}

function applyMediaAssetFilter() {
    const filter = document.getElementById('mediaFilter')?.value || 'all';
    if (!lastMediaAssets.length) {
        renderMediaAssetPicker([]);
        return;
    }

    if (filter === 'all') {
        // Exclude audio/music files
        const filtered = lastMediaAssets.filter(asset => asset.type !== 'audio');
        renderMediaAssetPicker(filtered);
        return;
    }

    // Filter by type, excluding audio
    const filtered = lastMediaAssets.filter(asset => asset.type === filter && asset.type !== 'audio');
    renderMediaAssetPicker(filtered);
}

function renderMediaAssetPicker(assets) {
    const container = document.getElementById('mediaAssetPicker');
    if (!container) return;

    container.innerHTML = '';

    if (!assets.length) {
        const empty = document.createElement('div');
        empty.className = 'status info show';
        empty.textContent = 'No media assets available.';
        container.appendChild(empty);
        return;
    }

    assets.forEach((asset) => {
        const id = 'asset-' + Math.random().toString(36).slice(2);
        const item = document.createElement('div');
        item.className = 'media-grid-item';

        // Preview container with hover overlay
        const previewContainer = document.createElement('div');
        previewContainer.className = 'media-preview-container';

        const preview = document.createElement('div');
        preview.className = 'media-asset-preview';

        if (asset.type === 'image') {
            const img = document.createElement('img');
            img.src = asset.url;
            img.alt = asset.name;
            preview.appendChild(img);
        } else if (asset.type === 'video') {
            const video = document.createElement('video');
            video.src = asset.url;
            video.muted = true;
            video.loop = true;
            preview.appendChild(video);
        } else {
            const text = document.createElement('div');
            text.textContent = 'Preview not available';
            preview.appendChild(text);
        }

        // Hover overlay with select button
        const overlay = document.createElement('div');
        overlay.className = 'media-hover-overlay';

        const selectBtn = document.createElement('button');
        selectBtn.className = 'media-select-btn';
        selectBtn.textContent = '📁 Select Replacement';
        selectBtn.onclick = () => fileInput.click();

        overlay.appendChild(selectBtn);
        previewContainer.appendChild(preview);
        previewContainer.appendChild(overlay);

        // File name and path
        const info = document.createElement('div');
        info.className = 'media-info';

        const name = document.createElement('div');
        name.className = 'media-name';
        name.textContent = asset.name || asset.path.split('/').pop();

        const path = document.createElement('div');
        path.className = 'media-path';
        path.textContent = asset.path;

        info.appendChild(name);
        info.appendChild(path);

        // Hidden file input
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.id = `file-${id}`;
        fileInput.className = 'file-input';
        fileInput.style.display = 'none';
        fileInput.dataset.targetPath = asset.path;

        // Accept only images and videos based on type
        if (asset.type === 'image') {
            fileInput.accept = 'image/*';
        } else if (asset.type === 'video') {
            fileInput.accept = 'video/*';
        }

        // Status indicator
        const status = document.createElement('div');
        status.className = 'media-replacement-status';
        status.textContent = 'Using default';

        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;

            // Update preview
            preview.innerHTML = '';
            if (asset.type === 'image') {
                const img = document.createElement('img');
                img.src = URL.createObjectURL(file);
                img.alt = file.name;
                preview.appendChild(img);
            } else if (asset.type === 'video') {
                const video = document.createElement('video');
                video.src = URL.createObjectURL(file);
                video.muted = true;
                video.loop = true;
                video.controls = true;
                preview.appendChild(video);
            }

            // Update status
            status.textContent = `✓ ${file.name}`;
            status.style.color = '#54adf7';
            item.classList.add('has-replacement');

            // Update live preview
            updateLivePreviewMedia(asset.path, file);
        });

        item.appendChild(previewContainer);
        item.appendChild(info);
        item.appendChild(fileInput);
        item.appendChild(status);
        container.appendChild(item);
    });
}

/**
 * Update live preview when media is selected
 */
function updateLivePreviewMedia(targetPath, file) {
    const fileUrl = URL.createObjectURL(file);

    // Send to preview iframe
    updatePreviewMedia({
        [targetPath]: fileUrl
    });
}

/**
 * Remove media replacement
 */
function removeMediaReplacement(id) {
    document.getElementById(id).remove();
}

/**
 * Collect media replacements from UI
 */
function collectMediaReplacements() {
    const media = {};
    const fileInputs = document.querySelectorAll('#mediaAssetPicker .file-input');

    fileInputs.forEach(input => {
        const targetPath = input.dataset.targetPath;
        if (targetPath && input.files.length > 0) {
            media[targetPath] = input.files[0];
        }
    });

    return media;
}

/**
 * Apply media
 */
async function applyMedia() {
    const media = collectMediaReplacements();

    if (Object.keys(media).length === 0) {
        showStatus('media-status', 'Please add at least one media file', 'error');
        return;
    }

    // Show progress bar
    const statusEl = document.getElementById('media-status');
    if (statusEl && !statusEl.querySelector('.progress-bar-wrapper')) {
        const wrapper = document.createElement('div');
        wrapper.className = 'progress-bar-wrapper';
        wrapper.innerHTML = `
            <div class="progress-bar-container">
                <div class="progress-bar" id="media-progress-bar" style="width: 0%;"></div>
            </div>
            <div class="progress-text" id="media-progress-text" style="text-align: center; margin-top: 8px; font-size: 0.9em; color: #8db4d0;">Starting media upload...</div>
        `;
        statusEl.innerHTML = '';
        statusEl.appendChild(wrapper);
        statusEl.style.display = 'block';
    }

    try {
        const entries = Object.entries(media);
        const total = entries.length;
        let completed = 0;

        const progressBar = document.getElementById('media-progress-bar');
        const progressText = document.getElementById('media-progress-text');

        for (const [targetPath, file] of entries) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('targetPath', targetPath);

            if (progressText) {
                progressText.textContent = `Uploading ${completed + 1} of ${total}: ${file.name}`;
            }

            const response = await fetch('/api/upload-media', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `Failed to upload ${targetPath}`);
            }

            completed++;
            const progress = Math.round((completed / total) * 100);
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
            }
        }

        state.config.media = media;
        showStatus('media-status', '✓ Media files applied successfully', 'success');

    } catch (error) {
        showStatus('media-status', error.message, 'error');
    }
}

// ============================================================================
// Music Management Functions
// ============================================================================

/**
 * Load default music files from launcher
 */
async function loadDefaultMusic() {
    try {
        const response = await fetch('/api/default-music');
        const data = await response.json();
        if (response.ok && Array.isArray(data.files) && data.files.length > 0) {
            state.music = data.files.map((name) => ({
                name,
                isDefault: true
            }));
            renderMusicList();
            showStatus('music-status', '✓ Loaded default music playlist', 'success');
            return;
        }
    } catch (error) {
        // Fall back to static defaults below
    }

    state.music = [
        { name: 'GrimHex.ogg', isDefault: true },
        { name: 'StarMarine.ogg', isDefault: true }
    ];
    renderMusicList();
    showStatus('music-status', '✓ Loaded default music playlist', 'success');
}

/**
 * Render music list
 */
function renderMusicList() {
    const musicList = document.getElementById('musicList');
    if (!musicList) return;

    if (state.music.length === 0) {
        musicList.innerHTML = '<div style="color: #aaa; text-align: center; padding: 20px;">No music files added. Add music files or load defaults.</div>';
        return;
    }

    // Clear and rebuild using DOM methods to prevent XSS
    musicList.innerHTML = '';
    const fragment = document.createDocumentFragment();
    
    state.music.forEach((track, index) => {
        const item = document.createElement('div');
        item.className = 'music-item';
        item.setAttribute('data-index', index);
        
        const order = document.createElement('div');
        order.className = 'music-item-order';
        order.textContent = index + 1;
        item.appendChild(order);
        
        const nameDiv = document.createElement('div');
        nameDiv.className = 'music-item-name';
        
        const nameSpan = document.createElement('span');
        nameSpan.textContent = track.name;
        nameDiv.appendChild(nameSpan);
        
        const tagSpan = document.createElement('span');
        tagSpan.style.color = track.isDefault ? '#00d4ff' : '#80d0ff';
        tagSpan.style.fontSize = '12px';
        tagSpan.textContent = track.isDefault ? ' (default)' : ' (custom)';
        nameDiv.appendChild(tagSpan);
        
        item.appendChild(nameDiv);
        
        const controls = document.createElement('div');
        controls.className = 'music-item-controls';
        
        const playBtn = document.createElement('button');
        playBtn.textContent = '▶';
        playBtn.title = 'Play';
        playBtn.onclick = () => playMusicTrack(index);
        
        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-btn';
        removeBtn.textContent = '✕';
        removeBtn.title = 'Remove';
        removeBtn.onclick = () => removeMusicFile(index);
        
        controls.appendChild(playBtn);
        controls.appendChild(removeBtn);
        item.appendChild(controls);
        
        fragment.appendChild(item);
    });
    
    musicList.appendChild(fragment);
}

/**
 * Add music file
 */
function addMusicFile() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.ogg,.mp3,audio/ogg,audio/mpeg';
    input.multiple = true;
    
    input.onchange = (e) => {
        const files = Array.from(e.target.files);
        if (files.length === 0) return;

        files.forEach((file) => {
            state.music.push({
                name: file.name,
                file: file,
                isDefault: false
            });
        });

        renderMusicList();
        showStatus('music-status', `✓ Added ${files.length} music file${files.length > 1 ? 's' : ''}`, 'success');
    };

    input.click();
}

/**
 * Remove music file
 */
function removeMusicFile(index) {
    const track = state.music[index];
    state.music.splice(index, 1);
    renderMusicList();
    showStatus('music-status', `✓ Removed ${track.name}`, 'success');
}

/**
 * Play music track in player
 */
async function playMusicTrack(index) {
    const track = state.music[index];
    if (!track) {
        console.error('Track not found at index:', index);
        return;
    }

    const player = document.getElementById('musicPlayerElement');
    const titleEl = document.getElementById('currentTrackName');
    const typeEl = document.getElementById('currentTrackType');

    if (!player || !titleEl || !typeEl) {
        console.error('Music player elements not found');
        return;
    }

    try {
        // Stop and clear any existing playback
        player.pause();
        player.currentTime = 0;

        let audioUrl = null;

        if (track.file) {
            // Custom file selected by user
            audioUrl = URL.createObjectURL(track.file);
            titleEl.textContent = track.name;
            typeEl.textContent = 'Custom File';
        } else if (track.isDefault) {
            // Default file from server
            const response = await fetch(`/api/music/${encodeURIComponent(track.name)}`);
            if (response.ok) {
                const blob = await response.blob();
                audioUrl = URL.createObjectURL(blob);
                titleEl.textContent = track.name;
                typeEl.textContent = 'Default File';
            } else {
                showStatus('music-status', `Failed to load ${track.name}`, 'error');
                return;
            }
        }

        if (audioUrl) {
            // Set the source directly on the player
            player.src = audioUrl;
            player.load();
            
            // Play with user interaction handling
            const playPromise = player.play();
            if (playPromise !== undefined) {
                playPromise.catch(err => {
                    console.error('Error playing audio:', err);
                    showStatus('music-status', 'Click play button on the audio player to start', 'info');
                });
            }
        }
    } catch (error) {
        console.error('Error loading music track:', error);
        showStatus('music-status', `Error loading ${track.name}`, 'error');
    }
}

/**
 * Move music file up
 */
/**
 * Apply music files to launcher
 */
async function applyMusic() {
    if (state.music.length === 0) {
        showStatus('music-status', 'Please add at least one music file or load defaults', 'error');
        return;
    }

    showStatus('music-status', 'Uploading music files...', 'info');

    try {
        // First, clear existing music directory
        const clearResponse = await fetch('/api/clear-music', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!clearResponse.ok) {
            const clearData = await clearResponse.json();
            throw new Error(clearData.error || 'Failed to clear music directory');
        }

        // Upload each music file with original name
        let uploadedCount = 0;
        for (const track of state.music) {
            // Skip default tracks that don't have a file (already in launcher)
            if (track.isDefault && !track.file) {
                uploadedCount++;
                continue;
            }

            if (!track.file) {
                showStatus('music-status', `Skipping ${track.name} - no file available`, 'error');
                continue;
            }

            const formData = new FormData();
            formData.append('file', track.file);
            formData.append('targetPath', `assets/musics/${track.name}`);

            const response = await fetch('/api/upload-media', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `Failed to upload ${track.name}`);
            }
            
            uploadedCount++;
        }

        // Update main.*.js with new music file list
        showStatus('music-status', 'Updating launcher code...', 'info');
        
        const musicList = state.music.map(t => `/musics/${t.name}`);
        const codeResponse = await fetch('/api/update-music-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ musicFiles: musicList })
        });

        const codeData = await codeResponse.json();
        if (!codeResponse.ok) {
            throw new Error(codeData.error || 'Failed to update music code');
        }

        state.config.music = state.music.map(t => t.name);
        showStatus('music-status', `✓ Applied ${state.music.length} music track${state.music.length > 1 ? 's' : ''} successfully`, 'success');

    } catch (error) {
        showStatus('music-status', error.message, 'error');
    }
}

/**
 * Repack asar
 */
async function repackAsar() {
    showStatus('finalize-status', 'Repacking app.asar...', 'info');

    try {
        const response = await fetch('/api/repack', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to repack');
        }

        showStatus('finalize-status', `✓ Repacked successfully to: ${data.outputPath}`, 'success');

    } catch (error) {
        showStatus('finalize-status', error.message, 'error');
    }
}

/**
 * Compile changes and test launcher
 */
async function compileAndTest() {
    showStatus('finalize-status', 'Compiling changes...', 'info');

    try {
        // Compile
        let response = await fetch('/api/compile-changes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        let data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Compilation failed');
        }

        showStatus('finalize-status', '✓ Compiled successfully. Launching...', 'success');

        // Wait a moment then launch
        setTimeout(async () => {
            try {
                response = await fetch('/api/test-launcher', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({})
                });

                data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Failed to launch');
                }

                showStatus('finalize-status', '✓ Launcher started! Check your screen.', 'success');

            } catch (error) {
                showStatus('finalize-status', `Launch warning: ${error.message}`, 'error');
            }
        }, 1000);

    } catch (error) {
        showStatus('finalize-status', error.message, 'error');
    }
}

/**
 * Test launcher - temporarily pack and run without installing
 */
async function testLauncher() {
    showStatus('finalize-status', 'Packing theme and launching RSI Launcher...', 'info');

    try {
        const response = await fetch('/api/test-launcher', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to launch');
        }

        showStatus('finalize-status', '✓ Launcher started with test theme! It will restore to original in a moment.', 'success');

    } catch (error) {
        showStatus('finalize-status', error.message, 'error');
    }
}

/**
 * Deploy theme - permanently install to RSI Launcher directory
 */
async function deployTheme() {
    const confirmed = confirm('Deploy theme to RSI Launcher? This will permanently apply your changes.');
    if (!confirmed) return;

    showStatus('finalize-status', 'Deploying theme to RSI Launcher...', 'info');

    try {
        const response = await fetch('/api/deploy-theme', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to deploy theme');
        }

        showStatus('finalize-status', '✓ Theme deployed successfully! Your changes are now installed.', 'success');

    } catch (error) {
        showStatus('finalize-status', error.message, 'error');
    }
}

/**
 * Repack asar

/**
 * Save theme configuration
 */
async function saveTheme() {
    const themeName = prompt('Enter theme name:', state.config.name || 'My Theme');

    if (!themeName) return;

    const colors = collectColorMappings();
    const media = collectMediaReplacements();

    showStatus('finalize-status', 'Saving theme...', 'info');

    try {
        const response = await fetch('/api/config/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: themeName,
                config: {
                    colors,
                    media: Object.keys(media),
                    music: state.music.map(t => ({ name: t.name, isDefault: t.isDefault || false }))
                }
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to save theme');
        }

        state.config.name = themeName;
        showStatus('finalize-status', `✓ Theme saved: ${data.message}`, 'success');

    } catch (error) {
        showStatus('finalize-status', error.message, 'error');
    }
}

/**
 * Export theme to file
 */
async function exportTheme() {
    const themeName = prompt('Enter theme name for export:', state.config.name || 'My Theme');

    if (!themeName) return;

    const colors = collectColorMappings();
    const media = collectMediaReplacements();

    try {
        const response = await fetch('/api/config/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: themeName,
                config: {
                    colors,
                    media: Object.keys(media),
                    music: state.music.map(t => ({ name: t.name, isDefault: t.isDefault || false }))
                }
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to export theme');
        }

        // Download as file
        const themeJson = JSON.stringify(data.theme, null, 2);
        const blob = new Blob([themeJson], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${themeName.replace(/[^a-z0-9]/gi, '-')}.theme.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showStatus('finalize-status', `✓ Theme exported: ${a.download}`, 'success');

    } catch (error) {
        showStatus('finalize-status', error.message, 'error');
    }
}

/**
 * Import theme from file
 */
function importTheme() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.theme.json,.json';
    input.style.display = 'none';
    input.onchange = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        try {
            const text = await file.text();
            const theme = JSON.parse(text);

            if (!theme.colors) {
                throw new Error('Invalid theme file: missing colors');
            }

            // Apply theme colors
            state.colors = theme.colors;
            
            // Apply theme media if available
            if (theme.media) {
                state.media = theme.media;
            }
            
            state.config.name = theme.name || 'Imported Theme';
            
            renderColorMappings();
            showStatus('finalize-status', `✓ Theme imported: ${theme.name || 'Imported Theme'}`, 'success');

        } catch (error) {
            showStatus('finalize-status', `Import failed: ${error.message}`, 'error');
        }
    };
    document.body.appendChild(input);
    input.click();
    document.body.removeChild(input);
}

/**
 * Import theme from Colors page
 */
function importThemeFromColors() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.theme.json,.json';
    input.style.display = 'none';
    input.onchange = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        try {
            const text = await file.text();
            const theme = JSON.parse(text);

            if (!theme.colors) {
                throw new Error('Invalid theme file: missing colors');
            }

            // Apply theme colors
            state.colors = theme.colors;
            
            // Apply theme media if available
            if (theme.media) {
                state.media = theme.media;
                updatePreviewMedia(theme.media);
            }
            
            state.config.name = theme.name || 'Imported Theme';
            
            renderColorMappings();
            showStatus('colors-status', `✓ Theme imported: ${theme.name || 'Imported Theme'}`, 'success');

        } catch (error) {
            showStatus('colors-status', `Import failed: ${error.message}`, 'error');
        }
    };
    document.body.appendChild(input);
    input.click();
    document.body.removeChild(input);
}

/**
 * Export current preset to file
 */
function exportCurrentPreset() {
    if (Object.keys(state.colors).length === 0) {
        showStatus('colors-status', 'No colors to export. Please add color mappings first.', 'error');
        return;
    }

    const theme = {
        name: state.config.name || 'Custom Theme',
        description: 'Exported from RUIE',
        colors: state.colors,
        media: state.media || {},
        music: state.music || [],
        timestamp: new Date().toISOString()
    };

    const json = JSON.stringify(theme, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    const filename = (state.config.name || 'custom-theme').toLowerCase().replace(/\s+/g, '-');
    a.download = `${filename}.theme.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showStatus('colors-status', '✓ Theme exported successfully', 'success');
}

/**
 * Save current preset to server
 */
async function saveCurrentPreset() {
    if (Object.keys(state.colors).length === 0) {
        showStatus('colors-status', 'No colors to save. Please add color mappings first.', 'error');
        return;
    }

    const themeName = prompt('Enter a name for this preset:', state.config.name || 'My Custom Theme');
    if (!themeName) return;

    try {
        const theme = {
            name: themeName,
            description: 'Custom preset',
            colors: state.colors,
            media: state.media || {},
            music: state.music || []
        };

        const response = await fetch('/api/save-preset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(theme)
        });

        const data = await response.json();
        
        if (data.success) {
            state.config.name = themeName;
            showStatus('colors-status', `✓ Preset "${themeName}" saved successfully`, 'success');
        } else {
            showStatus('colors-status', `Failed to save preset: ${data.error || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error saving preset:', error);
        showStatus('colors-status', `Error saving preset: ${error.message}`, 'error');
    }
}

/**
 * Handle theme file import
 */
async function handleThemeImport(event) {
    const file = event.target.files[0];
    if (!file) return;

    try {
        const text = await file.text();
        const theme = JSON.parse(text);

        if (!theme.colors) {
            throw new Error('Invalid theme file: missing colors');
        }

        // Apply theme
        state.colors = theme.colors;
        state.config.name = theme.name || 'Imported Theme';
        
        renderColorMappings();
        showStatus('finalize-status', `✓ Theme imported: ${theme.name}`, 'success');

        // Reset file input
        event.target.value = '';

    } catch (error) {
        showStatus('finalize-status', `Import failed: ${error.message}`, 'error');
        event.target.value = '';
    }
}

/**
 * Load saved themes list
 */
async function loadSavedThemes() {
    const section = document.getElementById('themes-section');
    const list = document.getElementById('themesList');

    showStatus('finalize-status', 'Loading saved themes...', 'info');

    try {
        const response = await fetch('/api/config/list');
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to load themes');
        }

        if (data.themes.length === 0) {
            list.innerHTML = '<p class="no-items">No saved themes found. Save a theme first!</p>';
        } else {
            list.innerHTML = data.themes.map(theme => `
                <div class="theme-item">
                    <div class="theme-info">
                        <h4>${theme.name}</h4>
                        <p>${theme.colorCount} colors, ${theme.mediaCount} media files</p>
                        <small>${new Date(theme.created).toLocaleString()}</small>
                    </div>
                    <button class="btn btn-primary" onclick="loadTheme('${theme.filename}')">Load</button>
                </div>
            `).join('');
        }

        section.style.display = 'block';
        showStatus('finalize-status', '', '');

    } catch (error) {
        showStatus('finalize-status', error.message, 'error');
    }
}

/**
 * Load specific theme
 */
async function loadTheme(filename) {
    showStatus('finalize-status', 'Loading theme...', 'info');

    try {
        const response = await fetch('/api/config/load', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to load theme');
        }

        // Apply theme
        state.colors = data.theme.colors;
        state.config.name = data.theme.name;
        
        renderColorMappings();
        updatePreviewFromColors(state.colors);
        
        closeThemesList();
        showStatus('finalize-status', `✓ Theme loaded: ${data.theme.name}`, 'success');

    } catch (error) {
        showStatus('finalize-status', error.message, 'error');
    }
}

/**
 * Close themes list
 */
function closeThemesList() {
    document.getElementById('themes-section').style.display = 'none';
}

/**
 * View backups
 */
async function viewBackups() {
    const section = document.getElementById('backups-section');
    const list = document.getElementById('backupsList');

    showStatus('finalize-status', 'Loading backups...', 'info');

    try {
        const response = await fetch('/api/backups');
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to load backups');
        }

        if (data.backups.length === 0) {
            list.innerHTML = '<p>No backups found</p>';
        } else {
            list.innerHTML = data.backups.map(backup => `
                <div class="backup-item">
                    <span>${backup.name} (${new Date(backup.timestamp).toLocaleString()})</span>
                    <button onclick="restoreBackup('${backup.path}')">Restore</button>
                </div>
            `).join('');
        }

        section.style.display = 'block';
        showStatus('finalize-status', '', 'info');

    } catch (error) {
        showStatus('finalize-status', error.message, 'error');
    }
}

/**
 * Show status message
 */
function showStatus(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.className = `status show ${type}`;
}

/**
 * Check for available updates
 */
async function checkForUpdates() {
    try {
        const response = await fetch('/api/check-updates');
        if (!response.ok) throw new Error('Failed to check updates');
        
        const data = await response.json();
        
        if (data.success && data.has_update) {
            // Show update notification
            showUpdateNotification(data.latest_version, data.release_url, data.release_notes);
        }
    } catch (error) {
        console.log('[Updates] Could not check for updates:', error.message);
        // Silently fail - don't interrupt user experience
    }
}

/**
 * Display update notification banner
 */
function showUpdateNotification(latestVersion, releaseUrl, releaseNotes) {
    // Create or update the notification banner
    let banner = document.getElementById('update-notification');
    
    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'update-notification';
        banner.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 10000;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        `;
        document.body.insertBefore(banner, document.body.firstChild);
        
        // Adjust body margin to accommodate banner
        document.body.style.marginTop = '60px';
    }
    
    banner.innerHTML = `
        <div style="flex: 1;">
            <strong>Update Available!</strong> RUIE v${latestVersion} is now available.
            ${releaseNotes ? `<div style="font-size: 0.9em; margin-top: 4px; opacity: 0.9;">${releaseNotes}</div>` : ''}
        </div>
        <div style="display: flex; gap: 12px; margin-left: 16px;">
            <a href="${releaseUrl}" target="_blank" style="
                background: white;
                color: #667eea;
                padding: 8px 16px;
                border-radius: 4px;
                text-decoration: none;
                font-weight: 600;
                font-size: 0.9em;
                cursor: pointer;
                border: none;
                transition: all 0.2s;
            " onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">
                Download
            </a>
            <button onclick="document.getElementById('update-notification').style.display='none'; document.body.style.marginTop='0';" style="
                background: rgba(255,255,255,0.2);
                color: white;
                border: 1px solid rgba(255,255,255,0.4);
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                font-weight: 500;
                font-size: 0.9em;
                transition: all 0.2s;
            " onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'">
                Dismiss
            </button>
        </div>
    `;
}

window.addEventListener('load', () => { console.log('[EVENT] window load event fired'); startApp(); });
document.addEventListener('DOMContentLoaded', () => { console.log('[EVENT] DOMContentLoaded event fired'); startApp(); });

window.addEventListener('beforeunload', () => {
    stopListPolling();
});

// Also run immediately if DOM is already ready
if (document.readyState === 'loading') {
    // DOM is still loading, wait for DOMContentLoaded
    console.log('[app.js] DOM still loading, waiting for DOMContentLoaded');
} else {
    // DOM is already loaded, run immediately
    console.log('[app.js] DOM already loaded, running immediately');
    startApp();
}

/**
 * Open Update Manager window
 */
function openUpdateManager() {
    console.log('[APP] openUpdateManager called');
    try {
        fetch('/api/update-manager', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        })
            .then(r => r.json())
            .then(data => {
                console.log('[APP] Update manager data:', data);
                if (data.success) {
                    // Create a modal dialog for update manager
                    const modalHtml = `
                        <div id="update-modal" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10000; display: flex; align-items: center; justify-content: center;">
                            <div style="background: #0a1d29; border: 2px solid #00d4ff; border-radius: 8px; padding: 30px; max-width: 600px; max-height: 80vh; overflow-y: auto; color: #c0c8d0; font-family: Segoe UI, Arial, sans-serif;">
                                <h2 style="color: #00d4ff; margin-top: 0; margin-bottom: 20px;">⚙️ Update Manager</h2>
                                
                                <div style="background: #1a2a3a; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                                    <h3 style="color: #8db4d0; margin: 0 0 10px 0;">Current Version</h3>
                                    <p style="margin: 0; font-size: 1.1em;">${data.current_version || 'Unknown'}</p>
                                </div>
                                
                                <div style="background: #1a2a3a; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                                    <h3 style="color: #8db4d0; margin: 0 0 10px 0;">Latest Available Version</h3>
                                    <p style="margin: 0; font-size: 1.1em;">${data.latest_version || 'Checking...'}</p>
                                    ${data.update_available ? '<p style="color: #64c864; margin: 10px 0 0 0;">✓ Update available!</p>' : '<p style="color: #7a8a9a; margin: 10px 0 0 0;">You are up to date.</p>'}
                                </div>
                                
                                <div style="background: #1a2a3a; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                                    <h3 style="color: #8db4d0; margin: 0 0 10px 0;">Application Info</h3>
                                    <p style="margin: 5px 0;">Build: ${data.build_type || 'Unknown'}</p>
                                    <p style="margin: 5px 0;">Python: ${data.python_version || 'Unknown'}</p>
                                    <p style="margin: 5px 0;">Platform: Windows</p>
                                </div>
                                
                                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                                    <button onclick="closeUpdateModal()" class="btn btn-secondary" style="padding: 8px 16px;">Close</button>
                                    ${data.update_available ? '<button onclick="downloadUpdate()" class="btn btn-primary" style="padding: 8px 16px;">📥 Download Update</button>' : ''}
                                </div>
                            </div>
                        </div>
                    `;
                    
                    // Remove existing modal if any
                    const existing = document.getElementById('update-modal');
                    if (existing) existing.remove();
                    
                    // Add modal to body
                    document.body.insertAdjacentHTML('beforeend', modalHtml);
                } else {
                    alert('Error loading update manager: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(err => {
                console.error('[APP] Update manager error:', err);
                alert('Error: ' + err.message);
            });
    } catch (err) {
        console.error('[APP] openUpdateManager error:', err);
        alert('Error: ' + err.message);
    }
}

/**
 * Close Update Manager modal
 */
function closeUpdateModal() {
    const modal = document.getElementById('update-modal');
    if (modal) modal.remove();
}

/**
 * Download and install update
 */
function downloadUpdate() {
    console.log('[APP] downloadUpdate called');
    try {
        fetch('/api/download-update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    alert('✓ Update downloaded! Please restart the application.');
                    closeUpdateModal();
                } else {
                    alert('Error downloading update: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(err => alert('Error: ' + err.message));
    } catch (err) {
        console.error('[APP] downloadUpdate error:', err);
        alert('Error: ' + err.message);
    }
}

async function startApp() {
    // Safety check - ensure we only run once
    const msg1 = '[startApp] ***** STARTING APPLICATION *****';
    console.log(msg1);
    sendDebugToServer(msg1);
    console.log('[startApp] Called, window.appStarted =', window.appStarted);
    sendDebugToServer(`window.appStarted = ${window.appStarted}`);
    
    if (window.appStarted) {
        console.log('[startApp] Already started, returning');
        sendDebugToServer('startApp already started, returning');
        return;
    }
    
    console.log('[startApp] Setting window.appStarted = true');
    sendDebugToServer('Setting window.appStarted = true');
    window.appStarted = true;
    
    try {
        // Initialize DOM cache first for performance
        console.log('[startApp] Starting initialization');
        DOM.init();
        console.log('[startApp] DOM initialized, asarPath element:', DOM.asarPath);
        
        // Ensure Update Manager button is visible and functional
        console.log('[startApp] Checking Update Manager button...');
        const updateBtn = document.getElementById('update-manager-btn');
        const updateWrapper = document.getElementById('update-manager-wrapper');
        if (updateBtn) {
            console.log('[startApp] ✓ Update Manager button found');
            updateBtn.style.display = 'block';
            updateBtn.style.visibility = 'visible';
            updateBtn.style.opacity = '1';
            if (updateWrapper) {
                updateWrapper.style.display = 'flex';
                updateWrapper.style.visibility = 'visible';
                updateWrapper.style.opacity = '1';
            }
        } else {
            console.error('[startApp] ✗ Update Manager button NOT found');
            sendDebugToServer('ERROR: Update Manager button not found in DOM', 'ERROR');
        }
        
        // DEBUG: All debug output now goes to the separate debug console window
        // No on-screen debug display needed since we have a dedicated console
        const appendDebug = (msg) => { 
            // Send to server debug console instead of displaying on screen
            sendDebugToServer(msg, 'DEBUG');
            console.log('[DEBUG] ' + msg);
        };

        appendDebug('DOM initialized');
        console.log('[window.load] Navigating to page 1...');
        navigateToPage(1);
        appendDebug('Page navigation done');
        console.log('[window.load] Page navigation complete');
        
        // Load presets in background with timeout
        console.log('[window.load] Loading preset files...');
        Promise.race([
            loadPresetFiles(),
            new Promise((_, reject) => setTimeout(() => reject(new Error('Preset loading timeout')), 5000))
        ]).then(() => {
            appendDebug('Presets loaded');
            console.log('[window.load] Preset files loaded');
        }).catch((err) => {
            console.warn('[window.load] Preset loading failed, continuing anyway:', err.message);
            appendDebug('Warning: Preset loading timeout, continuing');
        });
        
        // Detect and initialize launcher FIRST
        console.log('[window.load] Calling detectLauncher...');
        appendDebug('Calling detectLauncher...');
        await detectLauncher({ autoInit: true, silentFailure: false });
        appendDebug('detectLauncher complete');
        appendDebug('asarPath value: ' + (DOM.asarPath?.value || 'EMPTY'));
        console.log('[window.load] detectLauncher complete, asarPath value:', DOM.asarPath?.value);
        
        // Load initial backups list (only after launcher is detected)
        try {
            console.log('[window.load] Loading backups...');
            appendDebug('Loading backups...');
            await loadBackupsList();
            appendDebug('Backups loaded');
            console.log('[window.load] Backups loaded');
        } catch (e) {
            appendDebug('Backup error: ' + e.message);
            console.warn('[window.load] Error loading backups:', e);
        }

        // Load initial extracted list
        try {
            console.log('[window.load] Loading extractions...');
            appendDebug('Loading extractions...');
            await loadExtractedASARList();
            appendDebug('Extractions loaded');
            console.log('[window.load] Extractions loaded');
        } catch (e) {
            appendDebug('Extraction error: ' + e.message);
            console.warn('[window.load] Error loading extractions:', e);
        }

        // Start real-time polling for backups/extractions
        startListPolling(5000);
        
        // Load extracted ASAR list (only after launcher is detected)
        try {
            console.log('[window.load] Loading extracted ASARs...');
            appendDebug('Loading extracted ASARs...');
            await loadExtractedASARList();
            appendDebug('Extracted ASARs loaded');
            console.log('[window.load] Extracted ASARs loaded');
        } catch (e) {
            appendDebug('Extracted ASAR error: ' + e.message);
            console.warn('[window.load] Error loading extracted ASARs:', e);
        }
        
        // CRITICAL: Attach button event listeners
        console.log('[startApp] Attaching button event listeners...');
        
        // Extract/Decompile ASAR button
        const extractBtn = document.getElementById('extract-btn');
        if (extractBtn) {
            extractBtn.addEventListener('click', extractAsar);
            console.log('[startApp] ✓ Extract button listener attached');
        } else {
            console.warn('[startApp] ✗ Extract button not found');
        }
        
        // Next button (each page)
        const nextButtons = document.querySelectorAll('[id^="next-"]');
        nextButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const currentPage = parseInt(this.id.split('-')[1]);
                navigateToPage(currentPage + 1);
            });
        });
        console.log(`[startApp] ✓ Attached ${nextButtons.length} next buttons`);
        
        // Previous button (each page)
        const prevButtons = document.querySelectorAll('[id^="prev-"]');
        prevButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const currentPage = parseInt(this.id.split('-')[1]);
                navigateToPage(currentPage - 1);
            });
        });
        console.log(`[startApp] ✓ Attached ${prevButtons.length} previous buttons`);
        
        // Color preset buttons
        const presetButtons = document.querySelectorAll('[data-preset-id]');
        presetButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const presetId = this.getAttribute('data-preset-id');
                if (presetId && colorPresets[presetId]) {
                    state.colors = { ...colorPresets[presetId].colors };
                    renderColorMappings();
                }
            });
        });
        console.log(`[startApp] ✓ Attached ${presetButtons.length} color preset buttons`);
        
        // Check for updates asynchronously (non-blocking)
        setTimeout(() => {
            checkForUpdates();
        }, 2000); // Wait 2 seconds after app loads
        
        // Check for updates every 24 hours
        setInterval(checkForUpdates, 24 * 60 * 60 * 1000);
        
        appendDebug('✓ Application fully initialized');
        console.log('[startApp] Application fully initialized successfully');
        
    } catch (error) {
        console.error('[startApp] FATAL ERROR:', error);
        console.error('[startApp] Stack:', error.stack);
        // Try to display error in debug element if it exists
        if (document.getElementById('debug-info')) {
            document.getElementById('debug-info').innerHTML = 'CRITICAL ERROR: ' + error.message;
        }
        throw error;  // Re-throw so caller knows there was an error
    }
}
