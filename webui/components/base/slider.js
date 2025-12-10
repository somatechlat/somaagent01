/**
 * Slider Component
 * 
 * Range slider with value display and step support.
 * 
 * Usage:
 * <div x-data="slider({ value: 50, min: 0, max: 100 })">
 *   <input x-bind="input" type="range" />
 *   <span x-text="displayValue"></span>
 * </div>
 * 
 * @module components/base/slider
 */

/**
 * Slider component factory
 * @param {Object} options - Slider options
 * @param {number} [options.value=0] - Initial value
 * @param {number} [options.min=0] - Minimum value
 * @param {number} [options.max=100] - Maximum value
 * @param {number} [options.step=1] - Step increment
 * @param {boolean} [options.disabled=false] - Disabled state
 * @param {Function} [options.format] - Value formatter
 * @param {Function} [options.onChange] - Change handler
 * @returns {Object} Alpine component data
 */
export default function Slider(options = {}) {
  return {
    value: options.value ?? 0,
    min: options.min ?? 0,
    max: options.max ?? 100,
    step: options.step ?? 1,
    disabled: options.disabled ?? false,
    
    /**
     * Formatted display value
     */
    get displayValue() {
      if (options.format) {
        return options.format(this.value);
      }
      return this.value;
    },
    
    /**
     * Progress percentage (0-100)
     */
    get progress() {
      return ((this.value - this.min) / (this.max - this.min)) * 100;
    },
    
    /**
     * Bind object for range input
     */
    get input() {
      return {
        'type': 'range',
        ':value': () => this.value,
        ':min': () => this.min,
        ':max': () => this.max,
        ':step': () => this.step,
        ':disabled': () => this.disabled,
        ':style': () => `--progress: ${this.progress}%`,
        '@input': (e) => {
          this.value = Number(e.target.value);
          options.onChange?.(this.value);
        },
      };
    },
    
    /**
     * Set value programmatically
     * @param {number} val - New value
     */
    setValue(val) {
      this.value = Math.min(Math.max(val, this.min), this.max);
      options.onChange?.(this.value);
    },
    
    /**
     * Increment value by step
     */
    increment() {
      this.setValue(this.value + this.step);
    },
    
    /**
     * Decrement value by step
     */
    decrement() {
      this.setValue(this.value - this.step);
    },
  };
}
