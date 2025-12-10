/**
 * Dropdown Component
 * 
 * Accessible dropdown menu with keyboard navigation.
 * 
 * Usage:
 * <div x-data="dropdown()" class="dropdown">
 *   <button x-bind="trigger" class="btn">Menu</button>
 *   <div x-bind="menu" class="dropdown-menu">
 *     <button x-bind="item" class="dropdown-item">Item 1</button>
 *     <button x-bind="item" class="dropdown-item">Item 2</button>
 *   </div>
 * </div>
 * 
 * @module components/base/dropdown
 */

/**
 * Dropdown component factory
 * @param {Object} options - Dropdown options
 * @param {string} [options.placement='bottom-start'] - Menu placement
 * @param {boolean} [options.closeOnSelect=true] - Close on item select
 * @param {Function} [options.onOpen] - Open callback
 * @param {Function} [options.onClose] - Close callback
 * @returns {Object} Alpine component data
 */
export default function Dropdown(options = {}) {
  return {
    isOpen: false,
    highlightedIndex: -1,
    items: [],
    
    init() {
      // Close on outside click
      document.addEventListener('click', (e) => {
        if (this.isOpen && !this.$el.contains(e.target)) {
          this.close();
        }
      });
    },
    
    /**
     * Bind object for trigger button
     */
    get trigger() {
      return {
        '@click': () => this.toggle(),
        '@keydown.enter.prevent': () => this.toggle(),
        '@keydown.space.prevent': () => this.toggle(),
        '@keydown.escape': () => this.close(),
        '@keydown.arrow-down.prevent': () => {
          if (!this.isOpen) this.open();
          else this.highlightNext();
        },
        '@keydown.arrow-up.prevent': () => {
          if (!this.isOpen) this.open();
          else this.highlightPrev();
        },
        ':aria-expanded': () => this.isOpen,
        ':aria-haspopup': () => 'menu',
      };
    },
    
    /**
     * Bind object for menu container
     */
    get menu() {
      return {
        'x-show': () => this.isOpen,
        'x-transition:enter': 'transition ease-out duration-100',
        'x-transition:enter-start': 'opacity-0 scale-95',
        'x-transition:enter-end': 'opacity-100 scale-100',
        'x-transition:leave': 'transition ease-in duration-75',
        'x-transition:leave-start': 'opacity-100 scale-100',
        'x-transition:leave-end': 'opacity-0 scale-95',
        ':data-open': () => this.isOpen,
        'role': 'menu',
        '@keydown.escape': () => this.close(),
        '@keydown.arrow-down.prevent': () => this.highlightNext(),
        '@keydown.arrow-up.prevent': () => this.highlightPrev(),
        '@keydown.enter.prevent': () => this.selectHighlighted(),
        '@keydown.tab': () => this.close(),
      };
    },
    
    /**
     * Bind factory for menu items
     * @param {number} index - Item index
     */
    item(index) {
      return {
        '@click': () => this.selectItem(index),
        '@mouseenter': () => { this.highlightedIndex = index; },
        ':class': () => ({
          'bg-bg-2': this.highlightedIndex === index,
        }),
        ':tabindex': () => this.highlightedIndex === index ? 0 : -1,
        'role': 'menuitem',
      };
    },
    
    /**
     * Open dropdown
     */
    open() {
      this.isOpen = true;
      this.highlightedIndex = 0;
      
      // Focus first item
      this.$nextTick(() => {
        const firstItem = this.$el.querySelector('[role="menuitem"]');
        firstItem?.focus();
      });
      
      options.onOpen?.();
    },
    
    /**
     * Close dropdown
     */
    close() {
      this.isOpen = false;
      this.highlightedIndex = -1;
      options.onClose?.();
    },
    
    /**
     * Toggle dropdown
     */
    toggle() {
      if (this.isOpen) {
        this.close();
      } else {
        this.open();
      }
    },
    
    /**
     * Highlight next item
     */
    highlightNext() {
      const items = this.$el.querySelectorAll('[role="menuitem"]');
      this.highlightedIndex = Math.min(this.highlightedIndex + 1, items.length - 1);
      items[this.highlightedIndex]?.focus();
    },
    
    /**
     * Highlight previous item
     */
    highlightPrev() {
      this.highlightedIndex = Math.max(this.highlightedIndex - 1, 0);
      const items = this.$el.querySelectorAll('[role="menuitem"]');
      items[this.highlightedIndex]?.focus();
    },
    
    /**
     * Select highlighted item
     */
    selectHighlighted() {
      const items = this.$el.querySelectorAll('[role="menuitem"]');
      items[this.highlightedIndex]?.click();
    },
    
    /**
     * Select item by index
     * @param {number} index - Item index
     */
    selectItem(index) {
      if (options.closeOnSelect !== false) {
        this.close();
      }
    },
  };
}
