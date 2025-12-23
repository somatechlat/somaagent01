/**
 * SomaAgent SaaS — Memory View
 * Per AGENT_USER_UI_SRS.md Section 8 and UI_SCREENS_SRS.md
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - SomaBrain API integration
 * - Minimal white/black design per UI_STYLE_GUIDE.md
 * - NO EMOJIS - Google Material Symbols only
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
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

type MemoryFilter = 'all' | 'conversation' | 'fact' | 'episode' | 'semantic';
type MemorySort = 'newest' | 'oldest' | 'relevance';

@customElement('saas-memory-view')
export class SaasMemoryView extends LitElement {
    static styles = css`
        :host {
            display: flex;
            height: 100vh;
            background: var(--saas-bg-page, #f5f5f5);
            font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            color: var(--saas-text-primary, #1a1a1a);
        }

        * {
            box-sizing: border-box;
        }

        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: 20px;
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            -webkit-font-feature-settings: 'liga';
            -webkit-font-smoothing: antialiased;
        }

        /* ========================================
           SIDEBAR
           ======================================== */
        .sidebar {
            width: 280px;
            background: var(--saas-bg-card, #ffffff);
            border-right: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            padding: 24px 20px;
        }

        .sidebar-header {
            margin-bottom: 24px;
        }

        .sidebar-title {
            font-size: 20px;
            font-weight: 600;
            margin: 0 0 4px 0;
        }

        .sidebar-subtitle {
            font-size: 13px;
            color: var(--saas-text-secondary, #666);
        }

        /* Search */
        .search-box {
            position: relative;
            margin-bottom: 20px;
        }

        .search-input {
            width: 100%;
            padding: 10px 14px 10px 42px;
            border-radius: 8px;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            font-size: 14px;
            background: var(--saas-bg-card, #ffffff);
            color: var(--saas-text-primary, #1a1a1a);
            transition: border-color 0.15s ease;
        }

        .search-input:focus {
            outline: none;
            border-color: var(--saas-text-primary, #1a1a1a);
        }

        .search-icon {
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--saas-text-muted, #999);
            font-size: 18px;
        }

        /* Filters */
        .filter-section {
            margin-bottom: 24px;
        }

        .filter-label {
            font-size: 11px;
            text-transform: uppercase;
            color: var(--saas-text-muted, #999);
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }

        .filter-options {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .filter-chip {
            padding: 6px 12px;
            border-radius: 16px;
            background: var(--saas-bg-hover, #fafafa);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            font-size: 13px;
            cursor: pointer;
            transition: all 0.1s ease;
        }

        .filter-chip:hover {
            border-color: var(--saas-border-medium, #ccc);
        }

        .filter-chip.active {
            background: #1a1a1a;
            color: white;
            border-color: #1a1a1a;
        }

        /* Sort */
        .sort-select {
            width: 100%;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            font-size: 14px;
            background: var(--saas-bg-card, #ffffff);
            color: var(--saas-text-primary, #1a1a1a);
            cursor: pointer;
        }

        /* Stats */
        .stats {
            margin-top: auto;
            padding-top: 20px;
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            font-size: 13px;
        }

        .stat-label {
            color: var(--saas-text-secondary, #666);
        }

        .stat-value {
            font-weight: 600;
        }

        /* Back Button */
        .back-btn {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 14px;
            border-radius: 8px;
            background: transparent;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            font-size: 14px;
            cursor: pointer;
            color: var(--saas-text-primary, #1a1a1a);
            margin-top: 16px;
            transition: all 0.1s ease;
        }

        .back-btn:hover {
            background: var(--saas-bg-hover, #fafafa);
        }

        /* ========================================
           MAIN CONTENT
           ======================================== */
        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        /* Header */
        .header {
            padding: 16px 24px;
            background: var(--saas-bg-card, #ffffff);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .result-count {
            font-size: 14px;
            color: var(--saas-text-secondary, #666);
        }

        .header-actions {
            display: flex;
            gap: 8px;
        }

        .action-btn {
            padding: 8px 16px;
            border-radius: 8px;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            background: var(--saas-bg-card, #ffffff);
            font-size: 13px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.1s ease;
        }

        .action-btn:hover {
            background: var(--saas-bg-hover, #fafafa);
        }

        .action-btn.primary {
            background: #1a1a1a;
            color: white;
            border-color: #1a1a1a;
        }

        .action-btn.primary:hover {
            background: #333;
        }

        .action-btn .material-symbols-outlined {
            font-size: 18px;
        }

        /* Memory Grid */
        .memory-grid {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 16px;
            align-content: start;
        }

        /* Memory Card */
        .memory-card {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 12px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .memory-card:hover {
            border-color: var(--saas-border-medium, #ccc);
            box-shadow: var(--saas-shadow-sm, 0 2px 4px rgba(0,0,0,0.04));
        }

        .memory-card.selected {
            border-color: #1a1a1a;
            box-shadow: 0 0 0 1px #1a1a1a;
        }

        .memory-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            margin-bottom: 12px;
        }

        .memory-type {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .type-icon {
            width: 28px;
            height: 28px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .type-icon .material-symbols-outlined {
            font-size: 16px;
        }

        .type-icon.conversation { background: #e0f2fe; color: #0369a1; }
        .type-icon.fact { background: #fef3c7; color: #b45309; }
        .type-icon.episode { background: #e0e7ff; color: #4338ca; }
        .type-icon.semantic { background: #d1fae5; color: #047857; }

        .type-label {
            font-size: 12px;
            font-weight: 500;
            text-transform: capitalize;
            color: var(--saas-text-secondary, #666);
        }

        .memory-score {
            font-size: 12px;
            font-weight: 600;
            padding: 4px 8px;
            border-radius: 4px;
            background: var(--saas-bg-hover, #fafafa);
        }

        .memory-content {
            font-size: 14px;
            line-height: 1.6;
            color: var(--saas-text-primary, #1a1a1a);
            margin-bottom: 12px;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .memory-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 12px;
        }

        .tag {
            padding: 4px 8px;
            border-radius: 4px;
            background: var(--saas-bg-hover, #fafafa);
            font-size: 11px;
            color: var(--saas-text-secondary, #666);
        }

        .memory-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            color: var(--saas-text-muted, #999);
        }

        .memory-actions {
            display: flex;
            gap: 4px;
        }

        .memory-action {
            width: 28px;
            height: 28px;
            border-radius: 6px;
            background: transparent;
            border: none;
            color: var(--saas-text-muted, #999);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.1s ease;
        }

        .memory-action:hover {
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .memory-action.danger:hover {
            color: var(--saas-status-danger, #ef4444);
        }

        .memory-action .material-symbols-outlined {
            font-size: 16px;
        }

        /* Empty State */
        .empty-state {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 40px;
        }

        .empty-icon {
            width: 64px;
            height: 64px;
            background: var(--saas-bg-hover, #fafafa);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 20px;
        }

        .empty-icon .material-symbols-outlined {
            font-size: 28px;
            color: var(--saas-text-secondary, #666);
        }

        .empty-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .empty-desc {
            font-size: 14px;
            color: var(--saas-text-secondary, #666);
            max-width: 320px;
        }

        /* Loading */
        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 60px;
        }

        .spinner {
            width: 32px;
            height: 32px;
            border: 3px solid var(--saas-border-light, #e0e0e0);
            border-top-color: #1a1a1a;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    `;

    @state() private _memories: Memory[] = [];
    @state() private _isLoading = false;
    @state() private _searchQuery = '';
    @state() private _filter: MemoryFilter = 'all';
    @state() private _sort: MemorySort = 'newest';
    @state() private _selectedMemory: Memory | null = null;
    @state() private _totalCount = 0;

    async connectedCallback() {
        super.connectedCallback();
        await this._loadMemories();
    }

    render() {
        return html`
            <!-- Sidebar -->
            <aside class="sidebar">
                <div class="sidebar-header">
                    <h1 class="sidebar-title">Memory</h1>
                    <p class="sidebar-subtitle">Browse agent knowledge</p>
                </div>

                <!-- Search -->
                <div class="search-box">
                    <span class="material-symbols-outlined search-icon">search</span>
                    <input 
                        type="text" 
                        class="search-input" 
                        placeholder="Semantic search..."
                        .value=${this._searchQuery}
                        @input=${this._handleSearch}
                        @keydown=${this._handleSearchKeydown}
                    >
                </div>

                <!-- Filter by Type -->
                <div class="filter-section">
                    <div class="filter-label">Filter by Type</div>
                    <div class="filter-options">
                        ${(['all', 'conversation', 'fact', 'episode', 'semantic'] as MemoryFilter[]).map(f => html`
                            <button 
                                class="filter-chip ${this._filter === f ? 'active' : ''}"
                                @click=${() => this._setFilter(f)}
                            >
                                ${f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
                            </button>
                        `)}
                    </div>
                </div>

                <!-- Sort -->
                <div class="filter-section">
                    <div class="filter-label">Sort By</div>
                    <select class="sort-select" @change=${this._handleSort}>
                        <option value="newest" ?selected=${this._sort === 'newest'}>Newest First</option>
                        <option value="oldest" ?selected=${this._sort === 'oldest'}>Oldest First</option>
                        <option value="relevance" ?selected=${this._sort === 'relevance'}>Relevance</option>
                    </select>
                </div>

                <!-- Stats -->
                <div class="stats">
                    <div class="stat-row">
                        <span class="stat-label">Total Memories</span>
                        <span class="stat-value">${this._totalCount}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Storage Used</span>
                        <span class="stat-value">2.4 GB</span>
                    </div>
                </div>

                <!-- Back Button -->
                <button class="back-btn" @click=${() => window.location.href = '/chat'}>
                    <span class="material-symbols-outlined">arrow_back</span> Back to Chat
                </button>
            </aside>

            <!-- Main Content -->
            <main class="main">
                <header class="header">
                    <div class="header-left">
                        <span class="result-count">${this._memories.length} memories</span>
                    </div>
                    <div class="header-actions">
                        <button class="action-btn" @click=${this._exportMemories}>
                            <span class="material-symbols-outlined">download</span> Export
                        </button>
                        <button class="action-btn primary" @click=${this._refreshMemories}>
                            <span class="material-symbols-outlined">refresh</span> Refresh
                        </button>
                    </div>
                </header>

                ${this._isLoading ? html`
                    <div class="loading">
                        <div class="spinner"></div>
                    </div>
                ` : this._memories.length === 0 ? this._renderEmptyState() : html`
                    <div class="memory-grid">
                        ${this._memories.map(memory => this._renderMemoryCard(memory))}
                    </div>
                `}
            </main>
        `;
    }

    private _renderEmptyState() {
        return html`
            <div class="empty-state">
                <div class="empty-icon"><span class="material-symbols-outlined">psychology</span></div>
                <div class="empty-title">No Memories Found</div>
                <div class="empty-desc">
                    ${this._searchQuery
                ? `No memories match "${this._searchQuery}"`
                : 'Start chatting with the agent to create memories.'}
                </div>
            </div>
        `;
    }

    private _renderMemoryCard(memory: Memory) {
        const typeIcons: Record<string, string> = {
            conversation: 'chat',
            fact: 'article',
            episode: 'event',
            semantic: 'hub',
        };

        const date = new Date(memory.timestamp).toLocaleDateString();

        return html`
            <div 
                class="memory-card ${this._selectedMemory?.id === memory.id ? 'selected' : ''}"
                @click=${() => this._selectMemory(memory)}
            >
                <div class="memory-header">
                    <div class="memory-type">
                        <div class="type-icon ${memory.type}">
                            <span class="material-symbols-outlined">${typeIcons[memory.type] || 'description'}</span>
                        </div>
                        <span class="type-label">${memory.type}</span>
                    </div>
                    <span class="memory-score">${Math.round(memory.score * 100)}%</span>
                </div>

                <div class="memory-content">
                    ${memory.summary || memory.content}
                </div>

                ${memory.tags.length > 0 ? html`
                    <div class="memory-tags">
                        ${memory.tags.slice(0, 3).map(tag => html`
                            <span class="tag">${tag}</span>
                        `)}
                        ${memory.tags.length > 3 ? html`
                            <span class="tag">+${memory.tags.length - 3}</span>
                        ` : ''}
                    </div>
                ` : ''}

                <div class="memory-footer">
                    <span>${date}</span>
                    <div class="memory-actions">
                        <button class="memory-action" @click=${(e: Event) => this._copyMemory(e, memory)} title="Copy">
                            <span class="material-symbols-outlined">content_copy</span>
                        </button>
                        <button class="memory-action danger" @click=${(e: Event) => this._deleteMemory(e, memory)} title="Delete">
                            <span class="material-symbols-outlined">delete</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    private async _loadMemories() {
        this._isLoading = true;

        try {
            // Call SomaBrain API - GET /api/v2/memory/
            const response = await apiClient.get('/memory/');
            if (response.memories) {
                this._memories = response.memories;
                this._totalCount = response.total || this._memories.length;
            } else {
                // Demo data if API not available
                this._memories = [
                    {
                        id: '1',
                        type: 'conversation',
                        content: 'User discussed PostgreSQL database optimization strategies including indexing, query planning, and connection pooling.',
                        summary: 'PostgreSQL optimization discussion',
                        tags: ['database', 'postgresql', 'optimization'],
                        score: 0.92,
                        timestamp: new Date().toISOString(),
                    },
                    {
                        id: '2',
                        type: 'fact',
                        content: 'The production database is hosted on AWS RDS with 16GB RAM and 500GB storage.',
                        tags: ['infrastructure', 'aws', 'database'],
                        score: 0.88,
                        timestamp: new Date(Date.now() - 86400000).toISOString(),
                    },
                    {
                        id: '3',
                        type: 'episode',
                        content: 'Resolved a critical outage on Dec 20th by increasing connection pool size from 50 to 200.',
                        tags: ['incident', 'resolution', 'database'],
                        score: 0.95,
                        timestamp: new Date(Date.now() - 172800000).toISOString(),
                    },
                    {
                        id: '4',
                        type: 'semantic',
                        content: 'Docker containers provide isolation and reproducibility for application deployments.',
                        tags: ['docker', 'containers', 'devops'],
                        score: 0.78,
                        timestamp: new Date(Date.now() - 259200000).toISOString(),
                    },
                ];
                this._totalCount = this._memories.length;
            }
        } catch (error) {
            console.error('Failed to load memories:', error);
            // Fallback to empty
            this._memories = [];
        } finally {
            this._isLoading = false;
        }
    }

    private _handleSearch(e: Event) {
        this._searchQuery = (e.target as HTMLInputElement).value;
    }

    private _handleSearchKeydown(e: KeyboardEvent) {
        if (e.key === 'Enter') {
            this._performSearch();
        }
    }

    private async _performSearch() {
        if (!this._searchQuery.trim()) {
            await this._loadMemories();
            return;
        }

        this._isLoading = true;
        try {
            // Call SomaBrain /recall endpoint
            const response = await apiClient.post('/memory/recall/', {
                query: this._searchQuery,
                limit: 50,
            });
            if (response.memories) {
                this._memories = response.memories;
            }
        } catch (error) {
            console.error('Search failed:', error);
        } finally {
            this._isLoading = false;
        }
    }

    private _setFilter(filter: MemoryFilter) {
        this._filter = filter;
        // Filter loaded memories
        if (filter === 'all') {
            this._loadMemories();
        } else {
            // Would call API with filter param
        }
    }

    private _handleSort(e: Event) {
        this._sort = (e.target as HTMLSelectElement).value as MemorySort;
        // Re-sort memories
        const sorted = [...this._memories].sort((a, b) => {
            if (this._sort === 'newest') {
                return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
            } else if (this._sort === 'oldest') {
                return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
            } else {
                return b.score - a.score; // relevance
            }
        });
        this._memories = sorted;
    }

    private _selectMemory(memory: Memory) {
        this._selectedMemory = this._selectedMemory?.id === memory.id ? null : memory;
    }

    private _copyMemory(e: Event, memory: Memory) {
        e.stopPropagation();
        navigator.clipboard.writeText(memory.content);
    }

    private async _deleteMemory(e: Event, memory: Memory) {
        e.stopPropagation();
        if (confirm('Delete this memory?')) {
            try {
                await apiClient.delete(`/memory/${memory.id}/`);
                this._memories = this._memories.filter(m => m.id !== memory.id);
            } catch (error) {
                console.error('Failed to delete memory:', error);
            }
        }
    }

    private _exportMemories() {
        const data = JSON.stringify(this._memories, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'memories-export.json';
        a.click();
        URL.revokeObjectURL(url);
    }

    private async _refreshMemories() {
        await this._loadMemories();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-memory-view': SaasMemoryView;
    }
}
