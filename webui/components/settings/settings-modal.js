/**
 * Settings Modal Component
 * 
 * Full-screen settings modal with tabbed navigation.
 * 
 * @module components/settings/settings-modal
 */

import { settingsStore, switchTab, closeSettings, setLoading, setError } from '../../features/settings/settings.store.js';
import { fetchSettings, saveSettings } from '../../features/settings/settings.api.js';
import { toastManager } from '../base/toast.js';

/**
 * Settings tabs configuration
 */
const TABS = [
  { id: 'agent', label: 'Agent', icon: '🤖' },
  { id: 'external', label: 'External', icon: '🔌' },
  { id: 'connectivity', label: 'Connectivity', icon: '🌐' },
  { id: 'system', label: 'System', icon: '⚙️' },
];

/**
 * Settings Modal component factory
 * @returns {Object} Alpine component data
 */
export default function SettingsModal() {
  return {
    // State from store
    get isOpen() { return settingsStore.isOpen; },
    get isLoading() { return settingsStore.isLoading; },
    get activeTab() { return settingsStore.activeTab; },
    get sections() { return settingsStore.filteredSections; },
    get error() { return settingsStore.error; },
    
    // Local state
    tabs: TABS,
    isDirty: false,
    expandedCards: new Set(),
    formData: {},
    
    async init() {
      // Load settings when modal opens
      this.$watch('isOpen', async (open) => {
        if (open) {
          await this.loadSettings();
        }
      });
    },
    
    /**
     * Load settings from API
     */
    async loadSettings() {
      setLoading(true);
      setError(null);
      
      try {
        const { sections } = await fetchSettings();
        settingsStore.sections = sections;
        
        // Initialize form data from sections
        this.formData = {};
        for (const section of sections) {
          for (const field of section.fields || []) {
            this.formData[field.id] = field.value;
          }
        }
        
        this.isDirty = false;
      } catch (err) {
        setError(err.message);
        toastManager.error('Failed to load settings', err.message);
      } finally {
        setLoading(false);
      }
    },
    
    /**
     * Save settings to API
     */
    async saveSettings() {
      setLoading(true);
      setError(null);
      
      try {
        await saveSettings(this.formData);
        this.isDirty = false;
        toastManager.success('Settings saved', 'Your changes have been saved successfully.');
      } catch (err) {
        setError(err.message);
        toastManager.error('Failed to save settings', err.message);
      } finally {
        setLoading(false);
      }
    },
    
    /**
     * Handle field change
     * @param {string} fieldId - Field ID
     * @param {any} value - New value
     */
    onFieldChange(fieldId, value) {
      this.formData[fieldId] = value;
      this.isDirty = true;
    },
    
    /**
     * Switch tab
     * @param {string} tabId - Tab ID
     */
    switchTab(tabId) {
      switchTab(tabId);
    },
    
    /**
     * Close modal with confirmation if dirty
     */
    close() {
      if (this.isDirty) {
        if (!confirm('You have unsaved changes. Are you sure you want to close?')) {
          return;
        }
      }
      closeSettings();
    },
    
    /**
     * Toggle card expansion
     * @param {string} cardId - Card ID
     */
    toggleCard(cardId) {
      if (this.expandedCards.has(cardId)) {
        this.expandedCards.delete(cardId);
      } else {
        this.expandedCards.add(cardId);
      }
      // Force reactivity
      this.expandedCards = new Set(this.expandedCards);
    },
    
    /**
     * Check if card is expanded
     * @param {string} cardId - Card ID
     * @returns {boolean}
     */
    isCardExpanded(cardId) {
      return this.expandedCards.has(cardId);
    },
    
    /**
     * Expand all cards
     */
    expandAll() {
      for (const section of this.sections) {
        this.expandedCards.add(section.id);
      }
      this.expandedCards = new Set(this.expandedCards);
    },
    
    /**
     * Collapse all cards
     */
    collapseAll() {
      this.expandedCards.clear();
      this.expandedCards = new Set();
    },
    
    /**
     * Bind for backdrop
     */
    get backdrop() {
      return {
        'x-show': () => this.isOpen,
        'x-transition:enter': 'transition ease-out duration-200',
        'x-transition:enter-start': 'opacity-0',
        'x-transition:enter-end': 'opacity-100',
        'x-transition:leave': 'transition ease-in duration-150',
        'x-transition:leave-start': 'opacity-100',
        'x-transition:leave-end': 'opacity-0',
        '@click.self': () => this.close(),
        '@keydown.escape.window': () => this.close(),
      };
    },
    
    /**
     * Bind for modal dialog
     */
    get dialog() {
      return {
        'x-show': () => this.isOpen,
        'x-transition:enter': 'transition ease-out duration-200',
        'x-transition:enter-start': 'opacity-0 scale-95',
        'x-transition:enter-end': 'opacity-100 scale-100',
        'x-transition:leave': 'transition ease-in duration-150',
        'x-transition:leave-start': 'opacity-100 scale-100',
        'x-transition:leave-end': 'opacity-0 scale-95',
        'role': 'dialog',
        'aria-modal': 'true',
        'aria-labelledby': 'settings-title',
      };
    },
  };
}
