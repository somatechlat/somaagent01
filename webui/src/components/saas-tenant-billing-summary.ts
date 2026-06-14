/**
 * Tenant Billing Summary
 *
 * Renders the current subscription plan and current usage statistics.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { TenantBilling, UsageStat } from '../controllers/tenant-billing-controller.js';

@customElement('saas-tenant-billing-summary')
export class SaasTenantBillingSummary extends LitElement {
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

        .current-plan {
            text-align: center;
            padding: 32px;
        }

        .plan-name {
            font-size: 32px;
            font-weight: 700;
            color: var(--saas-primary, #3b82f6);
            margin-bottom: 8px;
        }

        .plan-price {
            font-size: 24px;
            font-weight: 600;
            color: var(--saas-text, #1e293b);
        }

        .plan-price span {
            font-size: 14px;
            color: var(--saas-text-dim, #64748b);
            font-weight: 400;
        }

        .billing-cycle {
            font-size: 14px;
            color: var(--saas-text-dim, #64748b);
            margin-top: 8px;
        }

        .usage-item {
            margin-bottom: 16px;
        }

        .usage-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 6px;
        }

        .usage-label {
            font-size: 14px;
            color: var(--saas-text, #1e293b);
        }

        .usage-value {
            font-size: 14px;
            color: var(--saas-text-dim, #64748b);
        }

        .usage-bar {
            height: 8px;
            background: var(--saas-bg, #f8fafc);
            border-radius: 4px;
            overflow: hidden;
        }

        .usage-fill {
            height: 100%;
            background: var(--saas-primary, #3b82f6);
            border-radius: 4px;
            transition: width 0.3s ease;
        }

        .usage-fill.warning {
            background: #f59e0b;
        }

        .usage-fill.danger {
            background: #ef4444;
        }

        .payment-method {
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 16px;
            background: var(--saas-bg, #f8fafc);
            border-radius: 8px;
            margin-bottom: 12px;
        }

        .card-icon {
            font-size: 24px;
        }

        .card-info {
            flex: 1;
        }

        .card-number {
            font-size: 14px;
            font-weight: 500;
            color: var(--saas-text, #1e293b);
        }

        .empty-state {
            text-align: center;
            padding: 24px;
            color: var(--saas-text-dim, #64748b);
            font-size: 14px;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 24px;
            margin-bottom: 32px;
        }

        @media (max-width: 1024px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }
    `;

    @property({ type: Object })
    currentPlan: TenantBilling | null = null;

    @property({ type: Array })
    usage: UsageStat[] = [];

    render() {
        return html`
            <div class="grid">
                <!-- Current Plan -->
                <div class="card">
                    ${this.currentPlan
                        ? html`
                              <div class="current-plan">
                                  <div class="plan-name">${this.currentPlan.current_tier}</div>
                                  <div class="plan-price">
                                      ${this._formatCurrency(this.currentPlan.price_cents / 100)}
                                      <span>/${this.currentPlan.billing_cycle || 'month'}</span>
                                  </div>
                                  <div class="billing-cycle">
                                      Next billing: ${this._formatDate(this.currentPlan.next_billing_date)}
                                  </div>
                              </div>
                          `
                        : html`<div class="empty-state">No subscription data</div>`}
                </div>

                <!-- Usage -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">
                            <span class="material-symbols-outlined">bar_chart</span> Current Usage
                        </span>
                    </div>
                    ${this.usage.length > 0
                        ? this.usage.map((stat) => {
                              const percent = this._getUsagePercent(stat);
                              return html`
                                  <div class="usage-item">
                                      <div class="usage-header">
                                          <span class="usage-label">${stat.metric}</span>
                                          <span class="usage-value">
                                              ${stat.used}${stat.unit ? ' ' + stat.unit : ''}
                                              ${stat.limit
                                                  ? ` / ${stat.limit}${stat.unit ? ' ' + stat.unit : ''}`
                                                  : ''}
                                          </span>
                                      </div>
                                      ${stat.limit
                                          ? html`
                                                <div class="usage-bar">
                                                    <div
                                                        class="usage-fill ${this._getUsageClass(percent)}"
                                                        style="width: ${percent}%"
                                                    ></div>
                                                </div>
                                            `
                                          : ''}
                                  </div>
                              `;
                          })
                        : html`<div class="empty-state">No usage data</div>`}
                </div>

                <!-- Payment Method -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">
                            <span class="material-symbols-outlined">credit_card</span> Payment Method
                        </span>
                    </div>
                    ${this.currentPlan?.payment_method && this.currentPlan?.payment_last4
                        ? html`
                              <div class="payment-method">
                                  <span class="material-symbols-outlined card-icon">credit_card</span>
                                  <div class="card-info">
                                      <div class="card-number">
                                          ${this.currentPlan.payment_method} •••• ${this.currentPlan.payment_last4}
                                      </div>
                                  </div>
                              </div>
                          `
                        : html`<div class="empty-state">No payment method on file</div>`}
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

    private _formatDate(dateStr?: string): string {
        if (!dateStr) return '—';
        return new Date(dateStr).toLocaleDateString();
    }

    private _getUsagePercent(stat: UsageStat): number {
        if (!stat.limit) return 0;
        return Math.min(100, (stat.used / stat.limit) * 100);
    }

    private _getUsageClass(percent: number): string {
        if (percent >= 90) return 'danger';
        if (percent >= 70) return 'warning';
        return '';
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-tenant-billing-summary': SaasTenantBillingSummary;
    }
}
