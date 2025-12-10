/**
 * Scheduler Feature Module
 * 
 * Public API for the Scheduler feature.
 * Re-exports store and API functions.
 * 
 * @module features/scheduler
 */

import * as store from './scheduler.store.js';
import * as api from './scheduler.api.js';

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

export default {
  store,
  api,
};
