/**
 * Memory View Controller
 * Manages search, load, and mutations for the memory view.
 */

import { apiClient } from '../services/api-client.js';

export interface Memory {
  id: string;
  type: 'conversation' | 'fact' | 'episode' | 'semantic';
  content: string;
  summary?: string;
  tags: string[];
  score: number;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export type MemoryFilter = 'all' | 'conversation' | 'fact' | 'episode' | 'semantic';
export type MemorySort = 'newest' | 'oldest' | 'relevance';

export interface MemoryViewHost {
  memories: Memory[];
  isLoading: boolean;
  searchQuery: string;
  filter: MemoryFilter;
  sort: MemorySort;
  selectedMemory: Memory | null;
  totalCount: number;
  requestUpdate(): void;
}

export class MemoryViewController {
  private host: MemoryViewHost;

  constructor(host: MemoryViewHost) {
    this.host = host;
  }

  async connect(): Promise<void> {
    await this.loadMemories();
  }

  setSearchQuery(query: string): void {
    this.host.searchQuery = query;
  }

  async handleSearchSubmit(): Promise<void> {
    await this.performSearch();
  }

  async setFilter(filter: MemoryFilter): Promise<void> {
    this.host.filter = filter;
    if (this.host.searchQuery.trim()) {
      await this.performSearch();
    } else {
      await this.loadMemories();
    }
  }

  setSort(sort: MemorySort): void {
    this.host.sort = sort;
    this._sortMemories();
  }

  selectMemory(memory: Memory): void {
    this.host.selectedMemory = this.host.selectedMemory?.id === memory.id ? null : memory;
  }

  copyMemory(memory: Memory): void {
    navigator.clipboard.writeText(memory.content);
  }

  async deleteMemory(memory: Memory): Promise<void> {
    if (!confirm('Delete this memory?')) {
      return;
    }
    try {
      await apiClient.delete(`/memory/${memory.id}`);
      this.host.memories = this.host.memories.filter((m) => m.id !== memory.id);
      if (this.host.selectedMemory?.id === memory.id) {
        this.host.selectedMemory = null;
      }
    } catch (error) {
      console.error('Failed to delete memory:', error);
    }
  }

  exportMemories(): void {
    const data = JSON.stringify(this.host.memories, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'memories-export.json';
    a.click();
    URL.revokeObjectURL(url);
  }

  async refreshMemories(): Promise<void> {
    await this.loadMemories();
  }

  async loadMemories(): Promise<void> {
    this.host.isLoading = true;
    try {
      const response = await apiClient.get<{ memories?: unknown[] }>('/memory/recent?limit=100');
      this.host.memories = (response.memories || []).map((m) => this._mapMemory(m));
      this.host.totalCount = this.host.memories.length;
      this._sortMemories();
    } catch (error) {
      console.error('Failed to load memories:', error);
      this.host.memories = [];
      this.host.totalCount = 0;
    } finally {
      this.host.isLoading = false;
    }
  }

  async performSearch(): Promise<void> {
    if (!this.host.searchQuery.trim()) {
      await this.loadMemories();
      return;
    }

    this.host.isLoading = true;
    try {
      const response = await apiClient.post<{ memories?: unknown[] }>('/memory/search', {
        query: this.host.searchQuery,
        limit: 50,
        memory_type: this._searchType(),
      });
      this.host.memories = (response.memories || []).map((m) => this._mapMemory(m));
      this._sortMemories();
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      this.host.isLoading = false;
    }
  }

  private _searchType(): string | undefined {
    const map: Record<string, string> = {
      conversation: 'episodic',
      fact: 'procedural',
      episode: 'episodic',
      semantic: 'semantic',
    };
    return this.host.filter === 'all' ? undefined : map[this.host.filter];
  }

  private _sortMemories(): void {
    const sorted = [...this.host.memories].sort((a, b) => {
      if (this.host.sort === 'newest') {
        return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      } else if (this.host.sort === 'oldest') {
        return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
      } else {
        return b.score - a.score;
      }
    });
    this.host.memories = sorted;
  }

  private _mapMemory(m: unknown): Memory {
    const raw = m as Record<string, unknown>;
    const meta = (raw.metadata || {}) as Record<string, unknown>;
    const typeMap: Record<string, Memory['type']> = {
      episodic: 'episode',
      semantic: 'semantic',
      procedural: 'fact',
    };
    const memoryType = String(raw.memory_type || '');
    return {
      id: String(raw.id),
      type: typeMap[memoryType] || 'semantic',
      content: String(raw.content || ''),
      summary: meta.summary ? String(meta.summary) : undefined,
      tags: Array.isArray(meta.tags) ? (meta.tags as unknown[]).map((t) => String(t)) : [],
      score: typeof raw.relevance_score === 'number' ? raw.relevance_score : 0,
      timestamp: String(raw.created_at || new Date().toISOString()),
      metadata: meta,
    };
  }
}
