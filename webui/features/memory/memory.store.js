/**
 * Memory Store
 * 
 * Centralized state management for the Memory Dashboard feature.
 * Handles memory items, search, and filters.
 * 
 * @module features/memory/memory.store
 */

import { createStore, subscribe } from '../../core/state/store.js';

/**
 * Initial memory state
 */
const initialState = {
  // Memory items
  memories: [],
  
  // Search and filter state
  searchQuery: '',
  filters: {
    type: null, // 'main' | 'fragments' | 'solutions' | 'instruments' | null (all)
    dateRange: null, // { start: Date, end: Date } | null
  },
  
  // Selected memory for detail view
  selectedMemoryId: null,
  
  // UI state
  isLoading: false,
  error: null,
  
  // Pagination
  page: 1,
  pageSize: 20,
  totalCount: 0,
};

/**
 * Memory store instance
 */
export const memoryStore = createStore('memory', initialState, {
  persist: true,
  persistKeys: ['filters', 'pageSize'],
});

/**
 * Set memories
 * @param {Array} memories - Memory items
 */
export function setMemories(memories) {
  memoryStore.memories = memories || [];
}

/**
 * Add a memory item
 * @param {Object} memory - Memory item
 */
export function addMemory(memory) {
  memoryStore.memories = [memory, ...memoryStore.memories];
}

/**
 * Remove a memory item
 * @param {string} memoryId - Memory ID
 */
export function removeMemory(memoryId) {
  memoryStore.memories = memoryStore.memories.filter(m => m.id !== memoryId);
}

/**
 * Set search query
 * @param {string} query - Search query
 */
export function setSearchQuery(query) {
  memoryStore.searchQuery = query;
  memoryStore.page = 1; // Reset to first page on search
}

/**
 * Set type filter
 * @param {string|null} type - Memory type filter
 */
export function setTypeFilter(type) {
  memoryStore.filters = { ...memoryStore.filters, type };
  memoryStore.page = 1;
}

/**
 * Set date range filter
 * @param {Object|null} dateRange - Date range { start, end }
 */
export function setDateRangeFilter(dateRange) {
  memoryStore.filters = { ...memoryStore.filters, dateRange };
  memoryStore.page = 1;
}

/**
 * Clear all filters
 */
export function clearFilters() {
  memoryStore.filters = { type: null, dateRange: null };
  memoryStore.searchQuery = '';
  memoryStore.page = 1;
}

/**
 * Select a memory for detail view
 * @param {string|null} memoryId - Memory ID or null to deselect
 */
export function selectMemory(memoryId) {
  memoryStore.selectedMemoryId = memoryId;
}

/**
 * Set loading state
 * @param {boolean} loading - Loading state
 */
export function setLoading(loading) {
  memoryStore.isLoading = loading;
}

/**
 * Set error state
 * @param {string|null} error - Error message
 */
export function setError(error) {
  memoryStore.error = error;
}

/**
 * Set page
 * @param {number} page - Page number
 */
export function setPage(page) {
  memoryStore.page = page;
}

/**
 * Set total count
 * @param {number} count - Total count
 */
export function setTotalCount(count) {
  memoryStore.totalCount = count;
}

/**
 * Get selected memory
 * @returns {Object|null} Selected memory or null
 */
export function getSelectedMemory() {
  if (!memoryStore.selectedMemoryId) return null;
  return memoryStore.memories.find(m => m.id === memoryStore.selectedMemoryId) || null;
}

/**
 * Get filtered memories
 * @returns {Array} Filtered memory items
 */
export function getFilteredMemories() {
  let result = [...memoryStore.memories];
  
  // Filter by type
  if (memoryStore.filters.type) {
    result = result.filter(m => m.type === memoryStore.filters.type);
  }
  
  // Filter by date range
  if (memoryStore.filters.dateRange) {
    const { start, end } = memoryStore.filters.dateRange;
    result = result.filter(m => {
      const date = new Date(m.timestamp);
      return date >= start && date <= end;
    });
  }
  
  // Filter by search query
  if (memoryStore.searchQuery) {
    const q = memoryStore.searchQuery.toLowerCase();
    result = result.filter(m => 
      m.content?.toLowerCase().includes(q) ||
      m.metadata?.subject?.toLowerCase().includes(q)
    );
  }
  
  return result;
}

/**
 * Subscribe to memory changes
 * @param {Function} callback - Callback function
 * @returns {Function} Unsubscribe function
 */
export function onMemoryChange(callback) {
  return subscribe('memory', callback);
}

export default {
  store: memoryStore,
  setMemories,
  addMemory,
  removeMemory,
  setSearchQuery,
  setTypeFilter,
  setDateRangeFilter,
  clearFilters,
  selectMemory,
  setLoading,
  setError,
  setPage,
  setTotalCount,
  getSelectedMemory,
  getFilteredMemories,
  onMemoryChange,
};
