import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('soma-button')
export class SomaButton extends LitElement {
    static styles = css`
        :host {
            display: inline-block;
        }

        button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 10px 16px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            font-family: inherit;
            border: 1px solid transparent;
            background: var(--soma-button-bg, #3b82f6);
            color: var(--soma-button-text, #ffffff);
            width: 100%;
        }

        button:hover:not(:disabled) {
            opacity: 0.9;
            transform: translateY(-1px);
        }

        button:active:not(:disabled) {
            transform: translateY(0);
        }

        button.secondary {
            background: transparent;
            border: 1px solid var(--soma-border-color, #e2e8f0);
            color: var(--soma-text-main, #e2e8f0);
        }

        button.secondary:hover:not(:disabled) {
            background: rgba(255, 255, 255, 0.05);
            border-color: var(--soma-text-main, #e2e8f0);
        }

        button.danger {
            background: var(--soma-danger, #ef4444);
            color: white;
        }

        button.ghost {
            background: transparent;
            color: var(--soma-text-dim, #94a3b8);
        }

        button.ghost:hover:not(:disabled) {
            color: var(--soma-text-bright, #f8fafc);
            background: rgba(255, 255, 255, 0.05);
        }

        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
    `;

    @property() variant: 'primary' | 'secondary' | 'danger' | 'ghost' = 'primary';
    @property({ type: Boolean }) disabled = false;
    @property({ type: String }) type: 'button' | 'submit' | 'reset' = 'button';

    render() {
        return html`
            <button 
                class="${this.variant}" 
                ?disabled=${this.disabled}
                type=${this.type}
            >
                <slot name="icon"></slot>
                <slot></slot>
            </button>
        `;
    }
}
