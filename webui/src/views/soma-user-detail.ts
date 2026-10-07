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
 * - lock Security Auditor: Role assignment, suspension
 * - palette UX Consultant: Tab navigation, clear actions
 * - bar_chart Analyst: Activity history
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';

import '../components/soma-user-profile-card.js';
import '../components/soma-permission-guard.js';

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

@customElement('soma-user-detail')
export class SomaUserDetail extends LitElement {
    static styles = css`
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
        :host {
          display: block;
          min-height: 100vh;
          background: var(--soma-bg-page, #f5f5f5);
          padding: var(--soma-space-lg, 24px);
        }

        .page-container {
          max-width: 1200px;
          margin: 0 auto;
        }

        .back-link {
          display: inline-flex;
          align-items: center;
          gap: var(--soma-space-xs, 4px);
          color: var(--soma-text-secondary, #666666);
          font-size: var(--soma-text-sm, 13px);
          text-decoration: none;
          margin-bottom: var(--soma-space-md, 16px);
          cursor: pointer;
        }

        .back-link:hover {
          color: var(--soma-text-primary, #1a1a1a);
        }

        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: var(--soma-space-lg, 24px);
        }

        .header-actions {
          display: flex;
          gap: var(--soma-space-sm, 8px);
        }

        .btn {
          padding: 8px 16px;
          border-radius: var(--soma-radius-md, 8px);
          font-size: var(--soma-text-sm, 13px);
          font-weight: 500;
          cursor: pointer;
          border: 1px solid var(--soma-border, #e0e0e0);
          background: var(--soma-bg-card, #ffffff);
          color: var(--soma-text-primary, #1a1a1a);
          transition: all 0.15s ease;
        }

        .btn:hover {
          background: var(--soma-bg-hover, #fafafa);
        }

        .btn-primary {
          background: var(--soma-accent, #2563eb);
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
          background: var(--soma-bg-card, #ffffff);
          border: 1px solid var(--soma-border, #e0e0e0);
          border-radius: var(--soma-radius-lg, 12px);
          margin-bottom: var(--soma-space-lg, 24px);
        }

        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--soma-space-md, 16px) var(--soma-space-lg, 24px);
          border-bottom: 1px solid var(--soma-border, #e0e0e0);
        }

        .section-title {
          font-size: var(--soma-text-md, 16px);
          font-weight: 600;
          color: var(--soma-text-primary, #1a1a1a);
        }

        .section-content {
          padding: var(--soma-space-lg, 24px);
        }

        /* Tabs */
        .tabs {
          display: flex;
          border-bottom: 1px solid var(--soma-border, #e0e0e0);
          padding: 0 var(--soma-space-lg, 24px);
        }

        .tab {
          padding: var(--soma-space-md, 16px) var(--soma-space-lg, 24px);
          font-size: var(--soma-text-sm, 13px);
          font-weight: 500;
          color: var(--soma-text-secondary, #666666);
          background: none;
          border: none;
          border-bottom: 2px solid transparent;
          cursor: pointer;
          transition: all 0.15s ease;
        }

        .tab:hover {
          color: var(--soma-text-primary, #1a1a1a);
        }

        .tab.active {
          color: var(--soma-accent, #2563eb);
          border-bottom-color: var(--soma-accent, #2563eb);
        }

        /* Role & Permissions */
        .role-selector {
          display: flex;
          flex-direction: column;
          gap: var(--soma-space-md, 16px);
        }

        .role-select {
          padding: 10px 12px;
          background: var(--soma-bg-input, #ffffff);
          border: 1px solid var(--soma-border, #e0e0e0);
          border-radius: var(--soma-radius-md, 8px);
          font-size: var(--soma-text-base, 14px);
          max-width: 300px;
        }

        .permissions-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: var(--soma-space-md, 16px);
          margin-top: var(--soma-space-md, 16px);
        }

        .permission-group {
          background: var(--soma-bg-surface, #fafafa);
          padding: var(--soma-space-md, 16px);
          border-radius: var(--soma-radius-md, 8px);
        }

        .permission-group-title {
          font-size: var(--soma-text-sm, 13px);
          font-weight: 600;
          color: var(--soma-text-primary, #1a1a1a);
          margin-bottom: var(--soma-space-sm, 8px);
        }

        .permission-item {
          display: flex;
          align-items: center;
          gap: var(--soma-space-sm, 8px);
          font-size: var(--soma-text-sm, 13px);
          color: var(--soma-text-secondary, #666666);
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
          padding: var(--soma-space-sm, 8px) var(--soma-space-md, 16px);
          text-align: left;
          border-bottom: 1px solid var(--soma-border, #e0e0e0);
        }

        .agent-table th {
          font-size: var(--soma-text-xs, 11px);
          font-weight: 600;
          text-transform: uppercase;
          color: var(--soma-text-muted, #999999);
        }

        .agent-table td {
          font-size: var(--soma-text-sm, 13px);
          color: var(--soma-text-primary, #1a1a1a);
        }

        .mode-badge {
          display: inline-block;
          padding: 2px 6px;
          background: var(--soma-bg-surface, #fafafa);
          border: 1px solid var(--soma-border, #e0e0e0);
          border-radius: var(--soma-radius-sm, 4px);
          font-size: var(--soma-text-xs, 11px);
          margin-right: 4px;
        }

        .owner-badge {
          padding: 2px 6px;
          background: #fef3c7;
          color: #92400e;
          border-radius: var(--soma-radius-sm, 4px);
          font-size: var(--soma-text-xs, 11px);
          font-weight: 500;
        }

        /* Activity Log */
        .activity-list {
          display: flex;
          flex-direction: column;
        }

        .activity-item {
          display: flex;
          gap: var(--soma-space-md, 16px);
          padding: var(--soma-space-md, 16px) 0;
          border-bottom: 1px solid var(--soma-border, #e0e0e0);
        }

        .activity-item:last-child {
          border-bottom: none;
        }

        .activity-time {
          font-size: var(--soma-text-xs, 11px);
          color: var(--soma-text-muted, #999999);
          min-width: 140px;
        }

        .activity-content {
          flex: 1;
        }

        .activity-action {
          font-size: var(--soma-text-sm, 13px);
          color: var(--soma-text-primary, #1a1a1a);
        }

        .activity-target {
          font-size: var(--soma-text-xs, 11px);
          color: var(--soma-text-secondary, #666666);
        }

        /* Account Actions */
        .action-buttons {
          display: flex;
          flex-wrap: wrap;
          gap: var(--soma-space-sm, 8px);
        }

        .loading {
          display: flex;
          align-items: center;
          justify-content: center;
          padding: var(--soma-space-2xl, 48px);
          color: var(--soma-text-muted, #999999);
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
            // UserDetailOut lives on GET /aaas/admin/users/{id}/detail
            // (admin/aaas/api/users.py:354-413). GET /aaas/admin/users/{id}
            // returns TenantUserOut — a different, narrower shape with none
            // of displayName/roleLabel/mfaEnabled/permissions/agentAccess/
            // activityLog/sessions. Calling the narrow endpoint typed as
            // UserDetail made six tabs render empty instead of wrong.
            this.user = await apiClient.get<UserDetail>(`/aaas/admin/users/${this.userId}/detail`);
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
            // admin/aaas/api/users.py:253-274 takes `role` as a query
            // parameter, not a JSON body.
            await apiClient.put(
                `/aaas/admin/users/${this.userId}/role?role=${encodeURIComponent(newRole)}`,
                {},
            );
            this._loadUser();
        } catch (e) {
            console.error('Failed to change role:', e);
        }
    }

    private async _suspendUser() {
        const suspended = this.user?.status === 'suspended';
        const verb = suspended ? 'unsuspend' : 'suspend';
        if (!confirm(`Are you sure you want to ${verb} this user?`)) return;
        try {
            // Two real endpoints (admin/aaas/api/users.py:418-461). The
            // button label follows the row state and so does the verb.
            await apiClient.post(`/aaas/admin/users/${this.userId}/${verb}`, {});
            this._loadUser();
        } catch (e) {
            console.error(`Failed to ${verb} user:`, e);
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
              <a class="back-link" @click=${this._goBack}><span class="material-symbols-outlined">arrow_back</span> Back to Users</a>

              <div class="page-header">
                <soma-user-profile-card
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
                ></soma-user-profile-card>
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
              <soma-permission-guard permission="org:user_update" fallback="hide">
                <div class="content-section">
                  <div class="section-header">
                    <span class="section-title">Account Actions</span>
                  </div>
                  <div class="section-content">
                    <div class="action-buttons">
                      <button class="btn btn-danger" @click=${this._suspendUser}>
                        ${this.user.status === 'suspended' ? 'Unsuspend User' : html`<span class='material-symbols-outlined'>warning</span> Suspend User`}
                      </button>
                    </div>
                    <p class="muted">Password reset, MFA revoke and account delete have no API on this deployment.</p>
                  </div>
                </div>
              </soma-permission-guard>
            </div>
        `;
    }

    private _renderProfileTab() {
        if (!this.user) return nothing;

        // UserDetailOut.permissions is the real catalog list from
        // get_permissions_for_roles (admin/aaas/api/users.py:414). Render it
        // as sent — never check it against an invented group catalog.
        const permissions = this.user.permissions ?? [];

        return html`
            <div class="role-selector">
              <label style="font-weight: 600;">Role</label>
              <select 
                class="role-select"
                .value=${this.user.role}
                @change=${(e: Event) => this._changeRole((e.target as HTMLSelectElement).value)}
              >
                <!-- Exactly authz.ORG_ASSIGNABLE_ROLES. sysadmin is
                     provisioned at install and agent_owner is transferred,
                     so neither may be assigned from this control. -->
                <option value="org_admin">Organization Administrator</option>
                <option value="developer">Developer</option>
                <option value="trainer">Trainer</option>
                <option value="member">Member</option>
                <option value="auditor">Auditor</option>
                ${this.user.role === 'sysadmin' || this.user.role === 'agent_owner'
                  ? html`<option value=${this.user.role} disabled>
                      ${this.user.roleLabel} (provisioned — not assignable)
                    </option>`
                  : nothing}
              </select>

              <div style="margin-top: 16px;">
                <label style="font-weight: 600;">Permissions (from ${this.user.roleLabel})</label>
                <div class="permissions-grid">
                  ${permissions.length === 0
                    ? html`<p class="muted">The server reported no permissions for this role.</p>`
                    : permissions.map(p => html`
                        <div class="permission-item">
                          <span class="permission-check">
                            <span class='material-symbols-outlined' style='font-size:12px;'>check_circle</span>
                          </span>
                          ${p}
                        </div>
                    `)}
                </div>
              </div>
            </div>
        `;
    }

    private _renderAgentsTab() {
        if (!this.user) return nothing;
        const access = this.user.agentAccess ?? [];
        if (access.length === 0) {
            return html`<div style="color: var(--soma-text-muted); padding: 24px 0;">No agent access recorded for this user.</div>`;
        }

        return html`
            <div class="section-header" style="border: none; padding: 0 0 16px 0;">
              <span class="section-title">Agent Access</span>
              <span class="muted">Agent access changes go through agent ownership transfer.</span>
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
                ${access.map(agent => html`
                    <tr>
                      <td>${agent.agentName}</td>
                      <td>
                        ${agent.modes.map(m => html`<span class="mode-badge">${m}</span>`)}
                      </td>
                      <td>${agent.isOwner ? html`<span class="owner-badge">Owner</span>` : 'No'}</td>
                      <td>
                        <span class="muted">—</span>
                      </td>
                    </tr>
                `)}
              </tbody>
            </table>
        `;
    }

    private _renderActivityTab() {
        if (!this.user) return nothing;
        const log = this.user.activityLog ?? [];
        if (log.length === 0) {
            return html`<div style="color: var(--soma-text-muted); padding: 24px 0;">No activity recorded</div>`;
        }

        return html`
            <div class="activity-list">
              ${log.map(entry => html`
                          <div class="activity-item">
                            <div class="activity-time">${entry.timestamp ? new Date(entry.timestamp).toLocaleString() : '—'}</div>
                            <div class="activity-content">
                              <div class="activity-action">${entry.action}</div>
                              <div class="activity-target">${entry.target}</div>
                            </div>
                          </div>
                      `)}
            </div>
        `;
    }

    private _renderSessionsTab() {
        if (!this.user) return nothing;
        const sessions = this.user.sessions ?? [];
        if (sessions.length === 0) {
            return html`<div style="color: var(--soma-text-muted); padding: 24px 0;">No sessions recorded for this user.</div>`;
        }

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
                ${sessions.map(session => html`
                    <tr>
                      <td>
                        ${session.device}
                        ${session.current ? html`<span class="mode-badge" style="background: #dcfce7; color: #166534;">Current</span>` : ''}
                      </td>
                      <td>${session.location}</td>
                      <td>${session.lastActive ? new Date(session.lastActive).toLocaleString() : '—'}</td>
                      <td>
                        ${session.current ? html`<span class="muted">current</span>` : html`<span class="muted">—</span>`}
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
        'soma-user-detail': SomaUserDetail;
    }
}
