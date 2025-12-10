/**
 * Settings Store
 * 
 * Centralized state management for the Settings feature.
 * Handles settings data, active tab, and modal state.
 * 
 * @module features/settings/settings.store
 */

import { createStore, subscribe } from '../../core/state/store.js';

/**
 * Initial settings state
 */
const initialState = {
  // Modal state
  isOpen: false,
  isLoading: false,
  
  // Tab state
  activeTab: localStorage.getItem('settingsActiveTab') || 'agent',
  
  // Settings data
  sections: [],
  filteredSections: [],
  
  // UI state
  title: 'Settings',
  error: null,
};

/**
 * Settings store instance
 */
export const settingsStore = createStore('settings', initialState, {
  persist: true,
  persistKeys: ['activeTab'],
});

/**
 * Open the settings modal
 */
export function openSettings() {
  settingsStore.isOpen = true;
  
  // Also update Alpine root store for backward compatibility
  const rootStore = globalThis.Alpine?.store('root');
  if (rootStore) {
    rootStore.isOpen = true;
  }
}

/**
 * Close the settings modal
 */
export function closeSettings() {
  settingsStore.isOpen = false;
  settingsStore.error = null;
  
  // Also update Alpine root store for backward compatibility
  const rootStore = globalThis.Alpine?.store('root');
  if (rootStore) {
    rootStore.isOpen = false;
  }
}

/**
 * Switch to a different tab
 * @param {string} tabId - Tab identifier
 */
export function switchTab(tabId) {
  settingsStore.activeTab = tabId;
  localStorage.setItem('settingsActiveTab', tabId);
  
  // Update filtered sections
  updateFilteredSections();
  
  // Also update Alpine root store for backward compatibility
  const rootStore = globalThis.Alpine?.store('root');
  if (rootStore) {
    rootStore.activeTab = tabId;
  }
}

/**
 * Set settings sections data
 * @param {Array} sections - Settings sections from API
 */
export function setSections(sections) {
  settingsStore.sections = sections || [];
  updateFilteredSections();
}

/**
 * Update filtered sections based on active tab
 */
export function updateFilteredSections() {
  const tab = settingsStore.activeTab;
  const sections = settingsStore.sections || [];
  
  if (tab === 'scheduler') {
    settingsStore.filteredSections = [];
  } else {
    settingsStore.filteredSections = sections.filter(section => section.tab === tab);
  }
}

/**
 * Set loading state
 * @param {boolean} loading - Loading state
 */
export function setLoading(loading) {
  settingsStore.isLoading = loading;
}

/**
 * Set error state
 * @param {string|null} error - Error message or null
 */
export function setError(error) {
  settingsStore.error = error;
}

/**
 * Get a field value by ID
 * @param {string} fieldId - Field identifier
 * @returns {any} Field value or undefined
 */
export function getFieldValue(fieldId) {
  for (const section of settingsStore.sections) {
    for (const field of section.fields || []) {
      if (field.id === fieldId) {
        return field.value;
      }
    }
  }
  return undefined;
}

/**
 * Set a field value by ID
 * @param {string} fieldId - Field identifier
 * @param {any} value - New value
 */
export function setFieldValue(fieldId, value) {
  for (const section of settingsStore.sections) {
    for (const field of section.fields || []) {
      if (field.id === fieldId) {
        field.value = value;
        return;
      }
    }
  }
}

/**
 * Subscribe to settings changes
 * @param {Function} callback - Callback function
 * @returns {Function} Unsubscribe function
 */
export function onSettingsChange(callback) {
  return subscribe('settings', callback);
}

export default {
  store: settingsStore,
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
};
