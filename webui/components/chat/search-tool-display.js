/**
 * Search Tool Display Component
 *
 * Specialized display for search tool results.
 * Shows query and results summary with expandable details.
 *
 * @module components/chat/search-tool-display
 * Requirements: 5.6
 */

/**
 * Search engine icons
 */
const SEARCH_ICONS = {
  searxng: '🔍',
  duckduckgo: '🦆',
  google: '🔎',
  bing: '🔎',
  default: '🔍',
};

/**
 * Search Tool Display component factory
 * @param {Object} options - Component options
 * @param {Object} options.search - Search execution data
 * @returns {Object} Alpine component data
 */
export default function SearchToolDisplay(options = {}) {
  return {
    search: options.search ?? {},

    // UI state
    showQuery: true,
    showResults: true,
    expandedResult: null,

    /**
     * Get search engine type
     */
    get engine() {
      return this.search.engine ?? this.search.provider ?? 'searxng';
    },

    /**
     * Get search engine icon
     */
    get engineIcon() {
      return SEARCH_ICONS[this.engine] ?? SEARCH_ICONS.default;
    },

    /**
     * Get search engine display name
     */
    get engineName() {
      const names = {
        searxng: 'SearXNG',
        duckduckgo: 'DuckDuckGo',
        google: 'Google',
        bing: 'Bing',
      };
      return names[this.engine] ?? this.engine;
    },

    /**
     * Get search query
     */
    get query() {
      return this.search.query ?? this.search.input?.query ?? '';
    },

    /**
     * Get search results
     */
    get results() {
      const output = this.search.output ?? this.search.result ?? {};
      return output.results ?? output.items ?? output ?? [];
    },

    /**
     * Get results count
     */
    get resultsCount() {
      if (Array.isArray(this.results)) {
        return this.results.length;
      }
      return 0;
    },

    /**
     * Get results summary text
     */
    get resultsSummary() {
      const count = this.resultsCount;
      if (count === 0) return 'No results found';
      if (count === 1) return '1 result found';
      return `${count} results found`;
    },

    /**
     * Check if search is still running
     */
    get isRunning() {
      return this.search.status === 'running';
    },

    /**
     * Check if search completed successfully
     */
    get isSuccess() {
      return this.search.status === 'success';
    },

    /**
     * Check if search failed
     */
    get isError() {
      return this.search.status === 'error';
    },

    /**
     * Get error message if any
     */
    get errorMessage() {
      return this.search.error ?? this.search.output?.error ?? null;
    },

    /**
     * Get duration
     */
    get duration() {
      if (!this.search.duration) return null;
      return `${(this.search.duration / 1000).toFixed(2)}s`;
    },

    /**
     * Toggle query section visibility
     */
    toggleQuery() {
      this.showQuery = !this.showQuery;
    },

    /**
     * Toggle results section visibility
     */
    toggleResults() {
      this.showResults = !this.showResults;
    },

    /**
     * Toggle individual result expansion
     * @param {number} index - Result index
     */
    toggleResult(index) {
      this.expandedResult = this.expandedResult === index ? null : index;
    },

    /**
     * Check if result is expanded
     * @param {number} index - Result index
     * @returns {boolean}
     */
    isResultExpanded(index) {
      return this.expandedResult === index;
    },

    /**
     * Format result for display
     * @param {Object} result - Search result
     * @returns {Object} Formatted result
     */
    formatResult(result) {
      return {
        title: result.title ?? result.name ?? 'Untitled',
        url: result.url ?? result.link ?? result.href ?? '',
        snippet: result.snippet ?? result.description ?? result.content ?? '',
        source: result.source ?? this.extractDomain(result.url ?? ''),
      };
    },

    /**
     * Extract domain from URL
     * @param {string} url - Full URL
     * @returns {string} Domain name
     */
    extractDomain(url) {
      try {
        const urlObj = new URL(url);
        return urlObj.hostname.replace('www.', '');
      } catch {
        return '';
      }
    },

    /**
     * Open URL in new tab
     * @param {string} url - URL to open
     */
    openUrl(url) {
      if (url) {
        window.open(url, '_blank', 'noopener,noreferrer');
      }
    },
  };
}

export { SEARCH_ICONS };
