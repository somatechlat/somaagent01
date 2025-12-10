/**
 * Sidebar Component
 * 
 * Navigation sidebar with sections, items, and session list.
 * Includes full ARIA accessibility support for keyboard navigation.
 * 
 * Usage:
 * <aside x-data="sidebar({ items: [...] })" x-bind="container" class="app-sidebar">
 *   <div class="sidebar-content">
 *     <nav x-bind="nav" class="sidebar-nav">
 *       <template x-for="section in sections">
 *         <div class="nav-section" role="group" :aria-labelledby="'section-' + section.id">
 *           <div :id="'section-' + section.id" class="nav-section-title" x-text="section.title"></div>
 *           <template x-for="item in section.items">
 *             <a x-bind="navItem(item)" class="nav-item">
 *               <span class="nav-item-icon" x-html="item.icon" aria-hidden="true"></span>
 *               <span class="nav-item-label" x-text="item.label"></span>
 *             </a>
 *           </template>
 *         </div>
 *       </template>
 *     </nav>
 *   </div>
 * </aside>
 * 
 * @module components/layout/sidebar
 */

import { emit } from '../../js/event-bus.js';
import { ARIA_LABELS } from '../../core/accessibility/index.js';

/**
 * Sidebar component factory
 * @param {Object} options - Sidebar options
 * @param {Array} [options.sections=[]] - Navigation sections
 * @param {string} [options.activeItem=''] - Currently active item ID
 * @param {Function} [options.onNavigate] - Navigation callback
 * @returns {Object} Alpine component data
 */
export default function Sidebar(options = {}) {
  return {
    sections: options.sections ?? [],
    activeItem: options.activeItem ?? '',
    isCollapsed: false,
    
    /**
     * Bind for sidebar container
     */
    get container() {
      return {
        'role': 'complementary',
        'aria-label': ARIA_LABELS.sidebar,
        ':aria-expanded': () => !this.isCollapsed,
      };
    },
    
    /**
     * Bind for navigation element
     */
    get nav() {
      return {
        'role': 'navigation',
        'aria-label': ARIA_LABELS.sidebar,
      };
    },
    
    /**
     * Bind factory for navigation items
     * @param {Object} item - Navigation item
     */
    navItem(item) {
      return {
        ':href': () => item.href ?? '#',
        ':data-active': () => this.activeItem === item.id,
        ':aria-current': () => this.activeItem === item.id ? 'page' : null,
        'aria-label': item.label,
        ':tabindex': () => 0,
        '@click': (e) => {
          if (!item.href || item.href === '#') {
            e.preventDefault();
          }
          this.navigate(item);
        },
        '@keydown.enter': (e) => {
          e.preventDefault();
          this.navigate(item);
        },
        '@keydown.space': (e) => {
          e.preventDefault();
          this.navigate(item);
        },
      };
    },
    
    /**
     * Navigate to an item
     * @param {Object} item - Navigation item
     */
    navigate(item) {
      this.activeItem = item.id;
      emit('nav:change', { item });
      options.onNavigate?.(item);
    },
    
    /**
     * Set active item
     * @param {string} itemId - Item ID
     */
    setActive(itemId) {
      this.activeItem = itemId;
    },
    
    /**
     * Add a section
     * @param {Object} section - Section to add
     */
    addSection(section) {
      this.sections.push(section);
    },
    
    /**
     * Update sections
     * @param {Array} sections - New sections
     */
    setSections(sections) {
      this.sections = sections;
    },
    
    /**
     * Toggle sidebar collapsed state
     */
    toggleCollapsed() {
      this.isCollapsed = !this.isCollapsed;
    },
    
    /**
     * Bind for collapse toggle button
     */
    get toggleButton() {
      return {
        '@click': () => this.toggleCollapsed(),
        'aria-label': ARIA_LABELS.sidebarToggle,
        ':aria-expanded': () => !this.isCollapsed,
        'aria-controls': 'sidebar-content',
      };
    },
  };
}
