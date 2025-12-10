/**
 * Core Module Index
 * 
 * Re-exports all core infrastructure modules.
 * Import from 'core' to access API client, state management, events, SSE, etc.
 * 
 * @module core
 */

// API Layer
export * from './api/client.js';
export * from './api/endpoints.js';

// State Management
export * from './state/store.js';

// Events
export * from './events/types.js';

// SSE Manager
export { sseManager, ConnectionState } from './sse/manager.js';

// Keyboard Navigation & Shortcuts
export * from './keyboard/index.js';

// Re-export event bus from existing location for backward compatibility
export { emit, on, once, off } from '../js/event-bus.js';
