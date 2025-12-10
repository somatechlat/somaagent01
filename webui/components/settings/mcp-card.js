/**
 * MCP Card Component
 *
 * Settings card for MCP (Model Context Protocol) configuration.
 * Includes MCP Client and MCP Server settings.
 *
 * @module components/settings/mcp-card
 */

import { toastManager } from '../base/toast.js';

/**
 * MCP Card component factory
 * @param {Object} options - Card options
 * @param {Object} options.config - Current configuration
 * @param {Function} options.onChange - Change handler
 * @returns {Object} Alpine component data
 */
export default function McpCard(options = {}) {
  return {
    // MCP Client settings
    clientEnabled: options.config?.client_enabled ?? false,
    serverConfig: options.config?.server_config ?? '{}',
    initTimeout: options.config?.init_timeout ?? 30,
    toolTimeout: options.config?.tool_timeout ?? 60,

    // MCP Server settings
    serverEnabled: options.config?.server_enabled ?? false,
    serverToken: options.config?.server_token ?? '',

    // A2A Server settings
    a2aEnabled: options.config?.a2a_enabled ?? false,
    a2aEndpoint: options.config?.a2a_endpoint ?? '/a2a',

    // UI state
    configError: null,
    showToken: false,

    /**
     * Get title
     */
    get title() {
      return 'MCP / A2A';
    },

    /**
     * Get icon
     */
    get icon() {
      return '🔌';
    },

    /**
     * Get description
     */
    get description() {
      return 'Configure Model Context Protocol and Agent-to-Agent communication';
    },


    /**
     * Handle client enabled change
     * @param {boolean} value - New value
     */
    onClientEnabledChange(value) {
      this.clientEnabled = value;
      this.emitChange();
    },

    /**
     * Handle server config change
     * @param {string} value - JSON string
     */
    onServerConfigChange(value) {
      this.serverConfig = value;
      this.configError = null;
      try {
        JSON.parse(value);
        this.emitChange();
      } catch (e) {
        this.configError = 'Invalid JSON format';
      }
    },

    /**
     * Handle init timeout change
     * @param {number} value - New value
     */
    onInitTimeoutChange(value) {
      this.initTimeout = parseInt(value, 10);
      this.emitChange();
    },

    /**
     * Handle tool timeout change
     * @param {number} value - New value
     */
    onToolTimeoutChange(value) {
      this.toolTimeout = parseInt(value, 10);
      this.emitChange();
    },

    /**
     * Handle server enabled change
     * @param {boolean} value - New value
     */
    onServerEnabledChange(value) {
      this.serverEnabled = value;
      this.emitChange();
    },

    /**
     * Handle A2A enabled change
     * @param {boolean} value - New value
     */
    onA2aEnabledChange(value) {
      this.a2aEnabled = value;
      this.emitChange();
    },

    /**
     * Handle A2A endpoint change
     * @param {string} value - New value
     */
    onA2aEndpointChange(value) {
      this.a2aEndpoint = value;
      this.emitChange();
    },

    /**
     * Toggle token visibility
     */
    toggleTokenVisibility() {
      this.showToken = !this.showToken;
    },

    /**
     * Copy token to clipboard
     */
    async copyToken() {
      if (!this.serverToken) {
        toastManager.warning('No token', 'No token available to copy.');
        return;
      }
      try {
        await navigator.clipboard.writeText(this.serverToken);
        toastManager.success('Copied', 'Token copied to clipboard.');
      } catch (e) {
        toastManager.error('Copy failed', 'Unable to copy token.');
      }
    },

    /**
     * Regenerate server token
     */
    regenerateToken() {
      if (!confirm('Are you sure you want to regenerate the token? Existing connections will be invalidated.')) {
        return;
      }
      // Generate a new random token
      const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
      let token = '';
      for (let i = 0; i < 32; i++) {
        token += chars.charAt(Math.floor(Math.random() * chars.length));
      }
      this.serverToken = token;
      this.emitChange();
      toastManager.success('Token regenerated', 'New token has been generated.');
    },

    /**
     * Emit change to parent
     */
    emitChange() {
      const config = {
        client_enabled: this.clientEnabled,
        server_config: this.serverConfig,
        init_timeout: this.initTimeout,
        tool_timeout: this.toolTimeout,
        server_enabled: this.serverEnabled,
        server_token: this.serverToken,
        a2a_enabled: this.a2aEnabled,
        a2a_endpoint: this.a2aEndpoint,
      };
      options.onChange?.('mcp', config);
    },

    /**
     * Reset to defaults
     */
    resetDefaults() {
      this.clientEnabled = false;
      this.serverConfig = '{}';
      this.initTimeout = 30;
      this.toolTimeout = 60;
      this.serverEnabled = false;
      this.a2aEnabled = false;
      this.a2aEndpoint = '/a2a';
      this.configError = null;
      this.emitChange();
    },

    /**
     * Get masked token for display
     */
    get maskedToken() {
      if (!this.serverToken) return '';
      if (this.serverToken.length <= 8) return '••••••••';
      return this.serverToken.slice(0, 4) + '••••••••' + this.serverToken.slice(-4);
    },

    /**
     * Get display token based on visibility
     */
    get displayToken() {
      return this.showToken ? this.serverToken : this.maskedToken;
    },

    /**
     * Get summary text for collapsed state
     */
    get summary() {
      const parts = [];
      if (this.clientEnabled) parts.push('Client: On');
      if (this.serverEnabled) parts.push('Server: On');
      if (this.a2aEnabled) parts.push('A2A: On');
      if (parts.length === 0) parts.push('All disabled');
      return parts.join(' • ');
    },

    /**
     * Format JSON for display
     */
    formatJson() {
      try {
        const parsed = JSON.parse(this.serverConfig);
        this.serverConfig = JSON.stringify(parsed, null, 2);
        this.configError = null;
      } catch (e) {
        this.configError = 'Invalid JSON format';
      }
    },
  };
}
