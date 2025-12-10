/**
 * Assistant Message Component
 * 
 * Displays an assistant message with streaming support and markdown rendering.
 * 
 * @module components/chat/assistant-message
 */

/**
 * Assistant Message component factory
 * @param {Object} options - Message options
 * @param {Object} options.message - Message object
 * @param {boolean} [options.isStreaming=false] - Whether message is streaming
 * @returns {Object} Alpine component data
 */
export default function AssistantMessage(options = {}) {
  return {
    message: options.message ?? {},
    isStreaming: options.isStreaming ?? false,
    
    /**
     * Get message content
     */
    get content() {
      return this.message.content ?? '';
    },
    
    /**
     * Get formatted timestamp
     */
    get timestamp() {
      if (!this.message.timestamp) return '';
      
      const date = new Date(this.message.timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    },
    
    /**
     * Check if message is temporary (streaming)
     */
    get isTemp() {
      return this.message.isTemp ?? false;
    },
    
    /**
     * Check if message is complete
     */
    get isComplete() {
      return this.message.metadata?.finished ?? !this.isTemp;
    },
    
    /**
     * Check if message has thinking content
     */
    get hasThinking() {
      return this.message.metadata?.thinking?.length > 0;
    },
    
    /**
     * Get thinking content
     */
    get thinking() {
      return this.message.metadata?.thinking ?? '';
    },
    
    /**
     * Check if message has tool calls
     */
    get hasToolCalls() {
      return this.message.metadata?.tool_calls?.length > 0;
    },
    
    /**
     * Get tool calls
     */
    get toolCalls() {
      return this.message.metadata?.tool_calls ?? [];
    },
    
    /**
     * Bind for streaming cursor
     */
    get cursor() {
      return {
        'x-show': () => this.isStreaming && !this.isComplete,
        'class': 'streaming-cursor',
      };
    },
    
    /**
     * Bind for thinking indicator
     */
    get thinkingIndicator() {
      return {
        'x-show': () => this.isStreaming && !this.content,
        'class': 'thinking-indicator',
      };
    },
  };
}
