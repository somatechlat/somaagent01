/**
 * Sidebar Component
 * 
 * Navigation sidebar with sections, items, and session list.
 * 
 * Usage:
 * <aside x-data="sidebar({ items: [...] })" class="app-sidebar">
 *   <div class="sidebar-content">
 *     <nav class="sidebar-nav">
 *       <template x-for="section in sections">
 *         <div class="nav-section">
 *           <div class="nav-section-title" x-text="section.title"></div>
 *           <template x-for="item in section.items">
 *             <a x-bind="navItem(item)" class="nav-item">
 *               <span class="nav-item-icon" x-html="item.icon"></span>
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
    
    /**
     * Bind factory for navigation items
     * @param {Object} item - Navigation item
     */
    navItem(item) {
      return {
        ':href': () => item.href ?? '#',
        ':data-active': () => this.activeItem === item.id,
        ':aria-current': () => this.activeItem === item.id ? 'page' : null,
        '@click': (e) => {
          if (!item.href || item.href === '#') {
            e.preventDefault();
          }
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
  };
}
