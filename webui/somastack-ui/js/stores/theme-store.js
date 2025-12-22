/**
 * SomaStack Unified UI Design System - Theme Store
 * 
 * Document ID: SOMASTACK-UI-THEME-STORE
 * Version: 1.0.0
 * 
 * Alpine.js store for theme management with light/dark/system support.
 * 
 * Requirements: FR-TH-001 through FR-TH-006
 */

const STORAGE_KEY = 'soma_theme_mode';
const THEME_CLASS_LIGHT = 'soma-light';
const THEME_CLASS_DARK = 'soma-dark';

/**
 * Register the theme store with Alpine.js
 * 
 * Usage:
 *   Alpine.store('theme').toggle()
 *   Alpine.store('theme').setMode('dark')
 *   x-show="$store.theme.mode === 'dark'"
 */
function registerThemeStore(Alpine) {
  Alpine.store('theme', {
    // State
    mode: 'system', // 'light' | 'dark' | 'system'
    currentTheme: 'light', // Resolved theme: 'light' | 'dark'
    
    /**
     * Initialize store on Alpine start
     * Requirement: FR-TH-003, FR-TH-004
     */
    init() {
      this.loadPreference();
      this.applyTheme();
      this.watchSystemPreference();
    },
    
    /**
     * Load theme preference from localStorage
     * Requirement: FR-TH-003
     */
    loadPreference() {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved && ['light', 'dark', 'system'].includes(saved)) {
        this.mode = saved;
      }
    },
    
    /**
     * Set theme mode and persist
     * Requirement: FR-TH-002
     * 
     * @param {string} mode - Theme mode ('light', 'dark', 'system')
     */
    setMode(mode) {
      if (!['light', 'dark', 'system'].includes(mode)) {
        console.warn('Invalid theme mode:', mode);
        return;
      }
      
      const startTime = performance.now();
      
      this.mode = mode;
      localStorage.setItem(STORAGE_KEY, mode);
      this.applyTheme();
      
      const elapsed = performance.now() - startTime;
      if (elapsed > 100) {
        console.warn(`Theme switch took ${elapsed.toFixed(2)}ms (target: <100ms)`);
      }
    },
    
    /**
     * Apply theme to document
     * Requirement: FR-TH-001, FR-TH-005, FR-TH-006
     */
    applyTheme() {
      const isDark = this.mode === 'dark' || 
        (this.mode === 'system' && this.systemPrefersDark());
      
      this.currentTheme = isDark ? 'dark' : 'light';
      
      const root = document.documentElement;
      
      // Add transition class for smooth theme change
      // Requirement: FR-TH-005
      root.style.setProperty('--theme-transition', '300ms');
      
      if (isDark) {
        root.classList.remove(THEME_CLASS_LIGHT);
        root.classList.add(THEME_CLASS_DARK);
        root.setAttribute('data-theme', 'dark');
      } else {
        root.classList.remove(THEME_CLASS_DARK);
        root.classList.add(THEME_CLASS_LIGHT);
        root.setAttribute('data-theme', 'light');
      }
      
      // Update meta theme-color for mobile browsers
      const metaThemeColor = document.querySelector('meta[name="theme-color"]');
      if (metaThemeColor) {
        metaThemeColor.setAttribute('content', isDark ? '#171717' : '#fafafa');
      }
    },
    
    /**
     * Check if system prefers dark mode
     * Requirement: FR-TH-004
     * 
     * @returns {boolean} True if system prefers dark
     */
    systemPrefersDark() {
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    },
    
    /**
     * Watch for system preference changes
     * Requirement: FR-TH-004
     */
    watchSystemPreference() {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      
      mediaQuery.addEventListener('change', () => {
        if (this.mode === 'system') {
          this.applyTheme();
        }
      });
    },
    
    /**
     * Toggle between light and dark modes
     * Requirement: FR-TH-002
     */
    toggle() {
      if (this.mode === 'system') {
        // If system, switch to opposite of current
        this.setMode(this.currentTheme === 'dark' ? 'light' : 'dark');
      } else {
        this.setMode(this.mode === 'dark' ? 'light' : 'dark');
      }
    },
    
    /**
     * Cycle through modes: light -> dark -> system -> light
     */
    cycle() {
      const modes = ['light', 'dark', 'system'];
      const currentIndex = modes.indexOf(this.mode);
      const nextIndex = (currentIndex + 1) % modes.length;
      this.setMode(modes[nextIndex]);
    },
    
    /**
     * Computed: Is dark mode active?
     */
    get isDark() {
      return this.currentTheme === 'dark';
    },
    
    /**
     * Computed: Is light mode active?
     */
    get isLight() {
      return this.currentTheme === 'light';
    },
    
    /**
     * Computed: Is system mode selected?
     */
    get isSystem() {
      return this.mode === 'system';
    },
    
    /**
     * Get icon for current mode
     * 
     * @returns {string} Icon character or emoji
     */
    get icon() {
      switch (this.mode) {
        case 'light': return '☀️';
        case 'dark': return '🌙';
        case 'system': return '💻';
        default: return '☀️';
      }
    },
    
    /**
     * Get label for current mode
     * 
     * @returns {string} Human-readable label
     */
    get label() {
      switch (this.mode) {
        case 'light': return 'Light';
        case 'dark': return 'Dark';
        case 'system': return 'System';
        default: return 'Light';
      }
    }
  });
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { registerThemeStore };
}

// Auto-register if Alpine is available
if (typeof Alpine !== 'undefined') {
  registerThemeStore(Alpine);
}
