/**
 * Eye of God Slider Component
 * Per Eye of God UIX Design Section 2.2
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Range input with custom styling
 * - Value display and marks
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('eog-slider')
export class EogSlider extends LitElement {
    static styles = css`
        :host {
            display: block;
        }

        .slider-wrapper {
            display: flex;
            flex-direction: column;
            gap: var(--eog-spacing-xs, 4px);
        }

        .slider-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        label {
            font-size: var(--eog-text-sm, 13px);
            font-weight: 500;
            color: var(--eog-text-main, #e2e8f0);
        }

        .value-display {
            font-size: var(--eog-text-sm, 13px);
            font-weight: 600;
            color: var(--eog-accent, #94a3b8);
            min-width: 50px;
            text-align: right;
        }

        .slider-container {
            position: relative;
            padding: var(--eog-spacing-xs, 4px) 0;
        }

        input[type="range"] {
            width: 100%;
            height: 6px;
            border-radius: 3px;
            background: var(--eog-border-color, rgba(255, 255, 255, 0.1));
            outline: none;
            -webkit-appearance: none;
            appearance: none;
        }

        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: var(--eog-accent, #94a3b8);
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            transition: transform 0.15s ease;
        }

        input[type="range"]::-webkit-slider-thumb:hover {
            transform: scale(1.1);
        }

        input[type="range"]::-moz-range-thumb {
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: var(--eog-accent, #94a3b8);
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }

        input[type="range"]:focus {
            outline: none;
        }

        input[type="range"]:focus::-webkit-slider-thumb {
            box-shadow: 0 0 0 3px rgba(148, 163, 184, 0.3);
        }

        input[type="range"]:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        input[type="range"]:disabled::-webkit-slider-thumb {
            cursor: not-allowed;
        }

        .track-fill {
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            height: 6px;
            border-radius: 3px;
            background: var(--eog-accent, #94a3b8);
            pointer-events: none;
        }

        .marks {
            display: flex;
            justify-content: space-between;
            margin-top: var(--eog-spacing-xs, 4px);
        }

        .mark {
            font-size: var(--eog-text-xs, 11px);
            color: var(--eog-text-dim, #64748b);
        }
    `;

    @property({ type: Number }) value = 50;
    @property({ type: Number }) min = 0;
    @property({ type: Number }) max = 100;
    @property({ type: Number }) step = 1;
    @property({ type: String }) label = '';
    @property({ type: String }) unit = '';
    @property({ type: Boolean }) disabled = false;
    @property({ type: Boolean }) showMarks = false;

    get _fillPercent(): number {
        return ((this.value - this.min) / (this.max - this.min)) * 100;
    }

    render() {
        return html`
            <div class="slider-wrapper">
                <div class="slider-header">
                    ${this.label ? html`<label>${this.label}</label>` : ''}
                    <span class="value-display">${this.value}${this.unit}</span>
                </div>
                
                <div class="slider-container">
                    <div class="track-fill" style="width: ${this._fillPercent}%"></div>
                    <input
                        type="range"
                        .value=${String(this.value)}
                        min=${this.min}
                        max=${this.max}
                        step=${this.step}
                        ?disabled=${this.disabled}
                        @input=${this._handleInput}
                        @change=${this._handleChange}
                        aria-label=${this.label}
                        aria-valuemin=${this.min}
                        aria-valuemax=${this.max}
                        aria-valuenow=${this.value}
                    />
                </div>

                ${this.showMarks ? html`
                    <div class="marks">
                        <span class="mark">${this.min}${this.unit}</span>
                        <span class="mark">${this.max}${this.unit}</span>
                    </div>
                ` : ''}
            </div>
        `;
    }

    private _handleInput(e: Event) {
        const input = e.target as HTMLInputElement;
        this.value = Number(input.value);

        this.dispatchEvent(new CustomEvent('eog-input', {
            detail: { value: this.value },
            bubbles: true,
            composed: true,
        }));
    }

    private _handleChange(e: Event) {
        const input = e.target as HTMLInputElement;
        this.value = Number(input.value);

        this.dispatchEvent(new CustomEvent('eog-change', {
            detail: { value: this.value },
            bubbles: true,
            composed: true,
        }));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-slider': EogSlider;
    }
}
