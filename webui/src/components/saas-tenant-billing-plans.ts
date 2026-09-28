/**
 * Tenant Billing Plans
 *
 * Renders available subscription plans and handles upgrade actions.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { SubscriptionPlan, UpgradePlanDetail } from '../controllers/tenant-billing-controller.js';

@customElement('saas-tenant-billing-plans')
export class SaasTenantBillingPlans extends LitElement {
    static styles = css`
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
            background: var(--saas-surface, white);
            border-radius: 16px;
            border: 1px solid var(--saas-border, #e2e8f0);
            padding: 24px;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .card-title {
            font-size: 16px;
            font-weight: 600;
            color: var(--saas-text, #1e293b);
        }

        .plans-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-top: 20px;
        }

        @media (max-width: 1024px) {
            .plans-grid {
                grid-template-columns: 1fr;
            }
        }

        .plan-card {
            padding: 24px;
            border-radius: 12px;
            border: 2px solid var(--saas-border, #e2e8f0);
            text-align: center;
            transition: all 0.2s ease;
        }

        .plan-card:hover {
            border-color: var(--saas-primary, #3b82f6);
        }

        .plan-card.current {
            border-color: var(--saas-primary, #3b82f6);
            background: rgba(59, 130, 246, 0.05);
        }

        .plan-card-name {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .plan-card-price {
            font-size: 28px;
            font-weight: 700;
            color: var(--saas-primary, #3b82f6);
        }

        .plan-features {
            list-style: none;
            padding: 0;
            margin: 16px 0;
            text-align: left;
        }

        .plan-features li {
            padding: 6px 0;
            font-size: 13px;
            color: var(--saas-text-dim, #64748b);
        }

        .plan-features li::before {
            content: 'check';
            font-family: 'Material Symbols Outlined';
            color: #22c55e;
        }

        .btn {
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            border: none;
            transition: all 0.2s ease;
        }

        .btn-primary {
            background: var(--saas-primary, #3b82f6);
            color: white;
        }

        .btn-primary:hover:not(:disabled) {
            background: var(--saas-primary-hover, #2563eb);
        }

        .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .btn-secondary {
            background: var(--saas-bg, #f8fafc);
            border: 1px solid var(--saas-border, #e2e8f0);
            color: var(--saas-text-dim, #64748b);
        }

        .upgrade-btn {
            width: 100%;
            padding: 10px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
        }

        .empty-state {
            text-align: center;
            padding: 24px;
            color: var(--saas-text-dim, #64748b);
            font-size: 14px;
        }
    `;

    @property({ type: Array })
    plans: SubscriptionPlan[] = [];

    @property({ type: Boolean })
    upgrading = false;

    render() {
        return html`
            <div class="card">
                <div class="card-header">
                    <span class="card-title">
                        <span class="material-symbols-outlined">rocket_launch</span> Available Plans
                    </span>
                </div>
                <div class="plans-grid">
                    ${this.plans.length > 0
                        ? this.plans.map(
                              (plan) => html`
                                  <div class="plan-card ${plan.is_current ? 'current' : ''}">
                                      <div class="plan-card-name">${plan.name}</div>
                                      <div class="plan-card-price">${this._formatCurrency(plan.price)}/mo</div>
                                      <ul class="plan-features">
                                          ${plan.features.map((f) => html`<li>${f}</li>`)}
                                      </ul>
                                      <button
                                          class="btn upgrade-btn ${plan.is_current ? 'btn-secondary' : 'btn-primary'}"
                                          style="${plan.is_current
                                              ? 'background: var(--saas-bg); border: 1px solid var(--saas-border); color: var(--saas-text-dim);'
                                              : ''}"
                                          ?disabled=${plan.is_current || this.upgrading}
                                          @click=${() => this._upgradePlan(plan)}
                                      >
                                          ${plan.is_current ? 'Current Plan' : 'Upgrade'}
                                      </button>
                                  </div>
                              `
                          )
                        : html`<div class="empty-state">No plans available</div>`}
                </div>
            </div>
        `;
    }

    private _formatCurrency(amount: number): string {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
        }).format(amount);
    }

    private _upgradePlan(plan: SubscriptionPlan) {
        this.dispatchEvent(
            new CustomEvent<UpgradePlanDetail>('upgrade-plan', {
                detail: { plan },
                bubbles: true,
                composed: true,
            })
        );
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-tenant-billing-plans': SaasTenantBillingPlans;
    }
}
