/**
 * Backup Card Component
 *
 * Settings card for backup and restore functionality.
 *
 * @module components/settings/backup-card
 */

import { toastManager } from '../base/toast.js';

/**
 * Backup Card component factory
 * @param {Object} options - Card options
 * @param {Function} options.onBackup - Backup handler
 * @param {Function} options.onRestore - Restore handler
 * @returns {Object} Alpine component data
 */
export default function BackupCard(options = {}) {
  return {
    // UI state
    isCreatingBackup: false,
    isRestoring: false,
    showRestoreConfirm: false,
    selectedFile: null,
    lastBackup: options.lastBackup ?? null,

    /**
     * Get title
     */
    get title() {
      return 'Backup & Restore';
    },

    /**
     * Get icon
     */
    get icon() {
      return '💾';
    },

    /**
     * Get description
     */
    get description() {
      return 'Create backups and restore from previous backups';
    },

    /**
     * Format last backup date
     */
    get lastBackupFormatted() {
      if (!this.lastBackup) return 'Never';
      const date = new Date(this.lastBackup);
      return date.toLocaleString();
    },

    /**
     * Create a backup
     */
    async createBackup() {
      this.isCreatingBackup = true;

      try {
        const result = await options.onBackup?.();

        if (result?.blob) {
          // Trigger download
          const url = URL.createObjectURL(result.blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = result.filename || `backup-${Date.now()}.json`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);

          this.lastBackup = new Date().toISOString();
          toastManager.success('Backup created', 'Your backup file has been downloaded.');
        }
      } catch (err) {
        toastManager.error('Backup failed', err.message);
      } finally {
        this.isCreatingBackup = false;
      }
    },


    /**
     * Handle file selection
     * @param {Event} event - File input change event
     */
    onFileSelect(event) {
      const file = event.target.files?.[0];
      if (file) {
        this.selectedFile = file;
        this.showRestoreConfirm = true;
      }
    },

    /**
     * Open file picker
     */
    openFilePicker() {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = '.json';
      input.onchange = (e) => this.onFileSelect(e);
      input.click();
    },

    /**
     * Confirm and execute restore
     */
    async confirmRestore() {
      if (!this.selectedFile) {
        toastManager.error('No file', 'Please select a backup file first.');
        return;
      }

      this.isRestoring = true;
      this.showRestoreConfirm = false;

      try {
        // Read file content
        const content = await this.readFile(this.selectedFile);
        const data = JSON.parse(content);

        await options.onRestore?.(data);

        toastManager.success('Restore complete', 'Your settings have been restored. Please refresh the page.');
        this.selectedFile = null;
      } catch (err) {
        toastManager.error('Restore failed', err.message);
      } finally {
        this.isRestoring = false;
      }
    },

    /**
     * Cancel restore
     */
    cancelRestore() {
      this.showRestoreConfirm = false;
      this.selectedFile = null;
    },

    /**
     * Read file as text
     * @param {File} file - File to read
     * @returns {Promise<string>} File content
     */
    readFile(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.readAsText(file);
      });
    },

    /**
     * Get selected file name
     */
    get selectedFileName() {
      return this.selectedFile?.name ?? 'No file selected';
    },

    /**
     * Get summary text for collapsed state
     */
    get summary() {
      return `Last backup: ${this.lastBackupFormatted}`;
    },

    /**
     * Bind for backup button
     */
    get backupButton() {
      return {
        '@click': () => this.createBackup(),
        ':disabled': () => this.isCreatingBackup,
        ':class': () => ({
          'btn-loading': this.isCreatingBackup,
        }),
      };
    },

    /**
     * Bind for restore button
     */
    get restoreButton() {
      return {
        '@click': () => this.openFilePicker(),
        ':disabled': () => this.isRestoring,
      };
    },
  };
}
