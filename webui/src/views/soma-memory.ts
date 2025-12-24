/**
 * Eye of God Memory Browser View
 * Per Eye of God UIX Design Section 2.2
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - SomaBrain memory integration
 * - Semantic search
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import '../components/soma-card.js';
import '../components/soma-input.js';
import '../components/soma-select.js';
import '../components/soma-tabs.js';

interface Memory {
    id: string;
    content: string;
    memory_type: 'episodic' | 'semantic' | 'procedural';
    importance: number;
    access_count: number;
    last_accessed: string;
    created_at: string;
}

interface SearchResult {
    memory: Memory;
    score: number;
}

@customElement('soma-memory')
export class SomaMemory extends LitElement {
    static styles = css`
        :host {
            display: block;
            padding: var(--soma-spacing-lg, 24px);
            height: 100%;
            overflow-y: auto;
        }

        .memory-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--soma-spacing-xl, 32px);
        }

        h1 {
            font-size: var(--soma-text-2xl, 24px);
            font-weight: 600;
            color: var(--soma-text-main, #e2e8f0);
            margin: 0;
        }

        .search-bar {
            display: flex;
            gap: var(--soma-spacing-md, 16px);
            margin-bottom: var(--soma-spacing-lg, 24px);
        }

        .search-input {
            flex: 1;
        }

        .filters {
            display: flex;
            gap: var(--soma-spacing-sm, 8px);
            margin-bottom: var(--soma-spacing-lg, 24px);
        }

        .filter-chip {
            padding: var(--soma-spacing-xs, 4px) var(--soma-spacing-md, 16px);
            border-radius: var(--soma-radius-full, 9999px);
            background: var(--soma-surface, rgba(30, 41, 59, 0.85));
            border: 1px solid var(--soma-border-color, rgba(255, 255, 255, 0.1));
            color: var(--soma-text-dim, #64748b);
            font-size: var(--soma-text-sm, 13px);
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .filter-chip:hover {
            border-color: var(--soma-accent, #94a3b8);
        }

        .filter-chip.active {
            background: var(--soma-accent, #94a3b8);
            color: var(--soma-bg-void, #0f172a);
            border-color: var(--soma-accent, #94a3b8);
        }

        .memory-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: var(--soma-spacing-lg, 24px);
        }

        .memory-card {
            position: relative;
        }

        .memory-type-badge {
            position: absolute;
            top: var(--soma-spacing-md, 16px);
            right: var(--soma-spacing-md, 16px);
            padding: 2px 8px;
            border-radius: var(--soma-radius-sm, 4px);
            font-size: var(--soma-text-xs, 11px);
            font-weight: 600;
            text-transform: uppercase;
        }

        .type-episodic {
            background: rgba(34, 197, 94, 0.2);
            color: var(--soma-success, #22c55e);
        }

        .type-semantic {
            background: rgba(59, 130, 246, 0.2);
            color: var(--soma-info, #3b82f6);
        }

        .type-procedural {
            background: rgba(168, 85, 247, 0.2);
            color: #a855f7;
        }

        .memory-content {
            font-size: var(--soma-text-sm, 13px);
            color: var(--soma-text-main, #e2e8f0);
            line-height: 1.6;
            margin-bottom: var(--soma-spacing-md, 16px);
            max-height: 100px;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .memory-meta {
            display: flex;
            gap: var(--soma-spacing-lg, 24px);
            font-size: var(--soma-text-xs, 11px);
            color: var(--soma-text-dim, #64748b);
        }

        .meta-item {
            display: flex;
            align-items: center;
            gap: var(--soma-spacing-xs, 4px);
        }

        .importance-bar {
            width: 60px;
            height: 4px;
            background: var(--soma-border-color, rgba(255, 255, 255, 0.1));
            border-radius: 2px;
            overflow: hidden;
        }

        .importance-bar-fill {
            height: 100%;
            background: var(--soma-accent, #94a3b8);
            transition: width 0.3s ease;
        }

        .score-badge {
            background: rgba(148, 163, 184, 0.2);
            color: var(--soma-accent, #94a3b8);
            padding: 2px 6px;
            border-radius: var(--soma-radius-sm, 4px);
            font-size: var(--soma-text-xs, 11px);
            font-weight: 600;
        }

        .empty-state {
            text-align: center;
            padding: var(--soma-spacing-2xl, 48px);
            color: var(--soma-text-dim, #64748b);
        }

        .empty-icon {
            font-size: 48px;
            margin-bottom: var(--soma-spacing-md, 16px);
        }

        .loading {
            display: flex;
            justify-content: center;
            padding: var(--soma-spacing-xl, 32px);
        }

        .spinner {
            width: 32px;
            height: 32px;
            border: 3px solid var(--soma-border-color, rgba(255, 255, 255, 0.1));
            border-top-color: var(--soma-accent, #94a3b8);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    `;

    @state() private _memories: Memory[] = [];
    @state() private _searchResults: SearchResult[] = [];
    @state() private _searchQuery = '';
    @state() private _selectedType: string | null = null;
    @state() private _isLoading = false;
    @state() private _isSearching = false;

    private _memoryTypes = [
        { id: 'all', label: 'All' },
        { id: 'episodic', label: 'Episodic' },
        { id: 'semantic', label: 'Semantic' },
        { id: 'procedural', label: 'Procedural' },
    ];

    connectedCallback() {
        super.connectedCallback();
        this._loadMemories();
    }

    render() {
        return html`
            <header class="memory-header">
                <h1>🧠 Memory Browser</h1>
            </header>

            <div class="search-bar">
                <soma-input
                    class="search-input"
                    placeholder="Search memories..."
                    .value=${this._searchQuery}
                    @soma-input=${this._handleSearchInput}
                    @keyup=${this._handleSearchKeyup}
                ></soma-input>
                <soma-button @click=${this._performSearch}>Search</soma-button>
            </div>

            <div class="filters">
                ${this._memoryTypes.map(type => html`
                    <button
                        class="filter-chip ${this._selectedType === type.id || (!this._selectedType && type.id === 'all') ? 'active' : ''}"
                        @click=${() => this._filterByType(type.id)}
                    >
                        ${type.label}
                    </button>
                `)}
            </div>

            ${this._isLoading || this._isSearching ? html`
                <div class="loading">
                    <div class="spinner"></div>
                </div>
            ` : this._renderContent()}
        `;
    }

    private _renderContent() {
        const items = this._searchResults.length > 0
            ? this._searchResults
            : this._memories.map(m => ({ memory: m, score: 0 }));

        const filtered = this._selectedType && this._selectedType !== 'all'
            ? items.filter(item => item.memory.memory_type === this._selectedType)
            : items;

        if (filtered.length === 0) {
            return html`
                <div class="empty-state">
                    <div class="empty-icon">🔍</div>
                    <p>No memories found</p>
                </div>
            `;
        }

        return html`
            <div class="memory-grid">
                ${filtered.map(item => this._renderMemoryCard(item))}
            </div>
        `;
    }

    private _renderMemoryCard(item: SearchResult) {
        const { memory, score } = item;
        const date = new Date(memory.created_at).toLocaleDateString();

        return html`
            <soma-card class="memory-card" clickable @soma-click=${() => this._viewMemory(memory)}>
                <span class="memory-type-badge type-${memory.memory_type}">${memory.memory_type}</span>
                <div class="memory-content">${memory.content}</div>
                <div class="memory-meta">
                    <div class="meta-item">
                        <span>Importance:</span>
                        <div class="importance-bar">
                            <div class="importance-bar-fill" style="width: ${memory.importance * 100}%"></div>
                        </div>
                    </div>
                    <div class="meta-item">
                        <span>👁️ ${memory.access_count}</span>
                    </div>
                    <div class="meta-item">
                        <span>📅 ${date}</span>
                    </div>
                    ${score > 0 ? html`
                        <span class="score-badge">${Math.round(score * 100)}% match</span>
                    ` : ''}
                </div>
            </soma-card>
        `;
    }

    private async _loadMemories() {
        this._isLoading = true;
        try {
            const response = await fetch('/api/v2/memory/', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            });
            if (response.ok) {
                this._memories = await response.json();
            }
        } catch (error) {
            console.error('Failed to load memories:', error);
        } finally {
            this._isLoading = false;
        }
    }

    private _handleSearchInput(e: CustomEvent) {
        this._searchQuery = e.detail.value;
    }

    private _handleSearchKeyup(e: KeyboardEvent) {
        if (e.key === 'Enter') {
            this._performSearch();
        }
    }

    private async _performSearch() {
        if (!this._searchQuery.trim()) {
            this._searchResults = [];
            return;
        }

        this._isSearching = true;
        try {
            const response = await fetch('/api/v2/memory/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    query: this._searchQuery,
                    limit: 20,
                }),
            });
            if (response.ok) {
                this._searchResults = await response.json();
            }
        } catch (error) {
            console.error('Search failed:', error);
        } finally {
            this._isSearching = false;
        }
    }

    private _filterByType(type: string) {
        this._selectedType = type === 'all' ? null : type;
    }

    private _viewMemory(memory: Memory) {
        this.dispatchEvent(new CustomEvent('soma-view-memory', {
            detail: { memory },
            bubbles: true,
            composed: true,
        }));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-memory': SomaMemory;
    }
}
