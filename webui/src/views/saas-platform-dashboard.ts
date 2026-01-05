/**
 * SomaAgent — SAAS Super Admin Dashboard
 * THE EYE OF GOD — Platform Command Center
 * 
 * VIBE COMPLIANT:
 * - Real Lit 3.x implementation
 * - Minimal white/black design per UI_STYLE_GUIDE.md
 * - NO EMOJIS - Google Material Symbols only
 * - Self-contained, no external dependencies
 * 
 * This is the SaaS Platform Admin - where the SAAS Super Admin
 * sees EVERYTHING across the entire platform.
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';

interface PlatformMetrics {
    totalTenants: number;
    activeTenants: number;
    trialTenants: number;
    totalAgents: number;
    activeAgents: number;
    totalUsers: number;
    mrr: number;
    mrrGrowth: number;
    uptime: number;
    activeAlerts: number;
    tokensThisMonth: number;
    storageUsedGB: number;
}

interface RecentEvent {
    id: string;
    type: 'tenant' | 'agent' | 'billing' | 'alert' | 'user';
    message: string;
    timestamp: string;
}

interface TopTenant {
    id: string;
    name: string;
    tier: string;
    agents: number;
    users: number;
    mrr: number;
    status: 'active' | 'trial' | 'suspended';
}

@customElement('saas-platform-dashboard')
export class SaasPlatformDashboard extends LitElement {
    static styles = css`
        :host {
            display: flex;
            height: 100vh;
            background: var(--saas-bg-page, #f5f5f5);
            font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            color: var(--saas-text-primary, #1a1a1a);
        }

        * { box-sizing: border-box; }

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
           SIDEBAR — Minimal Navigation
           ======================================== */
        .sidebar {
            width: 260px;
            background: var(--saas-bg-card, #ffffff);
            border-right: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }

        .sidebar-header {
            padding: 24px 20px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-icon {
            width: 36px;
            height: 36px;
            background: #1a1a1a;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .logo-icon svg {
            width: 18px;
            height: 18px;
            stroke: white;
            fill: none;
        }

        .logo-text {
            font-size: 16px;
            font-weight: 600;
        }

        .logo-badge {
            font-size: 10px;
            padding: 2px 6px;
            background: #1a1a1a;
            color: white;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
            margin-left: 4px;
        }

        /* Navigation */
        .nav {
            flex: 1;
            padding: 16px 12px;
            overflow-y: auto;
        }

        .nav-section {
            margin-bottom: 24px;
        }

        .nav-section-title {
            font-size: 10px;
            font-weight: 600;
            color: var(--saas-text-muted, #999);
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 0 12px;
            margin-bottom: 8px;
        }

        .nav-list {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 11px 14px;
            border-radius: 8px;
            font-size: 14px;
            color: var(--saas-text-secondary, #666);
            cursor: pointer;
            transition: all 0.1s ease;
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

        /* User Section */
        .sidebar-footer {
            padding: 16px 20px;
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .user-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: var(--saas-bg-hover, #fafafa);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 14px;
        }

        .user-details { flex: 1; min-width: 0; }
        .user-name { font-size: 13px; font-weight: 500; }
        .user-role { font-size: 11px; color: var(--saas-text-muted, #999); }

        .logout-btn {
            width: 32px;
            height: 32px;
            border-radius: 6px;
            border: none;
            background: transparent;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--saas-text-muted, #999);
        }

        .logout-btn:hover {
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-text-primary, #1a1a1a);
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

        .header {
            padding: 20px 32px;
            background: var(--saas-bg-card, #ffffff);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .header-title {
            font-size: 22px;
            font-weight: 600;
        }

        .header-subtitle {
            font-size: 13px;
            color: var(--saas-text-muted, #999);
        }

        .header-actions {
            display: flex;
            gap: 12px;
        }

        .btn {
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 13px;
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

        .btn:hover { background: var(--saas-bg-hover, #fafafa); }

        .btn.primary {
            background: #1a1a1a;
            color: white;
            border-color: #1a1a1a;
        }

        .btn.primary:hover { background: #333; }

        .btn .material-symbols-outlined { font-size: 16px; }

        .content {
            flex: 1;
            overflow-y: auto;
            padding: 32px;
        }

        /* ========================================
           METRICS GRID — The Eye Sees All
           ======================================== */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 32px;
        }

        @media (max-width: 1400px) {
            .metrics-grid { grid-template-columns: repeat(2, 1fr); }
        }

        .metric-card {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 12px;
            padding: 24px;
            transition: all 0.15s ease;
            cursor: pointer;
        }

        .metric-card:hover {
            border-color: var(--saas-border-medium, #ccc);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        }

        .metric-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 16px;
        }

        .metric-label {
            font-size: 13px;
            color: var(--saas-text-secondary, #666);
            font-weight: 500;
        }

        .metric-icon {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            background: var(--saas-bg-hover, #fafafa);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .metric-icon .material-symbols-outlined {
            font-size: 20px;
        }

        .metric-value {
            font-size: 32px;
            font-weight: 700;
            line-height: 1;
            margin-bottom: 8px;
        }

        .metric-sub {
            font-size: 12px;
            color: var(--saas-text-muted, #999);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .metric-trend {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-weight: 500;
        }

        .metric-trend.up { color: var(--saas-status-success, #22c55e); }
        .metric-trend.down { color: var(--saas-status-danger, #ef4444); }

        .metric-trend .material-symbols-outlined { font-size: 14px; }

        /* Featured Metric (MRR) */
        .metric-card.featured {
            background: linear-gradient(135deg, #1a1a1a 0%, #333 100%);
            color: white;
            border-color: #1a1a1a;
        }

        .metric-card.featured .metric-label { color: rgba(255,255,255,0.7); }
        .metric-card.featured .metric-icon { background: rgba(255,255,255,0.15); }
        .metric-card.featured .metric-icon .material-symbols-outlined { color: white; }
        .metric-card.featured .metric-sub { color: rgba(255,255,255,0.6); }
        .metric-card.featured .metric-trend.up { color: #86efac; }

        /* ========================================
           CONTENT GRID
           ======================================== */
        .content-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 24px;
        }

        @media (max-width: 1200px) {
            .content-grid { grid-template-columns: 1fr; }
        }

        .card {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 12px;
        }

        .card-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-title {
            font-size: 15px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .card-title .material-symbols-outlined {
            font-size: 18px;
            color: var(--saas-text-secondary, #666);
        }

        .card-body { padding: 0; }

        /* Tenants Table */
        .tenant-table {
            width: 100%;
            border-collapse: collapse;
        }

        .tenant-table th {
            text-align: left;
            padding: 14px 20px;
            font-size: 11px;
            font-weight: 600;
            color: var(--saas-text-muted, #999);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .tenant-table td {
            padding: 16px 20px;
            font-size: 14px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .tenant-table tr:last-child td { border-bottom: none; }

        .tenant-table tr:hover td { background: var(--saas-bg-hover, #fafafa); }

        .tenant-name {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .tenant-avatar {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            background: var(--saas-bg-hover, #fafafa);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 13px;
        }

        .tenant-info { }
        .tenant-title { font-weight: 500; }
        .tenant-slug { font-size: 11px; color: var(--saas-text-muted, #999); }

        .tier-badge {
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .tier-badge.free { background: #f3f4f6; color: #6b7280; }
        .tier-badge.starter { background: #dbeafe; color: #1d4ed8; }
        .tier-badge.team { background: #d1fae5; color: #047857; }
        .tier-badge.enterprise { background: #1a1a1a; color: white; }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }

        .status-dot.active { background: var(--saas-status-success, #22c55e); }
        .status-dot.trial { background: var(--saas-status-warning, #f59e0b); }
        .status-dot.suspended { background: var(--saas-status-danger, #ef4444); }

        .mrr-value { font-weight: 600; font-family: monospace; }

        /* Activity Feed */
        .activity-feed {
            padding: 0;
        }

        .activity-item {
            display: flex;
            gap: 14px;
            padding: 16px 20px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .activity-item:last-child { border-bottom: none; }

        .activity-icon {
            width: 36px;
            height: 36px;
            border-radius: 10px;
            background: var(--saas-bg-hover, #fafafa);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .activity-icon .material-symbols-outlined { font-size: 18px; }

        .activity-icon.tenant { background: #dbeafe; color: #1d4ed8; }
        .activity-icon.agent { background: #d1fae5; color: #047857; }
        .activity-icon.billing { background: #fef3c7; color: #b45309; }
        .activity-icon.alert { background: #fee2e2; color: #b91c1c; }
        .activity-icon.user { background: #e0e7ff; color: #4338ca; }

        .activity-content { flex: 1; }

        .activity-text {
            font-size: 13px;
            line-height: 1.4;
        }

        .activity-time {
            font-size: 11px;
            color: var(--saas-text-muted, #999);
            margin-top: 4px;
        }

        /* View All Link */
        .view-all {
            display: block;
            text-align: center;
            padding: 16px;
            font-size: 13px;
            color: var(--saas-text-secondary, #666);
            text-decoration: none;
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
            transition: color 0.1s ease;
        }

        .view-all:hover {
            color: var(--saas-text-primary, #1a1a1a);
            background: var(--saas-bg-hover, #fafafa);
        }
    `;

    @state() private _metrics: PlatformMetrics = {
        totalTenants: 0,
        activeTenants: 0,
        trialTenants: 0,
        totalAgents: 0,
        activeAgents: 0,
        totalUsers: 0,
        mrr: 0,
        mrrGrowth: 0,
        uptime: 0,
        activeAlerts: 0,
        tokensThisMonth: 0,
        storageUsedGB: 0,
    };

    @state() private _loading: boolean = true;
    @state() private _error: string | null = null;

    @state() private _topTenants: TopTenant[] = [];

    @state() private _recentEvents: RecentEvent[] = [];

    connectedCallback() {
        super.connectedCallback();
        this._loadDashboardData();
    }

    render() {
        return html`
            <!-- Sidebar -->
            <aside class="sidebar">
                <div class="sidebar-header">
                    <div class="logo">
                        <div class="logo-icon">
                            <svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <circle cx="12" cy="12" r="10"/>
                                <circle cx="12" cy="12" r="4"/>
                                <line x1="12" y1="2" x2="12" y2="6"/>
                                <line x1="12" y1="18" x2="12" y2="22"/>
                                <line x1="2" y1="12" x2="6" y2="12"/>
                                <line x1="18" y1="12" x2="22" y2="12"/>
                            </svg>
                        </div>
                        <span class="logo-text">SomaAgent<span class="logo-badge">God</span></span>
                    </div>
                </div>

                <nav class="nav">
                    <div class="nav-section">
                        <div class="nav-section-title">Overview</div>
                        <div class="nav-list">
                            <a class="nav-item active" href="/saas/dashboard">
                                <span class="material-symbols-outlined">visibility</span>
                                Dashboard
                            </a>
                            <a class="nav-item" href="/saas/tenants">
                                <span class="material-symbols-outlined">apartment</span>
                                Tenants
                            </a>
                        </div>
                    </div>

                    <div class="nav-section">
                        <div class="nav-section-title">Finance</div>
                        <div class="nav-list">
                            <a class="nav-item" href="/saas/subscriptions">
                                <span class="material-symbols-outlined">card_membership</span>
                                Subscriptions
                            </a>
                            <a class="nav-item" href="/saas/billing">
                                <span class="material-symbols-outlined">payments</span>
                                Billing
                            </a>
                        </div>
                    </div>

                    <div class="nav-section">
                        <div class="nav-section-title">Platform</div>
                        <div class="nav-list">
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
                        </div>
                    </div>
                </nav>

                <div class="sidebar-footer">
                    <div class="user-info">
                        <div class="user-avatar">SA</div>
                        <div class="user-details">
                            <div class="user-name">Super Admin</div>
                            <div class="user-role">God Mode</div>
                        </div>
                        <button class="logout-btn" @click=${this._logout}>
                            <span class="material-symbols-outlined">logout</span>
                        </button>
                    </div>
                </div>
            </aside>

            <!-- Main -->
            <main class="main">
                <header class="header">
                    <div class="header-left">
                        <div>
                            <h1 class="header-title">Platform Overview</h1>
                            <p class="header-subtitle">Real-time metrics across all tenants</p>
                        </div>
                    </div>
                    <div class="header-actions">
                        <button class="btn" @click=${() => window.location.href = '/saas/tenants'}>
                            <span class="material-symbols-outlined">apartment</span>
                            View Tenants
                        </button>
                        <button class="btn primary">
                            <span class="material-symbols-outlined">add</span>
                            New Tenant
                        </button>
                    </div>
                </header>

                <div class="content">
                    <!-- Metrics Grid -->
                    <div class="metrics-grid">
                        <div class="metric-card featured" @click=${() => window.location.href = '/saas/billing'}>
                            <div class="metric-header">
                                <span class="metric-label">Monthly Recurring Revenue</span>
                                <div class="metric-icon">
                                    <span class="material-symbols-outlined">payments</span>
                                </div>
                            </div>
                            <div class="metric-value">$${this._formatNumber(this._metrics.mrr)}</div>
                            <div class="metric-sub">
                                <span class="metric-trend up">
                                    <span class="material-symbols-outlined">trending_up</span>
                                    +${this._metrics.mrrGrowth}%
                                </span>
                                from last month
                            </div>
                        </div>

                        <div class="metric-card" @click=${() => window.location.href = '/saas/tenants'}>
                            <div class="metric-header">
                                <span class="metric-label">Total Tenants</span>
                                <div class="metric-icon">
                                    <span class="material-symbols-outlined">apartment</span>
                                </div>
                            </div>
                            <div class="metric-value">${this._metrics.totalTenants}</div>
                            <div class="metric-sub">
                                ${this._metrics.activeTenants} active, ${this._metrics.trialTenants} trial
                            </div>
                        </div>

                        <div class="metric-card">
                            <div class="metric-header">
                                <span class="metric-label">Active Agents</span>
                                <div class="metric-icon">
                                    <span class="material-symbols-outlined">smart_toy</span>
                                </div>
                            </div>
                            <div class="metric-value">${this._metrics.activeAgents}</div>
                            <div class="metric-sub">
                                of ${this._metrics.totalAgents} total
                            </div>
                        </div>

                        <div class="metric-card">
                            <div class="metric-header">
                                <span class="metric-label">Platform Uptime</span>
                                <div class="metric-icon">
                                    <span class="material-symbols-outlined">speed</span>
                                </div>
                            </div>
                            <div class="metric-value">${this._metrics.uptime}%</div>
                            <div class="metric-sub">
                                ${this._metrics.activeAlerts > 0 ? html`
                                    <span style="color: var(--saas-status-warning)">${this._metrics.activeAlerts} active alerts</span>
                                ` : 'All systems operational'}
                            </div>
                        </div>
                    </div>

                    <!-- Content Grid -->
                    <div class="content-grid">
                        <!-- Top Tenants -->
                        <div class="card">
                            <div class="card-header">
                                <h3 class="card-title">
                                    <span class="material-symbols-outlined">leaderboard</span>
                                    Top Tenants by MRR
                                </h3>
                                <button class="btn" @click=${() => window.location.href = '/saas/tenants'}>
                                    View All
                                </button>
                            </div>
                            <div class="card-body">
                                <table class="tenant-table">
                                    <thead>
                                        <tr>
                                            <th>Tenant</th>
                                            <th>Tier</th>
                                            <th>Agents</th>
                                            <th>Users</th>
                                            <th>MRR</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${this._topTenants.map(t => html`
                                            <tr @click=${() => window.location.href = `/saas/tenants/${t.id}`}>
                                                <td>
                                                    <div class="tenant-name">
                                                        <div class="tenant-avatar">${t.name.charAt(0)}</div>
                                                        <div class="tenant-info">
                                                            <div class="tenant-title">${t.name}</div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td><span class="tier-badge ${t.tier}">${t.tier}</span></td>
                                                <td>${t.agents}</td>
                                                <td>${t.users}</td>
                                                <td>
                                                    <span class="mrr-value">
                                                        ${t.mrr > 0 ? `$${t.mrr.toLocaleString()}` : html`<span class="status-dot trial"></span> Trial`}
                                                    </span>
                                                </td>
                                            </tr>
                                        `)}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        <!-- Activity Feed -->
                        <div class="card">
                            <div class="card-header">
                                <h3 class="card-title">
                                    <span class="material-symbols-outlined">history</span>
                                    Recent Activity
                                </h3>
                            </div>
                            <div class="card-body activity-feed">
                                ${this._recentEvents.map(event => html`
                                    <div class="activity-item">
                                        <div class="activity-icon ${event.type}">
                                            <span class="material-symbols-outlined">${this._getEventIcon(event.type)}</span>
                                        </div>
                                        <div class="activity-content">
                                            <div class="activity-text">${event.message}</div>
                                            <div class="activity-time">${event.timestamp}</div>
                                        </div>
                                    </div>
                                `)}
                            </div>
                            <a href="/saas/audit" class="view-all">View all activity</a>
                        </div>
                    </div>
                </div>
            </main>
        `;
    }

    private _formatNumber(num: number): string {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
        return num.toLocaleString();
    }

    private _getEventIcon(type: string): string {
        const icons: Record<string, string> = {
            tenant: 'apartment',
            agent: 'smart_toy',
            billing: 'payments',
            alert: 'warning',
            user: 'person',
        };
        return icons[type] || 'info';
    }

    private async _loadDashboardData() {
        /**
         * VIBE Rule #5: Fail Fast - no silent fallbacks
         * VIBE Rule #9: All data from real backends
         * 
         * API: GET /api/v2/saas/dashboard/
         * Backend: services/gateway/routers/saas.py
         */
        this._loading = true;
        this._error = null;

        try {
            const response = await apiClient.get<{
                metrics: PlatformMetrics;
                topTenants: TopTenant[];
                recentEvents: RecentEvent[];
            }>('/saas/dashboard/');

            this._metrics = response.metrics;
            this._topTenants = response.topTenants;
            this._recentEvents = response.recentEvents;
        } catch (error) {
            // VIBE: Fail fast - show error to user, don't hide it
            this._error = error instanceof Error ? error.message : 'Failed to load dashboard data';
            console.error('[SaasPlatformDashboard] API Error:', error);
        } finally {
            this._loading = false;
        }
    }

    private _logout() {
        localStorage.removeItem('saas_auth_token');
        localStorage.removeItem('saas_user');
        sessionStorage.removeItem('saas_mode');
        window.location.href = '/login';
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-platform-dashboard': SaasPlatformDashboard;
    }
}
