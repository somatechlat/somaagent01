/**
 * Eye of God Input Component
 * Per Eye of God UIX Design Section 4.1
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Validation support
 * - ARIA accessibility
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

@customElement('eog-input')
export class EogInput extends LitElement {
    static styles = css`
        :host {
            display: block;
        }

        .input-wrapper {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        label {
            font-size: var(--eog-text-sm, 13px);
            font-weight: 600;
            color: var(--eog-text-main, #e2e8f0);
        }

        .input-container {
            position: relative;
            display: flex;
            align-items: center;
        }

        input {
            width: 100%;
            padding: var(--eog-spacing-sm, 8px) var(--eog-spacing-md, 16px);
            border-radius: var(--eog-radius-md, 8px);
            border: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.1));
            background: var(--eog-input-bg, rgba(15, 23, 42, 0.8));
            color: var(--eog-text-main, #e2e8f0);
            font-family: var(--eog-font-sans);
            font-size: var(--eog-text-base, 14px);
            outline: none;
            transition: all 0.2s ease;
        }

        input::placeholder {
            color: var(--eog-text-dim, #64748b);
        }

        input:focus {
            border-color: var(--eog-accent, #94a3b8);
            box-shadow: 0 0 0 2px rgba(148, 163, 184, 0.2);
        }

        input:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        input.error {
            border-color: var(--eog-danger, #ef4444);
        }

        input.error:focus {
            box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.2);
        }

        .prefix, .suffix {
            position: absolute;
            color: var(--eog-text-dim, #64748b);
            pointer-events: none;
        }

        .prefix {
            left: 12px;
        }

        .suffix {
            right: 12px;
        }

        input.has-prefix {
            padding-left: 36px;
        }

        input.has-suffix {
            padding-right: 36px;
        }

        .error-message {
            font-size: var(--eog-text-xs, 11px);
            color: var(--eog-danger, #ef4444);
        }

        .hint {
            font-size: var(--eog-text-xs, 11px);
            color: var(--eog-text-dim, #64748b);
        }
    `;

    @property({ type: String }) label = '';
    @property({ type: String }) placeholder = '';
    @property({ type: String }) value = '';
    @property({ type: String }) type: 'text' | 'email' | 'password' | 'number' | 'search' = 'text';
    @property({ type: Boolean }) disabled = false;
    @property({ type: Boolean }) required = false;
    @property({ type: String }) error = '';
    @property({ type: String }) hint = '';
    @property({ type: String }) prefix = '';
    @property({ type: String }) suffix = '';
    @property({ type: String }) pattern = '';
    @property({ type: Number }) maxlength?: number;
    @property({ type: Number }) minlength?: number;

    @state() private _focused = false;

    render() {
        const inputClasses = [
            this.error ? 'error' : '',
            this.prefix ? 'has-prefix' : '',
            this.suffix ? 'has-suffix' : '',
        ].filter(Boolean).join(' ');

        return html`
            <div class="input-wrapper">
                ${this.label ? html`
                    <label for="input">
                        ${this.label}
                        ${this.required ? html`<span style="color: var(--eog-danger)">*</span>` : ''}
                    </label>
                ` : ''}
                
                <div class="input-container">
                    ${this.prefix ? html`<span class="prefix">${this.prefix}</span>` : ''}
                    
                    <input
                        id="input"
                        type=${this.type}
                        class=${inputClasses}
                        .value=${this.value}
                        placeholder=${this.placeholder}
                        ?disabled=${this.disabled}
                        ?required=${this.required}
                        pattern=${this.pattern || '.*'}
                        maxlength=${this.maxlength || ''}
                        minlength=${this.minlength || ''}
                        @input=${this._handleInput}
                        @focus=${() => this._focused = true}
                        @blur=${this._handleBlur}
                        aria-invalid=${this.error ? 'true' : 'false'}
                        aria-describedby=${this.error ? 'error' : this.hint ? 'hint' : ''}
                    />
                    
                    ${this.suffix ? html`<span class="suffix">${this.suffix}</span>` : ''}
                </div>
                
                ${this.error ? html`
                    <span class="error-message" id="error" role="alert">${this.error}</span>
                ` : this.hint ? html`
                    <span class="hint" id="hint">${this.hint}</span>
                ` : ''}
            </div>
        `;
    }

    private _handleInput(e: Event) {
        const target = e.target as HTMLInputElement;
        this.value = target.value;

        this.dispatchEvent(new CustomEvent('eog-input', {
            bubbles: true,
            composed: true,
            detail: { value: this.value }
        }));
    }

    private _handleBlur() {
        this._focused = false;

        this.dispatchEvent(new CustomEvent('eog-blur', {
            bubbles: true,
            composed: true,
            detail: { value: this.value }
        }));
    }

    /** Focus the input programmatically */
    focus() {
        const input = this.shadowRoot?.querySelector('input');
        input?.focus();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-input': EogInput;
    }
}
