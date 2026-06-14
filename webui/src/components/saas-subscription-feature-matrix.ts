/**
 * SaaS Subscription Feature Matrix
 * Renders a feature comparison matrix for subscription tiers.
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - CSS custom properties
 * - Material Symbols only
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { SubscriptionTier } from '../controllers/subscriptions-controller.js';

interface FeatureRow {
    key: keyof SubscriptionTier;
    label: string;
    icon: string;
    format: (tier: SubscriptionTier) => string;
}

@customElement('saas-subscription-feature-matrix')
export class SaasSubscriptionFeatureMatrix extends LitElement {
    static styles = css`
        :host {
            display: block;
        }

        * {
            box-sizing: border-box;
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

        .matrix-section {
            margin-top: 32px;
        }

        .matrix-title {
            font-size: 16px;
            font-weight: 600;
            margin: 0 0 16px 0;
        }

        .matrix {
            width: 100%;
            border-collapse: collapse;
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 12px;
            overflow: hidden;
        }

        .matrix th,
        .matrix td {
            padding: 14px 16px;
            text-align: left;
            font-size: 14px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .matrix thead th {
            background: var(--saas-bg-hover, #fafafa);
            font-weight: 600;
            color: var(--saas-text-secondary, #666);
        }

        .matrix tbody tr:last-child td {
            border-bottom: none;
        }

        .matrix tbody tr:hover {
            background: var(--saas-bg-hover, #fafafa);
        }

        .feature-label {
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--saas-text-secondary, #666);
        }

        .feature-label .material-symbols-outlined {
            font-size: 16px;
        }

        .tier-name {
            font-weight: 500;
            min-width: 120px;
        }

        .value-unlimited {
            color: var(--saas-status-success, #22c55e);
            font-weight: 500;
        }
    `;

    @property({ type: Array }) tiers: SubscriptionTier[] = [];

    private _getFeatureRows(): FeatureRow[] {
        return [
            {
                key: 'maxAgents',
                label: 'Agents',
                icon: 'smart_toy',
                format: (tier) => tier.maxAgents === -1 ? 'Unlimited' : String(tier.maxAgents),
            },
            {
                key: 'maxUsers',
                label: 'Users',
                icon: 'group',
                format: (tier) => tier.maxUsers === -1 ? 'Unlimited' : String(tier.maxUsers),
            },
            {
                key: 'maxTokensPerMonth',
                label: 'Tokens/mo',
                icon: 'token',
                format: (tier) => tier.maxTokensPerMonth === -1 ? 'Custom' : this._formatNumber(tier.maxTokensPerMonth),
            },
            {
                key: 'maxStorageGB',
                label: 'Storage',
                icon: 'cloud',
                format: (tier) => tier.maxStorageGB === -1 ? 'Custom' : `${tier.maxStorageGB} GB`,
            },
            {
                key: 'priceCents',
                label: 'Price',
                icon: 'payments',
                format: (tier) => tier.priceCents === 0 ? 'Free' : `$${(tier.priceCents / 100).toFixed(0)}/${tier.billingInterval === 'yearly' ? 'yr' : 'mo'}`,
            },
            {
                key: 'tenantCount',
                label: 'Active Tenants',
                icon: 'apartment',
                format: (tier) => String(tier.tenantCount),
            },
        ];
    }

    render() {
        if (this.tiers.length === 0) {
            return html``;
        }

        const rows = this._getFeatureRows();

        return html`
            <div class="matrix-section">
                <h3 class="matrix-title">Feature Comparison</h3>
                <table class="matrix">
                    <thead>
                        <tr>
                            <th>Feature</th>
                            ${this.tiers.map(tier => html`<th class="tier-name">${tier.name}</th>`)}
                        </tr>
                    </thead>
                    <tbody>
                        ${rows.map(row => html`
                            <tr>
                                <td>
                                    <span class="feature-label">
                                        <span class="material-symbols-outlined">${row.icon}</span>
                                        ${row.label}
                                    </span>
                                </td>
                                ${this.tiers.map(tier => {
                                    const value = row.format(tier);
                                    const unlimited = value === 'Unlimited' || value === 'Custom';
                                    return html`<td class="${unlimited ? 'value-unlimited' : ''}">${value}</td>`;
                                })}
                            </tr>
                        `)}
                    </tbody>
                </table>
            </div>
        `;
    }

    private _formatNumber(num: number): string {
        if (num >= 1000000) {
            return `${(num / 1000000).toFixed(0)}M`;
        } else if (num >= 1000) {
            return `${(num / 1000).toFixed(0)}K`;
        }
        return String(num);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-subscription-feature-matrix': SaasSubscriptionFeatureMatrix;
    }
}
