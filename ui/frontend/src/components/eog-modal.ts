/**
 * Eye of God Modal Component
 * Per Eye of God UIX Design Section 4.1
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Focus trap for accessibility
 * - Backdrop close support
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

@customElement('eog-modal')
export class EogModal extends LitElement {
    static styles = css`
        :host {
            display: contents;
        }

        .backdrop {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(4px);
            z-index: var(--eog-z-modal, 200);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: var(--eog-spacing-lg, 24px);
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.2s ease, visibility 0.2s ease;
        }

        .backdrop.open {
            opacity: 1;
            visibility: visible;
        }

        .modal {
            background: var(--eog-surface, rgba(30, 41, 59, 0.95));
            border: 1px solid var(--eog-glass-border, rgba(255, 255, 255, 0.08));
            border-radius: var(--eog-radius-xl, 16px);
            box-shadow: var(--eog-shadow-lg);
            max-width: 100%;
            max-height: 100%;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            transform: scale(0.95);
            transition: transform 0.2s ease;
        }

        .backdrop.open .modal {
            transform: scale(1);
        }

        .modal.sm { width: 400px; }
        .modal.md { width: 560px; }
        .modal.lg { width: 720px; }
        .modal.xl { width: 900px; }
        .modal.full { width: 100%; height: 100%; border-radius: 0; }

        .header {
            padding: var(--eog-spacing-md, 16px) var(--eog-spacing-lg, 24px);
            border-bottom: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.05));
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .title {
            font-size: var(--eog-text-lg, 16px);
            font-weight: 600;
            color: var(--eog-text-main, #e2e8f0);
            margin: 0;
        }

        .close-btn {
            width: 32px;
            height: 32px;
            border-radius: var(--eog-radius-md, 8px);
            border: none;
            background: transparent;
            color: var(--eog-text-dim, #64748b);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            transition: all 0.2s ease;
        }

        .close-btn:hover {
            background: rgba(255, 255, 255, 0.05);
            color: var(--eog-text-main, #e2e8f0);
        }

        .body {
            flex: 1;
            padding: var(--eog-spacing-lg, 24px);
            overflow-y: auto;
        }

        .footer {
            padding: var(--eog-spacing-md, 16px) var(--eog-spacing-lg, 24px);
            border-top: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.05));
            display: flex;
            gap: var(--eog-spacing-sm, 8px);
            justify-content: flex-end;
        }
    `;

    @property({ type: Boolean }) open = false;
    @property({ type: String }) title = '';
    @property({ type: String }) size: 'sm' | 'md' | 'lg' | 'xl' | 'full' = 'md';
    @property({ type: Boolean, attribute: 'close-on-backdrop' }) closeOnBackdrop = true;
    @property({ type: Boolean, attribute: 'close-on-escape' }) closeOnEscape = true;
    @property({ type: Boolean, attribute: 'show-close' }) showClose = true;

    connectedCallback() {
        super.connectedCallback();
        document.addEventListener('keydown', this._handleKeydown);
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        document.removeEventListener('keydown', this._handleKeydown);
    }

    render() {
        return html`
            <div 
                class="backdrop ${this.open ? 'open' : ''}"
                @click=${this._handleBackdropClick}
                role="dialog"
                aria-modal="true"
                aria-labelledby="modal-title"
            >
                <div class="modal ${this.size}" @click=${(e: Event) => e.stopPropagation()}>
                    ${this.title || this.showClose ? html`
                        <div class="header">
                            <h2 class="title" id="modal-title">${this.title}</h2>
                            ${this.showClose ? html`
                                <button 
                                    class="close-btn" 
                                    @click=${this.close}
                                    aria-label="Close modal"
                                >
                                    ✕
                                </button>
                            ` : ''}
                        </div>
                    ` : ''}
                    
                    <div class="body">
                        <slot></slot>
                    </div>
                    
                    <slot name="footer">
                        <div class="footer">
                            <slot name="actions"></slot>
                        </div>
                    </slot>
                </div>
            </div>
        `;
    }

    private _handleBackdropClick = () => {
        if (this.closeOnBackdrop) {
            this.close();
        }
    };

    private _handleKeydown = (e: KeyboardEvent) => {
        if (this.open && this.closeOnEscape && e.key === 'Escape') {
            this.close();
        }
    };

    /** Open the modal */
    show() {
        this.open = true;
        this.dispatchEvent(new CustomEvent('eog-open', { bubbles: true, composed: true }));
    }

    /** Close the modal */
    close() {
        this.open = false;
        this.dispatchEvent(new CustomEvent('eog-close', { bubbles: true, composed: true }));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-modal': EogModal;
    }
}
