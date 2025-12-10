/**
 * Memory Tool Display Component
 *
 * Specialized display for memory tool results.
 * Shows operation type and affected items.
 *
 * @module components/chat/memory-tool-display
 * Requirements: 5.7
 */

/**
 * Memory operation icons
 */
const MEMORY_ICONS = {
  memory_save: '💾',
  memory_load: '📖',
  memory_delete: '🗑️',
  memory_forget: '🧹',
  remember: '💾',
  recall: '📖',
  delete: '🗑️',
  forget: '🧹',
  default: '🧠',
};

/**
 * Memory operation display names
 */
const OPERATION_NAMES = {
  memory_save: 'Save Memory',
  memory_load: 'Load Memory',
  memory_delete: 'Delete Memory',
  memory_forget: 'Forget Memories',
  remember: 'Remember',
  recall: 'Recall',
  delete: 'Delete',
  forget: 'Forget',
};

/**
 * Memory Tool Display component factory
 * @param {Object} options - Component options
 * @param {Object} options.memory - Memory operation data
 * @returns {Object} Alpine component data
 */
export default function MemoryToolDisplay(options = {}) {
  return {
    memory: options.memory ?? {},

    // UI state
    showInput: true,
    showOutput: true,
    expandedItem: null,

    /**
     * Get operation type
     */
    get operation() {
      return this.memory.name ?? this.memory.operation ?? 'memory_load';
    },

    /**
     * Get operation icon
     */
    get operationIcon() {
      return MEMORY_ICONS[this.operation] ?? MEMORY_ICONS.default;
    },

    /**
     * Get operation display name
     */
    get operationName() {
      return OPERATION_NAMES[this.operation] ?? this.operation;
    },

    /**
     * Check if this is a save operation
     */
    get isSaveOperation() {
      return ['memory_save', 'remember'].includes(this.operation);
    },

    /**
     * Check if this is a load/recall operation
     */
    get isLoadOperation() {
      return ['memory_load', 'recall'].includes(this.operation);
    },

    /**
     * Check if this is a delete operation
     */
    get isDeleteOperation() {
      return ['memory_delete', 'delete'].includes(this.operation);
    },

    /**
     * Check if this is a forget operation
     */
    get isForgetOperation() {
      return ['memory_forget', 'forget'].includes(this.operation);
    },

    /**
     * Get input data
     */
    get input() {
      return this.memory.input ?? this.memory.arguments ?? {};
    },

    /**
     * Get query/content being operated on
     */
    get query() {
      return this.input.query ?? this.input.text ?? this.input.content ?? '';
    },

    /**
     * Get memory area
     */
    get area() {
      return this.input.area ?? this.input.memory_area ?? 'main';
    },

    /**
     * Get output/result
     */
    get output() {
      return this.memory.output ?? this.memory.result ?? {};
    },

    /**
     * Get affected items (memories returned or affected)
     */
    get items() {
      const out = this.output;
      if (Array.isArray(out)) return out;
      if (out.memories) return out.memories;
      if (out.results) return out.results;
      if (out.items) return out.items;
      return [];
    },

    /**
     * Get items count
     */
    get itemsCount() {
      return this.items.length;
    },

    /**
     * Get summary text based on operation
     */
    get summary() {
      if (this.isSaveOperation) {
        return this.output.success ? 'Memory saved successfully' : 'Failed to save memory';
      }
      if (this.isLoadOperation) {
        const count = this.itemsCount;
        if (count === 0) return 'No memories found';
        if (count === 1) return '1 memory recalled';
        return `${count} memories recalled`;
      }
      if (this.isDeleteOperation) {
        return this.output.success ? 'Memory deleted' : 'Failed to delete memory';
      }
      if (this.isForgetOperation) {
        const count = this.output.deleted_count ?? this.itemsCount;
        if (count === 0) return 'No memories forgotten';
        if (count === 1) return '1 memory forgotten';
        return `${count} memories forgotten`;
      }
      return '';
    },

    /**
     * Check if operation is still running
     */
    get isRunning() {
      return this.memory.status === 'running';
    },

    /**
     * Check if operation completed successfully
     */
    get isSuccess() {
      return this.memory.status === 'success';
    },

    /**
     * Check if operation failed
     */
    get isError() {
      return this.memory.status === 'error';
    },

    /**
     * Get error message if any
     */
    get errorMessage() {
      return this.memory.error ?? this.output?.error ?? null;
    },

    /**
     * Get duration
     */
    get duration() {
      if (!this.memory.duration) return null;
      return `${(this.memory.duration / 1000).toFixed(2)}s`;
    },

    /**
     * Toggle input section visibility
     */
    toggleInput() {
      this.showInput = !this.showInput;
    },

    /**
     * Toggle output section visibility
     */
    toggleOutput() {
      this.showOutput = !this.showOutput;
    },

    /**
     * Toggle individual item expansion
     * @param {number} index - Item index
     */
    toggleItem(index) {
      this.expandedItem = this.expandedItem === index ? null : index;
    },

    /**
     * Check if item is expanded
     * @param {number} index - Item index
     * @returns {boolean}
     */
    isItemExpanded(index) {
      return this.expandedItem === index;
    },

    /**
     * Format memory item for display
     * @param {Object} item - Memory item
     * @returns {Object} Formatted item
     */
    formatItem(item) {
      return {
        content: item.content ?? item.text ?? item.payload?.content ?? '',
        score: item.score ?? item.relevance ?? item.similarity ?? null,
        timestamp: item.timestamp ?? item.created_at ?? item.payload?.timestamp ?? null,
        area: item.area ?? item.memory_area ?? item.payload?.area ?? 'main',
        metadata: item.metadata ?? item.payload ?? {},
      };
    },

    /**
     * Format relevance score as percentage
     * @param {number} score - Score between 0 and 1
     * @returns {string} Formatted percentage
     */
    formatScore(score) {
      if (score === null || score === undefined) return '';
      return `${Math.round(score * 100)}%`;
    },

    /**
     * Truncate text for preview
     * @param {string} text - Full text
     * @param {number} maxLength - Maximum length
     * @returns {string} Truncated text
     */
    truncate(text, maxLength = 150) {
      if (!text || text.length <= maxLength) return text;
      return text.substring(0, maxLength) + '...';
    },
  };
}

export { MEMORY_ICONS, OPERATION_NAMES };
