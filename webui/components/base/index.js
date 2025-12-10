/**
 * Base Components Library
 * 
 * Alpine.js component definitions for the design system.
 * Each component is a factory function that returns Alpine data.
 * 
 * Pattern: Headless components with CSS classes from design-system
 * 
 * @module components/base
 */

// Re-export all base components
export { default as Button } from './button.js';
export { default as Input } from './input.js';
export { default as Select } from './select.js';
export { default as Toggle } from './toggle.js';
export { default as Slider } from './slider.js';
export { default as Modal } from './modal.js';
export { default as Card } from './card.js';
export { default as Avatar } from './avatar.js';
export { default as Badge } from './badge.js';
export { default as Tooltip } from './tooltip.js';
export { default as Dropdown } from './dropdown.js';
export { default as Toast, toastManager } from './toast.js';

/**
 * Register all base components with Alpine
 * @param {Object} Alpine - Alpine.js instance
 */
export function registerBaseComponents(Alpine) {
  // Import components dynamically to avoid circular deps
  const components = {
    button: () => import('./button.js').then(m => m.default),
    input: () => import('./input.js').then(m => m.default),
    select: () => import('./select.js').then(m => m.default),
    toggle: () => import('./toggle.js').then(m => m.default),
    slider: () => import('./slider.js').then(m => m.default),
    modal: () => import('./modal.js').then(m => m.default),
    card: () => import('./card.js').then(m => m.default),
    dropdown: () => import('./dropdown.js').then(m => m.default),
  };

  // Register each as Alpine.data
  Object.entries(components).forEach(([name, loader]) => {
    Alpine.data(name, (...args) => {
      // Lazy load component definition
      return loader().then(factory => factory(...args));
    });
  });
}
