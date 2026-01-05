/**
 * User Detail View (Tenant Admin)
 * Detailed user management with role assignment and agent access.
 *
 * Route: /admin/users/:id
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Django Ninja API integration
 * - Permission-gated actions
 *
 * PERSONAS APPLIED:
 * - 🔒 Security Auditor: Role assignment, suspension
 * - 🎨 UX Consultant: Tab navigation, clear actions
 * - 📊 Analyst: Activity history
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

import '../components/saas-user-profile-card.js';
import '../components/saas-permission-guard.js';
import '../components/saas-tabs.js';

interface UserDetail {
    id: string;
    email: string;
    displayName: string;
    avatarUrl?: string;
    role: string;
    roleLabel: string;
    status: 'active' | 'pending' | 'suspended' | 'archived';
    lastSeen?: string;
    mfaEnabled: boolean;
    createdAt: string;
    permissions: string[];
    agentAccess: AgentAccess[];
    activityLog: ActivityEntry[];
    sessions: SessionInfo[];
}

interface AgentAccess {
    agentId: string;
    agentName: string;
    modes: string[];
    isOwner: boolean;
}

interface ActivityEntry {
    id: string;
    action: string;
    target: string;
    timestamp: string;
    ip?: string;
}

interface SessionInfo {
    id: string;
    device: string;
    location: string;
    lastActive: string;
    current: boolean;
}

@customElement('saas-user-detail')
export class SaasUserDetail extends LitElement {
    static styles = css`
    :host {
      display: block;
      min-height: 100vh;
      background: var(--saas-bg-page, #f5f5f5);
      padding: var(--saas-space-lg, 24px);
    }

    .page-container {
      max-width: 1200px;
      margin: 0 auto;
    }

    .back-link {
      display: inline-flex;
      align-items: center;
      gap: var(--saas-space-xs, 4px);
      color: var(--saas-text-secondary, #666666);
      font-size: var(--saas-text-sm, 13px);
      text-decoration: none;
      margin-bottom: var(--saas-space-md, 16px);
      cursor: pointer;
    }

    .back-link:hover {
      color: var(--saas-text-primary, #1a1a1a);
    }

    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: var(--saas-space-lg, 24px);
    }

    .header-actions {
      display: flex;
      gap: var(--saas-space-sm, 8px);
    }

    .btn {
      padding: 8px 16px;
      border-radius: var(--saas-radius-md, 8px);
      font-size: var(--saas-text-sm, 13px);
      font-weight: 500;
      cursor: pointer;
      border: 1px solid var(--saas-border, #e0e0e0);
      background: var(--saas-bg-card, #ffffff);
      color: var(--saas-text-primary, #1a1a1a);
      transition: all 0.15s ease;
    }

    .btn:hover {
      background: var(--saas-bg-hover, #fafafa);
    }

    .btn-primary {
      background: var(--saas-accent, #2563eb);
      color: white;
      border: none;
    }

    .btn-primary:hover {
      background: #1d4ed8;
    }

    .btn-danger {
      color: #dc2626;
      border-color: #dc2626;
    }

    .btn-danger:hover {
      background: #dc2626;
      color: white;
    }

    .content-section {
      background: var(--saas-bg-card, #ffffff);
      border: 1px solid var(--saas-border, #e0e0e0);
      border-radius: var(--saas-radius-lg, 12px);
      margin-bottom: var(--saas-space-lg, 24px);
    }

    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: var(--saas-space-md, 16px) var(--saas-space-lg, 24px);
      border-bottom: 1px solid var(--saas-border, #e0e0e0);
    }

    .section-title {
      font-size: var(--saas-text-md, 16px);
      font-weight: 600;
      color: var(--saas-text-primary, #1a1a1a);
    }

    .section-content {
      padding: var(--saas-space-lg, 24px);
    }

    /* Tabs */
    .tabs {
      display: flex;
      border-bottom: 1px solid var(--saas-border, #e0e0e0);
      padding: 0 var(--saas-space-lg, 24px);
    }

    .tab {
      padding: var(--saas-space-md, 16px) var(--saas-space-lg, 24px);
      font-size: var(--saas-text-sm, 13px);
      font-weight: 500;
      color: var(--saas-text-secondary, #666666);
      background: none;
      border: none;
      border-bottom: 2px solid transparent;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .tab:hover {
      color: var(--saas-text-primary, #1a1a1a);
    }

    .tab.active {
      color: var(--saas-accent, #2563eb);
      border-bottom-color: var(--saas-accent, #2563eb);
    }

    /* Role & Permissions */
    .role-selector {
      display: flex;
      flex-direction: column;
      gap: var(--saas-space-md, 16px);
    }

    .role-select {
      padding: 10px 12px;
      background: var(--saas-bg-input, #ffffff);
      border: 1px solid var(--saas-border, #e0e0e0);
      border-radius: var(--saas-radius-md, 8px);
      font-size: var(--saas-text-base, 14px);
      max-width: 300px;
    }

    .permissions-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: var(--saas-space-md, 16px);
      margin-top: var(--saas-space-md, 16px);
    }

    .permission-group {
      background: var(--saas-bg-surface, #fafafa);
      padding: var(--saas-space-md, 16px);
      border-radius: var(--saas-radius-md, 8px);
    }

    .permission-group-title {
      font-size: var(--saas-text-sm, 13px);
      font-weight: 600;
      color: var(--saas-text-primary, #1a1a1a);
      margin-bottom: var(--saas-space-sm, 8px);
    }

    .permission-item {
      display: flex;
      align-items: center;
      gap: var(--saas-space-sm, 8px);
      font-size: var(--saas-text-sm, 13px);
      color: var(--saas-text-secondary, #666666);
      padding: 4px 0;
    }

    .permission-check {
      color: #22c55e;
    }

    .permission-cross {
      color: #dc2626;
    }

    /* Agent Access Table */
    .agent-table {
      width: 100%;
      border-collapse: collapse;
    }

    .agent-table th,
    .agent-table td {
      padding: var(--saas-space-sm, 8px) var(--saas-space-md, 16px);
      text-align: left;
      border-bottom: 1px solid var(--saas-border, #e0e0e0);
    }

    .agent-table th {
      font-size: var(--saas-text-xs, 11px);
      font-weight: 600;
      text-transform: uppercase;
      color: var(--saas-text-muted, #999999);
    }

    .agent-table td {
      font-size: var(--saas-text-sm, 13px);
      color: var(--saas-text-primary, #1a1a1a);
    }

    .mode-badge {
      display: inline-block;
      padding: 2px 6px;
      background: var(--saas-bg-surface, #fafafa);
      border: 1px solid var(--saas-border, #e0e0e0);
      border-radius: var(--saas-radius-sm, 4px);
      font-size: var(--saas-text-xs, 11px);
      margin-right: 4px;
    }

    .owner-badge {
      padding: 2px 6px;
      background: #fef3c7;
      color: #92400e;
      border-radius: var(--saas-radius-sm, 4px);
      font-size: var(--saas-text-xs, 11px);
      font-weight: 500;
    }

    /* Activity Log */
    .activity-list {
      display: flex;
      flex-direction: column;
    }

    .activity-item {
      display: flex;
      gap: var(--saas-space-md, 16px);
      padding: var(--saas-space-md, 16px) 0;
      border-bottom: 1px solid var(--saas-border, #e0e0e0);
    }

    .activity-item:last-child {
      border-bottom: none;
    }

    .activity-time {
      font-size: var(--saas-text-xs, 11px);
      color: var(--saas-text-muted, #999999);
      min-width: 140px;
    }

    .activity-content {
      flex: 1;
    }

    .activity-action {
      font-size: var(--saas-text-sm, 13px);
      color: var(--saas-text-primary, #1a1a1a);
    }

    .activity-target {
      font-size: var(--saas-text-xs, 11px);
      color: var(--saas-text-secondary, #666666);
    }

    /* Account Actions */
    .action-buttons {
      display: flex;
      flex-wrap: wrap;
      gap: var(--saas-space-sm, 8px);
    }

    .loading {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: var(--saas-space-2xl, 48px);
      color: var(--saas-text-muted, #999999);
    }
  `;

    @property({ type: String }) userId = '';

    @state() private user: UserDetail | null = null;
    @state() private loading = true;
    @state() private activeTab = 'profile';

    connectedCallback() {
        super.connectedCallback();
        // Get userId from URL
        const path = window.location.pathname;
        const match = path.match(/\/admin\/users\/([^/]+)/);
        if (match) {
            this.userId = match[1];
        }
        this._loadUser();
    }

    private async _loadUser() {
        this.loading = true;
        try {
            const token = localStorage.getItem('auth_token');
            const res = await fetch(`/api/v2/admin/users/${this.userId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.ok) {
                const data = await res.json();
                this.user = data;
            }
        } catch (e) {
            console.error('Failed to load user:', e);
        } finally {
            this.loading = false;
        }
    }

    private _goBack() {
        window.history.back();
    }

    private async _changeRole(newRole: string) {
        if (!this.user) return;
        try {
            const token = localStorage.getItem('auth_token');
            await fetch(`/api/v2/admin/users/${this.userId}/role`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ role: newRole }),
            });
            this._loadUser();
        } catch (e) {
            console.error('Failed to change role:', e);
        }
    }

    private async _suspendUser() {
        if (!confirm('Are you sure you want to suspend this user?')) return;
        try {
            const token = localStorage.getItem('auth_token');
            await fetch(`/api/v2/admin/users/${this.userId}/suspend`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
            });
            this._loadUser();
        } catch (e) {
            console.error('Failed to suspend user:', e);
        }
    }

    render() {
        if (this.loading) {
            return html`<div class="loading">Loading user...</div>`;
        }

        if (!this.user) {
            return html`<div class="loading">User not found</div>`;
        }

        return html`
      <div class="page-container">
        <a class="back-link" @click=${this._goBack}>← Back to Users</a>

        <div class="page-header">
          <saas-user-profile-card
            .user=${{
                id: this.user.id,
                email: this.user.email,
                displayName: this.user.displayName,
                avatarUrl: this.user.avatarUrl,
                role: this.user.role,
                roleLabel: this.user.roleLabel,
                status: this.user.status,
                lastSeen: this.user.lastSeen,
                mfaEnabled: this.user.mfaEnabled,
            }}
          ></saas-user-profile-card>
        </div>

        <!-- Tabs -->
        <div class="content-section">
          <div class="tabs">
            <button 
              class="tab ${this.activeTab === 'profile' ? 'active' : ''}"
              @click=${() => this.activeTab = 'profile'}
            >Profile</button>
            <button 
              class="tab ${this.activeTab === 'agents' ? 'active' : ''}"
              @click=${() => this.activeTab = 'agents'}
            >Agent Access</button>
            <button 
              class="tab ${this.activeTab === 'activity' ? 'active' : ''}"
              @click=${() => this.activeTab = 'activity'}
            >Activity</button>
            <button 
              class="tab ${this.activeTab === 'sessions' ? 'active' : ''}"
              @click=${() => this.activeTab = 'sessions'}
            >Sessions</button>
          </div>

          <div class="section-content">
            ${this.activeTab === 'profile' ? this._renderProfileTab() : ''}
            ${this.activeTab === 'agents' ? this._renderAgentsTab() : ''}
            ${this.activeTab === 'activity' ? this._renderActivityTab() : ''}
            ${this.activeTab === 'sessions' ? this._renderSessionsTab() : ''}
          </div>
        </div>

        <!-- Account Actions -->
        <saas-permission-guard permission="user:update" fallback="hide">
          <div class="content-section">
            <div class="section-header">
              <span class="section-title">Account Actions</span>
            </div>
            <div class="section-content">
              <div class="action-buttons">
                <button class="btn">Reset Password</button>
                <button class="btn">Revoke MFA</button>
                <button class="btn btn-danger" @click=${this._suspendUser}>
                  ${this.user.status === 'suspended' ? 'Unsuspend User' : '⚠️ Suspend User'}
                </button>
                <saas-permission-guard permission="user:delete" fallback="hide">
                  <button class="btn btn-danger">🗑️ Delete User</button>
                </saas-permission-guard>
              </div>
            </div>
          </div>
        </saas-permission-guard>
      </div>
    `;
    }

    private _renderProfileTab() {
        if (!this.user) return nothing;

        const permissionGroups = [
            { name: 'Agent', permissions: ['agent:read', 'agent:update', 'agent:create', 'agent:delete'] },
            { name: 'Conversation', permissions: ['conversation:read', 'conversation:send_message', 'conversation:delete'] },
            { name: 'Memory', permissions: ['memory:read', 'memory:search', 'memory:delete'] },
        ];

        return html`
      <div class="role-selector">
        <label style="font-weight: 600;">Role</label>
        <select 
          class="role-select"
          .value=${this.user.role}
          @change=${(e: Event) => this._changeRole((e.target as HTMLSelectElement).value)}
        >
          <option value="sysadmin">SysAdmin</option>
          <option value="admin">Admin</option>
          <option value="developer">Developer</option>
          <option value="trainer">Trainer</option>
          <option value="user">User</option>
          <option value="viewer">Viewer</option>
        </select>

        <div style="margin-top: 16px;">
          <label style="font-weight: 600;">Inherited Permissions (from ${this.user.roleLabel})</label>
          <div class="permissions-grid">
            ${permissionGroups.map(group => html`
              <div class="permission-group">
                <div class="permission-group-title">${group.name}</div>
                ${group.permissions.map(p => html`
                  <div class="permission-item">
                    <span class="${this.user!.permissions.includes(p) ? 'permission-check' : 'permission-cross'}">
                      ${this.user!.permissions.includes(p) ? '✓' : '✗'}
                    </span>
                    ${p}
                  </div>
                `)}
              </div>
            `)}
          </div>
        </div>
      </div>
    `;
    }

    private _renderAgentsTab() {
        if (!this.user || !this.user.agentAccess) return nothing;

        return html`
      <div class="section-header" style="border: none; padding: 0 0 16px 0;">
        <span class="section-title">Agent Access</span>
        <button class="btn btn-primary">+ Add Agent</button>
      </div>
      <table class="agent-table">
        <thead>
          <tr>
            <th>Agent</th>
            <th>Modes</th>
            <th>Owner</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${this.user.agentAccess.map(agent => html`
            <tr>
              <td>${agent.agentName}</td>
              <td>
                ${agent.modes.map(m => html`<span class="mode-badge">${m}</span>`)}
              </td>
              <td>${agent.isOwner ? html`<span class="owner-badge">Owner</span>` : 'No'}</td>
              <td>
                <button class="btn" style="padding: 4px 8px;">Edit</button>
                <button class="btn" style="padding: 4px 8px;">Remove</button>
              </td>
            </tr>
          `)}
        </tbody>
      </table>
    `;
    }

    private _renderActivityTab() {
        if (!this.user || !this.user.activityLog) return nothing;

        return html`
      <div class="activity-list">
        ${this.user.activityLog.length === 0
                ? html`<div style="color: var(--saas-text-muted); padding: 24px 0;">No activity recorded</div>`
                : this.user.activityLog.map(entry => html`
            <div class="activity-item">
              <div class="activity-time">${new Date(entry.timestamp).toLocaleString()}</div>
              <div class="activity-content">
                <div class="activity-action">${entry.action}</div>
                <div class="activity-target">${entry.target}</div>
              </div>
            </div>
          `)
            }
      </div>
    `;
    }

    private _renderSessionsTab() {
        if (!this.user || !this.user.sessions) return nothing;

        return html`
      <table class="agent-table">
        <thead>
          <tr>
            <th>Device</th>
            <th>Location</th>
            <th>Last Active</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${this.user.sessions.map(session => html`
            <tr>
              <td>
                ${session.device}
                ${session.current ? html`<span class="mode-badge" style="background: #dcfce7; color: #166534;">Current</span>` : ''}
              </td>
              <td>${session.location}</td>
              <td>${new Date(session.lastActive).toLocaleString()}</td>
              <td>
                ${!session.current ? html`<button class="btn btn-danger" style="padding: 4px 8px;">Revoke</button>` : ''}
              </td>
            </tr>
          `)}
        </tbody>
      </table>
    `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-user-detail': SaasUserDetail;
    }
}
