/**
 * Code Execution Display Component
 *
 * Specialized display for code execution tool results.
 * Shows collapsible code input and output sections.
 *
 * @module components/chat/code-execution-display
 */

import { toastManager } from '../base/toast.js';

/**
 * Runtime icons
 */
const RUNTIME_ICONS = {
  python: '🐍',
  nodejs: '🟢',
  terminal: '💻',
  bash: '💻',
  shell: '💻',
  default: '⚡',
};

/**
 * Code Execution Display component factory
 * @param {Object} options - Component options
 * @param {Object} options.execution - Execution data
 * @returns {Object} Alpine component data
 */
export default function CodeExecutionDisplay(options = {}) {
  return {
    execution: options.execution ?? {},

    // UI state
    showInput: true,
    showOutput: true,
    copied: false,

    /**
     * Get runtime type
     */
    get runtime() {
      return this.execution.runtime ?? 'terminal';
    },

    /**
     * Get runtime icon
     */
    get runtimeIcon() {
      return RUNTIME_ICONS[this.runtime] ?? RUNTIME_ICONS.default;
    },

    /**
     * Get runtime display name
     */
    get runtimeName() {
      const names = {
        python: 'Python',
        nodejs: 'Node.js',
        terminal: 'Terminal',
        bash: 'Bash',
        shell: 'Shell',
      };
      return names[this.runtime] ?? this.runtime;
    },

    /**
     * Get code input
     */
    get code() {
      return this.execution.code ?? this.execution.input ?? '';
    },
