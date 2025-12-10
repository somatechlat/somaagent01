/**
 * Button Component
 * 
 * Headless button with loading state, variants, and accessibility.
 * 
 * Usage:
 * <button x-data="button({ loading: false })" x-bind="trigger" class="btn btn-primary">
 *   <span x-show="!loading">Click me</span>
 *   <span x-show="loading">Loading...</span>
 * </button>
 * 
 * @module components/base/button
 */

/**
 * Button component factory
 * @param {Object} options - Button options
 * @param {boolean} [options.loading=false] - Loading state
 * @param {boolean} [options.disabled=false] - Disabled state
 * @param {Function} [options.onClick] - Click handler
 * @returns {Object} Alpine component data
 */
export default function Button(options = {}) {
  return {
    loading: options.loading ?? false,
    disabled: options.disabled ?? false,
    
    /**
     * Bind object for button element
     */
    get trigger() {
      return {
        ':disabled': () => this.disabled || this.loading,
        ':class': () => ({
          'btn-loading': this.loading,
        }),
        ':aria-busy': () => this.loading,
        ':aria-disabled': () => this.disabled,
        '@click': (e) => {
          if (this.loading || this.disabled) {
            e.preventDefault();
            return;
          }
          options.onClick?.(e);
        },
      };
    },
    
    /**
     * Set loading state
     * @param {boolean} state - Loading state
     */
    setLoading(state) {
      this.loading = state;
    },
    
    /**
     * Set disabled state
     * @param {boolean} state - Disabled state
     */
    setDisabled(state) {
      this.disabled = state;
    },
    
    /**
     * Execute async action with loading state
     * @param {Function} action - Async action to execute
     */
    async execute(action) {
      if (this.loading || this.disabled) return;
      
      this.loading = true;
      try {
        await action();
      } finally {
        this.loading = false;
      }
    },
  };
}
