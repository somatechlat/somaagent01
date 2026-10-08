/**
 * SOMA Glassmorphism Modal Component
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

@customElement('soma-glass-modal')
export class SomaGlassModal extends LitElement {
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
            padding: var(--soma-space-lg, 24px);
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
            background: var(--soma-glass-bg, rgba(18, 18, 18, 0.92));
            border: 1px solid var(--soma-glass-border, rgba(255, 255, 255, 0.12));
            border-radius: var(--soma-radius-xl, 16px);
            box-shadow: var(--soma-shadow-glass, 0 24px 64px rgba(0, 0, 0, 0.55));
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
            border-radius: var(--soma-radius-lg, 12px);
        }

        .header {
            padding: var(--soma-space-md, 16px) var(--soma-space-lg, 24px);
            border-bottom: 1px solid var(--soma-border-light, #e0e0e0);
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-shrink: 0;
        }

        .title {
            color: #FFFFFF;
            font-size: var(--soma-text-lg, 18px);
            font-weight: var(--soma-font-semibold, 600);
            color: var(--soma-text-primary, #1a1a1a);
            margin: 0;
        }

        .subtitle {
            font-size: var(--soma-text-sm, 13px);
            color: var(--soma-text-secondary, #666666);
            margin-top: 2px;
         color: #C4C4C4; }

        .close-btn {
            width: 36px;
            height: 36px;
            border-radius: var(--soma-radius-md, 8px);
            border: 1px solid var(--soma-border-light, #e0e0e0);
            background: var(--soma-bg-card, #ffffff);
            color: var(--soma-text-secondary, #666666);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            transition: all var(--soma-transition-fast, 150ms ease);
        }

        .close-btn:hover {
            background: var(--soma-bg-hover, #fafafa);
            color: var(--soma-text-primary, #1a1a1a);
            border-color: var(--soma-border-medium, #cccccc);
        }

        .body {
            flex: 1;
            padding: var(--soma-space-lg, 24px);
            overflow-y: auto;
            color: var(--soma-text-primary, #1a1a1a);
        }

        .body.no-padding {
            padding: 0;
        }

        .footer {
            padding: var(--soma-space-md, 16px) var(--soma-space-lg, 24px);
            border-top: 1px solid var(--soma-border-light, #e0e0e0);
            display: flex;
            gap: var(--soma-space-sm, 8px);
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
            background: var(--soma-border-medium, #cccccc);
            border-radius: 3px;
        }

        .body::-webkit-scrollbar-thumb:hover {
            background: var(--soma-text-muted, #999999);
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
                                    <span class="material-symbols-outlined">close</span>
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
        this.dispatchEvent(new CustomEvent('soma-modal-open', { bubbles: true, composed: true }));
    }

    /** Close the modal */
    close() {
        this.open = false;
        this.dispatchEvent(new CustomEvent('soma-modal-close', { bubbles: true, composed: true }));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-glass-modal': SomaGlassModal;
    }
}
