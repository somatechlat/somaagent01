/**
 * Settings Feature Module
 * 
 * Public API for the Settings feature.
 * Re-exports store and API functions.
 * 
 * NOTE: The settingsModal Alpine component is pre-initialized in index.html
 * to ensure availability before Alpine processes the DOM (required for x-teleport).
 * The settingsModalProxy is defined in js/settings.js for backward compatibility.
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
 * Get the settings modal proxy (defined in js/settings.js)
 * @returns {Object} Settings modal proxy
 */
export function getSettingsModalProxy() {
  return globalThis.settingsModalProxy;
}

export default {
  store,
  api,
  getSettingsModalProxy,
};
