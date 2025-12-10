/**
 * Panel Component
 * 
 * Slide-in detail panel for secondary content.
 * 
 * Usage:
 * <aside x-data="panel()" x-bind="container" class="app-panel">
 *   <div class="panel-content">
 *     <div class="panel-header">
 *       <h2 class="panel-title" x-text="title"></h2>
 *       <button @click="close()" class="btn btn-icon">×</button>
 *     </div>
 *     <div class="panel-body">
 *       <!-- Panel content -->
 *     </div>
 *   </div>
 * </aside>
 * 
 * @module components/layout/panel
 */

/**
 * Panel component factory
 * @param {Object} options - Panel options
 * @param {boolean} [options.isOpen=false] - Initial open state
 * @param {string} [options.title=''] - Panel title
 * @param {number} [options.width=320] - Panel width
 * @param {Function} [options.onOpen] - Open callback
 * @param {Function} [options.onClose] - Close callback
 * @returns {Object} Alpine component data
 */
export default function Panel(options = {}) {
  return {
    isOpen: options.isOpen ?? false,
    title: options.title ?? '',
    width: options.width ?? 320,
    
    /**
     * Bind object for panel container
     */
    get container() {
      return {
        ':data-open': () => this.isOpen,
        ':style': () => this.isOpen ? `width: ${this.width}px` : 'width: 0',
      };
    },
    
    /**
     * Open the panel
     * @param {Object} [config] - Optional config
     * @param {string} [config.title] - Panel title
     */
    open(config = {}) {
      if (config.title) {
        this.title = config.title;
      }
      this.isOpen = true;
      options.onOpen?.();
    },
    
    /**
     * Close the panel
     */
    close() {
      this.isOpen = false;
      options.onClose?.();
    },
    
    /**
     * Toggle the panel
     */
    toggle() {
      if (this.isOpen) {
        this.close();
      } else {
        this.open();
      }
    },
    
    /**
     * Set panel title
     * @param {string} newTitle - New title
     */
    setTitle(newTitle) {
      this.title = newTitle;
    },
    
    /**
     * Set panel width
     * @param {number} newWidth - New width
     */
    setWidth(newWidth) {
      this.width = Math.max(240, Math.min(600, newWidth));
    },
  };
}
