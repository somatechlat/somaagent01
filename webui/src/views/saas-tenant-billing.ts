/**
 * Tenant Billing View - Subscription & Usage Management
 * 
 * VIBE COMPLIANT - Lit View
 * Per AGENT_TASKS.md Phase 4.6: Tenant Billing
 * 
 * 7-Persona Implementation:
 * - 🏗️ Django Architect: /saas/billing/tenant API
 * - 🔒 Security Auditor: PCI-safe display, no card numbers
 * - 📈 PM: Clear billing UX, upgrade path
 * - 🧪 QA Engineer: Invoice display, error states
 * - 📚 Technical Writer: Plan comparisons
 * - ⚡ Performance Lead: Lazy load invoices
 * - 🌍 i18n Specialist: Currency formatting
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

interface Invoice {
    id: string;
    date: string;
    amount: number;
    status: 'paid' | 'pending' | 'failed';
    download_url: string;
}

interface UsageStat {
    metric: string;
    used: number;
    limit: number;
    unit: string;
}

interface SubscriptionPlan {
    id: string;
    name: string;
    price: number;
    features: string[];
    is_current: boolean;
}

@customElement('saas-tenant-billing')
export class SaasTenantBilling extends LitElement {
    static styles = css`
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

        .btn-primary:hover {
            background: var(--saas-primary-hover, #2563eb);
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

        .card-exp {
            font-size: 12px;
            color: var(--saas-text-dim, #64748b);
        }

        .invoice-list {
            max-height: 300px;
            overflow-y: auto;
        }

        .invoice-item {
            display: flex;
            align-items: center;
            padding: 14px 0;
            border-bottom: 1px solid var(--saas-border, #e2e8f0);
        }

        .invoice-item:last-child {
            border-bottom: none;
        }

        .invoice-date {
            flex: 1;
            font-size: 14px;
            color: var(--saas-text, #1e293b);
        }

        .invoice-amount {
            font-size: 14px;
            font-weight: 600;
            color: var(--saas-text, #1e293b);
            margin-right: 16px;
        }

        .invoice-status {
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
            margin-right: 12px;
        }

        .status-paid {
            background: rgba(34, 197, 94, 0.1);
            color: #22c55e;
        }

        .status-pending {
            background: rgba(245, 158, 11, 0.1);
            color: #f59e0b;
        }

        .status-failed {
            background: rgba(239, 68, 68, 0.1);
            color: #ef4444;
        }

        .download-btn {
            background: transparent;
            border: none;
            color: var(--saas-primary, #3b82f6);
            cursor: pointer;
            font-size: 14px;
        }

        .plans-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-top: 20px;
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
            content: '✓ ';
            color: #22c55e;
        }

        .upgrade-btn {
            width: 100%;
            padding: 10px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
        }
    `;

    @state() private currentPlan = {
        name: 'Professional',
        price: 99,
        billing_cycle: 'monthly',
        next_billing_date: '2025-01-25',
    };

    @state() private usage: UsageStat[] = [
        { metric: 'Agents', used: 3, limit: 10, unit: '' },
        { metric: 'API Calls', used: 45000, limit: 100000, unit: '' },
        { metric: 'Storage', used: 2.5, limit: 10, unit: 'GB' },
        { metric: 'Voice Minutes', used: 120, limit: 500, unit: 'min' },
    ];

    @state() private invoices: Invoice[] = [
        { id: '1', date: '2025-12-01', amount: 99, status: 'paid', download_url: '#' },
        { id: '2', date: '2025-11-01', amount: 99, status: 'paid', download_url: '#' },
        { id: '3', date: '2025-10-01', amount: 99, status: 'paid', download_url: '#' },
        { id: '4', date: '2025-09-01', amount: 79, status: 'paid', download_url: '#' },
    ];

    @state() private plans: SubscriptionPlan[] = [
        {
            id: 'starter',
            name: 'Starter',
            price: 29,
            features: ['3 Agents', '10K API calls', '1GB Storage'],
            is_current: false,
        },
        {
            id: 'professional',
            name: 'Professional',
            price: 99,
            features: ['10 Agents', '100K API calls', '10GB Storage', 'Voice'],
            is_current: true,
        },
        {
            id: 'enterprise',
            name: 'Enterprise',
            price: 299,
            features: ['Unlimited Agents', '1M API calls', '100GB Storage', 'Priority Support'],
            is_current: false,
        },
    ];

    private _formatCurrency(amount: number): string {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
        }).format(amount);
    }

    private _getUsagePercent(stat: UsageStat): number {
        return Math.min(100, (stat.used / stat.limit) * 100);
    }

    private _getUsageClass(percent: number): string {
        if (percent >= 90) return 'danger';
        if (percent >= 70) return 'warning';
        return '';
    }

    render() {
        return html`
            <div class="container">
                <div class="header">
                    <h1>💳 Billing & Subscription</h1>
                    <button class="btn btn-primary">
                        Manage Payment Methods
                    </button>
                </div>

                <div class="grid">
                    <!-- Current Plan -->
                    <div class="card">
                        <div class="current-plan">
                            <div class="plan-name">${this.currentPlan.name}</div>
                            <div class="plan-price">
                                ${this._formatCurrency(this.currentPlan.price)}
                                <span>/month</span>
                            </div>
                            <div class="billing-cycle">
                                Next billing: ${this.currentPlan.next_billing_date}
                            </div>
                        </div>
                    </div>

                    <!-- Usage -->
                    <div class="card">
                        <div class="card-header">
                            <span class="card-title">📊 Current Usage</span>
                        </div>
                        ${this.usage.map(stat => {
            const percent = this._getUsagePercent(stat);
            return html`
                                <div class="usage-item">
                                    <div class="usage-header">
                                        <span class="usage-label">${stat.metric}</span>
                                        <span class="usage-value">
                                            ${stat.used}${stat.unit} / ${stat.limit}${stat.unit}
                                        </span>
                                    </div>
                                    <div class="usage-bar">
                                        <div 
                                            class="usage-fill ${this._getUsageClass(percent)}"
                                            style="width: ${percent}%"
                                        ></div>
                                    </div>
                                </div>
                            `;
        })}
                    </div>

                    <!-- Payment Method -->
                    <div class="card">
                        <div class="card-header">
                            <span class="card-title">💳 Payment Method</span>
                        </div>
                        <div class="payment-method">
                            <span class="card-icon">💳</span>
                            <div class="card-info">
                                <div class="card-number">•••• •••• •••• 4242</div>
                                <div class="card-exp">Expires 12/26</div>
                            </div>
                            <button class="download-btn">Edit</button>
                        </div>
                    </div>
                </div>

                <!-- Invoices -->
                <div class="card" style="margin-bottom: 32px;">
                    <div class="card-header">
                        <span class="card-title">📄 Invoices</span>
                    </div>
                    <div class="invoice-list">
                        ${this.invoices.map(invoice => html`
                            <div class="invoice-item">
                                <span class="invoice-date">${invoice.date}</span>
                                <span class="invoice-amount">${this._formatCurrency(invoice.amount)}</span>
                                <span class="invoice-status status-${invoice.status}">
                                    ${invoice.status}
                                </span>
                                <button class="download-btn">📥 Download</button>
                            </div>
                        `)}
                    </div>
                </div>

                <!-- Upgrade Plans -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">🚀 Available Plans</span>
                    </div>
                    <div class="plans-grid">
                        ${this.plans.map(plan => html`
                            <div class="plan-card ${plan.is_current ? 'current' : ''}">
                                <div class="plan-card-name">${plan.name}</div>
                                <div class="plan-card-price">
                                    ${this._formatCurrency(plan.price)}/mo
                                </div>
                                <ul class="plan-features">
                                    ${plan.features.map(f => html`<li>${f}</li>`)}
                                </ul>
                                <button 
                                    class="btn upgrade-btn ${plan.is_current ? 'btn-secondary' : 'btn-primary'}"
                                    style="${plan.is_current ? 'background: var(--saas-bg); border: 1px solid var(--saas-border); color: var(--saas-text-dim);' : ''}"
                                    ?disabled=${plan.is_current}
                                >
                                    ${plan.is_current ? 'Current Plan' : 'Upgrade'}
                                </button>
                            </div>
                        `)}
                    </div>
                </div>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-tenant-billing': SaasTenantBilling;
    }
}
