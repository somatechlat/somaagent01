/**
 * Entity Manager Component
 * CRUD interface for the entity types that actually have screens and APIs.
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Permission-aware action filtering
 * - Composes soma-data-table and soma-action-menu
 * - Light theme, minimal, professional
 * - Material Symbols icons
 *
 * Usage:
 * <entity-manager
 *   entity="user"
 *   api-base="/api/v2/aaas/admin"
 *   .permissions=${userPermissions}
 * />
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import type { TableColumn } from './soma-data-table.js';
import type { ActionItem } from './soma-action-menu.js';
import './soma-data-table.js';
import './soma-action-menu.js';

// Entity configuration for different entity types
interface EntityConfig {
    displayName: string;
    displayNamePlural: string;
    icon: string;
    defaultColumns: TableColumn[];
    actions: ActionDef[];
    /** Field the status filter reads. Users carry `is_active: boolean`;
     *  agents carry `status: string`. One vocabulary per entity, never both. */
    statusField: 'is_active' | 'status';
    /** Values the status filter offers, as the server stores them. */
    statusOptions: { value: string; label: string }[];
}

interface ActionDef {
    id: string;
    label: string;
    icon: string;
    /** A permission name from the authorization catalog (admin.core.authz).
     *  Never a template fragment: a name the catalog does not contain is not
     *  a permission, and a control gated on one can never be authorized. */
    permission: string;
    variant?: 'default' | 'danger';
    requiresConfirm?: boolean;
    /** REQ-UIX-005: present-but-disabled, with the blocking reason inline.
     *  A control with no handler is a lie; a disabled control with no reason
     *  is a compliance failure. */
    disabledReason?: string;
}

// Actions are declared per entity below with the exact catalog permission
// that authorizes them. There is no shared default list: the same verb on two
// entities is two different permissions (`org:update` is not `agent:update`),
// and a shared template is how the old `tenant:edit` style names appeared.

// Blocking reasons for controls whose backend handler is not mounted on this
// deployment. Printed inline (REQ-UIX-005). Verified against
// admin/aaas/api/users.py, admin/aaas/api/tenant_agents.py, admin/auth/api.py.
const REASON_NO_PASSWORD_RESET =
    'Blocked: no password-reset route is mounted (admin/auth/api.py).';
const REASON_NO_EDIT_SCREEN =
    'Blocked: no edit screen is routed for this entity.';
const REASON_NO_CREATE_SCREEN =
    'Blocked: no create screen is routed for this entity.';
const REASON_NO_AGENT_DETAIL =
    'Blocked: no agent detail screen is routed on this deployment.';
const REASON_NO_DUPLICATE_API =
    'Blocked: no agent duplicate route is mounted.';

// Only the two entity types that have both a mounted screen and a mounted
// API. Tenant, feature-flag and rate-limit configs were declared here with
// no reader (no view mounts them) and no matching /aaas/admin route — a
// setting with no reader is a lie, so they are gone.
// Column keys are the field names the server actually returns (TenantUserOut,
// AgentSchema) — never invented aliases.
const ENTITY_CONFIGS: Record<string, EntityConfig> = {
    user: {
        displayName: 'User',
        displayNamePlural: 'Users',
        icon: 'person',
        // TenantUserOut (admin/aaas/api/users.py:35-45): id, email, name,
        // role, is_active, tenant_id, created_at, last_login_at.
        defaultColumns: [
            { key: 'email', label: 'Email', sortable: true },
            { key: 'name', label: 'Name', sortable: true },
            { key: 'role', label: 'Role', sortable: true },
            { key: 'is_active', label: 'Active', sortable: true, align: 'center' },
            { key: 'last_login_at', label: 'Last Login', sortable: true },
        ],
        statusField: 'is_active',
        statusOptions: [
            { value: '', label: 'All Status' },
            { value: 'true', label: 'Active' },
            { value: 'false', label: 'Inactive' },
        ],
        actions: [
            { id: 'view', label: 'View', icon: 'visibility', permission: 'org:user_read' },
            { id: 'edit', label: 'Edit', icon: 'edit', permission: 'org:user_update', disabledReason: REASON_NO_EDIT_SCREEN },
            { id: 'reset_password', label: 'Reset Password', icon: 'key', permission: 'org:user_update', disabledReason: REASON_NO_PASSWORD_RESET },
            { id: 'suspend', label: 'Suspend', icon: 'pause_circle', permission: 'org:user_update', variant: 'danger' },
            { id: 'delete', label: 'Delete', icon: 'delete', permission: 'org:user_delete', variant: 'danger', requiresConfirm: true },
        ],
    },
    agent: {
        displayName: 'Agent',
        displayNamePlural: 'Agents',
        icon: 'smart_toy',
        // AgentSchema (admin/aaas/api/tenant_agents.py:35-48): id, name, slug,
        // status, tenant_id, chat_model, memory_enabled, voice_enabled,
        // created_at, conversations, tokens_used. No message_count exists.
        defaultColumns: [
            { key: 'name', label: 'Name', sortable: true },
            { key: 'chat_model', label: 'Chat Model', sortable: true },
            { key: 'status', label: 'Status', sortable: true },
            { key: 'created_at', label: 'Created', sortable: true },
        ],
        statusField: 'status',
        statusOptions: [
            { value: '', label: 'All Status' },
            { value: 'active', label: 'Active' },
        ],
        actions: [
            { id: 'view', label: 'View', icon: 'visibility', permission: 'agent:read', disabledReason: REASON_NO_AGENT_DETAIL },
            { id: 'edit', label: 'Edit', icon: 'edit', permission: 'agent:update', disabledReason: REASON_NO_EDIT_SCREEN },
            { id: 'duplicate', label: 'Duplicate', icon: 'content_copy', permission: 'agent:create', disabledReason: REASON_NO_DUPLICATE_API },
            { id: 'delete', label: 'Delete', icon: 'delete', permission: 'agent:delete', variant: 'danger', requiresConfirm: true },
        ],
    },
};

@customElement('entity-manager')
export class EntityManager extends LitElement {
    static styles = css`
    :host {
      display: block;
    }

    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .title {
      font-size: 22px;
      font-weight: 600;
      margin: 0;
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .title-icon {
      width: 40px;
      height: 40px;
      background: var(--soma-bg-hover, #fafafa);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .material-symbols-outlined {
      font-family: 'Material Symbols Outlined';
      font-weight: normal;
      font-style: normal;
      font-size: 20px;
      line-height: 1;
      display: inline-block;
      -webkit-font-smoothing: antialiased;
    }

    .count {
      font-size: 14px;
      color: var(--soma-text-muted, #999);
      font-weight: 400;
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
      border: 1px solid var(--soma-border-light, #e0e0e0);
      background: var(--soma-bg-card, #ffffff);
      color: var(--soma-text-primary, #1a1a1a);
    }

    .btn:hover {
      background: var(--soma-bg-hover, #fafafa);
    }

    .btn.primary {
      background: #1a1a1a;
      color: white;
      border-color: #1a1a1a;
    }

    .btn.primary:hover {
      background: #333;
    }

    .btn .material-symbols-outlined {
      font-size: 16px;
    }

    .btn:disabled {
      opacity: 0.55;
      cursor: not-allowed;
    }

    .btn-reason {
      font-size: 11px;
      font-weight: 400;
      opacity: 0.85;
      max-width: 220px;
      text-align: left;
      line-height: 1.3;
    }

    /* Search/Filter Bar */
    .filter-bar {
      display: flex;
      gap: 12px;
      margin-bottom: 20px;
    }

    .search-input {
      flex: 1;
      max-width: 300px;
      padding: 10px 14px;
      border: 1px solid var(--soma-border-light, #e0e0e0);
      border-radius: 8px;
      font-size: 14px;
      outline: none;
      transition: border-color 0.15s ease;
    }

    .search-input:focus {
      border-color: #1a1a1a;
    }

    .filter-select {
      padding: 10px 14px;
      border: 1px solid var(--soma-border-light, #e0e0e0);
      border-radius: 8px;
      font-size: 13px;
      background: var(--soma-bg-card, #ffffff);
      cursor: pointer;
    }

    /* Loading State */
    .loading {
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 60px;
      color: var(--soma-text-muted, #999);
    }

    .spinner {
      animation: spin 1s linear infinite;
    }

    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }

    /* Action Column */
    .action-cell {
      display: flex;
      justify-content: flex-end;
    }
  `;

    // Required properties
    @property({ type: String }) entity = 'tenant';
    @property({ type: String, attribute: 'api-base' }) apiBase = '/api/v2';
    @property({ type: Array }) columns: TableColumn[] = [];
    @property({ type: Array }) permissions: string[] = [];

    // State
    @state() private data: Record<string, unknown>[] = [];
    @state() private loading = true;
    @state() private error: string | null = null;
    @state() private searchQuery = '';
    @state() private selectedStatus = '';

    connectedCallback() {
        super.connectedCallback();
        this.fetchData();
    }

    private get config(): EntityConfig {
        const cfg = ENTITY_CONFIGS[this.entity];
        if (!cfg) {
            // Refuse rather than fall back to another entity's config.
            throw new Error(`entity-manager: unknown entity "${this.entity}"`);
        }
        return cfg;
    }

    private get effectiveColumns(): TableColumn[] {
        const cols = this.columns.length > 0 ? this.columns : this.config.defaultColumns;

        // Add action column if user has any action permissions
        const anyActions = this.config.actions.some(action => this.hasPermission(action.permission));
        if (anyActions) {
            return [
                ...cols,
                {
                    key: '_actions',
                    label: '',
                    width: '60px',
                    align: 'right',
                    render: (_value, row) => html`
            <div class="action-cell">
              <soma-action-menu
                .actions=${this.getAvailableActions(row)}
                @soma-action=${(e: CustomEvent) => this.handleAction(e.detail.action, row)}
              ></soma-action-menu>
            </div>
          `,
                },
            ];
        }
        return cols;
    }

    private getAvailableActions(row: Record<string, unknown>): ActionItem[] {
        return this.config.actions
            .filter(action => this.hasPermission(action.permission))
            .map(action => {
                let label = action.label;
                // Suspend toggles: the row's real state decides the verb.
                if (action.id === 'suspend' && this.entity === 'user' && !action.disabledReason) {
                    label = row.is_active === true ? 'Suspend' : 'Unsuspend';
                }
                return {
                    id: action.id,
                    label,
                    icon: action.icon,
                    variant: action.variant,
                    disabled: action.disabledReason !== undefined && action.disabledReason !== '',
                    disabledReason: action.disabledReason,
                };
            });
    }

    private hasPermission(perm: string): boolean {
        // Exact match only. The previous version also accepted `*` and
        // `<entity>:*`, which is a client-side bypass: one wildcard in the
        // permission list unlocked every control on the screen regardless of
        // what the server decided. The catalog has no wildcard and neither
        // does this.
        return this.permissions.includes(perm);
    }

    private apiPath(suffix: string): string {
        const base = this.apiBase.replace(/^\/api\/v2/, '');
        return `${base}/${suffix}`;
    }

    async fetchData() {
        this.loading = true;
        this.error = null;
        try {
            const json = await apiClient.get<Record<string, unknown>[] | { items?: Record<string, unknown>[]; data?: Record<string, unknown>[] }>(this.apiPath(`${this.entity}s`));
            // Handle both array and { items: [...] } responses
            this.data = Array.isArray(json) ? json : (json.items || json.data || []);
        } catch (err) {
            // Failure is not "no rows". Keep the previous rows and surface
            // the failure — never render an empty table as if it were data.
            console.error(`Failed to fetch ${this.entity}s:`, err);
            this.error = `Failed to load ${this.config.displayNamePlural.toLowerCase()}. The request did not succeed.`;
        } finally {
            this.loading = false;
        }
    }

    private get filteredData(): Record<string, unknown>[] {
        let result = this.data;

        // Search filter
        if (this.searchQuery) {
            const q = this.searchQuery.toLowerCase();
            result = result.filter(item =>
                Object.values(item).some(v =>
                    String(v).toLowerCase().includes(q)
                )
            );
        }

        // Status filter on the field the server actually sends.
        if (this.selectedStatus) {
            const field = this.config.statusField;
            result = result.filter(item => {
                const raw = item[field];
                if (field === 'is_active') {
                    return String(raw === true) === this.selectedStatus;
                }
                return String(raw) === this.selectedStatus;
            });
        }

        return result;
    }

    private handleAction(actionId: string, row: Record<string, unknown>) {
        const action = this.config.actions.find(a => a.id === actionId);
        if (!action || action.disabledReason) {
            // A disabled control never acts. Its reason is already printed.
            return;
        }

        if (action.requiresConfirm) {
            if (!confirm(`Are you sure you want to ${action.label.toLowerCase()} this ${this.config.displayName}?`)) {
                return;
            }
        }

        // Every action is handled here. There is no external action-event
        // listener anywhere in the app — dispatching one was a dead control.
        switch (actionId) {
            case 'view':
                this.navigateToView(row);
                break;
            case 'suspend':
                if (this.entity === 'user') {
                    void this.toggleUserSuspended(row);
                }
                break;
            case 'delete':
                void this.deleteEntity(row.id as string);
                break;
        }
    }

    /** Real routed screens only. A route that is called and does not exist is
     *  a lie: /admin/users/{id} is the only entity detail branch in main.ts. */
    private navigateToView(row: Record<string, unknown>) {
        if (this.entity === 'user') {
            window.dispatchEvent(new CustomEvent('soma-navigate', {
                detail: { route: `/admin/users/${row.id}` }
            }));
        }
    }

    private async toggleUserSuspended(row: Record<string, unknown>) {
        const id = row.id as string;
        const active = row.is_active === true;
        // POST /aaas/admin/users/{id}/suspend and /unsuspend
        // (admin/aaas/api/users.py:418-461). One verb per real endpoint.
        const verb = active ? 'suspend' : 'unsuspend';
        try {
            await apiClient.post(this.apiPath(`users/${id}/${verb}`), {});
            await this.fetchData();
        } catch (err) {
            console.error(`Failed to ${verb} user:`, err);
        }
    }

    private async deleteEntity(id: string) {
        try {
            await apiClient.delete(this.apiPath(`${this.entity}s/${id}`));
            this.data = this.data.filter(item => item.id !== id);
        } catch (err) {
            console.error(`Failed to delete ${this.entity}:`, err);
        }
    }

    render() {
        return html`
      <div class="header">
        <div class="header-left">
          <h1 class="title">
            <span class="title-icon">
              <span class="material-symbols-outlined">${this.config.icon}</span>
            </span>
            ${this.config.displayNamePlural}
            <span class="count">(${this.data.length})</span>
          </h1>
        </div>
        <div class="header-actions">
          <button class="btn" @click=${() => this.fetchData()}>
            <span class="material-symbols-outlined ${this.loading ? 'spinner' : ''}">refresh</span>
            Refresh
          </button>
          ${this.hasPermission(`${this.entity}:create`) ? html`
            <button class="btn primary" disabled
              title=${REASON_NO_CREATE_SCREEN}
              data-control="create-${this.entity}">
              <span class="material-symbols-outlined">add</span>
              Create ${this.config.displayName}
              <span class="btn-reason">${REASON_NO_CREATE_SCREEN}</span>
            </button>
          ` : nothing}
        </div>
      </div>

      <div class="filter-bar">
        <input
          type="text"
          class="search-input"
          placeholder="Search ${this.config.displayNamePlural.toLowerCase()}..."
          .value=${this.searchQuery}
          @input=${(e: InputEvent) => this.searchQuery = (e.target as HTMLInputElement).value}
        />
        <select
          class="filter-select"
          .value=${this.selectedStatus}
          @change=${(e: Event) => this.selectedStatus = (e.target as HTMLSelectElement).value}
        >
          ${this.config.statusOptions.map(opt => html`
            <option value=${opt.value}>${opt.label}</option>
          `)}
        </select>
      </div>

      ${this.loading ? html`
        <div class="loading">
          <span class="material-symbols-outlined spinner">autorenew</span>
          Loading ${this.config.displayNamePlural.toLowerCase()}...
        </div>
      ` : this.error ? html`
        <div class="loading" data-control="entity-error">
          <span class="material-symbols-outlined">error</span>
          &nbsp;${this.error}
        </div>
      ` : html`
        <soma-data-table
          .columns=${this.effectiveColumns}
          .data=${this.filteredData}
          clickable
          empty-message="No ${this.config.displayNamePlural.toLowerCase()} found"
          @soma-row-click=${(e: CustomEvent) => this.handleAction('view', e.detail.row)}
        ></soma-data-table>
      `}
    `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'entity-manager': EntityManager;
    }
}
