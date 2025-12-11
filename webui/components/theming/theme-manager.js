/**
 * Theme Manager Component
 * Dark/light mode toggle and accent color selection
 * Requirements: 26.1, 26.2, 26.3, 26.4, 26.5
 */

/**
 * Theme Manager Class
 */
export class ThemeManager {
  constructor() {
    this.currentTheme = 'dark';
    this.currentAccent = 'indigo';
    this.storageKey = 'theme-preferences';
    
    // Accent color presets
    this.accentColors = {
      indigo: { primary: '#6366f1', secondary: '#818cf8' },
      violet: { primary: '#8b5cf6', secondary: '#a78bfa' },
      blue: { primary: '#3b82f6', secondary: '#60a5fa' },
      cyan: { primary: '#06b6d4', secondary: '#22d3ee' },
      emerald: { primary: '#10b981', secondary: '#34d399' },
      amber: { primary: '#f59e0b', secondary: '#fbbf24' },
      rose: { primary: '#f43f5e', secondary: '#fb7185' },
      pink: { primary: '#ec4899', secondary: '#f472b6' }
    };
    
    this.init();
  }

  /**
   * Initialize theme from storage or system preference
   */
  init() {
    const saved = this.loadPreferences();
    
    if (saved) {
      this.currentTheme = saved.theme || 'dark';
      this.currentAccent = saved.accent || 'indigo';
    } else {
      // Check system preference
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
        this.currentTheme = 'light';
      }
    }
    
    this.applyTheme();
    this.applyAccent();
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!this.loadPreferences()?.theme) {
        this.setTheme(e.matches ? 'dark' : 'light', false);
      }
    });
  }

  /**
   * Set theme (dark/light)
   * @param {string} theme - 'dark' or 'light'
   * @param {boolean} save - Whether to save preference
   */
  setTheme(theme, save = true) {
    this.currentTheme = theme;
    this.applyTheme();
    if (save) this.savePreferences();
  }

  /**
   * Toggle between dark and light theme
   */
  toggleTheme() {
    this.setTheme(this.currentTheme === 'dark' ? 'light' : 'dark');
  }

  /**
   * Apply current theme to document
   */
  applyTheme() {
    document.documentElement.dataset.theme = this.currentTheme;
    
    // Update meta theme-color for mobile browsers
    const metaTheme = document.querySelector('meta[name="theme-color"]');
    if (metaTheme) {
      metaTheme.content = this.currentTheme === 'dark' ? '#0f172a' : '#f3f4f6';
    }
  }

  /**
   * Set accent color
   * @param {string} accent - Accent color name
   */
  setAccent(accent) {
    if (!this.accentColors[accent]) return;
    
    this.currentAccent = accent;
    this.applyAccent();
    this.savePreferences();
  }

  /**
   * Apply current accent color to document
   */
  applyAccent() {
    const colors = this.accentColors[this.currentAccent];
    if (!colors) return;
    
    document.documentElement.style.setProperty('--accent-primary', colors.primary);
    document.documentElement.style.setProperty('--accent-secondary', colors.secondary);
    document.documentElement.style.setProperty('--accent-color', colors.primary);
    document.documentElement.style.setProperty('--accent-hover', colors.secondary);
    
    // Update gradient
    document.documentElement.style.setProperty(
      '--gradient-ai',
      `linear-gradient(135deg, ${colors.primary} 0%, ${colors.secondary} 100%)`
    );
  }

  /**
   * Set custom accent color
   * @param {string} primary - Primary color hex
   * @param {string} secondary - Secondary color hex (optional)
   */
  setCustomAccent(primary, secondary) {
    if (!secondary) {
      // Generate lighter secondary from primary
      secondary = this.lightenColor(primary, 20);
    }
    
    document.documentElement.style.setProperty('--accent-primary', primary);
    document.documentElement.style.setProperty('--accent-secondary', secondary);
    document.documentElement.style.setProperty('--accent-color', primary);
    document.documentElement.style.setProperty('--accent-hover', secondary);
    document.documentElement.style.setProperty(
      '--gradient-ai',
      `linear-gradient(135deg, ${primary} 0%, ${secondary} 100%)`
    );
    
    this.currentAccent = 'custom';
    this.savePreferences({ customPrimary: primary, customSecondary: secondary });
  }

  /**
   * Lighten a hex color
   * @param {string} hex - Hex color
   * @param {number} percent - Percentage to lighten
   * @returns {string} Lightened hex color
   */
  lightenColor(hex, percent) {
    const num = parseInt(hex.replace('#', ''), 16);
    const amt = Math.round(2.55 * percent);
    const R = Math.min(255, (num >> 16) + amt);
    const G = Math.min(255, ((num >> 8) & 0x00FF) + amt);
    const B = Math.min(255, (num & 0x0000FF) + amt);
    return '#' + (0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1);
  }

  /**
   * Save preferences to localStorage
   */
  savePreferences(extra = {}) {
    const prefs = {
      theme: this.currentTheme,
      accent: this.currentAccent,
      ...extra
    };
    localStorage.setItem(this.storageKey, JSON.stringify(prefs));
  }

  /**
   * Load preferences from localStorage
   * @returns {Object|null} Saved preferences
   */
  loadPreferences() {
    try {
      const saved = localStorage.getItem(this.storageKey);
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      return null;
    }
  }

  /**
   * Reset to default theme
   */
  reset() {
    localStorage.removeItem(this.storageKey);
    this.currentTheme = 'dark';
    this.currentAccent = 'indigo';
    this.applyTheme();
    this.applyAccent();
  }
}

// Singleton instance
export const themeManager = new ThemeManager();

/**
 * Theme Picker Alpine Component
 */
export function createThemePicker() {
  return {
    // State
    isOpen: false,
    currentTheme: themeManager.currentTheme,
    currentAccent: themeManager.currentAccent,
    customColor: '#6366f1',
    
    // Options
    accentColors: Object.entries(themeManager.accentColors).map(([id, colors]) => ({
      id,
      label: id.charAt(0).toUpperCase() + id.slice(1),
      color: colors.primary
    })),
    
    // Lifecycle
    init() {
      this.currentTheme = themeManager.currentTheme;
      this.currentAccent = themeManager.currentAccent;
    },
    
    // Methods
    open() {
      this.isOpen = true;
    },
    
    close() {
      this.isOpen = false;
    },
    
    setTheme(theme) {
      this.currentTheme = theme;
      themeManager.setTheme(theme);
    },
    
    toggleTheme() {
      this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
      themeManager.setTheme(this.currentTheme);
    },
    
    setAccent(accent) {
      this.currentAccent = accent;
      themeManager.setAccent(accent);
    },
    
    setCustomColor(color) {
      this.customColor = color;
      this.currentAccent = 'custom';
      themeManager.setCustomAccent(color);
    },
    
    reset() {
      themeManager.reset();
      this.currentTheme = 'dark';
      this.currentAccent = 'indigo';
    }
  };
}

/**
 * Register Alpine component
 */
export function registerThemePicker() {
  if (typeof Alpine !== 'undefined') {
    Alpine.data('themePicker', createThemePicker);
  }
}

export default themeManager;
