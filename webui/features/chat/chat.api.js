/**
 * Chat API
 * 
 * API calls for the Chat feature.
 * All backend communication for chat goes through this module.
 * 
 * @module features/chat/chat.api
 */

import { fetchApi, callJsonApi } from '../../core/api/client.js';
import { ENDPOINTS, buildUrl } from '../../core/api/endpoints.js';

/**
 * Send a chat message
 * @param {Object} params - Message parameters
 * @param {string} params.message - Message content
 * @param {string} [params.sessionId] - Session ID (optional for new sessions)
 * @param {string[]} [params.attachments] - Attachment IDs
 * @returns {Promise<{session_id: string}>} Response with session ID
 */
export async function sendMessage({ message, sessionId, attachments = [] }) {
  const payload = {
    message,
    attachments,
  };
  
  if (sessionId) {
    payload.session_id = sessionId;
  }
  
  const response = await fetchApi(buildUrl(ENDPOINTS.SESSION_MESSAGE), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Failed to send message');
  }
  
  return response.json();
}

/**
 * Fetch all sessions
 * @returns {Promise<Array>} Array of session objects
 */
export async function fetchSessions() {
  const response = await fetchApi(buildUrl(ENDPOINTS.SESSIONS));
  
  if (!response.ok) {
    throw new Error(`Failed to fetch sessions: ${response.status}`);
  }
  
  return response.json();
}

/**
 * Fetch session history
 * @param {string} sessionId - Session ID
 * @returns {Promise<{events: Array}>} Session history
 */
export async function fetchSessionHistory(sessionId) {
  const response = await fetchApi(buildUrl(ENDPOINTS.SESSION_HISTORY, sessionId));
  
  if (!response.ok) {
    throw new Error(`Failed to fetch session history: ${response.status}`);
  }
  
  return response.json();
}

/**
 * Create a new session
 * @returns {Promise<{session_id: string}>} New session info
 */
export async function createSession() {
  // Creating a session is implicit when sending the first message
  // This function is for explicit session creation if needed
  const response = await fetchApi(buildUrl(ENDPOINTS.SESSIONS), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({}),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to create session: ${response.status}`);
  }
  
  return response.json();
}

/**
 * Delete a session
 * @param {string} sessionId - Session ID to delete
 * @returns {Promise<void>}
 */
export async function deleteSession(sessionId) {
  return callJsonApi('/chat_remove', { context: sessionId });
}

/**
 * Reset a session (clear messages but keep session)
 * @param {string} sessionId - Session ID to reset
 * @returns {Promise<void>}
 */
export async function resetSession(sessionId) {
  return callJsonApi('/chat_reset', { context: sessionId });
}

/**
 * Pause/unpause the agent
 * @param {boolean} paused - Whether to pause
 * @param {string} sessionId - Session ID
 * @returns {Promise<void>}
 */
export async function pauseAgent(paused, sessionId) {
  return callJsonApi('/pause', { paused, context: sessionId });
}

/**
 * Load saved chats
 * @returns {Promise<Array>} Array of saved chat objects
 */
export async function loadSavedChats() {
  const response = await fetchApi('/load_chats');
  
  if (!response.ok) {
    throw new Error(`Failed to load chats: ${response.status}`);
  }
  
  return response.json();
}

/**
 * Save current chat
 * @param {string} sessionId - Session ID to save
 * @returns {Promise<void>}
 */
export async function saveChat(sessionId) {
  return callJsonApi('/save_chat', { context: sessionId });
}

/**
 * Import knowledge files
 * @param {FileList} files - Files to import
 * @param {string} sessionId - Session ID
 * @returns {Promise<{filenames: string[]}>} Imported file names
 */
export async function importKnowledge(files, sessionId) {
  const formData = new FormData();
  
  for (const file of files) {
    formData.append('files[]', file);
  }
  
  formData.append('ctxid', sessionId);
  
  const response = await fetchApi('/import_knowledge', {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Failed to import knowledge');
  }
  
  return response.json();
}

export default {
  sendMessage,
  fetchSessions,
  fetchSessionHistory,
  createSession,
  deleteSession,
  resetSession,
  pauseAgent,
  loadSavedChats,
  saveChat,
  importKnowledge,
};
