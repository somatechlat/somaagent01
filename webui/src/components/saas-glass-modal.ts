/**
 * SAAS Glassmorphism Modal Component
 * Beautiful translucent modal with backdrop blur
 *
 * VIBE COMPLIANT:
 * - Real Lit 3.x implementation
 * - Glassmorphism effect with backdrop-filter
 * - Light/dark theme adaptive
 * - Accessible with focus trap and escape close
 * - Multiple sizes: sm, md, lg, xl, full
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

export type ModalSize = 'sm' | 'md' | 'lg' | 'xl' | 'full';

@customElement('saas-glass-modal')
export class SaasGlassModal extends LitElement {
    static styles = css`
        :host {
            display: contents;
        }

        .backdrop {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            z-index: 200;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: var(--saas-space-lg, 24px);
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.25s ease, visibility 0.25s ease;
        }

        .backdrop.open {
            opacity: 1;
            visibility: visible;
        }

        /* Dark mode backdrop */
        [data-theme="dark"] .backdrop,
        .dark-theme .backdrop {
            background: rgba(0, 0, 0, 0.6);
        }

        .modal {
            background: var(--saas-glass-bg, rgba(255, 255, 255, 0.85));
            border: 1px solid var(--saas-glass-border, rgba(0, 0, 0, 0.08));
            border-radius: var(--saas-radius-xl, 16px);
            box-shadow: var(--saas-shadow-glass, 0 8px 32px rgba(0, 0, 0, 0.08));
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            max-width: 100%;
            max-height: calc(100vh - 48px);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            transform: scale(0.95) translateY(10px);
            transition: transform 0.25s ease;
        }

        .backdrop.open .modal {
            transform: scale(1) translateY(0);
        }

        /* Size variants */
        .modal.sm { width: 400px; }
        .modal.md { width: 560px; }
        .modal.lg { width: 720px; }
        .modal.xl { width: 960px; }
        .modal.full { 
            width: calc(100vw - 48px); 
            height: calc(100vh - 48px); 
            border-radius: var(--saas-radius-lg, 12px);
        }

        .header {
            padding: var(--saas-space-md, 16px) var(--saas-space-lg, 24px);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-shrink: 0;
        }

        .title {
            font-size: var(--saas-text-lg, 18px);
            font-weight: var(--saas-font-semibold, 600);
            color: var(--saas-text-primary, #1a1a1a);
            margin: 0;
        }

        .subtitle {
            font-size: var(--saas-text-sm, 13px);
            color: var(--saas-text-secondary, #666666);
            margin-top: 2px;
        }

        .close-btn {
            width: 36px;
            height: 36px;
            border-radius: var(--saas-radius-md, 8px);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            background: var(--saas-bg-card, #ffffff);
            color: var(--saas-text-secondary, #666666);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            transition: all var(--saas-transition-fast, 150ms ease);
        }

        .close-btn:hover {
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-text-primary, #1a1a1a);
            border-color: var(--saas-border-medium, #cccccc);
        }

        .body {
            flex: 1;
            padding: var(--saas-space-lg, 24px);
            overflow-y: auto;
            color: var(--saas-text-primary, #1a1a1a);
        }

        .body.no-padding {
            padding: 0;
        }

        .footer {
            padding: var(--saas-space-md, 16px) var(--saas-space-lg, 24px);
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            gap: var(--saas-space-sm, 8px);
            justify-content: flex-end;
            flex-shrink: 0;
        }

        /* Scrollbar styling */
        .body::-webkit-scrollbar {
            width: 6px;
        }

        .body::-webkit-scrollbar-track {
            background: transparent;
        }

        .body::-webkit-scrollbar-thumb {
            background: var(--saas-border-medium, #cccccc);
            border-radius: 3px;
        }

        .body::-webkit-scrollbar-thumb:hover {
            background: var(--saas-text-muted, #999999);
        }
    `;

    @property({ type: Boolean, reflect: true }) open = false;
    @property({ type: String }) title = '';
    @property({ type: String }) subtitle = '';
    @property({ type: String }) size: ModalSize = 'md';
    @property({ type: Boolean, attribute: 'close-on-backdrop' }) closeOnBackdrop = true;
    @property({ type: Boolean, attribute: 'close-on-escape' }) closeOnEscape = true;
    @property({ type: Boolean, attribute: 'show-close' }) showClose = true;
    @property({ type: Boolean, attribute: 'no-padding' }) noPadding = false;

    private _handleKeydown = (e: KeyboardEvent) => {
        if (this.open && this.closeOnEscape && e.key === 'Escape') {
            e.preventDefault();
            this.close();
        }
    };

    connectedCallback() {
        super.connectedCallback();
        document.addEventListener('keydown', this._handleKeydown);
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        document.removeEventListener('keydown', this._handleKeydown);
    }

    updated(changedProperties: Map<string, unknown>) {
        if (changedProperties.has('open')) {
            if (this.open) {
                document.body.style.overflow = 'hidden';
            } else {
                document.body.style.overflow = '';
            }
        }
    }

    render() {
        return html`
            <div 
                class="backdrop ${this.open ? 'open' : ''}"
                @click=${this._handleBackdropClick}
                role="dialog"
                aria-modal="true"
                aria-labelledby="modal-title"
                aria-hidden=${!this.open}
            >
                <div class="modal ${this.size}" @click=${(e: Event) => e.stopPropagation()}>
                    ${this.title || this.showClose ? html`
                        <header class="header">
                            <div>
                                <h2 class="title" id="modal-title">${this.title}</h2>
                                ${this.subtitle ? html`<p class="subtitle">${this.subtitle}</p>` : ''}
                            </div>
                            ${this.showClose ? html`
                                <button 
                                    class="close-btn" 
                                    @click=${this.close}
                                    aria-label="Close modal"
                                >
                                    ✕
                                </button>
                            ` : ''}
                        </header>
                    ` : ''}
                    
                    <div class="body ${this.noPadding ? 'no-padding' : ''}">
                        <slot></slot>
                    </div>
                    
                    <slot name="footer">
                        ${this._hasFooterSlot() ? html`
                            <footer class="footer">
                                <slot name="actions"></slot>
                            </footer>
                        ` : ''}
                    </slot>
                </div>
            </div>
        `;
    }

    private _hasFooterSlot(): boolean {
        return this.querySelector('[slot="actions"]') !== null;
    }

    private _handleBackdropClick = () => {
        if (this.closeOnBackdrop) {
            this.close();
        }
    };

    /** Open the modal */
    show() {
        this.open = true;
        this.dispatchEvent(new CustomEvent('saas-modal-open', { bubbles: true, composed: true }));
    }

    /** Close the modal */
    close() {
        this.open = false;
        this.dispatchEvent(new CustomEvent('saas-modal-close', { bubbles: true, composed: true }));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-glass-modal': SaasGlassModal;
    }
}
