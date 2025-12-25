import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
// Components imported dynamically as needed

// Interface Definitions based on API
interface Role {
  role_id: string;
  name: string;
  description?: string;
  permissions: string[];
  is_system: boolean;
  tenant_id?: string;
}

interface Permission {
  permission_id: string;
  name: string;
  resource: string;
  action: string;
  description?: string;
}

interface GranularPermission {
  id: string;
  name: string;
  resource: string;
  description: string;
}

@customElement('saas-permissions')
export class SaasPermissions extends LitElement {
  @state() roles: Role[] = [];
  @state() permissions: Permission[] = [];
  @state() loading = true;
  @state() error = '';
  @state() activeTab: 'matrix' | 'check' | 'roles' = 'matrix';

  // Filtering
  @state() selectedResource = 'all';

  // Checker State
  @state() checkUserId = '';
  @state() checkPermission = '';
  @state() checkResult: { allowed: boolean; reason: string } | null = null;
  @state() checking = false;

  static styles = css`
    :host {
      display: block;
      height: 100vh;
      background-color: var(--saas-bg-main, #f9fafb);
      color: var(--saas-text-main, #111827);
      font-family: var(--saas-font-sans, 'Inter', sans-serif);
      --saas-border: #e5e7eb;
      --saas-primary: #000000;
      --saas-success: #10b981;
      --saas-danger: #ef4444;
    }

    .layout {
      display: flex;
      height: 100%;
    }

    main {
      flex: 1;
      overflow-y: auto;
      padding: 2rem;
    }

    header {
      margin-bottom: 2rem;
    }

    h1 {
      font-size: 1.5rem;
      font-weight: 600;
      margin: 0;
    }
    
    p.subtitle {
      color: #6b7280;
      margin-top: 0.5rem;
    }

    .tabs {
      display: flex;
      gap: 1rem;
      border-bottom: 1px solid var(--saas-border);
      margin-bottom: 1.5rem;
    }

    .tab {
      padding: 0.75rem 1rem;
      cursor: pointer;
      border-bottom: 2px solid transparent;
      font-weight: 500;
      color: #6b7280;
    }

    .tab.active {
      color: var(--saas-primary);
      border-bottom-color: var(--saas-primary);
    }

    /* Matrix Styles */
    .matrix-container {
      background: white;
      border: 1px solid var(--saas-border);
      border-radius: 0.5rem;
      overflow-x: auto;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .toolbar {
      padding: 1rem;
      border-bottom: 1px solid var(--saas-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    select, input {
      padding: 0.5rem;
      border: 1px solid var(--saas-border);
      border-radius: 0.375rem;
      font-size: 0.875rem;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.875rem;
    }

    th, td {
      padding: 0.75rem 1rem;
      text-align: left;
      border-bottom: 1px solid var(--saas-border);
    }

    th {
      background-color: #f9fafb;
      font-weight: 600;
      position: sticky;
      top: 0;
    }
    
    .role-header {
      writing-mode: vertical-rl;
      transform: rotate(180deg);
      padding: 1rem 0.5rem;
      height: 120px;
      vertical-align: bottom;
    }

    .check-mark {
      color: var(--saas-success);
      font-weight: bold;
      text-align: center;
    }
    
    .dash-mark {
      color: #d1d5db;
      text-align: center;
    }

    /* Permission Checker Styles */
    .checker-card {
      background: white;
      padding: 2rem;
      border: 1px solid var(--saas-border);
      border-radius: 0.5rem;
      max-width: 600px;
    }

    .form-group {
      margin-bottom: 1rem;
    }

    label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: 500;
    }

    button {
      background-color: var(--saas-primary);
      color: white;
      padding: 0.5rem 1rem;
      border-radius: 0.375rem;
      border: none;
      cursor: pointer;
      font-weight: 500;
    }

    .result-box {
      margin-top: 1.5rem;
      padding: 1rem;
      border-radius: 0.375rem;
    }
    
    .result-box.allowed {
      background-color: #ecfdf5; /* green-50 */
      color: #065f46; /* green-800 */
      border: 1px solid #10b981;
    }

    .result-box.denied {
      background-color: #fef2f2; /* red-50 */
      color: #991b1b; /* red-800 */
      border: 1px solid #ef4444;
    }
    
    .tag {
      display: inline-block;
      padding: 0.125rem 0.375rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 500;
    }
    
    .tag.system { background: #e0e7ff; color: #3730a3; }
    .tag.custom { background: #f3f4f6; color: #1f2937; }
  `;

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  async fetchData() {
    try {
      this.loading = true;
      const token = localStorage.getItem('auth_token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Parallel fetch
      const [rolesRes, permsRes] = await Promise.all([
        fetch('/api/v2/permissions/roles', { headers }),
        fetch('/api/v2/permissions/permissions', { headers }),
      ]);

      if (!rolesRes.ok || !permsRes.ok) throw new Error('Failed to fetch data');

      const rolesData = await rolesRes.json();
      const permsData = await permsRes.json();

      this.roles = rolesData.roles;
      this.permissions = permsData.permissions;
    } catch (err: any) {
      this.error = err.message;
    } finally {
      this.loading = false;
    }
  }

  async checkPermissionApi() {
    if (!this.checkUserId || !this.checkPermission) return;

    this.checking = true;
    this.checkResult = null;

    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch('/api/v2/permissions/check', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: this.checkUserId,
          permission: this.checkPermission
        })
      });

      const data = await res.json();
      this.checkResult = data;
    } catch (err) {
      this.checkResult = { allowed: false, reason: 'API Error' };
    } finally {
      this.checking = false;
    }
  }

  // Helper to check if a role key exists in permissions array (simplified logic for now)
  hasPermission(role: Role, perm: Permission): boolean {
    if (role.permissions.includes('*')) return true;
    if (role.permissions.includes(`${perm.resource}:*`)) return true; // Wildcard resource
    return role.permissions.includes(perm.permission_id);
  }

  uniqueResources() {
    const resources = new Set(this.permissions.map(p => p.resource));
    return ['all', ...Array.from(resources)];
  }

  filteredPermissions() {
    if (this.selectedResource === 'all') return this.permissions;
    return this.permissions.filter(p => p.resource === this.selectedResource);
  }

  render() {
    return html`
      <div class="layout">
        <!-- Sidebar placeholder if not globally included -->
        <!-- <saas-sidebar></saas-sidebar> -->
        
        <main>
          <header>
            <h1>Permission Browser</h1>
            <p class="subtitle">Inspect Role-Based Access Control policies across the platform.</p>
          </header>

          <div class="tabs">
            <div class="tab ${this.activeTab === 'matrix' ? 'active' : ''}" 
                 @click=${() => this.activeTab = 'matrix'}>
              Permission Matrix
            </div>
            <div class="tab ${this.activeTab === 'check' ? 'active' : ''}" 
                 @click=${() => this.activeTab = 'check'}>
              Access Checker
            </div>
          </div>

          ${this.loading ? html`<div class="loading">Loading permissions...</div>` : nothing}
          ${this.error ? html`<div class="error">${this.error}</div>` : nothing}

          ${!this.loading && this.activeTab === 'matrix' ? this.renderMatrix() : nothing}
          ${!this.loading && this.activeTab === 'check' ? this.renderChecker() : nothing}
        </main>
      </div>
    `;
  }

  renderMatrix() {
    const visiblePermissions = this.filteredPermissions();

    return html`
      <div class="matrix-container">
        <div class="toolbar">
          <div>
            <label for="resource-filter" style="display:inline; margin-right: 0.5rem">Filter by Resource:</label>
            <select id="resource-filter" .value=${this.selectedResource} @change=${(e: any) => this.selectedResource = e.target.value}>
              ${this.uniqueResources().map(r => html`<option value=${r}>${r.toUpperCase()}</option>`)}
            </select>
          </div>
          <div>
            <!-- Actions could go here -->
          </div>
        </div>
        
        <table>
          <thead>
            <tr>
              <th style="min-width: 200px;">Permission</th>
              <th style="min-width: 100px;">Resource</th>
              ${this.roles.map(role => html`
                <th class="role-header" title="${role.description}">
                  ${role.name}
                  <span class="tag ${role.is_system ? 'system' : 'custom'}">
                    ${role.is_system ? 'SYS' : 'CUS'}
                  </span>
                </th>
              `)}
            </tr>
          </thead>
          <tbody>
            ${visiblePermissions.map(perm => html`
              <tr>
                <td>
                  <strong>${perm.name}</strong><br>
                  <span style="color:#9ca3af; font-family:monospace; font-size:0.75rem">${perm.permission_id}</span>
                </td>
                <td><span class="tag custom">${perm.resource}</span></td>
                ${this.roles.map(role => html`
                  <td style="text-align:center;">
                    ${this.hasPermission(role, perm)
        ? html`<span class="check-mark">✓</span>`
        : html`<span class="dash-mark">-</span>`}
                  </td>
                `)}
              </tr>
            `)}
          </tbody>
        </table>
      </div>
    `;
  }

  renderChecker() {
    return html`
      <div class="checker-card">
        <h3>Verify Access</h3>
        <p style="color:#6b7280; margin-bottom: 1.5rem">Simulate a permission check for a specific user and action.</p>
        
        <div class="form-group">
          <label>User ID / Email</label>
          <input type="text" 
                 placeholder="e.g. user-123 or admin@example.com" 
                 .value=${this.checkUserId}
                 @input=${(e: any) => this.checkUserId = e.target.value}>
        </div>
        
        <div class="form-group">
          <label>Permission Key</label>
          <input type="text" 
                 placeholder="e.g. agent:write" 
                 .value=${this.checkPermission}
                 @input=${(e: any) => this.checkPermission = e.target.value}>
        </div>
        
        <button @click=${this.checkPermissionApi} ?disabled=${this.checking}>
          ${this.checking ? 'Checking...' : 'Check Access'}
        </button>
        
        ${this.checkResult ? html`
          <div class="result-box ${this.checkResult.allowed ? 'allowed' : 'denied'}">
            <strong>${this.checkResult.allowed ? 'ACCESS GRANTED' : 'ACCESS DENIED'}</strong>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.875rem">Reason: ${this.checkResult.reason}</p>
          </div>
        ` : nothing}
      </div>
    `;
  }
}
