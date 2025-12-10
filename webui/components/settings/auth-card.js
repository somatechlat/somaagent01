/**
 * Authentication Card Component
 *
 * Settings card for authentication configuration (username, password).
 *
 * @module components/settings/auth-card
 */

import { toastManager } from '../base/toast.js';

/**
 * Password strength levels
 */
const STRENGTH_LEVELS = {
  weak: { label: 'Weak', color: 'var(--error)', minScore: 0 },
  fair: { label: 'Fair', color: 'var(--warning)', minScore: 2 },
  good: { label: 'Good', color: 'var(--info)', minScore: 3 },
  strong: { label: 'Strong', color: 'var(--success)', minScore: 4 },
};

/**
 * Calculate password strength score
 * @param {string} password - Password to check
 * @returns {number} Score from 0-5
 */
function calculateStrength(password) {
  let score = 0;
  if (!password) return score;

  // Length checks
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;

  // Character variety checks
  if (/[a-z]/.test(password)) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^a-zA-Z0-9]/.test(password)) score++;

  return Math.min(score, 5);
}

/**
 * Auth Card component factory
 * @param {Object} options - Card options
 * @param {Object} options.config - Current configuration
 * @param {boolean} options.isDocker - Whether running in Docker
 * @param {Function} options.onChange - Change handler
 * @param {Function} options.onSave - Save handler
 * @returns {Object} Alpine component data
 */
export default function AuthCard(options = {}) {
  return {
    // Form state
    username: options.config?.username ?? '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
    rootPassword: '',
    rootPasswordConfirm: '',

    // UI state
    isDocker: options.isDocker ?? false,
    showCurrentPassword: false,
    showNewPassword: false,
    showRootPassword: false,
    isSaving: false,


    /**
     * Get title
     */
    get title() {
      return 'Authentication';
    },

    /**
     * Get icon
     */
    get icon() {
      return '🔐';
    },

    /**
     * Get description
     */
    get description() {
      return 'Configure login credentials and security settings';
    },

    /**
     * Calculate password strength
     */
    get passwordStrength() {
      const score = calculateStrength(this.newPassword);
      if (score >= 4) return STRENGTH_LEVELS.strong;
      if (score >= 3) return STRENGTH_LEVELS.good;
      if (score >= 2) return STRENGTH_LEVELS.fair;
      return STRENGTH_LEVELS.weak;
    },

    /**
     * Get strength percentage for progress bar
     */
    get strengthPercent() {
      const score = calculateStrength(this.newPassword);
      return (score / 5) * 100;
    },

    /**
     * Check if passwords match
     */
    get passwordsMatch() {
      return this.newPassword === this.confirmPassword;
    },

    /**
     * Check if root passwords match
     */
    get rootPasswordsMatch() {
      return this.rootPassword === this.rootPasswordConfirm;
    },

    /**
     * Check if form is valid
     */
    get isValid() {
      // Username required
      if (!this.username.trim()) return false;

      // If changing password, all fields required and must match
      if (this.newPassword) {
        if (!this.currentPassword) return false;
        if (!this.confirmPassword) return false;
        if (!this.passwordsMatch) return false;
        if (calculateStrength(this.newPassword) < 2) return false;
      }

      // If Docker and changing root password
      if (this.isDocker && this.rootPassword) {
        if (!this.rootPasswordConfirm) return false;
        if (!this.rootPasswordsMatch) return false;
      }

      return true;
    },

    /**
     * Handle username change
     * @param {string} value - New username
     */
    onUsernameChange(value) {
      this.username = value;
    },

    /**
     * Handle current password change
     * @param {string} value - Current password
     */
    onCurrentPasswordChange(value) {
      this.currentPassword = value;
    },

    /**
     * Handle new password change
     * @param {string} value - New password
     */
    onNewPasswordChange(value) {
      this.newPassword = value;
    },

    /**
     * Handle confirm password change
     * @param {string} value - Confirm password
     */
    onConfirmPasswordChange(value) {
      this.confirmPassword = value;
    },

    /**
     * Handle root password change
     * @param {string} value - Root password
     */
    onRootPasswordChange(value) {
      this.rootPassword = value;
    },

    /**
     * Handle root password confirm change
     * @param {string} value - Root password confirm
     */
    onRootPasswordConfirmChange(value) {
      this.rootPasswordConfirm = value;
    },

    /**
     * Toggle current password visibility
     */
    toggleCurrentPassword() {
      this.showCurrentPassword = !this.showCurrentPassword;
    },

    /**
     * Toggle new password visibility
     */
    toggleNewPassword() {
      this.showNewPassword = !this.showNewPassword;
    },

    /**
     * Toggle root password visibility
     */
    toggleRootPassword() {
      this.showRootPassword = !this.showRootPassword;
    },

    /**
     * Save authentication settings
     */
    async save() {
      if (!this.isValid) {
        toastManager.error('Invalid form', 'Please fix the errors before saving.');
        return;
      }

      this.isSaving = true;

      try {
        const data = {
          username: this.username,
        };

        if (this.newPassword) {
          data.current_password = this.currentPassword;
          data.new_password = this.newPassword;
        }

        if (this.isDocker && this.rootPassword) {
          data.root_password = this.rootPassword;
        }

        await options.onSave?.(data);

        // Clear password fields on success
        this.currentPassword = '';
        this.newPassword = '';
        this.confirmPassword = '';
        this.rootPassword = '';
        this.rootPasswordConfirm = '';

        toastManager.success('Saved', 'Authentication settings updated.');
      } catch (err) {
        toastManager.error('Save failed', err.message);
      } finally {
        this.isSaving = false;
      }
    },

    /**
     * Reset form
     */
    reset() {
      this.currentPassword = '';
      this.newPassword = '';
      this.confirmPassword = '';
      this.rootPassword = '';
      this.rootPasswordConfirm = '';
    },

    /**
     * Get summary text for collapsed state
     */
    get summary() {
      return `User: ${this.username || 'Not set'}`;
    },
  };
}

export { calculateStrength, STRENGTH_LEVELS };
