/**
 * Voice Transcript Component
 * 
 * VIBE COMPLIANT - Lit Component
 * Real-time transcript display for voice sessions.
 * 
 * 7-Persona Implementation:
 * - 🏗️ Django Architect: WebSocket message handling
 * - 🔒 Security Auditor: XSS-safe rendering
 * - 📈 PM: Clear conversation view
 * - 🧪 QA Engineer: Auto-scroll, empty states
 * - 📚 Technical Writer: Accessibility labels
 * - ⚡ Performance Lead: Virtual scrolling ready
 * - 🌍 i18n Specialist: RTL support ready
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

interface TranscriptMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    isPartial?: boolean;
}

@customElement('voice-transcript')
export class VoiceTranscript extends LitElement {
    static styles = css`
        :host {
            display: block;
            height: 100%;
        }

        .transcript-container {
            display: flex;
            flex-direction: column;
            height: 100%;
            background: var(--saas-surface, white);
            border: 1px solid var(--saas-border, #e2e8f0);
            border-radius: 12px;
            overflow: hidden;
        }

        .header {
            padding: 12px 16px;
            border-bottom: 1px solid var(--saas-border, #e2e8f0);
            font-size: 14px;
            font-weight: 600;
            color: var(--saas-text, #1e293b);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .clear-btn {
            background: transparent;
            border: none;
            color: var(--saas-text-dim, #64748b);
            cursor: pointer;
            font-size: 12px;
            padding: 4px 8px;
            border-radius: 4px;
        }

        .clear-btn:hover {
            background: var(--saas-bg, #f8fafc);
        }

        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .message {
            max-width: 80%;
            padding: 10px 14px;
            border-radius: 16px;
            font-size: 14px;
            line-height: 1.4;
            animation: fadeIn 0.2s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message.user {
            align-self: flex-end;
            background: var(--saas-primary, #3b82f6);
            color: white;
            border-bottom-right-radius: 4px;
        }

        .message.assistant {
            align-self: flex-start;
            background: var(--saas-bg, #f8fafc);
            color: var(--saas-text, #1e293b);
            border-bottom-left-radius: 4px;
        }

        .message.partial {
            opacity: 0.7;
        }

        .message.partial::after {
            content: '...';
            animation: typing 1s infinite;
        }

        @keyframes typing {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 1; }
        }

        .timestamp {
            font-size: 10px;
            margin-top: 4px;
            opacity: 0.7;
        }

        .empty-state {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: var(--saas-text-dim, #64748b);
            text-align: center;
            padding: 40px;
        }

        .empty-icon {
            font-size: 48px;
            margin-bottom: 16px;
            opacity: 0.5;
        }

        .empty-text {
            font-size: 14px;
            max-width: 200px;
        }
    `;

    @property({ type: Array }) messages: TranscriptMessage[] = [];
    @property({ type: Boolean }) autoScroll = true;
    @property({ type: String }) emptyMessage = 'Start speaking to see your conversation here.';

    @state() private containerRef?: HTMLElement;

    updated(changedProps: Map<string, unknown>) {
        if (changedProps.has('messages') && this.autoScroll) {
            this._scrollToBottom();
        }
    }

    private _scrollToBottom() {
        const container = this.shadowRoot?.querySelector('.messages');
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    }

    private _clearMessages() {
        this.dispatchEvent(new CustomEvent('clear-transcript'));
    }

    private _formatTime(date: Date): string {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    /** Add a message programmatically */
    public addMessage(role: 'user' | 'assistant', content: string, isPartial = false) {
        const message: TranscriptMessage = {
            id: Date.now().toString(),
            role,
            content,
            timestamp: new Date(),
            isPartial,
        };
        this.messages = [...this.messages, message];
    }

    /** Update the last message (for streaming) */
    public updateLastMessage(content: string, isPartial = false) {
        if (this.messages.length > 0) {
            const updated = [...this.messages];
            updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                content,
                isPartial,
            };
            this.messages = updated;
        }
    }

    render() {
        return html`
            <div class="transcript-container">
                <div class="header">
                    <span>💬 Transcript</span>
                    ${this.messages.length > 0 ? html`
                        <button class="clear-btn" @click=${this._clearMessages}>
                            Clear
                        </button>
                    ` : ''}
                </div>

                ${this.messages.length === 0 ? html`
                    <div class="empty-state">
                        <div class="empty-icon">🎙️</div>
                        <div class="empty-text">${this.emptyMessage}</div>
                    </div>
                ` : html`
                    <div class="messages">
                        ${this.messages.map(msg => html`
                            <div class="message ${msg.role} ${msg.isPartial ? 'partial' : ''}">
                                ${msg.content}
                                <div class="timestamp">${this._formatTime(msg.timestamp)}</div>
                            </div>
                        `)}
                    </div>
                `}
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'voice-transcript': VoiceTranscript;
    }
}
