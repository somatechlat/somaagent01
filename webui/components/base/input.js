/**
 * Input Component
 * 
 * Enhanced input with validation, error states, and accessibility.
 * 
 * Usage:
 * <div x-data="input({ value: '', rules: ['required'] })">
 *   <input x-bind="field" class="input" />
 *   <span x-show="error" x-text="error" class="text-error"></span>
 * </div>
 * 
 * @module components/base/input
 */

/**
 * Validation rules
 */
const validators = {
  required: (v) => (v && v.toString().trim() !== '') || 'This field is required',
  email: (v) => !v || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) || 'Invalid email address',
  minLength: (min) => (v) => !v || v.length >= min || `Minimum ${min} characters`,
  maxLength: (max) => (v) => !v || v.length <= max || `Maximum ${max} characters`,
  pattern: (regex, msg) => (v) => !v || regex.test(v) || msg || 'Invalid format',
  number: (v) => !v || !isNaN(Number(v)) || 'Must be a number',
  integer: (v) => !v || Number.isInteger(Number(v)) || 'Must be an integer',
  min: (min) => (v) => !v || Number(v) >= min || `Minimum value is ${min}`,
  max: (max) => (v) => !v || Number(v) <= max || `Maximum value is ${max}`,
  url: (v) => {
    if (!v) return true;
    try { new URL(v); return true; } catch { return 'Invalid URL'; }
  },
};

/**
 * Input component factory
 * @param {Object} options - Input options
 * @param {string} [options.value=''] - Initial value
 * @param {Array} [options.rules=[]] - Validation rules
 * @param {boolean} [options.validateOnBlur=true] - Validate on blur
 * @param {boolean} [options.validateOnInput=false] - Validate on input
 * @param {Function} [options.onChange] - Change handler
 * @returns {Object} Alpine component data
 */
export default function Input(options = {}) {
  return {
    value: options.value ?? '',
    error: null,
    touched: false,
    dirty: false,
    rules: options.rules ?? [],
    
    init() {
      // Watch for external value changes
      if (options.model) {
        this.$watch(options.model, (newVal) => {
          this.value = newVal;
        });
      }
    },
    
    /**
     * Bind object for input element
     */
    get field() {
      return {
        ':value': () => this.value,
        ':class': () => ({
          'input-error': this.error && this.touched,
        }),
        ':aria-invalid': () => !!(this.error && this.touched),
        ':aria-describedby': () => this.error ? `${this.$id('input')}-error` : null,
        '@input': (e) => {
          this.value = e.target.value;
          this.dirty = true;
          if (options.validateOnInput) {
            this.validate();
          }
          options.onChange?.(this.value);
        },
        '@blur': () => {
          this.touched = true;
          if (options.validateOnBlur !== false) {
            this.validate();
          }
        },
        '@focus': () => {
          // Clear error on focus if desired
        },
      };
    },
    
    /**
     * Validate the input value
     * @returns {boolean} Is valid
     */
    validate() {
      this.error = null;
      
      for (const rule of this.rules) {
        let validator;
        
        if (typeof rule === 'string') {
          validator = validators[rule];
        } else if (typeof rule === 'function') {
          validator = rule;
        } else if (Array.isArray(rule)) {
          const [name, ...args] = rule;
          validator = validators[name]?.(...args);
        }
        
        if (validator) {
          const result = validator(this.value);
          if (result !== true) {
            this.error = result;
            return false;
          }
        }
      }
      
      return true;
    },
    
    /**
     * Reset the input state
     * @param {string} [value=''] - New value
     */
    reset(value = '') {
      this.value = value;
      this.error = null;
      this.touched = false;
      this.dirty = false;
    },
    
    /**
     * Check if input is valid
     * @returns {boolean}
     */
    get isValid() {
      return !this.error;
    },
  };
}

// Export validators for custom rules
export { validators };
