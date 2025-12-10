/**
 * Chat Feature Module
 * 
 * Public API for the Chat feature.
 * Re-exports store and API functions.
 * 
 * @module features/chat
 */

import * as store from './chat.store.js';
import * as api from './chat.api.js';

// Re-export store functions
export const {
  chatStore,
  setSession,
  addMessage,
  updateMessage,
  clearMessages,
  setSessions,
  addSession,
  removeSession,
  setConnectionStatus,
  setLoading,
  setSending,
  setAutoScroll,
  setInputText,
  setError,
  startAssistantStream,
  appendAssistantBuffer,
  endAssistantStream,
  getAssistantBuffer,
  onChatChange,
} = store;

// Re-export API functions
export const {
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
} = api;

/**
 * Generate a unique message ID
 * @returns {string} UUID v4
 */
export function generateMessageId() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Generate a short session ID
 * @returns {string} 8-character alphanumeric ID
 */
export function generateShortId() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < 8; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

/**
 * Map SSE event type to UI message type
 * @param {Object} event - SSE event object
 * @returns {string} UI message type
 */
export function mapEventToUiType(event) {
  const type = (event.type || '').toLowerCase();
  const role = (event.role || '').toLowerCase();
  
  if (type === 'assistant.delta' || type === 'assistant.final' || role === 'assistant') {
    return 'response';
  }
  if (role === 'user') {
    return 'user';
  }
  if (role === 'tool' || type.startsWith('tool')) {
    return 'tool';
  }
  if (type.endsWith('.error')) {
    return 'error';
  }
  return 'agent';
}

/**
 * Process an SSE event and update the chat store
 * @param {Object} event - SSE event object
 */
export function processSSEEvent(event) {
  const uiType = mapEventToUiType(event);
  
  // Skip keepalive events
  if (event.type === 'system.keepalive') {
    return;
  }
  
  if (uiType === 'response') {
    const eventType = (event.type || '').toLowerCase();
    
    if (eventType === 'assistant.delta') {
      // Streaming delta
      if (!chatStore.currentAssistantId) {
        const id = generateMessageId();
        startAssistantStream(id);
        addMessage({
          id,
          type: 'response',
          content: '',
          isTemp: true,
          metadata: event.metadata || null,
        });
      }
      
      appendAssistantBuffer(event.message || '');
      updateMessage(chatStore.currentAssistantId, {
        content: getAssistantBuffer(),
      });
    } else {
      // Final message
      const id = chatStore.currentAssistantId || generateMessageId();
      const content = getAssistantBuffer() + (event.message || '');
      
      updateMessage(id, {
        content,
        isTemp: false,
        metadata: { ...event.metadata, finished: true },
      });
      
      endAssistantStream();
    }
  } else {
    // Non-response messages
    const id = event.event_id || generateMessageId();
    const heading = event.metadata?.subject || event.metadata?.tool_name || null;
    const content = event.message || (event.metadata ? JSON.stringify(event.metadata, null, 2) : '');
    
    addMessage({
      id,
      type: uiType,
      heading,
      content,
      isTemp: false,
      metadata: event.metadata || null,
    });
  }
}

export default {
  store,
  api,
  generateMessageId,
  generateShortId,
  mapEventToUiType,
  processSSEEvent,
};
