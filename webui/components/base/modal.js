/**
 * Modal Component
 * 
 * Accessible modal dialog with focus trap and keyboard handling.
 * 
 * Usage:
 * <div x-data="modal()">
 *   <button @click="open()">Open Modal</button>
 *   <template x-teleport="body">
 *     <div x-bind="backdrop" class="modal-backdrop">
 *       <div x-bind="dialog" class="modal">
 *         <div class="modal-header">
 *           <h2 class="modal-title">Title</h2>
 *           <button @click="close()" class="btn btn-icon">×</button>
 *         </div>
 *         <div class="modal-body">Content</div>
 *       </div>
 *     </div>
 *   </template>
 * </div>
 * 
 * @module components/base/modal
 */

/**
 * Modal component factory
 * @param {Object} options - Modal options
 * @param {boolean} [options.isOpen=false] - Initial open state
 * @param {boolean} [options.closeOnBackdrop=true] - Close on backdrop click
 * @param {boolean} [options.closeOnEscape=true] - Close on Escape key
 * @param {Function} [options.onOpen] - Open callback
 * @param {Function} [options.onClose] - Close callback
 * @returns {Object} Alpine component data
 */
export default function Modal(options = {}) {
  return {
    isOpen: options.isOpen ?? false,
    previousActiveElement: null,
    
    init() {
      // Handle escape key globally
      if (options.closeOnEscape !== false) {
        document.addEventListener('keydown', (e) => {
          if (e.key === 'Escape' && this.isOpen) {
            this.close();
          }
        });
      }
    },
    
    /**
     * Bind object for backdrop element
     */
    get backdrop() {
      return {
        'x-show': () => this.isOpen,
        'x-transition:enter': 'transition ease-out duration-200',
        'x-transition:enter-start': 'opacity-0',
        'x-transition:enter-end': 'opacity-100',
        'x-transition:leave': 'transition ease-in duration-150',
        'x-transition:leave-start': 'opacity-100',
        'x-transition:leave-end': 'opacity-0',
        ':data-open': () => this.isOpen,
        '@click.self': () => {
          if (options.closeOnBackdrop !== false) {
            this.close();
          }
        },
        'aria-hidden': () => !this.isOpen,
      };
    },
    
    /**
     * Bind object for dialog element
     */
    get dialog() {
      return {
        'x-show': () => this.isOpen,
        'x-transition:enter': 'transition ease-out duration-200',
        'x-transition:enter-start': 'opacity-0 scale-95',
        'x-transition:enter-end': 'opacity-100 scale-100',
        'x-transition:leave': 'transition ease-in duration-150',
        'x-transition:leave-start': 'opacity-100 scale-100',
        'x-transition:leave-end': 'opacity-0 scale-95',
        ':data-open': () => this.isOpen,
        'role': 'dialog',
        'aria-modal': 'true',
        '@keydown.tab': (e) => this.trapFocus(e),
      };
    },
    
    /**
     * Open the modal
     */
    open() {
      this.previousActiveElement = document.activeElement;
      this.isOpen = true;
      
      // Prevent body scroll
      document.body.style.overflow = 'hidden';
      
      // Focus first focusable element
      this.$nextTick(() => {
        const focusable = this.$el.querySelector(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        focusable?.focus();
      });
      
      options.onOpen?.();
    },
    
    /**
     * Close the modal
     */
    close() {
      this.isOpen = false;
      
      // Restore body scroll
      document.body.style.overflow = '';
      
      // Restore focus
      this.previousActiveElement?.focus();
      
      options.onClose?.();
    },
    
    /**
     * Toggle modal state
     */
    toggle() {
      if (this.isOpen) {
        this.close();
      } else {
        this.open();
      }
    },
    
    /**
     * Trap focus within modal
     * @param {KeyboardEvent} e - Keyboard event
     */
    trapFocus(e) {
      const focusableElements = this.$el.querySelectorAll(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );
      
      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];
      
      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement?.focus();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement?.focus();
      }
    },
  };
}
