/**
 * Entity Manager Component
 * Generic CRUD interface for any entity type
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Permission-aware action filtering
 * - Composes saas-data-table and saas-action-menu
 * - Light theme, minimal, professional
 * - Material Symbols icons
 * 
 * Usage:
 * <entity-manager
 *   entity="tenant"
 *   api-base="/api/v2/aaas"
 *   .columns=${tenantColumns}
 *   .permissions=${userPermissions}
 * />
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import type { TableColumn } from './saas-data-table.js';
import type { ActionItem } from './saas-action-menu.js';
import './saas-data-table.js';
import './saas-action-menu.js';

// Entity configuration for different entity types
interface EntityConfig {
    displayName: string;
    displayNamePlural: string;
    icon: string;
    defaultColumns: TableColumn[];
    actions: ActionDef[];
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
}

// Actions are declared per entity below with the exact catalog permission
// that authorizes them. There is no shared default list: the same verb on two
// entities is two different permissions (`org:update` is not `agent:update`),
// and a shared template is how the old `tenant:edit` style names appeared.
const DEFAULT_ACTIONS: ActionDef[] = [];

// Entity-specific configurations
const ENTITY_CONFIGS: Record<string, EntityConfig> = {
    tenant: {
        displayName: 'Tenant',
        displayNamePlural: 'Tenants',
        icon: 'apartment',
        defaultColumns: [
            { key: 'name', label: 'Name', sortable: true },
            { key: 'slug', label: 'Slug', sortable: true },
            { key: 'tier_name', label: 'Tier', sortable: true },
            { key: 'user_count', label: 'Users', sortable: true, align: 'center' },
            { key: 'status', label: 'Status', sortable: true },
            { key: 'created_at', label: 'Created', sortable: true },
        ],
        actions: [
            { id: 'view', label: 'View', icon: 'visibility', permission: 'org:read' },
            { id: 'edit', label: 'Edit', icon: 'edit', permission: 'org:update' },
            { id: 'suspend', label: 'Suspend', icon: 'pause_circle', permission: 'org:manage', variant: 'danger' },
            { id: 'delete', label: 'Delete', icon: 'delete', permission: 'system:configure', variant: 'danger', requiresConfirm: true },
            // Impersonation is gone. Acting as another subject is authority
            // none of the eight roles grants, so a control for it can never be
            // authorized by the catalog. A button that can never be correctly
            // gated is not a feature, it is a trap.
        ],
    },
    user: {
        displayName: 'User',
        displayNamePlural: 'Users',
        icon: 'person',
        defaultColumns: [
            { key: 'email', label: 'Email', sortable: true },
            { key: 'name', label: 'Name', sortable: true },
            { key: 'role', label: 'Role', sortable: true },
            { key: 'status', label: 'Status', sortable: true },
            { key: 'last_login', label: 'Last Login', sortable: true },
        ],
        actions: [
            { id: 'view', label: 'View', icon: 'visibility', permission: 'org:user_read' },
            { id: 'edit', label: 'Edit', icon: 'edit', permission: 'org:user_update' },
            { id: 'reset_password', label: 'Reset Password', icon: 'key', permission: 'org:user_update' },
            { id: 'suspend', label: 'Suspend', icon: 'pause_circle', permission: 'org:user_update', variant: 'danger' },
            { id: 'delete', label: 'Delete', icon: 'delete', permission: 'org:user_delete', variant: 'danger', requiresConfirm: true },
        ],
    },
    agent: {
        displayName: 'Agent',
        displayNamePlural: 'Agents',
        icon: 'smart_toy',
        defaultColumns: [
            { key: 'name', label: 'Name', sortable: true },
            { key: 'model', label: 'Model', sortable: true },
            { key: 'status', label: 'Status', sortable: true },
            { key: 'message_count', label: 'Messages', sortable: true, align: 'center' },
            { key: 'created_at', label: 'Created', sortable: true },
        ],
        actions: [
            { id: 'view', label: 'View', icon: 'visibility', permission: 'agent:read' },
            { id: 'edit', label: 'Edit', icon: 'edit', permission: 'agent:update' },
            { id: 'duplicate', label: 'Duplicate', icon: 'content_copy', permission: 'agent:create' },
            { id: 'delete', label: 'Delete', icon: 'delete', permission: 'agent:delete', variant: 'danger', requiresConfirm: true },
        ],
    },
    feature: {
        displayName: 'Feature',
        displayNamePlural: 'Features',
        icon: 'extension',
        defaultColumns: [
            { key: 'name', label: 'Name', sortable: true },
            { key: 'code', label: 'Code', sortable: true },
            { key: 'category', label: 'Category', sortable: true },
            { key: 'is_active', label: 'Active', sortable: true, align: 'center' },
        ],
        actions: [
            { id: 'view', label: 'View', icon: 'visibility', permission: 'system:configure' },
            { id: 'edit', label: 'Edit', icon: 'edit', permission: 'system:configure' },
            { id: 'toggle', label: 'Toggle', icon: 'toggle_on', permission: 'system:configure' },
        ],
    },
    ratelimit: {
        displayName: 'Rate Limit',
        displayNamePlural: 'Rate Limits',
        icon: 'speed',
        defaultColumns: [
            { key: 'key', label: 'Key', sortable: true },
            { key: 'limit', label: 'Limit', sortable: true, align: 'right' },
            { key: 'window_display', label: 'Window', sortable: true },
            { key: 'policy', label: 'Policy', sortable: true },
            { key: 'is_active', label: 'Active', sortable: true, align: 'center' },
        ],
        actions: [
            { id: 'view', label: 'View', icon: 'visibility', permission: 'system:ratelimit' },
            { id: 'edit', label: 'Edit', icon: 'edit', permission: 'system:ratelimit' },
            { id: 'delete', label: 'Delete', icon: 'delete', permission: 'system:ratelimit', variant: 'danger' },
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
      background: var(--saas-bg-hover, #fafafa);
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
      color: var(--saas-text-muted, #999);
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
      border: 1px solid var(--saas-border-light, #e0e0e0);
      background: var(--saas-bg-card, #ffffff);
      color: var(--saas-text-primary, #1a1a1a);
    }

    .btn:hover {
      background: var(--saas-bg-hover, #fafafa);
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
      border: 1px solid var(--saas-border-light, #e0e0e0);
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
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 8px;
      font-size: 13px;
      background: var(--saas-bg-card, #ffffff);
      cursor: pointer;
    }

    /* Loading State */
    .loading {
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 60px;
      color: var(--saas-text-muted, #999);
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
    @state() private searchQuery = '';
    @state() private selectedStatus = '';

    connectedCallback() {
        super.connectedCallback();
        this.fetchData();
    }

    private get config(): EntityConfig {
        return ENTITY_CONFIGS[this.entity] || ENTITY_CONFIGS.tenant;
    }

    private get effectiveColumns(): TableColumn[] {
        const cols = this.columns.length > 0 ? this.columns : this.config.defaultColumns;

        // Add action column if user has any action permissions
        const availableActions = this.getAvailableActions();
        if (availableActions.length > 0) {
            return [
                ...cols,
                {
                    key: '_actions',
                    label: '',
                    width: '60px',
                    align: 'right',
                    render: (_value, row) => html`
            <div class="action-cell">
              <saas-action-menu
                .actions=${availableActions}
                @saas-action=${(e: CustomEvent) => this.handleAction(e.detail.action, row)}
              ></saas-action-menu>
            </div>
          `,
                },
            ];
        }
        return cols;
    }

    private getAvailableActions(): ActionItem[] {
        return this.config.actions
            .filter(action => this.hasPermission(action.permission))
            .map(action => ({
                id: action.id,
                label: action.label,
                icon: action.icon,
                variant: action.variant,
            }));
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
        try {
            const json = await apiClient.get<Record<string, unknown>[] | { items?: Record<string, unknown>[]; data?: Record<string, unknown>[] }>(this.apiPath(`${this.entity}s`));
            // Handle both array and { items: [...] } responses
            this.data = Array.isArray(json) ? json : (json.items || json.data || []);
        } catch (err) {
            console.error(`Failed to fetch ${this.entity}s:`, err);
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

        // Status filter
        if (this.selectedStatus) {
            result = result.filter(item => item.status === this.selectedStatus);
        }

        return result;
    }

    private handleAction(actionId: string, row: Record<string, unknown>) {
        const action = this.config.actions.find(a => a.id === actionId);

        if (action?.requiresConfirm) {
            if (!confirm(`Are you sure you want to ${action.label.toLowerCase()} this ${this.config.displayName}?`)) {
                return;
            }
        }

        this.dispatchEvent(new CustomEvent('entity-action', {
            bubbles: true,
            composed: true,
            detail: { action: actionId, entity: this.entity, row, id: row.id },
        }));

        // Handle common actions
        switch (actionId) {
            case 'view':
                this.navigateTo(`${this.entity}s/${row.id}`);
                break;
            case 'edit':
                this.navigateTo(`${this.entity}s/${row.id}/edit`);
                break;
            case 'delete':
                this.deleteEntity(row.id as string);
                break;
        }
    }

    private navigateTo(path: string) {
        window.dispatchEvent(new CustomEvent('saas-navigate', {
            detail: { route: `/${path}` }
        }));
    }

    private async deleteEntity(id: string) {
        try {
            await apiClient.delete(this.apiPath(`${this.entity}s/${id}`));
            this.data = this.data.filter(item => item.id !== id);
        } catch (err) {
            console.error(`Failed to delete ${this.entity}:`, err);
        }
    }

    private openCreate() {
        this.navigateTo(`${this.entity}s/new`);
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
            <button class="btn primary" @click=${() => this.openCreate()}>
              <span class="material-symbols-outlined">add</span>
              Create ${this.config.displayName}
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
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
          <option value="pending">Pending</option>
        </select>
      </div>

      ${this.loading ? html`
        <div class="loading">
          <span class="material-symbols-outlined spinner">autorenew</span>
          Loading ${this.config.displayNamePlural.toLowerCase()}...
        </div>
      ` : html`
        <saas-data-table
          .columns=${this.effectiveColumns}
          .data=${this.filteredData}
          clickable
          empty-message="No ${this.config.displayNamePlural.toLowerCase()} found"
          @saas-row-click=${(e: CustomEvent) => this.handleAction('view', e.detail.row)}
        ></saas-data-table>
      `}
    `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'entity-manager': EntityManager;
    }
}
