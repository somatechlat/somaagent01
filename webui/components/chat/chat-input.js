/**
 * Chat Input Component
 * 
 * Multi-line input with auto-resize, attachments, and send button.
 * 
 * @module components/chat/chat-input
 */

/**
 * Chat Input component factory
 * @param {Object} options - Input options
 * @param {string} [options.value=''] - Initial value
 * @param {string} [options.placeholder='Type a message...'] - Placeholder text
 * @param {boolean} [options.disabled=false] - Disabled state
 * @param {Function} options.onSend - Send handler
 * @param {Function} [options.onChange] - Change handler
 * @param {Function} [options.onAttach] - Attachment handler
 * @returns {Object} Alpine component data
 */
export default function ChatInput(options = {}) {
  return {
    value: options.value ?? '',
    placeholder: options.placeholder ?? 'Type a message...',
    disabled: options.disabled ?? false,
    isSending: false,
    attachments: [],
    maxHeight: 200,
    
    /**
     * Bind for textarea
     */
    get textarea() {
      return {
        ':value': () => this.value,
        '@input': (e) => this.onInput(e),
        '@keydown.enter': (e) => this.onKeyDown(e),
        '@paste': (e) => this.onPaste(e),
        ':placeholder': () => this.placeholder,
        ':disabled': () => this.disabled || this.isSending,
        ':rows': () => 1,
        ':style': () => `max-height: ${this.maxHeight}px; overflow-y: auto;`,
        'class': 'input textarea',
      };
    },
    
    /**
     * Handle input change
     * @param {Event} e - Input event
     */
    onInput(e) {
      this.value = e.target.value;
      this.autoResize(e.target);
      options.onChange?.(this.value);
    },
    
    /**
     * Handle key down
     * @param {KeyboardEvent} e - Keyboard event
     */
    onKeyDown(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.send();
      }
    },
    
    /**
     * Handle paste for images
     * @param {ClipboardEvent} e - Paste event
     */
    onPaste(e) {
      const items = e.clipboardData?.items;
      if (!items) return;
      
      for (const item of items) {
        if (item.type.startsWith('image/')) {
          e.preventDefault();
          const file = item.getAsFile();
          if (file) {
            this.addAttachment(file);
          }
          break;
        }
      }
    },
    
    /**
     * Auto-resize textarea
     * @param {HTMLTextAreaElement} el - Textarea element
     */
    autoResize(el) {
      el.style.height = 'auto';
      el.style.height = Math.min(el.scrollHeight, this.maxHeight) + 'px';
    },
    
    /**
     * Send message
     */
    async send() {
      const text = this.value.trim();
      if (!text && this.attachments.length === 0) return;
      if (this.disabled || this.isSending) return;
      
      this.isSending = true;
      
      try {
        await options.onSend?.(text, this.attachments);
        this.value = '';
        this.attachments = [];
        
        // Reset textarea height
        this.$nextTick(() => {
          const textarea = this.$el.querySelector('textarea');
          if (textarea) {
            textarea.style.height = 'auto';
          }
        });
      } finally {
        this.isSending = false;
      }
    },
    
    /**
     * Add attachment
     * @param {File} file - File to attach
     */
    addAttachment(file) {
      this.attachments.push({
        id: crypto.randomUUID(),
        file,
        name: file.name,
        type: file.type,
        preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : null,
      });
      options.onAttach?.(this.attachments);
    },
    
    /**
     * Remove attachment
     * @param {string} id - Attachment ID
     */
    removeAttachment(id) {
      const index = this.attachments.findIndex(a => a.id === id);
      if (index >= 0) {
        const attachment = this.attachments[index];
        if (attachment.preview) {
          URL.revokeObjectURL(attachment.preview);
        }
        this.attachments.splice(index, 1);
      }
    },
    
    /**
     * Open file picker
     */
    openFilePicker() {
      const input = document.createElement('input');
      input.type = 'file';
      input.multiple = true;
      input.accept = 'image/*,.pdf,.txt,.md,.json,.csv';
      input.onchange = (e) => {
        for (const file of e.target.files) {
          this.addAttachment(file);
        }
      };
      input.click();
    },
    
    /**
     * Check if can send
     */
    get canSend() {
      return (this.value.trim() || this.attachments.length > 0) && !this.disabled && !this.isSending;
    },
    
    /**
     * Bind for send button
     */
    get sendButton() {
      return {
        '@click': () => this.send(),
        ':disabled': () => !this.canSend,
        ':class': () => ({
          'btn-loading': this.isSending,
        }),
      };
    },
    
    /**
     * Bind for attach button
     */
    get attachButton() {
      return {
        '@click': () => this.openFilePicker(),
        ':disabled': () => this.disabled,
      };
    },
  };
}
