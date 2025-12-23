/**
 * SAAS Stat Card Component
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

@customElement('saas-stat-card')
export class SaasStatCard extends LitElement {
    static styles = css`
        :host {
            display: block;
        }

        .card {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: var(--saas-radius-lg, 12px);
            padding: var(--saas-space-lg, 24px);
            cursor: pointer;
            transition: all var(--saas-transition-normal, 200ms ease);
            position: relative;
            overflow: hidden;
        }

        .card:hover {
            border-color: var(--saas-border-medium, #cccccc);
            transform: translateY(-2px);
            box-shadow: var(--saas-shadow-md, 0 2px 8px rgba(0, 0, 0, 0.06));
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

        .status-stripe.success { background: var(--saas-status-success, #22c55e); }
        .status-stripe.warning { background: var(--saas-status-warning, #f59e0b); }
        .status-stripe.danger { background: var(--saas-status-danger, #ef4444); }
        .status-stripe.info { background: var(--saas-status-info, #3b82f6); }
        .status-stripe.neutral { background: var(--saas-border-light, #e0e0e0); }

        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: var(--saas-space-sm, 8px);
        }

        .title {
            font-size: var(--saas-text-sm, 13px);
            font-weight: var(--saas-font-medium, 500);
            color: var(--saas-text-secondary, #666666);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin: 0;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: var(--saas-radius-full, 9999px);
            animation: pulse 2s infinite;
        }

        .status-dot.success { background: var(--saas-status-success, #22c55e); }
        .status-dot.warning { background: var(--saas-status-warning, #f59e0b); }
        .status-dot.danger { background: var(--saas-status-danger, #ef4444); }
        .status-dot.info { background: var(--saas-status-info, #3b82f6); }
        .status-dot.neutral { background: var(--saas-text-muted, #999999); }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .value-row {
            display: flex;
            align-items: baseline;
            gap: var(--saas-space-sm, 8px);
        }

        .value {
            font-size: var(--saas-text-2xl, 28px);
            font-weight: var(--saas-font-bold, 700);
            color: var(--saas-text-primary, #1a1a1a);
            line-height: 1.2;
        }

        .unit {
            font-size: var(--saas-text-sm, 13px);
            color: var(--saas-text-muted, #999999);
            font-weight: var(--saas-font-normal, 400);
        }

        .trend {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 2px 8px;
            border-radius: var(--saas-radius-sm, 4px);
            font-size: var(--saas-text-xs, 11px);
            font-weight: var(--saas-font-semibold, 600);
            margin-top: var(--saas-space-sm, 8px);
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
            font-size: var(--saas-text-xs, 11px);
            color: var(--saas-text-muted, #999999);
            margin-top: var(--saas-space-xs, 4px);
        }

        /* Icon slot */
        .icon {
            position: absolute;
            top: var(--saas-space-md, 16px);
            right: var(--saas-space-md, 16px);
            opacity: 0.15;
            font-size: 48px;
        }

        ::slotted([slot="icon"]) {
            position: absolute;
            top: var(--saas-space-md, 16px);
            right: var(--saas-space-md, 16px);
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
                        <span class="trend-arrow">${this._getTrendArrow()}</span>
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
            case 'up': return '↑';
            case 'down': return '↓';
            case 'stable': return '→';
            default: return '';
        }
    }

    private _handleClick() {
        this.dispatchEvent(new CustomEvent('saas-card-click', {
            bubbles: true,
            composed: true,
            detail: { title: this.title, value: this.value }
        }));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-stat-card': SaasStatCard;
    }
}
