/**
 * SomaAgent01 — Chat Workspace Wrapper
 * Embeds real chat streaming within the workspace layout.
 *
 * Transport: REST `POST /api/v2/chat/conversations/{id}/messages` (sync mode,
 * admin/chat/api/chat.py). No placeholder replies — failures surface as
 * system messages.
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import type { ComposerSendDetail } from './saas-composer.js';
import type { ToolCallStep } from './saas-tool-timeline.js';
import './saas-message.js';
import './saas-composer.js';

interface WorkspaceMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    tools?: ToolCallStep[];
}

@customElement('saas-chat-workspace')
export class SaasChatWorkspace extends LitElement {
    @state() private _hasConversation = false;
    @state() private _messages: WorkspaceMessage[] = [];
    @state() private _isStreaming = false;
    @state() private _conversationId = '';
    @state() private _agentId = '';

    static styles = css`
        :host {
            display: flex;
            flex-direction: column;
            flex: 1;
            min-height: 0;
            background: var(--aaas-bg-void, #f5f5f5);
        }

        .chat-area {
            flex: 1;
            min-height: 0;
            overflow-y: auto;
            padding: 20px;
        }

        .messages {
            max-width: 720px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 16px;
        }

        .typing-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--aaas-text-muted, #999999);
            animation: typingBounce 1.4s ease-in-out infinite;
        }

        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typingBounce {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-6px); }
        }
    `;

    connectedCallback() {
        super.connectedCallback();

        this.addEventListener('send-message', ((e: CustomEvent<ComposerSendDetail>) => {
            void this._handleSend(e.detail);
        }) as EventListener);

        this.addEventListener('clear-chat', () => {
            this._messages = [];
            this._hasConversation = false;
            this._conversationId = '';
        });

        this.addEventListener('new-conversation', () => {
            this._messages = [];
            this._hasConversation = true;
            this._conversationId = '';
        });
    }

    private _pushSystem(content: string) {
        this._messages = [...this._messages, {
            role: 'system',
            content,
            timestamp: new Date().toISOString(),
        }];
        this._hasConversation = true;
    }

    private async _ensureConversation(): Promise<string | null> {
        if (this._conversationId) return this._conversationId;
        try {
            const data = await apiClient.post<{ id?: string }>('/chat/conversations', {
                agent_id: this._agentId || undefined,
            });
            const id = data?.id ?? null;
            if (id) {
                this._conversationId = id;
                return id;
            }
            this._pushSystem('Failed to create conversation');
            return null;
        } catch (err) {
            console.error('[SaasChatWorkspace] create conversation failed', err);
            this._pushSystem('Failed to create conversation');
            return null;
        }
    }

    private async _handleSend(detail: ComposerSendDetail) {
        const text = (detail?.text ?? '').trim();
        if (!text && (!detail.attachments || detail.attachments.length === 0)) return;
        if (this._isStreaming) {
            this._pushSystem('Still finishing the previous turn — try again shortly');
            return;
        }

        this._hasConversation = true;
        this._messages = [...this._messages, {
            role: 'user',
            content: text,
            timestamp: new Date().toISOString(),
        }];

        this._isStreaming = true;
        try {
            const conversationId = await this._ensureConversation();
            if (!conversationId) {
                this._isStreaming = false;
                return;
            }

            const response = await apiClient.post<{ content?: string; model?: string }>(
                `/chat/conversations/${conversationId}/messages`,
                { content: text, stream: false },
            );

            this._messages = [...this._messages, {
                role: 'assistant',
                content: response?.content ?? '',
                timestamp: new Date().toISOString(),
            }];
        } catch (err) {
            console.error('[SaasChatWorkspace] send failed', err);
            this._pushSystem('Message failed — the chat API is unavailable');
        } finally {
            this._isStreaming = false;
        }
    }

    render() {
        if (!this._hasConversation && this._messages.length === 0) {
            return html`
                <div style="flex:1;overflow:auto;">
                    <saas-welcome-dashboard></saas-welcome-dashboard>
                </div>
                <saas-composer .busy=${this._isStreaming}></saas-composer>
            `;
        }

        return html`
            <div class="chat-area">
                <div class="messages">
                    ${this._messages.map((m) => html`
                        <saas-message
                            message-role=${m.role}
                            .text=${m.content}
                            .timestamp=${m.timestamp}
                            .tools=${m.tools ?? []}
                        ></saas-message>
                    `)}
                    ${this._isStreaming ? html`
                        <div class="typing-indicator">
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                        </div>
                    ` : ''}
                </div>
            </div>
            <saas-composer .busy=${this._isStreaming}></saas-composer>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-chat-workspace': SaasChatWorkspace;
    }
}
