/**
 * Eye of God Select Component
 * Per Eye of God UIX Design Section 2.2
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Keyboard navigation
 * - Full accessibility
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state, query } from 'lit/decorators.js';

export interface SelectOption {
    value: string;
    label: string;
    disabled?: boolean;
}

@customElement('soma-select')
export class SomaSelect extends LitElement {
    static styles = css`
        :host {
            display: block;
        }

        .select-wrapper {
            position: relative;
            display: flex;
            flex-direction: column;
            gap: var(--soma-spacing-xs, 4px);
        }

        label {
            font-size: var(--soma-text-sm, 13px);
            font-weight: 500;
            color: var(--soma-text-main, #e2e8f0);
        }

        .select-container {
            position: relative;
        }

        .select-trigger {
            width: 100%;
            padding: var(--soma-spacing-sm, 8px) var(--soma-spacing-md, 16px);
            padding-right: 40px;
            border-radius: var(--soma-radius-md, 8px);
            border: 1px solid var(--soma-border-color, rgba(255, 255, 255, 0.1));
            background: var(--soma-bg-base, #1e293b);
            color: var(--soma-text-main, #e2e8f0);
            font-size: var(--soma-text-base, 14px);
            cursor: pointer;
            text-align: left;
            transition: border-color 0.2s ease;
        }

        .select-trigger:hover:not(:disabled) {
            border-color: var(--soma-accent, #94a3b8);
        }

        .select-trigger:focus {
            outline: none;
            border-color: var(--soma-accent, #94a3b8);
            box-shadow: 0 0 0 3px rgba(148, 163, 184, 0.2);
        }

        .select-trigger:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .select-trigger.placeholder {
            color: var(--soma-text-dim, #64748b);
        }

        .chevron {
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%) rotate(0deg);
            transition: transform 0.2s ease;
            pointer-events: none;
        }

        .chevron.open {
            transform: translateY(-50%) rotate(180deg);
        }

        .dropdown {
            position: absolute;
            top: calc(100% + 4px);
            left: 0;
            right: 0;
            max-height: 200px;
            overflow-y: auto;
            background: var(--soma-surface, rgba(30, 41, 59, 0.95));
            border: 1px solid var(--soma-border-color, rgba(255, 255, 255, 0.1));
            border-radius: var(--soma-radius-md, 8px);
            z-index: var(--soma-z-dropdown, 100);
            opacity: 0;
            visibility: hidden;
            transform: translateY(-8px);
            transition: all 0.2s ease;
        }

        .dropdown.open {
            opacity: 1;
            visibility: visible;
            transform: translateY(0);
        }

        .option {
            padding: var(--soma-spacing-sm, 8px) var(--soma-spacing-md, 16px);
            cursor: pointer;
            transition: background-color 0.15s ease;
        }

        .option:hover:not(.disabled) {
            background: rgba(255, 255, 255, 0.05);
        }

        .option.selected {
            background: rgba(148, 163, 184, 0.15);
            color: var(--soma-accent, #94a3b8);
        }

        .option.disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .option.focused {
            background: rgba(255, 255, 255, 0.08);
        }
    `;

    @property({ type: String }) label = '';
    @property({ type: String }) value = '';
    @property({ type: String }) placeholder = 'Select...';
    @property({ type: Array }) options: SelectOption[] = [];
    @property({ type: Boolean }) disabled = false;
    @property({ type: Boolean }) required = false;

    @state() private _isOpen = false;
    @state() private _focusedIndex = -1;

    @query('.select-trigger') private _trigger!: HTMLButtonElement;

    render() {
        const selectedOption = this.options.find(o => o.value === this.value);
        const displayText = selectedOption?.label || this.placeholder;

        return html`
            <div class="select-wrapper">
                ${this.label ? html`<label>${this.label}</label>` : ''}
                <div class="select-container">
                    <button
                        class="select-trigger ${!selectedOption ? 'placeholder' : ''}"
                        ?disabled=${this.disabled}
                        @click=${this._toggleDropdown}
                        @keydown=${this._handleKeydown}
                        aria-haspopup="listbox"
                        aria-expanded=${this._isOpen}
                    >
                        ${displayText}
                    </button>
                    <span class="chevron ${this._isOpen ? 'open' : ''}">▼</span>
                    
                    <div class="dropdown ${this._isOpen ? 'open' : ''}" role="listbox">
                        ${this.options.map((option, index) => html`
                            <div
                                class="option ${option.value === this.value ? 'selected' : ''} ${option.disabled ? 'disabled' : ''} ${index === this._focusedIndex ? 'focused' : ''}"
                                role="option"
                                aria-selected=${option.value === this.value}
                                @click=${() => this._selectOption(option)}
                            >
                                ${option.label}
                            </div>
                        `)}
                    </div>
                </div>
            </div>
        `;
    }

    private _toggleDropdown() {
        this._isOpen = !this._isOpen;
        if (this._isOpen) {
            this._focusedIndex = this.options.findIndex(o => o.value === this.value);
        }
    }

    private _selectOption(option: SelectOption) {
        if (option.disabled) return;

        this.value = option.value;
        this._isOpen = false;

        this.dispatchEvent(new CustomEvent('soma-change', {
            detail: { value: option.value, option },
            bubbles: true,
            composed: true,
        }));
    }

    private _handleKeydown(e: KeyboardEvent) {
        switch (e.key) {
            case 'Enter':
            case ' ':
                e.preventDefault();
                if (this._isOpen && this._focusedIndex >= 0) {
                    this._selectOption(this.options[this._focusedIndex]);
                } else {
                    this._toggleDropdown();
                }
                break;
            case 'Escape':
                this._isOpen = false;
                break;
            case 'ArrowDown':
                e.preventDefault();
                if (!this._isOpen) {
                    this._isOpen = true;
                } else {
                    this._focusedIndex = Math.min(this._focusedIndex + 1, this.options.length - 1);
                }
                break;
            case 'ArrowUp':
                e.preventDefault();
                this._focusedIndex = Math.max(this._focusedIndex - 1, 0);
                break;
        }
    }

    connectedCallback() {
        super.connectedCallback();
        document.addEventListener('click', this._handleOutsideClick);
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        document.removeEventListener('click', this._handleOutsideClick);
    }

    private _handleOutsideClick = (e: Event) => {
        if (!this.contains(e.target as Node)) {
            this._isOpen = false;
        }
    };
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-select': SomaSelect;
    }
}
