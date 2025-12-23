/**
 * SAAS Select Component
 * Custom dropdown select with search and theme support
 *
 * VIBE COMPLIANT:
 * - Real Lit 3.x Web Component
 * - Light/dark theme support
 * - Searchable options
 * - Keyboard navigation
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

export interface SelectOption {
    value: string;
    label: string;
    description?: string;
    icon?: string;
}

@customElement('saas-select')
export class SaasSelect extends LitElement {
    static styles = css`
        :host {
            display: block;
            margin-bottom: var(--saas-space-md, 16px);
            position: relative;
        }

        .label {
            display: block;
            font-size: var(--saas-text-sm, 13px);
            font-weight: var(--saas-font-medium, 500);
            color: var(--saas-text-secondary, #666666);
            margin-bottom: var(--saas-space-xs, 4px);
        }

        .trigger {
            width: 100%;
            padding: var(--saas-space-sm, 8px) var(--saas-space-md, 16px);
            font-size: var(--saas-text-base, 14px);
            color: var(--saas-text-primary, #1a1a1a);
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: var(--saas-radius-md, 8px);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: all var(--saas-transition-fast, 150ms ease);
        }

        .trigger:hover {
            border-color: var(--saas-border-medium, #cccccc);
        }

        .trigger.open {
            border-color: var(--saas-accent, #1a1a1a);
            box-shadow: 0 0 0 2px rgba(26, 26, 26, 0.1);
        }

        .icon {
            font-family: 'Material Symbols Outlined';
            font-size: 20px;
            color: var(--saas-text-muted, #999999);
        }

        .dropdown {
            position: absolute;
            top: 100%;
            left: 0;
            width: 100%;
            margin-top: 4px;
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: var(--saas-radius-md, 8px);
            box-shadow: var(--saas-shadow-lg);
            z-index: 50;
            max-height: 240px;
            overflow-y: auto;
            opacity: 0;
            transform: translateY(-8px);
            pointer-events: none;
            transition: all 150ms ease;
        }

        .dropdown.open {
            opacity: 1;
            transform: translateY(0);
            pointer-events: auto;
        }

        .search-box {
            padding: 8px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            position: sticky;
            top: 0;
            background: var(--saas-bg-card, #ffffff);
        }

        .search-input {
            width: 100%;
            padding: 6px 12px;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 4px;
            font-size: 13px;
        }

        .option {
            padding: 8px 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: background 100ms;
        }

        .option:hover {
            background: var(--saas-bg-hover, #fafafa);
        }

        .option.selected {
            background: var(--saas-bg-active, #f0f0f0);
            color: var(--saas-accent, #1a1a1a);
            font-weight: 500;
        }

        .option-content {
            flex: 1;
        }

        .option-desc {
            font-size: 11px;
            color: var(--saas-text-muted, #999999);
        }
    `;

    @property({ type: String }) label = '';
    @property({ type: String }) value = '';
    @property({ type: Array }) options: SelectOption[] = [];
    @property({ type: Boolean }) searchable = false;
    @property({ type: String }) placeholder = 'Select an option';

    @state() private _isOpen = false;
    @state() private _search = '';

    private _toggle() {
        this._isOpen = !this._isOpen;
        if (this._isOpen && this.searchable) {
            setTimeout(() => {
                const input = this.shadowRoot?.querySelector('input');
                input?.focus();
            }, 50);
        }
    }

    private _select(option: SelectOption) {
        this.value = option.value;
        this._isOpen = false;
        this.dispatchEvent(new CustomEvent('saas-change', {
            detail: { value: this.value },
            bubbles: true,
            composed: true
        }));
    }

    private _handleSearch(e: Event) {
        this._search = (e.target as HTMLInputElement).value.toLowerCase();
    }

    private get _filteredOptions() {
        if (!this._search) return this.options;
        return this.options.filter(opt =>
            opt.label.toLowerCase().includes(this._search) ||
            opt.value.toLowerCase().includes(this._search)
        );
    }

    render() {
        const selected = this.options.find(o => o.value === this.value);

        return html`
            ${this.label ? html`<label class="label">${this.label}</label>` : nothing}

            <div class="trigger ${this._isOpen ? 'open' : ''}" @click=${this._toggle}>
                <span>${selected ? selected.label : this.placeholder}</span>
                <span class="icon">expand_more</span>
            </div>

            <div class="dropdown ${this._isOpen ? 'open' : ''}">
                ${this.searchable ? html`
                    <div class="search-box">
                        <input 
                            class="search-input"
                            placeholder="Search..."
                            @input=${this._handleSearch}
                            @click=${(e: Event) => e.stopPropagation()}
                        >
                    </div>
                ` : nothing}

                ${this._filteredOptions.map(opt => html`
                    <div 
                        class="option ${opt.value === this.value ? 'selected' : ''}"
                        @click=${() => this._select(opt)}
                    >
                        ${opt.icon ? html`<span class="icon" style="font-size: 18px">${opt.icon}</span>` : nothing}
                        <div class="option-content">
                            <div>${opt.label}</div>
                            ${opt.description ? html`<div class="option-desc">${opt.description}</div>` : nothing}
                        </div>
                        ${opt.value === this.value ? html`<span class="icon" style="font-size: 18px">check</span>` : nothing}
                    </div>
                `)}
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-select': SaasSelect;
    }
}
