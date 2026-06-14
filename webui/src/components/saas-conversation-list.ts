/**
 * SomaAgent SaaS — Conversation List
 * Renders the sidebar conversation list.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { Conversation } from '../views/saas-chat.js';

@customElement('saas-conversation-list')
export class SaasConversationList extends LitElement {
    static styles = css`
        :host {
            display: flex;
            flex-direction: column;
            width: 280px;
            background: var(--saas-bg-card, #ffffff);
            border-right: 1px solid var(--saas-border-light, #e0e0e0);
            flex-shrink: 0;
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
            padding: 20px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-icon {
            width: 36px;
            height: 36px;
            background: #1a1a1a;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .brand-icon svg {
            width: 18px;
            height: 18px;
            stroke: white;
            fill: none;
        }

        .brand-name {
            font-size: 16px;
            font-weight: 600;
        }

        .new-chat-btn {
            margin: 16px 20px;
            padding: 12px 16px;
            border-radius: 8px;
            background: #1a1a1a;
            color: white;
            border: none;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: background 0.15s ease;
        }

        .new-chat-btn:hover {
            background: #333;
        }

        .conversations-section {
            padding: 0 12px;
            flex: 1;
            overflow-y: auto;
        }

        .section-label {
            font-size: 11px;
            text-transform: uppercase;
            color: var(--saas-text-muted, #999);
            padding: 16px 8px 8px;
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        .conversation-item {
            padding: 12px;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.1s ease;
            margin-bottom: 4px;
        }

        .conversation-item:hover {
            background: var(--saas-bg-hover, #fafafa);
        }

        .conversation-item.active {
            background: var(--saas-bg-active, #f0f0f0);
        }

        .conversation-title {
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .conversation-preview {
            font-size: 12px;
            color: var(--saas-text-secondary, #666);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .quick-links {
            padding: 16px 12px;
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .quick-link {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            border-radius: 8px;
            font-size: 14px;
            color: var(--saas-text-secondary, #666);
            cursor: pointer;
            transition: all 0.1s ease;
        }

        .quick-link:hover {
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .quick-link-icon {
            font-size: 18px;
            width: 20px;
            text-align: center;
        }

        .user-section {
            padding: 16px 20px;
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .user-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: var(--saas-bg-active, #f0f0f0);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: 600;
        }

        .user-info {
            flex: 1;
        }

        .user-name {
            font-size: 14px;
            font-weight: 500;
        }

        .user-role {
            font-size: 12px;
            color: var(--saas-text-muted, #999);
        }

        .logout-btn {
            width: 32px;
            height: 32px;
            border-radius: 6px;
            background: transparent;
            border: none;
            color: var(--saas-text-secondary, #666);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.1s ease;
        }

        .logout-btn:hover {
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-status-danger, #ef4444);
        }
    `;

    @property({ type: Array }) conversations: Conversation[] = [];
    @property({ type: String }) activeConversationId = '';
    @property({ type: String }) userName = '';
    @property({ type: String }) userRole = '';

    render() {
        return html`
            <div class="sidebar-header">
                <div class="brand">
                    <div class="brand-icon">
                        <svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="3" y="3" width="7" height="7" rx="1"/>
                            <rect x="14" y="3" width="7" height="7" rx="1"/>
                            <rect x="14" y="14" width="7" height="7" rx="1"/>
                            <rect x="3" y="14" width="7" height="7" rx="1"/>
                        </svg>
                    </div>
                    <span class="brand-name">SomaAgent</span>
                </div>
            </div>

            <button class="new-chat-btn" @click=${this._startNewChat}>
                <span class="material-symbols-outlined">add</span> New Conversation
            </button>

            <div class="conversations-section">
                <div class="section-label">Conversations</div>
                ${this.conversations.map((conv) => html`
                    <div
                        class="conversation-item ${conv.id === this.activeConversationId ? 'active' : ''}"
                        @click=${() => this._selectConversation(conv.id)}
                    >
                        <div class="conversation-title">${conv.title}</div>
                        <div class="conversation-preview">${conv.lastMessage}</div>
                    </div>
                `)}
            </div>

            <div class="quick-links">
                <div class="section-label">Quick Access</div>
                <div class="quick-link" @click=${() => this._navigate('/memory')}>
                    <span class="material-symbols-outlined quick-link-icon">psychology</span> Memory
                </div>
                <div class="quick-link" @click=${() => this._navigate('/tools')}>
                    <span class="material-symbols-outlined quick-link-icon">construction</span> Tools
                </div>
                <div class="quick-link" @click=${() => this._navigate('/settings')}>
                    <span class="material-symbols-outlined quick-link-icon">settings</span> Settings
                </div>
                <div class="quick-link" @click=${() => this._navigate('/themes')}>
                    <span class="material-symbols-outlined quick-link-icon">palette</span> Theme
                </div>
            </div>

            <div class="user-section">
                <div class="user-avatar">${this._getInitials(this.userName)}</div>
                <div class="user-info">
                    <div class="user-name">${this.userName}</div>
                    <div class="user-role">${this.userRole}</div>
                </div>
                <button class="logout-btn" @click=${this._logout} title="Logout">
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                        <polyline points="16 17 21 12 16 7"/>
                        <line x1="21" y1="12" x2="9" y2="12"/>
                    </svg>
                </button>
            </div>
        `;
    }

    private _getInitials(name: string): string {
        return name
            .split(' ')
            .map((part) => part[0])
            .join('')
            .slice(0, 2)
            .toUpperCase();
    }

    private _selectConversation(id: string) {
        this.dispatchEvent(new CustomEvent('saas-select-conversation', {
            detail: id,
            bubbles: true,
            composed: true,
        }));
    }

    private _startNewChat() {
        this.dispatchEvent(new CustomEvent('saas-new-chat', {
            bubbles: true,
            composed: true,
        }));
    }

    private _navigate(path: string) {
        this.dispatchEvent(new CustomEvent('saas-navigate', {
            detail: { route: path },
            bubbles: true,
            composed: true,
        }));
    }

    private _logout() {
        this.dispatchEvent(new CustomEvent('saas-logout', {
            bubbles: true,
            composed: true,
        }));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-conversation-list': SaasConversationList;
    }
}
