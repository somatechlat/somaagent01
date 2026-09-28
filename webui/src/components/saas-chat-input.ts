/**
 * SomaAgent SaaS — Chat Input
 * Renders the message input, attach button, and send button.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, query } from 'lit/decorators.js';

@customElement('saas-chat-input')
export class SaasChatInput extends LitElement {
    static styles = css`
        :host {
            display: flex;
            width: 100%;
            max-width: 700px;
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 24px;
            padding: 8px;
            align-items: flex-end;
            gap: 8px;
            box-shadow: var(--saas-shadow-lg, 0 8px 24px rgba(0,0,0,0.1));
            transition: box-shadow 0.2s ease;
        }

        :host(:focus-within) {
            border-color: var(--saas-border-medium, #ccc);
            box-shadow: var(--saas-shadow-lg, 0 8px 24px rgba(0,0,0,0.1)), 0 0 0 2px rgba(0,0,0,0.05);
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

        .attach-btn {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: transparent;
            border: none;
            color: var(--saas-text-secondary, #666);
            font-size: 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.1s ease;
            flex-shrink: 0;
        }

        .attach-btn:hover:not(:disabled) {
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .attach-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .input-field {
            flex: 1;
            padding: 8px 4px;
        }

        .input-field textarea {
            width: 100%;
            padding: 4px 0;
            border: none;
            background: transparent;
            color: var(--saas-text-primary, #1a1a1a);
            font-family: inherit;
            font-size: 14px;
            resize: none;
            outline: none;
            max-height: 120px;
            line-height: 1.5;
        }

        .input-field textarea::placeholder {
            color: var(--saas-text-muted, #999);
        }

        .input-field textarea:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .voice-btn {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: transparent;
            border: none;
            color: var(--saas-text-secondary, #666);
            font-size: 18px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.1s ease;
            flex-shrink: 0;
        }

        .voice-btn:hover:not(:disabled) {
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .voice-btn.active {
            background: var(--saas-status-danger, #ef4444);
            color: white;
        }

        .send-btn {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #1a1a1a;
            border: none;
            color: white;
            font-size: 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.15s ease;
            flex-shrink: 0;
        }

        .send-btn:hover:not(:disabled) {
            background: #333;
            transform: scale(1.05);
        }

        .send-btn:disabled {
            background: var(--saas-border-light, #e0e0e0);
            color: var(--saas-text-muted, #999);
            cursor: not-allowed;
        }
    `;

    @property({ type: String }) value = '';
    @property({ type: Boolean }) disabled = false;
    @property({ type: Boolean }) isStreaming = false;

    @query('textarea') private _textarea!: HTMLTextAreaElement;

    render() {
        const canSend = this.value.trim() && !this.isStreaming && !this.disabled;

        return html`
            <button class="attach-btn" title="Attach file" ?disabled=${this.disabled}>
                <span class="material-symbols-outlined">attach_file</span>
            </button>
            <div class="input-field">
                <textarea
                    rows="1"
                    placeholder=${this.disabled ? 'Select an agent to start chatting' : 'Type your message...'}
                    .value=${this.value}
                    ?disabled=${this.disabled}
                    @input=${this._handleInput}
                    @keydown=${this._handleKeydown}
                ></textarea>
            </div>
            <button class="voice-btn" title="Voice input" ?disabled=${this.disabled}>
                <span class="material-symbols-outlined">mic</span>
            </button>
            <button
                class="send-btn"
                ?disabled=${!canSend}
                @click=${this._send}
                title="Send message"
            >
                <span class="material-symbols-outlined">arrow_forward</span>
            </button>
        `;
    }

    updated(changed: Map<string, unknown>) {
        super.updated(changed);
        if (changed.has('value') && !this.value && this._textarea) {
            this._textarea.style.height = 'auto';
        }
    }

    private _handleInput(e: Event) {
        const textarea = e.target as HTMLTextAreaElement;
        this.value = textarea.value;

        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';

        this.dispatchEvent(new CustomEvent('saas-input', {
            detail: this.value,
            bubbles: true,
            composed: true,
        }));
    }

    private _handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this._send();
        }
    }

    private _send() {
        const content = this.value.trim();
        if (!content || this.isStreaming || this.disabled) {
            return;
        }

        this.dispatchEvent(new CustomEvent('saas-send', {
            detail: content,
            bubbles: true,
            composed: true,
        }));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-chat-input': SaasChatInput;
    }
}
