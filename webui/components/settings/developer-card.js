/**
 * Developer Card Component
 *
 * Settings card for developer/debug configuration.
 *
 * @module components/settings/developer-card
 */

/**
 * Shell interface options
 */
const SHELL_INTERFACES = [
  { value: 'local', label: 'Local Shell', icon: '💻' },
  { value: 'ssh', label: 'SSH Remote', icon: '🔗' },
];

/**
 * Developer Card component factory
 * @param {Object} options - Card options
 * @param {Object} options.config - Current configuration
 * @param {boolean} options.isDevelopment - Whether in development mode
 * @param {Function} options.onChange - Change handler
 * @returns {Object} Alpine component data
 */
export default function DeveloperCard(options = {}) {
  return {
    // Shell settings
    shellInterface: options.config?.shell_interface ?? 'local',
    shellInterfaces: SHELL_INTERFACES,

    // SSH settings
    sshHost: options.config?.ssh_host ?? '',
    sshPort: options.config?.ssh_port ?? 22,
    sshUser: options.config?.ssh_user ?? '',
    sshKeyPath: options.config?.ssh_key_path ?? '',

    // RFC connection settings
    rfcEnabled: options.config?.rfc_enabled ?? false,
    rfcHost: options.config?.rfc_host ?? 'localhost',
    rfcPort: options.config?.rfc_port ?? 8080,

    // Debug settings
    debugEnabled: options.config?.debug_enabled ?? false,
    verboseLogging: options.config?.verbose_logging ?? false,
    traceRequests: options.config?.trace_requests ?? false,

    // UI state
    isDevelopment: options.isDevelopment ?? false,

    /**
     * Get title
     */
    get title() {
      return 'Developer';
    },

    /**
     * Get icon
     */
    get icon() {
      return '🛠️';
    },

    /**
     * Get description
     */
    get description() {
      return 'Configure shell interface, RFC connections, and debug options';
    },


    /**
     * Check if SSH is selected
     */
    get isSsh() {
      return this.shellInterface === 'ssh';
    },

    /**
     * Get current shell interface object
     */
    get currentShellInterface() {
      return this.shellInterfaces.find((s) => s.value === this.shellInterface);
    },

    /**
     * Handle shell interface change
     * @param {string} value - New interface
     */
    onShellInterfaceChange(value) {
      this.shellInterface = value;
      this.emitChange();
    },

    /**
     * Handle SSH host change
     * @param {string} value - New host
     */
    onSshHostChange(value) {
      this.sshHost = value;
      this.emitChange();
    },

    /**
     * Handle SSH port change
     * @param {number} value - New port
     */
    onSshPortChange(value) {
      this.sshPort = parseInt(value, 10);
      this.emitChange();
    },

    /**
     * Handle SSH user change
     * @param {string} value - New user
     */
    onSshUserChange(value) {
      this.sshUser = value;
      this.emitChange();
    },

    /**
     * Handle SSH key path change
     * @param {string} value - New key path
     */
    onSshKeyPathChange(value) {
      this.sshKeyPath = value;
      this.emitChange();
    },

    /**
     * Handle RFC enabled change
     * @param {boolean} value - New value
     */
    onRfcEnabledChange(value) {
      this.rfcEnabled = value;
      this.emitChange();
    },

    /**
     * Handle RFC host change
     * @param {string} value - New host
     */
    onRfcHostChange(value) {
      this.rfcHost = value;
      this.emitChange();
    },

    /**
     * Handle RFC port change
     * @param {number} value - New port
     */
    onRfcPortChange(value) {
      this.rfcPort = parseInt(value, 10);
      this.emitChange();
    },

    /**
     * Handle debug enabled change
     * @param {boolean} value - New value
     */
    onDebugEnabledChange(value) {
      this.debugEnabled = value;
      this.emitChange();
    },

    /**
     * Handle verbose logging change
     * @param {boolean} value - New value
     */
    onVerboseLoggingChange(value) {
      this.verboseLogging = value;
      this.emitChange();
    },

    /**
     * Handle trace requests change
     * @param {boolean} value - New value
     */
    onTraceRequestsChange(value) {
      this.traceRequests = value;
      this.emitChange();
    },

    /**
     * Emit change to parent
     */
    emitChange() {
      const config = {
        shell_interface: this.shellInterface,
        ssh_host: this.sshHost,
        ssh_port: this.sshPort,
        ssh_user: this.sshUser,
        ssh_key_path: this.sshKeyPath,
        rfc_enabled: this.rfcEnabled,
        rfc_host: this.rfcHost,
        rfc_port: this.rfcPort,
        debug_enabled: this.debugEnabled,
        verbose_logging: this.verboseLogging,
        trace_requests: this.traceRequests,
      };
      options.onChange?.('developer', config);
    },

    /**
     * Reset to defaults
     */
    resetDefaults() {
      this.shellInterface = 'local';
      this.sshHost = '';
      this.sshPort = 22;
      this.sshUser = '';
      this.sshKeyPath = '';
      this.rfcEnabled = false;
      this.rfcHost = 'localhost';
      this.rfcPort = 8080;
      this.debugEnabled = false;
      this.verboseLogging = false;
      this.traceRequests = false;
      this.emitChange();
    },

    /**
     * Get summary text for collapsed state
     */
    get summary() {
      const parts = [];
      parts.push(`Shell: ${this.currentShellInterface?.label || this.shellInterface}`);
      if (this.rfcEnabled) parts.push('RFC: On');
      if (this.debugEnabled) parts.push('Debug: On');
      return parts.join(' • ');
    },
  };
}

export { SHELL_INTERFACES };
