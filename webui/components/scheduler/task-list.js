/**
 * Task List Component
 *
 * Displays scheduler tasks in a table with name, type, schedule, and status.
 *
 * @module components/scheduler/task-list
 * Requirements: 9.2
 */

import {
  schedulerStore,
  TASK_TYPES,
  TASK_STATES,
  getFilteredTasks,
  selectTask,
  setFilterType,
  setFilterState,
  setSort,
} from '../../features/scheduler/scheduler.store.js';

/**
 * Task type icons
 */
const TYPE_ICONS = {
  [TASK_TYPES.SCHEDULED]: '🕐',
  [TASK_TYPES.ADHOC]: '⚡',
  [TASK_TYPES.PLANNED]: '📅',
};

/**
 * Task type labels
 */
const TYPE_LABELS = {
  [TASK_TYPES.SCHEDULED]: 'Scheduled',
  [TASK_TYPES.ADHOC]: 'Ad-hoc',
  [TASK_TYPES.PLANNED]: 'Planned',
};

/**
 * Task state colors
 */
const STATE_COLORS = {
  [TASK_STATES.IDLE]: 'var(--text-secondary)',
  [TASK_STATES.RUNNING]: 'var(--info)',
  [TASK_STATES.DISABLED]: 'var(--text-muted)',
  [TASK_STATES.ERROR]: 'var(--error)',
};

/**
 * Task List component factory
 * @param {Object} options - Component options
 * @returns {Object} Alpine component data
 */
export default function TaskList(options = {}) {
  return {
    // Reference to store
    store: schedulerStore,

    // Local UI state
    searchQuery: '',

    /**
     * Get filtered tasks
     */
    get tasks() {
      let tasks = getFilteredTasks();

      // Apply local search filter
      if (this.searchQuery.trim()) {
        const query = this.searchQuery.toLowerCase();
        tasks = tasks.filter(
          (t) =>
            t.name?.toLowerCase().includes(query) || t.prompt?.toLowerCase().includes(query)
        );
      }

      return tasks;
    },

    /**
     * Get task count
     */
    get taskCount() {
      return this.tasks.length;
    },

    /**
     * Get total task count (unfiltered)
     */
    get totalCount() {
      return schedulerStore.tasks.length;
    },

    /**
     * Check if loading
     */
    get isLoading() {
      return schedulerStore.isLoading;
    },

    /**
     * Get error message
     */
    get error() {
      return schedulerStore.error;
    },

    /**
     * Get current filter type
     */
    get filterType() {
      return schedulerStore.filterType;
    },

    /**
     * Get current filter state
     */
    get filterState() {
      return schedulerStore.filterState;
    },

    /**
     * Get current sort field
     */
    get sortField() {
      return schedulerStore.sortField;
    },

    /**
     * Get current sort direction
     */
    get sortDirection() {
      return schedulerStore.sortDirection;
    },

    /**
     * Get selected task ID
     */
    get selectedTaskId() {
      return schedulerStore.selectedTaskId;
    },

    /**
     * Get type icon
     * @param {string} type - Task type
     * @returns {string} Icon emoji
     */
    getTypeIcon(type) {
      return TYPE_ICONS[type] ?? '📋';
    },

    /**
     * Get type label
     * @param {string} type - Task type
     * @returns {string} Display label
     */
    getTypeLabel(type) {
      return TYPE_LABELS[type] ?? type;
    },

    /**
     * Get state color
     * @param {string} state - Task state
     * @returns {string} CSS color
     */
    getStateColor(state) {
      return STATE_COLORS[state] ?? 'var(--text-secondary)';
    },

    /**
     * Get state label
     * @param {string} state - Task state
     * @returns {string} Display label
     */
    getStateLabel(state) {
      return state?.charAt(0).toUpperCase() + state?.slice(1) ?? 'Unknown';
    },

    /**
     * Format schedule for display
     * @param {Object} task - Task object
     * @returns {string} Formatted schedule
     */
    formatSchedule(task) {
      if (task.type === TASK_TYPES.SCHEDULED && task.schedule) {
        return this.formatCron(task.schedule);
      }
      if (task.type === TASK_TYPES.PLANNED && task.scheduled_time) {
        return this.formatDateTime(task.scheduled_time);
      }
      if (task.type === TASK_TYPES.ADHOC) {
        return 'Token-triggered';
      }
      return '-';
    },

    /**
     * Format cron schedule
     * @param {Object} schedule - Cron schedule object
     * @returns {string} Human-readable schedule
     */
    formatCron(schedule) {
      if (!schedule) return '-';

      const { minute, hour, day, month, weekday } = schedule;

      // Simple human-readable conversion
      if (minute === '*' && hour === '*') return 'Every minute';
      if (minute === '0' && hour === '*') return 'Every hour';
      if (minute === '0' && hour === '0') return 'Daily at midnight';
      if (weekday && weekday !== '*') return `Weekly on ${this.formatWeekday(weekday)}`;

      // Fallback to cron notation
      return `${minute ?? '*'} ${hour ?? '*'} ${day ?? '*'} ${month ?? '*'} ${weekday ?? '*'}`;
    },

    /**
     * Format weekday number to name
     * @param {string|number} weekday - Weekday number (0-6)
     * @returns {string} Weekday name
     */
    formatWeekday(weekday) {
      const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
      const num = parseInt(weekday, 10);
      return days[num] ?? weekday;
    },

    /**
     * Format datetime
     * @param {string} datetime - ISO datetime string
     * @returns {string} Formatted datetime
     */
    formatDateTime(datetime) {
      if (!datetime) return '-';
      const date = new Date(datetime);
      return date.toLocaleString(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short',
      });
    },

    /**
     * Format next run time
     * @param {string} nextRun - ISO datetime string
     * @returns {string} Relative time
     */
    formatNextRun(nextRun) {
      if (!nextRun) return '-';
      const date = new Date(nextRun);
      const now = new Date();
      const diff = date - now;

      if (diff < 0) return 'Overdue';
      if (diff < 60000) return 'Less than a minute';
      if (diff < 3600000) return `${Math.round(diff / 60000)} minutes`;
      if (diff < 86400000) return `${Math.round(diff / 3600000)} hours`;
      return `${Math.round(diff / 86400000)} days`;
    },

    /**
     * Check if task is selected
     * @param {string} taskId - Task ID
     * @returns {boolean}
     */
    isSelected(taskId) {
      return this.selectedTaskId === taskId;
    },

    /**
     * Select a task
     * @param {string} taskId - Task ID
     */
    select(taskId) {
      selectTask(taskId);
    },

    /**
     * Set filter type
     * @param {string} type - Filter type
     */
    setType(type) {
      setFilterType(type);
    },

    /**
     * Set filter state
     * @param {string} state - Filter state
     */
    setState(state) {
      setFilterState(state);
    },

    /**
     * Toggle sort
     * @param {string} field - Sort field
     */
    toggleSort(field) {
      if (this.sortField === field) {
        setSort(field, this.sortDirection === 'asc' ? 'desc' : 'asc');
      } else {
        setSort(field, 'asc');
      }
    },

    /**
     * Get sort indicator
     * @param {string} field - Sort field
     * @returns {string} Sort indicator
     */
    getSortIndicator(field) {
      if (this.sortField !== field) return '';
      return this.sortDirection === 'asc' ? '↑' : '↓';
    },

    /**
     * Clear filters
     */
    clearFilters() {
      this.searchQuery = '';
      setFilterType('all');
      setFilterState('all');
    },
  };
}

export { TYPE_ICONS, TYPE_LABELS, STATE_COLORS };
