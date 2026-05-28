/**
 * SomaAgent01 — Composer "+" Menu
 * Attachments, Memory, Skills, History, Clear, Export
 */

import { LitElement, html, css } from 'lit';
import { customElement } from 'lit/decorators.js';
import { consume } from '@lit/context';
import { composerContext, ComposerStore } from '../stores/composer-store.js';

interface MenuItem {
    icon: string;
    label: string;
    action: () => void;
    divider?: boolean;
}

@customElement('saas-composer-menu')
export class SaasComposerMenu extends LitElement {
    @consume({ context: composerContext })
    composerStore!: ComposerStore;

    static styles = css`
        :host {
            display: block;
            position: relative;
            z-index: 100;
        }

        .menu {
            position: absolute;
            bottom: calc(100% + 8px);
            left: 0;
            min-width: 200px;
            background: var(--aaas-bg-card, #1e1e1e);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            border-radius: var(--aaas-radius-lg, 12px);
            padding: 6px;
            box-shadow: var(--aaas-shadow-lg, 0 8px 24px rgba(0,0,0,0.6));
            animation: menuIn 150ms ease-out;
        }

        @keyframes menuIn {
            from { opacity: 0; transform: translateY(4px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .menu-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 9px 12px;
            border-radius: var(--aaas-radius-md, 8px);
            cursor: pointer;
            font-size: 13px;
            color: var(--aaas-text-secondary, #a1a1a1);
            transition: all 100ms ease;
        }

        .menu-item:hover {
            background: var(--aaas-bg-hover, #141414);
            color: var(--aaas-text-primary, #ffffff);
        }

        .menu-item .icon {
            font-size: 15px;
            width: 20px;
            text-align: center;
        }

        .menu-divider {
            height: 1px;
            background: var(--aaas-border-light, rgba(255,255,255,0.06));
            margin: 4px 0;
        }

        input[type="file"] {
            display: none;
        }
    `;

    private _onFileSelect(e: Event) {
        const input = e.target as HTMLInputElement;
        if (input.files) {
            Array.from(input.files).forEach(f => this.composerStore.addAttachment(f));
        }
    }

    private _clearChat() {
        if (confirm('Clear all messages in this conversation?')) {
            window.dispatchEvent(new CustomEvent('clear-chat'));
        }
    }

    render() {
        return html`
            <div class="menu">
                <label class="menu-item">
                    <span class="icon">📎</span>
                    <span>Attach Files</span>
                    <input type="file" multiple @change=${this._onFileSelect} />
                </label>
                <div class="menu-item" @click=${() => {}}>
                    <span class="icon">🧠</span>
                    <span>Memory Context</span>
                </div>
                <div class="menu-item" @click=${() => {}}>
                    <span class="icon">🎯</span>
                    <span>Skills</span>
                </div>
                <div class="menu-item" @click=${() => {}}>
                    <span class="icon">📜</span>
                    <span>History</span>
                </div>
                <div class="menu-divider"></div>
                <div class="menu-item" @click=${this._clearChat}>
                    <span class="icon">🗑</span>
                    <span>Clear Chat</span>
                </div>
                <div class="menu-item" @click=${() => {}}>
                    <span class="icon">📤</span>
                    <span>Export Chat</span>
                </div>
            </div>
        `;
    }
}
