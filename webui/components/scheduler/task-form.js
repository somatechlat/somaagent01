/**
 * Task Form Component
 *
 * Form for creating and editing scheduler tasks.
 * Includes cron builder, datetime picker, and token display.
 *
 * @module components/scheduler/task-form
 * Requirements: 9.4, 9.5, 9.6
 */

import { TASK_TYPES } from '../../features/scheduler/scheduler.store.js';
import {
  createScheduledTask,
  createAdHocTask,
  createPlannedTask,
  updateTask,
} from '../../features/scheduler/scheduler.api.js';

/**
 * Cron presets for quick selection
 */
const CRON_PRESETS = [
  { label: 'Every minute', value: { minute: '*', hour: '*', day: '*', month: '*', weekday: '*' } },
  { label: 'Every hour', value: { minute: '0', hour: '*', day: '*', month: '*', weekday: '*' } },
  { label: 'Every day at midnight', value: { minute: '0', hour: '0', day: '*', month: '*', weekday: '*' } },
  { label: 'Every day at noon', value: { minute: '0', hour: '12', day: '*', month: '*', weekday: '*' } },
  { label: 'Every Monday', value: { minute: '0', hour: '9', day: '*', month: '*', weekday: '1' } },
  { label: 'Every weekday', value: { minute: '0', hour: '9', day: '*', month: '*', weekday: '1-5' } },
  { label: 'First of month', value: { minute: '0', hour: '0', day: '1', month: '*', weekday: '*' } },
];

/**
 * Task Form component factory
 * @param {Object} options - Component options
 * @param {Object} options.task - Existing task for editing (optional)
 * @param {Function} options.onSave - Callback after save
 * @param {Function} options.onCancel - Callback on cancel
 * @returns {Object} Alpine component data
 */
export default function TaskForm(options = {}) {
  const existingTask = options.task ?? null;
  const isEditing = !!existingTask;

  return {
    // Form state
    isEditing,
    taskId: existingTask?.id ?? null,

    // Form fields
    name: existingTask?.name ?? '',
    prompt: existingTask?.prompt ?? '',
    type: existingTask?.type ?? TASK_TYPES.SCHEDULED,
    enabled: existingTask?.enabled ?? true,

    // Scheduled task fields (cron)
    cronMinute: existingTask?.schedule?.minute ?? '0',
    cronHour: existingTask?.schedule?.hour ?? '*',
    cronDay: existingTask?.schedule?.day ?? '*',
    cronMonth: existingTask?.schedule?.month ?? '*',
    cronWeekday: existingTask?.schedule?.weekday ?? '*',
    selectedPreset: null,

    // Planned task fields
    scheduledDate: '',
    scheduledTime: '',

    // Ad-hoc task fields
    generatedToken: existingTask?.token ?? null,

    // UI state
    isSubmitting: false,
    error: null,
    showAdvancedCron: false,

    // Callbacks
    onSave: options.onSave ?? (() => {}),
    onCancel: options.onCancel ?? (() => {}),

    /**
     * Initialize form
     */
    init() {
      if (this.isEditing && existingTask?.scheduled_time) {
        const dt = new Date(existingTask.scheduled_time);
        this.scheduledDate = dt.toISOString().split('T')[0];
        this.scheduledTime = dt.toTimeString().slice(0, 5);
      }
    },

    /**
     * Get task types for dropdown
     */
    get taskTypes() {
      return [
        { value: TASK_TYPES.SCHEDULED, label: 'Scheduled (Cron)', icon: '🕐' },
        { value: TASK_TYPES.ADHOC, label: 'Ad-hoc (Token)', icon: '⚡' },
        { value: TASK_TYPES.PLANNED, label: 'Planned (One-time)', icon: '📅' },
      ];
    },

    /**
     * Get cron presets
     */
    get cronPresets() {
      return CRON_PRESETS;
    },

    /**
     * Check if form is valid
     */
    get isValid() {
      if (!this.name.trim()) return false;
      if (!this.prompt.trim()) return false;

      if (this.type === TASK_TYPES.PLANNED) {
        if (!this.scheduledDate || !this.scheduledTime) return false;
      }

      return true;
    },

    /**
     * Get current cron schedule object
     */
    get cronSchedule() {
      return {
        minute: this.cronMinute,
        hour: this.cronHour,
        day: this.cronDay,
        month: this.cronMonth,
        weekday: this.cronWeekday,
      };
    },

    /**
     * Get cron expression string
     */
    get cronExpression() {
      return `${this.cronMinute} ${this.cronHour} ${this.cronDay} ${this.cronMonth} ${this.cronWeekday}`;
    },

    /**
     * Get human-readable cron description
     */
    get cronDescription() {
      const { cronMinute, cronHour, cronDay, cronMonth, cronWeekday } = this;

      if (cronMinute === '*' && cronHour === '*') return 'Every minute';
      if (cronMinute === '0' && cronHour === '*') return 'Every hour at minute 0';
      if (cronMinute === '0' && cronHour === '0' && cronDay === '*' && cronWeekday === '*') {
        return 'Every day at midnight';
      }
      if (cronWeekday !== '*' && cronDay === '*') {
        return `At ${cronHour}:${cronMinute.padStart(2, '0')} on ${this.formatWeekday(cronWeekday)}`;
      }
      if (cronDay !== '*' && cronMonth === '*') {
        return `At ${cronHour}:${cronMinute.padStart(2, '0')} on day ${cronDay} of every month`;
      }

      return this.cronExpression;
    },

    /**
     * Format weekday for display
     * @param {string} weekday - Weekday value
     * @returns {string} Formatted weekday
     */
    formatWeekday(weekday) {
      const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
      if (weekday === '1-5') return 'weekdays';
      if (weekday === '0,6') return 'weekends';
      const num = parseInt(weekday, 10);
      return days[num] ?? weekday;
    },

    /**
     * Get scheduled datetime ISO string
     */
    get scheduledDateTime() {
      if (!this.scheduledDate || !this.scheduledTime) return null;
      return `${this.scheduledDate}T${this.scheduledTime}:00`;
    },

    /**
     * Apply cron preset
     * @param {number} index - Preset index
     */
    applyPreset(index) {
      const preset = CRON_PRESETS[index];
      if (preset) {
        this.cronMinute = preset.value.minute;
        this.cronHour = preset.value.hour;
        this.cronDay = preset.value.day;
        this.cronMonth = preset.value.month;
        this.cronWeekday = preset.value.weekday;
        this.selectedPreset = index;
      }
    },

    /**
     * Clear preset selection when manually editing
     */
    clearPreset() {
      this.selectedPreset = null;
    },

    /**
     * Toggle advanced cron editor
     */
    toggleAdvancedCron() {
      this.showAdvancedCron = !this.showAdvancedCron;
    },

    /**
     * Copy token to clipboard
     */
    async copyToken() {
      if (this.generatedToken) {
        try {
          await navigator.clipboard.writeText(this.generatedToken);
          // Could emit toast notification here
        } catch (err) {
          console.error('Failed to copy token:', err);
        }
      }
    },

    /**
     * Submit form
     */
    async submit() {
      if (!this.isValid || this.isSubmitting) return;

      this.isSubmitting = true;
      this.error = null;

      try {
        let result;

        if (this.isEditing) {
          // Update existing task
          const updates = {
            name: this.name,
            prompt: this.prompt,
            enabled: this.enabled,
          };

          if (this.type === TASK_TYPES.SCHEDULED) {
            updates.schedule = this.cronSchedule;
          } else if (this.type === TASK_TYPES.PLANNED) {
            updates.scheduled_time = this.scheduledDateTime;
          }

          result = await updateTask(this.taskId, updates);
        } else {
          // Create new task
          const taskData = {
            name: this.name,
            prompt: this.prompt,
            enabled: this.enabled,
          };

          if (this.type === TASK_TYPES.SCHEDULED) {
            taskData.schedule = this.cronSchedule;
            result = await createScheduledTask(taskData);
          } else if (this.type === TASK_TYPES.ADHOC) {
            result = await createAdHocTask(taskData);
            // Store generated token
            if (result.token) {
              this.generatedToken = result.token;
            }
          } else if (this.type === TASK_TYPES.PLANNED) {
            taskData.scheduled_time = this.scheduledDateTime;
            result = await createPlannedTask(taskData);
          }
        }

        this.onSave(result);
      } catch (err) {
        this.error = err.message || 'Failed to save task';
        console.error('Task form error:', err);
      } finally {
        this.isSubmitting = false;
      }
    },

    /**
     * Cancel form
     */
    cancel() {
      this.onCancel();
    },

    /**
     * Reset form
     */
    reset() {
      this.name = '';
      this.prompt = '';
      this.type = TASK_TYPES.SCHEDULED;
      this.enabled = true;
      this.cronMinute = '0';
      this.cronHour = '*';
      this.cronDay = '*';
      this.cronMonth = '*';
      this.cronWeekday = '*';
      this.selectedPreset = null;
      this.scheduledDate = '';
      this.scheduledTime = '';
      this.generatedToken = null;
      this.error = null;
    },
  };
}

export { CRON_PRESETS };
