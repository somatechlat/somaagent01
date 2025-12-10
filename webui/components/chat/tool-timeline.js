/**
 * Tool Timeline Component
 *
 * Displays multiple tool executions in chronological order with timeline visualization.
 *
 * @module components/chat/tool-timeline
 * Requirements: 5.9
 */

import { TOOL_ICONS } from './tool-execution.js';

/**
 * Tool Timeline component factory
 * @param {Object} options - Component options
 * @param {Array} options.tools - Array of tool execution data
 * @returns {Object} Alpine component data
 */
export default function ToolTimeline(options = {}) {
  return {
    tools: options.tools ?? [],

    // UI state
    expandedTools: new Set(),
    showAll: false,
    maxVisible: 3,

    /**
     * Initialize component
     */
    init() {
      // Auto-expand running tools
      this.tools.forEach((tool, index) => {
        if (tool.status === 'running') {
          this.expandedTools.add(index);
        }
      });
    },

    /**
     * Get sorted tools by start time
     */
    get sortedTools() {
      return [...this.tools].sort((a, b) => {
        const timeA = a.started_at ?? a.timestamp ?? 0;
        const timeB = b.started_at ?? b.timestamp ?? 0;
        return new Date(timeA) - new Date(timeB);
      });
    },

    /**
     * Get visible tools based on showAll state
     */
    get visibleTools() {
      if (this.showAll || this.tools.length <= this.maxVisible) {
        return this.sortedTools;
      }
      return this.sortedTools.slice(0, this.maxVisible);
    },

    /**
     * Get hidden tools count
     */
    get hiddenCount() {
      if (this.showAll) return 0;
      return Math.max(0, this.tools.length - this.maxVisible);
    },

    /**
     * Check if there are hidden tools
     */
    get hasHiddenTools() {
      return this.hiddenCount > 0;
    },

    /**
     * Get total tools count
     */
    get totalCount() {
      return this.tools.length;
    },

    /**
     * Get running tools count
     */
    get runningCount() {
      return this.tools.filter((t) => t.status === 'running').length;
    },

    /**
     * Get successful tools count
     */
    get successCount() {
      return this.tools.filter((t) => t.status === 'success').length;
    },

    /**
     * Get failed tools count
     */
    get errorCount() {
      return this.tools.filter((t) => t.status === 'error').length;
    },

    /**
     * Check if any tool is running
     */
    get hasRunning() {
      return this.runningCount > 0;
    },

    /**
     * Check if all tools completed
     */
    get allCompleted() {
      return this.runningCount === 0 && this.totalCount > 0;
    },

    /**
     * Get overall status
     */
    get overallStatus() {
      if (this.hasRunning) return 'running';
      if (this.errorCount > 0) return 'partial';
      return 'success';
    },

    /**
     * Get summary text
     */
    get summary() {
      if (this.hasRunning) {
        return `${this.runningCount} tool${this.runningCount > 1 ? 's' : ''} running...`;
      }
      if (this.errorCount > 0) {
        return `${this.successCount}/${this.totalCount} completed, ${this.errorCount} failed`;
      }
      return `${this.totalCount} tool${this.totalCount > 1 ? 's' : ''} completed`;
    },

    /**
     * Get total duration
     */
    get totalDuration() {
      const total = this.tools.reduce((sum, tool) => {
        return sum + (tool.duration ?? 0);
      }, 0);
      if (total === 0) return null;
      return `${(total / 1000).toFixed(2)}s`;
    },

    /**
     * Get tool icon
     * @param {Object} tool - Tool data
     * @returns {string} Icon emoji
     */
    getToolIcon(tool) {
      const name = tool.name ?? tool.tool_name ?? '';
      return TOOL_ICONS[name] ?? TOOL_ICONS.default;
    },

    /**
     * Get tool name
     * @param {Object} tool - Tool data
     * @returns {string} Display name
     */
    getToolName(tool) {
      const name = tool.name ?? tool.tool_name ?? 'Unknown';
      return name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    },

    /**
     * Get tool status class
     * @param {Object} tool - Tool data
     * @returns {string} CSS class
     */
    getStatusClass(tool) {
      switch (tool.status) {
        case 'running':
          return 'timeline-item-running';
        case 'success':
          return 'timeline-item-success';
        case 'error':
          return 'timeline-item-error';
        default:
          return 'timeline-item-pending';
      }
    },

    /**
     * Get tool duration
     * @param {Object} tool - Tool data
     * @returns {string|null} Formatted duration
     */
    getToolDuration(tool) {
      if (!tool.duration) return null;
      return `${(tool.duration / 1000).toFixed(2)}s`;
    },

    /**
     * Check if tool is expanded
     * @param {number} index - Tool index
     * @returns {boolean}
     */
    isExpanded(index) {
      return this.expandedTools.has(index);
    },

    /**
     * Toggle tool expansion
     * @param {number} index - Tool index
     */
    toggleTool(index) {
      if (this.expandedTools.has(index)) {
        this.expandedTools.delete(index);
      } else {
        this.expandedTools.add(index);
      }
      // Trigger reactivity
      this.expandedTools = new Set(this.expandedTools);
    },

    /**
     * Expand all tools
     */
    expandAll() {
      this.tools.forEach((_, index) => {
        this.expandedTools.add(index);
      });
      this.expandedTools = new Set(this.expandedTools);
    },

    /**
     * Collapse all tools
     */
    collapseAll() {
      this.expandedTools.clear();
      this.expandedTools = new Set(this.expandedTools);
    },

    /**
     * Toggle show all tools
     */
    toggleShowAll() {
      this.showAll = !this.showAll;
    },

    /**
     * Get tool type for specialized display
     * @param {Object} tool - Tool data
     * @returns {string} Tool type
     */
    getToolType(tool) {
      const name = tool.name ?? tool.tool_name ?? '';
      if (name === 'code_execution') return 'code';
      if (name === 'search_engine') return 'search';
      if (name.startsWith('memory_')) return 'memory';
      if (name === 'browser_agent') return 'browser';
      return 'generic';
    },

    /**
     * Format timestamp
     * @param {string} timestamp - ISO timestamp
     * @returns {string} Formatted time
     */
    formatTime(timestamp) {
      if (!timestamp) return '';
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    },
  };
}
