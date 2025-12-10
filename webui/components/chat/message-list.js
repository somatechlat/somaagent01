/**
 * Message List Component
 * 
 * Virtualized message list with smooth scrolling.
 * 
 * @module components/chat/message-list
 */

/**
 * Message List component factory
 * @param {Object} options - List options
 * @param {Array} options.messages - Messages array
 * @param {boolean} [options.virtualize=false] - Enable virtualization for large lists
 * @param {number} [options.itemHeight=80] - Estimated item height for virtualization
 * @returns {Object} Alpine component data
 */
export default function MessageList(options = {}) {
  return {
    messages: options.messages ?? [],
    virtualize: options.virtualize ?? false,
    itemHeight: options.itemHeight ?? 80,
    
    // Virtualization state
    scrollTop: 0,
    containerHeight: 0,
    
    init() {
      // Set up resize observer for container
      if (this.virtualize) {
        const observer = new ResizeObserver((entries) => {
          this.containerHeight = entries[0].contentRect.height;
        });
        observer.observe(this.$el);
      }
    },
    
    /**
     * Get visible messages for virtualization
     */
    get visibleMessages() {
      if (!this.virtualize || this.messages.length < 100) {
        return this.messages.map((msg, i) => ({ ...msg, index: i }));
      }
      
      const startIndex = Math.max(0, Math.floor(this.scrollTop / this.itemHeight) - 5);
      const endIndex = Math.min(
        this.messages.length,
        Math.ceil((this.scrollTop + this.containerHeight) / this.itemHeight) + 5
      );
      
      return this.messages.slice(startIndex, endIndex).map((msg, i) => ({
        ...msg,
        index: startIndex + i,
      }));
    },
    
    /**
     * Get total height for virtualization
     */
    get totalHeight() {
      return this.messages.length * this.itemHeight;
    },
    
    /**
     * Get offset for virtualized items
     */
    get offsetY() {
      if (!this.virtualize || this.messages.length < 100) return 0;
      const startIndex = Math.max(0, Math.floor(this.scrollTop / this.itemHeight) - 5);
      return startIndex * this.itemHeight;
    },
    
    /**
     * Handle scroll for virtualization
     * @param {Event} e - Scroll event
     */
    onScroll(e) {
      this.scrollTop = e.target.scrollTop;
    },
    
    /**
     * Scroll to a specific message
     * @param {string} messageId - Message ID
     */
    scrollToMessage(messageId) {
      const index = this.messages.findIndex(m => m.id === messageId);
      if (index >= 0) {
        const offset = index * this.itemHeight;
        this.$el.scrollTop = offset;
      }
    },
    
    /**
     * Scroll to bottom
     */
    scrollToBottom() {
      this.$el.scrollTop = this.$el.scrollHeight;
    },
    
    /**
     * Bind for container
     */
    get container() {
      return {
        '@scroll': (e) => this.onScroll(e),
        ':style': () => this.virtualize ? `position: relative; overflow-y: auto;` : '',
      };
    },
    
    /**
     * Bind for inner wrapper (virtualization)
     */
    get inner() {
      return {
        ':style': () => this.virtualize 
          ? `height: ${this.totalHeight}px; position: relative;`
          : '',
      };
    },
    
    /**
     * Bind for items wrapper (virtualization)
     */
    get items() {
      return {
        ':style': () => this.virtualize
          ? `transform: translateY(${this.offsetY}px);`
          : '',
      };
    },
  };
}
