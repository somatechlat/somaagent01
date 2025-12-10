/**
 * Memory Feature Module
 * 
 * Public API for the Memory Dashboard feature.
 * Re-exports store and API functions.
 * 
 * @module features/memory
 */

import * as store from './memory.store.js';
import * as api from './memory.api.js';

// Re-export store functions
export const {
  memoryStore,
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
} = store;

// Re-export API functions
export const {
  fetchMemories,
  searchMemories,
  deleteMemory,
  saveMemory,
} = api;

export default {
  store,
  api,
};
