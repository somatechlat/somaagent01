/**
 * Settings Card Component
 * 
 * Collapsible card for settings sections with icon and description.
 * Includes full ARIA accessibility support.
 * 
 * @module components/settings/settings-card
 */

import { ARIA_LABELS } from '../../core/accessibility/index.js';

/**
 * Settings Card component factory
 * @param {Object} options - Card options
 * @param {string} options.id - Card ID
 * @param {string} options.title - Card title
 * @param {string} [options.description] - Card description
 * @param {string} [options.icon] - Card icon (emoji or SVG)
 * @param {boolean} [options.expanded=false] - Initial expanded state
 * @param {Function} [options.onToggle] - Toggle callback
 * @returns {Object} Alpine component data
 */
export default function SettingsCard(options = {}) {
  return {
    id: options.id ?? '',
    title: options.title ?? '',
    description: options.description ?? '',
    icon: options.icon ?? '⚙️',
    expanded: options.expanded ?? false,
    
    /**
     * Bind for card container
     */
    get container() {
      return {
        'role': 'region',
        ':aria-labelledby': () => `${this.id}-header`,
      };
    },
    
    /**
     * Bind for card header (acts as button)
     */
    get header() {
      return {
        'id': `${this.id}-header`,
        'role': 'button',
        'tabindex': '0',
        '@click': () => this.toggle(),
        '@keydown.enter.prevent': () => this.toggle(),
        '@keydown.space.prevent': () => this.toggle(),
        ':aria-expanded': () => this.expanded,
        ':aria-controls': () => `${this.id}-content`,
        ':aria-label': () => this.expanded 
          ? ARIA_LABELS.collapseCard(this.title)
          : ARIA_LABELS.expandCard(this.title),
        'class': 'card-header cursor-pointer',
      };
    },
    
    /**
     * Bind for card body
     */
    get body() {
      return {
        'x-show': () => this.expanded,
        'x-collapse': '',
        'id': `${this.id}-content`,
        'role': 'region',
        ':aria-labelledby': () => `${this.id}-header`,
        ':aria-hidden': () => !this.expanded,
        'class': 'card-body',
      };
    },
    
    /**
     * Bind for chevron icon
     */
    get chevron() {
      return {
        ':class': () => ({
          'rotate-180': this.expanded,
        }),
        'class': 'transition-transform duration-200',
      };
    },
    
    /**
     * Toggle expanded state
     */
    toggle() {
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
