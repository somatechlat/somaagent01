/**
 * SomaAgent SaaS — Memory Search Bar
 * Renders the search/filter sidebar for the memory view.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { MemoryFilter, MemorySort } from '../controllers/memory-view-controller.js';

const FILTERS: MemoryFilter[] = ['all', 'conversation', 'fact', 'episode', 'semantic'];

@customElement('saas-memory-search-bar')
export class SaasMemorySearchBar extends LitElement {
    static styles = css`
        :host {
            display: flex;
            flex-direction: column;
            width: 280px;
            flex-shrink: 0;
            background: var(--saas-bg-card, #ffffff);
            border-right: 1px solid var(--saas-border-light, #e0e0e0);
            padding: 24px 20px;
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
    `;

    @property({ type: String }) searchQuery = '';
    @property({ type: String }) filter: MemoryFilter = 'all';
    @property({ type: String }) sort: MemorySort = 'newest';
    @property({ type: Number }) totalCount = 0;

    render() {
        return html`
            <div class="sidebar-header">
                <h1 class="sidebar-title">Memory</h1>
                <p class="sidebar-subtitle">Browse agent knowledge</p>
            </div>

            <div class="search-box">
                <span class="material-symbols-outlined search-icon">search</span>
                <input
                    type="text"
                    class="search-input"
                    placeholder="Semantic search..."
                    .value=${this.searchQuery}
                    @input=${this._handleInput}
                    @keydown=${this._handleKeydown}
                />
            </div>

            <div class="filter-section">
                <div class="filter-label">Filter by Type</div>
                <div class="filter-options">
                    ${FILTERS.map((f) => html`
                        <button
                            class="filter-chip ${this.filter === f ? 'active' : ''}"
                            @click=${() => this._setFilter(f)}
                        >
                            ${f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
                        </button>
                    `)}
                </div>
            </div>

            <div class="filter-section">
                <div class="filter-label">Sort By</div>
                <select class="sort-select" @change=${this._handleSort}>
                    <option value="newest" ?selected=${this.sort === 'newest'}>Newest First</option>
                    <option value="oldest" ?selected=${this.sort === 'oldest'}>Oldest First</option>
                    <option value="relevance" ?selected=${this.sort === 'relevance'}>Relevance</option>
                </select>
            </div>

            <div class="stats">
                <div class="stat-row">
                    <span class="stat-label">Total Memories</span>
                    <span class="stat-value">${this.totalCount}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Storage Used</span>
                    <span class="stat-value">2.4 GB</span>
                </div>
            </div>

            <button class="back-btn" @click=${this._goBack}>
                <span class="material-symbols-outlined">arrow_back</span> Back to Chat
            </button>
        `;
    }

    private _handleInput(e: Event) {
        this.dispatchEvent(new CustomEvent('search-input', {
            detail: (e.target as HTMLInputElement).value,
            bubbles: true,
            composed: true,
        }));
    }

    private _handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Enter') {
            this.dispatchEvent(new CustomEvent('search-submit', {
                bubbles: true,
                composed: true,
            }));
        }
    }

    private _setFilter(filter: MemoryFilter) {
        this.dispatchEvent(new CustomEvent('filter-change', {
            detail: filter,
            bubbles: true,
            composed: true,
        }));
    }

    private _handleSort(e: Event) {
        this.dispatchEvent(new CustomEvent('sort-change', {
            detail: (e.target as HTMLSelectElement).value,
            bubbles: true,
            composed: true,
        }));
    }

    private _goBack() {
        this.dispatchEvent(new CustomEvent('navigate-back', {
            detail: '/chat',
            bubbles: true,
            composed: true,
        }));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-memory-search-bar': SaasMemorySearchBar;
    }
}
