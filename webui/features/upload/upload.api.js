/**
 * Upload API
 * 
 * API calls for the File Upload feature.
 * Handles multipart uploads with progress tracking.
 * 
 * @module features/upload/upload.api
 */

import { ENDPOINTS, buildUrl } from '../../core/api/endpoints.js';

/**
 * Upload a file with progress tracking
 * @param {File} file - File to upload
 * @param {Object} options - Upload options
 * @param {string} [options.sessionId] - Session ID
 * @param {Function} [options.onProgress] - Progress callback (0-100)
 * @param {AbortSignal} [options.signal] - Abort signal
 * @returns {Promise<Object>} Upload result
 */
export async function uploadFile(file, options = {}) {
  const formData = new FormData();
  formData.append('file', file);
  
  if (options.sessionId) {
    formData.append('session_id', options.sessionId);
  }
  
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    
    // Progress tracking
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        const progress = Math.round((e.loaded / e.total) * 100);
        options.onProgress?.(progress);
      }
    });
    
    // Completion
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const result = JSON.parse(xhr.responseText);
          resolve(result);
        } catch {
          resolve({ success: true });
        }
      } else {
        reject(new Error(xhr.responseText || `Upload failed: ${xhr.status}`));
      }
    });
    
    // Error
    xhr.addEventListener('error', () => {
      reject(new Error('Upload failed: Network error'));
    });
    
    // Abort
    xhr.addEventListener('abort', () => {
      reject(new Error('Upload cancelled'));
    });
    
    // Handle abort signal
    if (options.signal) {
      options.signal.addEventListener('abort', () => {
        xhr.abort();
      });
    }
    
    // Send request
    xhr.open('POST', buildUrl(ENDPOINTS.UPLOADS));
    xhr.withCredentials = true;
    xhr.send(formData);
  });
}

/**
 * Upload multiple files
 * @param {FileList|Array<File>} files - Files to upload
 * @param {Object} options - Upload options
 * @returns {Promise<Array>} Upload results
 */
export async function uploadFiles(files, options = {}) {
  const results = [];
  
  for (const file of files) {
    try {
      const result = await uploadFile(file, options);
      results.push({ file: file.name, success: true, result });
    } catch (err) {
      results.push({ file: file.name, success: false, error: err.message });
    }
  }
  
  return results;
}

/**
 * Get file icon based on type
 * @param {string} mimeType - MIME type
 * @returns {string} Icon emoji
 */
export function getFileIcon(mimeType) {
  if (!mimeType) return '📄';
  
  if (mimeType.startsWith('image/')) return '🖼️';
  if (mimeType.startsWith('video/')) return '🎬';
  if (mimeType.startsWith('audio/')) return '🎵';
  if (mimeType.includes('pdf')) return '📕';
  if (mimeType.includes('word') || mimeType.includes('document')) return '📝';
  if (mimeType.includes('excel') || mimeType.includes('spreadsheet')) return '📊';
  if (mimeType.includes('json')) return '📋';
  if (mimeType.includes('text')) return '📄';
  if (mimeType.includes('zip') || mimeType.includes('archive')) return '📦';
  
  return '📄';
}

/**
 * Format file size
 * @param {number} bytes - Size in bytes
 * @returns {string} Formatted size
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  const size = bytes / Math.pow(1024, i);
  
  return `${size.toFixed(i > 0 ? 1 : 0)} ${units[i]}`;
}

/**
 * Validate file
 * @param {File} file - File to validate
 * @param {Object} options - Validation options
 * @param {number} [options.maxSize] - Max size in bytes
 * @param {Array<string>} [options.allowedTypes] - Allowed MIME types
 * @returns {{valid: boolean, error?: string}}
 */
export function validateFile(file, options = {}) {
  if (options.maxSize && file.size > options.maxSize) {
    return {
      valid: false,
      error: `File too large. Maximum size is ${formatFileSize(options.maxSize)}`,
    };
  }
  
  if (options.allowedTypes && options.allowedTypes.length > 0) {
    const isAllowed = options.allowedTypes.some(type => {
      if (type.endsWith('/*')) {
        return file.type.startsWith(type.slice(0, -1));
      }
      return file.type === type;
    });
    
    if (!isAllowed) {
      return {
        valid: false,
        error: 'File type not allowed',
      };
    }
  }
  
  return { valid: true };
}

export default {
  uploadFile,
  uploadFiles,
  getFileIcon,
  formatFileSize,
  validateFile,
};
