import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('saas-input')
export class SaasInput extends LitElement {
    static styles = css`
        :host {
            display: block;
            margin-bottom: 16px;
        }

        label {
            display: block;
            font-size: 13px;
            font-weight: 500;
            color: var(--saas-text-dim, #94a3b8);
            margin-bottom: 6px;
        }

        .input-wrapper {
            position: relative;
            display: flex;
            align-items: center;
        }

        input {
            width: 100%;
            padding: 10px 12px;
            border-radius: 8px;
            border: 1px solid var(--saas-border-color, rgba(255, 255, 255, 0.1));
            background: var(--saas-bg-base, #1e293b);
            color: var(--saas-text-main, #e2e8f0);
            font-size: 14px;
            transition: all 0.2s ease;
            font-family: inherit;
        }

        input:focus {
            outline: none;
            border-color: var(--saas-primary, #3b82f6);
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
        }

        input::placeholder {
            color: rgba(255, 255, 255, 0.2);
        }

        .icon {
            position: absolute;
            left: 12px;
            color: var(--saas-text-dim, #94a3b8);
            pointer-events: none;
        }

        input.has-icon {
            padding-left: 36px;
        }
    `;

    @property() label = '';
    @property() type = 'text';
    @property() placeholder = '';
    @property() value = '';
    @property() icon = '';

    private _handleInput(e: Event) {
        const target = e.target as HTMLInputElement;
        this.value = target.value;
        this.dispatchEvent(new CustomEvent('input', {
            detail: { value: this.value },
            bubbles: true,
            composed: true
        }));
    }

    render() {
        return html`
            ${this.label ? html`<label>${this.label}</label>` : ''}
            <div class="input-wrapper">
                ${this.icon ? html`<span class="material-symbols-outlined icon">${this.icon}</span>` : ''}
                <input
                    class="${this.icon ? 'has-icon' : ''}"
                    type="${this.type}"
                    placeholder="${this.placeholder}"
                    .value="${this.value}"
                    @input="${this._handleInput}"
                />
            </div>
        `;
    }
}
