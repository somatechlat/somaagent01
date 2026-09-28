/**
 * Tenant Billing View - Subscription & Usage Management
 *
 * VIBE COMPLIANT - Lit View
 * Per AGENT_TASKS.md Phase 4.6: Tenant Billing
 *
 * Real backend endpoints:
 * - /aaas/billing/tenant/{tenant_id}
 * - /aaas/billing/tenant/{tenant_id}/invoices
 * - /aaas/billing/usage/{tenant_id}
 * - /aaas/tiers
 * - /aaas/billing/tenant/{tenant_id}/upgrade
 */

import { LitElement, html, css } from 'lit';
import { customElement } from 'lit/decorators.js';
import '../components/saas-tenant-billing-summary.js';
import '../components/saas-tenant-billing-invoices.js';
import '../components/saas-tenant-billing-plans.js';
import {
    TenantBillingController,
    type UpgradePlanDetail,
} from '../controllers/tenant-billing-controller.js';

@customElement('saas-tenant-billing')
export class SaasTenantBilling extends LitElement {
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

        :host {
            display: block;
            min-height: 100vh;
            background: var(--saas-bg, #f8fafc);
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 24px;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 32px;
        }

        h1 {
            font-size: 28px;
            font-weight: 600;
            color: var(--saas-text, #1e293b);
            margin: 0;
        }

        .error-banner {
            padding: 12px 16px;
            background: rgba(239, 68, 68, 0.1);
            color: #dc2626;
            border-radius: 8px;
            margin-bottom: 24px;
            font-size: 14px;
        }

        .empty-state {
            text-align: center;
            padding: 24px;
            color: var(--saas-text-dim, #64748b);
            font-size: 14px;
        }

        @media (max-width: 1024px) {
            .container {
                padding: 16px;
            }
        }
    `;

    private _controller = new TenantBillingController(this);

    connectedCallback() {
        super.connectedCallback();
        this._controller.loadBillingData();
    }

    render() {
        return html`
            <div class="container">
                <div class="header">
                    <h1>
                        <span class="material-symbols-outlined">credit_card</span>
                        Billing & Subscription
                    </h1>
                </div>

                ${this._controller.error
                    ? html`<div class="error-banner">${this._controller.error}</div>`
                    : ''}

                ${this._controller.loading
                    ? html`<div class="empty-state">Loading billing data...</div>`
                    : html`
                          <saas-tenant-billing-summary
                              .currentPlan=${this._controller.currentPlan}
                              .usage=${this._controller.usage}
                          ></saas-tenant-billing-summary>

                          <saas-tenant-billing-invoices
                              .invoices=${this._controller.invoices}
                          ></saas-tenant-billing-invoices>

                          <saas-tenant-billing-plans
                              .plans=${this._controller.plans}
                              .upgrading=${this._controller.upgrading}
                              @upgrade-plan=${this._onUpgradePlan}
                          ></saas-tenant-billing-plans>
                      `}
            </div>
        `;
    }

    private _onUpgradePlan(event: CustomEvent<UpgradePlanDetail>) {
        const { plan } = event.detail;
        this._controller.upgradePlan(plan);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-tenant-billing': SaasTenantBilling;
    }
}
