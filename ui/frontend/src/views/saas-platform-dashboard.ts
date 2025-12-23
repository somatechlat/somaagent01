/**
 * SAAS Platform Dashboard — Light Theme
 * Admin overview with stat cards, trend badges, and glassmorphism modals
 *
 * VIBE COMPLIANT:
 * - Real Lit 3.x Web Component
 * - Light/dark theme support via CSS tokens
 * - Stat cards with status indicators
 * - Click cards to open detailed modals
 * - Uses SAAS component system
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import '../components/saas-stat-card.js';
import '../components/saas-glass-modal.js';
import '../components/saas-status-badge.js';
import '../components/saas-data-table.js';
import '../components/saas-sidebar.js';
import type { NavSection } from '../components/saas-sidebar.js';
import type { TableColumn } from '../components/saas-data-table.js';

interface DashboardMetrics {
    totalTenants: number;
    tenantsTrend: number;
    totalAgents: number;
    agentsTrend: number;
    mrr: number;
    mrrTrend: number;
    uptime: number;
    activeAlerts: number;
}

interface TenantSummary {
    id: string;
    name: string;
    agents: number;
    users: number;
    status: 'active' | 'trial' | 'suspended';
    mrr: number;
}

@customElement('saas-platform-dashboard')
export class SaasPlatformDashboard extends LitElement {
    static styles = css`
        :host {
            display: block;
            min-height: 100vh;
            background: var(--saas-bg-page, #f5f5f5);
            color: var(--saas-text-primary, #1a1a1a);
            font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, sans-serif);
        }

        * { box-sizing: border-box; }

        .layout {
            display: flex;
            min-height: 100vh;
        }

        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
        }

        /* Header */
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: var(--saas-space-md, 16px) var(--saas-space-lg, 24px);
            background: var(--saas-bg-card, #ffffff);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .header-title {
            font-size: var(--saas-text-xl, 22px);
            font-weight: var(--saas-font-semibold, 600);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: var(--saas-space-sm, 8px);
        }

        .search-input {
            width: 280px;
            padding: var(--saas-space-sm, 8px) var(--saas-space-md, 16px);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: var(--saas-radius-md, 8px);
            font-size: var(--saas-text-sm, 13px);
            background: var(--saas-bg-page, #f5f5f5);
        }

        .search-input:focus {
            outline: none;
            border-color: var(--saas-accent, #1a1a1a);
        }

        .btn-primary {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: var(--saas-space-sm, 8px) var(--saas-space-md, 16px);
            background: var(--saas-accent, #1a1a1a);
            color: var(--saas-text-inverse, #ffffff);
            border: none;
            border-radius: var(--saas-radius-md, 8px);
            font-size: var(--saas-text-sm, 13px);
            font-weight: var(--saas-font-medium, 500);
            cursor: pointer;
            transition: background var(--saas-transition-fast, 150ms ease);
        }

        .btn-primary:hover {
            background: var(--saas-accent-hover, #333333);
        }

        /* Content */
        .content {
            flex: 1;
            padding: var(--saas-space-lg, 24px);
            overflow-y: auto;
        }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: var(--saas-space-md, 16px);
            margin-bottom: var(--saas-space-lg, 24px);
        }

        @media (max-width: 1200px) {
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }

        /* Section */
        .section {
            margin-bottom: var(--saas-space-lg, 24px);
        }

        .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: var(--saas-space-md, 16px);
        }

        .section-title {
            font-size: var(--saas-text-lg, 18px);
            font-weight: var(--saas-font-semibold, 600);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .section-actions {
            display: flex;
            gap: var(--saas-space-sm, 8px);
        }

        .btn-secondary {
            padding: 6px 12px;
            background: var(--saas-bg-card, #ffffff);
            color: var(--saas-text-secondary, #666666);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: var(--saas-radius-md, 8px);
            font-size: var(--saas-text-sm, 13px);
            cursor: pointer;
            transition: all var(--saas-transition-fast, 150ms ease);
        }

        .btn-secondary:hover {
            background: var(--saas-bg-hover, #fafafa);
            border-color: var(--saas-border-medium, #cccccc);
        }

        /* Two Column Layout */
        .two-cols {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: var(--saas-space-lg, 24px);
        }

        @media (max-width: 1024px) {
            .two-cols {
                grid-template-columns: 1fr;
            }
        }

        /* Card */
        .card {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: var(--saas-radius-lg, 12px);
            padding: var(--saas-space-lg, 24px);
        }

        .card-title {
            font-size: var(--saas-text-md, 16px);
            font-weight: var(--saas-font-semibold, 600);
            margin-bottom: var(--saas-space-md, 16px);
        }

        /* Activity List */
        .activity-list {
            display: flex;
            flex-direction: column;
            gap: var(--saas-space-sm, 8px);
        }

        .activity-item {
            display: flex;
            align-items: flex-start;
            gap: var(--saas-space-sm, 8px);
            padding: var(--saas-space-sm, 8px) 0;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .activity-item:last-child {
            border-bottom: none;
        }

        .activity-icon {
            width: 32px;
            height: 32px;
            border-radius: var(--saas-radius-full, 9999px);
            background: var(--saas-bg-active, #f0f0f0);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            font-family: 'Material Symbols Outlined';
            font-size: 18px;
            color: var(--saas-text-secondary, #666666);
        }

        .activity-content {
            flex: 1;
        }

        .activity-text {
            font-size: var(--saas-text-sm, 13px);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .activity-time {
            font-size: var(--saas-text-xs, 11px);
            color: var(--saas-text-muted, #999999);
            margin-top: 2px;
        }
    `;

    @state() private _metrics: DashboardMetrics = {
        totalTenants: 124,
        tenantsTrend: 12,
        totalAgents: 847,
        agentsTrend: 8.5,
        mrr: 48250,
        mrrTrend: 15.3,
        uptime: 99.97,
        activeAlerts: 3
    };

    @state() private _topTenants: TenantSummary[] = [
        { id: '1', name: 'Acme Corporation', agents: 45, users: 1240, status: 'active', mrr: 4500 },
        { id: '2', name: 'TechStart Inc', agents: 32, users: 890, status: 'active', mrr: 3200 },
        { id: '3', name: 'Global Services', agents: 28, users: 756, status: 'active', mrr: 2800 },
        { id: '4', name: 'Digital Labs', agents: 22, users: 654, status: 'trial', mrr: 0 },
        { id: '5', name: 'Enterprise Co', agents: 18, users: 432, status: 'active', mrr: 1800 },
    ];

    @state() private _recentActivity = [
        { icon: 'apartment', text: 'New tenant "CloudOps Ltd" created', time: '2 min ago' },
        { icon: 'smart_toy', text: 'Agent "Sales-AI" reached 1000 users', time: '15 min ago' },
        { icon: 'warning', text: 'High memory usage on cluster-us-west', time: '32 min ago' },
        { icon: 'payments', text: 'Acme Corporation upgraded to Enterprise', time: '1 hour ago' },
        { icon: 'flag', text: 'New feature flag "voice_v2" activated', time: '2 hours ago' },
    ];

    @state() private _showTenantModal = false;
    @state() private _selectedStat = '';

    @state() private _navSections: NavSection[] = [
        {
            id: 'main',
            label: 'Main',
            items: [
                { id: 'dashboard', label: 'Dashboard', icon: 'dashboard', route: '/platform' },
                { id: 'tenants', label: 'Tenants', icon: 'apartment', route: '/platform/tenants' },
                { id: 'agents', label: 'Agents', icon: 'smart_toy', route: '/platform/agents' },
            ]
        },
        {
            id: 'config',
            label: 'Configuration',
            items: [
                { id: 'models', label: 'Models', icon: 'psychology', route: '/platform/models' },
                { id: 'roles', label: 'Roles', icon: 'admin_panel_settings', route: '/platform/roles' },
                { id: 'flags', label: 'Feature Flags', icon: 'flag', route: '/platform/flags' },
                { id: 'keys', label: 'API Keys', icon: 'vpn_key', route: '/platform/api-keys' },
            ]
        },
        {
            id: 'finance',
            label: 'Finance',
            items: [
                { id: 'billing', label: 'Billing', icon: 'payments', route: '/platform/billing' },
                { id: 'subscriptions', label: 'Subscriptions', icon: 'receipt_long', route: '/platform/subscriptions' },
            ]
        },
        {
            id: 'system',
            label: 'System',
            items: [
                { id: 'audit', label: 'Audit Log', icon: 'history', route: '/platform/audit' },
                { id: 'settings', label: 'Settings', icon: 'settings', route: '/platform/settings' },
            ]
        }
    ];

    private _tenantColumns: TableColumn[] = [
        { key: 'name', label: 'Tenant', sortable: true },
        { key: 'agents', label: 'Agents', sortable: true, width: '80px', align: 'center' },
        { key: 'users', label: 'Users', sortable: true, width: '80px', align: 'center' },
        {
            key: 'status',
            label: 'Status',
            width: '100px',
            render: (val) => html`
                <saas-status-badge 
                    variant=${val === 'active' ? 'success' : val === 'trial' ? 'info' : 'warning'}
                    size="sm"
                >${val}</saas-status-badge>
            `
        },
        {
            key: 'mrr',
            label: 'MRR',
            sortable: true,
            width: '100px',
            align: 'right',
            render: (val) => val ? `$${(val as number).toLocaleString()}` : '—'
        },
    ];

    render() {
        return html`
            <div class="layout">
                <saas-sidebar
                    .sections=${this._navSections}
                    activeRoute="/platform"
                    userName="System Admin"
                    userRole="SAAS Administrator"
                    logoText="SomaAgent"
                    @saas-navigate=${this._handleNavigate}
                ></saas-sidebar>

                <main class="main">
                    <header class="header">
                        <h1 class="header-title">Platform Dashboard</h1>
                        <div class="header-actions">
                            <input type="text" class="search-input" placeholder="Search tenants, agents...">
                            <button class="btn-primary">
                                <span>+</span> New Tenant
                            </button>
                        </div>
                    </header>

                    <div class="content">
                        <!-- Stats Grid -->
                        <div class="stats-grid">
                            <saas-stat-card
                                title="Total Tenants"
                                value="${this._metrics.totalTenants}"
                                status="success"
                                trend="up"
                                trend-value="+${this._metrics.tenantsTrend}%"
                                show-stripe
                                @saas-card-click=${() => this._openStatModal('tenants')}
                            ></saas-stat-card>

                            <saas-stat-card
                                title="Active Agents"
                                value="${this._metrics.totalAgents}"
                                status="success"
                                trend="up"
                                trend-value="+${this._metrics.agentsTrend}%"
                                show-stripe
                                @saas-card-click=${() => this._openStatModal('agents')}
                            ></saas-stat-card>

                            <saas-stat-card
                                title="Monthly Revenue"
                                value="$${this._metrics.mrr.toLocaleString()}"
                                status="success"
                                trend="up"
                                trend-value="+${this._metrics.mrrTrend}%"
                                show-stripe
                                @saas-card-click=${() => this._openStatModal('revenue')}
                            ></saas-stat-card>

                            <saas-stat-card
                                title="Platform Uptime"
                                value="${this._metrics.uptime}%"
                                unit=""
                                status=${this._metrics.activeAlerts > 0 ? 'warning' : 'success'}
                                subtitle="${this._metrics.activeAlerts} active alerts"
                                show-stripe
                                @saas-card-click=${() => this._openStatModal('health')}
                            ></saas-stat-card>
                        </div>

                        <!-- Two Column Layout -->
                        <div class="two-cols">
                            <!-- Top Tenants Table -->
                            <div class="section">
                                <div class="section-header">
                                    <h2 class="section-title">Top Tenants</h2>
                                    <div class="section-actions">
                                        <button class="btn-secondary">Export</button>
                                        <button class="btn-secondary">View All</button>
                                    </div>
                                </div>
                                <saas-data-table
                                    .columns=${this._tenantColumns}
                                    .data=${this._topTenants}
                                    clickable
                                    @saas-row-click=${this._handleTenantClick}
                                ></saas-data-table>
                            </div>

                            <!-- Recent Activity -->
                            <div class="card">
                                <h3 class="card-title">Recent Activity</h3>
                                <div class="activity-list">
                                    ${this._recentActivity.map(item => html`
                                        <div class="activity-item">
                                            <div class="activity-icon">${item.icon}</div>
                                            <div class="activity-content">
                                                <div class="activity-text">${item.text}</div>
                                                <div class="activity-time">${item.time}</div>
                                            </div>
                                        </div>
                                    `)}
                                </div>
                            </div>
                        </div>
                    </div>
                </main>
            </div>

            <!-- Detail Modal -->
            <saas-glass-modal
                ?open=${this._showTenantModal}
                title="Stat Details: ${this._selectedStat}"
                size="lg"
                @saas-modal-close=${() => this._showTenantModal = false}
            >
                <p>Detailed information for ${this._selectedStat} would appear here.</p>
                <p>This modal uses glassmorphism effect with backdrop blur.</p>
            </saas-glass-modal>
        `;
    }

    private _handleNavigate(e: CustomEvent) {
        console.log('Navigate to:', e.detail.route);
        // Router integration would go here
    }

    private _openStatModal(stat: string) {
        this._selectedStat = stat;
        this._showTenantModal = true;
    }

    private _handleTenantClick(e: CustomEvent) {
        console.log('Tenant clicked:', e.detail.row);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-platform-dashboard': SaasPlatformDashboard;
    }
}
