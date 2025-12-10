/**
 * Math Renderer Component
 *
 * Renders LaTeX math expressions using KaTeX.
 * Supports both inline ($...$) and block ($$...$$) math.
 *
 * @module components/chat/math-renderer
 */

/**
 * KaTeX rendering options
 */
const KATEX_OPTIONS = {
  throwOnError: false,
  errorColor: '#ef4444',
  displayMode: false,
  trust: false,
  strict: false,
  macros: {
    '\\R': '\\mathbb{R}',
    '\\N': '\\mathbb{N}',
    '\\Z': '\\mathbb{Z}',
    '\\Q': '\\mathbb{Q}',
    '\\C': '\\mathbb{C}',
  },
};

/**
 * Math Renderer component factory
 * @param {Object} options - Component options
 * @param {string} options.expression - LaTeX expression
 * @param {boolean} [options.displayMode=false] - Block mode (centered)
 * @returns {Object} Alpine component data
 */
export default function MathRenderer(options = {}) {
  return {
    expression: options.expression ?? '',
    displayMode: options.displayMode ?? false,

    // Rendered HTML
    renderedHtml: '',
    error: null,

    init() {
      this.render();
      // Re-render when expression changes
      this.$watch('expression', () => this.render());
    },

    /**
     * Render LaTeX to HTML using KaTeX
     */
    render() {
      if (!this.expression) {
        this.renderedHtml = '';
        this.error = null;
        return;
      }

      // Check if KaTeX is available
      if (typeof katex !== 'undefined') {
        try {
          this.renderedHtml = katex.renderToString(this.expression, {
            ...KATEX_OPTIONS,
            displayMode: this.displayMode,
          });
          this.error = null;
        } catch (err) {
          console.error('KaTeX rendering error:', err);
          this.error = err.message;
          this.renderedHtml = this.renderError(err.message);
        }
      } else {
        // Fallback: show raw expression
        this.renderedHtml = this.renderFallback();
      }
    },


    /**
     * Render error message
     * @param {string} message - Error message
     * @returns {string} HTML
     */
    renderError(message) {
      return `<span class="math-error" title="${this.escapeHtml(message)}">${this.escapeHtml(this.expression)}</span>`;
    },

    /**
     * Render fallback when KaTeX is not available
     * @returns {string} HTML
     */
    renderFallback() {
      const escaped = this.escapeHtml(this.expression);
      if (this.displayMode) {
        return `<div class="math-fallback math-block">$$${escaped}$$</div>`;
      }
      return `<span class="math-fallback math-inline">$${escaped}$</span>`;
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
     * Update expression
     * @param {string} newExpression - New LaTeX expression
     */
    setExpression(newExpression) {
      this.expression = newExpression;
    },

    /**
     * Check if has error
     */
    get hasError() {
      return this.error !== null;
    },

    /**
     * Bind for container element
     */
    get container() {
      return {
        'x-html': () => this.renderedHtml,
        ':class': () => ({
          'math-container': true,
          'math-display': this.displayMode,
          'math-inline': !this.displayMode,
          'math-has-error': this.hasError,
        }),
      };
    },
  };
}

/**
 * Parse text and extract math expressions
 * @param {string} text - Text with math expressions
 * @returns {Array} Array of {type: 'text'|'inline'|'block', content: string}
 */
export function parseMathExpressions(text) {
  const parts = [];
  let remaining = text;

  // Pattern for block math ($$...$$)
  const blockPattern = /\$\$([^$]+)\$\$/g;
  // Pattern for inline math ($...$)
  const inlinePattern = /\$([^$\n]+)\$/g;

  // First, extract block math
  let lastIndex = 0;
  let match;

  // Reset regex
  blockPattern.lastIndex = 0;

  while ((match = blockPattern.exec(text)) !== null) {
    // Add text before match
    if (match.index > lastIndex) {
      parts.push({
        type: 'text',
        content: text.slice(lastIndex, match.index),
      });
    }

    // Add block math
    parts.push({
      type: 'block',
      content: match[1].trim(),
    });

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push({
      type: 'text',
      content: text.slice(lastIndex),
    });
  }

  // Now process inline math in text parts
  const finalParts = [];
  for (const part of parts) {
    if (part.type !== 'text') {
      finalParts.push(part);
      continue;
    }

    // Extract inline math from text
    let textRemaining = part.content;
    let textLastIndex = 0;
    inlinePattern.lastIndex = 0;

    while ((match = inlinePattern.exec(part.content)) !== null) {
      // Add text before match
      if (match.index > textLastIndex) {
        finalParts.push({
          type: 'text',
          content: part.content.slice(textLastIndex, match.index),
        });
      }

      // Add inline math
      finalParts.push({
        type: 'inline',
        content: match[1].trim(),
      });

      textLastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (textLastIndex < part.content.length) {
      finalParts.push({
        type: 'text',
        content: part.content.slice(textLastIndex),
      });
    }
  }

  return finalParts;
}

export { KATEX_OPTIONS };
