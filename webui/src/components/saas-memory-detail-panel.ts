/**
 * SomaAgent SaaS — Memory Detail Panel
 * Renders the details of the selected memory.
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

@customElement('saas-memory-detail-panel')
export class SaasMemoryDetailPanel extends LitElement {
    static styles = css`
        :host {
            display: flex;
            flex-direction: column;
            width: 360px;
            flex-shrink: 0;
            background: var(--saas-bg-card, #ffffff);
            border-left: 1px solid var(--saas-border-light, #e0e0e0);
            overflow-y: auto;
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

        .panel-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 16px;
        }

        .memory-type {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .type-icon {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .type-icon .material-symbols-outlined {
            font-size: 18px;
        }

        .type-icon.conversation { background: #e0f2fe; color: #0369a1; }
        .type-icon.fact { background: #fef3c7; color: #b45309; }
        .type-icon.episode { background: #e0e7ff; color: #4338ca; }
        .type-icon.semantic { background: #d1fae5; color: #047857; }

        .type-label {
            font-size: 13px;
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

        .close-btn {
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

        .close-btn:hover {
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .panel-body {
            padding: 24px;
            flex: 1;
        }

        .section {
            margin-bottom: 24px;
        }

        .section-title {
            font-size: 11px;
            text-transform: uppercase;
            color: var(--saas-text-muted, #999);
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }

        .content {
            font-size: 14px;
            line-height: 1.7;
            color: var(--saas-text-primary, #1a1a1a);
            white-space: pre-wrap;
        }

        .summary {
            font-size: 14px;
            line-height: 1.7;
            color: var(--saas-text-secondary, #666);
            font-style: italic;
        }

        .memory-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }

        .tag {
            padding: 4px 8px;
            border-radius: 4px;
            background: var(--saas-bg-hover, #fafafa);
            font-size: 11px;
            color: var(--saas-text-secondary, #666);
        }

        .metadata-table {
            width: 100%;
            font-size: 13px;
            border-collapse: collapse;
        }

        .metadata-table td {
            padding: 8px 0;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            color: var(--saas-text-secondary, #666);
        }

        .metadata-table td:first-child {
            width: 40%;
            color: var(--saas-text-muted, #999);
        }

        .metadata-table tr:last-child td {
            border-bottom: none;
        }

        .panel-actions {
            padding: 16px 24px;
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            gap: 8px;
        }

        .action-btn {
            flex: 1;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            background: var(--saas-bg-card, #ffffff);
            font-size: 13px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            transition: all 0.1s ease;
        }

        .action-btn:hover {
            background: var(--saas-bg-hover, #fafafa);
        }

        .action-btn.danger {
            color: var(--saas-status-danger, #ef4444);
            border-color: rgba(239, 68, 68, 0.3);
        }

        .action-btn.danger:hover {
            background: rgba(239, 68, 68, 0.05);
        }
    `;

    @property({ type: Object }) memory?: Memory;

    render() {
        if (!this.memory) {
            return html``;
        }

        const date = new Date(this.memory.timestamp).toLocaleString();
        const meta = this.memory.metadata || {};

        return html`
            <div class="panel-header">
                <div class="memory-type">
                    <div class="type-icon ${this.memory.type}">
                        <span class="material-symbols-outlined">${TYPE_ICONS[this.memory.type] || 'description'}</span>
                    </div>
                    <div>
                        <div class="type-label">${this.memory.type}</div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span class="memory-score">${Math.round(this.memory.score * 100)}%</span>
                    <button class="close-btn" @click=${this._close} title="Close">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
            </div>

            <div class="panel-body">
                ${this.memory.summary ? html`
                    <div class="section">
                        <div class="section-title">Summary</div>
                        <div class="summary">${this.memory.summary}</div>
                    </div>
                ` : ''}

                <div class="section">
                    <div class="section-title">Content</div>
                    <div class="content">${this.memory.content}</div>
                </div>

                ${this.memory.tags.length > 0 ? html`
                    <div class="section">
                        <div class="section-title">Tags</div>
                        <div class="memory-tags">
                            ${this.memory.tags.map((tag) => html`<span class="tag">${tag}</span>`)}
                        </div>
                    </div>
                ` : ''}

                <div class="section">
                    <div class="section-title">Details</div>
                    <table class="metadata-table">
                        <tr><td>ID</td><td>${this.memory.id}</td></tr>
                        <tr><td>Created</td><td>${date}</td></tr>
                        <tr><td>Score</td><td>${this.memory.score.toFixed(4)}</td></tr>
                        ${Object.entries(meta).filter(([key]) => key !== 'tags' && key !== 'summary').map(([key, value]) => html`
                            <tr><td>${key}</td><td>${String(value)}</td></tr>
                        `)}
                    </table>
                </div>
            </div>

            <div class="panel-actions">
                <button class="action-btn" @click=${this._copy}>
                    <span class="material-symbols-outlined">content_copy</span> Copy
                </button>
                <button class="action-btn danger" @click=${this._delete}>
                    <span class="material-symbols-outlined">delete</span> Delete
                </button>
            </div>
        `;
    }

    private _close() {
        if (this.memory) {
            this.dispatchEvent(new CustomEvent('memory-select', {
                detail: this.memory,
                bubbles: true,
                composed: true,
            }));
        }
    }

    private _copy() {
        if (this.memory) {
            this.dispatchEvent(new CustomEvent('memory-copy', {
                detail: this.memory,
                bubbles: true,
                composed: true,
            }));
        }
    }

    private _delete() {
        if (this.memory) {
            this.dispatchEvent(new CustomEvent('memory-delete', {
                detail: this.memory,
                bubbles: true,
                composed: true,
            }));
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-memory-detail-panel': SaasMemoryDetailPanel;
    }
}
