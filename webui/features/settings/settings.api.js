/**
 * Settings API
 * 
 * API calls for the Settings feature.
 * All backend communication for settings goes through this module.
 * 
 * @module features/settings/settings.api
 */

import { fetchApi } from '../../core/api/client.js';
import { ENDPOINTS, buildUrl } from '../../core/api/endpoints.js';

/**
 * Fetch all settings sections from the backend
 * @returns {Promise<{sections: Array}>} Settings data
 */
export async function fetchSettings() {
  const response = await fetchApi(buildUrl(ENDPOINTS.SETTINGS_SECTIONS));
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Failed to fetch settings: ${response.status}`);
  }
  
  const data = await response.json();
  
  // Normalize response - backend may return sections in different formats
  let sections = data?.sections || data?.settings?.sections || data?.data?.sections;
  if (!Array.isArray(sections)) {
    sections = [];
  }
  
  return { sections };
}

/**
 * Save settings to the backend
 * @param {Object} formData - Key-value pairs of field IDs and values
 * @returns {Promise<void>}
 */
export async function saveSettings(formData) {
  const response = await fetchApi(buildUrl(ENDPOINTS.SETTINGS_SECTIONS), {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ data: formData }),
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Failed to save settings: ${response.status}`);
  }
  
  return response.json();
}

/**
 * Test connection to an external service
 * @param {string} service - Service identifier (e.g., 'openai', 'anthropic')
 * @param {string} apiKey - API key to test
 * @returns {Promise<{success: boolean, error?: string}>}
 */
export async function testConnection(service, apiKey) {
  const response = await fetchApi(buildUrl(ENDPOINTS.TEST_CONNECTION), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      service,
      api_key: apiKey,
    }),
  });
  
  const data = await response.json();
  
  if (!response.ok || !data.success) {
    return {
      success: false,
      error: data.error || 'Connection failed',
    };
  }
  
  return { success: true };
}

/**
 * Get a specific setting value
 * @param {string} key - Setting key
 * @returns {Promise<any>} Setting value
 */
export async function getSetting(key) {
  const { sections } = await fetchSettings();
  
  for (const section of sections) {
    for (const field of section.fields || []) {
      if (field.id === key) {
        return field.value;
      }
    }
  }
  
  return undefined;
}

/**
 * Update a specific setting value
 * @param {string} key - Setting key
 * @param {any} value - New value
 * @returns {Promise<void>}
 */
export async function updateSetting(key, value) {
  return saveSettings({ [key]: value });
}

export default {
  fetchSettings,
  saveSettings,
  testConnection,
  getSetting,
  updateSetting,
};
