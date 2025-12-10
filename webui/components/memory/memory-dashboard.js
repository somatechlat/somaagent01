/**
 * Memory Dashboard Component
 * 
 * Main memory management interface with search, filters, and detail view.
 * 
 * @module components/memory/memory-dashboard
 */

import { 
  memoryStore, 
  setMemories, 
  setSearchQuery, 
  setTypeFilter, 
  selectMemory,
  setLoading, 
  setError,
  removeMemory,
  getFilteredMemories,
  getSelectedMemory,
} from '../../features/memory/index.js';
import { fetchMemories, deleteMemory } from '../../features/memory/memory.api.js';
import { toastManager } from '../base/toast.js';

/**
 * Memory type options
 */
const MEMORY_TYPES = [
  { value: null, label: 'All Types' },
  { value: 'main', label: 'Main' },
  { value: 'fragments', label: 'Fragments' },
  { value: 'solutions', label: 'Solutions' },
  { value: 'instruments', label: 'Instruments' },
];

/**
 * Memory Dashboard component factory
 * @returns {Object} Alpine component data
 */
export default function MemoryDashboard() {
  return {
    // State from store
    get memories() { return getFilteredMemories(); },
    get selectedMemory() { return getSelectedMemory(); },
    get isLoading() { return memoryStore.isLoading; },
    get error() { return memoryStore.error; },
    get searchQuery() { return memoryStore.searchQuery; },
    get typeFilter() { return memoryStore.filters.type; },
    
    // Local state
    memoryTypes: MEMORY_TYPES,
    isDeleting: false,
    
    async init() {
      await this.loadMemories();
    },
    
    /**
     * Load memories from API
     */
    async loadMemories() {
      setLoading(true);
      setError(null);
      
      try {
        const { memories } = await fetchMemories({
          query: memoryStore.searchQuery || '*',
          top_k: 50,
        });
        setMemories(memories);
      } catch (err) {
        setError(err.message);
        toastManager.error('Failed to load memories', err.message);
      } finally {
        setLoading(false);
      }
    },
    
    /**
     * Handle search input
     * @param {string} query - Search query
     */
    onSearch(query) {
      setSearchQuery(query);
      // Debounce API call
      clearTimeout(this._searchTimeout);
      this._searchTimeout = setTimeout(() => this.loadMemories(), 300);
    },
    
    /**
     * Handle type filter change
     * @param {string|null} type - Memory type
     */
    onTypeFilterChange(type) {
      setTypeFilter(type);
    },
    
    /**
     * Select a memory for detail view
     * @param {Object} memory - Memory to select
     */
    onSelectMemory(memory) {
      selectMemory(memory.id);
    },
    
    /**
     * Close detail panel
     */
    closeDetail() {
      selectMemory(null);
    },
    
    /**
     * Delete a memory
     * @param {Object} memory - Memory to delete
     */
    async onDeleteMemory(memory) {
      if (!confirm('Are you sure you want to delete this memory?')) return;
      
      this.isDeleting = true;
      
      try {
        await deleteMemory(memory.coordinate);
        removeMemory(memory.id);
        
        if (memoryStore.selectedMemoryId === memory.id) {
          selectMemory(null);
        }
        
        toastManager.success('Memory deleted', 'The memory has been removed.');
      } catch (err) {
        toastManager.error('Failed to delete memory', err.message);
      } finally {
        this.isDeleting = false;
      }
    },
    
    /**
     * Format memory timestamp
     * @param {string} timestamp - ISO timestamp
     * @returns {string} Formatted date
     */
    formatDate(timestamp) {
      if (!timestamp) return '';
      return new Date(timestamp).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    },
    
    /**
     * Format relevance score
     * @param {number} score - Score 0-1
     * @returns {string} Formatted percentage
     */
    formatScore(score) {
      if (score == null) return '';
      return `${Math.round(score * 100)}%`;
    },
    
    /**
     * Truncate content for preview
     * @param {string} content - Full content
     * @param {number} maxLength - Max length
     * @returns {string} Truncated content
     */
    truncate(content, maxLength = 150) {
      if (!content || content.length <= maxLength) return content;
      return content.slice(0, maxLength) + '...';
    },
    
    /**
     * Get type badge class
     * @param {string} type - Memory type
     * @returns {string} Badge class
     */
    getTypeBadgeClass(type) {
      const classes = {
        main: 'badge-info',
        fragments: 'badge-warning',
        solutions: 'badge-success',
        instruments: 'badge-accent',
      };
      return classes[type] || '';
    },
    
    /**
     * Bind for search input
     */
    get searchInput() {
      return {
        ':value': () => this.searchQuery,
        '@input': (e) => this.onSearch(e.target.value),
        'placeholder': 'Search memories...',
        'class': 'input',
      };
    },
    
    /**
     * Bind for memory item
     * @param {Object} memory - Memory object
     */
    memoryItem(memory) {
      return {
        '@click': () => this.onSelectMemory(memory),
        ':class': () => ({
          'memory-item': true,
          'memory-item-selected': memoryStore.selectedMemoryId === memory.id,
        }),
      };
    },
  };
}

export { MEMORY_TYPES };
