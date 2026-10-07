/**
 * SOMA Stat Card Component
 * Dashboard metric card with status indicators and trend arrows
 *
 * VIBE COMPLIANT:
 * - Real Lit 3.x implementation
 * - Light/dark theme support via CSS custom properties
 * - Click to open detail modal
 * - Status colors: success (green), warning (amber), danger (red), info (blue)
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

export type StatStatus = 'success' | 'warning' | 'danger' | 'info' | 'neutral';
export type TrendDirection = 'up' | 'down' | 'stable';

@customElement('soma-stat-card')
export class SomaStatCard extends LitElement {
    static styles = css`
        :host {
            display: block;
        }

        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: 20px;
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            -webkit-font-feature-settings: 'liga';
            -webkit-font-smoothing: antialiased;
        }

        .card {
            background: var(--soma-bg-card, #ffffff);
            border: 1px solid var(--soma-border-light, #e0e0e0);
            border-radius: var(--soma-radius-lg, 12px);
            padding: var(--soma-space-lg, 24px);
            cursor: pointer;
            transition: all var(--soma-transition-normal, 200ms ease);
            position: relative;
            overflow: hidden;
        }

        .card:hover {
            border-color: var(--soma-border-medium, #cccccc);
            transform: translateY(-2px);
            box-shadow: var(--soma-shadow-md, 0 2px 8px rgba(0, 0, 0, 0.06));
        }

        .card:active {
            transform: translateY(0);
        }

        /* Status indicator stripe */
        .status-stripe {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
        }

        .status-stripe.success { background: var(--soma-status-success, #22c55e); }
        .status-stripe.warning { background: var(--soma-status-warning, #f59e0b); }
        .status-stripe.danger { background: var(--soma-status-danger, #ef4444); }
        .status-stripe.info { background: var(--soma-status-info, #3b82f6); }
        .status-stripe.neutral { background: var(--soma-border-light, #e0e0e0); }

        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: var(--soma-space-sm, 8px);
        }

        .title {
            font-size: var(--soma-text-sm, 13px);
            font-weight: var(--soma-font-medium, 500);
            color: var(--soma-text-secondary, #666666);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin: 0;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: var(--soma-radius-full, 9999px);
            animation: pulse 2s infinite;
        }

        .status-dot.success { background: var(--soma-status-success, #22c55e); }
        .status-dot.warning { background: var(--soma-status-warning, #f59e0b); }
        .status-dot.danger { background: var(--soma-status-danger, #ef4444); }
        .status-dot.info { background: var(--soma-status-info, #3b82f6); }
        .status-dot.neutral { background: var(--soma-text-muted, #999999); }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .value-row {
            display: flex;
            align-items: baseline;
            gap: var(--soma-space-sm, 8px);
        }

        .value {
            font-size: var(--soma-text-2xl, 28px);
            font-weight: var(--soma-font-bold, 700);
            color: var(--soma-text-primary, #1a1a1a);
            line-height: 1.2;
        }

        .unit {
            font-size: var(--soma-text-sm, 13px);
            color: var(--soma-text-muted, #999999);
            font-weight: var(--soma-font-normal, 400);
        }

        .trend {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 2px 8px;
            border-radius: var(--soma-radius-sm, 4px);
            font-size: var(--soma-text-xs, 11px);
            font-weight: var(--soma-font-semibold, 600);
            margin-top: var(--soma-space-sm, 8px);
        }

        .trend.up {
            background: rgba(34, 197, 94, 0.1);
            color: #16a34a;
        }

        .trend.down {
            background: rgba(239, 68, 68, 0.1);
            color: #dc2626;
        }

        .trend.stable {
            background: rgba(107, 114, 128, 0.1);
            color: #6b7280;
        }

        .trend-arrow {
            font-size: 10px;
        }

        .subtitle {
            font-size: var(--soma-text-xs, 11px);
            color: var(--soma-text-muted, #999999);
            margin-top: var(--soma-space-xs, 4px);
        }

        /* Icon slot */
        .icon {
            position: absolute;
            top: var(--soma-space-md, 16px);
            right: var(--soma-space-md, 16px);
            opacity: 0.15;
            font-size: 48px;
        }

        ::slotted([slot="icon"]) {
            position: absolute;
            top: var(--soma-space-md, 16px);
            right: var(--soma-space-md, 16px);
            opacity: 0.15;
            width: 48px;
            height: 48px;
        }
    `;

    @property({ type: String }) title = '';
    @property({ type: String }) value = '';
    @property({ type: String }) unit = '';
    @property({ type: String }) subtitle = '';
    @property({ type: String }) status: StatStatus = 'neutral';
    @property({ type: String }) trend: TrendDirection | '' = '';
    @property({ type: String, attribute: 'trend-value' }) trendValue = '';
    @property({ type: Boolean, attribute: 'show-stripe' }) showStripe = false;

    render() {
        return html`
            <article class="card" @click=${this._handleClick}>
                ${this.showStripe ? html`
                    <div class="status-stripe ${this.status}"></div>
                ` : ''}

                <slot name="icon"></slot>

                <header class="header">
                    <h3 class="title">${this.title}</h3>
                    <span class="status-dot ${this.status}"></span>
                </header>

                <div class="value-row">
                    <span class="value">${this.value}</span>
                    ${this.unit ? html`<span class="unit">${this.unit}</span>` : ''}
                </div>

                ${this.trend ? html`
                    <div class="trend ${this.trend}">
                        <span class="trend-arrow material-symbols-outlined">${this._getTrendArrow()}</span>
                        <span>${this.trendValue}</span>
                    </div>
                ` : ''}

                ${this.subtitle ? html`
                    <p class="subtitle">${this.subtitle}</p>
                ` : ''}

                <slot></slot>
            </article>
        `;
    }

    private _getTrendArrow(): string {
        switch (this.trend) {
            case 'up': return 'arrow_upward';
            case 'down': return 'arrow_downward';
            case 'stable': return 'trending_flat';
            default: return '';
        }
    }

    private _handleClick() {
        this.dispatchEvent(new CustomEvent('soma-card-click', {
            bubbles: true,
            composed: true,
            detail: { title: this.title, value: this.value }
        }));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-stat-card': SomaStatCard;
    }
}
