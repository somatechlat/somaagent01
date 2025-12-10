/**
 * Memory API
 * 
 * API calls for the Memory Dashboard feature.
 * Integrates with SomaBrain memory endpoints.
 * 
 * @module features/memory/memory.api
 */

import { fetchApi } from '../../core/api/client.js';

/**
 * Fetch memories with optional search
 * @param {Object} params - Query parameters
 * @param {string} [params.query] - Search query
 * @param {number} [params.top_k=20] - Number of results
 * @param {string} [params.universe] - Memory universe/namespace
 * @returns {Promise<{memories: Array}>} Memory results
 */
export async function fetchMemories({ query = '', top_k = 20, universe = null } = {}) {
  const payload = {
    query: query || '*',
    top_k,
  };
  
  if (universe) {
    payload.universe = universe;
  }
  
  const response = await fetchApi('/recall', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Failed to fetch memories');
  }
  
  const data = await response.json();
  
  // Normalize response - SomaBrain returns results in different formats
  const memories = data.memory || data.results || data.wm || [];
  
  return {
    memories: memories.map(normalizeMemory),
  };
}

/**
 * Search memories by query
 * @param {string} query - Search query
 * @param {number} [topK=10] - Number of results
 * @returns {Promise<Array>} Search results
 */
export async function searchMemories(query, topK = 10) {
  const { memories } = await fetchMemories({ query, top_k: topK });
  return memories;
}

/**
 * Delete a memory by coordinate
 * @param {Array<number>} coordinate - Memory coordinate vector
 * @returns {Promise<void>}
 */
export async function deleteMemory(coordinate) {
  const response = await fetchApi('/delete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ coordinate }),
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Failed to delete memory');
  }
}

/**
 * Save a new memory
 * @param {Object} memory - Memory to save
 * @param {string} memory.content - Memory content
 * @param {Object} [memory.metadata] - Additional metadata
 * @returns {Promise<{ok: boolean}>}
 */
export async function saveMemory({ content, metadata = {} }) {
  const payload = {
    payload: {
      content,
      ...metadata,
      timestamp: new Date().toISOString(),
    },
  };
  
  const response = await fetchApi('/remember', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Failed to save memory');
  }
  
  return response.json();
}

/**
 * Normalize memory object from API response
 * @param {Object} raw - Raw memory object
 * @returns {Object} Normalized memory
 */
function normalizeMemory(raw) {
  const payload = raw.payload || raw;
  
  return {
    id: payload.id || payload.coordinate?.join(',') || crypto.randomUUID(),
    content: payload.content || payload.text || '',
    type: payload.type || payload.area || 'main',
    score: raw.score ?? 1.0,
    timestamp: payload.timestamp || payload.created_at || new Date().toISOString(),
    metadata: {
      subject: payload.subject || payload.metadata?.subject,
      source: payload.source || payload.metadata?.source,
      ...payload.metadata,
    },
    coordinate: raw.coordinate || payload.coordinate,
  };
}

export default {
  fetchMemories,
  searchMemories,
  deleteMemory,
  saveMemory,
};
