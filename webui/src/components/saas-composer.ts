/**
 * SomaAgent01 — Chat Composer
 * Auto-expanding textarea, "+" menu, action buttons
 */

import { LitElement, html, css } from 'lit';
import { customElement, state, query } from 'lit/decorators.js';
import { composerStore } from '../stores/composer-store.js';

@customElement('saas-composer')
export class SaasComposer extends LitElement {
    @state() private _input = '';
    @state() private _menuOpen = false;
    @state() private _isSending = false;
    @state() private _attachments = composerStore.state.attachments;

    @query('textarea') private _textarea!: HTMLTextAreaElement;

    static styles = css`
        :host {
            display: block;
            padding: 12px 20px 16px;
        }

        .composer {
            max-width: 720px;
            margin: 0 auto;
        }

        .input-row {
            display: flex;
            align-items: flex-end;
            gap: 8px;
            background: var(--aaas-bg-card, #1e1e1e);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            border-radius: var(--aaas-radius-xl, 16px);
            padding: 10px 14px;
            transition: border-color 200ms ease, box-shadow 200ms ease;
        }

        .input-row:focus-within {
            border-color: var(--aaas-border-medium, rgba(255,255,255,0.1));
            box-shadow: 0 0 0 3px rgba(232, 228, 220, 0.08);
        }

        .plus-btn {
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background: transparent;
            border: none;
            color: var(--aaas-text-muted, #6b6b6b);
            cursor: pointer;
            font-size: 18px;
            flex-shrink: 0;
            transition: all 150ms ease;
        }

        .plus-btn:hover {
            background: var(--aaas-bg-hover, #141414);
            color: var(--aaas-text-secondary, #a1a1a1);
        }

        .plus-btn.active {
            background: var(--aaas-bg-active, #1a1a1a);
            color: var(--aaas-accent, #e8e4dc);
            transform: rotate(45deg);
        }

        textarea {
            flex: 1;
            background: transparent;
            border: none;
            color: var(--aaas-text-primary, #ffffff);
            font-size: 14px;
            line-height: 1.5;
            resize: none;
            outline: none;
            min-height: 24px;
            max-height: 120px;
            padding: 4px 0;
            font-family: inherit;
        }

        textarea::placeholder {
            color: var(--aaas-text-muted, #6b6b6b);
        }

        .send-btn {
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background: var(--aaas-accent, #e8e4dc);
            border: none;
            color: var(--aaas-bg-void, #0a0a0a);
            cursor: pointer;
            font-size: 14px;
            flex-shrink: 0;
            transition: all 150ms ease;
        }

        .send-btn:hover {
            background: var(--aaas-accent-hover, #ffffff);
            transform: scale(1.05);
        }

        .send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        .actions-row {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin-top: 8px;
        }

        .action-btn {
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 5px 12px;
            border-radius: var(--aaas-radius-full, 9999px);
            background: transparent;
            border: 1px solid transparent;
            color: var(--aaas-text-muted, #6b6b6b);
            font-size: 12px;
            cursor: pointer;
            transition: all 150ms ease;
        }

        .action-btn:hover {
            background: var(--aaas-bg-hover, #141414);
            color: var(--aaas-text-secondary, #a1a1a1);
            border-color: var(--aaas-border-light, rgba(255,255,255,0.06));
        }

        .attachments {
            display: flex;
            gap: 6px;
            margin-bottom: 8px;
            flex-wrap: wrap;
        }

        .attachment-chip {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            background: var(--aaas-bg-hover, #141414);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            border-radius: var(--aaas-radius-md, 8px);
            font-size: 12px;
            color: var(--aaas-text-secondary, #a1a1a1);
        }

        .attachment-chip .remove {
            cursor: pointer;
            color: var(--aaas-text-muted, #6b6b6b);
            transition: color 150ms ease;
        }

        .attachment-chip .remove:hover {
            color: var(--aaas-danger, #ef4444);
        }
    `;

    connectedCallback() {
        super.connectedCallback();
        composerStore.subscribe(() => {
            this._attachments = composerStore.state.attachments;
        });
    }

    private _onInput() {
        this._input = this._textarea.value;
        this._adjustHeight();
    }

    private _adjustHeight() {
        this._textarea.style.height = 'auto';
        this._textarea.style.height = Math.min(this._textarea.scrollHeight, 120) + 'px';
    }

    private _onKeydown(e: KeyboardEvent) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this._send();
        }
    }

    private _send() {
        const text = this._input.trim();
        if (!text || this._isSending) return;
        this._isSending = true;
        this.dispatchEvent(new CustomEvent('send-message', { detail: { text, attachments: this._attachments } }));
        this._input = '';
        this._textarea.value = '';
        this._adjustHeight();
        composerStore.clearAttachments();
        this._isSending = false;
    }

    private _toggleMenu() {
        this._menuOpen = !this._menuOpen;
        composerStore.setMenuOpen(this._menuOpen);
    }

    render() {
        return html`
            <div class="composer">
                ${this._attachments.length > 0 ? html`
                    <div class="attachments">
                        ${this._attachments.map((file, i) => html`
                            <div class="attachment-chip">
                                <span>📎 ${file.name}</span>
                                <span class="remove" @click=${() => composerStore.removeAttachment(i)}>✕</span>
                            </div>
                        `)}
                    </div>
                ` : ''}

                <div class="input-row">
                    <button 
                        class="plus-btn ${this._menuOpen ? 'active' : ''}"
                        @click=${this._toggleMenu}
                        title="Menu"
                    >
                        +
                    </button>
                    <textarea
                        placeholder="Describe what you want the agent to do..."
                        .value=${this._input}
                        @input=${this._onInput}
                        @keydown=${this._onKeydown}
                        rows="1"
                    ></textarea>
                    <button 
                        class="send-btn"
                        @click=${this._send}
                        ?disabled=${!this._input.trim() || this._isSending}
                        title="Send"
                    >
                        ➤
                    </button>
                </div>

                ${this._menuOpen ? html`<saas-composer-menu></saas-composer-menu>` : ''}

                <div class="actions-row">
                    <button class="action-btn" @click=${() => {}}>🎤 Voice</button>
                    <button class="action-btn" @click=${() => {}}>Compact</button>
                    <button class="action-btn" @click=${() => {}}>⏸ Pause</button>
                    <button class="action-btn" @click=${() => {}}>👋 Nudge</button>
                </div>
            </div>
        `;
    }
}
