/**
 * Upload Store
 * 
 * Centralized state management for the File Upload feature.
 * 
 * @module features/upload/upload.store
 */

import { createStore, subscribe } from '../../core/state/store.js';

/**
 * Upload status types
 */
export const UPLOAD_STATUS = Object.freeze({
  PENDING: 'pending',
  UPLOADING: 'uploading',
  PROCESSING: 'processing',
  COMPLETE: 'complete',
  ERROR: 'error',
});

/**
 * Initial upload state
 */
const initialState = {
  // Upload queue
  uploads: [],
  
  // Current upload
  currentUploadId: null,
  
  // UI state
  isDragging: false,
  isUploading: false,
  error: null,
};

/**
 * Upload store instance
 */
export const uploadStore = createStore('upload', initialState, {
  persist: false,
});

/**
 * Add file to upload queue
 * @param {File} file - File to upload
 * @returns {string} Upload ID
 */
export function addUpload(file) {
  const id = crypto.randomUUID();
  const upload = {
    id,
    file,
    name: file.name,
    size: file.size,
    type: file.type,
    status: UPLOAD_STATUS.PENDING,
    progress: 0,
    error: null,
    preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : null,
    createdAt: new Date().toISOString(),
  };
  
  uploadStore.uploads = [...uploadStore.uploads, upload];
  return id;
}

/**
 * Update upload progress
 * @param {string} uploadId - Upload ID
 * @param {number} progress - Progress 0-100
 */
export function updateProgress(uploadId, progress) {
  const index = uploadStore.uploads.findIndex(u => u.id === uploadId);
  if (index >= 0) {
    uploadStore.uploads[index] = {
      ...uploadStore.uploads[index],
      progress,
      status: progress < 100 ? UPLOAD_STATUS.UPLOADING : UPLOAD_STATUS.PROCESSING,
    };
    uploadStore.uploads = [...uploadStore.uploads];
  }
}

/**
 * Mark upload as complete
 * @param {string} uploadId - Upload ID
 * @param {Object} result - Upload result
 */
export function completeUpload(uploadId, result) {
  const index = uploadStore.uploads.findIndex(u => u.id === uploadId);
  if (index >= 0) {
    uploadStore.uploads[index] = {
      ...uploadStore.uploads[index],
      status: UPLOAD_STATUS.COMPLETE,
      progress: 100,
      result,
    };
    uploadStore.uploads = [...uploadStore.uploads];
  }
}

/**
 * Mark upload as failed
 * @param {string} uploadId - Upload ID
 * @param {string} error - Error message
 */
export function failUpload(uploadId, error) {
  const index = uploadStore.uploads.findIndex(u => u.id === uploadId);
  if (index >= 0) {
    uploadStore.uploads[index] = {
      ...uploadStore.uploads[index],
      status: UPLOAD_STATUS.ERROR,
      error,
    };
    uploadStore.uploads = [...uploadStore.uploads];
  }
}

/**
 * Remove upload from queue
 * @param {string} uploadId - Upload ID
 */
export function removeUpload(uploadId) {
  const upload = uploadStore.uploads.find(u => u.id === uploadId);
  if (upload?.preview) {
    URL.revokeObjectURL(upload.preview);
  }
  uploadStore.uploads = uploadStore.uploads.filter(u => u.id !== uploadId);
}

/**
 * Clear completed uploads
 */
export function clearCompleted() {
  uploadStore.uploads.forEach(u => {
    if (u.preview && u.status === UPLOAD_STATUS.COMPLETE) {
      URL.revokeObjectURL(u.preview);
    }
  });
  uploadStore.uploads = uploadStore.uploads.filter(u => u.status !== UPLOAD_STATUS.COMPLETE);
}

/**
 * Set dragging state
 * @param {boolean} dragging - Dragging state
 */
export function setDragging(dragging) {
  uploadStore.isDragging = dragging;
}

/**
 * Set uploading state
 * @param {boolean} uploading - Uploading state
 */
export function setUploading(uploading) {
  uploadStore.isUploading = uploading;
}

/**
 * Set error state
 * @param {string|null} error - Error message
 */
export function setError(error) {
  uploadStore.error = error;
}

/**
 * Get pending uploads
 * @returns {Array} Pending uploads
 */
export function getPendingUploads() {
  return uploadStore.uploads.filter(u => u.status === UPLOAD_STATUS.PENDING);
}

/**
 * Get active uploads
 * @returns {Array} Active uploads
 */
export function getActiveUploads() {
  return uploadStore.uploads.filter(u => 
    u.status === UPLOAD_STATUS.UPLOADING || u.status === UPLOAD_STATUS.PROCESSING
  );
}

/**
 * Subscribe to upload changes
 * @param {Function} callback - Callback function
 * @returns {Function} Unsubscribe function
 */
export function onUploadChange(callback) {
  return subscribe('upload', callback);
}

export default {
  store: uploadStore,
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
};
