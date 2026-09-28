/**
 * SomaAgent SaaS — Chat Message List
 * Renders the list of messages and streaming content.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { ChatMessage } from '../views/saas-chat.js';

@customElement('saas-chat-message-list')
export class SaasChatMessageList extends LitElement {
    static styles = css`
        :host {
            display: flex;
            flex: 1;
            flex-direction: column;
            overflow-y: auto;
            padding: 24px;
            padding-bottom: 120px;
            gap: 16px;
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

        .message {
            max-width: 75%;
            padding: 14px 18px;
            border-radius: 16px;
            font-size: 14px;
            line-height: 1.6;
            animation: fadeIn 0.2s ease-out;
        }

        .message.user {
            align-self: flex-end;
            background: #1a1a1a;
            color: white;
            border-bottom-right-radius: 4px;
        }

        .message.assistant {
            align-self: flex-start;
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            color: var(--saas-text-primary, #1a1a1a);
            border-bottom-left-radius: 4px;
        }

        .message.system {
            align-self: center;
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-text-secondary, #666);
            font-size: 13px;
            border-radius: 99px;
            padding: 8px 16px;
        }

        .message-time {
            font-size: 11px;
            color: inherit;
            opacity: 0.6;
            margin-top: 6px;
        }

        .message.user .message-time {
            color: rgba(255, 255, 255, 0.7);
        }

        .confidence {
            font-size: 11px;
            color: var(--saas-text-muted, #999);
            margin-top: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .confidence-bar {
            width: 60px;
            height: 4px;
            background: var(--saas-border-light, #e0e0e0);
            border-radius: 2px;
            overflow: hidden;
        }

        .confidence-fill {
            height: 100%;
            background: var(--saas-status-success, #22c55e);
            border-radius: 2px;
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
            font-size: 28px;
            margin-bottom: 20px;
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

        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 14px 18px;
            align-self: flex-start;
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 16px;
            border-bottom-left-radius: 4px;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            background: var(--saas-text-muted, #999);
            border-radius: 50%;
            animation: typing 1.4s infinite ease-in-out;
        }

        .typing-dot:nth-child(1) { animation-delay: 0s; }
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); opacity: 0.6; }
            30% { transform: translateY(-6px); opacity: 1; }
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }
    `;

    @property({ type: Array }) messages: ChatMessage[] = [];
    @property({ type: String }) streamContent = '';
    @property({ type: Boolean }) isStreaming = false;

    render() {
        if (this.messages.length === 0 && !this.isStreaming) {
            return this._renderEmptyState();
        }

        return html`
            ${this.messages.map((msg) => this._renderMessage(msg))}
            ${this.isStreaming ? this._renderStreamingMessage() : ''}
        `;
    }

    private _renderEmptyState() {
        return html`
            <div class="empty-state">
                <div class="empty-icon"><span class="material-symbols-outlined">chat</span></div>
                <div class="empty-title">Start a Conversation</div>
                <div class="empty-desc">
                    Ask me anything about your data, configurations, or system management.
                </div>
            </div>
        `;
    }

    private _renderMessage(msg: ChatMessage) {
        const time = new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        return html`
            <div class="message ${msg.role}">
                <div class="message-content" style="white-space: pre-wrap;">${msg.coordinate ?? msg.content}</div>
                <div class="message-time">${time}</div>
                ${msg.confidence != null ? html`
                    <div class="confidence">
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: ${msg.confidence * 100}%"></div>
                        </div>
                        <span>${Math.round(msg.confidence * 100)}%</span>
                    </div>
                ` : ''}
            </div>
        `;
    }

    private _renderStreamingMessage() {
        return html`
            <div class="message assistant">
                <div class="message-content" style="white-space: pre-wrap;">${this.streamContent}</div>
                <div class="message-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-chat-message-list': SaasChatMessageList;
    }
}
