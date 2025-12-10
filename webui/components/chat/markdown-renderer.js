/**
 * Markdown Renderer Component
 *
 * Renders markdown content with support for headings, lists, links,
 * formatting, blockquotes, and tables.
 * Uses marked.js for parsing.
 *
 * @module components/chat/markdown-renderer
 */

/**
 * Configure marked options
 * @returns {Object} Marked options
 */
function getMarkedOptions() {
  return {
    gfm: true, // GitHub Flavored Markdown
    breaks: true, // Convert \n to <br>
    headerIds: false, // Don't add IDs to headers
    mangle: false, // Don't mangle email addresses
    sanitize: false, // We'll sanitize separately
  };
}

/**
 * Sanitize HTML to prevent XSS
 * @param {string} html - HTML string
 * @returns {string} Sanitized HTML
 */
function sanitizeHtml(html) {
  // Basic sanitization - remove script tags and event handlers
  return html
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/on\w+\s*=\s*["'][^"']*["']/gi, '')
    .replace(/javascript:/gi, '');
}

/**
 * Markdown Renderer component factory
 * @param {Object} options - Component options
 * @param {string} options.content - Markdown content
 * @param {boolean} [options.sanitize=true] - Sanitize output
 * @param {boolean} [options.linkTarget='_blank'] - Link target
 * @returns {Object} Alpine component data
 */
export default function MarkdownRenderer(options = {}) {
  return {
    content: options.content ?? '',
    sanitize: options.sanitize ?? true,
    linkTarget: options.linkTarget ?? '_blank',

    // Rendered HTML
    renderedHtml: '',

    init() {
      this.render();
      // Re-render when content changes
      this.$watch('content', () => this.render());
    },


    /**
     * Render markdown to HTML
     */
    render() {
      if (!this.content) {
        this.renderedHtml = '';
        return;
      }

      // Check if marked is available
      if (typeof marked !== 'undefined') {
        try {
          // Configure marked
          marked.setOptions(getMarkedOptions());

          // Custom renderer for links
          const renderer = new marked.Renderer();
          renderer.link = (href, title, text) => {
            const titleAttr = title ? ` title="${title}"` : '';
            return `<a href="${href}"${titleAttr} target="${this.linkTarget}" rel="noopener noreferrer">${text}</a>`;
          };

          // Parse markdown
          let html = marked.parse(this.content, { renderer });

          // Sanitize if enabled
          if (this.sanitize) {
            html = sanitizeHtml(html);
          }

          this.renderedHtml = html;
        } catch (err) {
          console.error('Markdown rendering error:', err);
          this.renderedHtml = this.escapeHtml(this.content);
        }
      } else {
        // Fallback: basic rendering without marked
        this.renderedHtml = this.basicRender(this.content);
      }
    },

    /**
     * Basic markdown rendering fallback
     * @param {string} text - Markdown text
     * @returns {string} HTML
     */
    basicRender(text) {
      let html = this.escapeHtml(text);

      // Bold
      html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');

      // Italic
      html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
      html = html.replace(/_(.+?)_/g, '<em>$1</em>');

      // Strikethrough
      html = html.replace(/~~(.+?)~~/g, '<del>$1</del>');

      // Inline code
      html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

      // Links
      html = html.replace(
        /\[([^\]]+)\]\(([^)]+)\)/g,
        `<a href="$2" target="${this.linkTarget}" rel="noopener noreferrer">$1</a>`
      );

      // Line breaks
      html = html.replace(/\n/g, '<br>');

      return html;
    },

    /**
     * Escape HTML entities
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    },

    /**
     * Update content
     * @param {string} newContent - New markdown content
     */
    setContent(newContent) {
      this.content = newContent;
    },

    /**
     * Bind for container element
     */
    get container() {
      return {
        'x-html': () => this.renderedHtml,
        class: 'markdown-content',
      };
    },
  };
}

export { getMarkedOptions, sanitizeHtml };
