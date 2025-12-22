/**
 * SomaStack UI - Toast Component
 * Version: 1.0.0
 */

document.addEventListener('alpine:init', () => {
  // Toast container component
  Alpine.data('toastContainer', () => ({
    toasts: [],
    nextId: 1,
    defaultTimeout: 5000,
    
    init() {
      // Make toast functions globally available
      window.somaToast = {
        show: (message, options) => this.show(message, options),
        info: (message, options) => this.info(message, options),
        success: (message, options) => this.success(message, options),
        warning: (message, options) => this.warning(message, options),
        error: (message, options) => this.error(message, options),
        dismiss: (id) => this.dismiss(id),
        dismissAll: () => this.dismissAll()
      };
    },
    
    show(message, options = {}) {
      const id = this.nextId++;
      
      const toast = {
        id,
        message,
        variant: options.variant || 'info',
        visible: true,
        timeout: options.timeout !== undefined ? options.timeout : this.defaultTimeout,
        action: options.action || null,
        actionLabel: options.actionLabel || null
      };
      
      this.toasts.push(toast);
      
      // Auto-dismiss
      if (toast.timeout > 0) {
        setTimeout(() => {
          this.dismiss(id);
        }, toast.timeout);
      }
      
      return id;
    },
    
    info(message, options = {}) {
      return this.show(message, { ...options, variant: 'info' });
    },
    
    success(message, options = {}) {
      return this.show(message, { ...options, variant: 'success' });
    },
    
    warning(message, options = {}) {
      return this.show(message, { ...options, variant: 'warning' });
    },
    
    error(message, options = {}) {
      return this.show(message, { ...options, variant: 'error' });
    },
    
    dismiss(id) {
      const index = this.toasts.findIndex(t => t.id === id);
      if (index !== -1) {
        this.toasts[index].visible = false;
        
        // Remove after animation
        setTimeout(() => {
          this.toasts = this.toasts.filter(t => t.id !== id);
        }, 200);
      }
    },
    
    dismissAll() {
      this.toasts.forEach(t => t.visible = false);
      setTimeout(() => {
        this.toasts = [];
      }, 200);
    },
    
    getIcon(variant) {
      const icons = {
        info: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>`,
        success: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
        warning: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>`,
        error: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>`
      };
      return icons[variant] || icons.info;
    }
  }));
  
  // Alpine magic for toast
  Alpine.magic('toast', () => ({
    show: (message, options) => window.somaToast?.show(message, options),
    info: (message, options) => window.somaToast?.info(message, options),
    success: (message, options) => window.somaToast?.success(message, options),
    warning: (message, options) => window.somaToast?.warning(message, options),
    error: (message, options) => window.somaToast?.error(message, options),
    dismiss: (id) => window.somaToast?.dismiss(id),
    dismissAll: () => window.somaToast?.dismissAll()
  }));
});
