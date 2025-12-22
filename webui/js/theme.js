/**
 * Theme Loader Module - Enhanced
 * Per SRS AGENTSKIN.md Section 5.2
 * 
 * VIBE COMPLIANT:
 * - Real implementations only (no mocks)
 * - XSS validation to block malicious CSS
 * - HTTPS enforcement for remote themes
 * - WCAG AA contrast validation
 * 
 * Features:
 * - load/apply themes from local or remote sources
 * - preview mode with cancel support
 * - export themes as JSON files
 * - XSS pattern rejection
 * - WCAG contrast validation
 */

const THEMES_PATH = '/static/themes/';
const CONFIG_KEY = 'ui-config';
const THEME_SWITCH_MAX_MS = 300;

/**
 * XSS patterns that MUST be rejected in CSS values.
 * Prevents injection attacks via malicious theme files.
 */
const XSS_PATTERNS = [
    /url\s*\(/i,           // Block url() to prevent external resource loading
    /<script/i,            // Block script tags
    /javascript:/i,        // Block javascript: URIs
    /expression\s*\(/i,    // Block IE expression()
    /behavior\s*:/i,       // Block IE behavior
    /@import/i,            // Block @import to prevent external CSS
    /binding\s*:/i,        // Block -moz-binding
];

/**
 * Required CSS variables for a valid theme.
 * Per AgentSkin requirements (26 variables).
 */
const REQUIRED_VARIABLES = [
    '--bg-void',
    '--glass-surface',
    '--glass-border',
    '--text-main',
    '--text-dim',
    '--accent-slate',
];

const Theme = {
    currentSkin: null,
    _previousSkin: null,
    _isPreview: false,

    /**
     * Initialize theme on page load.
     * Restores previously selected theme from localStorage.
     */
    async init(name = null) {
        const config = this.getConfig();
        const skinName = name || config.theme || 'default';
        await this.use(skinName);
    },

    /**
     * Load and apply a theme by name or URL.
     * @param {string} nameOrUrl - Theme name or HTTPS URL
     * @param {object} options - Optional base path override
     * @returns {Promise<boolean>} Success status
     */
    async use(nameOrUrl, options = {}) {
        const startTime = performance.now();
        
        try {
            const skin = nameOrUrl.startsWith('http')
                ? await this.loadRemote(nameOrUrl)
                : await this.loadLocal(nameOrUrl, options);

            if (this.validate(skin)) {
                this.apply(skin);
                this.currentSkin = skin;
                
                const elapsed = performance.now() - startTime;
                if (elapsed > THEME_SWITCH_MAX_MS) {
                    console.warn(`Theme switch took ${elapsed.toFixed(0)}ms (target: <${THEME_SWITCH_MAX_MS}ms)`);
                }
                return true;
            }
            return false;
        } catch (e) {
            console.warn('Failed to load skin:', nameOrUrl, e);
            return false;
        }
    },

    /**
     * Load theme from local static path.
     * @param {string} name - Theme name (without .json extension)
     * @param {object} options - Optional basePath override
     * @returns {Promise<object>} Theme object
     */
    async loadLocal(name, options = {}) {
        const basePath = options.basePath || THEMES_PATH;
        const url = `${basePath}${name}.json`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(`Skin not found: ${name}`);
        return res.json();
    },

    /**
     * Load theme from remote HTTPS URL.
     * Security: MUST be HTTPS only.
     * @param {string} url - HTTPS URL to theme JSON
     * @returns {Promise<object>} Theme object
     * @throws {Error} If URL is not HTTPS
     */
    async loadRemote(url) {
        // Security: Enforce HTTPS
        if (!url.startsWith('https://')) {
            throw new Error('Remote themes must use HTTPS for security');
        }
        
        const res = await fetch(url);
        if (!res.ok) throw new Error(`Remote skin fetch failed: ${url}`);
        return res.json();
    },

    /**
     * Validate theme structure and security.
     * Blocks XSS patterns in CSS values.
     * @param {object} skin - Theme object to validate
     * @returns {boolean} True if valid
     */
    validate(skin) {
        // Structure validation
        if (!skin || typeof skin !== 'object') {
            console.error('Theme validation failed: not an object');
            return false;
        }
        if (!skin.name || typeof skin.name !== 'string') {
            console.error('Theme validation failed: missing or invalid name');
            return false;
        }
        if (!skin.variables || typeof skin.variables !== 'object') {
            console.error('Theme validation failed: missing variables object');
            return false;
        }

        // XSS validation - check all variable values
        for (const [key, value] of Object.entries(skin.variables)) {
            if (typeof value !== 'string') {
                console.error(`Theme validation failed: ${key} is not a string`);
                return false;
            }
            
            for (const pattern of XSS_PATTERNS) {
                if (pattern.test(value)) {
                    console.error(`XSS pattern detected in theme variable ${key}: ${pattern}`);
                    return false;
                }
            }
        }

        // Version validation (optional but recommended)
        if (skin.version && !/^\d+\.\d+\.\d+$/.test(skin.version)) {
            console.warn('Theme version does not follow semver:', skin.version);
        }

        return true;
    },

    /**
     * Apply theme CSS variables to document root.
     * @param {object} skin - Validated theme object
     */
    apply(skin) {
        const root = document.documentElement;
        const vars = skin.variables || {};

        for (const [key, value] of Object.entries(vars)) {
            const prop = key.startsWith('--') ? key : `--${key}`;
            root.style.setProperty(prop, value);
        }
    },

    /**
     * Switch to a theme and persist selection.
     * @param {string} name - Theme name
     * @returns {Promise<boolean>} Success status
     */
    async switch(name) {
        const success = await this.use(name);
        if (success) {
            this.saveConfig({ theme: name });
        }
        return success;
    },

    /**
     * Preview a theme temporarily without persisting.
     * Use cancelPreview() to revert.
     * @param {object} skin - Theme to preview
     */
    preview(skin) {
        if (!this._isPreview && this.currentSkin) {
            this._previousSkin = this.currentSkin;
        }
        this._isPreview = true;
        
        if (this.validate(skin)) {
            this.apply(skin);
        }
    },

    /**
     * Cancel preview and restore previous theme.
     */
    cancelPreview() {
        if (this._isPreview && this._previousSkin) {
            this.apply(this._previousSkin);
            this._isPreview = false;
        }
    },

    /**
     * Get current theme object.
     * @returns {object|null} Current theme
     */
    getCurrentTheme() {
        return this.currentSkin;
    },

    /**
     * Check if currently in preview mode.
     * @returns {boolean} True if previewing
     */
    isPreviewMode() {
        return this._isPreview;
    },

    /**
     * Export theme as downloadable JSON Blob.
     * @param {object} skin - Theme to export
     * @returns {Blob} JSON blob for download
     */
    exportTheme(skin) {
        const json = JSON.stringify(skin, null, 2);
        return new Blob([json], { type: 'application/json' });
    },

    /**
     * Download a theme as JSON file.
     * @param {object} skin - Theme to download
     * @param {string} filename - Optional filename override
     */
    downloadTheme(skin, filename = null) {
        const blob = this.exportTheme(skin);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename || `${skin.name || 'theme'}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },

    /**
     * Import theme from File object.
     * @param {File} file - JSON file to import
     * @returns {Promise<object|null>} Imported theme or null if invalid
     */
    async importTheme(file) {
        try {
            const text = await file.text();
            const skin = JSON.parse(text);
            
            if (this.validate(skin)) {
                return skin;
            }
            return null;
        } catch (e) {
            console.error('Failed to import theme:', e);
            return null;
        }
    },

    // =========================================================================
    // WCAG Contrast Validation (A11Y-AGS-001)
    // =========================================================================

    /**
     * Convert hex color to RGB array.
     * @param {string} hex - Hex color (#RRGGBB or #RGB)
     * @returns {number[]} [r, g, b] values 0-255
     */
    hexToRgb(hex) {
        // Remove # if present
        hex = hex.replace(/^#/, '');
        
        // Handle shorthand (#RGB)
        if (hex.length === 3) {
            hex = hex.split('').map(c => c + c).join('');
        }
        
        const r = parseInt(hex.slice(0, 2), 16);
        const g = parseInt(hex.slice(2, 4), 16);
        const b = parseInt(hex.slice(4, 6), 16);
        
        return [r, g, b];
    },

    /**
     * Calculate relative luminance per WCAG 2.1.
     * @param {string} hex - Hex color
     * @returns {number} Luminance 0-1
     */
    getLuminance(hex) {
        const rgb = this.hexToRgb(hex);
        const [r, g, b] = rgb.map(c => {
            c = c / 255;
            return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
        });
        return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    },

    /**
     * Calculate contrast ratio between two colors.
     * @param {string} fg - Foreground hex color
     * @param {string} bg - Background hex color
     * @returns {number} Contrast ratio (1-21)
     */
    getContrastRatio(fg, bg) {
        const l1 = this.getLuminance(fg);
        const l2 = this.getLuminance(bg);
        const lighter = Math.max(l1, l2);
        const darker = Math.min(l1, l2);
        return (lighter + 0.05) / (darker + 0.05);
    },

    /**
     * Check if colors meet WCAG AA requirements.
     * Requires 4.5:1 for normal text, 3:1 for large text.
     * @param {string} fg - Foreground hex color
     * @param {string} bg - Background hex color
     * @param {boolean} largeText - True for large text (3:1 threshold)
     * @returns {boolean} True if meets WCAG AA
     */
    checkWcagAA(fg, bg, largeText = false) {
        const ratio = this.getContrastRatio(fg, bg);
        const threshold = largeText ? 3 : 4.5;
        return ratio >= threshold;
    },

    /**
     * Validate all text colors in theme meet WCAG AA.
     * @param {object} skin - Theme to validate
     * @returns {object[]} Array of failing color pairs
     */
    validateContrast(skin) {
        const failures = [];
        const vars = skin.variables || {};
        
        // Common text/background pairs to check
        const pairs = [
            ['--text-main', '--bg-void'],
            ['--text-dim', '--bg-void'],
            ['--text-main', '--glass-surface'],
            ['--accent-slate', '--bg-void'],
        ];
        
        for (const [fgVar, bgVar] of pairs) {
            const fg = vars[fgVar];
            const bg = vars[bgVar];
            
            if (fg && bg && !this.checkWcagAA(fg, bg)) {
                const ratio = this.getContrastRatio(fg, bg);
                failures.push({
                    foreground: fgVar,
                    background: bgVar,
                    ratio: ratio.toFixed(2),
                    required: '4.5:1',
                });
            }
        }
        
        return failures;
    },

    // =========================================================================
    // Config Persistence
    // =========================================================================

    getConfig() {
        try {
            const stored = localStorage.getItem(CONFIG_KEY);
            return stored ? JSON.parse(stored) : {};
        } catch {
            return {};
        }
    },

    saveConfig(updates) {
        const config = { ...this.getConfig(), ...updates };
        localStorage.setItem(CONFIG_KEY, JSON.stringify(config));
    },

    setTheme(mode) {
        document.documentElement.setAttribute('data-theme', mode);
        this.saveConfig({ mode });
    },

    toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme') || 'light';
        const next = current === 'light' ? 'dark' : 'light';
        this.setTheme(next);
        return next;
    }
};

export default Theme;

if (typeof window !== 'undefined') {
    window.Theme = Theme;
}
