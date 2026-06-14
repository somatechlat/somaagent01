/**
 * SaaS Subscription Tier Cards
 * Renders a grid of tier selection cards.
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - CSS custom properties
 * - Material Symbols only
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { SubscriptionTier } from '../controllers/subscriptions-controller.js';

@customElement('saas-subscription-tier-cards')
export class SaasSubscriptionTierCards extends LitElement {
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

        .tier-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
        }

        .tier-card {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 16px;
            padding: 24px;
            display: flex;
            flex-direction: column;
        }

        .tier-card.featured {
            border-color: #1a1a1a;
            box-shadow: 0 0 0 1px #1a1a1a;
        }

        .tier-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 16px;
        }

        .tier-name {
            font-size: 18px;
            font-weight: 600;
        }

        .tier-badge {
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .tier-badge.custom {
            background: #fef3c7;
            color: #b45309;
        }

        .tier-badge.popular {
            background: #1a1a1a;
            color: white;
        }

        .tier-price {
            margin-bottom: 20px;
        }

        .price-amount {
            font-size: 32px;
            font-weight: 700;
        }

        .price-period {
            font-size: 14px;
            color: var(--saas-text-secondary, #666);
        }

        .tier-limits {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-bottom: 20px;
        }

        .limit-row {
            display: flex;
            justify-content: space-between;
            font-size: 14px;
        }

        .limit-label {
            color: var(--saas-text-secondary, #666);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .limit-label .material-symbols-outlined {
            font-size: 16px;
        }

        .limit-value {
            font-weight: 500;
        }

        .limit-value.unlimited {
            color: var(--saas-status-success, #22c55e);
        }

        .tier-stats {
            padding-top: 16px;
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
            margin-bottom: 16px;
        }

        .stat-row {
            display: flex;
            justify-content: space-between;
            font-size: 13px;
        }

        .stat-label {
            color: var(--saas-text-muted, #999);
        }

        .stat-value {
            font-weight: 500;
        }

        .tier-actions {
            display: flex;
            gap: 8px;
        }

        .tier-btn {
            flex: 1;
            padding: 10px;
            border-radius: 8px;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            background: var(--saas-bg-card, #ffffff);
            font-size: 13px;
            cursor: pointer;
            transition: all 0.1s ease;
        }

        .tier-btn:hover {
            background: var(--saas-bg-hover, #fafafa);
        }
    `;

    @property({ type: Array }) tiers: SubscriptionTier[] = [];

    render() {
        return html`
            <div class="tier-grid">
                ${this.tiers.map(tier => this._renderTierCard(tier))}
            </div>
        `;
    }

    private _renderTierCard(tier: SubscriptionTier) {
        const isPopular = tier.slug === 'team';
        const priceDisplay = tier.priceCents === 0
            ? '$0'
            : `$${(tier.priceCents / 100).toFixed(0)}`;

        return html`
            <div class="tier-card ${isPopular ? 'featured' : ''}">
                <div class="tier-header">
                    <span class="tier-name">${tier.name}</span>
                    ${tier.isCustom ? html`<span class="tier-badge custom">Custom</span>` : ''}
                    ${isPopular ? html`<span class="tier-badge popular">Popular</span>` : ''}
                </div>

                <div class="tier-price">
                    <span class="price-amount">${priceDisplay}</span>
                    <span class="price-period">/${tier.billingInterval === 'yearly' ? 'year' : 'mo'}</span>
                </div>

                <div class="tier-limits">
                    <div class="limit-row">
                        <span class="limit-label">
                            <span class="material-symbols-outlined">smart_toy</span>
                            Agents
                        </span>
                        <span class="limit-value ${tier.maxAgents === -1 ? 'unlimited' : ''}">
                            ${tier.maxAgents === -1 ? 'Unlimited' : tier.maxAgents}
                        </span>
                    </div>
                    <div class="limit-row">
                        <span class="limit-label">
                            <span class="material-symbols-outlined">group</span>
                            Users
                        </span>
                        <span class="limit-value ${tier.maxUsers === -1 ? 'unlimited' : ''}">
                            ${tier.maxUsers === -1 ? 'Unlimited' : tier.maxUsers}
                        </span>
                    </div>
                    <div class="limit-row">
                        <span class="limit-label">
                            <span class="material-symbols-outlined">token</span>
                            Tokens/mo
                        </span>
                        <span class="limit-value ${tier.maxTokensPerMonth === -1 ? 'unlimited' : ''}">
                            ${tier.maxTokensPerMonth === -1 ? 'Custom' : this._formatNumber(tier.maxTokensPerMonth)}
                        </span>
                    </div>
                    <div class="limit-row">
                        <span class="limit-label">
                            <span class="material-symbols-outlined">cloud</span>
                            Storage
                        </span>
                        <span class="limit-value ${tier.maxStorageGB === -1 ? 'unlimited' : ''}">
                            ${tier.maxStorageGB === -1 ? 'Custom' : `${tier.maxStorageGB} GB`}
                        </span>
                    </div>
                </div>

                <div class="tier-stats">
                    <div class="stat-row">
                        <span class="stat-label">Active tenants</span>
                        <span class="stat-value">${tier.tenantCount}</span>
                    </div>
                </div>

                <div class="tier-actions">
                    <button class="tier-btn" @click=${() => this._emitEdit(tier)}>Edit</button>
                    ${tier.isCustom ? html`
                        <button class="tier-btn" @click=${() => this._emitDelete(tier.id)}>Delete</button>
                    ` : ''}
                </div>
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

    private _emitEdit(tier: SubscriptionTier) {
        this.dispatchEvent(new CustomEvent('edit-tier', {
            detail: tier,
            bubbles: true,
            composed: true,
        }));
    }

    private _emitDelete(tierId: string) {
        this.dispatchEvent(new CustomEvent('delete-tier', {
            detail: tierId,
            bubbles: true,
            composed: true,
        }));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-subscription-tier-cards': SaasSubscriptionTierCards;
    }
}
