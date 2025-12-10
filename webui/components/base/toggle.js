/**
 * Toggle/Switch Component
 * 
 * Accessible toggle switch with keyboard support.
 * 
 * Usage:
 * <button x-data="toggle({ checked: false })" x-bind="trigger" class="toggle">
 *   <span class="sr-only">Enable feature</span>
 * </button>
 * 
 * @module components/base/toggle
 */

/**
 * Toggle component factory
 * @param {Object} options - Toggle options
 * @param {boolean} [options.checked=false] - Initial checked state
 * @param {boolean} [options.disabled=false] - Disabled state
 * @param {Function} [options.onChange] - Change handler
 * @returns {Object} Alpine component data
 */
export default function Toggle(options = {}) {
  return {
    checked: options.checked ?? false,
    disabled: options.disabled ?? false,
    
    /**
     * Bind object for toggle button
     */
    get trigger() {
      return {
        'role': 'switch',
        ':aria-checked': () => this.checked,
        ':aria-disabled': () => this.disabled,
        ':data-checked': () => this.checked,
        ':disabled': () => this.disabled,
        '@click': () => this.toggle(),
        '@keydown.enter.prevent': () => this.toggle(),
        '@keydown.space.prevent': () => this.toggle(),
      };
    },
    
    /**
     * Toggle the checked state
     */
    toggle() {
      if (this.disabled) return;
      this.checked = !this.checked;
      options.onChange?.(this.checked);
    },
    
    /**
     * Set checked state
     * @param {boolean} state - New state
     */
    setChecked(state) {
      if (this.disabled) return;
      this.checked = state;
      options.onChange?.(this.checked);
    },
  };
}
