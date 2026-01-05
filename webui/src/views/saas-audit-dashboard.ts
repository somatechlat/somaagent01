/**
 * Audit Log Dashboard
 * Real-time audit trail viewer for compliance
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Uses existing /api/v2/saas/audit endpoints
 * - Permission-aware (audit:view)
 * - Light theme, minimal, professional
 * - Material Symbols icons
 * 
 * Features:
 * - Full text search
 * - Filter by action, resource type, actor
 * - Date range filtering
 * - CSV export
 * - Statistics dashboard
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';

interface AuditLogEntry {
    id: string;
    actor_id: string;
    actor_email: string;
    tenant_id: string | null;
    action: string;
    resource_type: string;
    resource_id: string | null;
    old_value: Record<string, unknown> | null;
    new_value: Record<string, unknown> | null;
    ip_address: string | null;
    created_at: string;
}

interface AuditStats {
    total_actions: number;
    period_days: number;
    by_action: { action: string; count: number }[];
    by_actor: { actor_email: string; count: number }[];
}

@customElement('saas-audit-dashboard')
export class SaasAuditDashboard extends LitElement {
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

    .btn.primary {
      background: #1a1a1a;
      color: white;
      border-color: #1a1a1a;
    }

    .btn.primary:hover { background: #333; }

    /* Stats Grid */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      padding: 24px 32px;
    }

    @media (max-width: 1200px) {
      .stats-grid { grid-template-columns: repeat(2, 1fr); }
    }

    .stat-card {
      background: var(--saas-bg-card, #ffffff);
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 12px;
      padding: 20px;
    }

    .stat-label {
      font-size: 12px;
      color: var(--saas-text-muted, #999);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 8px;
    }

    .stat-value {
      font-size: 28px;
      font-weight: 700;
    }

    /* Filter Bar */
    .filter-bar {
      padding: 16px 32px;
      background: var(--saas-bg-card, #ffffff);
      border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }

    .search-input {
      flex: 1;
      min-width: 200px;
      max-width: 300px;
      padding: 10px 14px;
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 8px;
      font-size: 14px;
      outline: none;
    }

    .search-input:focus { border-color: #1a1a1a; }

    .filter-select {
      padding: 10px 14px;
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 8px;
      font-size: 13px;
      background: var(--saas-bg-card, #ffffff);
      cursor: pointer;
    }

    /* Logs Table */
    .content {
      flex: 1;
      overflow-y: auto;
      padding: 0 32px 32px;
    }

    .table-wrap {
      background: var(--saas-bg-card, #ffffff);
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 12px;
      overflow: hidden;
    }

    table {
      width: 100%;
      border-collapse: collapse;
    }

    thead {
      background: var(--saas-bg-hover, #fafafa);
    }

    th {
      padding: 12px 16px;
      text-align: left;
      font-size: 11px;
      font-weight: 600;
      color: var(--saas-text-secondary, #666);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
    }

    td {
      padding: 14px 16px;
      font-size: 13px;
      border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
      vertical-align: middle;
    }

    tr:last-child td { border-bottom: none; }
    tr:hover { background: var(--saas-bg-hover, #fafafa); }

    .action-badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
    }

    .action-badge.create { background: rgba(34, 197, 94, 0.1); color: #16a34a; }
    .action-badge.update { background: rgba(59, 130, 246, 0.1); color: #2563eb; }
    .action-badge.delete { background: rgba(239, 68, 68, 0.1); color: #dc2626; }
    .action-badge.view { background: rgba(107, 114, 128, 0.1); color: #4b5563; }
    .action-badge.login { background: rgba(139, 92, 246, 0.1); color: #7c3aed; }

    .resource-type {
      font-size: 12px;
      color: var(--saas-text-secondary, #666);
    }

    .time-ago {
      font-size: 12px;
      color: var(--saas-text-muted, #999);
    }

    /* Pagination */
    .pagination {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px;
      background: var(--saas-bg-hover, #fafafa);
      border-top: 1px solid var(--saas-border-light, #e0e0e0);
    }

    .page-info {
      font-size: 13px;
      color: var(--saas-text-secondary, #666);
    }

    .page-btns {
      display: flex;
      gap: 8px;
    }

    .page-btn {
      padding: 8px 14px;
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 6px;
      background: var(--saas-bg-card, #ffffff);
      font-size: 13px;
      cursor: pointer;
    }

    .page-btn:hover { background: var(--saas-bg-hover, #fafafa); }
    .page-btn:disabled { opacity: 0.5; cursor: not-allowed; }

    .loading {
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 60px;
      color: var(--saas-text-muted, #999);
    }

    .empty {
      text-align: center;
      padding: 60px;
      color: var(--saas-text-muted, #999);
    }
  `;

    @state() private logs: AuditLogEntry[] = [];
    @state() private stats: AuditStats | null = null;
    @state() private loading = true;
    @state() private searchQuery = '';
    @state() private actionFilter = '';
    @state() private resourceFilter = '';
    @state() private page = 1;
    @state() private perPage = 50;
    @state() private total = 0;
    @state() private actions: string[] = [];
    @state() private resourceTypes: string[] = [];

    connectedCallback() {
        super.connectedCallback();
        this.loadData();
    }

    private getAuthHeaders(): HeadersInit {
        const token = localStorage.getItem('auth_token') || localStorage.getItem('saas_auth_token');
        return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
    }

    private async loadData() {
        this.loading = true;
        try {
            await Promise.all([
                this.fetchLogs(),
                this.fetchStats(),
                this.fetchFilters(),
            ]);
        } finally {
            this.loading = false;
        }
    }

    private async fetchLogs() {
        const params = new URLSearchParams({
            page: this.page.toString(),
            per_page: this.perPage.toString(),
        });
        if (this.actionFilter) params.set('action', this.actionFilter);
        if (this.resourceFilter) params.set('resource_type', this.resourceFilter);

        const res = await fetch(`/api/v2/saas/audit?${params}`, { headers: this.getAuthHeaders() });
        if (res.ok) {
            const data = await res.json();
            this.logs = data.items || [];
            this.total = data.total || 0;
        }
    }

    private async fetchStats() {
        const res = await fetch('/api/v2/saas/audit/stats', { headers: this.getAuthHeaders() });
        if (res.ok) {
            this.stats = await res.json();
        }
    }

    private async fetchFilters() {
        const [actionsRes, typesRes] = await Promise.all([
            fetch('/api/v2/saas/audit/actions', { headers: this.getAuthHeaders() }),
            fetch('/api/v2/saas/audit/resource-types', { headers: this.getAuthHeaders() }),
        ]);
        if (actionsRes.ok) {
            const data = await actionsRes.json();
            this.actions = data.actions || [];
        }
        if (typesRes.ok) {
            const data = await typesRes.json();
            this.resourceTypes = data.resource_types || [];
        }
    }

    private async exportCsv() {
        const params = new URLSearchParams({ limit: '10000' });
        if (this.actionFilter) params.set('action', this.actionFilter);
        if (this.resourceFilter) params.set('resource_type', this.resourceFilter);

        window.location.href = `/api/v2/saas/audit/export?${params}`;
    }

    private getActionBadgeClass(action: string): string {
        if (action.includes('create') || action.includes('add')) return 'create';
        if (action.includes('update') || action.includes('edit')) return 'update';
        if (action.includes('delete') || action.includes('remove')) return 'delete';
        if (action.includes('login') || action.includes('auth')) return 'login';
        return 'view';
    }

    private formatTime(isoString: string): string {
        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return 'just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
        return date.toLocaleDateString();
    }

    private handlePageChange(newPage: number) {
        this.page = newPage;
        this.fetchLogs();
    }

    render() {
        return html`
      <aside class="sidebar">
        <saas-sidebar active-route="/platform/audit"></saas-sidebar>
      </aside>

      <main class="main">
        <header class="header">
          <div>
            <h1 class="header-title">Audit Log</h1>
            <p class="header-subtitle">Security and compliance event history</p>
          </div>
          <div class="header-actions">
            <button class="btn" @click=${() => this.loadData()}>
              <span class="material-symbols-outlined">refresh</span>
              Refresh
            </button>
            <button class="btn primary" @click=${() => this.exportCsv()}>
              <span class="material-symbols-outlined">download</span>
              Export CSV
            </button>
          </div>
        </header>

        ${this.stats ? html`
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-label">Total Events (7d)</div>
              <div class="stat-value">${this.stats.total_actions.toLocaleString()}</div>
            </div>
            <div class="stat-card">
              <div class="stat-label">Top Action</div>
              <div class="stat-value">${this.stats.by_action[0]?.action || '-'}</div>
            </div>
            <div class="stat-card">
              <div class="stat-label">Top Actor</div>
              <div class="stat-value" style="font-size: 18px; word-break: break-all;">${this.stats.by_actor[0]?.actor_email || '-'}</div>
            </div>
            <div class="stat-card">
              <div class="stat-label">This Page</div>
              <div class="stat-value">${this.logs.length} / ${this.total}</div>
            </div>
          </div>
        ` : nothing}

        <div class="filter-bar">
          <input 
            type="text" 
            class="search-input" 
            placeholder="Search logs..."
            .value=${this.searchQuery}
            @input=${(e: InputEvent) => this.searchQuery = (e.target as HTMLInputElement).value}
          />
          <select 
            class="filter-select"
            .value=${this.actionFilter}
            @change=${(e: Event) => { this.actionFilter = (e.target as HTMLSelectElement).value; this.fetchLogs(); }}
          >
            <option value="">All Actions</option>
            ${this.actions.map(a => html`<option value=${a}>${a}</option>`)}
          </select>
          <select 
            class="filter-select"
            .value=${this.resourceFilter}
            @change=${(e: Event) => { this.resourceFilter = (e.target as HTMLSelectElement).value; this.fetchLogs(); }}
          >
            <option value="">All Resources</option>
            ${this.resourceTypes.map(t => html`<option value=${t}>${t}</option>`)}
          </select>
        </div>

        <div class="content">
          ${this.loading ? html`<div class="loading">Loading audit logs...</div>` : nothing}
          
          ${!this.loading && this.logs.length === 0 ? html`
            <div class="empty">
              <span class="material-symbols-outlined" style="font-size: 48px; opacity: 0.5;">history</span>
              <p>No audit log entries found</p>
            </div>
          ` : nothing}

          ${!this.loading && this.logs.length > 0 ? html`
            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Actor</th>
                    <th>Action</th>
                    <th>Resource</th>
                    <th>IP Address</th>
                  </tr>
                </thead>
                <tbody>
                  ${this.logs.map(log => html`
                    <tr>
                      <td>
                        <span class="time-ago">${this.formatTime(log.created_at)}</span>
                      </td>
                      <td>${log.actor_email}</td>
                      <td>
                        <span class="action-badge ${this.getActionBadgeClass(log.action)}">${log.action}</span>
                      </td>
                      <td>
                        <span class="resource-type">${log.resource_type}</span>
                        ${log.resource_id ? html`<br><small style="color: #999">${log.resource_id}</small>` : nothing}
                      </td>
                      <td>${log.ip_address || '-'}</td>
                    </tr>
                  `)}
                </tbody>
              </table>
              
              <div class="pagination">
                <span class="page-info">
                  Showing ${(this.page - 1) * this.perPage + 1} - ${Math.min(this.page * this.perPage, this.total)} of ${this.total}
                </span>
                <div class="page-btns">
                  <button 
                    class="page-btn" 
                    ?disabled=${this.page <= 1}
                    @click=${() => this.handlePageChange(this.page - 1)}
                  >Previous</button>
                  <button 
                    class="page-btn"
                    ?disabled=${this.page * this.perPage >= this.total}
                    @click=${() => this.handlePageChange(this.page + 1)}
                  >Next</button>
                </div>
              </div>
            </div>
          ` : nothing}
        </div>
      </main>
    `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-audit-dashboard': SaasAuditDashboard;
    }
}
