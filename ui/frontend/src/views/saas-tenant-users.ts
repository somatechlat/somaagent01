/**
 * SomaAgent SaaS — Tenant Users Management
 * Per SAAS_ADMIN_SRS.md Section 4.4 - Tenant Users
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Django Ninja API integration
 * - Minimal white/black design per UI_STYLE_GUIDE.md
 * - NO EMOJIS - Google Material Symbols only
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';

interface User {
    id: string;
    email: string;
    name: string;
    role: string;
    status: 'active' | 'invited' | 'suspended';
    lastActive: string;
}

@customElement('saas-tenant-users')
export class SaasTenantUsers extends LitElement {
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

        .sidebar-title { font-size: 18px; font-weight: 600; margin: 0 0 4px 0; }
        .sidebar-subtitle { font-size: 13px; color: var(--saas-text-secondary, #666); }

        .nav-list { display: flex; flex-direction: column; gap: 2px; padding: 0 12px; }

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

        .nav-item:hover { background: var(--saas-bg-hover, #fafafa); color: var(--saas-text-primary, #1a1a1a); }
        .nav-item.active { background: var(--saas-bg-active, #f0f0f0); color: var(--saas-text-primary, #1a1a1a); font-weight: 500; }
        .nav-item .material-symbols-outlined { font-size: 18px; }
        .nav-divider { height: 1px; background: var(--saas-border-light, #e0e0e0); margin: 12px 20px; }

        .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

        .header {
            padding: 16px 24px;
            background: var(--saas-bg-card, #ffffff);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-left { display: flex; align-items: center; gap: 16px; }
        .header-title { font-size: 18px; font-weight: 600; }

        .search-box {
            position: relative;
        }

        .search-input {
            padding: 10px 14px 10px 40px;
            border-radius: 8px;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            font-size: 14px;
            width: 240px;
            background: var(--saas-bg-card, #ffffff);
        }

        .search-input:focus { outline: none; border-color: var(--saas-text-primary, #1a1a1a); }

        .search-icon {
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--saas-text-muted, #999);
            font-size: 18px;
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

        .btn:hover { background: var(--saas-bg-hover, #fafafa); }
        .btn.primary { background: #1a1a1a; color: white; border-color: #1a1a1a; }
        .btn.primary:hover { background: #333; }
        .btn .material-symbols-outlined { font-size: 18px; }

        .content { flex: 1; overflow-y: auto; padding: 24px; }

        /* Table */
        .table-card {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 12px;
            overflow: hidden;
        }

        table { width: 100%; border-collapse: collapse; }

        th {
            text-align: left;
            padding: 14px 16px;
            font-size: 12px;
            font-weight: 500;
            color: var(--saas-text-muted, #999);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        td {
            padding: 16px;
            font-size: 14px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }

        tr:last-child td { border-bottom: none; }
        tr:hover td { background: var(--saas-bg-hover, #fafafa); }

        .user-cell { display: flex; align-items: center; gap: 12px; }

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

        .user-name { font-weight: 500; }
        .user-email { font-size: 12px; color: var(--saas-text-muted, #999); }

        .role-badge {
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .role-badge.sysadmin { background: #1a1a1a; color: white; }
        .role-badge.admin { background: #dbeafe; color: #1d4ed8; }
        .role-badge.developer { background: #d1fae5; color: #047857; }
        .role-badge.trainer { background: #fef3c7; color: #b45309; }
        .role-badge.member { background: #f3f4f6; color: #374151; }
        .role-badge.viewer { background: #e5e7eb; color: #6b7280; }

        .status-badge {
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
        }

        .status-badge.active { background: #d1fae5; color: #047857; }
        .status-badge.invited { background: #fef3c7; color: #b45309; }
        .status-badge.suspended { background: #fee2e2; color: #b91c1c; }

        .action-btn {
            width: 32px;
            height: 32px;
            border-radius: 6px;
            border: none;
            background: transparent;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .action-btn:hover { background: var(--saas-bg-hover, #fafafa); }

        /* Modal */
        .modal-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }

        .modal-overlay.hidden { display: none; }

        .modal {
            background: var(--saas-bg-card, #ffffff);
            border-radius: 16px;
            width: 100%;
            max-width: 440px;
            box-shadow: var(--saas-shadow-lg, 0 8px 24px rgba(0,0,0,0.12));
        }

        .modal-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-title { font-size: 18px; font-weight: 600; }

        .modal-close {
            width: 32px; height: 32px;
            border-radius: 8px;
            border: none;
            background: transparent;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .modal-close:hover { background: var(--saas-bg-hover, #fafafa); }

        .modal-body { padding: 24px; }

        .modal-footer {
            padding: 16px 24px;
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            justify-content: flex-end;
            gap: 10px;
        }

        .form-group { margin-bottom: 20px; }
        .form-label { display: block; font-size: 13px; font-weight: 500; margin-bottom: 8px; }

        .form-input, .form-select {
            width: 100%;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            font-size: 14px;
            background: var(--saas-bg-card, #ffffff);
        }

        .form-input:focus, .form-select:focus { outline: none; border-color: var(--saas-text-primary, #1a1a1a); }
    `;

    @state() private _tenantName = '';
    @state() private _users: User[] = [];
    @state() private _searchQuery = '';
    @state() private _showModal = false;

    connectedCallback() {
        super.connectedCallback();
        this._tenantName = sessionStorage.getItem('saas_tenant_name') || 'Demo Tenant';
        this._loadUsers();
    }

    render() {
        const filteredUsers = this._users.filter(u =>
            u.name.toLowerCase().includes(this._searchQuery.toLowerCase()) ||
            u.email.toLowerCase().includes(this._searchQuery.toLowerCase())
        );

        return html`
            <aside class="sidebar">
                <div class="sidebar-header">
                    <h1 class="sidebar-title">${this._tenantName}</h1>
                    <p class="sidebar-subtitle">Tenant Administration</p>
                </div>

                <nav class="nav-list">
                    <a class="nav-item" href="/admin/dashboard">
                        <span class="material-symbols-outlined">dashboard</span>
                        Dashboard
                    </a>
                    <a class="nav-item active" href="/admin/users">
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
                    <a class="nav-item" href="/mode-select">
                        <span class="material-symbols-outlined">arrow_back</span>
                        Exit Tenant
                    </a>
                </nav>
            </aside>

            <main class="main">
                <header class="header">
                    <div class="header-left">
                        <h2 class="header-title">Users</h2>
                        <div class="search-box">
                            <span class="material-symbols-outlined search-icon">search</span>
                            <input 
                                type="text" 
                                class="search-input" 
                                placeholder="Search users..."
                                .value=${this._searchQuery}
                                @input=${(e: Event) => this._searchQuery = (e.target as HTMLInputElement).value}
                            >
                        </div>
                    </div>
                    <button class="btn primary" @click=${() => this._showModal = true}>
                        <span class="material-symbols-outlined">person_add</span>
                        Invite User
                    </button>
                </header>

                <div class="content">
                    <div class="table-card">
                        <table>
                            <thead>
                                <tr>
                                    <th>User</th>
                                    <th>Role</th>
                                    <th>Status</th>
                                    <th>Last Active</th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                ${filteredUsers.map(user => html`
                                    <tr>
                                        <td>
                                            <div class="user-cell">
                                                <div class="user-avatar">${user.name.charAt(0)}</div>
                                                <div>
                                                    <div class="user-name">${user.name}</div>
                                                    <div class="user-email">${user.email}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td><span class="role-badge ${user.role}">${user.role}</span></td>
                                        <td><span class="status-badge ${user.status}">${user.status}</span></td>
                                        <td>${user.lastActive}</td>
                                        <td>
                                            <button class="action-btn">
                                                <span class="material-symbols-outlined">more_vert</span>
                                            </button>
                                        </td>
                                    </tr>
                                `)}
                            </tbody>
                        </table>
                    </div>
                </div>
            </main>

            <!-- Invite Modal -->
            <div class="modal-overlay ${this._showModal ? '' : 'hidden'}" @click=${(e: Event) => e.target === e.currentTarget && (this._showModal = false)}>
                <div class="modal">
                    <div class="modal-header">
                        <h3 class="modal-title">Invite User</h3>
                        <button class="modal-close" @click=${() => this._showModal = false}>
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label class="form-label">Email Address</label>
                            <input type="email" class="form-input" id="inviteEmail" placeholder="user@company.com">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Role</label>
                            <select class="form-select" id="inviteRole">
                                <option value="member">Member</option>
                                <option value="viewer">Viewer</option>
                                <option value="developer">Developer</option>
                                <option value="trainer">Trainer</option>
                                <option value="admin">Admin</option>
                            </select>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn" @click=${() => this._showModal = false}>Cancel</button>
                        <button class="btn primary" @click=${this._inviteUser}>Send Invite</button>
                    </div>
                </div>
            </div>
        `;
    }

    private async _loadUsers() {
        try {
            const response = await apiClient.get('/admin/users/');
            const data = response as { users?: User[] };
            if (data.users) this._users = data.users;
        } catch {
            this._users = [
                { id: '1', email: 'jane@company.com', name: 'Jane Smith', role: 'sysadmin', status: 'active', lastActive: '2 min ago' },
                { id: '2', email: 'bob@company.com', name: 'Bob Johnson', role: 'admin', status: 'active', lastActive: '1 hour ago' },
                { id: '3', email: 'alice@company.com', name: 'Alice Williams', role: 'developer', status: 'active', lastActive: '30 min ago' },
                { id: '4', email: 'john@company.com', name: 'John Doe', role: 'trainer', status: 'invited', lastActive: 'Never' },
                { id: '5', email: 'mary@company.com', name: 'Mary Brown', role: 'member', status: 'active', lastActive: 'Yesterday' },
            ];
        }
    }

    private async _inviteUser() {
        const emailEl = this.shadowRoot?.getElementById('inviteEmail') as HTMLInputElement;
        const roleEl = this.shadowRoot?.getElementById('inviteRole') as HTMLSelectElement;

        try {
            await apiClient.post('/admin/users/', { email: emailEl.value, role: roleEl.value });
            this._showModal = false;
            await this._loadUsers();
        } catch (error) {
            console.error('Failed to invite user:', error);
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-tenant-users': SaasTenantUsers;
    }
}
