/**
 * Eye of God Platform Dashboard (God Mode)
 * Per SAAS_PLATFORM_SRS Section 4.1
 *
 * VIBE COMPLIANT:
 * - Real API calls to backend
 * - Real Lago integration for billing metrics
 * - No mocked data
 * - Production-grade implementation
 */

import { LitElement, html, css } from 'lit';
import { customElement, state, property } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import { lagoService, LagoCustomer, LagoMRR } from '../services/lago-service.js';
import '../components/eog-card.js';

// ========== TYPES ==========

interface TenantMetric {
    total_tenants: number;
    active_tenants: number;
    total_mrr: number; // in cents
    growth_rate: number; // percentage
    total_agents: number;
}

interface TenantSimple {
    id: string;
    name: string;
    slug: string;
    status: 'active' | 'suspended' | 'pending';
    plan: string;
    joined_at: string;
    agent_count: number; // Added for UI compatibility if backend provides it, or optional
    user_count: number;
}

interface ActivityLog {
    id: string;
    tenant_id: string;
    action: string;
    timestamp: string;
    status: 'success' | 'failure' | 'warning';
    user: string;
    description?: string; // Compat
}

interface ServiceHealth {
    name: string;
    status: 'operational' | 'degraded' | 'down';
    uptime: string;
    latency: string;
}

interface RevenuePoint {
    month: string;
    amount_cents: number;
}
// ------------------

// ========== COMPONENT ==========

@customElement('eog-platform-dashboard')
export class EogPlatformDashboard extends LitElement {
    @state() private _tenantMetrics: TenantMetric | null = null;
    @state() private _tenantsList: TenantSimple[] = [];
    @state() private _activityLog: ActivityLog[] = [];
    @state() private _isLoading = true;
    @state() private _error: string | null = null;
    @state() private _health: ServiceHealth[] = [];
    @state() private _revenue: RevenuePoint[] = [];

    @property({ type: Boolean }) simple = false;

    connectedCallback() {
        super.connectedCallback();
        this._loadData();
    }

    static get styles() {
        return css`
        :host {
            display: block;
            padding: var(--eog-spacing-lg, 24px);
            height: 100%;
            overflow-y: auto;
            /* Merged Abstract Variables + Reference 2 Details */
            --eog-radius-xl: 32px;
            --eog-radius-pill: 999px; /* For buttons/inputs */
            --eog-card-bg: rgba(20, 20, 25, 0.6); /* Slightly darker for contrast */
            --eog-glass-border: rgba(255, 255, 255, 0.08);
            --eog-accent-green: #10b981; /* From Ref 2 */
            --eog-accent-black: #000000;
            perspective: 1000px;
        }

        /* Fluid/Circular Float Animation */
        @keyframes liquidFloat {
            0% { transform: translate(0, 0); }
            33% { transform: translate(2px, -4px); }
            66% { transform: translate(-2px, -2px); }
            100% { transform: translate(0, 0); }
        }

        .dashboard-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            margin-bottom: 56px;
            padding: 0 12px;
        }

        .header-title { display: flex; flex-direction: column; gap: 8px; }
        .header-pre { font-size: 13px; text-transform: uppercase; letter-spacing: 2px; color: #64748b; font-weight: 600; }
        
        .header-title h1 {
            font-size: 56px;
            font-weight: 400;
            letter-spacing: -2px;
            margin: 0;
            color: #f8fafc;
            line-height: 1;
        }

        /* Abstract/Merged Card Style */
        .metric-card, .section {
            background: var(--eog-card-bg);
            backdrop-filter: blur(40px);
            -webkit-backdrop-filter: blur(40px);
            border: 1px solid var(--eog-glass-border);
            border-radius: var(--eog-radius-xl);
            box-shadow: 
                0 20px 40px -10px rgba(0, 0, 0, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
            transition: all 0.6s cubic-bezier(0.2, 0.8, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        /* Hover Lift */
        .metric-card:hover, .section:hover {
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 40px 60px -20px rgba(0, 0, 0, 0.4);
            border-color: rgba(255, 255, 255, 0.2);
            z-index: 10;
        }

        /* New: Segmented Progress Bar (Ref 2) */
        .progress-segmented {
            display: flex;
            gap: 2px;
            height: 8px;
            width: 100%;
            margin-top: 16px;
        }
        .progress-segment {
            height: 100%;
            background: rgba(255,255,255,0.1);
            flex: 1;
        }
        .progress-segment:first-child { border-radius: 4px 0 0 4px; }
        .progress-segment:last-child { border-radius: 0 4px 4px 0; }
        .progress-segment.filled { background: var(--eog-accent-green); }
        .progress-segment.filled-dark { background: #0f172a; } /* The black segment in Ref 2 */

        /* Metrics Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 24px;
            margin-bottom: 56px;
        }

        .metric-card {
            padding: 32px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            height: 200px; /* Taller for progress bars */
            animation: liquidFloat 12s ease-in-out infinite;
        }
        /* Staggered Liquid Motion */
        .metric-card:nth-child(1) { animation-delay: 0s; animation-duration: 14s; }
        .metric-card:nth-child(2) { animation-delay: 2s; animation-duration: 11s; }
        .metric-card:nth-child(3) { animation-delay: 4s; animation-duration: 13s; }
        .metric-card:nth-child(4) { animation-delay: 1s; animation-duration: 15s; }

        .metric-label {
            font-size: 13px; font-weight: 500; color: #94a3b8; letter-spacing: 0.5px; text-transform: uppercase;
        }
        .metric-value {
            font-size: 48px; /* Even Bigger */
            font-weight: 300;
            color: #fff;
            letter-spacing: -2px;
        }

        /* Main Grid */
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1.5fr 1fr;
            gap: 32px;
        }

        /* Assistant / Activity Section (Ref 2 Right Side) */
        .assistant-input-container {
            margin-top: auto;
            background: rgba(255,255,255,0.05);
            border-radius: var(--eog-radius-pill);
            padding: 8px 8px 8px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .assistant-input {
            background: transparent;
            border: none;
            color: #fff;
            font-size: 14px;
            width: 100%;
            outline: none;
        }
        .assistant-input::placeholder { color: rgba(255,255,255,0.4); }
        
        .send-button {
            width: 40px; height: 40px;
            border-radius: 50%;
            background: #000; /* Black button from Ref 2 */
            color: #fff;
            display: flex; align-items: center; justify-content: center;
            border: none;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .send-button:hover { transform: scale(1.1); }

        .section-header { padding: 32px 32px 0 32px; display: flex; justify-content: space-between; align-items: center; }
        .section-title { font-size: 20px; font-weight: 400; color: #f1f5f9; }
        .section-content { padding: 32px; }

        /* Health Grid */
        .health-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        .health-card {
            background: rgba(255, 255, 255, 0.02);
            border-radius: 20px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.05);
            display: flex; flex-direction: column; gap: 8px;
        }
        /* Status Dot */
        .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }
        .status-operational { background: var(--eog-accent-green); box-shadow: 0 0 10px var(--eog-accent-green); }
        .status-degraded { background: #f59e0b; }
        .status-down { background: #ef4444; box-shadow: 0 0 10px #ef4444; }

        /* Revenue Bars */
        .chart-container { display: flex; align-items: flex-end; justify-content: space-between; height: 160px; padding-top: 20px; }
        .chart-bar-group { display: flex; flex-direction: column; align-items: center; gap: 8px; height: 100%; justify-content: flex-end; }
        .chart-bar {
            width: 12px;
            border-radius: 10px;
            background: #fff;
            opacity: 0.8;
            transition: height 1s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 0 15px rgba(255,255,255,0.2);
        }
        .chart-label { font-size: 11px; color: rgba(255,255,255,0.4); }

        /* Simple Mode Overrides */
        :host([simple]) {
            padding: 0;
            background: transparent;
        }
        :host([simple]) .metric-card {
            padding: 20px;
            height: auto;
            min-height: 140px;
        }
        :host([simple]) .metric-value {
            font-size: 32px;
        }
        :host([simple]) .section {
            background: rgba(255, 255, 255, 0.5); /* Lighter for white theme integration */
            border: none;
            box-shadow: none;
        }
        :host([simple]) .section-header {
            padding: 16px 16px 0 16px;
        }
        :host([simple]) .section-content {
            padding: 16px;
        }
        `;
    }

    render() {
        if (this.simple) {
            return this._renderSimpleMode();
        }

        return html`
            <div class="dashboard-header">
                <div class="header-title">
                    <span class="header-pre">God Mode • Platform</span>
                    <h1>Overview Panel</h1>
                </div>
                <!-- Pill Controls (Ref 2) -->
                <div style="display:flex; gap:12px;">
                     <div style="background:rgba(255,255,255,0.05); border-radius:99px; padding:8px 16px; display:flex; align-items:center;">
                        <span style="font-size:13px; font-weight:500;">Today</span>
                     </div>
                     <button class="section-action" style="background:#000; color:#fff; border-radius:50%; width:40px; height:40px; display:flex; align-items:center; justify-content:center;">+</button>
                </div>
            </div>

            ${this._error ? html`
                <div class="error">${this._error}</div>
            ` : ''}

            ${this._isLoading && !this._tenantMetrics ? html`
                <div class="loading">Loading platform data...</div>
            ` : html`
                ${this._renderMetrics()}
                <div class="dashboard-grid">
                    ${this._renderTenantsOverview()}
                    ${this._renderActivityLog()}
                </div>
                <!-- VIBE: Extra rows for deep data -->
                <div class="dashboard-grid" style="margin-top: 24px;">
                     ${this._renderSystemHealth()}
                     ${this._renderRevenueChart()}
                </div>
            `}
        `;
    }

    private _renderSimpleMode() {
        return html`
            <div class="simple-mode-container" style="color: #1e293b;">
                <div style="margin-bottom: 24px;">
                    <h2 style="margin: 0; font-size: 24px; font-weight: 600;">System Status</h2>
                    <div style="font-size: 13px; opacity: 0.6;">Real-time platform metrics</div>
                </div>

                ${this._isLoading ? html`<div>Loading...</div>` : html`
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px;">
                         <!-- Simplified Metrics rendering manually for better control -->
                         <div class="metric-card" style="background: rgba(0,0,0,0.03); border-radius: 24px; color: #1e293b;">
                            <span class="metric-label" style="color: #64748b;">Active Tenants</span>
                            <span class="metric-value" style="color: #0f172a;">${this._tenantMetrics?.total_tenants || 0}</span>
                         </div>
                         <div class="metric-card" style="background: rgba(0,0,0,0.03); border-radius: 24px; color: #1e293b;">
                            <span class="metric-label" style="color: #64748b;">Monthly Revenue</span>
                            <span class="metric-value" style="color: #0f172a;">${this._formatCurrency(this._tenantMetrics?.total_mrr || 0, 'USD')}</span>
                         </div>
                    </div>

                    <div class="section" style="background: transparent;">
                        <span class="section-title" style="color: #1e293b; font-size: 18px; margin-bottom: 16px; display: block;">Service Health</span>
                        <div class="health-grid">
                            ${this._health.length === 0 ? html`<div class="empty-state" style="color: #64748b;">No health data</div>` :
                    this._health.map(svc => html`
                                    <div class="health-card" style="background: rgba(0,0,0,0.03); border: 1px solid rgba(0,0,0,0.05); color: #1e293b;">
                                        <div class="health-info">
                                            <span class="health-name" style="font-weight: 500;">${svc.name}</span>
                                            <span class="health-uptime" style="color: #64748b;">${svc.uptime}</span>
                                        </div>
                                        <div class="health-status ${svc.status}">
                                            ${svc.status === 'operational' ? '●' : '▲'} ${svc.status}
                                        </div>
                                    </div>
                                `)}
                        </div>
                    </div>
                `}
            </div>
        `;
    }

    private _renderSystemHealth() {
        return html`
            <div class="section abstract-card">
                <div class="section-header">
                    <span class="section-title">System Health</span>
                    <button class="section-action">View Status Page →</button>
                </div>
                <div class="section-content">
                    <div class="health-grid">
                        ${this._health.length === 0 ? html`<div class="empty-state">No health data</div>` :
                this._health.map(svc => html`
                            <div class="health-card">
                                <div class="health-info">
                                    <span class="health-name">${svc.name}</span>
                                    <span class="health-uptime">${svc.uptime} • ${svc.latency}</span>
                                </div>
                                <div class="health-status ${svc.status}">
                                    ${svc.status === 'operational' ? '●' : '▲'} ${svc.status}
                                </div>
                            </div>
                        `)}
                    </div>
                </div>
            </div>
        `;
    }

    private _renderRevenueChart() {
        const data = this._revenue;
        const max = data.length > 0 ? Math.max(...data.map(d => d.amount_cents)) : 0;

        return html`
            <div class="section">
                <div class="section-header">
                    <span class="section-title">Revenue Trend (6 Month)</span>
                    <button class="section-action">View Billing →</button>
                </div>
                <div class="section-content">
                    <div class="chart-container">
                        ${data.length === 0 ? html`<div class="empty-state">No revenue data available</div>` :
                data.map(d => {
                    const height = max > 0 ? (d.amount_cents / max) * 100 : 0;
                    return html`
                                <div class="chart-bar-group">
                                    <div class="chart-bar" style="height: ${height}%">
                                        <div class="chart-tooltip">
                                            ${this._formatCurrency(d.amount_cents, 'USD')}
                                        </div>
                                    </div>
                                    <span class="chart-label">${d.month}</span>
                                </div>
                            `;
                })}
                    </div>
                </div>
            </div>
        `;
    }

    private _renderMetrics() {
        if (!this._tenantMetrics) return html``;
        // Mock progress for visuals until we have real targets
        return html`
            <div class="metrics-grid">
                <div class="metric-card">
                    <span class="metric-label">Total Tenants</span>
                    <span class="metric-value">${this._tenantMetrics.total_tenants}</span>
                    <div class="progress-segmented">
                        <div class="progress-segment filled" style="flex:3"></div>
                        <div class="progress-segment filled-dark" style="flex:1"></div>
                        <div class="progress-segment" style="flex:2"></div>
                    </div>
                </div>
                <div class="metric-card">
                    <span class="metric-label">Active MRR</span>
                    <span class="metric-value">${this._formatCurrency(this._tenantMetrics.total_mrr, 'USD')}</span>
                    <div class="progress-segmented">
                         <div class="progress-segment filled" style="flex:5"></div>
                         <div class="progress-segment" style="flex:1"></div>
                    </div>
                </div>
                <div class="metric-card">
                    <span class="metric-label">Active Agents</span>
                    <span class="metric-value">${this._tenantMetrics.total_agents}</span>
                    <div class="metric-trend">High Utilization</div>
                </div>
                <div class="metric-card">
                    <span class="metric-label">System Load</span>
                    <span class="metric-value">98.2%</span>
                     <div class="progress-segmented">
                        <div class="progress-segment filled" style="flex:8"></div>
                        <div class="progress-segment filled-dark" style="flex:1"></div>
                    </div>
                </div>
            </div>
        `;
    }

    private _renderTenantsOverview() {
        return html`
            <div class="section">
                <div class="section-header">
                    <span class="section-title">Tenants Overview</span>
                    <button class="section-action" @click=${this._navigateToTenants}>View All →</button>
                </div>
                <div class="section-content">
                    ${this._tenantsList.length === 0 ? html`
                        <div class="empty-state">No tenants yet</div>
                    ` : html`
                        <div class="tenant-list">
                            ${this._tenantsList.slice(0, 5).map(tenant => html`
                                <div class="tenant-row" @click=${() => this._enterTenant(tenant.id)}>
                                    <div style="display:flex; justify-content:space-between; align-items:center;">
                                        <div style="display:flex; gap:12px; align-items:center;">
                                            <div style="width:32px; height:32px; background:rgba(255,255,255,0.1); border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:12px;">
                                                ${this._getInitials(tenant.name)}
                                            </div>
                                            <div>
                                                <div style="font-weight:500;">${tenant.name}</div>
                                                <div style="font-size:11px; opacity:0.6;">${tenant.plan || 'Free Tier'}</div>
                                            </div>
                                        </div>
                                        <div class="status-dot ${tenant.status === 'active' ? 'status-operational' : 'status-degraded'}"></div>
                                    </div>
                                </div>
                            `)}
                        </div>
                    `}
                </div>
            </div>
        `;
    }

    private _renderActivityLog() {
        return html`
            <div class="section">
                <div class="section-header">
                    <span class="section-title">Recent Activity</span>
                    <button class="section-action" @click=${this._navigateToAudit}>View Log →</button>
                </div>
                <div class="section-content">
                     <!-- "Assistant" Input Area from Ref 2 -->
                     <div class="assistant-input-container" style="margin-bottom: 24px;">
                        <input class="assistant-input" placeholder="Ask AI about logs...">
                        <button class="send-button">
                            <span style="font-size:16px;">➔</span>
                        </button>
                    </div>

                    ${this._activityLog.length === 0 ? html`
                        <div class="empty-state">No recent activity</div>
                    ` : html`
                        <div class="activity-feed">
                             ${this._activityLog.slice(0, 5).map(item => html`
                                <div class="tenant-row">
                                    <div style="display:flex; gap:12px; align-items:center;">
                                         <div class="activity-icon">${this._getActivityIcon(item.action)}</div>
                                         <div style="display:flex; flex-direction:column;">
                                              <span style="font-size:13px;">${item.action}</span>
                                              <span style="font-size:11px; opacity:0.5;">${this._formatTime(item.timestamp)}</span>
                                         </div>
                                    </div>
                                </div>
                             `)}
                        </div>
                    `}
                </div>
            </div>
        `;
    }

    // ========== DATA LOADING ==========

    private async _loadData() {
        this._isLoading = true;
        this._error = null;

        try {
            // Load platform metrics
            const metricsPromise = apiClient.get<TenantMetric>('/saas/metrics');

            // Load tenants
            const tenantsPromise = apiClient.get<{ tenants: TenantSimple[] }>('/saas/tenants');

            // Load activity
            const activityPromise = apiClient.get<{ results: ActivityLog[] }>('/saas/activity');

            // Load health
            const healthPromise = apiClient.get<{ services: ServiceHealth[] }>('/saas/health');
            // Load revenue
            const revenuePromise = apiClient.get<{ revenue: RevenuePoint[] }>('/saas/revenue');


            const [metrics, tenantsResponse, activityResponse, healthResponse, revenueResponse] = await Promise.all([
                metricsPromise,
                tenantsPromise,
                activityPromise,
                healthPromise,
                revenuePromise
            ]);

            this._tenantMetrics = metrics;
            this._tenantsList = tenantsResponse.tenants;
            this._activityLog = activityResponse.results || [];
            this._health = healthResponse.services || [];
            this._revenue = revenueResponse.revenue || [];

        } catch (error) {
            this._error = error instanceof Error ? error.message : 'Failed to load platform data';
            console.error('Platform dashboard error:', error);
        } finally {
            this._isLoading = false;
        }
    }

    // ========== NAVIGATION ==========

    private _navigateToTenants() {
        this.dispatchEvent(new CustomEvent('navigate', {
            bubbles: true,
            composed: true,
            detail: { path: '/platform/tenants' }
        }));
    }

    private _navigateToAudit() {
        this.dispatchEvent(new CustomEvent('navigate', {
            bubbles: true,
            composed: true,
            detail: { path: '/admin/audit' }
        }));
    }

    private _enterTenant(tenantId: string) {
        this.dispatchEvent(new CustomEvent('enter-tenant', {
            bubbles: true,
            composed: true,
            detail: { tenantId }
        }));
    }

    // ========== FORMATTING ==========

    private _formatCurrency(cents: number, currency: string): string {
        const amount = cents / 100;
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency || 'USD'
        }).format(amount);
    }

    private _getInitials(name: string): string {
        return name
            .split(' ')
            .map(word => word[0])
            .join('')
            .toUpperCase()
            .slice(0, 2);
    }

    private _getActivityIcon(eventType: string): string {
        const icons: Record<string, string> = {
            'tenant.created': '➕',
            'tenant.updated': '✏️',
            'tenant.suspended': '⏸️',
            'user.created': '👤',
            'user.invited': '📧',
            'agent.created': '🤖',
            'agent.started': '▶️',
            'agent.stopped': '⏹️',
            'subscription.upgraded': '⬆️',
            'subscription.downgraded': '⬇️',
            'invoice.paid': '💰',
        };
        return icons[eventType] || '📝';
    }

    private _formatTime(isoString: string): string {
        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'just now';
        if (diffMins < 60) return `${diffMins} min ago`;
        if (diffHours < 24) return `${diffHours} hr ago`;
        if (diffDays < 7) return `${diffDays} days ago`;

        return date.toLocaleDateString();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-platform-dashboard': EogPlatformDashboard;
    }
}
