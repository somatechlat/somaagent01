/**
 * Scheduler Feature Module
 * 
 * Public API for the Scheduler feature.
 * Re-exports store and API functions.
 * Includes SSE subscription for real-time task status updates.
 * 
 * @module features/scheduler
 * Requirements: 9.9
 */

import * as store from './scheduler.store.js';
import * as api from './scheduler.api.js';
import { on, off } from '../../js/event-bus.js';
import { SSE } from '../../core/events/types.js';

// Re-export store functions
export const {
  schedulerStore,
  TASK_TYPES,
  TASK_STATES,
  setTasks,
  addTask,
  updateTask,
  removeTask,
  setFilterType,
  setFilterState,
  setSort,
  selectTask,
  setLoading,
  setError,
  getFilteredTasks,
  getSelectedTask,
  onSchedulerChange,
} = store;

// Re-export API functions
export const {
  fetchTasks,
  createScheduledTask,
  createAdHocTask,
  createPlannedTask,
  updateTask: updateTaskApi,
  deleteTask,
  runTask,
  toggleTask,
} = api;

/**
 * SSE event handlers for scheduler
 */
let sseUnsubscribers = [];

/**
 * Handle task status update from SSE
 * @param {Object} data - Event data
 */
function handleTaskStatusUpdate(data) {
  if (!data || !data.task_id) return;
  
  const { task_id, status, state, ...rest } = data;
  
  // Update task in store
  store.updateTask(task_id, {
    state: state || status,
    ...rest,
  });
}

/**
 * Handle task created event from SSE
 * @param {Object} data - Event data
 */
function handleTaskCreated(data) {
  if (!data || !data.task) return;
  store.addTask(data.task);
}

/**
 * Handle task deleted event from SSE
 * @param {Object} data - Event data
 */
function handleTaskDeleted(data) {
  if (!data || !data.task_id) return;
  store.removeTask(data.task_id);
}

/**
 * Handle task run started event
 * @param {Object} data - Event data
 */
function handleTaskRunStarted(data) {
  if (!data || !data.task_id) return;
  store.updateTask(data.task_id, {
    state: store.TASK_STATES.RUNNING,
    last_run_started: data.started_at || new Date().toISOString(),
  });
}

/**
 * Handle task run completed event
 * @param {Object} data - Event data
 */
function handleTaskRunCompleted(data) {
  if (!data || !data.task_id) return;
  store.updateTask(data.task_id, {
    state: data.success ? store.TASK_STATES.IDLE : store.TASK_STATES.ERROR,
    last_run_completed: data.completed_at || new Date().toISOString(),
    last_run_success: data.success,
    last_run_error: data.error || null,
  });
}

/**
 * Subscribe to SSE events for scheduler updates
 * Call this when the scheduler feature is initialized
 */
export function subscribeToSSE() {
  // Unsubscribe from any existing subscriptions
  unsubscribeFromSSE();
  
  // Subscribe to scheduler-related SSE events
  sseUnsubscribers.push(
    on('scheduler.task.status', handleTaskStatusUpdate),
    on('scheduler.task.created', handleTaskCreated),
    on('scheduler.task.deleted', handleTaskDeleted),
    on('scheduler.task.run.started', handleTaskRunStarted),
    on('scheduler.task.run.completed', handleTaskRunCompleted),
    // Also listen for generic SSE events and filter
    on(SSE.EVENT, (event) => {
      if (event.type?.startsWith('scheduler.')) {
        const handler = {
          'scheduler.task.status': handleTaskStatusUpdate,
          'scheduler.task.created': handleTaskCreated,
          'scheduler.task.deleted': handleTaskDeleted,
          'scheduler.task.run.started': handleTaskRunStarted,
          'scheduler.task.run.completed': handleTaskRunCompleted,
        }[event.type];
        handler?.(event.data);
      }
    })
  );
}

/**
 * Unsubscribe from SSE events
 * Call this when the scheduler feature is destroyed
 */
export function unsubscribeFromSSE() {
  sseUnsubscribers.forEach(unsub => {
    if (typeof unsub === 'function') unsub();
  });
  sseUnsubscribers = [];
}

/**
 * Initialize scheduler feature
 * Fetches tasks and subscribes to SSE
 */
export async function initScheduler() {
  store.setLoading(true);
  store.setError(null);
  
  try {
    const tasks = await api.fetchTasks();
    store.setTasks(tasks);
    subscribeToSSE();
  } catch (error) {
    store.setError(error.message || 'Failed to load tasks');
    console.error('Scheduler init error:', error);
  } finally {
    store.setLoading(false);
  }
}

/**
 * Cleanup scheduler feature
 */
export function cleanupScheduler() {
  unsubscribeFromSSE();
}

export default {
  store,
  api,
  initScheduler,
  cleanupScheduler,
  subscribeToSSE,
  unsubscribeFromSSE,
};
