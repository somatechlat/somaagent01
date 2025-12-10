/**
 * Event Type Constants
 * 
 * Centralized event type definitions for the event bus.
 * Using constants prevents typos and enables IDE autocomplete.
 * 
 * @module core/events/types
 */

/**
 * Stream/SSE events
 */
export const STREAM = Object.freeze({
  ONLINE: 'stream.online',
  OFFLINE: 'stream.offline',
  STALE: 'stream.stale',
  HEARTBEAT: 'stream.heartbeat',
  RECONNECTING: 'stream.reconnecting',
  RETRY_SUCCESS: 'stream.retry.success',
  RETRY_GIVEUP: 'stream.retry.giveup',
  REQUEST_RECONNECT: 'stream.requestReconnect',
});

/**
 * SSE event types from backend
 */
export const SSE = Object.freeze({
  EVENT: 'sse:event',
  KEEPALIVE: 'system.keepalive',
  ASSISTANT_STARTED: 'assistant.started',
  ASSISTANT_DELTA: 'assistant.delta',
  ASSISTANT_FINAL: 'assistant.final',
  ASSISTANT_THINKING_STARTED: 'assistant.thinking.started',
  ASSISTANT_THINKING_FINAL: 'assistant.thinking.final',
  TOOL_STARTED: 'assistant.tool.started',
  TOOL_DELTA: 'assistant.tool.delta',
  TOOL_FINAL: 'assistant.tool.final',
  UPLOADS_PROGRESS: 'uploads.progress',
});

/**
 * UI events
 */
export const UI = Object.freeze({
  SIDEBAR_TOGGLE: 'ui.sidebar.toggle',
  TAB_CHANGE: 'ui.tab.change',
  MODAL_OPEN: 'ui.modal.open',
  MODAL_CLOSE: 'ui.modal.close',
  THEME_CHANGE: 'ui.theme.change',
  RESIZE: 'ui.resize',
});

/**
 * Chat events
 */
export const CHAT = Object.freeze({
  MESSAGE_SENT: 'chat.message.sent',
  MESSAGE_RECEIVED: 'chat.message.received',
  CONTEXT_CHANGE: 'chat.context.change',
  RESET: 'chat.reset',
  NEW: 'chat.new',
  DELETE: 'chat.delete',
  SELECT: 'chat.select',
});

/**
 * Settings events
 */
export const SETTINGS = Object.freeze({
  OPEN: 'settings.open',
  CLOSE: 'settings.close',
  TAB_CHANGE: 'settings.tab.change',
  SAVE: 'settings.save',
  LOAD: 'settings.load',
  ERROR: 'settings.error',
});

/**
 * Notification events
 */
export const NOTIFICATION = Object.freeze({
  CREATE: 'notification.create',
  DISMISS: 'notification.dismiss',
  CLEAR_ALL: 'notification.clearAll',
});

/**
 * Component events
 */
export const COMPONENT = Object.freeze({
  LOADED: 'component.loaded',
  ERROR: 'component.error',
  WARNING: 'component.warning',
});

/**
 * Error events
 */
export const ERROR = Object.freeze({
  EVENTBUS: 'eventbus.error',
  CRITICAL: 'eventbus.critical',
  API: 'error.api',
  COMPONENT: 'error.component',
});

/**
 * Scheduler events
 */
export const SCHEDULER = Object.freeze({
  TASK_CREATED: 'scheduler.task.created',
  TASK_UPDATED: 'scheduler.task.updated',
  TASK_DELETED: 'scheduler.task.deleted',
  TASK_RUN: 'scheduler.task.run',
});

/**
 * All event types grouped
 */
export const EVENTS = Object.freeze({
  STREAM,
  SSE,
  UI,
  CHAT,
  SETTINGS,
  NOTIFICATION,
  COMPONENT,
  ERROR,
  SCHEDULER,
});

export default EVENTS;
