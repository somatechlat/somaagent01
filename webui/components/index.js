/**
 * Components Library Index
 * 
 * Central export for all UI components.
 * 
 * @module components
 */

// Base Components
export * from './base/index.js';

// Layout Components
export * from './layout/index.js';

// Chat Components
export * from './chat/index.js';

// Settings Components
export * from './settings/index.js';

// Session Components
export * from './sessions/index.js';

// Memory Components
export * from './memory/index.js';

// Health Components
export * from './health/index.js';

// Upload Components
export * from './upload/index.js';

/**
 * Register all components with Alpine.js
 * @param {Object} Alpine - Alpine.js instance
 */
export function registerComponents(Alpine) {
  // Import and register base components
  import('./base/button.js').then(m => Alpine.data('button', m.default));
  import('./base/input.js').then(m => Alpine.data('input', m.default));
  import('./base/select.js').then(m => Alpine.data('select', m.default));
  import('./base/toggle.js').then(m => Alpine.data('toggle', m.default));
  import('./base/slider.js').then(m => Alpine.data('slider', m.default));
  import('./base/modal.js').then(m => Alpine.data('modal', m.default));
  import('./base/card.js').then(m => Alpine.data('card', m.default));
  import('./base/dropdown.js').then(m => Alpine.data('dropdown', m.default));
  import('./base/badge.js').then(m => Alpine.data('badge', m.default));
  import('./base/avatar.js').then(m => Alpine.data('avatar', m.default));
  import('./base/tooltip.js').then(m => Alpine.data('tooltip', m.default));
  import('./base/toast.js').then(m => Alpine.data('toastContainer', m.default));
  
  // Import and register layout components
  import('./layout/app-shell.js').then(m => Alpine.data('appShell', m.default));
  import('./layout/sidebar.js').then(m => Alpine.data('sidebar', m.default));
  import('./layout/header.js').then(m => Alpine.data('header', m.default));
  import('./layout/panel.js').then(m => Alpine.data('panel', m.default));
}

/**
 * Initialize the component library
 * Call this before Alpine.start()
 * @param {Object} Alpine - Alpine.js instance
 */
export function initComponentLibrary(Alpine) {
  registerComponents(Alpine);
  
  // Add global utilities
  Alpine.magic('toast', () => {
    return import('./base/toast.js').then(m => m.toastManager);
  });
}
