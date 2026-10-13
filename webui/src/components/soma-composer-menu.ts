/**
 * SomaAgent01 — Composer "+" Menu
 * Attach files ONLY (operator). Closes after pick. No memory/export/clear items.
 */
import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { composerStore } from '../stores/composer-store.js';

@customElement('soma-composer-menu')
export class SomaComposerMenu extends LitElement {
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
            display: inline-block;
            white-space: nowrap;
        }

        .menu {
            position: absolute;
            bottom: calc(100% + 8px);
            left: 0;
            min-width: 200px;
            background: var(--skin-color-bg-card, var(--platform-bg-card, #fff));
            border: 1px solid var(--skin-color-border, var(--platform-border-light, rgba(0,0,0,.08)));
            border-radius: var(--skin-radius-lg, 12px);
            padding: 6px;
            box-shadow: var(--skin-shadow-md, 0 8px 24px rgba(0,0,0,.12));
        }

        .menu-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            border-radius: var(--skin-radius-md, 8px);
            cursor: pointer;
            font-size: 13px;
            color: var(--skin-color-text-primary, #1a1a1a);
            border: none;
            background: transparent;
            width: 100%;
            text-align: left;
            font-family: inherit;
        }

        .menu-item:hover {
            background: var(--skin-color-bg-hover, #f5f5f5);
        }

        .menu-item:focus-visible {
            outline: 2px solid var(--skin-focus-ring, var(--skin-color-accent, #FF4D00));
            outline-offset: -1px;
        }

        input[type='file'] {
            display: none;
        }

        .notice {
            padding: 6px 12px;
            font-size: 11px;
            color: var(--skin-color-text-secondary, #666);
        }

        .notice.error {
            color: var(--skin-color-danger, #ef4444);
        }
    `;

    private _close() {
        this.dispatchEvent(new CustomEvent('soma-menu-close', {
            bubbles: true,
            composed: true,
        }));
    }

    private _onFileSelect(e: Event) {
        const input = e.target as HTMLInputElement;
        if (input.files && input.files.length > 0) {
            Array.from(input.files).forEach((f) => composerStore.addAttachment(f));
            this._notice = '';
            // Close the menu as soon as files are chosen — upload runs from chips.
            this._close();
        } else {
            this._notice = 'No files selected';
        }
        input.value = '';
    }

    render() {
        return html`
            <div class="menu" role="menu">
                <label class="menu-item" role="menuitem" title="Upload files">
                    <span class="material-symbols-outlined icon">attach_file</span>
                    <span>Upload files</span>
                    <input type="file" multiple @change=${this._onFileSelect} />
                </label>
                ${this._notice
                    ? html`<div class="notice error" role="alert">${this._notice}</div>`
                    : nothing}
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-composer-menu': SomaComposerMenu;
    }
}
