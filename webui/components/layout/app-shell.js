/**
 * App Shell Component
 * 
 * Main application layout container with sidebar, header, and panel management.
 * Handles responsive breakpoints and persists layout preferences.
 * 
 * Usage:
 * <div x-data="appShell()" x-bind="shell" class="app-shell">
 *   <header class="app-header">...</header>
 *   <aside class="app-sidebar">...</aside>
 *   <main class="app-main">...</main>
 *   <aside class="app-panel">...</aside>
 * </div>
 * 
 * @module components/layout/app-shell
 */

const STORAGE_KEY = 'soma-layout-prefs';
const BREAKPOINTS = {
  mobile: 768,
  tablet: 1024,
};

/**
 * App Shell component factory
 * @param {Object} options - Shell options
 * @param {string} [options.defaultSidebar='expanded'] - Default sidebar state
 * @param {boolean} [options.persistLayout=true] - Persist layout to localStorage
 * @returns {Object} Alpine component data
 */
export default function AppShell(options = {}) {
  return {
    // Sidebar state: 'expanded' | 'collapsed' | 'hidden' | 'open' (mobile)
    sidebarState: options.defaultSidebar ?? 'expanded',
    // Panel state
    panelOpen: false,
    panelWidth: 320,
    // Viewport
    isMobile: false,
    isTablet: false,
    // Resize observer
    resizeObserver: null,
    
    init() {
      // Load persisted preferences
      if (options.persistLayout !== false) {
        this.loadPreferences();
      }
      
      // Set up viewport detection
      this.checkViewport();
      window.addEventListener('resize', () => this.checkViewport());
      
      // Watch for sidebar state changes to persist
      this.$watch('sidebarState', () => this.savePreferences());
      this.$watch('panelWidth', () => this.savePreferences());
    },
    
    destroy() {
      window.removeEventListener('resize', this.checkViewport);
    },
    
    /**
     * Bind object for shell container
     */
    get shell() {
      return {
        ':data-sidebar': () => this.sidebarState,
        ':data-mobile': () => this.isMobile,
        ':data-tablet': () => this.isTablet,
      };
    },
    
    /**
     * Check viewport size and adjust layout
     */
    checkViewport() {
      const width = window.innerWidth;
      const wasMobile = this.isMobile;
      const wasTablet = this.isTablet;
      
      this.isMobile = width < BREAKPOINTS.mobile;
      this.isTablet = width >= BREAKPOINTS.mobile && width < BREAKPOINTS.tablet;
      
      // Auto-adjust sidebar on viewport change
      if (this.isMobile && !wasMobile) {
        this.sidebarState = 'hidden';
      } else if (this.isTablet && !wasTablet) {
        this.sidebarState = 'collapsed';
      } else if (!this.isMobile && !this.isTablet && (wasMobile || wasTablet)) {
        this.sidebarState = 'expanded';
      }
    },
    
    /**
     * Toggle sidebar state
     */
    toggleSidebar() {
      if (this.isMobile) {
        this.sidebarState = this.sidebarState === 'open' ? 'hidden' : 'open';
      } else if (this.isTablet) {
        this.sidebarState = this.sidebarState === 'collapsed' ? 'expanded' : 'collapsed';
      } else {
        this.sidebarState = this.sidebarState === 'expanded' ? 'collapsed' : 'expanded';
      }
    },
    
    /**
     * Open sidebar (mobile)
     */
    openSidebar() {
      if (this.isMobile) {
        this.sidebarState = 'open';
      } else {
        this.sidebarState = 'expanded';
      }
    },
    
    /**
     * Close sidebar (mobile)
     */
    closeSidebar() {
      if (this.isMobile) {
        this.sidebarState = 'hidden';
      } else {
        this.sidebarState = 'collapsed';
      }
    },
    
    /**
     * Toggle panel
     */
    togglePanel() {
      this.panelOpen = !this.panelOpen;
    },
    
    /**
     * Open panel
     */
    openPanel() {
      this.panelOpen = true;
    },
    
    /**
     * Close panel
     */
    closePanel() {
      this.panelOpen = false;
    },
    
    /**
     * Set panel width
     * @param {number} width - Panel width in pixels
     */
    setPanelWidth(width) {
      this.panelWidth = Math.max(240, Math.min(480, width));
    },
    
    /**
     * Load preferences from localStorage
     */
    loadPreferences() {
      try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          const prefs = JSON.parse(stored);
          // Only apply if not on mobile (mobile always starts hidden)
          if (!this.isMobile && prefs.sidebarState) {
            this.sidebarState = prefs.sidebarState;
          }
          if (prefs.panelWidth) {
            this.panelWidth = prefs.panelWidth;
          }
        }
      } catch (e) {
        console.warn('Failed to load layout preferences:', e);
      }
    },
    
    /**
     * Save preferences to localStorage
     */
    savePreferences() {
      if (options.persistLayout === false) return;
      
      try {
        const prefs = {
          sidebarState: this.sidebarState,
          panelWidth: this.panelWidth,
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
      } catch (e) {
        console.warn('Failed to save layout preferences:', e);
      }
    },
    
    /**
     * Check if sidebar is visible
     */
    get isSidebarVisible() {
      return this.sidebarState === 'expanded' || 
             this.sidebarState === 'collapsed' || 
             this.sidebarState === 'open';
    },
    
    /**
     * Check if sidebar is expanded
     */
    get isSidebarExpanded() {
      return this.sidebarState === 'expanded' || this.sidebarState === 'open';
    },
  };
}
