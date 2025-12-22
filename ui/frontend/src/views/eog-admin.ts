/**
 * Eye of God Admin View
 * Per Eye of God UIX Design Section 2.2
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - System metrics dashboard
 * - User/tenant management
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import '../components/eog-card.js';
import '../components/eog-tabs.js';

interface SystemMetrics {
    uptime_seconds: number;
    active_users: number;
    total_requests: number;
    avg_latency_ms: number;
    error_rate: number;
    memory_usage_mb: number;
    cpu_usage_percent: number;
    database_connections: number;
    cache_hit_rate: number;
}

interface UserAdmin {
    id: string;
    username: string;
    email?: string;
    role: string;
    is_active: boolean;
    last_login?: string;
}

interface AuditLogEntry {
    id: string;
    username: string;
    action: string;
    resource_type: string;
    created_at: string;
}

interface FeatureFlag {
    key: string;
    name: string;
    enabled: boolean;
    rollout_percent: number;
}

@customElement('eog-admin')
export class EogAdmin extends LitElement {
    static styles = css`
        :host {
            display: block;
            padding: var(--eog-spacing-lg, 24px);
            height: 100%;
            overflow-y: auto;
        }

        .admin-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--eog-spacing-xl, 32px);
        }

        h1 {
            font-size: var(--eog-text-2xl, 24px);
            font-weight: 600;
            color: var(--eog-text-main, #e2e8f0);
            margin: 0;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: var(--eog-spacing-md, 16px);
            margin-bottom: var(--eog-spacing-xl, 32px);
        }

        .metric-card {
            text-align: center;
            padding: var(--eog-spacing-lg, 24px);
        }

        .metric-value {
            font-size: var(--eog-text-3xl, 30px);
            font-weight: 700;
            color: var(--eog-accent, #94a3b8);
            margin-bottom: var(--eog-spacing-xs, 4px);
        }

        .metric-label {
            font-size: var(--eog-text-sm, 13px);
            color: var(--eog-text-dim, #64748b);
        }

        .metric-trend {
            font-size: var(--eog-text-xs, 11px);
            margin-top: var(--eog-spacing-xs, 4px);
        }

        .trend-up { color: var(--eog-success, #22c55e); }
        .trend-down { color: var(--eog-danger, #ef4444); }

        .section {
            margin-bottom: var(--eog-spacing-xl, 32px);
        }

        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--eog-spacing-md, 16px);
        }

        h2 {
            font-size: var(--eog-text-lg, 16px);
            font-weight: 600;
            color: var(--eog-text-main, #e2e8f0);
            margin: 0;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            padding: var(--eog-spacing-sm, 8px) var(--eog-spacing-md, 16px);
            text-align: left;
            border-bottom: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.1));
        }

        th {
            font-size: var(--eog-text-xs, 11px);
            font-weight: 600;
            color: var(--eog-text-dim, #64748b);
            text-transform: uppercase;
        }

        td {
            font-size: var(--eog-text-sm, 13px);
            color: var(--eog-text-main, #e2e8f0);
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 2px 8px;
            border-radius: var(--eog-radius-full, 9999px);
            font-size: var(--eog-text-xs, 11px);
            font-weight: 600;
        }

        .status-active {
            background: rgba(34, 197, 94, 0.2);
            color: var(--eog-success, #22c55e);
        }

        .status-inactive {
            background: rgba(239, 68, 68, 0.2);
            color: var(--eog-danger, #ef4444);
        }

        .role-badge {
            padding: 2px 8px;
            border-radius: var(--eog-radius-sm, 4px);
            font-size: var(--eog-text-xs, 11px);
            background: rgba(148, 163, 184, 0.2);
            color: var(--eog-accent, #94a3b8);
        }

        .role-admin { 
            background: rgba(245, 158, 11, 0.2); 
            color: var(--eog-warning, #f59e0b); 
        }

        .role-sysadmin { 
            background: rgba(239, 68, 68, 0.2); 
            color: var(--eog-danger, #ef4444); 
        }

        .flag-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: var(--eog-spacing-md, 16px);
            border-bottom: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.1));
        }

        .flag-info {
            flex: 1;
        }

        .flag-name {
            font-weight: 600;
            color: var(--eog-text-main, #e2e8f0);
        }

        .flag-key {
            font-size: var(--eog-text-xs, 11px);
            color: var(--eog-text-dim, #64748b);
            font-family: monospace;
        }

        .flag-rollout {
            font-size: var(--eog-text-sm, 13px);
            color: var(--eog-accent, #94a3b8);
            margin-right: var(--eog-spacing-md, 16px);
        }

        .action-btn {
            padding: var(--eog-spacing-xs, 4px) var(--eog-spacing-sm, 8px);
            border-radius: var(--eog-radius-sm, 4px);
            border: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.1));
            background: transparent;
            color: var(--eog-text-main, #e2e8f0);
            font-size: var(--eog-text-xs, 11px);
            cursor: pointer;
        }

        .action-btn:hover {
            background: rgba(148, 163, 184, 0.1);
        }
    `;

    @state() private _metrics: SystemMetrics | null = null;
    @state() private _users: UserAdmin[] = [];
    @state() private _auditLogs: AuditLogEntry[] = [];
    @state() private _featureFlags: FeatureFlag[] = [];
    @state() private _isLoading = false;
    @state() private _activeTab = 'overview';

    private _tabs = [
        { id: 'overview', label: 'Overview' },
        { id: 'users', label: 'Users' },
        { id: 'audit', label: 'Audit Logs' },
        { id: 'flags', label: 'Feature Flags' },
    ];

    connectedCallback() {
        super.connectedCallback();
        this._loadMetrics();
        this._loadUsers();
        this._loadAuditLogs();
        this._loadFeatureFlags();
    }

    render() {
        return html`
            <header class="admin-header">
                <h1>🛡️ Admin Dashboard</h1>
            </header>

            <eog-tabs
                .tabs=${this._tabs}
                .selected=${this._activeTab}
                @eog-tab-change=${(e: CustomEvent) => this._activeTab = e.detail.id}
            >
                <div slot="overview">
                    ${this._renderOverview()}
                </div>
                <div slot="users">
                    ${this._renderUsers()}
                </div>
                <div slot="audit">
                    ${this._renderAuditLogs()}
                </div>
                <div slot="flags">
                    ${this._renderFeatureFlags()}
                </div>
            </eog-tabs>
        `;
    }

    private _renderOverview() {
        if (!this._metrics) return html`<p>Loading metrics...</p>`;

        return html`
            <div class="metrics-grid">
                <eog-card class="metric-card">
                    <div class="metric-value">${this._formatUptime(this._metrics.uptime_seconds)}</div>
                    <div class="metric-label">Uptime</div>
                </eog-card>
                <eog-card class="metric-card">
                    <div class="metric-value">${this._metrics.active_users}</div>
                    <div class="metric-label">Active Users</div>
                </eog-card>
                <eog-card class="metric-card">
                    <div class="metric-value">${this._formatNumber(this._metrics.total_requests)}</div>
                    <div class="metric-label">Total Requests</div>
                </eog-card>
                <eog-card class="metric-card">
                    <div class="metric-value">${this._metrics.avg_latency_ms}ms</div>
                    <div class="metric-label">Avg Latency</div>
                </eog-card>
                <eog-card class="metric-card">
                    <div class="metric-value">${(this._metrics.error_rate * 100).toFixed(2)}%</div>
                    <div class="metric-label">Error Rate</div>
                    <div class="metric-trend ${this._metrics.error_rate < 0.01 ? 'trend-up' : 'trend-down'}">
                        ${this._metrics.error_rate < 0.01 ? '✓ Healthy' : '⚠ Elevated'}
                    </div>
                </eog-card>
                <eog-card class="metric-card">
                    <div class="metric-value">${this._metrics.memory_usage_mb}MB</div>
                    <div class="metric-label">Memory Usage</div>
                </eog-card>
                <eog-card class="metric-card">
                    <div class="metric-value">${this._metrics.cpu_usage_percent}%</div>
                    <div class="metric-label">CPU Usage</div>
                </eog-card>
                <eog-card class="metric-card">
                    <div class="metric-value">${(this._metrics.cache_hit_rate * 100).toFixed(0)}%</div>
                    <div class="metric-label">Cache Hit Rate</div>
                </eog-card>
            </div>
        `;
    }

    private _renderUsers() {
        return html`
            <div class="section">
                <div class="section-header">
                    <h2>Users (${this._users.length})</h2>
                    <eog-button size="small" @click=${this._inviteUser}>+ Invite User</eog-button>
                </div>
                <eog-card>
                    <table>
                        <thead>
                            <tr>
                                <th>Username</th>
                                <th>Email</th>
                                <th>Role</th>
                                <th>Status</th>
                                <th>Last Login</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${this._users.map(user => html`
                                <tr>
                                    <td>${user.username}</td>
                                    <td>${user.email || '-'}</td>
                                    <td>
                                        <span class="role-badge ${user.role === 'admin' ? 'role-admin' : user.role === 'sysadmin' ? 'role-sysadmin' : ''}">
                                            ${user.role}
                                        </span>
                                    </td>
                                    <td>
                                        <span class="status-badge ${user.is_active ? 'status-active' : 'status-inactive'}">
                                            ${user.is_active ? '● Active' : '○ Inactive'}
                                        </span>
                                    </td>
                                    <td>${user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}</td>
                                    <td>
                                        <button class="action-btn" @click=${() => this._editUser(user)}>Edit</button>
                                    </td>
                                </tr>
                            `)}
                        </tbody>
                    </table>
                </eog-card>
            </div>
        `;
    }

    private _renderAuditLogs() {
        return html`
            <div class="section">
                <div class="section-header">
                    <h2>Recent Audit Logs</h2>
                    <eog-button size="small" variant="secondary" @click=${this._exportLogs}>Export</eog-button>
                </div>
                <eog-card>
                    <table>
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>User</th>
                                <th>Action</th>
                                <th>Resource</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${this._auditLogs.map(log => html`
                                <tr>
                                    <td>${new Date(log.created_at).toLocaleString()}</td>
                                    <td>${log.username}</td>
                                    <td>${log.action}</td>
                                    <td>${log.resource_type}</td>
                                </tr>
                            `)}
                        </tbody>
                    </table>
                </eog-card>
            </div>
        `;
    }

    private _renderFeatureFlags() {
        return html`
            <div class="section">
                <div class="section-header">
                    <h2>Feature Flags</h2>
                    <eog-button size="small" @click=${this._createFlag}>+ New Flag</eog-button>
                </div>
                <eog-card>
                    ${this._featureFlags.map(flag => html`
                        <div class="flag-row">
                            <div class="flag-info">
                                <div class="flag-name">${flag.name}</div>
                                <div class="flag-key">${flag.key}</div>
                            </div>
                            <span class="flag-rollout">${flag.rollout_percent}%</span>
                            <eog-toggle 
                                .checked=${flag.enabled}
                                @eog-change=${(e: CustomEvent) => this._toggleFlag(flag.key, e.detail.checked)}
                            ></eog-toggle>
                        </div>
                    `)}
                </eog-card>
            </div>
        `;
    }

    private _formatUptime(seconds: number): string {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        if (days > 0) return `${days}d ${hours}h`;
        const mins = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${mins}m`;
    }

    private _formatNumber(num: number): string {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
        return num.toString();
    }

    private async _loadMetrics() {
        try {
            const response = await fetch('/api/v2/admin/metrics', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('eog_auth_token')}` }
            });
            if (response.ok) this._metrics = await response.json();
        } catch (error) {
            console.error('Failed to load metrics:', error);
        }
    }

    private async _loadUsers() {
        try {
            const response = await fetch('/api/v2/admin/users', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('eog_auth_token')}` }
            });
            if (response.ok) this._users = await response.json();
        } catch (error) {
            console.error('Failed to load users:', error);
        }
    }

    private async _loadAuditLogs() {
        try {
            const response = await fetch('/api/v2/admin/audit-logs?page_size=20', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('eog_auth_token')}` }
            });
            if (response.ok) this._auditLogs = await response.json();
        } catch (error) {
            console.error('Failed to load audit logs:', error);
        }
    }

    private async _loadFeatureFlags() {
        try {
            const response = await fetch('/api/v2/admin/feature-flags', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('eog_auth_token')}` }
            });
            if (response.ok) this._featureFlags = await response.json();
        } catch (error) {
            console.error('Failed to load feature flags:', error);
        }
    }

    private _inviteUser() {
        this.dispatchEvent(new CustomEvent('eog-navigate', {
            detail: { path: '/admin/users/invite' },
            bubbles: true, composed: true,
        }));
    }

    private _editUser(user: UserAdmin) {
        this.dispatchEvent(new CustomEvent('eog-navigate', {
            detail: { path: `/admin/users/${user.id}` },
            bubbles: true, composed: true,
        }));
    }

    private _exportLogs() {
        window.open('/api/v2/admin/audit-logs/export', '_blank');
    }

    private _createFlag() {
        this.dispatchEvent(new CustomEvent('eog-navigate', {
            detail: { path: '/admin/flags/new' },
            bubbles: true, composed: true,
        }));
    }

    private async _toggleFlag(key: string, enabled: boolean) {
        try {
            await fetch(`/api/v2/admin/feature-flags/${key}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('eog_auth_token')}`
                },
                body: JSON.stringify({ enabled }),
            });
            this._loadFeatureFlags();
        } catch (error) {
            console.error('Failed to toggle flag:', error);
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-admin': EogAdmin;
    }
}
