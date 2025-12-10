/**
 * Notifications Store
 * 
 * Centralized state management for the Notifications feature.
 * Handles toast notifications, system alerts, and notification history.
 * 
 * @module features/notifications/notifications.store
 */

import { createStore, subscribe } from '../../core/state/store.js';

/**
 * Notification severity levels
 */
export const SEVERITY = Object.freeze({
  INFO: 'info',
  SUCCESS: 'success',
  WARNING: 'warning',
  ERROR: 'error',
  CRITICAL: 'critical',
});

/**
 * Notification types
 */
export const NOTIFICATION_TYPE = Object.freeze({
  TOAST: 'toast',
  SYSTEM: 'system',
  ALERT: 'alert',
});

/**
 * Initial notifications state
 */
const initialState = {
  // Active notifications (visible toasts)
  active: [],
  
  // Notification history
  history: [],
  
  // Maximum history size
  maxHistory: 100,
  
  // Default TTL in seconds
  defaultTtl: 5,
  
  // Counter for unique IDs
  idCounter: 0,
};

/**
 * Notifications store instance
 */
export const notificationsStore = createStore('notifications', initialState);

/**
 * Generate a unique notification ID
 * @returns {string} Unique ID
 */
function generateId() {
  notificationsStore.idCounter++;
  return `notif-${Date.now()}-${notificationsStore.idCounter}`;
}

/**
 * Create a new notification
 * @param {Object} options - Notification options
 * @param {string} options.type - Notification type
 * @param {string} options.title - Notification title
 * @param {string} [options.body] - Notification body
 * @param {string} [options.severity] - Severity level
 * @param {number} [options.ttl_seconds] - Time to live in seconds
 * @returns {string} Notification ID
 */
export function create(options) {
  const id = generateId();
  const now = Date.now();
  
  const notification = {
    id,
    type: options.type || NOTIFICATION_TYPE.TOAST,
    title: options.title || '',
    body: options.body || '',
    severity: options.severity || SEVERITY.INFO,
    ttl: (options.ttl_seconds || notificationsStore.defaultTtl) * 1000,
    createdAt: now,
    expiresAt: now + ((options.ttl_seconds || notificationsStore.defaultTtl) * 1000),
    dismissed: false,
  };
  
  // Add to active notifications
  notificationsStore.active = [...notificationsStore.active, notification];
  
  // Add to history
  addToHistory(notification);
  
  // Schedule auto-dismiss
  if (notification.ttl > 0) {
    setTimeout(() => dismiss(id), notification.ttl);
  }
  
  return id;
}

/**
 * Create an info notification
 * @param {string} message - Message text
 * @param {string} [title] - Optional title
 * @param {number} [ttl] - Time to live in seconds
 * @returns {string} Notification ID
 */
export function info(message, title = 'Info', ttl = 5) {
  return create({
    type: NOTIFICATION_TYPE.TOAST,
    title,
    body: message,
    severity: SEVERITY.INFO,
    ttl_seconds: ttl,
  });
}

/**
 * Create a success notification
 * @param {string} message - Message text
 * @param {string} [title] - Optional title
 * @param {number} [ttl] - Time to live in seconds
 * @returns {string} Notification ID
 */
export function success(message, title = 'Success', ttl = 3) {
  return create({
    type: NOTIFICATION_TYPE.TOAST,
    title,
    body: message,
    severity: SEVERITY.SUCCESS,
    ttl_seconds: ttl,
  });
}

/**
 * Create a warning notification
 * @param {string} message - Message text
 * @param {string} [title] - Optional title
 * @param {number} [ttl] - Time to live in seconds
 * @returns {string} Notification ID
 */
export function warning(message, title = 'Warning', ttl = 5) {
  return create({
    type: NOTIFICATION_TYPE.TOAST,
    title,
    body: message,
    severity: SEVERITY.WARNING,
    ttl_seconds: ttl,
  });
}

/**
 * Create an error notification
 * @param {string} message - Message text
 * @param {string} [title] - Optional title
 * @param {number} [ttl] - Time to live in seconds
 * @returns {string} Notification ID
 */
export function error(message, title = 'Error', ttl = 8) {
  return create({
    type: NOTIFICATION_TYPE.TOAST,
    title,
    body: message,
    severity: SEVERITY.ERROR,
    ttl_seconds: ttl,
  });
}

/**
 * Dismiss a notification
 * @param {string} id - Notification ID
 */
export function dismiss(id) {
  const notification = notificationsStore.active.find(n => n.id === id);
  if (notification) {
    notification.dismissed = true;
    notificationsStore.active = notificationsStore.active.filter(n => n.id !== id);
  }
}

/**
 * Dismiss all active notifications
 */
export function dismissAll() {
  notificationsStore.active.forEach(n => n.dismissed = true);
  notificationsStore.active = [];
}

/**
 * Add notification to history
 * @param {Object} notification - Notification object
 */
function addToHistory(notification) {
  notificationsStore.history = [notification, ...notificationsStore.history];
  
  // Trim history if too large
  if (notificationsStore.history.length > notificationsStore.maxHistory) {
    notificationsStore.history = notificationsStore.history.slice(0, notificationsStore.maxHistory);
  }
}

/**
 * Clear notification history
 */
export function clearHistory() {
  notificationsStore.history = [];
}

/**
 * Get active notifications
 * @returns {Array} Active notifications
 */
export function getActive() {
  return notificationsStore.active;
}

/**
 * Get notification history
 * @returns {Array} Notification history
 */
export function getHistory() {
  return notificationsStore.history;
}

/**
 * Subscribe to notification changes
 * @param {Function} callback - Callback function
 * @returns {Function} Unsubscribe function
 */
export function onNotificationChange(callback) {
  return subscribe('notifications', callback);
}

// Backward compatibility aliases
export const frontendInfo = info;
export const frontendSuccess = success;
export const frontendWarning = warning;
export const frontendError = error;

export default {
  store: notificationsStore,
  SEVERITY,
  NOTIFICATION_TYPE,
  create,
  info,
  success,
  warning,
  error,
  dismiss,
  dismissAll,
  clearHistory,
  getActive,
  getHistory,
  onNotificationChange,
  // Backward compatibility
  frontendInfo,
  frontendSuccess,
  frontendWarning,
  frontendError,
};
