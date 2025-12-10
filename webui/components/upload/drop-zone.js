/**
 * Drop Zone Component
 * 
 * Drag-and-drop file upload zone.
 * 
 * @module components/upload/drop-zone
 */

import { 
  uploadStore, 
  addUpload, 
  updateProgress, 
  completeUpload, 
  failUpload,
  setDragging,
  setUploading,
} from '../../features/upload/index.js';
import { uploadFile, validateFile, getFileIcon, formatFileSize } from '../../features/upload/upload.api.js';
import { toastManager } from '../base/toast.js';

/**
 * Drop Zone component factory
 * @param {Object} options - Component options
 * @param {string} [options.sessionId] - Session ID for uploads
 * @param {number} [options.maxSize] - Max file size in bytes
 * @param {Array<string>} [options.allowedTypes] - Allowed MIME types
 * @param {Function} [options.onUpload] - Upload complete callback
 * @returns {Object} Alpine component data
 */
export default function DropZone(options = {}) {
  return {
    // State from store
    get isDragging() { return uploadStore.isDragging; },
    get uploads() { return uploadStore.uploads; },
    get isUploading() { return uploadStore.isUploading; },
    
    // Local state
    dragCounter: 0,
    
    /**
     * Handle drag enter
     * @param {DragEvent} e - Drag event
     */
    onDragEnter(e) {
      e.preventDefault();
      this.dragCounter++;
      if (this.dragCounter === 1) {
        setDragging(true);
      }
    },
    
    /**
     * Handle drag leave
     * @param {DragEvent} e - Drag event
     */
    onDragLeave(e) {
      e.preventDefault();
      this.dragCounter--;
      if (this.dragCounter === 0) {
        setDragging(false);
      }
    },
    
    /**
     * Handle drag over
     * @param {DragEvent} e - Drag event
     */
    onDragOver(e) {
      e.preventDefault();
    },
    
    /**
     * Handle drop
     * @param {DragEvent} e - Drop event
     */
    async onDrop(e) {
      e.preventDefault();
      this.dragCounter = 0;
      setDragging(false);
      
      const files = e.dataTransfer?.files;
      if (files?.length) {
        await this.uploadFiles(files);
      }
    },
    
    /**
     * Handle file input change
     * @param {Event} e - Change event
     */
    async onFileSelect(e) {
      const files = e.target.files;
      if (files?.length) {
        await this.uploadFiles(files);
        e.target.value = ''; // Reset input
      }
    },
    
    /**
     * Upload files
     * @param {FileList} files - Files to upload
     */
    async uploadFiles(files) {
      setUploading(true);
      
      for (const file of files) {
        // Validate file
        const validation = validateFile(file, {
          maxSize: options.maxSize,
          allowedTypes: options.allowedTypes,
        });
        
        if (!validation.valid) {
          toastManager.error('Upload failed', validation.error);
          continue;
        }
        
        // Add to queue
        const uploadId = addUpload(file);
        
        try {
          const result = await uploadFile(file, {
            sessionId: options.sessionId,
            onProgress: (progress) => updateProgress(uploadId, progress),
          });
          
          completeUpload(uploadId, result);
          options.onUpload?.(file, result);
          toastManager.success('Upload complete', `${file.name} uploaded successfully.`);
        } catch (err) {
          failUpload(uploadId, err.message);
          toastManager.error('Upload failed', err.message);
        }
      }
      
      setUploading(false);
    },
    
    /**
     * Open file picker
     */
    openFilePicker() {
      this.$refs.fileInput?.click();
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
     * Bind for drop zone container
     */
    get zone() {
      return {
        '@dragenter': (e) => this.onDragEnter(e),
        '@dragleave': (e) => this.onDragLeave(e),
        '@dragover': (e) => this.onDragOver(e),
        '@drop': (e) => this.onDrop(e),
        ':class': () => ({
          'drop-zone': true,
          'drop-zone-active': this.isDragging,
        }),
      };
    },
    
    /**
     * Bind for file input
     */
    get fileInput() {
      return {
        'x-ref': 'fileInput',
        'type': 'file',
        'multiple': true,
        ':accept': () => options.allowedTypes?.join(',') || '*',
        '@change': (e) => this.onFileSelect(e),
        'class': 'sr-only',
      };
    },
  };
}
