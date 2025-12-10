/**
 * Upload Feature Module
 * 
 * Public API for the File Upload feature.
 * Re-exports store and API functions.
 * 
 * @module features/upload
 */

import * as store from './upload.store.js';
import * as api from './upload.api.js';

// Re-export store functions
export const {
  uploadStore,
  UPLOAD_STATUS,
  addUpload,
  updateProgress,
  completeUpload,
  failUpload,
  removeUpload,
  clearCompleted,
  setDragging,
  setUploading,
  setError,
  getPendingUploads,
  getActiveUploads,
  onUploadChange,
} = store;

// Re-export API functions
export const {
  uploadFile,
  uploadFiles,
  getFileIcon,
  formatFileSize,
  validateFile,
} = api;

export default {
  store,
  api,
};
