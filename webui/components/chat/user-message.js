/**
 * User Message Component
 * 
 * Displays a user message with avatar and timestamp.
 * 
 * @module components/chat/user-message
 */

/**
 * User Message component factory
 * @param {Object} options - Message options
 * @param {Object} options.message - Message object
 * @returns {Object} Alpine component data
 */
export default function UserMessage(options = {}) {
  return {
    message: options.message ?? {},
    
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
     * Get user initials for avatar
     */
    get initials() {
      return 'U';
    },
    
    /**
     * Check if message has attachments
     */
    get hasAttachments() {
      return this.message.attachments?.length > 0;
    },
    
    /**
     * Get attachments
     */
    get attachments() {
      return this.message.attachments ?? [];
    },
  };
}
