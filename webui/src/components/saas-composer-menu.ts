/**
 * SomaAgent01 — Composer "+" Menu
 * Attachments (composerStore), Memory Context, Clear, Export
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { composerStore } from '../stores/composer-store.js';

@customElement('saas-composer-menu')
export class SaasComposerMenu extends LitElement {
    @state() private _notice = '';

    static styles = css`
        :host {
            display: block;
            position: relative;
            z-index: 100;
        }

        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: 18px;
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

        .menu {
            position: absolute;
            bottom: calc(100% + 8px);
            left: 0;
            min-width: 220px;
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
            border: none;
            background: transparent;
            width: 100%;
            text-align: left;
            font-family: inherit;
        }

        .menu-item:hover {
            background: var(--aaas-bg-hover, #141414);
            color: var(--aaas-text-primary, #ffffff);
        }

        .menu-item:focus-visible {
            outline: 2px solid var(--aaas-info, #3b82f6);
            outline-offset: -1px;
        }

        .menu-item .icon {
            width: 20px;
            text-align: center;
            flex-shrink: 0;
        }

        .menu-divider {
            height: 1px;
            background: var(--aaas-border-light, rgba(255,255,255,0.06));
            margin: 4px 0;
        }

        input[type='file'] {
            display: none;
        }

        .notice {
            padding: 6px 12px;
            font-size: 11px;
            color: var(--aaas-text-muted, #999999);
        }

        .notice.error {
            color: var(--aaas-danger, #ef4444);
        }
    `;

    private _onFileSelect(e: Event) {
        const input = e.target as HTMLInputElement;
        if (input.files) {
            Array.from(input.files).forEach((f) => composerStore.addAttachment(f));
            this._notice = '';
        } else {
            this._notice = 'No files selected';
        }
        input.value = '';
    }

    private _clearChat() {
        this.dispatchEvent(new CustomEvent('clear-chat', {
            bubbles: true,
            composed: true,
        }));
    }

    private _exportChat() {
        this.dispatchEvent(new CustomEvent('export-chat', {
            bubbles: true,
            composed: true,
        }));
    }

    private _navigate(path: string) {
        window.dispatchEvent(new CustomEvent('saas-navigate', {
            detail: { route: path },
        }));
    }

    render() {
        return html`
            <div class="menu" role="menu">
                <label class="menu-item" role="menuitem">
                    <span class="material-symbols-outlined icon">attach_file</span>
                    <span>Attach Files</span>
                    <input type="file" multiple @change=${this._onFileSelect} />
                </label>
                <button type="button" class="menu-item" role="menuitem" @click=${() => this._navigate('/memory')}>
                    <span class="material-symbols-outlined icon">psychology</span>
                    <span>Memory Context</span>
                </button>
                <!--
                    Skills was a misroute: it sent people to /settings, which is
                    not a skills surface. There is no skills registry API in this
                    deployment (no /skills router in admin/api.py) and no screen
                    in SOMA-01-UIUX-001, so a picker here would be fabricated.
                    composerStore.activeSkills has no server-backed catalog to
                    read, so the entry is removed rather than shipped as a lie.
                -->
                <div class="menu-divider"></div>
                <button type="button" class="menu-item" role="menuitem" @click=${this._clearChat}>
                    <span class="material-symbols-outlined icon">delete_sweep</span>
                    <span>Clear Chat</span>
                </button>
                <button type="button" class="menu-item" role="menuitem" @click=${this._exportChat}>
                    <span class="material-symbols-outlined icon">download</span>
                    <span>Export Chat</span>
                </button>
                ${this._notice ? html`<div class="notice ${this._notice.includes('fail') || this._notice.includes('No') ? 'error' : ''}">${this._notice}</div>` : nothing}
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-composer-menu': SaasComposerMenu;
    }
}
