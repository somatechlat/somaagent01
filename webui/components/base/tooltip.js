/**
 * Tooltip Component
 * 
 * Accessible tooltip with positioning and delay.
 * 
 * Usage:
 * <div x-data="tooltip({ content: 'Help text', position: 'top' })">
 *   <button x-bind="trigger">Hover me</button>
 *   <div x-bind="tip" class="tooltip-content" x-text="content"></div>
 * </div>
 * 
 * @module components/base/tooltip
 */

/**
 * Tooltip positions
 */
const POSITIONS = ['top', 'right', 'bottom', 'left'];

/**
 * Tooltip component factory
 * @param {Object} options - Tooltip options
 * @param {string} options.content - Tooltip content
 * @param {string} [options.position='top'] - Tooltip position
 * @param {number} [options.delay=200] - Show delay in ms
 * @param {boolean} [options.disabled=false] - Disable tooltip
 * @returns {Object} Alpine component data
 */
export default function Tooltip(options = {}) {
  return {
    content: options.content ?? '',
    position: options.position ?? 'top',
    isVisible: false,
    disabled: options.disabled ?? false,
    showTimeout: null,
    
    /**
     * Bind object for trigger element
     */
    get trigger() {
      return {
        '@mouseenter': () => this.scheduleShow(),
        '@mouseleave': () => this.hide(),
        '@focus': () => this.scheduleShow(),
        '@blur': () => this.hide(),
        ':aria-describedby': () => this.isVisible ? this.tooltipId : null,
      };
    },
    
    /**
     * Bind object for tooltip element
     */
    get tip() {
      return {
        'x-show': () => this.isVisible && !this.disabled,
        'x-transition:enter': 'transition ease-out duration-100',
        'x-transition:enter-start': 'opacity-0 scale-95',
        'x-transition:enter-end': 'opacity-100 scale-100',
        'x-transition:leave': 'transition ease-in duration-75',
        'x-transition:leave-start': 'opacity-100 scale-100',
        'x-transition:leave-end': 'opacity-0 scale-95',
        ':id': () => this.tooltipId,
        ':class': () => `tooltip-${this.position}`,
        'role': 'tooltip',
      };
    },
    
    /**
     * Unique tooltip ID
     */
    get tooltipId() {
      return `tooltip-${this.$id('tooltip')}`;
    },
    
    /**
     * Schedule tooltip show with delay
     */
    scheduleShow() {
      if (this.disabled) return;
      
      this.showTimeout = setTimeout(() => {
        this.isVisible = true;
      }, options.delay ?? 200);
    },
    
    /**
     * Hide tooltip immediately
     */
    hide() {
      clearTimeout(this.showTimeout);
      this.isVisible = false;
    },
    
    /**
     * Show tooltip immediately
     */
    show() {
      if (this.disabled) return;
      clearTimeout(this.showTimeout);
      this.isVisible = true;
    },
    
    /**
     * Update content
     * @param {string} newContent - New content
     */
    setContent(newContent) {
      this.content = newContent;
    },
    
    /**
     * Set position
     * @param {string} newPosition - New position
     */
    setPosition(newPosition) {
      if (POSITIONS.includes(newPosition)) {
        this.position = newPosition;
      }
    },
  };
}

export { POSITIONS };
