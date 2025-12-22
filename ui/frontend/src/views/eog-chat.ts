/**
 * Eye of God Chat View
 * Per Eye of God UIX Design Section 4.3
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - WebSocket streaming support
 * - Message rendering
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state, query } from 'lit/decorators.js';
import { wsClient } from '../services/websocket-client.js';
import { apiClient } from '../services/api-client.js';
import '../components/eog-button.js';
import '../components/eog-input.js';

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    confidence?: number;
    streaming?: boolean;
}

@customElement('eog-chat')
export class EogChat extends LitElement {
    static styles = css`
        :host {
            display: flex;
            flex-direction: column;
            height: 100%;
            background: var(--eog-bg-base, #1e293b);
        }

        .messages {
            flex: 1;
            overflow-y: auto;
            padding: var(--eog-spacing-lg, 24px);
            display: flex;
            flex-direction: column;
            gap: var(--eog-spacing-md, 16px);
        }

        .message {
            max-width: 80%;
            padding: var(--eog-spacing-md, 16px);
            border-radius: var(--eog-radius-lg, 12px);
            position: relative;
        }

        .message.user {
            align-self: flex-end;
            background: var(--eog-accent, #94a3b8);
            color: white;
        }

        .message.assistant {
            align-self: flex-start;
            background: var(--eog-surface, rgba(30, 41, 59, 0.85));
            border: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.05));
            color: var(--eog-text-main, #e2e8f0);
        }

        .message.system {
            align-self: center;
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.2);
            color: var(--eog-info, #3b82f6);
            font-size: var(--eog-text-sm, 13px);
            max-width: 60%;
        }

        .message-content {
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: var(--eog-text-base, 14px);
            line-height: var(--eog-leading-relaxed, 1.75);
        }

        .message-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: var(--eog-spacing-sm, 8px);
            font-size: var(--eog-text-xs, 11px);
            opacity: 0.7;
        }

        .confidence {
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .confidence-bar {
            width: 40px;
            height: 4px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 2px;
            overflow: hidden;
        }

        .confidence-fill {
            height: 100%;
            background: var(--eog-success, #22c55e);
            transition: width 0.3s ease;
        }

        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: var(--eog-spacing-sm, 8px);
        }

        .typing-dot {
            width: 6px;
            height: 6px;
            background: var(--eog-text-dim, #64748b);
            border-radius: 50%;
            animation: typing 1.4s infinite ease-in-out;
        }

        .typing-dot:nth-child(1) { animation-delay: 0s; }
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
            0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
            40% { transform: scale(1); opacity: 1; }
        }

        .input-container {
            padding: var(--eog-spacing-md, 16px);
            background: var(--eog-surface, rgba(30, 41, 59, 0.85));
            border-top: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.05));
            display: flex;
            gap: var(--eog-spacing-sm, 8px);
        }

        .chat-input {
            flex: 1;
        }

        .chat-input textarea {
            width: 100%;
            padding: var(--eog-spacing-sm, 8px) var(--eog-spacing-md, 16px);
            border-radius: var(--eog-radius-md, 8px);
            border: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.1));
            background: var(--eog-bg-base, #1e293b);
            color: var(--eog-text-main, #e2e8f0);
            font-family: var(--eog-font-sans);
            font-size: var(--eog-text-base, 14px);
            resize: none;
            outline: none;
            min-height: 44px;
            max-height: 120px;
        }

        .chat-input textarea:focus {
            border-color: var(--eog-accent, #94a3b8);
        }

        .chat-input textarea::placeholder {
            color: var(--eog-text-dim, #64748b);
        }

        .empty-state {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: var(--eog-text-dim, #64748b);
            text-align: center;
            padding: var(--eog-spacing-xl, 32px);
        }

        .empty-state-icon {
            font-size: 48px;
            margin-bottom: var(--eog-spacing-md, 16px);
        }

        .empty-state h3 {
            margin: 0 0 var(--eog-spacing-xs, 4px) 0;
            color: var(--eog-text-main, #e2e8f0);
        }
    `;

    @property({ type: String }) sessionId = '';
    @state() private _messages: ChatMessage[] = [];
    @state() private _input = '';
    @state() private _isStreaming = false;
    @state() private _streamContent = '';

    @query('.messages') private _messagesContainer!: HTMLElement;

    private _unsubscribe?: () => void;

    async connectedCallback() {
        super.connectedCallback();

        // Subscribe to WebSocket events
        this._unsubscribe = wsClient.on('chat.message', (data) => {
            this._handleIncomingMessage(data as ChatMessage);
        });

        wsClient.on('chat.stream', (data: unknown) => {
            const chunk = data as { content: string; done: boolean; confidence?: number };
            this._handleStreamChunk(chunk);
        });

        // Load history if session exists
        if (this.sessionId) {
            await this._loadHistory();
        }
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this._unsubscribe?.();
    }

    render() {
        return html`
            ${this._messages.length === 0 ? this._renderEmptyState() : html`
                <div class="messages">
                    ${this._messages.map(msg => this._renderMessage(msg))}
                    ${this._isStreaming ? this._renderStreamingMessage() : ''}
                </div>
            `}

            <div class="input-container">
                <div class="chat-input">
                    <textarea
                        rows="1"
                        placeholder="Type a message..."
                        .value=${this._input}
                        @input=${(e: Event) => this._input = (e.target as HTMLTextAreaElement).value}
                        @keydown=${this._handleKeydown}
                    ></textarea>
                </div>
                <eog-button 
                    variant="primary" 
                    ?disabled=${!this._input.trim() || this._isStreaming}
                    @eog-click=${this._sendMessage}
                >
                    Send
                </eog-button>
            </div>
        `;
    }

    private _renderEmptyState() {
        return html`
            <div class="empty-state">
                <div class="empty-state-icon">💬</div>
                <h3>Start a conversation</h3>
                <p>Send a message to begin chatting with the agent.</p>
            </div>
        `;
    }

    private _renderMessage(msg: ChatMessage) {
        return html`
            <div class="message ${msg.role}">
                <div class="message-content">${msg.content}</div>
                <div class="message-meta">
                    <span>${this._formatTime(msg.timestamp)}</span>
                    ${msg.confidence != null ? html`
                        <div class="confidence">
                            <span>${(msg.confidence * 100).toFixed(0)}%</span>
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: ${msg.confidence * 100}%"></div>
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    private _renderStreamingMessage() {
        return html`
            <div class="message assistant">
                ${this._streamContent ? html`
                    <div class="message-content">${this._streamContent}</div>
                ` : html`
                    <div class="typing-indicator">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                `}
            </div>
        `;
    }

    private _handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this._sendMessage();
        }
    }

    private async _sendMessage() {
        const content = this._input.trim();
        if (!content || this._isStreaming) return;

        // Add user message
        const userMessage: ChatMessage = {
            id: `msg-${Date.now()}`,
            role: 'user',
            content,
            timestamp: new Date().toISOString(),
        };
        this._messages = [...this._messages, userMessage];
        this._input = '';
        this._isStreaming = true;
        this._streamContent = '';

        // Scroll to bottom
        this.updateComplete.then(() => this._scrollToBottom());

        try {
            // Send via WebSocket or API
            wsClient.send('chat.send', {
                session_id: this.sessionId,
                content,
            });
        } catch (error) {
            console.error('Failed to send message:', error);
            this._isStreaming = false;
        }
    }

    private _handleIncomingMessage(msg: ChatMessage) {
        this._isStreaming = false;
        this._streamContent = '';
        this._messages = [...this._messages, msg];
        this.updateComplete.then(() => this._scrollToBottom());
    }

    private _handleStreamChunk(chunk: { content: string; done: boolean; confidence?: number }) {
        this._streamContent += chunk.content;

        if (chunk.done) {
            // Convert stream to final message
            const message: ChatMessage = {
                id: `msg-${Date.now()}`,
                role: 'assistant',
                content: this._streamContent,
                timestamp: new Date().toISOString(),
                confidence: chunk.confidence,
            };
            this._handleIncomingMessage(message);
        }

        this.updateComplete.then(() => this._scrollToBottom());
    }

    private async _loadHistory() {
        try {
            const messages = await apiClient.get<ChatMessage[]>(
                `/chat/${this.sessionId}/messages`
            );
            this._messages = messages;
        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    }

    private _scrollToBottom() {
        if (this._messagesContainer) {
            this._messagesContainer.scrollTop = this._messagesContainer.scrollHeight;
        }
    }

    private _formatTime(timestamp: string): string {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-chat': EogChat;
    }
}
