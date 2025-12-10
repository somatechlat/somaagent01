/**
 * Memory/SomaBrain Settings Card Component
 * 
 * Settings card for memory and SomaBrain configuration.
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
    recallTopK: options.config?.recall_top_k ?? 5,
    recallThreshold: options.config?.recall_threshold ?? 0.7,
    
    // Memorization settings
    autoMemorize: options.config?.auto_memorize ?? true,
    memorizeThreshold: options.config?.memorize_threshold ?? 0.8,
    
    // Search settings
    searchLimit: options.config?.search_limit ?? 20,
    
    // UI state
    expanded: false,
    
    /**
     * Handle recall enabled change
     * @param {boolean} value - New value
     */
    onRecallEnabledChange(value) {
      this.recallEnabled = value;
      this.emitChange();
    },
    
    /**
     * Handle recall top_k change
     * @param {number} value - New value
     */
    onRecallTopKChange(value) {
      this.recallTopK = parseInt(value, 10);
      this.emitChange();
    },
    
    /**
     * Handle recall threshold change
     * @param {number} value - New value
     */
    onRecallThresholdChange(value) {
      this.recallThreshold = parseFloat(value);
      this.emitChange();
    },
    
    /**
     * Handle auto memorize change
     * @param {boolean} value - New value
     */
    onAutoMemorizeChange(value) {
      this.autoMemorize = value;
      this.emitChange();
    },
    
    /**
     * Handle memorize threshold change
     * @param {number} value - New value
     */
    onMemorizeThresholdChange(value) {
      this.memorizeThreshold = parseFloat(value);
      this.emitChange();
    },
    
    /**
     * Handle search limit change
     * @param {number} value - New value
     */
    onSearchLimitChange(value) {
      this.searchLimit = parseInt(value, 10);
      this.emitChange();
    },
    
    /**
     * Emit change to parent
     */
    emitChange() {
      const config = {
        recall_enabled: this.recallEnabled,
        recall_top_k: this.recallTopK,
        recall_threshold: this.recallThreshold,
        auto_memorize: this.autoMemorize,
        memorize_threshold: this.memorizeThreshold,
        search_limit: this.searchLimit,
      };
      options.onChange?.(config);
    },
    
    /**
     * Format threshold as percentage
     * @param {number} value - Threshold value
     * @returns {string} Formatted percentage
     */
    formatThreshold(value) {
      return `${Math.round(value * 100)}%`;
    },
    
    /**
     * Toggle expanded state
     */
    toggle() {
      this.expanded = !this.expanded;
    },
  };
}
