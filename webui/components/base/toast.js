/**
 * Toast/Notification Component
 * 
 * Toast notification system with auto-dismiss and stacking.
 * 
 * Usage:
 * // In Alpine store or component:
 * toastManager.show({ title: 'Success', message: 'Saved!', variant: 'success' });
 * 
 * // In HTML:
 * <div x-data="toastContainer()" class="toast-container">
 *   <template x-for="toast in toasts" :key="toast.id">
 *     <div x-bind="toastAttrs(toast)" class="toast">
 *       <div class="toast-content">
 *         <div class="toast-title" x-text="toast.title"></div>
 *         <div class="toast-message" x-text="toast.message"></div>
 *       </div>
 *       <button @click="dismiss(toast.id)" class="toast-close">×</button>
 *     </div>
 *   </template>
 * </div>
 * 
 * @module components/base/toast
 */

/**
 * Toast variants
 */
const VARIANTS = ['success', 'error', 'warning', 'info'];

/**
 * Toast manager singleton
 */
class ToastManager {
  constructor() {
    this.toasts = [];
    this.listeners = new Set();
    this.idCounter = 0;
    this.maxToasts = 5;
    this.defaultDuration = 5000;
  }
  
  /**
   * Subscribe to toast changes
   * @param {Function} listener - Callback function
   * @returns {Function} Unsubscribe function
   */
  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }
  
  /**
   * Notify all listeners
   */
  notify() {
    this.listeners.forEach(fn => fn([...this.toasts]));
  }
  
  /**
   * Show a toast notification
   * @param {Object} options - Toast options
   * @param {string} options.title - Toast title
   * @param {string} [options.message] - Toast message
   * @param {string} [options.variant='info'] - Toast variant
   * @param {number} [options.duration] - Auto-dismiss duration (0 = no auto-dismiss)
   * @param {boolean} [options.dismissible=true] - Can be dismissed
   * @returns {string} Toast ID
   */
  show(options) {
    const id = `toast-${++this.idCounter}`;
    const toast = {
      id,
      title: options.title ?? '',
      message: options.message ?? '',
      variant: VARIANTS.includes(options.variant) ? options.variant : 'info',
      duration: options.duration ?? this.defaultDuration,
      dismissible: options.dismissible ?? true,
      createdAt: Date.now(),
    };
    
    // Add to stack
    this.toasts.push(toast);
    
    // Limit stack size
    if (this.toasts.length > this.maxToasts) {
      this.toasts.shift();
    }
    
    this.notify();
    
    // Auto-dismiss
    if (toast.duration > 0) {
      setTimeout(() => this.dismiss(id), toast.duration);
    }
    
    return id;
  }
  
  /**
   * Dismiss a toast
   * @param {string} id - Toast ID
   */
  dismiss(id) {
    const index = this.toasts.findIndex(t => t.id === id);
    if (index !== -1) {
      this.toasts.splice(index, 1);
      this.notify();
    }
  }
  
  /**
   * Dismiss all toasts
   */
  dismissAll() {
    this.toasts = [];
    this.notify();
  }
  
  /**
   * Convenience methods
   */
  success(title, message) {
    return this.show({ title, message, variant: 'success' });
  }
  
  error(title, message) {
    return this.show({ title, message, variant: 'error', duration: 8000 });
  }
  
  warning(title, message) {
    return this.show({ title, message, variant: 'warning' });
  }
  
  info(title, message) {
    return this.show({ title, message, variant: 'info' });
  }
}

// Singleton instance
export const toastManager = new ToastManager();

/**
 * Toast container component factory
 * @returns {Object} Alpine component data
 */
export default function Toast() {
  return {
    toasts: [],
    
    init() {
      // Subscribe to toast manager
      this.toasts = [...toastManager.toasts];
      toastManager.subscribe((toasts) => {
        this.toasts = toasts;
      });
    },
    
    /**
     * Bind factory for toast elements
     * @param {Object} toast - Toast object
     */
    toastAttrs(toast) {
      return {
        ':class': () => `toast toast-${toast.variant}`,
        'x-transition:enter': 'transition ease-out duration-300',
        'x-transition:enter-start': 'opacity-0 translate-x-full',
        'x-transition:enter-end': 'opacity-100 translate-x-0',
        'x-transition:leave': 'transition ease-in duration-200',
        'x-transition:leave-start': 'opacity-100 translate-x-0',
        'x-transition:leave-end': 'opacity-0 translate-x-full',
        'role': 'alert',
        'aria-live': 'polite',
      };
    },
    
    /**
     * Dismiss a toast
     * @param {string} id - Toast ID
     */
    dismiss(id) {
      toastManager.dismiss(id);
    },
    
    /**
     * Dismiss all toasts
     */
    dismissAll() {
      toastManager.dismissAll();
    },
  };
}

export { VARIANTS };
