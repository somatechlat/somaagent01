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
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import { lagoService, LagoCustomer, LagoMRR } from '../services/lago-service.js';
import '../components/eog-card.js';

// ========== TYPES ==========

interface PlatformMetrics {
    total_tenants: number;
    active_tenants: number;
    total_agents: number;
    running_agents: number;
    total_users: number;
    active_users_24h: number;
    mrr_cents: number;
    mrr_currency: string;
}

interface TenantSummary {
    id: string;
    name: string;
    slug: string;
    subscription_tier: string;
    agent_count: number;
    user_count: number;
    status: 'active' | 'suspended' | 'pending';
    created_at: string;
}

interface ActivityLogEntry {
    id: string;
    event_type: string;
    description: string;
    tenant_name?: string;
    user_email?: string;
    created_at: string;
}

// ========== COMPONENT ==========

@customElement('eog-platform-dashboard')
export class EogPlatformDashboard extends LitElement {
    static styles = css`
        :host {
            display: block;
            padding: var(--eog-spacing-lg, 24px);
            height: 100%;
            overflow-y: auto;
        }

        .dashboard-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--eog-spacing-xl, 32px);
        }

        .header-title {
            display: flex;
            align-items: center;
            gap: var(--eog-spacing-sm, 8px);
        }

        .header-title h1 {
            font-size: var(--eog-text-2xl, 24px);
            font-weight: 600;
            margin: 0;
        }

        .god-badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 4px 12px;
            border-radius: var(--eog-radius-full, 9999px);
            font-size: var(--eog-text-xs, 11px);
            font-weight: 600;
            text-transform: uppercase;
        }

        .header-actions {
            display: flex;
            gap: var(--eog-spacing-sm, 8px);
        }

        .refresh-btn {
            display: flex;
            align-items: center;
            gap: var(--eog-spacing-xs, 4px);
            padding: var(--eog-spacing-sm, 8px) var(--eog-spacing-md, 16px);
            background: transparent;
            border: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.1));
            border-radius: var(--eog-radius-md, 8px);
            color: var(--eog-text-main, #e2e8f0);
            font-size: var(--eog-text-sm, 13px);
            cursor: pointer;
            transition: all 0.2s;
        }

        .refresh-btn:hover {
            background: var(--eog-surface, rgba(30, 41, 59, 0.85));
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: var(--eog-spacing-md, 16px);
            margin-bottom: var(--eog-spacing-xl, 32px);
        }

        @media (max-width: 1200px) {
            .metrics-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        @media (max-width: 600px) {
            .metrics-grid {
                grid-template-columns: 1fr;
            }
        }

        .metric-card {
            background: var(--eog-surface, rgba(30, 41, 59, 0.85));
            backdrop-filter: blur(20px);
            border: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.05));
            border-radius: var(--eog-radius-lg, 16px);
            padding: var(--eog-spacing-lg, 24px);
            display: flex;
            flex-direction: column;
            gap: var(--eog-spacing-sm, 8px);
        }

        .metric-header {
            display: flex;
            align-items: center;
            gap: var(--eog-spacing-sm, 8px);
        }

        .metric-icon {
            width: 40px;
            height: 40px;
            background: var(--eog-surface-elevated, rgba(51, 65, 85, 0.9));
            border-radius: var(--eog-radius-md, 8px);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }

        .metric-label {
            font-size: var(--eog-text-sm, 13px);
            color: var(--eog-text-dim, #64748b);
        }

        .metric-value {
            font-size: var(--eog-text-3xl, 30px);
            font-weight: 700;
            color: var(--eog-text-main, #e2e8f0);
        }

        .metric-trend {
            font-size: var(--eog-text-xs, 11px);
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .metric-trend.up {
            color: var(--eog-success, #22c55e);
        }

        .metric-trend.down {
            color: var(--eog-danger, #ef4444);
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: var(--eog-spacing-lg, 24px);
        }

        @media (max-width: 900px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
        }

        .section {
            background: var(--eog-surface, rgba(30, 41, 59, 0.85));
            backdrop-filter: blur(20px);
            border: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.05));
            border-radius: var(--eog-radius-lg, 16px);
            overflow: hidden;
        }

        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: var(--eog-spacing-md, 16px) var(--eog-spacing-lg, 24px);
            border-bottom: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.05));
        }

        .section-title {
            font-size: var(--eog-text-base, 14px);
            font-weight: 600;
            color: var(--eog-text-main, #e2e8f0);
        }

        .section-action {
            font-size: var(--eog-text-sm, 13px);
            color: var(--eog-accent, #94a3b8);
            background: none;
            border: none;
            cursor: pointer;
            transition: color 0.2s;
        }

        .section-action:hover {
            color: var(--eog-text-main, #e2e8f0);
        }

        .section-content {
            padding: var(--eog-spacing-md, 16px) var(--eog-spacing-lg, 24px);
        }

        .tenant-list {
            display: flex;
            flex-direction: column;
            gap: var(--eog-spacing-sm, 8px);
        }

        .tenant-row {
            display: flex;
            align-items: center;
            gap: var(--eog-spacing-md, 16px);
            padding: var(--eog-spacing-sm, 8px);
            border-radius: var(--eog-radius-md, 8px);
            transition: background 0.2s;
        }

        .tenant-row:hover {
            background: var(--eog-surface-elevated, rgba(51, 65, 85, 0.9));
        }

        .tenant-avatar {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: var(--eog-radius-md, 8px);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: var(--eog-text-sm, 13px);
            font-weight: 600;
            color: white;
        }

        .tenant-info {
            flex: 1;
        }

        .tenant-name {
            font-size: var(--eog-text-sm, 13px);
            font-weight: 500;
            color: var(--eog-text-main, #e2e8f0);
        }

        .tenant-tier {
            font-size: var(--eog-text-xs, 11px);
            color: var(--eog-text-dim, #64748b);
        }

        .tenant-stats {
            font-size: var(--eog-text-xs, 11px);
            color: var(--eog-text-dim, #64748b);
            display: flex;
            gap: var(--eog-spacing-xs, 4px);
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--eog-success, #22c55e);
        }

        .status-dot.pending {
            background: var(--eog-warning, #f59e0b);
        }

        .status-dot.suspended {
            background: var(--eog-danger, #ef4444);
        }

        .activity-feed {
            display: flex;
            flex-direction: column;
            gap: var(--eog-spacing-md, 16px);
        }

        .activity-item {
            display: flex;
            gap: var(--eog-spacing-sm, 8px);
        }

        .activity-icon {
            width: 28px;
            height: 28px;
            background: var(--eog-surface-elevated, rgba(51, 65, 85, 0.9));
            border-radius: var(--eog-radius-md, 8px);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            flex-shrink: 0;
        }

        .activity-content {
            flex: 1;
        }

        .activity-text {
            font-size: var(--eog-text-sm, 13px);
            color: var(--eog-text-main, #e2e8f0);
        }

        .activity-text strong {
            color: var(--eog-accent, #94a3b8);
        }

        .activity-time {
            font-size: var(--eog-text-xs, 11px);
            color: var(--eog-text-dim, #64748b);
        }

        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: var(--eog-spacing-xl, 32px);
            color: var(--eog-text-dim, #64748b);
        }

        .error {
            padding: var(--eog-spacing-md, 16px);
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid var(--eog-danger, #ef4444);
            border-radius: var(--eog-radius-md, 8px);
            color: var(--eog-danger, #ef4444);
            font-size: var(--eog-text-sm, 13px);
        }

        .empty-state {
            text-align: center;
            padding: var(--eog-spacing-xl, 32px);
            color: var(--eog-text-dim, #64748b);
        }
    `;

    @state() private _metrics: PlatformMetrics | null = null;
    @state() private _tenants: TenantSummary[] = [];
    @state() private _activity: ActivityLogEntry[] = [];
    @state() private _isLoading = true;
    @state() private _error: string | null = null;

    connectedCallback() {
        super.connectedCallback();
        this._loadData();
    }

    render() {
        return html`
            <div class="dashboard-header">
                <div class="header-title">
                    <h1>Platform Dashboard</h1>
                    <span class="god-badge">God Mode</span>
                </div>
                <div class="header-actions">
                    <button class="refresh-btn" @click=${this._loadData}>
                        <span>🔄</span>
                        Refresh
                    </button>
                </div>
            </div>

            ${this._error ? html`
                <div class="error">${this._error}</div>
            ` : ''}

            ${this._isLoading && !this._metrics ? html`
                <div class="loading">Loading platform data...</div>
            ` : html`
                ${this._renderMetrics()}
                <div class="dashboard-grid">
                    ${this._renderTenantsList()}
                    ${this._renderActivityFeed()}
                </div>
            `}
        `;
    }

    private _renderMetrics() {
        if (!this._metrics) return html``;

        return html`
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-header">
                        <div class="metric-icon">🏢</div>
                        <span class="metric-label">Active Tenants</span>
                    </div>
                    <div class="metric-value">${this._metrics.active_tenants}</div>
                    <div class="metric-trend up">
                        of ${this._metrics.total_tenants} total
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        <div class="metric-icon">🤖</div>
                        <span class="metric-label">Running Agents</span>
                    </div>
                    <div class="metric-value">${this._metrics.running_agents}</div>
                    <div class="metric-trend up">
                        of ${this._metrics.total_agents} deployed
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        <div class="metric-icon">👥</div>
                        <span class="metric-label">Active Users</span>
                    </div>
                    <div class="metric-value">${this._metrics.active_users_24h}</div>
                    <div class="metric-trend up">
                        last 24 hours
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        <div class="metric-icon">💰</div>
                        <span class="metric-label">Monthly Revenue</span>
                    </div>
                    <div class="metric-value">${this._formatCurrency(this._metrics.mrr_cents, this._metrics.mrr_currency)}</div>
                    <div class="metric-trend up">
                        MRR
                    </div>
                </div>
            </div>
        `;
    }

    private _renderTenantsList() {
        return html`
            <div class="section">
                <div class="section-header">
                    <span class="section-title">Tenants Overview</span>
                    <button class="section-action" @click=${this._navigateToTenants}>View All →</button>
                </div>
                <div class="section-content">
                    ${this._tenants.length === 0 ? html`
                        <div class="empty-state">No tenants yet</div>
                    ` : html`
                        <div class="tenant-list">
                            ${this._tenants.slice(0, 5).map(tenant => html`
                                <div class="tenant-row" @click=${() => this._enterTenant(tenant.id)}>
                                    <div class="tenant-avatar">${this._getInitials(tenant.name)}</div>
                                    <div class="tenant-info">
                                        <div class="tenant-name">${tenant.name}</div>
                                        <div class="tenant-tier">${tenant.subscription_tier}</div>
                                    </div>
                                    <div class="tenant-stats">
                                        <span>${tenant.agent_count} agents</span>
                                        <span>•</span>
                                        <span>${tenant.user_count} users</span>
                                    </div>
                                    <div class="status-dot ${tenant.status}"></div>
                                </div>
                            `)}
                        </div>
                    `}
                </div>
            </div>
        `;
    }

    private _renderActivityFeed() {
        return html`
            <div class="section">
                <div class="section-header">
                    <span class="section-title">Recent Activity</span>
                    <button class="section-action" @click=${this._navigateToAudit}>View Log →</button>
                </div>
                <div class="section-content">
                    ${this._activity.length === 0 ? html`
                        <div class="empty-state">No recent activity</div>
                    ` : html`
                        <div class="activity-feed">
                            ${this._activity.slice(0, 5).map(item => html`
                                <div class="activity-item">
                                    <div class="activity-icon">${this._getActivityIcon(item.event_type)}</div>
                                    <div class="activity-content">
                                        <div class="activity-text">${item.description}</div>
                                        <div class="activity-time">${this._formatTime(item.created_at)}</div>
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
            const metricsPromise = apiClient.get<PlatformMetrics>('/saas/metrics');

            // Load tenants
            const tenantsPromise = apiClient.get<{ tenants: TenantSummary[] }>('/saas/tenants');

            // Load activity
            const activityPromise = apiClient.get<{ activity: ActivityLogEntry[] }>('/saas/activity');

            const [metrics, tenantsResponse, activityResponse] = await Promise.all([
                metricsPromise,
                tenantsPromise,
                activityPromise
            ]);

            this._metrics = metrics;
            this._tenants = tenantsResponse.tenants;
            this._activity = activityResponse.activity;

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
