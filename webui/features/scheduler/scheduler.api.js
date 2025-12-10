/**
 * Scheduler API
 * 
 * API calls for the Scheduler feature.
 * Wraps existing scheduler endpoints.
 * 
 * @module features/scheduler/scheduler.api
 */

import { fetchApi } from '../../core/api/client.js';
import { ENDPOINTS, buildUrl } from '../../core/api/endpoints.js';

/**
 * Fetch all scheduler tasks
 * @returns {Promise<Array>} Array of task objects
 */
export async function fetchTasks() {
  const response = await fetchApi('/scheduler_tasks_list', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({}),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch tasks: ${response.status}`);
  }
  
  const data = await response.json();
  return data.tasks || [];
}

/**
 * Create a scheduled task (cron-based)
 * @param {Object} task - Task configuration
 * @param {string} task.name - Task name
 * @param {string} task.prompt - Task prompt
 * @param {Object} task.schedule - Cron schedule
 * @returns {Promise<Object>} Created task
 */
export async function createScheduledTask(task) {
  const response = await fetchApi('/scheduler_task_create', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      type: 'scheduled',
      name: task.name,
      prompt: task.prompt,
      schedule: task.schedule,
      enabled: task.enabled ?? true,
    }),
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Failed to create task');
  }
  
  return response.json();
}

/**
 * Create an ad-hoc task (token-triggered)
 * @param {Object} task - Task configuration
 * @param {string} task.name - Task name
 * @param {string} task.prompt - Task prompt
 * @returns {Promise<Object>} Created task with token
 */
export async function createAdHocTask(task) {
  const response = await fetchApi('/scheduler_task_create', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      type: 'adhoc',
      name: task.name,
      prompt: task.prompt,
      enabled: task.enabled ?? true,
    }),
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Failed to create task');
  }
  
  return response.json();
}

/**
 * Create a planned task (datetime-scheduled)
 * @param {Object} task - Task configuration
 * @param {string} task.name - Task name
 * @param {string} task.prompt - Task prompt
 * @param {string} task.scheduled_time - ISO datetime
 * @returns {Promise<Object>} Created task
 */
export async function createPlannedTask(task) {
  const response = await fetchApi('/scheduler_task_create', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      type: 'planned',
      name: task.name,
      prompt: task.prompt,
      scheduled_time: task.scheduled_time,
      enabled: task.enabled ?? true,
    }),
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Failed to create task');
  }
  
  return response.json();
}

/**
 * Update a task
 * @param {string} taskId - Task ID
 * @param {Object} updates - Task updates
 * @returns {Promise<Object>} Updated task
 */
export async function updateTask(taskId, updates) {
  const response = await fetchApi('/scheduler_task_update', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      task_id: taskId,
      ...updates,
    }),
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Failed to update task');
  }
  
  return response.json();
}

/**
 * Delete a task
 * @param {string} taskId - Task ID
 * @returns {Promise<void>}
 */
export async function deleteTask(taskId) {
  const response = await fetchApi('/scheduler_task_delete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ task_id: taskId }),
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Failed to delete task');
  }
}

/**
 * Run a task immediately
 * @param {string} taskId - Task ID
 * @returns {Promise<Object>} Run result
 */
export async function runTask(taskId) {
  const response = await fetchApi('/scheduler_task_run', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ task_id: taskId }),
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Failed to run task');
  }
  
  return response.json();
}

/**
 * Toggle task enabled state
 * @param {string} taskId - Task ID
 * @param {boolean} enabled - New enabled state
 * @returns {Promise<Object>} Updated task
 */
export async function toggleTask(taskId, enabled) {
  return updateTask(taskId, { enabled });
}

export default {
  fetchTasks,
  createScheduledTask,
  createAdHocTask,
  createPlannedTask,
  updateTask,
  deleteTask,
  runTask,
  toggleTask,
};
