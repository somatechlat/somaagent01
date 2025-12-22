/**
 * SomaStack UI - Modal Component
 * Version: 1.0.0
 */

document.addEventListener('alpine:init', () => {
  Alpine.data('modal', (config = {}) => ({
    isOpen: false,
    title: config.title || '',
    size: config.size || 'md',
    closeOnBackdrop: config.closeOnBackdrop !== false,
    closeOnEscape: config.closeOnEscape !== false,
    showFooter: config.showFooter !== false,
    onConfirm: config.onConfirm || null,
    onCancel: config.onCancel || null,
    
    previousActiveElement: null,
    
    init() {
      // Handle escape key globally
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && this.isOpen && this.closeOnEscape) {
          this.close();
        }
      });
    },
    
    open(options = {}) {
      // Store currently focused element
      this.previousActiveElement = document.activeElement;
      
      // Apply options
      if (options.title) this.title = options.title;
      if (options.size) this.size = options.size;
      if (options.onConfirm) this.onConfirm = options.onConfirm;
      if (options.onCancel) this.onCancel = options.onCancel;
      
      this.isOpen = true;
      
      // Prevent body scroll
      document.body.style.overflow = 'hidden';
      
      // Focus first focusable element in modal
      this.$nextTick(() => {
        const focusable = this.$el.querySelector(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusable) focusable.focus();
      });
    },
    
    close() {
      this.isOpen = false;
      
      // Restore body scroll
      document.body.style.overflow = '';
      
      // Restore focus
      if (this.previousActiveElement) {
        this.previousActiveElement.focus();
        this.previousActiveElement = null;
      }
      
      if (this.onCancel) {
        this.onCancel();
      }
    },
    
    confirm() {
      if (this.onConfirm) {
        const result = this.onConfirm();
        
        // If onConfirm returns a promise, wait for it
        if (result instanceof Promise) {
          result.then(() => this.close()).catch(() => {});
          return;
        }
        
        // If onConfirm returns false, don't close
        if (result === false) return;
      }
      
      this.isOpen = false;
      document.body.style.overflow = '';
      
      if (this.previousActiveElement) {
        this.previousActiveElement.focus();
        this.previousActiveElement = null;
      }
    },
    
    handleBackdropClick() {
      if (this.closeOnBackdrop) {
        this.close();
      }
    },
    
    // Focus trap
    handleTab(event) {
      const focusableElements = this.$el.querySelectorAll(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );
      
      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];
      
      if (event.shiftKey && document.activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
      } else if (!event.shiftKey && document.activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
    }
  }));
  
  // Global modal helper
  Alpine.magic('modal', () => ({
    open(id, options = {}) {
      const modal = document.querySelector(`[x-data*="modal"][data-modal-id="${id}"]`);
      if (modal && modal.__x) {
        modal.__x.$data.open(options);
      }
    },
    
    close(id) {
      const modal = document.querySelector(`[x-data*="modal"][data-modal-id="${id}"]`);
      if (modal && modal.__x) {
        modal.__x.$data.close();
      }
    }
  }));
});
