/**
 * Card Component
 * 
 * Collapsible card with header, body, and footer slots.
 * 
 * Usage:
 * <div x-data="card({ collapsible: true })" class="card">
 *   <div x-bind="header" class="card-header">
 *     <span>Title</span>
 *     <button x-show="collapsible" @click="toggle()">▼</button>
 *   </div>
 *   <div x-bind="body" class="card-body">Content</div>
 * </div>
 * 
 * @module components/base/card
 */

/**
 * Card component factory
 * @param {Object} options - Card options
 * @param {boolean} [options.collapsible=false] - Enable collapse
 * @param {boolean} [options.expanded=true] - Initial expanded state
 * @param {boolean} [options.interactive=false] - Enable hover effects
 * @param {Function} [options.onToggle] - Toggle callback
 * @returns {Object} Alpine component data
 */
export default function Card(options = {}) {
  return {
    collapsible: options.collapsible ?? false,
    expanded: options.expanded ?? true,
    interactive: options.interactive ?? false,
    
    /**
     * Bind object for header element
     */
    get header() {
      return {
        '@click': () => {
          if (this.collapsible) this.toggle();
        },
        ':class': () => ({
          'cursor-pointer': this.collapsible,
        }),
        ':aria-expanded': () => this.expanded,
      };
    },
    
    /**
     * Bind object for body element
     */
    get body() {
      return {
        'x-show': () => !this.collapsible || this.expanded,
        'x-collapse': this.collapsible ? '' : undefined,
      };
    },
    
    /**
     * Toggle expanded state
     */
    toggle() {
      if (!this.collapsible) return;
      this.expanded = !this.expanded;
      options.onToggle?.(this.expanded);
    },
    
    /**
     * Expand the card
     */
    expand() {
      this.expanded = true;
      options.onToggle?.(true);
    },
    
    /**
     * Collapse the card
     */
    collapse() {
      this.expanded = false;
      options.onToggle?.(false);
    },
  };
}
