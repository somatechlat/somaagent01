/**
 * SomaAgent01 — Chat Workspace Wrapper
 * Embeds existing saas-chat functionality within the workspace layout
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

@customElement('saas-chat-workspace')
export class SaasChatWorkspace extends LitElement {
    @state() private _hasConversation = false;
    @state() private _messages: Array<{role: string; content: string}> = [];

    static styles = css`
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
        :host {
            display: flex;
            flex-direction: column;
            flex: 1;
            min-height: 0;
            background: var(--aaas-bg-void, #0a0a0a);
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

        .message {
            display: flex;
            gap: 12px;
            max-width: 85%;
        }

        .message.user {
            align-self: flex-end;
            flex-direction: row-reverse;
        }

        .message-bubble {
            padding: 12px 16px;
            border-radius: var(--aaas-radius-lg, 12px);
            font-size: 14px;
            line-height: 1.6;
            word-wrap: break-word;
        }

        .message.user .message-bubble {
            background: var(--aaas-bg-active, #1a1a1a);
            color: var(--aaas-text-primary, #ffffff);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            border-bottom-right-radius: 4px;
        }

        .message.assistant .message-bubble {
            background: var(--aaas-bg-card, #1e1e1e);
            color: var(--aaas-text-primary, #ffffff);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            border-bottom-left-radius: 4px;
        }

        .message-avatar {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            flex-shrink: 0;
            background: var(--aaas-bg-hover, #141414);
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
            background: var(--aaas-text-muted, #6b6b6b);
            animation: typingBounce 1.4s ease-in-out infinite;
        }

        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typingBounce {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-6px); }
        }

        .confidence-bar {
            height: 3px;
            background: var(--aaas-bg-hover, #141414);
            border-radius: var(--aaas-radius-full, 9999px);
            margin-top: 8px;
            overflow: hidden;
        }

        .confidence-fill {
            height: 100%;
            border-radius: var(--aaas-radius-full, 9999px);
            transition: width 500ms ease;
        }
    `;

    connectedCallback() {
        super.connectedCallback();
        this.addEventListener('send-message', ((e: CustomEvent) => {
            this._hasConversation = true;
            this._messages.push({ role: 'user', content: e.detail.text });
            this.requestUpdate();
        }) as EventListener);

        this.addEventListener('clear-chat', () => {
            this._messages = [];
            this._hasConversation = false;
            this.requestUpdate();
        });

        this.addEventListener('new-conversation', () => {
            this._messages = [];
            this._hasConversation = true;
            this.requestUpdate();
        });
    }

    render() {
        if (!this._hasConversation && this._messages.length === 0) {
            return html`
                <div style="flex:1;overflow:auto;">
                    <saas-welcome-dashboard></saas-welcome-dashboard>
                </div>
                <saas-composer></saas-composer>
            `;
        }

        return html`
            <div class="chat-area">
                <div class="messages">
                    ${this._messages.map(m => html`
                        <div class="message ${m.role}">
                            <div class="message-avatar">${m.role === 'user' ? html`<span class='material-symbols-outlined'>person</span>` : html`<span class='material-symbols-outlined'>smart_toy</span>`}</div>
                            <div class="message-bubble">
                                ${m.content}
                            </div>
                        </div>
                    `)}
                    <div class="typing-indicator" style="display:none">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            </div>
            <saas-composer></saas-composer>
        `;
    }
}
