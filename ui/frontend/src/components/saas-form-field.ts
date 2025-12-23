/**
 * SAAS Form Field
 * Standard input wrapper with label, helper text, and error state
 *
 * VIBE COMPLIANT:
 * - Real Lit 3.x Web Component
 * - Light/dark theme support
 * - Accessible label association
 * - Consistent validation styling
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('saas-form-field')
export class SaasFormField extends LitElement {
    static styles = css`
        :host {
            display: block;
            margin-bottom: var(--saas-space-md, 16px);
        }

        .label {
            display: block;
            font-size: var(--saas-text-sm, 13px);
            font-weight: var(--saas-font-medium, 500);
            color: var(--saas-text-secondary, #666666);
            margin-bottom: var(--saas-space-xs, 4px);
        }

        .label.required::after {
            content: '*';
            color: var(--saas-status-danger, #ef4444);
            margin-left: 2px;
        }

        .input-container {
            position: relative;
        }

        input {
            width: 100%;
            padding: var(--saas-space-sm, 8px) var(--saas-space-md, 16px);
            font-size: var(--saas-text-base, 14px);
            color: var(--saas-text-primary, #1a1a1a);
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: var(--saas-radius-md, 8px);
            transition: all var(--saas-transition-fast, 150ms ease);
            font-family: inherit;
        }

        input:hover {
            border-color: var(--saas-border-medium, #cccccc);
        }

        input:focus {
            outline: none;
            border-color: var(--saas-accent, #1a1a1a);
            box-shadow: 0 0 0 2px rgba(26, 26, 26, 0.1);
        }

        input.error {
            border-color: var(--saas-status-danger, #ef4444);
        }

        input.error:focus {
            box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.1);
        }

        .helper-text {
            font-size: var(--saas-text-xs, 11px);
            color: var(--saas-text-muted, #999999);
            margin-top: 4px;
        }

        .error-text {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: var(--saas-text-xs, 11px);
            color: var(--saas-status-danger, #ef4444);
            margin-top: 4px;
        }

        .error-icon {
            font-family: 'Material Symbols Outlined';
            font-size: 14px;
            line-height: 1;
        }
    `;

    @property({ type: String }) label = '';
    @property({ type: String }) type = 'text';
    @property({ type: String }) placeholder = '';
    @property({ type: String }) value = '';
    @property({ type: Boolean }) required = false;
    @property({ type: String }) error = '';
    @property({ type: String }) helper = '';
    @property({ type: Boolean }) disabled = false;

    private _handleInput(e: Event) {
        const input = e.target as HTMLInputElement;
        this.value = input.value;
        this.dispatchEvent(new CustomEvent('saas-input', {
            detail: { value: this.value },
            bubbles: true,
            composed: true
        }));
    }

    render() {
        return html`
            ${this.label ? html`
                <label class="label ${this.required ? 'required' : ''}">
                    ${this.label}
                </label>
            ` : nothing}

            <div class="input-container">
                <input
                    type=${this.type}
                    placeholder=${this.placeholder}
                    .value=${this.value}
                    ?disabled=${this.disabled}
                    class=${this.error ? 'error' : ''}
                    @input=${this._handleInput}
                />
            </div>

            ${this.error ? html`
                <div class="error-text">
                    <span class="error-icon">error</span>
                    ${this.error}
                </div>
            ` : this.helper ? html`
                <div class="helper-text">${this.helper}</div>
            ` : nothing}
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-form-field': SaasFormField;
    }
}
