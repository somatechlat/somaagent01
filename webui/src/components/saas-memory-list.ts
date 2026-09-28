/**
 * SomaAgent SaaS — Memory List
 * Renders the memory entries list with header actions.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { Memory } from '../controllers/memory-view-controller.js';

const TYPE_ICONS: Record<string, string> = {
    conversation: 'chat',
    fact: 'article',
    episode: 'event',
    semantic: 'hub',
};

@customElement('saas-memory-list')
export class SaasMemoryList extends LitElement {
    static styles = css`
        :host {
            display: flex;
            flex: 1;
            flex-direction: column;
            overflow: hidden;
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

        .header {
            padding: 16px 24px;
            background: var(--saas-bg-card, #ffffff);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-shrink: 0;
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

        .memory-grid {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 16px;
            align-content: start;
        }

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

        .loading {
            flex: 1;
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

    @property({ type: Array }) memories: Memory[] = [];
    @property({ type: Boolean }) isLoading = false;
    @property({ type: Object }) selectedMemory: Memory | null = null;
    @property({ type: String }) searchQuery = '';

    render() {
        return html`
            <header class="header">
                <div class="header-left">
                    <span class="result-count">${this.memories.length} memories</span>
                </div>
                <div class="header-actions">
                    <button class="action-btn" @click=${this._export}>
                        <span class="material-symbols-outlined">download</span> Export
                    </button>
                    <button class="action-btn primary" @click=${this._refresh}>
                        <span class="material-symbols-outlined">refresh</span> Refresh
                    </button>
                </div>
            </header>

            ${this.isLoading ? html`
                <div class="loading">
                    <div class="spinner"></div>
                </div>
            ` : this.memories.length === 0 ? this._renderEmptyState() : html`
                <div class="memory-grid">
                    ${this.memories.map((memory) => this._renderMemoryCard(memory))}
                </div>
            `}
        `;
    }

    private _renderEmptyState() {
        return html`
            <div class="empty-state">
                <div class="empty-icon"><span class="material-symbols-outlined">psychology</span></div>
                <div class="empty-title">No Memories Found</div>
                <div class="empty-desc">
                    ${this.searchQuery
                        ? `No memories match "${this.searchQuery}"`
                        : 'Start chatting with the agent to create memories.'}
                </div>
            </div>
        `;
    }

    private _renderMemoryCard(memory: Memory) {
        const date = new Date(memory.timestamp).toLocaleDateString();

        return html`
            <div
                class="memory-card ${this.selectedMemory?.id === memory.id ? 'selected' : ''}"
                @click=${() => this._select(memory)}
            >
                <div class="memory-header">
                    <div class="memory-type">
                        <div class="type-icon ${memory.type}">
                            <span class="material-symbols-outlined">${TYPE_ICONS[memory.type] || 'description'}</span>
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
                        ${memory.tags.slice(0, 3).map((tag) => html`
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
                        <button class="memory-action" @click=${(e: Event) => this._copy(e, memory)} title="Copy">
                            <span class="material-symbols-outlined">content_copy</span>
                        </button>
                        <button class="memory-action danger" @click=${(e: Event) => this._delete(e, memory)} title="Delete">
                            <span class="material-symbols-outlined">delete</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    private _select(memory: Memory) {
        this.dispatchEvent(new CustomEvent('memory-select', {
            detail: memory,
            bubbles: true,
            composed: true,
        }));
    }

    private _copy(e: Event, memory: Memory) {
        e.stopPropagation();
        this.dispatchEvent(new CustomEvent('memory-copy', {
            detail: memory,
            bubbles: true,
            composed: true,
        }));
    }

    private _delete(e: Event, memory: Memory) {
        e.stopPropagation();
        this.dispatchEvent(new CustomEvent('memory-delete', {
            detail: memory,
            bubbles: true,
            composed: true,
        }));
    }

    private _export() {
        this.dispatchEvent(new CustomEvent('export-memories', {
            bubbles: true,
            composed: true,
        }));
    }

    private _refresh() {
        this.dispatchEvent(new CustomEvent('refresh-memories', {
            bubbles: true,
            composed: true,
        }));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-memory-list': SaasMemoryList;
    }
}
