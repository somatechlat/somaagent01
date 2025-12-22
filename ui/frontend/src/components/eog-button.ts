/**
 * Eye of God Button Component
 * Per Eye of God UIX Design Section 4.1
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - CSS custom properties for theming
 * - ARIA support for accessibility
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('eog-button')
export class EogButton extends LitElement {
    static styles = css`
        :host {
            display: inline-block;
        }

        button {
            padding: var(--eog-spacing-sm, 8px) var(--eog-spacing-md, 16px);
            border-radius: var(--eog-radius-md, 8px);
            border: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.1));
            background: var(--eog-surface, rgba(30, 41, 59, 0.85));
            color: var(--eog-text-main, #e2e8f0);
            font-family: var(--eog-font-sans, 'Inter', sans-serif);
            font-size: var(--eog-text-sm, 13px);
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        button:hover:not(:disabled) {
            background: var(--eog-surface-hover, rgba(51, 65, 85, 0.9));
            border-color: var(--eog-border-hover, rgba(255, 255, 255, 0.2));
        }

        button:focus-visible {
            outline: 2px solid var(--eog-accent, #94a3b8);
            outline-offset: 2px;
        }

        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        button.primary {
            background: var(--eog-accent, #94a3b8);
            color: white;
            border-color: var(--eog-accent, #94a3b8);
        }

        button.primary:hover:not(:disabled) {
            filter: brightness(1.1);
        }

        button.danger {
            background: var(--eog-danger, #ef4444);
            color: white;
            border-color: var(--eog-danger, #ef4444);
        }

        button.ghost {
            background: transparent;
            border-color: transparent;
        }

        button.ghost:hover:not(:disabled) {
            background: rgba(255, 255, 255, 0.05);
        }

        .spinner {
            width: 14px;
            height: 14px;
            border: 2px solid currentColor;
            border-right-color: transparent;
            border-radius: 50%;
            animation: spin 0.75s linear infinite;
        }

        @keyframes spin {
            to {
                transform: rotate(360deg);
            }
        }
    `;

    @property({ type: String }) variant: 'default' | 'primary' | 'danger' | 'ghost' = 'default';
    @property({ type: Boolean }) disabled = false;
    @property({ type: Boolean }) loading = false;
    @property({ type: String }) type: 'button' | 'submit' | 'reset' = 'button';

    render() {
        return html`
            <button
                type=${this.type}
                class=${this.variant}
                ?disabled=${this.disabled || this.loading}
                @click=${this._handleClick}
                aria-busy=${this.loading}
            >
                ${this.loading ? html`<span class="spinner" aria-hidden="true"></span>` : ''}
                <slot></slot>
            </button>
        `;
    }

    private _handleClick(e: Event) {
        if (!this.disabled && !this.loading) {
            this.dispatchEvent(new CustomEvent('eog-click', {
                bubbles: true,
                composed: true,
                detail: { originalEvent: e }
            }));
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-button': EogButton;
    }
}
