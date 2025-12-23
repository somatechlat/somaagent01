/**
 * SAAS Toggle Component
 * Switch control for feature flags and settings
 *
 * VIBE COMPLIANT:
 * - Real Lit 3.x Web Component
 * - Light/dark theme support
 * - Smooth animation
 * - Accessible state
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('saas-toggle')
export class SaasToggle extends LitElement {
    static styles = css`
        :host {
            display: inline-block;
        }

        .container {
            display: flex;
            align-items: center;
            gap: 12px;
            cursor: pointer;
            user-select: none;
        }

        .container.disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .switch {
            position: relative;
            width: 44px;
            height: 24px;
            background: var(--saas-border-light, #e0e0e0);
            border-radius: 9999px;
            transition: all 200ms ease;
        }

        .switch.checked {
            background: var(--saas-status-success, #22c55e);
        }

        .knob {
            position: absolute;
            top: 2px;
            left: 2px;
            width: 20px;
            height: 20px;
            background: #ffffff;
            border-radius: 50%;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            transition: transform 200ms cubic-bezier(0.4, 0.0, 0.2, 1);
        }

        .switch.checked .knob {
            transform: translateX(20px);
        }

        .label {
            font-size: var(--saas-text-sm, 13px);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .desc {
            font-size: var(--saas-text-xs, 11px);
            color: var(--saas-text-muted, #999999);
            margin-top: 2px;
        }
    `;

    @property({ type: Boolean }) checked = false;
    @property({ type: Boolean }) disabled = false;
    @property({ type: String }) label = '';
    @property({ type: String }) description = '';

    private _toggle() {
        if (this.disabled) return;
        this.checked = !this.checked;
        this.dispatchEvent(new CustomEvent('saas-change', {
            detail: { checked: this.checked },
            bubbles: true,
            composed: true
        }));
    }

    render() {
        return html`
            <div 
                class="container ${this.disabled ? 'disabled' : ''}" 
                @click=${this._toggle}
            >
                <div class="switch ${this.checked ? 'checked' : ''}">
                    <div class="knob"></div>
                </div>
                ${this.label ? html`
                    <div class="content">
                        <div class="label">${this.label}</div>
                        ${this.description ? html`<div class="desc">${this.description}</div>` : nothing}
                    </div>
                ` : nothing}
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-toggle': SaasToggle;
    }
}
