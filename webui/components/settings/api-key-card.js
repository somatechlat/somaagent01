/**
 * API Key Card Component
 * 
 * Settings card for API key management with masking and test connection.
 * 
 * @module components/settings/api-key-card
 */

import { testConnection } from '../../features/settings/settings.api.js';
import { toastManager } from '../base/toast.js';

/**
 * API Key Card component factory
 * @param {Object} options - Card options
 * @param {string} options.service - Service identifier
 * @param {string} options.label - Display label
 * @param {string} [options.value] - Current API key value
 * @param {string} [options.placeholder] - Input placeholder
 * @param {Function} options.onChange - Change handler
 * @returns {Object} Alpine component data
 */
export default function ApiKeyCard(options = {}) {
  return {
    service: options.service ?? '',
    label: options.label ?? 'API Key',
    value: options.value ?? '',
    placeholder: options.placeholder ?? 'Enter API key...',
    
    // UI state
    isVisible: false,
    isTesting: false,
    testResult: null, // 'success' | 'error' | null
    
    /**
     * Masked value for display
     */
    get maskedValue() {
      if (!this.value) return '';
      if (this.value.length <= 8) return '••••••••';
      return this.value.slice(0, 4) + '••••••••' + this.value.slice(-4);
    },
    
    /**
     * Display value based on visibility
     */
    get displayValue() {
      return this.isVisible ? this.value : this.maskedValue;
    },
    
    /**
     * Toggle visibility
     */
    toggleVisibility() {
      this.isVisible = !this.isVisible;
    },
    
    /**
     * Handle value change
     * @param {string} newValue - New API key
     */
    onValueChange(newValue) {
      this.value = newValue;
      this.testResult = null;
      options.onChange?.(this.service, newValue);
    },
    
    /**
     * Test the API key connection
     */
    async testKey() {
      if (!this.value) {
        toastManager.warning('No API key', 'Please enter an API key first.');
        return;
      }
      
      this.isTesting = true;
      this.testResult = null;
      
      try {
        const result = await testConnection(this.service, this.value);
        
        if (result.success) {
          this.testResult = 'success';
          toastManager.success('Connection successful', `${this.label} is working correctly.`);
        } else {
          this.testResult = 'error';
          toastManager.error('Connection failed', result.error || 'Unable to connect.');
        }
      } catch (err) {
        this.testResult = 'error';
        toastManager.error('Test failed', err.message);
      } finally {
        this.isTesting = false;
      }
    },
    
    /**
     * Clear the API key
     */
    clearKey() {
      if (confirm('Are you sure you want to clear this API key?')) {
        this.value = '';
        this.testResult = null;
        options.onChange?.(this.service, '');
      }
    },
    
    /**
     * Bind for input element
     */
    get input() {
      return {
        ':type': () => this.isVisible ? 'text' : 'password',
        ':value': () => this.value,
        '@input': (e) => this.onValueChange(e.target.value),
        ':placeholder': () => this.placeholder,
        'autocomplete': 'off',
        'class': 'input',
      };
    },
    
    /**
     * Bind for visibility toggle button
     */
    get visibilityToggle() {
      return {
        '@click': () => this.toggleVisibility(),
        ':aria-label': () => this.isVisible ? 'Hide API key' : 'Show API key',
        ':title': () => this.isVisible ? 'Hide' : 'Show',
      };
    },
    
    /**
     * Bind for test button
     */
    get testButton() {
      return {
        '@click': () => this.testKey(),
        ':disabled': () => this.isTesting || !this.value,
        ':class': () => ({
          'btn-loading': this.isTesting,
        }),
      };
    },
    
    /**
     * Get status indicator class
     */
    get statusClass() {
      if (this.testResult === 'success') return 'badge-success';
      if (this.testResult === 'error') return 'badge-error';
      return '';
    },
  };
}
