/**
 * SomaStack UI - Memory Browser Component
 * Version: 1.0.0
 * 
 * Provides card/list view toggle, search by content/coordinate/metadata,
 * memory type badges, age/decay display, detail panel, and admin delete.
 */

document.addEventListener('alpine:init', () => {
  /**
   * Memory Browser Component
   * Full-featured memory browsing interface
   */
  Alpine.data('memoryBrowser', (config = {}) => ({
    memories: config.memories || [],
    viewMode: config.viewMode || 'card',
    searchQuery: '',
    searchField: 'all',
    selectedMemory: null,
    isLoading: false,
    isDetailOpen: false,
    sortBy: 'timestamp',
    sortDirection: 'desc',
    pageSize: config.pageSize || 12,
    currentPage: 1,
    endpoint: config.endpoint || 'http://localhost:9595',
    
    init() {
      if (config.autoLoad !== false) {
        this.loadMemories();
      }
    },
    
    async loadMemories() {
      this.isLoading = true;
      try {
        const response = await fetch(`${this.endpoint}/memories`);
        if (response.ok) {
          const data = await response.json();
          this.memories = data.memories || data || [];
        }
      } catch (err) {
        console.warn('Failed to load memories:', err.message);
        if (window.$toast) {
          window.$toast.error('Failed to load memories');
        }
      } finally {
        this.isLoading = false;
      }
    },
    
    async searchMemories(query) {
      if (!query.trim()) {
        return this.loadMemories();
      }
      
      this.isLoading = true;
      try {
        const response = await fetch(`${this.endpoint}/memories/search`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, top_k: 50 })
        });
        if (response.ok) {
          const data = await response.json();
          this.memories = data.results || data.memories || [];
        }
      } catch (err) {
        console.warn('Failed to search memories:', err.message);
      } finally {
        this.isLoading = false;
      }
    },
    
    get filteredMemories() {
      let result = [...this.memories];
      
      // Apply local search filter
      if (this.searchQuery.trim()) {
        const query = this.searchQuery.toLowerCase();
        result = result.filter(m => {
          if (this.searchField === 'all' || this.searchField === 'content') {
            if (this.getContent(m).toLowerCase().includes(query)) return true;
          }
          if (this.searchField === 'all' || this.searchField === 'coordinate') {
            if (this.formatCoordinate(m.coordinate).toLowerCase().includes(query)) return true;
          }
          if (this.searchField === 'all' || this.searchField === 'metadata') {
            if (JSON.stringify(m.metadata || {}).toLowerCase().includes(query)) return true;
          }
          return false;
        });
      }
      
      // Apply sorting
      result.sort((a, b) => {
        let aVal, bVal;
        
        switch (this.sortBy) {
          case 'timestamp':
            aVal = new Date(a.timestamp || a.created_at || 0);
            bVal = new Date(b.timestamp || b.created_at || 0);
            break;
          case 'type':
            aVal = a.memory_type || a.type || '';
            bVal = b.memory_type || b.type || '';
            break;
          case 'score':
            aVal = a.score || a.similarity || 0;
            bVal = b.score || b.similarity || 0;
            break;
          default:
            aVal = a[this.sortBy] || '';
            bVal = b[this.sortBy] || '';
        }
        
        if (aVal < bVal) return this.sortDirection === 'asc' ? -1 : 1;
        if (aVal > bVal) return this.sortDirection === 'asc' ? 1 : -1;
        return 0;
      });
      
      return result;
    },
    
    get paginatedMemories() {
      const start = (this.currentPage - 1) * this.pageSize;
      return this.filteredMemories.slice(start, start + this.pageSize);
    },
    
    get totalPages() {
      return Math.ceil(this.filteredMemories.length / this.pageSize);
    },
    
    get totalItems() {
      return this.filteredMemories.length;
    },
    
    get showPagination() {
      return this.totalItems > this.pageSize;
    },
    
    // View mode
    setViewMode(mode) {
      this.viewMode = mode;
    },
    
    // Sorting
    toggleSort(field) {
      if (this.sortBy === field) {
        this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
      } else {
        this.sortBy = field;
        this.sortDirection = 'desc';
      }
    },
    
    // Pagination
    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++;
      }
    },
    
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
      }
    },
    
    goToPage(page) {
      this.currentPage = Math.max(1, Math.min(page, this.totalPages));
    },
    
    // Memory selection
    selectMemory(memory) {
      this.selectedMemory = memory;
      this.isDetailOpen = true;
    },
    
    closeDetail() {
      this.isDetailOpen = false;
      this.selectedMemory = null;
    },
    
    // Memory type helpers
    getMemoryType(memory) {
      return memory.memory_type || memory.type || 'unknown';
    },
    
    getTypeClass(memory) {
      const type = this.getMemoryType(memory);
      return `soma-memory-badge--${type}`;
    },
    
    getTypeIcon(memory) {
      const type = this.getMemoryType(memory);
      const icons = {
        episodic: '📅',
        semantic: '📚',
        procedural: '⚙️',
        working: '💭',
        unknown: '❓'
      };
      return icons[type] || icons.unknown;
    },
    
    // Content helpers
    getContent(memory) {
      return memory.content || memory.payload?.content || memory.text || '';
    },
    
    getPreview(memory, maxLength = 150) {
      const content = this.getContent(memory);
      if (content.length <= maxLength) return content;
      return content.substring(0, maxLength) + '...';
    },
    
    // Coordinate helpers
    formatCoordinate(coord) {
      if (!coord) return 'N/A';
      if (Array.isArray(coord)) {
        return `[${coord.map(c => c.toFixed(3)).join(', ')}]`;
      }
      return String(coord);
    },
    
    // Age and decay helpers
    getAge(memory) {
      const timestamp = memory.timestamp || memory.created_at;
      if (!timestamp) return 'Unknown';
      
      const now = new Date();
      const created = new Date(timestamp);
      const diffMs = now - created;
      
      const minutes = Math.floor(diffMs / 60000);
      const hours = Math.floor(diffMs / 3600000);
      const days = Math.floor(diffMs / 86400000);
      
      if (days > 0) return `${days}d ago`;
      if (hours > 0) return `${hours}h ago`;
      if (minutes > 0) return `${minutes}m ago`;
      return 'Just now';
    },
    
    getDecayLevel(memory) {
      const decay = memory.decay || memory.strength || 1;
      if (decay > 0.7) return 'fresh';
      if (decay > 0.3) return 'aging';
      return 'fading';
    },
    
    getDecayClass(memory) {
      return `soma-memory-decay--${this.getDecayLevel(memory)}`;
    },
    
    getDecayPercent(memory) {
      const decay = memory.decay || memory.strength || 1;
      return Math.round(decay * 100);
    },
    
    // Similarity score
    getScore(memory) {
      const score = memory.score || memory.similarity;
      if (score === undefined || score === null) return null;
      return (score * 100).toFixed(1);
    },
    
    // Admin actions
    async deleteMemory(memory) {
      if (!Alpine.store('auth')?.hasPermission('delete')) {
        if (window.$toast) {
          window.$toast.error('You do not have permission to delete memories');
        }
        return;
      }
      
      const confirmed = confirm('Are you sure you want to delete this memory?');
      if (!confirmed) return;
      
      try {
        const response = await fetch(`${this.endpoint}/delete`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ coordinate: memory.coordinate })
        });
        
        if (response.ok) {
          this.memories = this.memories.filter(m => m !== memory);
          this.closeDetail();
          if (window.$toast) {
            window.$toast.success('Memory deleted');
          }
        } else {
          throw new Error('Delete failed');
        }
      } catch (err) {
        console.error('Failed to delete memory:', err);
        if (window.$toast) {
          window.$toast.error('Failed to delete memory');
        }
      }
    },
    
    // Refresh
    refresh() {
      this.currentPage = 1;
      this.loadMemories();
    }
  }));

  /**
   * Memory Card Component
   * Individual memory card for card view
   */
  Alpine.data('memoryCard', (config = {}) => ({
    memory: config.memory || {},
    isHovered: false,
    
    get typeClass() {
      const type = this.memory.memory_type || this.memory.type || 'unknown';
      return `soma-memory-card--${type}`;
    }
  }));

  /**
   * Memory Detail Panel Component
   * Detailed view of a single memory
   */
  Alpine.data('memoryDetail', (config = {}) => ({
    memory: config.memory || null,
    activeTab: 'content',
    
    setTab(tab) {
      this.activeTab = tab;
    },
    
    get hasMetadata() {
      return this.memory?.metadata && Object.keys(this.memory.metadata).length > 0;
    },
    
    get hasVector() {
      return this.memory?.vector || this.memory?.embedding;
    },
    
    formatJson(obj) {
      return JSON.stringify(obj, null, 2);
    }
  }));
});
