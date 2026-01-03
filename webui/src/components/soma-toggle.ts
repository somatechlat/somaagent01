/**
 * Eye of God Toggle Component
 * Per Eye of God UIX Design Section 2.2
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - iOS-style toggle switch
 * - Full accessibility
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('soma-toggle')
export class SomaToggle extends LitElement {
    static styles = css`
        :host {
            display: inline-block;
        }

        .toggle-wrapper {
            display: flex;
            align-items: center;
            gap: var(--soma-spacing-sm, 8px);
        }

        .toggle-label {
            font-size: var(--soma-text-sm, 13px);
            color: var(--soma-text-main, #e2e8f0);
            user-select: none;
        }

        .toggle-label.left {
            order: -1;
        }

        .toggle-track {
            position: relative;
            width: 44px;
            height: 24px;
            border-radius: 12px;
            background: var(--soma-border-color, rgba(255, 255, 255, 0.1));
            cursor: pointer;
            transition: background-color 0.2s ease;
        }

        .toggle-track:focus-within {
            box-shadow: 0 0 0 3px rgba(148, 163, 184, 0.2);
        }

        .toggle-track.checked {
            background: var(--soma-success, #22c55e);
        }

        .toggle-track.disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        input {
            position: absolute;
            opacity: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
            margin: 0;
        }

        input:disabled {
            cursor: not-allowed;
        }

        .toggle-thumb {
            position: absolute;
            top: 2px;
            left: 2px;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: white;
            transition: transform 0.2s ease;
            pointer-events: none;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
        }

        .toggle-track.checked .toggle-thumb {
            transform: translateX(20px);
        }

        .description {
            font-size: var(--soma-text-xs, 11px);
            color: var(--soma-text-dim, #64748b);
            margin-top: var(--soma-spacing-xs, 4px);
        }
    `;

    @property({ type: Boolean }) checked = false;
    @property({ type: Boolean }) disabled = false;
    @property({ type: String }) label = '';
    @property({ type: String }) description = '';
    @property({ type: String }) labelPosition: 'left' | 'right' = 'right';

    render() {
        return html`
            <div class="toggle-wrapper">
                <div 
                    class="toggle-track ${this.checked ? 'checked' : ''} ${this.disabled ? 'disabled' : ''}"
                >
                    <input
                        type="checkbox"
                        .checked=${this.checked}
                        ?disabled=${this.disabled}
                        @change=${this._handleChange}
                        aria-label=${this.label}
                        role="switch"
                        aria-checked=${this.checked}
                    />
                    <span class="toggle-thumb"></span>
                </div>
                ${this.label ? html`
                    <span class="toggle-label ${this.labelPosition}">${this.label}</span>
                ` : ''}
            </div>
            ${this.description ? html`
                <div class="description">${this.description}</div>
            ` : ''}
        `;
    }

    private _handleChange(e: Event) {
        const input = e.target as HTMLInputElement;
        this.checked = input.checked;

        this.dispatchEvent(new CustomEvent('soma-change', {
            detail: { checked: this.checked },
            bubbles: true,
            composed: true,
        }));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-toggle': SomaToggle;
    }
}
