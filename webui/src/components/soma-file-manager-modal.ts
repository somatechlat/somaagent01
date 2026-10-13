/**
 * soma-file-manager-modal — full-screen file manager (product: Files).
 * Takes the whole window: tree · list · preview · upload · folder ops.
 * Material Symbols only — no emojis.
 */
import { LitElement, css, html, nothing } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import './soma-file-manager.js';

@customElement('soma-file-manager-modal')
export class SomaFileManagerModal extends LitElement {
    @property({ type: Boolean, reflect: true }) open = false;

    static styles = css`
        :host {
            display: none;
            position: fixed;
            inset: 0;
            z-index: 400;
        }
        :host([open]) {
            display: block;
        }
        .scrim {
            position: absolute;
            inset: 0;
            background: color-mix(in srgb, var(--skin-color-bg-void, #000) 45%, transparent);
            backdrop-filter: blur(6px);
            -webkit-backdrop-filter: blur(6px);
        }
        .sheet {
            position: absolute;
            inset: 16px;
            display: flex;
            flex-direction: column;
            background: var(--skin-color-bg-base, #fff);
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.1));
            border-radius: var(--skin-radius-xl, 16px);
            box-shadow: var(--skin-shadow-overlay, 0 16px 48px rgba(0, 0, 0, 0.25));
            overflow: hidden;
            font-family: var(--skin-font-sans, system-ui, sans-serif);
            color: var(--skin-color-text-primary, #1a1a1a);
        }
        .bar {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px 18px;
            border-bottom: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
            background: color-mix(in srgb, var(--skin-color-bg-card, #fff) 90%, transparent);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
        }
        .bar h2 {
            margin: 0;
            font-size: 15px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .bar h2 .material-symbols-outlined {
            color: var(--skin-color-accent, #FF4D00);
        }
        .spacer {
            flex: 1;
        }
        .close {
            width: 36px;
            height: 36px;
            border: none;
            border-radius: 50%;
            background: var(--skin-color-bg-hover, #f0f0f0);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--skin-color-text-primary, #1a1a1a);
        }
        .close:hover {
            background: var(--skin-color-bg-active, #e5e5e5);
        }
        .body {
            flex: 1;
            min-height: 0;
            overflow: hidden;
            display: flex;
        }
        .body soma-file-manager {
            flex: 1;
            min-width: 0;
            height: 100%;
            overflow: auto;
            --fm-panel-height: 100%;
        }
        .drop {
            position: absolute;
            inset: 16px;
            border: 2px dashed transparent;
            border-radius: var(--skin-radius-xl, 16px);
            pointer-events: none;
            z-index: 1;
        }
        .drop.on {
            border-color: var(--skin-color-accent, #FF4D00);
            background: color-mix(in srgb, var(--skin-color-accent, #FF4D00) 10%, transparent);
        }
    `;

    private _dragging = false;

    private _close(): void {
        this.open = false;
        this.dispatchEvent(new CustomEvent('close', { bubbles: true, composed: true }));
    }

    override render() {
        if (!this.open) return nothing;
        return html`
            <div class="scrim" @click=${() => this._close()}></div>
            <div
                class="sheet"
                role="dialog"
                aria-modal="true"
                aria-label="File manager"
                @dragover=${(e: DragEvent) => {
                    e.preventDefault();
                    this._dragging = true;
                    this.requestUpdate();
                }}
                @dragleave=${() => {
                    this._dragging = false;
                    this.requestUpdate();
                }}
                @drop=${(e: DragEvent) => {
                    e.preventDefault();
                    this._dragging = false;
                    this.requestUpdate();
                    const files = e.dataTransfer?.files;
                    if (files && files.length > 0) {
                        this.dispatchEvent(
                            new CustomEvent('soma-drop-files', {
                                detail: { files: Array.from(files) },
                                bubbles: true,
                                composed: true,
                            }),
                        );
                    }
                }}
            >
                <div class="drop ${this._dragging ? 'on' : ''}"></div>
                <div class="bar">
                    <h2>
                        <span class="material-symbols-outlined">folder_open</span>
                        Files
                    </h2>
                    <div class="spacer"></div>
                    <button class="close" aria-label="Close file manager" @click=${() => this._close()}>
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                <div class="body">
                    <soma-file-manager mode="manage" show-upload></soma-file-manager>
                </div>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-file-manager-modal': SomaFileManagerModal;
    }
}
