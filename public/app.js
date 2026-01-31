// Global state
const state = {
    initialized: false,
    extracted: false,
    colors: {}, // Will be initialized with rsiOriginal after presets are defined
    media: {},
    music: [], // Array of music files: [{ name: 'track1.ogg', file: File }, ...]
    config: {
        name: 'My Theme',
        colors: {},
        media: {},
        music: []
    },
    currentPage: 1
};

// Persisted preview state for syncing across steps/iframes
const previewState = {
    colors: {},
    media: {}
};

// DOM element cache for performance
const DOM = {
    pages: null,
    stepperSteps: null,
    previewFrame: null,
    asarPath: null,
    extractProgress: null,
    extractProgressBar: null,
    extractProgressText: null,
    extractBtn: null,
    extractStatus: null,
    extractSelect: null,
    initStatus: null,
    colorList: null,
    backBtn: null,
    nextBtn: null,
    init() {
        this.pages = document.querySelectorAll('.page');
        this.stepperSteps = document.querySelectorAll('.stepper-step');
        this.previewFrame = document.getElementById('previewFrame');
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

        // Sync preview state when any preview iframe loads
        const frames = document.querySelectorAll('.preview-frame');
        frames.forEach((frame) => {
            frame.addEventListener('load', () => {
                sendPreviewStateToFrame(frame);
            });
        });
    }
};

// Debounce helper for performance
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

// Page navigation system
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
        
        // Render color mappings when navigating to colors page
        if (pageNumber === 3) {
            // Show loading message
            const colorList = document.getElementById('colorList');
            if (colorList) {
                colorList.innerHTML = '<div style="padding: 20px; text-align: center; color: #888;">Loading color palette...</div>';
            }
            // Render after UI updates and update preview
            setTimeout(() => {
                renderColorMappings();
                // Update preview with current colors from UI
                const colors = collectColorMappings();
                if (Object.keys(colors).length > 0) {
                    updatePreviewFromColors(colors);
                }
            }, 50);
        }
        
        // Load media assets when navigating to media page
        if (pageNumber === 4) {
            if (lastMediaAssets.length === 0) {
                loadDefaultMediaAssets();
            }
            // Colors already synced via sendPreviewStateToFrame at top of function
        }
        
        // Initialize music list when navigating to music page
        if (pageNumber === 5) {
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
    DOM.nextBtn.style.display = currentPage < 6 ? 'block' : 'none';
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
    const wheelHidden = item.querySelector('.color-wheel-hidden');
    const newInput = item.querySelector('.new-color');
    const hexInput = item.querySelector('.hex-input');
    const rgbInput = item.querySelector('.rgb-input');
    const colorPickerButton = item.querySelector('.color-picker-button');

    const updateAllFields = (hex) => {
        if (hexInput) hexInput.value = hex;
        if (rgbInput) rgbInput.value = hexToRGB(hex);
        if (wheelHidden) wheelHidden.value = hex;
        if (newInput) newInput.value = hex;
        updatePreviewFromUi();
    };

    // Handle color wheel (hidden input)
    if (wheelHidden) {
        wheelHidden.addEventListener('input', (event) => {
            updateAllFields(event.target.value);
        });
    }

    // Handle hex input
    if (hexInput) {
        hexInput.addEventListener('input', () => {
            let hex = hexInput.value.trim();
            // Auto-format if user types without #
            if (hex && !hex.startsWith('#')) {
                hex = '#' + hex;
            }
            // Validate hex format
            if (hex.length === 7 && /^#[0-9A-Fa-f]{6}$/.test(hex)) {
                updateAllFields(hex.toUpperCase());
            }
        });

        hexInput.addEventListener('blur', () => {
            const hex = hexInput.value.trim();
            if (!hex || !hex.startsWith('#') || hex.length !== 7) {
                // Reset to current color on invalid input
                if (wheelHidden && wheelHidden.value) {
                    updateAllFields(wheelHidden.value);
                }
            }
        });
    }

    // Handle RGB input
    if (rgbInput) {
        rgbInput.addEventListener('input', () => {
            const rgb = rgbInput.value.trim();
            if (rgb) {
                const hex = rgbToHex(rgb);
                if (hex) {
                    updateAllFields(hex);
                }
            }
        });

        rgbInput.addEventListener('blur', () => {
            const rgb = rgbInput.value.trim();
            if (rgb) {
                const hex = rgbToHex(rgb);
                if (!hex) {
                    // Reset to current color on invalid input
                    if (wheelHidden && wheelHidden.value) {
                        updateAllFields(wheelHidden.value);
                    }
                }
            }
        });
    }

    // Handle color picker button
    if (colorPickerButton) {
        colorPickerButton.addEventListener('click', (event) => {
            openColorPicker(event);
        });
    }

    // Handle main new-color input
    if (newInput) {
        newInput.addEventListener('input', () => {
            const normalized = normalizeColorToHex(newInput.value);
            if (normalized) {
                updateAllFields(normalized);
            } else {
                updatePreviewFromUi();
            }
        });
    }
}

// Color presets
// RSI Original - actual RSI Launcher default colors
const rsiOriginal = {
    '--sol-color-primary-1': '#071a25',
    '--sol-color-primary-1-rgb': '7 26 37',
    '--sol-color-primary-2': '#0a1f2e',
    '--sol-color-primary-2-rgb': '10 31 46',
    '--sol-color-primary-3': '#0d2536',
    '--sol-color-primary-3-rgb': '13 37 54',
    '--sol-color-primary-4': '#102a3e',
    '--sol-color-primary-4-rgb': '16 42 62',
    '--sol-color-primary-5': '#133047',
    '--sol-color-primary-5-rgb': '19 48 71',
    '--sol-color-primary-6': '#16354f',
    '--sol-color-primary-6-rgb': '22 53 79',
    '--sol-color-primary-7': '#54adf7',
    '--sol-color-primary-7-rgb': '84 173 247',
    '--sol-color-primary-8': '#8fc7f9',
    '--sol-color-primary-8-rgb': '143 199 249',
    '--sol-color-neutral-1': '#091219',
    '--sol-color-neutral-1-rgb': '9 18 25',
    '--sol-color-neutral-2': '#334048',
    '--sol-color-neutral-2-rgb': '51 64 72',
    '--sol-color-neutral-3': '#9fb1bf',
    '--sol-color-neutral-3-rgb': '159 177 191',
    '--sol-color-neutral-4': '#edf2f5',
    '--sol-color-neutral-4-rgb': '237 242 245',
    '--sol-color-accent-1': '#54adf7',
    '--sol-color-accent-1-rgb': '84 173 247',
    '--sol-color-accent-2': '#41a1f5',
    '--sol-color-accent-2-rgb': '65 161 245',
    '--sol-color-accent-3': '#6db9f8',
    '--sol-color-accent-3-rgb': '109 185 248',
    '--sol-color-positive-1': '#4caf50',
    '--sol-color-positive-1-rgb': '76 175 80',
    '--sol-color-positive-2': '#66bb6a',
    '--sol-color-positive-2-rgb': '102 187 106',
    '--sol-color-positive-3': '#81c784',
    '--sol-color-positive-3-rgb': '129 199 132',
    '--sol-color-notice-1': '#ff9800',
    '--sol-color-notice-1-rgb': '255 152 0',
    '--sol-color-notice-2': '#ffa726',
    '--sol-color-notice-2-rgb': '255 167 38',
    '--sol-color-notice-3': '#ffb74d',
    '--sol-color-notice-3-rgb': '255 183 77',
    '--sol-color-negative-1': '#f44336',
    '--sol-color-negative-1-rgb': '244 67 54',
    '--sol-color-negative-2': '#e57373',
    '--sol-color-negative-2-rgb': '229 115 115',
    '--sol-color-negative-3': '#ef5350',
    '--sol-color-negative-3-rgb': '239 83 80',
    '--sol-color-highlight-1': '#9c27b0',
    '--sol-color-highlight-1-rgb': '156 39 176',
    '--sol-color-highlight-2': '#ab47bc',
    '--sol-color-highlight-2-rgb': '171 71 188',
    '--sol-color-highlight-3': '#ba68c8',
    '--sol-color-highlight-3-rgb': '186 104 200',
    '--sol-color-background': 'var(--sol-color-primary-1)',
    '--sol-color-focused': 'var(--sol-color-primary-7)',
    '--sol-color-overlay': 'rgba(var(--sol-color-neutral-1-rgb)/0.7)',
    '--sol-color-surface-0': 'var(--sol-color-primary-1)',
    '--sol-color-surface-1': 'var(--sol-color-primary-2)',
    '--sol-color-surface-2': 'var(--sol-color-primary-3)',
    '--sol-color-surface-3': 'var(--sol-color-primary-4)',
    '--sol-color-surface-0-hovered': 'var(--sol-color-primary-2)',
    '--sol-color-surface-0-pressed': 'var(--sol-color-primary-3)',
    '--sol-color-surface-1-hovered': 'var(--sol-color-primary-3)',
    '--sol-color-surface-1-pressed': 'var(--sol-color-primary-4)',
    '--sol-color-surface-2-hovered': 'var(--sol-color-primary-4)',
    '--sol-color-surface-2-pressed': 'var(--sol-color-primary-5)',
    '--sol-color-surface-3-hovered': 'var(--sol-color-primary-5)',
    '--sol-color-surface-3-pressed': 'var(--sol-color-primary-6)',
    '--sol-color-interactive': 'var(--sol-color-accent-1)',
    '--sol-color-interactive-hovered': 'var(--sol-color-accent-3)',
    '--sol-color-interactive-pressed': 'var(--sol-color-accent-2)',
    '--sol-color-interactive-selected': 'var(--sol-color-neutral-4)',
    '--sol-color-interactive-contrast': 'var(--sol-color-neutral-1)',
    '--sol-color-interactive-opacity': 'rgba(var(--sol-color-neutral-1-rgb)/0)',
    '--sol-color-interactive-opacity-hovered': 'rgba(var(--sol-color-neutral-1-rgb)/0.4)',
    '--sol-color-interactive-opacity-pressed': 'rgba(var(--sol-color-neutral-1-rgb)/0.4)',
    '--sol-color-interactive-opacity-selected': 'rgba(var(--sol-color-neutral-1-rgb)/0.6)',
    '--sol-color-interactive-negative': 'var(--sol-color-negative-1)',
    '--sol-color-interactive-negative-hovered': 'var(--sol-color-negative-3)',
    '--sol-color-interactive-negative-pressed': 'var(--sol-color-negative-2)',
    '--sol-color-interactive-negative-selected': 'var(--sol-color-neutral-4)',
    '--sol-color-interactive-notice': 'var(--sol-color-notice-1)',
    '--sol-color-interactive-notice-hovered': 'var(--sol-color-notice-3)',
    '--sol-color-interactive-notice-pressed': 'var(--sol-color-notice-2)',
    '--sol-color-interactive-notice-selected': 'var(--sol-color-neutral-4)',
    '--sol-color-interactive-positive': 'var(--sol-color-positive-1)',
    '--sol-color-interactive-positive-hovered': 'var(--sol-color-positive-3)',
    '--sol-color-interactive-positive-pressed': 'var(--sol-color-positive-2)',
    '--sol-color-interactive-positive-selected': 'var(--sol-color-neutral-4)',
    '--sol-color-interactive-neutral': 'var(--sol-color-neutral-4)',
    '--sol-color-interactive-neutral-hovered': 'var(--sol-color-neutral-4)',
    '--sol-color-interactive-neutral-pressed': 'var(--sol-color-neutral-3)',
    '--sol-color-interactive-neutral-selected': 'var(--sol-color-neutral-4)',
    '--sol-color-interactive-weak-default': 'var(--sol-color-primary-4)',
    '--sol-color-interactive-weak-hover': 'var(--sol-color-primary-5)',
    '--sol-color-interactive-weak-pressed': 'var(--sol-color-primary-6)',
    '--sol-color-interactive-weak-selected': 'var(--sol-color-neutral-4)',
    '--sol-color-status-informative': 'var(--sol-color-primary-7)',
    '--sol-color-status-informative-fill': 'var(--sol-color-primary-6)',
    '--sol-color-status-informative-fill-contrast': 'var(--sol-color-neutral-4)',
    '--sol-color-status-positive': 'var(--sol-color-positive-2)',
    '--sol-color-status-positive-fill': 'var(--sol-color-positive-1)',
    '--sol-color-status-positive-fill-contrast': 'var(--sol-color-neutral-1)',
    '--sol-color-status-notice': 'var(--sol-color-notice-3)',
    '--sol-color-status-notice-fill': 'var(--sol-color-notice-1)',
    '--sol-color-status-notice-fill-contrast': 'var(--sol-color-neutral-1)',
    '--sol-color-status-negative': 'var(--sol-color-negative-3)',
    '--sol-color-status-negative-fill': 'var(--sol-color-negative-1)',
    '--sol-color-status-negative-fill-contrast': 'var(--sol-color-neutral-1)',
    '--sol-color-status-highlight': 'var(--sol-color-highlight-3)',
    '--sol-color-status-highlight-fill': 'var(--sol-color-highlight-1)',
    '--sol-color-status-highlight-fill-contrast': 'var(--sol-color-neutral-1)',
    '--sol-color-status-neutral': 'var(--sol-color-neutral-3)',
    '--sol-color-status-neutral-fill': 'var(--sol-color-neutral-2)',
    '--sol-color-status-neutral-fill-contrast': 'var(--sol-color-neutral-4)',
    '--sol-color-foreground': 'var(--sol-color-neutral-4)',
    '--sol-color-foreground-weak': 'var(--sol-color-primary-8)',
    '--sol-color-foreground-weaker': 'var(--sol-color-neutral-3)',
    '--sol-color-foreground-highlight': 'var(--sol-color-primary-7)'
};

// C3RB - Custom dark red theme
const c3rbBaseline = {
    '--sol-color-primary-1': '#1f1f1f',
    '--sol-color-primary-1-rgb': '31 31 31',
    '--sol-color-primary-2': '#212121',
    '--sol-color-primary-2-rgb': '33 33 33',
    '--sol-color-primary-3': '#521414',
    '--sol-color-primary-3-rgb': '82 20 20',
    '--sol-color-primary-4': '#671919',
    '--sol-color-primary-4-rgb': '103 25 25',
    '--sol-color-primary-5': '#ffffff',
    '--sol-color-primary-5-rgb': '255 255 255',
    '--sol-color-primary-6': '#a42828',
    '--sol-color-primary-6-rgb': '164 40 40',
    '--sol-color-primary-7': '#dc6f6f',
    '--sol-color-primary-7-rgb': '220 111 111',
    '--sol-color-primary-8': '#ebadad',
    '--sol-color-primary-8-rgb': '235 173 173',
    '--sol-color-neutral-1': '#000',
    '--sol-color-neutral-1-rgb': '0 0 0',
    '--sol-color-neutral-2': '#6e6e6e',
    '--sol-color-neutral-2-rgb': '110 110 110',
    '--sol-color-neutral-3': '#c0b0b0',
    '--sol-color-neutral-3-rgb': '192 176 176',
    '--sol-color-neutral-4': '#fff',
    '--sol-color-neutral-4-rgb': '255 255 255',
    '--sol-color-accent-1': '#ff0000',
    '--sol-color-accent-1-rgb': '255 0 0',
    '--sol-color-accent-2': '#ff0000',
    '--sol-color-accent-2-rgb': '255 0 0',
    '--sol-color-accent-3': '#fa9e9e',
    '--sol-color-accent-3-rgb': '250 158 158',
    '--sol-color-positive-1': '#85c6a2',
    '--sol-color-positive-1-rgb': '133 198 162',
    '--sol-color-positive-2': '#a8d6bd',
    '--sol-color-positive-2-rgb': '168 214 189',
    '--sol-color-positive-3': '#cbe7d8',
    '--sol-color-positive-3-rgb': '203 231 216',
    '--sol-color-notice-1': '#e99449',
    '--sol-color-notice-1-rgb': '233 148 73',
    '--sol-color-notice-2': '#eeaf77',
    '--sol-color-notice-2-rgb': '238 175 119',
    '--sol-color-notice-3': '#f4c9a4',
    '--sol-color-notice-3-rgb': '244 201 164',
    '--sol-color-negative-1': '#80aaff',
    '--sol-color-negative-1-rgb': '128 170 255',
    '--sol-color-negative-2': '#f99',
    '--sol-color-negative-2-rgb': '255 153 153',
    '--sol-color-negative-3': '#ffb3b3',
    '--sol-color-negative-3-rgb': '255 179 179',
    '--sol-color-highlight-1': '#8186e4',
    '--sol-color-highlight-1-rgb': '129 134 228',
    '--sol-color-highlight-2': '#abafed',
    '--sol-color-highlight-2-rgb': '171 175 237',
    '--sol-color-highlight-3': '#d5d7f6',
    '--sol-color-highlight-3-rgb': '213 215 246',
    '--sol-color-background': 'var(--sol-color-primary-1)',
    '--sol-color-focused': 'var(--sol-color-primary-7)',
    '--sol-color-overlay': 'rgba(var(--sol-color-neutral-1-rgb)/0.7)',
    '--sol-color-surface-0': 'var(--sol-color-primary-1)',
    '--sol-color-surface-1': 'var(--sol-color-primary-2)',
    '--sol-color-surface-2': 'var(--sol-color-primary-3)',
    '--sol-color-surface-3': 'var(--sol-color-primary-4)',
    '--sol-color-surface-0-hovered': 'var(--sol-color-primary-2)',
    '--sol-color-surface-0-pressed': 'var(--sol-color-primary-3)',
    '--sol-color-surface-1-hovered': 'var(--sol-color-primary-3)',
    '--sol-color-surface-1-pressed': 'var(--sol-color-primary-4)',
    '--sol-color-surface-2-hovered': 'var(--sol-color-primary-4)',
    '--sol-color-surface-2-pressed': 'var(--sol-color-primary-5)',
    '--sol-color-surface-3-hovered': 'var(--sol-color-primary-5)',
    '--sol-color-surface-3-pressed': 'var(--sol-color-primary-6)',
    '--sol-color-interactive': 'var(--sol-color-accent-1)',
    '--sol-color-interactive-hovered': 'var(--sol-color-accent-3)',
    '--sol-color-interactive-pressed': 'var(--sol-color-accent-2)',
    '--sol-color-interactive-selected': 'var(--sol-color-neutral-4)',
    '--sol-color-interactive-contrast': 'var(--sol-color-neutral-1)',
    '--sol-color-interactive-opacity': 'rgba(var(--sol-color-neutral-1-rgb)/0)',
    '--sol-color-interactive-opacity-hovered': 'rgba(var(--sol-color-neutral-1-rgb)/0.4)',
    '--sol-color-interactive-opacity-pressed': 'rgba(var(--sol-color-neutral-1-rgb)/0.4)',
    '--sol-color-interactive-opacity-selected': 'rgba(var(--sol-color-neutral-1-rgb)/0.6)',
    '--sol-color-interactive-negative': 'var(--sol-color-negative-1)',
    '--sol-color-interactive-negative-hovered': 'var(--sol-color-negative-3)',
    '--sol-color-interactive-negative-pressed': 'var(--sol-color-negative-2)',
    '--sol-color-interactive-negative-selected': 'var(--sol-color-neutral-4)',
    '--sol-color-interactive-notice': 'var(--sol-color-notice-1)',
    '--sol-color-interactive-notice-hovered': 'var(--sol-color-notice-3)',
    '--sol-color-interactive-notice-pressed': 'var(--sol-color-notice-2)',
    '--sol-color-interactive-notice-selected': 'var(--sol-color-neutral-4)',
    '--sol-color-interactive-positive': 'var(--sol-color-positive-1)',
    '--sol-color-interactive-positive-hovered': 'var(--sol-color-positive-3)',
    '--sol-color-interactive-positive-pressed': 'var(--sol-color-positive-2)',
    '--sol-color-interactive-positive-selected': 'var(--sol-color-neutral-4)',
    '--sol-color-interactive-neutral': 'var(--sol-color-neutral-4)',
    '--sol-color-interactive-neutral-hovered': 'var(--sol-color-neutral-4)',
    '--sol-color-interactive-neutral-pressed': 'var(--sol-color-neutral-3)',
    '--sol-color-interactive-neutral-selected': 'var(--sol-color-neutral-4)',
    '--sol-color-interactive-weak-default': 'var(--sol-color-primary-4)',
    '--sol-color-interactive-weak-hover': 'var(--sol-color-primary-5)',
    '--sol-color-interactive-weak-pressed': 'var(--sol-color-primary-6)',
    '--sol-color-interactive-weak-selected': 'var(--sol-color-neutral-4)',
    '--sol-color-status-informative': 'var(--sol-color-primary-7)',
    '--sol-color-status-informative-fill': 'var(--sol-color-primary-6)',
    '--sol-color-status-informative-fill-contrast': 'var(--sol-color-neutral-4)',
    '--sol-color-status-positive': 'var(--sol-color-positive-2)',
    '--sol-color-status-positive-fill': 'var(--sol-color-positive-1)',
    '--sol-color-status-positive-fill-contrast': 'var(--sol-color-neutral-1)',
    '--sol-color-status-notice': 'var(--sol-color-notice-3)',
    '--sol-color-status-notice-fill': 'var(--sol-color-notice-1)',
    '--sol-color-status-notice-fill-contrast': 'var(--sol-color-neutral-1)',
    '--sol-color-status-negative': 'var(--sol-color-negative-3)',
    '--sol-color-status-negative-fill': 'var(--sol-color-negative-1)',
    '--sol-color-status-negative-fill-contrast': 'var(--sol-color-neutral-1)',
    '--sol-color-status-highlight': 'var(--sol-color-highlight-3)',
    '--sol-color-status-highlight-fill': 'var(--sol-color-highlight-1)',
    '--sol-color-status-highlight-fill-contrast': 'var(--sol-color-neutral-1)',
    '--sol-color-status-neutral': 'var(--sol-color-neutral-3)',
    '--sol-color-status-neutral-fill': 'var(--sol-color-neutral-2)',
    '--sol-color-status-neutral-fill-contrast': 'var(--sol-color-neutral-4)',
    '--sol-color-foreground': 'var(--sol-color-neutral-4)',
    '--sol-color-foreground-weak': 'var(--sol-color-primary-8)',
    '--sol-color-foreground-weaker': 'var(--sol-color-neutral-3)',
    '--sol-color-foreground-highlight': 'var(--sol-color-primary-7)'
};

const colorPresets = {
    'rsi': {
        colors: rsiOriginal,
        media: {
            logo: 'assets/logos/cig-logo.svg',
            background: 'assets/images/sc_bg_fallback.jpg'
        }
    },
    'aegis-dynamics': {
        colors: {
            ...rsiOriginal,
            '--sol-color-primary-1': '#040810',
            '--sol-color-primary-1-rgb': '4 8 16',
            '--sol-color-primary-2': '#060c18',
            '--sol-color-primary-2-rgb': '6 12 24',
            '--sol-color-primary-3': '#0a1220',
            '--sol-color-primary-3-rgb': '10 18 32',
            '--sol-color-primary-4': '#0e1a2e',
            '--sol-color-primary-4-rgb': '14 26 46',
            '--sol-color-primary-6': '#16273d',
            '--sol-color-primary-6-rgb': '22 39 61',
            '--sol-color-primary-7': '#4169a8',
            '--sol-color-primary-7-rgb': '65 105 168',
            '--sol-color-primary-8': '#6b8bc3',
            '--sol-color-primary-8-rgb': '107 139 195',
            '--sol-color-accent-1': '#2e5090',
            '--sol-color-accent-1-rgb': '46 80 144',
            '--sol-color-accent-2': '#1f3a70',
            '--sol-color-accent-2-rgb': '31 58 112',
            '--sol-color-accent-3': '#5578b0',
            '--sol-color-accent-3-rgb': '85 120 176'
        },
        media: {
            logo: 'assets/logos/cig-logo.svg',
            background: 'assets/images/sc_bg_fallback.jpg'
        }
    },
    'anvil-aerospace': {
        colors: {
            ...rsiOriginal,
            '--sol-color-primary-1': '#1a1c1e',
            '--sol-color-primary-1-rgb': '26 28 30',
            '--sol-color-primary-2': '#22252a',
            '--sol-color-primary-2-rgb': '34 37 42',
            '--sol-color-primary-3': '#2a2e34',
            '--sol-color-primary-3-rgb': '42 46 52',
            '--sol-color-primary-4': '#35393f',
            '--sol-color-primary-4-rgb': '53 57 63',
            '--sol-color-primary-6': '#4a5058',
            '--sol-color-primary-6-rgb': '74 80 88',
            '--sol-color-primary-7': '#e84a1f',
            '--sol-color-primary-7-rgb': '232 74 31',
            '--sol-color-primary-8': '#ff6b35',
            '--sol-color-primary-8-rgb': '255 107 53',
            '--sol-color-accent-1': '#d14520',
            '--sol-color-accent-1-rgb': '209 69 32',
            '--sol-color-accent-2': '#b83818',
            '--sol-color-accent-2-rgb': '184 56 24',
            '--sol-color-accent-3': '#ff7f4f',
            '--sol-color-accent-3-rgb': '255 127 79'
        },
        media: {
            logo: 'assets/logos/cig-logo.svg',
            background: 'assets/images/sc_bg_fallback.jpg'
        }
    },
    'origin-jumpworks': {
        colors: {
            ...rsiOriginal,
            '--sol-color-primary-1': '#0c1520',
            '--sol-color-primary-1-rgb': '12 21 32',
            '--sol-color-primary-2': '#10212e',
            '--sol-color-primary-2-rgb': '16 33 46',
            '--sol-color-primary-3': '#162e42',
            '--sol-color-primary-3-rgb': '22 46 66',
            '--sol-color-primary-4': '#1c3a54',
            '--sol-color-primary-4-rgb': '28 58 84',
            '--sol-color-primary-6': '#2a5478',
            '--sol-color-primary-6-rgb': '42 84 120',
            '--sol-color-primary-7': '#00d4ff',
            '--sol-color-primary-7-rgb': '0 212 255',
            '--sol-color-primary-8': '#6ee7ff',
            '--sol-color-primary-8-rgb': '110 231 255',
            '--sol-color-accent-1': '#00bfea',
            '--sol-color-accent-1-rgb': '0 191 234',
            '--sol-color-accent-2': '#0099cc',
            '--sol-color-accent-2-rgb': '0 153 204',
            '--sol-color-accent-3': '#66e0ff',
            '--sol-color-accent-3-rgb': '102 224 255'
        },
        media: {
            logo: 'assets/logos/cig-logo.svg',
            background: 'assets/images/sc_bg_fallback.jpg'
        }
    },
    'drake-interplanetary': {
        colors: {
            ...rsiOriginal,
            '--sol-color-primary-1': '#0d0d0a',
            '--sol-color-primary-1-rgb': '13 13 10',
            '--sol-color-primary-2': '#141410',
            '--sol-color-primary-2-rgb': '20 20 16',
            '--sol-color-primary-3': '#1a1a14',
            '--sol-color-primary-3-rgb': '26 26 20',
            '--sol-color-primary-4': '#23231c',
            '--sol-color-primary-4-rgb': '35 35 28',
            '--sol-color-primary-6': '#3a3a2e',
            '--sol-color-primary-6-rgb': '58 58 46',
            '--sol-color-primary-7': '#f5b800',
            '--sol-color-primary-7-rgb': '245 184 0',
            '--sol-color-primary-8': '#ffd133',
            '--sol-color-primary-8-rgb': '255 209 51',
            '--sol-color-accent-1': '#e6a500',
            '--sol-color-accent-1-rgb': '230 165 0',
            '--sol-color-accent-2': '#cc8800',
            '--sol-color-accent-2-rgb': '204 136 0',
            '--sol-color-accent-3': '#ffc933',
            '--sol-color-accent-3-rgb': '255 201 51'
        },
        media: {
            logo: 'assets/logos/cig-logo.svg',
            background: 'assets/images/sc_bg_fallback.jpg'
        }
    },
    'crusader-industries': {
        colors: {
            ...rsiOriginal,
            '--sol-color-primary-1': '#0a1419',
            '--sol-color-primary-1-rgb': '10 20 25',
            '--sol-color-primary-2': '#0e1e26',
            '--sol-color-primary-2-rgb': '14 30 38',
            '--sol-color-primary-3': '#14282f',
            '--sol-color-primary-3-rgb': '20 40 47',
            '--sol-color-primary-4': '#1a3641',
            '--sol-color-primary-4-rgb': '26 54 65',
            '--sol-color-primary-6': '#265968',
            '--sol-color-primary-6-rgb': '38 89 104',
            '--sol-color-primary-7': '#10d9c5',
            '--sol-color-primary-7-rgb': '16 217 197',
            '--sol-color-primary-8': '#5ce8d8',
            '--sol-color-primary-8-rgb': '92 232 216',
            '--sol-color-accent-1': '#0ec4b0',
            '--sol-color-accent-1-rgb': '14 196 176',
            '--sol-color-accent-2': '#0a9e8a',
            '--sol-color-accent-2-rgb': '10 158 138',
            '--sol-color-accent-3': '#7ff0e0',
            '--sol-color-accent-3-rgb': '127 240 224'
        },
        media: {
            logo: 'assets/logos/cig-logo.svg',
            background: 'assets/images/sc_bg_fallback.jpg'
        }
    },
    'misc': {
        colors: {
            ...rsiOriginal,
            '--sol-color-primary-1': '#0f1208',
            '--sol-color-primary-1-rgb': '15 18 8',
            '--sol-color-primary-2': '#14180d',
            '--sol-color-primary-2-rgb': '20 24 13',
            '--sol-color-primary-3': '#1a2012',
            '--sol-color-primary-3-rgb': '26 32 18',
            '--sol-color-primary-4': '#23291a',
            '--sol-color-primary-4-rgb': '35 41 26',
            '--sol-color-primary-6': '#3a4228',
            '--sol-color-primary-6-rgb': '58 66 40',
            '--sol-color-primary-7': '#9fdf3f',
            '--sol-color-primary-7-rgb': '159 223 63',
            '--sol-color-primary-8': '#bef55e',
            '--sol-color-primary-8-rgb': '190 245 94',
            '--sol-color-accent-1': '#8bc832',
            '--sol-color-accent-1-rgb': '139 200 50',
            '--sol-color-accent-2': '#6ea326',
            '--sol-color-accent-2-rgb': '110 163 38',
            '--sol-color-accent-3': '#c4f76f',
            '--sol-color-accent-3-rgb': '196 247 111'
        },
        media: {
            logo: 'assets/logos/cig-logo.svg',
            background: 'assets/images/sc_bg_fallback.jpg'
        }
    },
    'consolidated-outland': {
        colors: {
            ...rsiOriginal,
            '--sol-color-primary-1': '#12100d',
            '--sol-color-primary-1-rgb': '18 16 13',
            '--sol-color-primary-2': '#1a1612',
            '--sol-color-primary-2-rgb': '26 22 18',
            '--sol-color-primary-3': '#221e19',
            '--sol-color-primary-3-rgb': '34 30 25',
            '--sol-color-primary-4': '#2d2820',
            '--sol-color-primary-4-rgb': '45 40 32',
            '--sol-color-primary-6': '#473f32',
            '--sol-color-primary-6-rgb': '71 63 50',
            '--sol-color-primary-7': '#ff8c42',
            '--sol-color-primary-7-rgb': '255 140 66',
            '--sol-color-primary-8': '#ffa666',
            '--sol-color-primary-8-rgb': '255 166 102',
            '--sol-color-accent-1': '#f57730',
            '--sol-color-accent-1-rgb': '245 119 48',
            '--sol-color-accent-2': '#d66225',
            '--sol-color-accent-2-rgb': '214 98 37',
            '--sol-color-accent-3': '#ffb580',
            '--sol-color-accent-3-rgb': '255 181 128'
        },
        media: {
            logo: 'assets/logos/cig-logo.svg',
            background: 'assets/images/sc_bg_fallback.jpg'
        }
    },
    'banu': {
        colors: {
            ...rsiOriginal,
            '--sol-color-primary-1': '#0d0a12',
            '--sol-color-primary-1-rgb': '13 10 18',
            '--sol-color-primary-2': '#140f1c',
            '--sol-color-primary-2-rgb': '20 15 28',
            '--sol-color-primary-3': '#1c1426',
            '--sol-color-primary-3-rgb': '28 20 38',
            '--sol-color-primary-4': '#261c33',
            '--sol-color-primary-4-rgb': '38 28 51',
            '--sol-color-primary-6': '#3d2b52',
            '--sol-color-primary-6-rgb': '61 43 82',
            '--sol-color-primary-7': '#a855f7',
            '--sol-color-primary-7-rgb': '168 85 247',
            '--sol-color-primary-8': '#c084fc',
            '--sol-color-primary-8-rgb': '192 132 252',
            '--sol-color-accent-1': '#9333ea',
            '--sol-color-accent-1-rgb': '147 51 234',
            '--sol-color-accent-2': '#7e22ce',
            '--sol-color-accent-2-rgb': '126 34 206',
            '--sol-color-accent-3': '#d8b4fe',
            '--sol-color-accent-3-rgb': '216 180 254'
        },
        media: {
            logo: 'assets/logos/cig-logo.svg',
            background: 'assets/images/sc_bg_fallback.jpg'
        }
    },
    'esperia': {
        colors: {
            ...rsiOriginal,
            '--sol-color-primary-1': '#0d100e',
            '--sol-color-primary-1-rgb': '13 16 14',
            '--sol-color-primary-2': '#141a16',
            '--sol-color-primary-2-rgb': '20 26 22',
            '--sol-color-primary-3': '#1b241f',
            '--sol-color-primary-3-rgb': '27 36 31',
            '--sol-color-primary-4': '#253029',
            '--sol-color-primary-4-rgb': '37 48 41',
            '--sol-color-primary-6': '#3a4a3f',
            '--sol-color-primary-6-rgb': '58 74 63',
            '--sol-color-primary-7': '#34d399',
            '--sol-color-primary-7-rgb': '52 211 153',
            '--sol-color-primary-8': '#6ee7b7',
            '--sol-color-primary-8-rgb': '110 231 183',
            '--sol-color-accent-1': '#10b981',
            '--sol-color-accent-1-rgb': '16 185 129',
            '--sol-color-accent-2': '#059669',
            '--sol-color-accent-2-rgb': '5 150 105',
            '--sol-color-accent-3': '#86efac',
            '--sol-color-accent-3-rgb': '134 239 172'
        },
        media: {
            logo: 'assets/logos/cig-logo.svg',
            background: 'assets/images/sc_bg_fallback.jpg'
        }
    },
    'kruger': {
        colors: {
            ...rsiOriginal,
            '--sol-color-primary-1': '#0f0d12',
            '--sol-color-primary-1-rgb': '15 13 18',
            '--sol-color-primary-2': '#17141c',
            '--sol-color-primary-2-rgb': '23 20 28',
            '--sol-color-primary-3': '#201c26',
            '--sol-color-primary-3-rgb': '32 28 38',
            '--sol-color-primary-4': '#2b2533',
            '--sol-color-primary-4-rgb': '43 37 51',
            '--sol-color-primary-6': '#453a52',
            '--sol-color-primary-6-rgb': '69 58 82',
            '--sol-color-primary-7': '#e879f9',
            '--sol-color-primary-7-rgb': '232 121 249',
            '--sol-color-primary-8': '#f0abfc',
            '--sol-color-primary-8-rgb': '240 171 252',
            '--sol-color-accent-1': '#d946ef',
            '--sol-color-accent-1-rgb': '217 70 239',
            '--sol-color-accent-2': '#c026d3',
            '--sol-color-accent-2-rgb': '192 38 211',
            '--sol-color-accent-3': '#f5d0fe',
            '--sol-color-accent-3-rgb': '245 208 254'
        },
        media: {
            logo: 'assets/logos/cig-logo.svg',
            background: 'assets/images/sc_bg_fallback.jpg'
        }
    },
    'argo': {
        colors: {
            ...rsiOriginal,
            '--sol-color-primary-1': '#12100a',
            '--sol-color-primary-1-rgb': '18 16 10',
            '--sol-color-primary-2': '#1a160e',
            '--sol-color-primary-2-rgb': '26 22 14',
            '--sol-color-primary-3': '#241f14',
            '--sol-color-primary-3-rgb': '36 31 20',
            '--sol-color-primary-4': '#2f291c',
            '--sol-color-primary-4-rgb': '47 41 28',
            '--sol-color-primary-6': '#4a3f2b',
            '--sol-color-primary-6-rgb': '74 63 43',
            '--sol-color-primary-7': '#fbbf24',
            '--sol-color-primary-7-rgb': '251 191 36',
            '--sol-color-primary-8': '#fcd34d',
            '--sol-color-primary-8-rgb': '252 211 77',
            '--sol-color-accent-1': '#f59e0b',
            '--sol-color-accent-1-rgb': '245 158 11',
            '--sol-color-accent-2': '#d97706',
            '--sol-color-accent-2-rgb': '217 119 6',
            '--sol-color-accent-3': '#fde68a',
            '--sol-color-accent-3-rgb': '253 230 138'
        },
        media: {
            logo: 'assets/logos/cig-logo.svg',
            background: 'assets/images/sc_bg_fallback.jpg'
        }
    },
    'aopoa': {
        colors: {
            ...rsiOriginal,
            '--sol-color-primary-1': '#0a0f14',
            '--sol-color-primary-1-rgb': '10 15 20',
            '--sol-color-primary-2': '#0f161f',
            '--sol-color-primary-2-rgb': '15 22 31',
            '--sol-color-primary-3': '#141e2b',
            '--sol-color-primary-3-rgb': '20 30 43',
            '--sol-color-primary-4': '#1c2938',
            '--sol-color-primary-4-rgb': '28 41 56',
            '--sol-color-primary-6': '#2d4254',
            '--sol-color-primary-6-rgb': '45 66 84',
            '--sol-color-primary-7': '#22d3ee',
            '--sol-color-primary-7-rgb': '34 211 238',
            '--sol-color-primary-8': '#67e8f9',
            '--sol-color-primary-8-rgb': '103 232 249',
            '--sol-color-accent-1': '#06b6d4',
            '--sol-color-accent-1-rgb': '6 182 212',
            '--sol-color-accent-2': '#0891b2',
            '--sol-color-accent-2-rgb': '8 145 178',
            '--sol-color-accent-3': '#a5f3fc',
            '--sol-color-accent-3-rgb': '165 243 252'
        },
        media: {
            logo: 'assets/logos/cig-logo.svg',
            background: 'assets/images/sc_bg_fallback.jpg'
        }
    },
    'tumbril': {
        colors: {
            ...rsiOriginal,
            '--sol-color-primary-1': '#100d08',
            '--sol-color-primary-1-rgb': '16 13 8',
            '--sol-color-primary-2': '#18140d',
            '--sol-color-primary-2-rgb': '24 20 13',
            '--sol-color-primary-3': '#221c12',
            '--sol-color-primary-3-rgb': '34 28 18',
            '--sol-color-primary-4': '#2d251a',
            '--sol-color-primary-4-rgb': '45 37 26',
            '--sol-color-primary-6': '#473a28',
            '--sol-color-primary-6-rgb': '71 58 40',
            '--sol-color-primary-7': '#92400e',
            '--sol-color-primary-7-rgb': '146 64 14',
            '--sol-color-primary-8': '#c2630a',
            '--sol-color-primary-8-rgb': '194 99 10',
            '--sol-color-accent-1': '#78350f',
            '--sol-color-accent-1-rgb': '120 53 15',
            '--sol-color-accent-2': '#57210c',
            '--sol-color-accent-2-rgb': '87 33 12',
            '--sol-color-accent-3': '#ea8a0e',
            '--sol-color-accent-3-rgb': '234 138 14'
        },
        media: {
            logo: 'assets/logos/cig-logo.svg',
            background: 'assets/images/sc_bg_fallback.jpg'
        }
    },
    'greycat': {
        colors: {
            ...rsiOriginal,
            '--sol-color-primary-1': '#12120f',
            '--sol-color-primary-1-rgb': '18 18 15',
            '--sol-color-primary-2': '#1a1a16',
            '--sol-color-primary-2-rgb': '26 26 22',
            '--sol-color-primary-3': '#23231e',
            '--sol-color-primary-3-rgb': '35 35 30',
            '--sol-color-primary-4': '#2e2e27',
            '--sol-color-primary-4-rgb': '46 46 39',
            '--sol-color-primary-6': '#48483d',
            '--sol-color-primary-6-rgb': '72 72 61',
            '--sol-color-primary-7': '#71717a',
            '--sol-color-primary-7-rgb': '113 113 122',
            '--sol-color-primary-8': '#a1a1aa',
            '--sol-color-primary-8-rgb': '161 161 170',
            '--sol-color-accent-1': '#52525b',
            '--sol-color-accent-1-rgb': '82 82 91',
            '--sol-color-accent-2': '#3f3f46',
            '--sol-color-accent-2-rgb': '63 63 70',
            '--sol-color-accent-3': '#d4d4d8',
            '--sol-color-accent-3-rgb': '212 212 216'
        },
        media: {
            logo: 'assets/logos/cig-logo.svg',
            background: 'assets/images/sc_bg_fallback.jpg'
        }
    },
    'vanduul': {
        colors: {
            ...rsiOriginal,
            '--sol-color-primary-1': '#140505',
            '--sol-color-primary-1-rgb': '20 5 5',
            '--sol-color-primary-2': '#1c0808',
            '--sol-color-primary-2-rgb': '28 8 8',
            '--sol-color-primary-3': '#260c0c',
            '--sol-color-primary-3-rgb': '38 12 12',
            '--sol-color-primary-4': '#331111',
            '--sol-color-primary-4-rgb': '51 17 17',
            '--sol-color-primary-6': '#4d1a1a',
            '--sol-color-primary-6-rgb': '77 26 26',
            '--sol-color-primary-7': '#dc2626',
            '--sol-color-primary-7-rgb': '220 38 38',
            '--sol-color-primary-8': '#f87171',
            '--sol-color-primary-8-rgb': '248 113 113',
            '--sol-color-accent-1': '#b91c1c',
            '--sol-color-accent-1-rgb': '185 28 28',
            '--sol-color-accent-2': '#991b1b',
            '--sol-color-accent-2-rgb': '153 27 27',
            '--sol-color-accent-3': '#fca5a5',
            '--sol-color-accent-3-rgb': '252 165 165'
        },
        media: {
            logo: 'assets/logos/cig-logo.svg',
            background: 'assets/images/sc_bg_fallback.jpg'
        }
    },
    'gatac': {
        colors: {
            ...rsiOriginal,
            '--sol-color-primary-1': '#0d0f0a',
            '--sol-color-primary-1-rgb': '13 15 10',
            '--sol-color-primary-2': '#14180e',
            '--sol-color-primary-2-rgb': '20 24 14',
            '--sol-color-primary-3': '#1c2214',
            '--sol-color-primary-3-rgb': '28 34 20',
            '--sol-color-primary-4': '#262d1c',
            '--sol-color-primary-4-rgb': '38 45 28',
            '--sol-color-primary-6': '#3d462c',
            '--sol-color-primary-6-rgb': '61 70 44',
            '--sol-color-primary-7': '#84cc16',
            '--sol-color-primary-7-rgb': '132 204 22',
            '--sol-color-primary-8': '#a3e635',
            '--sol-color-primary-8-rgb': '163 230 53',
            '--sol-color-accent-1': '#65a30d',
            '--sol-color-accent-1-rgb': '101 163 13',
            '--sol-color-accent-2': '#4d7c0f',
            '--sol-color-accent-2-rgb': '77 124 15',
            '--sol-color-accent-3': '#bef264',
            '--sol-color-accent-3-rgb': '190 242 100'
        },
        media: {
            logo: 'assets/logos/cig-logo.svg',
            background: 'assets/images/sc_bg_fallback.jpg'
        }
    },
    'c3rb': {
        colors: c3rbBaseline,
        media: {
            logo: 'assets/logos/cig-logo.svg',
            background: 'assets/images/sc_bg_fallback.jpg'
        }
    }
};

// Initialize state.colors with RSI Original as default
state.colors = { ...rsiOriginal };

// Initialize state.media with default launcher media
state.media = {
    logo: 'assets/logos/cig-logo.svg',
    background: 'assets/images/sc_bg_fallback.jpg'
};

/**
 * Auto-detect RSI Launcher installation
 */
async function detectLauncher(options = {}) {
    const { autoInit = false, silentFailure = false } = options;

    if (!silentFailure) {
        showStatus('init-status', 'Detecting RSI Launcher...', 'info');
    }

    try {
        const response = await fetch('/api/detect-launcher');
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || data.message || 'Launcher not found');
        }

        DOM.asarPath.value = data.launcher.asarPath;
        showStatus('init-status', '✓ Installation path detected. Click "Initialize" to continue.', 'success');

        if (autoInit) {
            await initSession();
        }

    } catch (error) {
        if (!silentFailure) {
            showStatus('init-status', error.message, 'error');
        }
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
        showStatus('init-status', '✓ Initialized successfully. Click "Next" to continue.', 'success');
        
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
    const extractButton = document.getElementById('extract-btn');
    if (extractButton) extractButton.disabled = true;

    showStatus('extract-status', 'Extracting app.asar...', 'info');
    setExtractProgress(true, 5, 'Starting extraction...');
    startExtractPolling();

    try {
        const response = await fetch('/api/extract', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        let data = {};
        try {
            data = await response.json();
        } catch (parseError) {
            data = { error: 'Server returned an unexpected response.' };
        }

        if (!response.ok) {
            const details = data.details ? ` (${data.details})` : '';
            throw new Error((data.error || 'Failed to extract') + details);
        }

        state.extracted = true;
        setExtractProgress(true, 100, 'Extraction complete');
        showStatus('extract-status', '✓ Extracted successfully', 'success');
        
        // Navigate to Colors page (page 3)
        setTimeout(() => {
            navigateToPage(3);
            document.getElementById('extract-status').style.display = 'none';
        }, 500);

    } catch (error) {
        const message = error?.message?.includes('Failed to fetch')
            ? 'Failed to fetch. The local server may have stopped. Please restart the app.'
            : error.message;
        showStatus('extract-status', message, 'error');
        setExtractProgress(true, 0, 'Extraction failed');
    } finally {
        if (extractButton) extractButton.disabled = false;
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
            navigateToPage(3);
            document.getElementById('extract-status').style.display = 'none';
        }, 500);
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
    const preset = colorPresets[presetName];
    
    if (!preset) {
        showStatus('colors-status', 'Preset not found', 'error');
        return;
    }

    showStatus('colors-status', `Applying ${presetName} preset...`, 'info');
    state.colors = { ...preset.colors || preset };
    
    // Update media if preset includes it
    if (preset.media) {
        state.media = { ...preset.media };
        updatePreviewMedia(preset.media);
    }
    
    // Defer rendering to avoid blocking
    setTimeout(() => {
        renderColorMappings();
    }, 0);
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
        input.addEventListener('input', updatePreviewFromUi);
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
            
            // Show category label for main colors
            const categoryLabel = category ? `<span class="color-category">${category.toUpperCase()}</span>` : '';
            
            item.innerHTML = `
                ${categoryLabel}
                <input type="text" class="old-color" value="${oldColor}" placeholder="Old color" readonly>
                <div class="color-preview" style="background: ${newColor};" onclick="pickColor(this)"></div>
                <input type="text" class="new-color" value="${newColor}" placeholder="New color">
                <div class="color-tuning">
                    <div class="color-inputs">
                        <input type="text" class="hex-input" placeholder="HEX" maxlength="7" value="${normalizeColorToHex(newColor) || '#888888'}">
                        <input type="text" class="rgb-input" placeholder="RGB">
                    </div>
                    <button class="color-picker-button" type="button">🎨 Color Wheel</button>
                    <input type="color" class="color-wheel-hidden" value="${normalizeColorToHex(newColor) || '#888888'}" aria-label="Color wheel" style="display: none;">
                </div>
                <button class="remove-btn" onclick="removeColorMapping('${id}')">Remove</button>
            `;
            
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
                oldColorInputs[j].addEventListener('input', updatePreviewFromUi);
            }
            setColorControls(item, normalizeColorToHex(newColor) || '#888888');
        }
        
        setupIndex = endIndex;
        
        // Schedule next chunk or finalize
        if (setupIndex < totalItems) {
            setTimeout(setupNextChunk, 0);
        } else {
            // All setup done, update preview and show success
            updatePreviewFromColors(state.colors);
            showStatus('colors-status', `✓ Colors loaded successfully`, 'success');
        }
    }
    
    // Start setup process with initial message
    showStatus('colors-status', 'Loading colors... 0%', 'info');
    setTimeout(setupNextChunk, 0);
}

/**
 * Toggle color section visibility
 */
function toggleColorSection(sectionId) {
    const section = document.getElementById(sectionId);
    const content = section.querySelector('.color-section-content');
    const toggle = section.querySelector('.color-section-toggle');
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

    showStatus('colors-status', 'Applying colors...', 'info');

    try {
        const response = await fetch('/api/apply-colors', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ colors })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to apply colors');
        }

        state.config.colors = colors;
        showStatus('colors-status', '✓ Colors applied successfully', 'success');
        updatePreviewFromColors(colors);

    } catch (error) {
        showStatus('colors-status', error.message, 'error');
    }
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
        { path: 'assets/logos/star_engine.svg', type: 'image', name: 'Star Engine Logo', url: 'assets/logos/star_engine.svg' }
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

    showStatus('media-status', 'Uploading and replacing media...', 'info');

    try {
        for (const [targetPath, file] of Object.entries(media)) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('targetPath', targetPath);

            const response = await fetch('/api/upload-media', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `Failed to upload ${targetPath}`);
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

    musicList.innerHTML = state.music.map((track, index) => `
        <div class="music-item" data-index="${index}">
            <div class="music-item-order">${index + 1}</div>
            <div class="music-item-name">
                ${track.name}
                ${track.isDefault ? '<span style="color: #2875a4; font-size: 12px;"> (default)</span>' : ''}
            </div>
            <div class="music-item-controls">
                <button class="remove-btn" onclick="removeMusicFile(${index})" title="Remove">✕</button>
            </div>
        </div>
    `).join('');
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
    document.getElementById('themeImportInput').click();
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
 * Import theme from Finalize page
 */
function importTheme() {
    document.getElementById('themeImportInput').click();
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
 * Restore from backup
 */
async function restoreBackup(backupPath) {
    if (!confirm('Are you sure you want to restore from this backup?')) {
        return;
    }

    showStatus('finalize-status', 'Restoring from backup...', 'info');

    try {
        const response = await fetch('/api/restore', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ backupPath })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to restore');
        }

        showStatus('finalize-status', '✓ Restored successfully', 'success');
        setTimeout(viewBackups, 1000);

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

window.addEventListener('load', () => {
    // Initialize DOM cache first for performance
    DOM.init();
    
    // Initialize page navigation - start on initialization page (step 1)
    navigateToPage(1);
    
    setTimeout(() => {
        updatePreviewFromColors(state.colors || {});
        
        // Initialize with default RSI media if available
        if (state.media && Object.keys(state.media).length > 0) {
            updatePreviewMedia(state.media);
        }
    }, 200);

    detectLauncher({ autoInit: false, silentFailure: true });
});
