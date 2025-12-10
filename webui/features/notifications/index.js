/**
 * Notifications Feature Module
 * 
 * Public API for the Notifications feature.
 * Provides toast notifications, system alerts, and notification history.
 * 
 * @module features/notifications
 */

import * as store from './notifications.store.js';

// Re-export everything from store
export * from './notifications.store.js';

// Default export
export default store.default;
