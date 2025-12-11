/**
 * API Endpoint Definitions
 * 
 * Centralized endpoint configuration following VIBE Coding Rules.
 * All API paths are defined here - no hardcoded strings elsewhere.
 * 
 * @module core/api/endpoints
 */

/** API version prefix */
export const API_VERSION = '/v1';

/** 
 * API endpoint definitions
 * All paths are relative to API_VERSION
 */
export const ENDPOINTS = Object.freeze({
  // Health & Status
  HEALTH: '/health',
  SOMABRAIN_HEALTH: '/somabrain/health',
  
  // Sessions & Chat
  SESSIONS: '/sessions',
  SESSION: (sessionId) => `/sessions/${encodeURIComponent(sessionId)}`,
  SESSION_MESSAGE: '/session/message',
  SESSION_EVENTS: (sessionId) => `/session/${encodeURIComponent(sessionId)}/events`,
  SESSION_HISTORY: (sessionId) => `/sessions/${encodeURIComponent(sessionId)}/history`,
  CHAT: '/llm/invoke',
  
  // Settings
  SETTINGS: '/settings/sections',
  SETTINGS_SECTIONS: '/settings/sections',
  TEST_CONNECTION: '/settings/test-connection',
  
  // Uploads & Attachments
  UPLOADS: '/uploads',
  ATTACHMENTS: '/attachments',
  
  // Notifications
  NOTIFICATIONS: '/notifications',
  
  // Scheduler
  SCHEDULER_TASKS: '/scheduler/tasks',
  SCHEDULER_TASK: (taskId) => `/scheduler/tasks/${encodeURIComponent(taskId)}`,
  
  // Memory
  MEMORY: '/memory',
});

/**
 * Build full API URL from endpoint
 * @param {string|Function} endpoint - Endpoint path or function
 * @param {...any} args - Arguments for endpoint function
 * @returns {string} Full API URL
 */
export function buildUrl(endpoint, ...args) {
  const path = typeof endpoint === 'function' ? endpoint(...args) : endpoint;
  return `${API_VERSION}${path}`;
}
