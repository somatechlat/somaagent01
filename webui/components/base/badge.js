/**
 * Badge Component
 * 
 * Status badge with variants and dot indicator.
 * 
 * Usage:
 * <span x-data="badge({ variant: 'success', dot: true })" x-bind="attrs" class="badge">
 *   Active
 * </span>
 * 
 * @module components/base/badge
 */

/**
 * Badge variants
 */
const VARIANTS = ['default', 'accent', 'success', 'warning', 'error', 'info'];

/**
 * Badge component factory
 * @param {Object} options - Badge options
 * @param {string} [options.variant='default'] - Badge variant
 * @param {boolean} [options.dot=false] - Show dot indicator
 * @param {string} [options.label=''] - Badge text
 * @returns {Object} Alpine component data
 */
export default function Badge(options = {}) {
  return {
    variant: options.variant ?? 'default',
    dot: options.dot ?? false,
    label: options.label ?? '',
    
    /**
     * Bind object for badge element
     */
    get attrs() {
      return {
        ':class': () => this.classes,
      };
    },
    
    /**
     * Computed CSS classes
     */
    get classes() {
      const classes = ['badge'];
      
      if (this.variant !== 'default') {
        classes.push(`badge-${this.variant}`);
      }
      
      if (this.dot) {
        classes.push('badge-dot');
      }
      
      return classes.join(' ');
    },
    
    /**
     * Set variant
     * @param {string} newVariant - New variant
     */
    setVariant(newVariant) {
      if (VARIANTS.includes(newVariant)) {
        this.variant = newVariant;
      }
    },
    
    /**
     * Set label
     * @param {string} newLabel - New label
     */
    setLabel(newLabel) {
      this.label = newLabel;
    },
  };
}

export { VARIANTS };
