/**
 * Select Component
 * 
 * Custom select with search, multi-select, and keyboard navigation.
 * 
 * Usage:
 * <div x-data="select({ options: [...], value: '' })" class="dropdown">
 *   <button x-bind="trigger" class="btn">Select...</button>
 *   <div x-bind="menu" class="dropdown-menu">
 *     <template x-for="opt in filteredOptions">
 *       <div x-bind="option(opt)" class="dropdown-item" x-text="opt.label"></div>
 *     </template>
 *   </div>
 * </div>
 * 
 * @module components/base/select
 */

/**
 * Select component factory
 * @param {Object} options - Select options
 * @param {Array} options.options - Array of { value, label, icon?, disabled? }
 * @param {*} [options.value] - Selected value (or array for multi)
 * @param {boolean} [options.multiple=false] - Allow multiple selection
 * @param {boolean} [options.searchable=false] - Enable search
 * @param {string} [options.placeholder='Select...'] - Placeholder text
 * @param {Function} [options.onChange] - Change handler
 * @returns {Object} Alpine component data
 */
export default function Select(options = {}) {
  return {
    isOpen: false,
    search: '',
    value: options.multiple ? (options.value ?? []) : (options.value ?? null),
    options: options.options ?? [],
    highlightedIndex: -1,
    
    init() {
      // Close on outside click
      this.$watch('isOpen', (open) => {
        if (open) {
          this.highlightedIndex = this.selectedIndex;
          this.$nextTick(() => this.$refs.search?.focus());
        } else {
          this.search = '';
        }
      });
    },
    
    /**
     * Filtered options based on search
     */
    get filteredOptions() {
      if (!this.search) return this.options;
      const q = this.search.toLowerCase();
      return this.options.filter(opt => 
        opt.label.toLowerCase().includes(q) ||
        opt.value?.toString().toLowerCase().includes(q)
      );
    },
    
    /**
     * Currently selected option(s)
     */
    get selected() {
      if (options.multiple) {
        return this.options.filter(opt => this.value.includes(opt.value));
      }
      return this.options.find(opt => opt.value === this.value);
    },
    
    /**
     * Display text for trigger
     */
    get displayText() {
      if (options.multiple) {
        if (this.value.length === 0) return options.placeholder ?? 'Select...';
        if (this.value.length === 1) return this.selected[0]?.label;
        return `${this.value.length} selected`;
      }
      return this.selected?.label ?? options.placeholder ?? 'Select...';
    },
    
    /**
     * Index of first selected option
     */
    get selectedIndex() {
      if (options.multiple) {
        return this.options.findIndex(opt => this.value.includes(opt.value));
      }
      return this.options.findIndex(opt => opt.value === this.value);
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
        ':aria-haspopup': () => 'listbox',
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
        '@click.outside': () => this.close(),
        'role': 'listbox',
        ':aria-multiselectable': () => options.multiple,
      };
    },
    
    /**
     * Bind object for search input
     */
    get searchInput() {
      return {
        'x-ref': 'search',
        'x-model': 'search',
        '@keydown.escape': () => this.close(),
        '@keydown.enter.prevent': () => this.selectHighlighted(),
        '@keydown.arrow-down.prevent': () => this.highlightNext(),
        '@keydown.arrow-up.prevent': () => this.highlightPrev(),
        'placeholder': 'Search...',
        'class': 'input',
      };
    },
    
    /**
     * Bind factory for option elements
     * @param {Object} opt - Option object
     * @param {number} index - Option index
     */
    option(opt, index) {
      return {
        '@click': () => this.select(opt),
        '@mouseenter': () => { this.highlightedIndex = index; },
        ':class': () => ({
          'bg-accent-subtle': this.isSelected(opt),
          'bg-bg-2': this.highlightedIndex === index && !this.isSelected(opt),
        }),
        ':aria-selected': () => this.isSelected(opt),
        'role': 'option',
      };
    },
    
    /**
     * Check if option is selected
     * @param {Object} opt - Option object
     * @returns {boolean}
     */
    isSelected(opt) {
      if (options.multiple) {
        return this.value.includes(opt.value);
      }
      return this.value === opt.value;
    },
    
    /**
     * Select an option
     * @param {Object} opt - Option to select
     */
    select(opt) {
      if (opt.disabled) return;
      
      if (options.multiple) {
        const idx = this.value.indexOf(opt.value);
        if (idx === -1) {
          this.value = [...this.value, opt.value];
        } else {
          this.value = this.value.filter(v => v !== opt.value);
        }
      } else {
        this.value = opt.value;
        this.close();
      }
      
      options.onChange?.(this.value);
    },
    
    /**
     * Select highlighted option
     */
    selectHighlighted() {
      const opt = this.filteredOptions[this.highlightedIndex];
      if (opt) this.select(opt);
    },
    
    /**
     * Highlight next option
     */
    highlightNext() {
      const max = this.filteredOptions.length - 1;
      this.highlightedIndex = Math.min(this.highlightedIndex + 1, max);
    },
    
    /**
     * Highlight previous option
     */
    highlightPrev() {
      this.highlightedIndex = Math.max(this.highlightedIndex - 1, 0);
    },
    
    /**
     * Open dropdown
     */
    open() {
      this.isOpen = true;
    },
    
    /**
     * Close dropdown
     */
    close() {
      this.isOpen = false;
    },
    
    /**
     * Toggle dropdown
     */
    toggle() {
      this.isOpen = !this.isOpen;
    },
    
    /**
     * Clear selection
     */
    clear() {
      this.value = options.multiple ? [] : null;
      options.onChange?.(this.value);
    },
  };
}
