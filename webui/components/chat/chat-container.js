/**
 * Chat Container Component
 * 
 * Main chat interface container with message list and input.
 * 
 * @module components/chat/chat-container
 */

import { chatStore, setSession, setAutoScroll, setInputText, setSending } from '../../features/chat/chat.store.js';
import { sendMessage, fetchSessionHistory } from '../../features/chat/chat.api.js';
import { sseManager } from '../../core/sse/manager.js';
import { processSSEEvent } from '../../features/chat/index.js';
import { toastManager } from '../base/toast.js';

/**
 * Chat Container component factory
 * @param {Object} options - Container options
 * @param {string} [options.sessionId] - Initial session ID
 * @returns {Object} Alpine component data
 */
export default function ChatContainer(options = {}) {
  return {
    // State from store
    get sessionId() { return chatStore.sessionId; },
    get messages() { return chatStore.messages; },
    get isLoading() { return chatStore.isLoading; },
    get isSending() { return chatStore.isSending; },
    get autoScroll() { return chatStore.autoScroll; },
    get inputText() { return chatStore.inputText; },
    get connectionStatus() { return chatStore.connectionStatus; },
    get error() { return chatStore.error; },
    
    // Local state
    messageListRef: null,
    
    async init() {
      // Set initial session if provided
      if (options.sessionId) {
        await this.loadSession(options.sessionId);
      }
      
      // Watch for new messages to auto-scroll
      this.$watch('messages', () => {
        if (this.autoScroll) {
          this.$nextTick(() => this.scrollToBottom());
        }
      });
    },
    
    /**
     * Load a session and connect to SSE
     * @param {string} sessionId - Session ID
     */
    async loadSession(sessionId) {
      setSession(sessionId);
      
      // Load history
      try {
        await fetchSessionHistory(sessionId);
      } catch (err) {
        toastManager.error('Failed to load history', err.message);
      }
      
      // Connect to SSE
      sseManager.connect(sessionId, {
        onMessage: (event) => processSSEEvent(event.data),
        onConnect: () => chatStore.connectionStatus = 'online',
        onDisconnect: () => chatStore.connectionStatus = 'offline',
        onReconnecting: () => chatStore.connectionStatus = 'reconnecting',
      });
    },
    
    /**
     * Send a message
     */
    async send() {
      const text = chatStore.inputText.trim();
      if (!text || chatStore.isSending) return;
      
      setInputText('');
      setSending(true);
      
      try {
        await sendMessage({ 
          message: text, 
          sessionId: this.sessionId 
        });
      } catch (err) {
        toastManager.error('Failed to send message', err.message);
        setInputText(text); // Restore input on error
      } finally {
        setSending(false);
      }
    },
    
    /**
     * Handle input change
     * @param {string} value - New input value
     */
    onInputChange(value) {
      setInputText(value);
    },
    
    /**
     * Handle key press in input
     * @param {KeyboardEvent} e - Keyboard event
     */
    onKeyPress(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.send();
      }
    },
    
    /**
     * Scroll to bottom of message list
     */
    scrollToBottom() {
      if (this.messageListRef) {
        this.messageListRef.scrollTop = this.messageListRef.scrollHeight;
      }
    },
    
    /**
     * Toggle auto-scroll
     */
    toggleAutoScroll() {
      setAutoScroll(!this.autoScroll);
    },
    
    /**
     * Handle scroll event
     * @param {Event} e - Scroll event
     */
    onScroll(e) {
      const el = e.target;
      const isAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50;
      
      // Auto-enable auto-scroll when user scrolls to bottom
      if (isAtBottom && !this.autoScroll) {
        setAutoScroll(true);
      }
      // Disable auto-scroll when user scrolls up
      else if (!isAtBottom && this.autoScroll) {
        setAutoScroll(false);
      }
    },
    
    /**
     * Check if currently streaming
     */
    get isStreaming() {
      return chatStore.currentAssistantId !== null;
    },
    
    /**
     * Bind for message list container
     */
    get messageListBind() {
      return {
        'x-ref': 'messageList',
        '@scroll': (e) => this.onScroll(e),
        'class': 'main-content',
      };
    },
  };
}
