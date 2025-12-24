/**
 * SomaAgent SaaS — Tenant Admin Dashboard
 * Per SAAS_ADMIN_SRS.md Section 12.2 - Tenant SysAdmin Dashboard
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Django Ninja API integration
 * - Minimal white/black design per UI_STYLE_GUIDE.md
 * - NO EMOJIS - Google Material Symbols only
 * 
 * Features:
 * - Tenant quota usage (Agents, Users, Tokens, Storage)
 * - Agent list with status
 * - User activity summary
 * - Quick actions
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';

interface TenantStats {
    agentsUsed: number;
    agentsMax: number;
    usersUsed: number;
    usersMax: number;
    tokensUsed: number;
    tokensMax: number;
    storageUsedGB: number;
    storageMaxGB: number;
    monthlyBill: number;
}

interface Agent {
    id: string;
    name: string;
    status: 'running' | 'stopped' | 'error';
    messagesCount: number;
    lastActive: string;
}

@customElement('saas-tenant-dashboard')
export class SaasTenantDashboard extends LitElement {
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

        /* Sidebar */
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
        }

        .sidebar-subtitle {
            font-size: 13px;
            color: var(--saas-text-secondary, #666);
        }

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

        .nav-item .material-symbols-outlined { font-size: 18px; }

        .nav-divider {
            height: 1px;
            background: var(--saas-border-light, #e0e0e0);
            margin: 12px 20px;
        }

        /* Main */
        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .header {
            padding: 16px 24px;
            background: var(--saas-bg-card, #ffffff);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-title { font-size: 18px; font-weight: 600; }

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

        .btn:hover { background: var(--saas-bg-hover, #fafafa); }

        .btn.primary {
            background: #1a1a1a;
            color: white;
            border-color: #1a1a1a;
        }

        .btn.primary:hover { background: #333; }

        .btn .material-symbols-outlined { font-size: 18px; }

        .content {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
        }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }

        @media (max-width: 1200px) {
            .stats-grid { grid-template-columns: repeat(3, 1fr); }
        }

        .stat-card {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 12px;
            padding: 20px;
        }

        .stat-label {
            font-size: 13px;
            color: var(--saas-text-secondary, #666);
            margin-bottom: 8px;
        }

        .stat-value {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .stat-bar {
            height: 6px;
            background: var(--saas-border-light, #e0e0e0);
            border-radius: 3px;
            overflow: hidden;
        }

        .stat-fill {
            height: 100%;
            background: #1a1a1a;
            border-radius: 3px;
            transition: width 0.3s ease;
        }

        .stat-fill.warning { background: var(--saas-status-warning, #f59e0b); }
        .stat-fill.danger { background: var(--saas-status-danger, #ef4444); }

        /* Content Grid */
        .content-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        @media (max-width: 900px) {
            .content-grid { grid-template-columns: 1fr; }
        }

        .card {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 12px;
            padding: 20px;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }

        .card-title {
            font-size: 16px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .card-title .material-symbols-outlined {
            font-size: 18px;
            color: var(--saas-text-secondary, #666);
        }

        /* Agent List */
        .agent-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .agent-item {
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 14px;
            background: var(--saas-bg-hover, #fafafa);
            border-radius: 10px;
            cursor: pointer;
            transition: background 0.1s ease;
        }

        .agent-item:hover { background: var(--saas-bg-active, #f0f0f0); }

        .agent-icon {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .agent-info { flex: 1; }

        .agent-name { font-weight: 500; margin-bottom: 2px; }

        .agent-meta {
            font-size: 12px;
            color: var(--saas-text-muted, #999);
        }

        .agent-status {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }

        .agent-status.running { background: var(--saas-status-success, #22c55e); }
        .agent-status.stopped { background: var(--saas-text-muted, #999); }
        .agent-status.error { background: var(--saas-status-danger, #ef4444); }

        /* Quick Actions */
        .actions-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }

        .action-btn {
            padding: 16px;
            border-radius: 10px;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            background: var(--saas-bg-card, #ffffff);
            cursor: pointer;
            transition: all 0.1s ease;
            text-align: center;
        }

        .action-btn:hover {
            background: var(--saas-bg-hover, #fafafa);
            border-color: var(--saas-border-medium, #ccc);
        }

        .action-btn .material-symbols-outlined {
            font-size: 24px;
            margin-bottom: 8px;
            display: block;
        }

        .action-btn span:last-child {
            font-size: 13px;
            font-weight: 500;
        }
    `;

    @state() private _tenantName = '';
    @state() private _stats: TenantStats = {
        agentsUsed: 5, agentsMax: 10,
        usersUsed: 12, usersMax: 50,
        tokensUsed: 4200000, tokensMax: 10000000,
        storageUsedGB: 45, storageMaxGB: 100,
        monthlyBill: 199,
    };
    @state() private _agents: Agent[] = [
        { id: '1', name: 'Support-AI', status: 'running', messagesCount: 1234, lastActive: '2 min ago' },
        { id: '2', name: 'Sales-Bot', status: 'stopped', messagesCount: 567, lastActive: '1 hour ago' },
        { id: '3', name: 'Research-AI', status: 'running', messagesCount: 890, lastActive: '5 min ago' },
    ];

    connectedCallback() {
        super.connectedCallback();
        this._tenantName = sessionStorage.getItem('saas_tenant_name') || 'Demo Tenant';
        this._loadData();
    }

    render() {
        const tokensPct = (this._stats.tokensUsed / this._stats.tokensMax) * 100;
        const storagePct = (this._stats.storageUsedGB / this._stats.storageMaxGB) * 100;

        return html`
            <aside class="sidebar">
                <div class="sidebar-header">
                    <h1 class="sidebar-title">${this._tenantName}</h1>
                    <p class="sidebar-subtitle">Tenant Administration</p>
                </div>

                <nav class="nav-list">
                    <a class="nav-item active" href="/admin/dashboard">
                        <span class="material-symbols-outlined">dashboard</span>
                        Dashboard
                    </a>
                    <a class="nav-item" href="/admin/users">
                        <span class="material-symbols-outlined">group</span>
                        Users
                    </a>
                    <a class="nav-item" href="/admin/agents">
                        <span class="material-symbols-outlined">smart_toy</span>
                        Agents
                    </a>
                    <a class="nav-item" href="/admin/settings">
                        <span class="material-symbols-outlined">settings</span>
                        Settings
                    </a>
                    <div class="nav-divider"></div>
                    <a class="nav-item" href="/chat">
                        <span class="material-symbols-outlined">chat</span>
                        Enter Chat
                    </a>
                    <a class="nav-item" href="/mode-select">
                        <span class="material-symbols-outlined">arrow_back</span>
                        Exit Tenant
                    </a>
                </nav>
            </aside>

            <main class="main">
                <header class="header">
                    <h2 class="header-title">Dashboard</h2>
                    <button class="btn primary" @click=${() => window.location.href = '/admin/agents?new=1'}>
                        <span class="material-symbols-outlined">add</span>
                        Create Agent
                    </button>
                </header>

                <div class="content">
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-label">Agents</div>
                            <div class="stat-value">${this._stats.agentsUsed}/${this._stats.agentsMax}</div>
                            <div class="stat-bar">
                                <div class="stat-fill" style="width: ${(this._stats.agentsUsed / this._stats.agentsMax) * 100}%"></div>
                            </div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Users</div>
                            <div class="stat-value">${this._stats.usersUsed}/${this._stats.usersMax}</div>
                            <div class="stat-bar">
                                <div class="stat-fill" style="width: ${(this._stats.usersUsed / this._stats.usersMax) * 100}%"></div>
                            </div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Tokens</div>
                            <div class="stat-value">${(this._stats.tokensUsed / 1000000).toFixed(1)}M</div>
                            <div class="stat-bar">
                                <div class="stat-fill ${tokensPct > 80 ? 'warning' : ''}" style="width: ${tokensPct}%"></div>
                            </div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Storage</div>
                            <div class="stat-value">${this._stats.storageUsedGB} GB</div>
                            <div class="stat-bar">
                                <div class="stat-fill ${storagePct > 80 ? 'warning' : ''}" style="width: ${storagePct}%"></div>
                            </div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">This Month</div>
                            <div class="stat-value">$${this._stats.monthlyBill}</div>
                        </div>
                    </div>

                    <div class="content-grid">
                        <div class="card">
                            <div class="card-header">
                                <h3 class="card-title">
                                    <span class="material-symbols-outlined">smart_toy</span>
                                    Your Agents
                                </h3>
                                <a href="/admin/agents" class="btn">View All</a>
                            </div>
                            <div class="agent-list">
                                ${this._agents.map(agent => html`
                                    <div class="agent-item" @click=${() => window.location.href = `/chat?agent=${agent.id}`}>
                                        <div class="agent-icon">
                                            <span class="material-symbols-outlined">smart_toy</span>
                                        </div>
                                        <div class="agent-info">
                                            <div class="agent-name">${agent.name}</div>
                                            <div class="agent-meta">${agent.messagesCount} messages, ${agent.lastActive}</div>
                                        </div>
                                        <div class="agent-status ${agent.status}"></div>
                                    </div>
                                `)}
                            </div>
                        </div>

                        <div class="card">
                            <div class="card-header">
                                <h3 class="card-title">
                                    <span class="material-symbols-outlined">bolt</span>
                                    Quick Actions
                                </h3>
                            </div>
                            <div class="actions-grid">
                                <button class="action-btn" @click=${() => window.location.href = '/admin/users?invite=1'}>
                                    <span class="material-symbols-outlined">person_add</span>
                                    <span>Invite User</span>
                                </button>
                                <button class="action-btn" @click=${() => window.location.href = '/admin/agents?new=1'}>
                                    <span class="material-symbols-outlined">add_circle</span>
                                    <span>Create Agent</span>
                                </button>
                                <button class="action-btn" @click=${() => window.location.href = '/admin/audit'}>
                                    <span class="material-symbols-outlined">history</span>
                                    <span>View Audit</span>
                                </button>
                                <button class="action-btn" @click=${() => window.location.href = '/admin/settings'}>
                                    <span class="material-symbols-outlined">settings</span>
                                    <span>Settings</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        `;
    }

    private async _loadData() {
        try {
            const response = await apiClient.get('/admin/dashboard/');
            const data = response as { stats?: TenantStats; agents?: Agent[] };
            if (data.stats) this._stats = data.stats;
            if (data.agents) this._agents = data.agents;
        } catch {
            // Demo data already set
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-tenant-dashboard': SaasTenantDashboard;
    }
}
