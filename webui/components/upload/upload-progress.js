/**
 * Upload Progress Component
 * 
 * Displays upload progress with file info.
 * 
 * @module components/upload/upload-progress
 */

import { 
  uploadStore, 
  UPLOAD_STATUS,
  removeUpload, 
  clearCompleted,
} from '../../features/upload/index.js';
import { getFileIcon, formatFileSize } from '../../features/upload/upload.api.js';

/**
 * Upload Progress component factory
 * @returns {Object} Alpine component data
 */
export default function UploadProgress() {
  return {
    // State from store
    get uploads() { return uploadStore.uploads; },
    
    /**
     * Check if there are any uploads
     */
    get hasUploads() {
      return this.uploads.length > 0;
    },
    
    /**
     * Check if there are completed uploads
     */
    get hasCompleted() {
      return this.uploads.some(u => u.status === UPLOAD_STATUS.COMPLETE);
    },
    
    /**
     * Get status text
     * @param {string} status - Upload status
     * @returns {string} Status text
     */
    getStatusText(status) {
      switch (status) {
        case UPLOAD_STATUS.PENDING: return 'Pending';
        case UPLOAD_STATUS.UPLOADING: return 'Uploading';
        case UPLOAD_STATUS.PROCESSING: return 'Processing';
        case UPLOAD_STATUS.COMPLETE: return 'Complete';
        case UPLOAD_STATUS.ERROR: return 'Failed';
        default: return 'Unknown';
      }
    },
    
    /**
     * Get status class
     * @param {string} status - Upload status
     * @returns {string} CSS class
     */
    getStatusClass(status) {
      switch (status) {
        case UPLOAD_STATUS.COMPLETE: return 'badge-success';
        case UPLOAD_STATUS.ERROR: return 'badge-error';
        case UPLOAD_STATUS.UPLOADING:
        case UPLOAD_STATUS.PROCESSING: return 'badge-info';
        default: return '';
      }
    },
    
    /**
     * Get file icon
     * @param {string} type - MIME type
     * @returns {string} Icon
     */
    getIcon(type) {
      return getFileIcon(type);
    },
    
    /**
     * Format file size
     * @param {number} bytes - Size in bytes
     * @returns {string} Formatted size
     */
    formatSize(bytes) {
      return formatFileSize(bytes);
    },
    
    /**
     * Remove an upload
     * @param {string} uploadId - Upload ID
     */
    remove(uploadId) {
      removeUpload(uploadId);
    },
    
    /**
     * Clear all completed uploads
     */
    clearAll() {
      clearCompleted();
    },
    
    /**
     * Check if upload is in progress
     * @param {Object} upload - Upload object
     * @returns {boolean}
     */
    isInProgress(upload) {
      return upload.status === UPLOAD_STATUS.UPLOADING || 
             upload.status === UPLOAD_STATUS.PROCESSING;
    },
  };
}
