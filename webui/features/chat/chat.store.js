/**
 * Chat Store
 * 
 * Centralized state management for the Chat feature.
 * Handles messages, sessions, and chat UI state.
 * 
 * @module features/chat/chat.store
 */

import { createStore, subscribe } from '../../core/state/store.js';

/**
 * Initial chat state
 */
const initialState = {
  // Current session
  sessionId: null,
  
  // Messages in current session
  messages: [],
  
  // Available sessions/contexts
  sessions: [],
  
  // UI state
  isLoading: false,
  isSending: false,
  autoScroll: true,
  
  // Input state
  inputText: '',
  
  // Connection state
  connectionStatus: 'unknown', // 'online' | 'offline' | 'stale' | 'reconnecting' | 'unknown'
  
  // Assistant streaming state
  currentAssistantId: null,
  assistantBuffer: '',
  
  // Error state
  error: null,
};

/**
 * Chat store instance
 */
export const chatStore = createStore('chat', initialState, {
  persist: true,
  persistKeys: ['sessionId', 'autoScroll'],
});

/**
 * Set the current session ID
 * @param {string} sessionId - Session identifier
 */
export function setSession(sessionId) {
  chatStore.sessionId = sessionId;
  chatStore.messages = [];
  chatStore.currentAssistantId = null;
  chatStore.assistantBuffer = '';
}

/**
 * Add a message to the chat
 * @param {Object} message - Message object
 * @param {string} message.id - Unique message ID
 * @param {string} message.type - Message type ('user' | 'response' | 'tool' | 'agent' | 'error')
 * @param {string} message.content - Message content
 * @param {Object} [message.metadata] - Additional metadata
 * @param {boolean} [message.isTemp] - Whether this is a temporary/streaming message
 */
export function addMessage(message) {
  const existingIndex = chatStore.messages.findIndex(m => m.id === message.id);
  
  if (existingIndex >= 0) {
    // Update existing message
    chatStore.messages[existingIndex] = { ...chatStore.messages[existingIndex], ...message };
  } else {
    // Add new message
    chatStore.messages = [...chatStore.messages, message];
  }
}

/**
 * Update an existing message
 * @param {string} messageId - Message ID to update
 * @param {Object} updates - Properties to update
 */
export function updateMessage(messageId, updates) {
  const index = chatStore.messages.findIndex(m => m.id === messageId);
  if (index >= 0) {
    chatStore.messages[index] = { ...chatStore.messages[index], ...updates };
    chatStore.messages = [...chatStore.messages]; // Trigger reactivity
  }
}

/**
 * Clear all messages
 */
export function clearMessages() {
  chatStore.messages = [];
  chatStore.currentAssistantId = null;
  chatStore.assistantBuffer = '';
}

/**
 * Set available sessions
 * @param {Array} sessions - Array of session objects
 */
export function setSessions(sessions) {
  chatStore.sessions = sessions || [];
}

/**
 * Add a new session
 * @param {Object} session - Session object
 */
export function addSession(session) {
  chatStore.sessions = [session, ...chatStore.sessions];
}

/**
 * Remove a session
 * @param {string} sessionId - Session ID to remove
 */
export function removeSession(sessionId) {
  chatStore.sessions = chatStore.sessions.filter(s => s.id !== sessionId);
}

/**
 * Set connection status
 * @param {string} status - Connection status
 */
export function setConnectionStatus(status) {
  chatStore.connectionStatus = status;
}

/**
 * Set loading state
 * @param {boolean} loading - Loading state
 */
export function setLoading(loading) {
  chatStore.isLoading = loading;
}

/**
 * Set sending state
 * @param {boolean} sending - Sending state
 */
export function setSending(sending) {
  chatStore.isSending = sending;
}

/**
 * Set auto-scroll state
 * @param {boolean} autoScroll - Auto-scroll state
 */
export function setAutoScroll(autoScroll) {
  chatStore.autoScroll = autoScroll;
}

/**
 * Set input text
 * @param {string} text - Input text
 */
export function setInputText(text) {
  chatStore.inputText = text;
}

/**
 * Set error state
 * @param {string|null} error - Error message or null
 */
export function setError(error) {
  chatStore.error = error;
}

/**
 * Start streaming assistant response
 * @param {string} assistantId - Assistant message ID
 */
export function startAssistantStream(assistantId) {
  chatStore.currentAssistantId = assistantId;
  chatStore.assistantBuffer = '';
}

/**
 * Append to assistant stream buffer
 * @param {string} content - Content to append
 */
export function appendAssistantBuffer(content) {
  chatStore.assistantBuffer += content;
}

/**
 * End assistant stream
 */
export function endAssistantStream() {
  chatStore.currentAssistantId = null;
  chatStore.assistantBuffer = '';
}

/**
 * Get current assistant buffer
 * @returns {string} Current buffer content
 */
export function getAssistantBuffer() {
  return chatStore.assistantBuffer;
}

/**
 * Subscribe to chat changes
 * @param {Function} callback - Callback function
 * @returns {Function} Unsubscribe function
 */
export function onChatChange(callback) {
  return subscribe('chat', callback);
}

export default {
  store: chatStore,
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
};
