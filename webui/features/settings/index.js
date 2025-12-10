/**
 * Settings Feature Module
 * 
 * Public API for the Settings feature.
 * Re-exports store, API, and provides the Alpine component definition.
 * 
 * @module features/settings
 */

import * as store from './settings.store.js';
import * as api from './settings.api.js';

// Re-export store functions
export const {
  settingsStore,
  openSettings,
  closeSettings,
  switchTab,
  setSections,
  updateFilteredSections,
  setLoading,
  setError,
  getFieldValue,
  setFieldValue,
  onSettingsChange,
} = store;

// Re-export API functions
export const {
  fetchSettings,
  saveSettings,
  testConnection,
  getSetting,
  updateSetting,
} = api;

/**
 * Settings Modal Alpine Component Definition
 * 
 * This is the component factory function used by Alpine.js.
 * It's pre-initialized in index.html to ensure availability before Alpine processes the DOM.
 * 
 * @returns {Object} Alpine component definition
 */
export function settingsModalComponent() {
  return {
    // State
    settingsData: { sections: [] },
    filteredSections: [],
    activeTab: localStorage.getItem('settingsActiveTab') || 'agent',
    isLoading: true,
    isOpen: false,
    settings: { title: 'Settings' },

    // Lifecycle
    init() {
      // Sync isOpen with the global proxy (backward compatibility)
      this.isOpen = globalThis.settingsModalProxy?.isOpen || false;
      
      // Initialize with the store value
      const rootStore = Alpine.store('root');
      if (rootStore) {
        this.activeTab = rootStore.activeTab || 'agent';
      }

      // Watch store tab changes
      this.$watch('$store.root.activeTab', (newTab) => {
        if (typeof newTab !== 'undefined') {
          this.activeTab = newTab;
          localStorage.setItem('settingsActiveTab', newTab);
          this.updateFilteredSections();
        }
      });

      // Watch store isOpen changes
      this.$watch('$store.root.isOpen', (val) => {
        this.isOpen = val;
        if (val) {
          this.fetchSettings();
        }
      });

      // Load settings
      this.fetchSettings();
    },

    // Tab switching
    switchTab(tab) {
      this.activeTab = tab;
      const rootStore = Alpine.store('root');
      if (rootStore) {
        rootStore.activeTab = tab;
      }
      localStorage.setItem('settingsActiveTab', tab);
      this.updateFilteredSections();
    },

    // Fetch settings from API
    async fetchSettings() {
      try {
        this.isLoading = true;
        const { sections } = await api.fetchSettings();
        this.settingsData = { sections };
        this.updateFilteredSections();
      } catch (error) {
        console.error('Failed to fetch settings:', error);
      } finally {
        this.isLoading = false;
      }
    },

    // Filter sections by active tab
    updateFilteredSections() {
      const tab = this.activeTab;
      const sections = this.settingsData.sections || [];
      
      if (tab === 'scheduler') {
        this.filteredSections = [];
      } else {
        this.filteredSections = sections.filter(section => section.tab === tab);
      }
    },

    // Save settings
    async saveSettings() {
      try {
        // Validate required fields
        for (const section of this.settingsData.sections) {
          for (const field of section.fields) {
            if (field.required && (!field.value || field.value.trim() === '')) {
              console.error(`${field.title} in ${section.title} is required`);
              return;
            }
          }
        }

        // Build form data
        const formData = {};
        for (const section of this.settingsData.sections) {
          for (const field of section.fields) {
            formData[field.id] = field.value;
          }
        }

        await api.saveSettings(formData);
        console.log('Settings saved successfully');
        await this.fetchSettings();
      } catch (error) {
        console.error('Error saving settings:', error);
      }
    },

    // Handle field button actions
    handleFieldButton(field) {
      if (field.action === 'test_connection') {
        this.testConnection(field);
      } else if (field.action === 'reveal_token') {
        this.revealToken(field);
      } else if (field.action === 'generate_token') {
        this.generateToken(field);
      }
    },

    // Test API connection
    async testConnection(field) {
      try {
        field.testResult = 'Testing...';
        field.testStatus = 'loading';

        // Find the API key field
        let apiKey = '';
        for (const section of this.settingsData.sections) {
          for (const f of section.fields) {
            if (f.id === field.target) {
              apiKey = f.value;
              break;
            }
          }
        }

        if (!apiKey) {
          throw new Error('API key is required');
        }

        const result = await api.testConnection(field.service, apiKey);
        
        if (result.success) {
          field.testResult = 'Connection successful!';
          field.testStatus = 'success';
        } else {
          throw new Error(result.error || 'Connection failed');
        }
      } catch (error) {
        field.testResult = 'Failed: ' + error.message;
        field.testStatus = 'error';
      }
    },

    // Reveal/hide token
    revealToken(field) {
      for (const section of this.settingsData.sections) {
        for (const f of section.fields) {
          if (f.id === field.target) {
            f.type = f.type === 'password' ? 'text' : 'password';
            field.value = f.type === 'password' ? 'Show' : 'Hide';
            break;
          }
        }
      }
    },

    // Generate random token
    generateToken(field) {
      for (const section of this.settingsData.sections) {
        for (const f of section.fields) {
          if (f.id === field.target) {
            const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
            let token = '';
            for (let i = 0; i < 32; i++) {
              token += chars.charAt(Math.floor(Math.random() * chars.length));
            }
            f.value = token;
            break;
          }
        }
      }
    },

    // Close modal
    closeModal() {
      this.isOpen = false;
      if (this.$store && this.$store.root) {
        this.$store.root.isOpen = false;
      }
      if (globalThis.settingsModalProxy) {
        globalThis.settingsModalProxy.isOpen = false;
      }
    },

    // Handle cancel button
    handleCancel() {
      this.closeModal();
    }
  };
}

/**
 * Settings Modal Proxy
 * 
 * Global proxy object for opening/closing the settings modal.
 * Provides backward compatibility with existing code.
 */
export const settingsModalProxy = {
  isOpen: false,
  resolvePromise: null,
  activeTab: 'agent',
  settings: { sections: [] },
  
  openModal() {
    this.isOpen = true;
    const rootStore = globalThis.Alpine?.store('root');
    if (rootStore) {
      rootStore.isOpen = true;
    }
  },
  
  closeModal() {
    this.isOpen = false;
    const rootStore = globalThis.Alpine?.store('root');
    if (rootStore) {
      rootStore.isOpen = false;
    }
    if (this.resolvePromise) {
      this.resolvePromise({ status: 'cancelled' });
      this.resolvePromise = null;
    }
  }
};

// Export for global access
globalThis.settingsModalProxy = settingsModalProxy;

export default {
  store,
  api,
  settingsModalComponent,
  settingsModalProxy,
};
