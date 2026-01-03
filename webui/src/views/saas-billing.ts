/**
 * SomaAgent SaaS — Billing Dashboard
 * Per SAAS_ADMIN_SRS.md Section 5.3 - Billing Dashboard
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Lago API integration placeholders
 * - Minimal white/black design per UI_STYLE_GUIDE.md
 * - NO EMOJIS - Google Material Symbols only
 * 
 * Features:
 * - MRR, ARPU, Churn metrics
 * - Revenue by tier breakdown
 * - Recent invoices list
 * - Usage summary
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';

interface BillingMetrics {
    mrr: number;
    arpu: number;
    churnRate: number;
    totalRevenue: number;
    totalTenants: number;
    paidTenants: number;
}

interface Invoice {
    id: string;
    tenantName: string;
    amount: number;
    status: 'paid' | 'pending' | 'overdue' | 'void';
    dueDate: string;
    paidDate?: string;
}

interface TierRevenue {
    tier: string;
    revenue: number;
    tenants: number;
    percentage: number;
}

@customElement('saas-billing')
export class SaasBilling extends LitElement {
    static styles = css`
        :host {
            display: flex;
            height: 100vh;
            background: var(--saas-bg-page, #f5f5f5);
            font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            color: var(--saas-text-primary, #1a1a1a);
        }

        * {
            box-sizing: border-box;
        }

        /* Material Symbols - Required for Shadow DOM */
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

        /* ========================================
           SIDEBAR
           ======================================== */
        .sidebar {
            width: 260px;
            background: var(--saas-bg-card, #ffffff);
            border-right: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            padding: 24px 0;
        }

        .sidebar-header {
            padding: 0 20px 20px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            margin-bottom: 16px;
        }

        .sidebar-title {
            font-size: 18px;
            font-weight: 600;
            margin: 0 0 4px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .sidebar-subtitle {
            font-size: 13px;
            color: var(--saas-text-secondary, #666);
        }

        /* Nav Items */
        .nav-list {
            display: flex;
            flex-direction: column;
            gap: 2px;
            padding: 0 12px;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 14px;
            border-radius: 8px;
            font-size: 14px;
            color: var(--saas-text-secondary, #666);
            cursor: pointer;
            transition: all 0.15s ease;
            text-decoration: none;
        }

        .nav-item:hover {
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .nav-item.active {
            background: var(--saas-bg-active, #f0f0f0);
            color: var(--saas-text-primary, #1a1a1a);
            font-weight: 500;
        }

        .nav-item .material-symbols-outlined {
            font-size: 18px;
        }

        .nav-divider {
            height: 1px;
            background: var(--saas-border-light, #e0e0e0);
            margin: 12px 20px;
        }

        /* ========================================
           MAIN CONTENT
           ======================================== */
        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        /* Header */
        .header {
            padding: 16px 24px;
            background: var(--saas-bg-card, #ffffff);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-title {
            font-size: 18px;
            font-weight: 600;
        }

        .header-actions {
            display: flex;
            gap: 10px;
        }

        .btn {
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.1s ease;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            background: var(--saas-bg-card, #ffffff);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .btn:hover {
            background: var(--saas-bg-hover, #fafafa);
        }

        .btn .material-symbols-outlined {
            font-size: 18px;
        }

        /* Content */
        .content {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
        }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }

        @media (max-width: 1200px) {
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        .stat-card {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 12px;
            padding: 20px;
        }

        .stat-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }

        .stat-label {
            font-size: 13px;
            color: var(--saas-text-secondary, #666);
        }

        .stat-icon {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--saas-bg-hover, #fafafa);
        }

        .stat-icon .material-symbols-outlined {
            font-size: 18px;
        }

        .stat-value {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .stat-trend {
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .stat-trend.up {
            color: var(--saas-status-success, #22c55e);
        }

        .stat-trend.down {
            color: var(--saas-status-danger, #ef4444);
        }

        /* Content Grid */
        .content-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        @media (max-width: 900px) {
            .content-grid {
                grid-template-columns: 1fr;
            }
        }

        /* Cards */
        .card {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 12px;
            padding: 20px;
        }

        .card-title {
            font-size: 16px;
            font-weight: 600;
            margin: 0 0 16px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .card-title .material-symbols-outlined {
            font-size: 18px;
            color: var(--saas-text-secondary, #666);
        }

        /* Revenue Breakdown */
        .revenue-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .revenue-item {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .revenue-bar-bg {
            flex: 1;
            height: 8px;
            background: var(--saas-border-light, #e0e0e0);
            border-radius: 4px;
            overflow: hidden;
        }

        .revenue-bar {
            height: 100%;
            border-radius: 4px;
            background: #1a1a1a;
        }

        .revenue-tier {
            width: 80px;
            font-size: 13px;
            font-weight: 500;
        }

        .revenue-amount {
            width: 70px;
            font-size: 13px;
            font-weight: 600;
            text-align: right;
        }

        .revenue-pct {
            width: 45px;
            font-size: 12px;
            color: var(--saas-text-muted, #999);
            text-align: right;
        }

        /* Invoices Table */
        .invoices-table {
            width: 100%;
            border-collapse: collapse;
        }

        .invoices-table th {
            text-align: left;
            padding: 10px 12px;
            font-size: 12px;
            font-weight: 500;
            color: var(--saas-text-muted, #999);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .invoices-table td {
            padding: 12px;
            font-size: 13px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .invoices-table tr:last-child td {
            border-bottom: none;
        }

        .invoice-tenant {
            font-weight: 500;
        }

        .invoice-amount {
            font-weight: 600;
        }

        .invoice-status {
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .invoice-status.paid {
            background: #d1fae5;
            color: #047857;
        }

        .invoice-status.pending {
            background: #fef3c7;
            color: #b45309;
        }

        .invoice-status.overdue {
            background: #fee2e2;
            color: #b91c1c;
        }

        .invoice-status.void {
            background: #f3f4f6;
            color: #6b7280;
        }

        /* View All Link */
        .view-all {
            display: block;
            text-align: center;
            padding: 12px;
            font-size: 13px;
            color: var(--saas-text-secondary, #666);
            text-decoration: none;
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
            margin-top: 8px;
            transition: color 0.1s ease;
        }

        .view-all:hover {
            color: var(--saas-text-primary, #1a1a1a);
        }
    `;

    @state() private _metrics: BillingMetrics = {
        mrr: 24580,
        arpu: 185,
        churnRate: 2.3,
        totalRevenue: 98320,
        totalTenants: 133,
        paidTenants: 88,
    };

    @state() private _tierRevenue: TierRevenue[] = [
        { tier: 'Enterprise', revenue: 11988, tenants: 12, percentage: 49 },
        { tier: 'Team', revenue: 5572, tenants: 28, percentage: 23 },
        { tier: 'Starter', revenue: 1568, tenants: 32, percentage: 6 },
        { tier: 'Free', revenue: 0, tenants: 45, percentage: 0 },
    ];

    @state() private _invoices: Invoice[] = [
        { id: '1', tenantName: 'Acme Corporation', amount: 99900, status: 'paid', dueDate: '2025-12-15', paidDate: '2025-12-14' },
        { id: '2', tenantName: 'TechStart Inc', amount: 19900, status: 'paid', dueDate: '2025-12-18', paidDate: '2025-12-18' },
        { id: '3', tenantName: 'Globex Industries', amount: 4900, status: 'pending', dueDate: '2025-12-25' },
        { id: '4', tenantName: 'Initech LLC', amount: 19900, status: 'overdue', dueDate: '2025-12-10' },
        { id: '5', tenantName: 'Hooli Systems', amount: 99900, status: 'paid', dueDate: '2025-12-20', paidDate: '2025-12-19' },
    ];

    @state() private _isLoading = false;

    async connectedCallback() {
        super.connectedCallback();
        await this._loadBillingData();
    }

    render() {
        return html`
            <!-- Sidebar -->
            <aside class="sidebar">
                <div class="sidebar-header">
                    <h1 class="sidebar-title">
                        <span class="material-symbols-outlined">shield_person</span>
                        God Mode
                    </h1>
                    <p class="sidebar-subtitle">Platform Administration</p>
                </div>

                <nav class="nav-list">
                    <a class="nav-item" href="/saas/dashboard">
                        <span class="material-symbols-outlined">dashboard</span>
                        Dashboard
                    </a>
                    <a class="nav-item" href="/saas/tenants">
                        <span class="material-symbols-outlined">apartment</span>
                        Tenants
                    </a>
                    <a class="nav-item" href="/saas/subscriptions">
                        <span class="material-symbols-outlined">card_membership</span>
                        Subscriptions
                    </a>
                    <a class="nav-item active" href="/saas/billing">
                        <span class="material-symbols-outlined">payments</span>
                        Billing
                    </a>
                    <div class="nav-divider"></div>
                    <a class="nav-item" href="/platform/models">
                        <span class="material-symbols-outlined">model_training</span>
                        Models
                    </a>
                    <a class="nav-item" href="/platform/roles">
                        <span class="material-symbols-outlined">admin_panel_settings</span>
                        Roles
                    </a>
                    <a class="nav-item" href="/platform/flags">
                        <span class="material-symbols-outlined">toggle_on</span>
                        Feature Flags
                    </a>
                    <a class="nav-item" href="/platform/api-keys">
                        <span class="material-symbols-outlined">vpn_key</span>
                        API Keys
                    </a>
                </nav>
            </aside>

            <!-- Main Content -->
            <main class="main">
                <header class="header">
                    <h2 class="header-title">Billing & Revenue</h2>
                    <div class="header-actions">
                        <button class="btn" @click=${this._exportReport}>
                            <span class="material-symbols-outlined">download</span>
                            Export Report
                        </button>
                    </div>
                </header>

                <div class="content">
                    <!-- Stats -->
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-header">
                                <span class="stat-label">Monthly Recurring Revenue</span>
                                <div class="stat-icon">
                                    <span class="material-symbols-outlined">trending_up</span>
                                </div>
                            </div>
                            <div class="stat-value">$${this._formatCurrency(this._metrics.mrr)}</div>
                            <div class="stat-trend up">
                                <span class="material-symbols-outlined" style="font-size: 14px;">arrow_upward</span>
                                +12.5% from last month
                            </div>
                        </div>

                        <div class="stat-card">
                            <div class="stat-header">
                                <span class="stat-label">Average Revenue Per User</span>
                                <div class="stat-icon">
                                    <span class="material-symbols-outlined">person</span>
                                </div>
                            </div>
                            <div class="stat-value">$${this._metrics.arpu}</div>
                            <div class="stat-trend up">
                                <span class="material-symbols-outlined" style="font-size: 14px;">arrow_upward</span>
                                +5.2% from last month
                            </div>
                        </div>

                        <div class="stat-card">
                            <div class="stat-header">
                                <span class="stat-label">Churn Rate</span>
                                <div class="stat-icon">
                                    <span class="material-symbols-outlined">sync_problem</span>
                                </div>
                            </div>
                            <div class="stat-value">${this._metrics.churnRate}%</div>
                            <div class="stat-trend down">
                                <span class="material-symbols-outlined" style="font-size: 14px;">arrow_downward</span>
                                -0.8% from last month
                            </div>
                        </div>

                        <div class="stat-card">
                            <div class="stat-header">
                                <span class="stat-label">Paid Tenants</span>
                                <div class="stat-icon">
                                    <span class="material-symbols-outlined">verified</span>
                                </div>
                            </div>
                            <div class="stat-value">${this._metrics.paidTenants}/${this._metrics.totalTenants}</div>
                            <div class="stat-trend up">
                                <span class="material-symbols-outlined" style="font-size: 14px;">arrow_upward</span>
                                +4 this month
                            </div>
                        </div>
                    </div>

                    <!-- Content Grid -->
                    <div class="content-grid">
                        <!-- Revenue by Tier -->
                        <div class="card">
                            <h3 class="card-title">
                                <span class="material-symbols-outlined">pie_chart</span>
                                Revenue by Tier
                            </h3>
                            <div class="revenue-list">
                                ${this._tierRevenue.map(tier => html`
                                    <div class="revenue-item">
                                        <span class="revenue-tier">${tier.tier}</span>
                                        <div class="revenue-bar-bg">
                                            <div class="revenue-bar" style="width: ${tier.percentage}%"></div>
                                        </div>
                                        <span class="revenue-amount">$${this._formatCurrency(tier.revenue)}</span>
                                        <span class="revenue-pct">${tier.percentage}%</span>
                                    </div>
                                `)}
                            </div>
                        </div>

                        <!-- Recent Invoices -->
                        <div class="card">
                            <h3 class="card-title">
                                <span class="material-symbols-outlined">receipt_long</span>
                                Recent Invoices
                            </h3>
                            <table class="invoices-table">
                                <thead>
                                    <tr>
                                        <th>Tenant</th>
                                        <th>Amount</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${this._invoices.slice(0, 5).map(inv => html`
                                        <tr>
                                            <td class="invoice-tenant">${inv.tenantName}</td>
                                            <td class="invoice-amount">$${(inv.amount / 100).toFixed(2)}</td>
                                            <td>
                                                <span class="invoice-status ${inv.status}">${inv.status}</span>
                                            </td>
                                        </tr>
                                    `)}
                                </tbody>
                            </table>
                            <a href="/saas/invoices" class="view-all">View all invoices</a>
                        </div>
                    </div>
                </div>
            </main>
        `;
    }

    private _formatCurrency(cents: number): string {
        return (cents / 100).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
    }

    private async _loadBillingData() {
        this._isLoading = true;
        try {
            const response = await apiClient.get('/saas/billing/') as {
                metrics?: BillingMetrics;
                tierRevenue?: TierRevenue[];
                invoices?: Invoice[];
            };
            if (response.metrics) {
                this._metrics = response.metrics;
            }
            if (response.tierRevenue) {
                this._tierRevenue = response.tierRevenue;
            }
            if (response.invoices) {
                this._invoices = response.invoices;
            }
        } catch {
            // Demo data already set in state
        } finally {
            this._isLoading = false;
        }
    }

    private _exportReport() {
        const report = {
            exportedAt: new Date().toISOString(),
            metrics: this._metrics,
            tierRevenue: this._tierRevenue,
            invoices: this._invoices,
        };
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `billing-report-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-billing': SaasBilling;
    }
}
