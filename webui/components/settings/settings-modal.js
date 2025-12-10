/**
 * Settings Modal Component
 * 
 * Full-screen settings modal with tabbed navigation.
 * Includes full ARIA accessibility support.
 * 
 * @module components/settings/settings-modal
 */

import {
  settingsStore,
  switchTab,
  closeSettings,
  setLoading,
  setSaving,
  setError,
  markDirty,
  showUnsavedDialog,
  hideUnsavedDialog,
  discardChanges,
} from '../../features/settings/settings.store.js';
import { fetchSettings, saveSettings } from '../../features/settings/settings.api.js';
import { toastManager } from '../base/toast.js';
import { ARIA_LABELS, announce, createFocusTrap } from '../../core/accessibility/index.js';

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
    get isOpen() {
      return settingsStore.isOpen;
    },
    get isLoading() {
      return settingsStore.isLoading;
    },
    get isSaving() {
      return settingsStore.isSaving;
    },
    get activeTab() {
      return settingsStore.activeTab;
    },
    get sections() {
      return settingsStore.filteredSections;
    },
    get error() {
      return settingsStore.error;
    },
    get isDirty() {
      return settingsStore.isDirty;
    },
    get showUnsavedDialog() {
      return settingsStore.showUnsavedDialog;
    },

    // Local state
    tabs: TABS,
    expandedCards: new Set(),
    formData: {},
    focusTrap: null,
    
    async init() {
      // Load settings when modal opens
      this.$watch('isOpen', async (open) => {
        if (open) {
          await this.loadSettings();
          // Set up focus trap
          this.$nextTick(() => {
            this.focusTrap = createFocusTrap(this.$el.querySelector('[role="dialog"]'));
            this.focusTrap.activate();
            announce('Settings dialog opened');
          });
        } else {
          // Deactivate focus trap
          this.focusTrap?.deactivate();
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
    async save() {
      setSaving(true);
      setError(null);

      try {
        await saveSettings(this.formData);
        // Update original sections to match current
        settingsStore.originalSections = JSON.parse(
          JSON.stringify(settingsStore.sections)
        );
        settingsStore.isDirty = false;
        toastManager.success(
          'Settings saved',
          'Your changes have been saved successfully.'
        );
      } catch (err) {
        setError(err.message);
        toastManager.error('Failed to save settings', err.message);
      } finally {
        setSaving(false);
      }
    },

    /**
     * Cancel and close (with confirmation if dirty)
     */
    cancel() {
      if (this.isDirty) {
        showUnsavedDialog();
      } else {
        closeSettings();
      }
    },

    /**
     * Confirm discard changes
     */
    confirmDiscard() {
      discardChanges();
    },

    /**
     * Cancel discard dialog
     */
    cancelDiscard() {
      hideUnsavedDialog();
    },
    
    /**
     * Handle field change
     * @param {string} fieldId - Field ID
     * @param {any} value - New value
     */
    onFieldChange(fieldId, value) {
      this.formData[fieldId] = value;
      markDirty();
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
        showUnsavedDialog();
        return;
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
        'aria-describedby': 'settings-description',
      };
    },
    
    /**
     * Bind for tab list
     */
    get tabList() {
      return {
        'role': 'tablist',
        'aria-label': 'Settings categories',
      };
    },
    
    /**
     * Bind factory for tab buttons
     * @param {Object} tab - Tab object
     * @param {number} index - Tab index
     */
    tabButton(tab, index) {
      return {
        'role': 'tab',
        'id': `settings-tab-${tab.id}`,
        ':aria-selected': () => this.activeTab === tab.id,
        ':aria-controls': () => `settings-panel-${tab.id}`,
        ':tabindex': () => this.activeTab === tab.id ? 0 : -1,
        '@click': () => this.switchTab(tab.id),
        '@keydown.arrow-right.prevent': () => this.focusNextTab(index),
        '@keydown.arrow-left.prevent': () => this.focusPrevTab(index),
        '@keydown.home.prevent': () => this.focusFirstTab(),
        '@keydown.end.prevent': () => this.focusLastTab(),
      };
    },
    
    /**
     * Bind factory for tab panels
     * @param {Object} tab - Tab object
     */
    tabPanel(tab) {
      return {
        'role': 'tabpanel',
        'id': `settings-panel-${tab.id}`,
        ':aria-labelledby': () => `settings-tab-${tab.id}`,
        ':hidden': () => this.activeTab !== tab.id,
        ':tabindex': () => 0,
      };
    },
    
    /**
     * Focus next tab
     * @param {number} currentIndex - Current tab index
     */
    focusNextTab(currentIndex) {
      const nextIndex = (currentIndex + 1) % this.tabs.length;
      this.switchTab(this.tabs[nextIndex].id);
      this.$nextTick(() => {
        document.getElementById(`settings-tab-${this.tabs[nextIndex].id}`)?.focus();
      });
    },
    
    /**
     * Focus previous tab
     * @param {number} currentIndex - Current tab index
     */
    focusPrevTab(currentIndex) {
      const prevIndex = (currentIndex - 1 + this.tabs.length) % this.tabs.length;
      this.switchTab(this.tabs[prevIndex].id);
      this.$nextTick(() => {
        document.getElementById(`settings-tab-${this.tabs[prevIndex].id}`)?.focus();
      });
    },
    
    /**
     * Focus first tab
     */
    focusFirstTab() {
      this.switchTab(this.tabs[0].id);
      this.$nextTick(() => {
        document.getElementById(`settings-tab-${this.tabs[0].id}`)?.focus();
      });
    },
    
    /**
     * Focus last tab
     */
    focusLastTab() {
      const lastTab = this.tabs[this.tabs.length - 1];
      this.switchTab(lastTab.id);
      this.$nextTick(() => {
        document.getElementById(`settings-tab-${lastTab.id}`)?.focus();
      });
    },
    
    /**
     * Bind for close button
     */
    get closeButton() {
      return {
        '@click': () => this.close(),
        'aria-label': ARIA_LABELS.settingsClose,
        'type': 'button',
      };
    },
    
    /**
     * Bind for save button
     */
    get saveButton() {
      return {
        '@click': () => this.save(),
        ':disabled': () => this.isSaving || !this.isDirty,
        ':aria-busy': () => this.isSaving,
        'aria-label': ARIA_LABELS.settingsSave,
        'type': 'button',
      };
    },
    
    /**
     * Bind for cancel button
     */
    get cancelButton() {
      return {
        '@click': () => this.cancel(),
        ':disabled': () => this.isSaving,
        'aria-label': ARIA_LABELS.settingsCancel,
        'type': 'button',
      };
    },
  };
}
