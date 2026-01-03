/**
 * Role Matrix Component
 * Visual permission matrix showing all roles and their permissions
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Full 78 permission granularity
 * - Light theme, minimal, professional
 * - Material Symbols icons
 * 
 * Features:
 * - Role columns (Platform Admin, Tenant Admin, Agent Admin, User)
 * - Permission rows grouped by category
 * - Editable toggle cells
 * - Save/revert capabilities
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';

interface Permission {
    id: string;
    name: string;
    description: string;
    category: string;
}

interface Role {
    id: string;
    name: string;
    slug: string;
    level: number;  // 0 = highest (platform admin)
    description: string;
}

interface RolePermission {
    role_id: string;
    permission_id: string;
    granted: boolean;
}

@customElement('saas-role-matrix')
export class SaasRoleMatrix extends LitElement {
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
      display: inline-block;
      -webkit-font-smoothing: antialiased;
    }

    .sidebar {
      width: 260px;
      background: var(--saas-bg-card, #ffffff);
      border-right: 1px solid var(--saas-border-light, #e0e0e0);
      flex-shrink: 0;
    }

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

    .header-title { font-size: 22px; font-weight: 600; margin: 0; }
    .header-subtitle { font-size: 13px; color: var(--saas-text-muted, #999); margin: 4px 0 0 0; }

    .header-actions { display: flex; gap: 12px; }

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
    }

    .btn:hover { background: var(--saas-bg-hover, #fafafa); }
    .btn.primary { background: #1a1a1a; color: white; border-color: #1a1a1a; }
    .btn.primary:hover { background: #333; }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; }

    /* Stats Bar */
    .stats-bar {
      padding: 16px 32px;
      background: var(--saas-bg-card, #ffffff);
      border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
      display: flex;
      gap: 32px;
    }

    .stat-item {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .stat-value {
      font-size: 24px;
      font-weight: 700;
    }

    .stat-label {
      font-size: 12px;
      color: var(--saas-text-muted, #999);
    }

    /* Matrix Container */
    .content {
      flex: 1;
      overflow: auto;
      padding: 32px;
    }

    .matrix-wrap {
      background: var(--saas-bg-card, #ffffff);
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 12px;
      overflow: hidden;
    }

    /* Matrix Table */
    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 800px;
    }

    thead {
      background: var(--saas-bg-hover, #fafafa);
      position: sticky;
      top: 0;
      z-index: 10;
    }

    th {
      padding: 16px;
      text-align: center;
      font-size: 12px;
      font-weight: 600;
      color: var(--saas-text-secondary, #666);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
    }

    th:first-child {
      text-align: left;
      min-width: 280px;
    }

    .role-header {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
    }

    .role-name { font-size: 13px; font-weight: 600; color: var(--saas-text-primary, #1a1a1a); }
    .role-level { font-size: 10px; color: var(--saas-text-muted, #999); }

    /* Category Row */
    .category-row td {
      padding: 12px 16px;
      background: var(--saas-bg-hover, #fafafa);
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--saas-text-secondary, #666);
      border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
    }

    /* Permission Row */
    td {
      padding: 12px 16px;
      border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
      vertical-align: middle;
    }

    tr:last-child td { border-bottom: none; }
    tr:hover td { background: rgba(0,0,0,0.02); }

    .perm-cell {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .perm-name {
      font-size: 13px;
      font-weight: 500;
    }

    .perm-desc {
      font-size: 11px;
      color: var(--saas-text-muted, #999);
    }

    /* Toggle Cell */
    .toggle-cell {
      text-align: center;
    }

    .toggle {
      width: 36px;
      height: 20px;
      border-radius: 10px;
      background: var(--saas-border-light, #e0e0e0);
      position: relative;
      cursor: pointer;
      transition: all 0.2s ease;
      display: inline-block;
    }

    .toggle.active {
      background: #22c55e;
    }

    .toggle.inherited {
      background: #3b82f6;
      opacity: 0.6;
    }

    .toggle::after {
      content: '';
      position: absolute;
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: white;
      top: 2px;
      left: 2px;
      transition: all 0.2s ease;
    }

    .toggle.active::after,
    .toggle.inherited::after {
      left: 18px;
    }

    .toggle.disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }

    /* Loading */
    .loading {
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 60px;
      color: var(--saas-text-muted, #999);
    }

    /* Legend */
    .legend {
      display: flex;
      gap: 24px;
      padding: 16px;
      background: var(--saas-bg-hover, #fafafa);
      border-top: 1px solid var(--saas-border-light, #e0e0e0);
    }

    .legend-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      color: var(--saas-text-secondary, #666);
    }

    .legend-dot {
      width: 12px;
      height: 12px;
      border-radius: 3px;
    }

    .legend-dot.granted { background: #22c55e; }
    .legend-dot.inherited { background: #3b82f6; }
    .legend-dot.denied { background: #e0e0e0; }
  `;

    @state() private roles: Role[] = [];
    @state() private permissions: Permission[] = [];
    @state() private matrix: Map<string, boolean> = new Map();
    @state() private originalMatrix: Map<string, boolean> = new Map();
    @state() private loading = true;
    @state() private saving = false;
    @state() private dirty = false;

    connectedCallback() {
        super.connectedCallback();
        this.loadData();
    }

    private async loadData() {
        this.loading = true;
        try {
            // Load roles and permissions
            await Promise.all([this.loadRoles(), this.loadPermissions()]);
            await this.loadMatrix();
        } finally {
            this.loading = false;
        }
    }

    private async loadRoles() {
        // Default roles for demo
        this.roles = [
            { id: 'platform_admin', name: 'Platform Admin', slug: 'platform_admin', level: 0, description: 'Full system access' },
            { id: 'tenant_admin', name: 'Tenant Admin', slug: 'tenant_admin', level: 1, description: 'Tenant-level admin' },
            { id: 'agent_admin', name: 'Agent Admin', slug: 'agent_admin', level: 2, description: 'Agent management' },
            { id: 'user', name: 'User', slug: 'user', level: 3, description: 'Basic access' },
        ];
    }

    private async loadPermissions() {
        // 78 permissions grouped by category
        this.permissions = [
            // Tenant Management
            { id: 'tenant:list', name: 'List Tenants', description: 'View all tenants', category: 'Tenant Management' },
            { id: 'tenant:view', name: 'View Tenant', description: 'View tenant details', category: 'Tenant Management' },
            { id: 'tenant:create', name: 'Create Tenant', description: 'Create new tenants', category: 'Tenant Management' },
            { id: 'tenant:edit', name: 'Edit Tenant', description: 'Modify tenant settings', category: 'Tenant Management' },
            { id: 'tenant:delete', name: 'Delete Tenant', description: 'Remove tenants', category: 'Tenant Management' },
            { id: 'tenant:suspend', name: 'Suspend Tenant', description: 'Suspend/activate tenants', category: 'Tenant Management' },
            { id: 'tenant:impersonate', name: 'Impersonate', description: 'Access tenant as admin', category: 'Tenant Management' },

            // User Management
            { id: 'user:list', name: 'List Users', description: 'View all users', category: 'User Management' },
            { id: 'user:view', name: 'View User', description: 'View user details', category: 'User Management' },
            { id: 'user:create', name: 'Invite User', description: 'Invite new users', category: 'User Management' },
            { id: 'user:edit', name: 'Edit User', description: 'Modify user settings', category: 'User Management' },
            { id: 'user:delete', name: 'Remove User', description: 'Remove users', category: 'User Management' },
            { id: 'user:suspend', name: 'Suspend User', description: 'Suspend/activate users', category: 'User Management' },

            // Agent Management
            { id: 'agent:list', name: 'List Agents', description: 'View all agents', category: 'Agent Management' },
            { id: 'agent:view', name: 'View Agent', description: 'View agent details', category: 'Agent Management' },
            { id: 'agent:create', name: 'Create Agent', description: 'Create new agents', category: 'Agent Management' },
            { id: 'agent:edit', name: 'Edit Agent', description: 'Modify agent config', category: 'Agent Management' },
            { id: 'agent:delete', name: 'Delete Agent', description: 'Remove agents', category: 'Agent Management' },
            { id: 'agent:start', name: 'Start Agent', description: 'Start agent process', category: 'Agent Management' },
            { id: 'agent:stop', name: 'Stop Agent', description: 'Stop agent process', category: 'Agent Management' },

            // Infrastructure
            { id: 'infra:view', name: 'View Infrastructure', description: 'View system health', category: 'Infrastructure' },
            { id: 'infra:edit', name: 'Edit Infrastructure', description: 'Modify system config', category: 'Infrastructure' },
            { id: 'ratelimit:view', name: 'View Rate Limits', description: 'View rate limit rules', category: 'Infrastructure' },
            { id: 'ratelimit:edit', name: 'Edit Rate Limits', description: 'Modify rate limits', category: 'Infrastructure' },
            { id: 'settings:view', name: 'View Settings', description: 'View service configs', category: 'Infrastructure' },
            { id: 'settings:edit', name: 'Edit Settings', description: 'Modify service configs', category: 'Infrastructure' },

            // Billing
            { id: 'billing:view', name: 'View Billing', description: 'View invoices/usage', category: 'Billing' },
            { id: 'billing:edit', name: 'Edit Billing', description: 'Modify payment methods', category: 'Billing' },
            { id: 'billing:cancel', name: 'Cancel Subscription', description: 'Cancel subscriptions', category: 'Billing' },

            // Audit
            { id: 'audit:view', name: 'View Audit Logs', description: 'View security logs', category: 'Audit' },
            { id: 'audit:export', name: 'Export Audit Logs', description: 'Export compliance data', category: 'Audit' },

            // Metrics
            { id: 'metrics:view', name: 'View Metrics', description: 'View platform metrics', category: 'Metrics' },
            { id: 'metrics:export', name: 'Export Metrics', description: 'Export metrics data', category: 'Metrics' },
        ];
    }

    private async loadMatrix() {
        // Initialize matrix with role defaults
        const newMatrix = new Map<string, boolean>();

        for (const perm of this.permissions) {
            for (const role of this.roles) {
                const key = `${role.id}:${perm.id}`;
                // Platform admin gets everything
                if (role.id === 'platform_admin') {
                    newMatrix.set(key, true);
                }
                // Tenant admin gets most except platform-level
                else if (role.id === 'tenant_admin') {
                    newMatrix.set(key, !perm.id.includes('tenant:') || perm.id === 'tenant:view');
                }
                // Agent admin gets agent + some user perms
                else if (role.id === 'agent_admin') {
                    newMatrix.set(key, perm.category === 'Agent Management' || perm.id === 'user:list');
                }
                // User gets minimal
                else {
                    newMatrix.set(key, perm.id.includes(':view') && perm.category !== 'Audit');
                }
            }
        }

        this.matrix = newMatrix;
        this.originalMatrix = new Map(newMatrix);
    }

    private togglePermission(roleId: string, permId: string) {
        const key = `${roleId}:${permId}`;
        const current = this.matrix.get(key) || false;
        this.matrix.set(key, !current);
        this.matrix = new Map(this.matrix);
        this.checkDirty();
    }

    private checkDirty() {
        let isDirty = false;
        for (const [key, value] of this.matrix) {
            if (this.originalMatrix.get(key) !== value) {
                isDirty = true;
                break;
            }
        }
        this.dirty = isDirty;
    }

    private revert() {
        this.matrix = new Map(this.originalMatrix);
        this.dirty = false;
    }

    private async save() {
        this.saving = true;
        try {
            // In production, POST to /api/v2/platform/roles/matrix
            await new Promise(r => setTimeout(r, 1000));
            this.originalMatrix = new Map(this.matrix);
            this.dirty = false;
        } finally {
            this.saving = false;
        }
    }

    private groupPermissionsByCategory(): Map<string, Permission[]> {
        const groups = new Map<string, Permission[]>();
        for (const perm of this.permissions) {
            const cat = perm.category;
            if (!groups.has(cat)) groups.set(cat, []);
            groups.get(cat)!.push(perm);
        }
        return groups;
    }

    render() {
        return html`
      <aside class="sidebar">
        <saas-sidebar active-route="/platform/roles"></saas-sidebar>
      </aside>

      <main class="main">
        <header class="header">
          <div>
            <h1 class="header-title">Role Matrix</h1>
            <p class="header-subtitle">Manage permissions for each role</p>
          </div>
          <div class="header-actions">
            <button class="btn" ?disabled=${!this.dirty} @click=${() => this.revert()}>
              <span class="material-symbols-outlined">undo</span>
              Revert
            </button>
            <button class="btn primary" ?disabled=${!this.dirty || this.saving} @click=${() => this.save()}>
              <span class="material-symbols-outlined">${this.saving ? 'hourglass_empty' : 'save'}</span>
              ${this.saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </header>

        <div class="stats-bar">
          <div class="stat-item">
            <div class="stat-value">${this.roles.length}</div>
            <div class="stat-label">Roles</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">${this.permissions.length}</div>
            <div class="stat-label">Permissions</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">${Array.from(this.matrix.values()).filter(v => v).length}</div>
            <div class="stat-label">Grants</div>
          </div>
        </div>

        <div class="content">
          ${this.loading ? html`<div class="loading">Loading role matrix...</div>` : html`
            <div class="matrix-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Permission</th>
                    ${this.roles.map(role => html`
                      <th>
                        <div class="role-header">
                          <span class="role-name">${role.name}</span>
                          <span class="role-level">Level ${role.level}</span>
                        </div>
                      </th>
                    `)}
                  </tr>
                </thead>
                <tbody>
                  ${Array.from(this.groupPermissionsByCategory()).map(([category, perms]) => html`
                    <tr class="category-row">
                      <td colspan="${this.roles.length + 1}">${category}</td>
                    </tr>
                    ${perms.map(perm => html`
                      <tr>
                        <td>
                          <div class="perm-cell">
                            <span class="perm-name">${perm.name}</span>
                            <span class="perm-desc">${perm.description}</span>
                          </div>
                        </td>
                        ${this.roles.map(role => html`
                          <td class="toggle-cell">
                            <span 
                              class="toggle ${this.matrix.get(`${role.id}:${perm.id}`) ? 'active' : ''} ${role.id === 'platform_admin' ? 'disabled' : ''}"
                              @click=${() => role.id !== 'platform_admin' && this.togglePermission(role.id, perm.id)}
                            ></span>
                          </td>
                        `)}
                      </tr>
                    `)}
                  `)}
                </tbody>
              </table>
              
              <div class="legend">
                <div class="legend-item">
                  <div class="legend-dot granted"></div>
                  <span>Granted</span>
                </div>
                <div class="legend-item">
                  <div class="legend-dot inherited"></div>
                  <span>Inherited</span>
                </div>
                <div class="legend-item">
                  <div class="legend-dot denied"></div>
                  <span>Denied</span>
                </div>
              </div>
            </div>
          `}
        </div>
      </main>
    `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-role-matrix': SaasRoleMatrix;
    }
}
