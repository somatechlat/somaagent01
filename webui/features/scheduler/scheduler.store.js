/**
 * Scheduler Store
 * 
 * Centralized state management for the Scheduler feature.
 * 
 * @module features/scheduler/scheduler.store
 */

import { createStore, subscribe } from '../../core/state/store.js';

/**
 * Task types
 */
export const TASK_TYPES = Object.freeze({
  SCHEDULED: 'scheduled',
  ADHOC: 'adhoc',
  PLANNED: 'planned',
});

/**
 * Task states
 */
export const TASK_STATES = Object.freeze({
  IDLE: 'idle',
  RUNNING: 'running',
  DISABLED: 'disabled',
  ERROR: 'error',
});

/**
 * Initial scheduler state
 */
const initialState = {
  // Tasks
  tasks: [],
  
  // Filters
  filterType: 'all', // 'all' | 'scheduled' | 'adhoc' | 'planned'
  filterState: 'all', // 'all' | 'idle' | 'running' | 'disabled' | 'error'
  
  // Sort
  sortField: 'name',
  sortDirection: 'asc',
  
  // Selected task
  selectedTaskId: null,
  
  // UI state
  isLoading: false,
  error: null,
};

/**
 * Scheduler store instance
 */
export const schedulerStore = createStore('scheduler', initialState, {
  persist: true,
  persistKeys: ['filterType', 'filterState', 'sortField', 'sortDirection'],
});

/**
 * Set tasks
 * @param {Array} tasks - Task list
 */
export function setTasks(tasks) {
  schedulerStore.tasks = tasks || [];
}

/**
 * Add a task
 * @param {Object} task - Task to add
 */
export function addTask(task) {
  schedulerStore.tasks = [...schedulerStore.tasks, task];
}

/**
 * Update a task
 * @param {string} taskId - Task ID
 * @param {Object} updates - Updates to apply
 */
export function updateTask(taskId, updates) {
  const index = schedulerStore.tasks.findIndex(t => t.id === taskId);
  if (index >= 0) {
    schedulerStore.tasks[index] = { ...schedulerStore.tasks[index], ...updates };
    schedulerStore.tasks = [...schedulerStore.tasks];
  }
}

/**
 * Remove a task
 * @param {string} taskId - Task ID
 */
export function removeTask(taskId) {
  schedulerStore.tasks = schedulerStore.tasks.filter(t => t.id !== taskId);
}

/**
 * Set filter type
 * @param {string} type - Filter type
 */
export function setFilterType(type) {
  schedulerStore.filterType = type;
}

/**
 * Set filter state
 * @param {string} state - Filter state
 */
export function setFilterState(state) {
  schedulerStore.filterState = state;
}

/**
 * Set sort
 * @param {string} field - Sort field
 * @param {string} direction - Sort direction
 */
export function setSort(field, direction) {
  schedulerStore.sortField = field;
  schedulerStore.sortDirection = direction;
}

/**
 * Select a task
 * @param {string|null} taskId - Task ID
 */
export function selectTask(taskId) {
  schedulerStore.selectedTaskId = taskId;
}

/**
 * Set loading state
 * @param {boolean} loading - Loading state
 */
export function setLoading(loading) {
  schedulerStore.isLoading = loading;
}

/**
 * Set error state
 * @param {string|null} error - Error message
 */
export function setError(error) {
  schedulerStore.error = error;
}

/**
 * Get filtered and sorted tasks
 * @returns {Array} Filtered tasks
 */
export function getFilteredTasks() {
  let result = [...schedulerStore.tasks];
  
  // Filter by type
  if (schedulerStore.filterType !== 'all') {
    result = result.filter(t => t.type === schedulerStore.filterType);
  }
  
  // Filter by state
  if (schedulerStore.filterState !== 'all') {
    result = result.filter(t => t.state === schedulerStore.filterState);
  }
  
  // Sort
  const { sortField, sortDirection } = schedulerStore;
  result.sort((a, b) => {
    let cmp = 0;
    if (sortField === 'name') {
      cmp = (a.name || '').localeCompare(b.name || '');
    } else if (sortField === 'type') {
      cmp = (a.type || '').localeCompare(b.type || '');
    } else if (sortField === 'state') {
      cmp = (a.state || '').localeCompare(b.state || '');
    } else if (sortField === 'next_run') {
      cmp = new Date(a.next_run || 0) - new Date(b.next_run || 0);
    }
    return sortDirection === 'desc' ? -cmp : cmp;
  });
  
  return result;
}

/**
 * Get selected task
 * @returns {Object|null} Selected task
 */
export function getSelectedTask() {
  if (!schedulerStore.selectedTaskId) return null;
  return schedulerStore.tasks.find(t => t.id === schedulerStore.selectedTaskId) || null;
}

/**
 * Subscribe to scheduler changes
 * @param {Function} callback - Callback function
 * @returns {Function} Unsubscribe function
 */
export function onSchedulerChange(callback) {
  return subscribe('scheduler', callback);
}

export default {
  store: schedulerStore,
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
};
