/**
 * Global Search Component
 * Search across sessions, memories, and messages
 * Requirements: 24.1, 24.2, 24.3, 24.4, 24.5
 */

import { fetchApi } from '../../core/api/client.js';
import { ENDPOINTS } from '../../core/api/endpoints.js';
import { debounce } from '../../core/performance/index.js';

/**
 * Global Search Alpine Component
 */
export function createGlobalSearch() {
  return {
    // State
    isOpen: false,
    query: '',
    results: {
      sessions: [],
      memories: [],
      messages: []
    },
    isLoading: false,
    activeCategory: 'all',
    selectedIndex: 0,
    recentSearches: [],
    
    // Categories
    categories: [
      { id: 'all', label: 'All', icon: 'search' },
      { id: 'sessions', label: 'Sessions', icon: 'chat' },
      { id: 'memories', label: 'Memories', icon: 'psychology' },
      { id: 'messages', label: 'Messages', icon: 'message' }
    ],
    
    // Computed
    get hasResults() {
      return this.totalResults > 0;
    },
    
    get totalResults() {
      return this.results.sessions.length + 
             this.results.memories.length + 
             this.results.messages.length;
    },
    
    get filteredResults() {
      if (this.activeCategory === 'all') {
        return [
          ...this.results.sessions.map(r => ({ ...r, type: 'session' })),
          ...this.results.memories.map(r => ({ ...r, type: 'memory' })),
          ...this.results.messages.map(r => ({ ...r, type: 'message' }))
        ];
      }
      
      const categoryMap = {
        sessions: this.results.sessions.map(r => ({ ...r, type: 'session' })),
        memories: this.results.memories.map(r => ({ ...r, type: 'memory' })),
        messages: this.results.messages.map(r => ({ ...r, type: 'message' }))
      };
      
      return categoryMap[this.activeCategory] || [];
    },
    
    // Lifecycle
    init() {
      this.loadRecentSearches();
      this.debouncedSearch = debounce(this.performSearch.bind(this), 300);
      
      // Keyboard shortcut to open
      document.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
          e.preventDefault();
          this.open();
        }
      });
    },
    
    // Open/Close
    open() {
      this.isOpen = true;
      this.$nextTick(() => {
        this.$refs.searchInput?.focus();
      });
    },
    
    close() {
      this.isOpen = false;
      this.query = '';
      this.results = { sessions: [], memories: [], messages: [] };
      this.selectedIndex = 0;
    },
    
    // Search
    onInput() {
      if (this.query.length >= 2) {
        this.debouncedSearch();
      } else {
        this.results = { sessions: [], memories: [], messages: [] };
      }
    },
    
    async performSearch() {
      if (this.query.length < 2) return;
      
      this.isLoading = true;
      this.selectedIndex = 0;
      
      try {
        // Search in parallel
        const [sessions, memories, messages] = await Promise.all([
          this.searchSessions(this.query),
          this.searchMemories(this.query),
          this.searchMessages(this.query)
        ]);
        
        this.results = { sessions, memories, messages };
        
        // Save to recent searches
        this.addRecentSearch(this.query);
      } catch (err) {
        console.error('Search failed:', err);
      } finally {
        this.isLoading = false;
      }
    },
    
    async searchSessions(query) {
      try {
        const response = await fetchApi(`${ENDPOINTS.SESSIONS}?search=${encodeURIComponent(query)}`);
        return (response.contexts || response || []).slice(0, 5).map(s => ({
          id: s.id,
          title: s.name || `Chat #${s.no}`,
          subtitle: `${s.message_count || 0} messages`,
          timestamp: s.updated_at || s.created_at
        }));
      } catch (err) {
        return [];
      }
    },
    
    async searchMemories(query) {
      try {
        const response = await fetchApi(ENDPOINTS.MEMORY_SEARCH, {
          method: 'POST',
          body: JSON.stringify({ query, top_k: 5 })
        });
        return (response.results || []).map(m => ({
          id: m.id,
          title: m.content?.substring(0, 100) || 'Memory',
          subtitle: m.type || 'fact',
          score: m.score,
          timestamp: m.timestamp
        }));
      } catch (err) {
        return [];
      }
    },
    
    async searchMessages(query) {
      try {
        const response = await fetchApi(`/v1/messages/search?q=${encodeURIComponent(query)}&limit=5`);
        return (response.messages || []).map(m => ({
          id: m.id,
          title: m.content?.substring(0, 100) || 'Message',
          subtitle: m.role === 'user' ? 'You' : 'Agent',
          sessionId: m.session_id,
          timestamp: m.timestamp
        }));
      } catch (err) {
        return [];
      }
    },
    
    // Navigation
    onKeydown(e) {
      const results = this.filteredResults;
      
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          this.selectedIndex = Math.min(this.selectedIndex + 1, results.length - 1);
          break;
        case 'ArrowUp':
          e.preventDefault();
          this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
          break;
        case 'Enter':
          e.preventDefault();
          if (results[this.selectedIndex]) {
            this.selectResult(results[this.selectedIndex]);
          }
          break;
        case 'Escape':
          this.close();
          break;
      }
    },
    
    selectResult(result) {
      this.$dispatch('search:select', result);
      
      // Navigate based on type
      switch (result.type) {
        case 'session':
          this.$dispatch('navigate', { view: 'chat', sessionId: result.id });
          break;
        case 'memory':
          this.$dispatch('navigate', { view: 'memory', memoryId: result.id });
          break;
        case 'message':
          this.$dispatch('navigate', { view: 'chat', sessionId: result.sessionId, messageId: result.id });
          break;
      }
      
      this.close();
    },
    
    // Recent Searches
    loadRecentSearches() {
      try {
        const saved = localStorage.getItem('recentSearches');
        this.recentSearches = saved ? JSON.parse(saved) : [];
      } catch (err) {
        this.recentSearches = [];
      }
    },
    
    addRecentSearch(query) {
      if (!query || query.length < 2) return;
      
      // Remove duplicates and add to front
      this.recentSearches = [
        query,
        ...this.recentSearches.filter(s => s !== query)
      ].slice(0, 5);
      
      localStorage.setItem('recentSearches', JSON.stringify(this.recentSearches));
    },
    
    clearRecentSearches() {
      this.recentSearches = [];
      localStorage.removeItem('recentSearches');
    },
    
    useRecentSearch(query) {
      this.query = query;
      this.performSearch();
    },
    
    // Helpers
    getResultIcon(type) {
      const icons = {
        session: 'chat',
        memory: 'psychology',
        message: 'message'
      };
      return icons[type] || 'search';
    },
    
    highlightMatch(text, query) {
      if (!text || !query) return text;
      const regex = new RegExp(`(${query})`, 'gi');
      return text.replace(regex, '<mark>$1</mark>');
    },
    
    formatTimestamp(timestamp) {
      if (!timestamp) return '';
      const date = new Date(timestamp);
      const now = new Date();
      const diff = now - date;
      
      if (diff < 60000) return 'Just now';
      if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
      if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
      return date.toLocaleDateString();
    }
  };
}

/**
 * Register Alpine component
 */
export function registerGlobalSearch() {
  if (typeof Alpine !== 'undefined') {
    Alpine.data('globalSearch', createGlobalSearch);
  }
}

export default createGlobalSearch;
