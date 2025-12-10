/**
 * Settings Card Component
 * 
 * Collapsible card for settings sections with icon and description.
 * 
 * @module components/settings/settings-card
 */

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
     * Bind for card header
     */
    get header() {
      return {
        '@click': () => this.toggle(),
        ':aria-expanded': () => this.expanded,
        ':aria-controls': () => `${this.id}-content`,
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
        ':id': () => `${this.id}-content`,
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
