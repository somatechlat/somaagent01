/**
 * Memory Card Component
 *
 * Settings card for Memory/SomaBrain configuration.
 *
 * @module components/settings/memory-card
 */

/**
 * Memory Card component factory
 * @param {Object} options - Card options
 * @param {Object} options.config - Current configuration
 * @param {Function} options.onChange - Change handler
 * @returns {Object} Alpine component data
 */
export default function MemoryCard(options = {}) {
  return {
    // Recall settings
    recallEnabled: options.config?.recall_enabled ?? true,
    recallDelayed: options.config?.recall_delayed ?? false,
    recallInterval: options.config?.recall_interval ?? 5,

    // Search limits
    memoriesMax: options.config?.memories_max ?? 10,
    solutionsMax: options.config?.solutions_max ?? 5,

    // Similarity threshold
    similarityThreshold: options.config?.similarity_threshold ?? 0.7,

    // Memorization settings
    memorizationEnabled: options.config?.memorization_enabled ?? true,
    consolidationEnabled: options.config?.consolidation_enabled ?? true,

    // Knowledge settings
    knowledgeSubdirectory: options.config?.knowledge_subdirectory ?? 'default',
    knowledgeDirectories: options.config?.knowledge_directories ?? [
      'default',
      'custom',
      'shared',
    ],

    /**
     * Get title
     */
    get title() {
      return 'Memory / SomaBrain';
    },

    /**
     * Get icon
     */
    get icon() {
      return '🧠';
    },

    /**
     * Get description
     */
    get description() {
      return 'Configure memory recall, search limits, and memorization settings';
    },


    /**
     * Handle recall enabled change
     * @param {boolean} value - New value
     */
    onRecallEnabledChange(value) {
      this.recallEnabled = value;
      this.emitChange();
    },

    /**
     * Handle recall delayed change
     * @param {boolean} value - New value
     */
    onRecallDelayedChange(value) {
      this.recallDelayed = value;
      this.emitChange();
    },

    /**
     * Handle recall interval change
     * @param {number} value - New value
     */
    onRecallIntervalChange(value) {
      this.recallInterval = parseInt(value, 10);
      this.emitChange();
    },

    /**
     * Handle memories max change
     * @param {number} value - New value
     */
    onMemoriesMaxChange(value) {
      this.memoriesMax = parseInt(value, 10);
      this.emitChange();
    },

    /**
     * Handle solutions max change
     * @param {number} value - New value
     */
    onSolutionsMaxChange(value) {
      this.solutionsMax = parseInt(value, 10);
      this.emitChange();
    },

    /**
     * Handle similarity threshold change
     * @param {number} value - New value
     */
    onSimilarityThresholdChange(value) {
      this.similarityThreshold = parseFloat(value);
      this.emitChange();
    },

    /**
     * Handle memorization enabled change
     * @param {boolean} value - New value
     */
    onMemorizationEnabledChange(value) {
      this.memorizationEnabled = value;
      this.emitChange();
    },

    /**
     * Handle consolidation enabled change
     * @param {boolean} value - New value
     */
    onConsolidationEnabledChange(value) {
      this.consolidationEnabled = value;
      this.emitChange();
    },

    /**
     * Handle knowledge subdirectory change
     * @param {string} value - New value
     */
    onKnowledgeSubdirectoryChange(value) {
      this.knowledgeSubdirectory = value;
      this.emitChange();
    },

    /**
     * Emit change to parent
     */
    emitChange() {
      const config = {
        recall_enabled: this.recallEnabled,
        recall_delayed: this.recallDelayed,
        recall_interval: this.recallInterval,
        memories_max: this.memoriesMax,
        solutions_max: this.solutionsMax,
        similarity_threshold: this.similarityThreshold,
        memorization_enabled: this.memorizationEnabled,
        consolidation_enabled: this.consolidationEnabled,
        knowledge_subdirectory: this.knowledgeSubdirectory,
      };
      options.onChange?.('memory', config);
    },

    /**
     * Reset to defaults
     */
    resetDefaults() {
      this.recallEnabled = true;
      this.recallDelayed = false;
      this.recallInterval = 5;
      this.memoriesMax = 10;
      this.solutionsMax = 5;
      this.similarityThreshold = 0.7;
      this.memorizationEnabled = true;
      this.consolidationEnabled = true;
      this.knowledgeSubdirectory = 'default';
      this.emitChange();
    },

    /**
     * Get summary text for collapsed state
     */
    get summary() {
      const parts = [];
      if (this.recallEnabled) {
        parts.push(`Recall: ${this.memoriesMax} memories`);
      } else {
        parts.push('Recall: Off');
      }
      if (this.memorizationEnabled) {
        parts.push('Memorization: On');
      }
      return parts.join(' • ');
    },
  };
}
