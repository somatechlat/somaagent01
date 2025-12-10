/**
 * Code Block Component
 *
 * Renders code blocks with syntax highlighting, copy button, and line numbers.
 * Uses Prism.js for syntax highlighting.
 *
 * @module components/chat/code-block
 */

import { toastManager } from '../base/toast.js';

/**
 * Language display names
 */
const LANGUAGE_NAMES = {
  js: 'JavaScript',
  javascript: 'JavaScript',
  ts: 'TypeScript',
  typescript: 'TypeScript',
  py: 'Python',
  python: 'Python',
  rb: 'Ruby',
  ruby: 'Ruby',
  java: 'Java',
  cpp: 'C++',
  c: 'C',
  cs: 'C#',
  csharp: 'C#',
  go: 'Go',
  rust: 'Rust',
  rs: 'Rust',
  php: 'PHP',
  swift: 'Swift',
  kotlin: 'Kotlin',
  scala: 'Scala',
  html: 'HTML',
  css: 'CSS',
  scss: 'SCSS',
  sass: 'Sass',
  less: 'Less',
  json: 'JSON',
  yaml: 'YAML',
  yml: 'YAML',
  xml: 'XML',
  sql: 'SQL',
  bash: 'Bash',
  sh: 'Shell',
  shell: 'Shell',
  powershell: 'PowerShell',
  ps1: 'PowerShell',
  markdown: 'Markdown',
  md: 'Markdown',
  dockerfile: 'Dockerfile',
  docker: 'Dockerfile',
  makefile: 'Makefile',
  graphql: 'GraphQL',
  gql: 'GraphQL',
  regex: 'Regex',
  diff: 'Diff',
  plaintext: 'Plain Text',
  text: 'Plain Text',
};

/**
 * Code Block component factory
 * @param {Object} options - Component options
 * @param {string} options.code - Code content
 * @param {string} [options.language] - Language identifier
 * @param {boolean} [options.showLineNumbers=true] - Show line numbers
 * @param {number} [options.lineNumberThreshold=5] - Min lines for line numbers
 * @returns {Object} Alpine component data
 */
export default function CodeBlock(options = {}) {
  return {
    code: options.code ?? '',
    language: options.language ?? 'plaintext',
    showLineNumbers: options.showLineNumbers ?? true,
    lineNumberThreshold: options.lineNumberThreshold ?? 5,


    // UI state
    copied: false,
    copyTimeout: null,

    /**
     * Get display language name
     */
    get languageDisplay() {
      return LANGUAGE_NAMES[this.language?.toLowerCase()] || this.language || 'Code';
    },

    /**
     * Get lines of code
     */
    get lines() {
      return this.code.split('\n');
    },

    /**
     * Get line count
     */
    get lineCount() {
      return this.lines.length;
    },

    /**
     * Check if should show line numbers
     */
    get shouldShowLineNumbers() {
      return this.showLineNumbers && this.lineCount >= this.lineNumberThreshold;
    },

    /**
     * Get Prism language class
     */
    get prismLanguage() {
      return `language-${this.language || 'plaintext'}`;
    },

    /**
     * Copy code to clipboard
     */
    async copyCode() {
      try {
        await navigator.clipboard.writeText(this.code);
        this.copied = true;

        // Clear previous timeout
        if (this.copyTimeout) {
          clearTimeout(this.copyTimeout);
        }

        // Reset after 2 seconds
        this.copyTimeout = setTimeout(() => {
          this.copied = false;
        }, 2000);

        toastManager.success('Copied!', 'Code copied to clipboard.');
      } catch (err) {
        toastManager.error('Copy failed', 'Unable to copy code to clipboard.');
      }
    },

    /**
     * Highlight code using Prism
     */
    highlightCode() {
      // Check if Prism is available
      if (typeof Prism !== 'undefined') {
        this.$nextTick(() => {
          const codeEl = this.$refs.code;
          if (codeEl) {
            Prism.highlightElement(codeEl);
          }
        });
      }
    },

    init() {
      this.highlightCode();
    },

    /**
     * Bind for code element
     */
    get codeElement() {
      return {
        'x-ref': 'code',
        ':class': () => this.prismLanguage,
        'x-text': () => this.code,
      };
    },

    /**
     * Bind for copy button
     */
    get copyButton() {
      return {
        '@click': () => this.copyCode(),
        ':aria-label': () => (this.copied ? 'Copied!' : 'Copy code'),
        ':title': () => (this.copied ? 'Copied!' : 'Copy'),
      };
    },

    /**
     * Get copy button text/icon
     */
    get copyButtonText() {
      return this.copied ? '✓' : '📋';
    },
  };
}

export { LANGUAGE_NAMES };
