/**
 * Eye of God Tenants Management (God Mode)
 * Per SAAS_PLATFORM_SRS Section 4.2
 *
 * VIBE COMPLIANT:
 * - Real API calls to /saas/tenants
 * - Real Lago integration for billing
 * - No mocked data
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import { lagoService } from '../services/lago-service.js';
import '../components/soma-modal.js';
import '../components/soma-input.js';
import '../components/soma-select.js';
import '../components/soma-button.js';

// ========== TYPES ==========

interface Tenant {
    id: string;
    name: string;
    slug: string;
    owner_email: string;
    subscription_tier: string;
    status: 'active' | 'suspended' | 'pending';
    agent_count: number;
    agent_limit: number;
    user_count: number;
    user_limit: number;
    storage_used_bytes: number;
    storage_limit_bytes: number;
    created_at: string;
    suspended_at?: string;
}

interface CreateTenantRequest {
    name: string;
    slug: string;
    owner_email: string;
    subscription_tier: string;
}

// ========== COMPONENT ==========

@customElement('soma-tenants')
export class SomaTenants extends LitElement {
    static styles = css`
        :host {
            display: block;
            padding: var(--soma-spacing-lg, 24px);
            height: 100%;
            overflow-y: auto;
        }

        .page-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--soma-spacing-lg, 24px);
        }

        .header-left h1 {
            font-size: var(--soma-text-2xl, 24px);
            font-weight: 600;
            margin: 0 0 4px 0;
        }

        .header-left p {
            font-size: var(--soma-text-sm, 13px);
            color: var(--soma-text-dim, #64748b);
            margin: 0;
        }

        .header-actions {
            display: flex;
            gap: var(--soma-spacing-sm, 8px);
        }

        .toolbar {
            display: flex;
            gap: var(--soma-spacing-md, 16px);
            margin-bottom: var(--soma-spacing-lg, 24px);
            flex-wrap: wrap;
        }

        .search-input {
            flex: 1;
            min-width: 200px;
            max-width: 300px;
        }

        .filter-group {
            display: flex;
            gap: var(--soma-spacing-xs, 4px);
        }

        .filter-btn {
            padding: var(--soma-spacing-sm, 8px) var(--soma-spacing-md, 16px);
            background: transparent;
            border: 1px solid var(--soma-border-color, rgba(255, 255, 255, 0.1));
            border-radius: var(--soma-radius-md, 8px);
            color: var(--soma-text-dim, #64748b);
            font-size: var(--soma-text-sm, 13px);
            cursor: pointer;
            transition: all 0.2s;
        }

        .filter-btn:hover {
            border-color: var(--soma-accent, #94a3b8);
            color: var(--soma-text-main, #e2e8f0);
        }

        .filter-btn.active {
            background: var(--soma-accent, #94a3b8);
            color: var(--soma-bg, #0f172a);
            border-color: var(--soma-accent, #94a3b8);
        }

        .tenants-table {
            background: var(--soma-surface, rgba(30, 41, 59, 0.85));
            backdrop-filter: blur(20px);
            border: 1px solid var(--soma-border-color, rgba(255, 255, 255, 0.05));
            border-radius: var(--soma-radius-lg, 16px);
            overflow: hidden;
        }

        .table-header {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr 1fr 1fr 120px;
            gap: var(--soma-spacing-md, 16px);
            padding: var(--soma-spacing-md, 16px) var(--soma-spacing-lg, 24px);
            background: var(--soma-surface-elevated, rgba(51, 65, 85, 0.9));
            font-size: var(--soma-text-xs, 11px);
            font-weight: 600;
            color: var(--soma-text-dim, #64748b);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .table-row {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr 1fr 1fr 120px;
            gap: var(--soma-spacing-md, 16px);
            padding: var(--soma-spacing-md, 16px) var(--soma-spacing-lg, 24px);
            align-items: center;
            border-bottom: 1px solid var(--soma-border-color, rgba(255, 255, 255, 0.05));
            transition: background 0.2s;
        }

        .table-row:hover {
            background: var(--soma-surface-elevated, rgba(51, 65, 85, 0.5));
        }

        .table-row:last-child {
            border-bottom: none;
        }

        .tenant-cell {
            display: flex;
            align-items: center;
            gap: var(--soma-spacing-sm, 8px);
        }

        .tenant-avatar {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: var(--soma-radius-md, 8px);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: var(--soma-text-sm, 13px);
            font-weight: 600;
            color: white;
            flex-shrink: 0;
        }

        .tenant-details {
            min-width: 0;
        }

        .tenant-name {
            font-size: var(--soma-text-sm, 13px);
            font-weight: 500;
            color: var(--soma-text-main, #e2e8f0);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .tenant-email {
            font-size: var(--soma-text-xs, 11px);
            color: var(--soma-text-dim, #64748b);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .tier-badge {
            display: inline-block;
            padding: 4px 8px;
            background: var(--soma-surface-elevated, rgba(51, 65, 85, 0.9));
            border-radius: var(--soma-radius-sm, 4px);
            font-size: var(--soma-text-xs, 11px);
            font-weight: 500;
            color: var(--soma-text-main, #e2e8f0);
        }

        .tier-badge.enterprise {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .usage-text {
            font-size: var(--soma-text-sm, 13px);
            color: var(--soma-text-main, #e2e8f0);
        }

        .usage-limit {
            font-size: var(--soma-text-xs, 11px);
            color: var(--soma-text-dim, #64748b);
        }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: var(--soma-text-sm, 13px);
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }

        .status-dot.active {
            background: var(--soma-success, #22c55e);
        }

        .status-dot.suspended {
            background: var(--soma-danger, #ef4444);
        }

        .status-dot.pending {
            background: var(--soma-warning, #f59e0b);
        }

        .actions-cell {
            display: flex;
            gap: var(--soma-spacing-xs, 4px);
        }

        .action-btn {
            width: 32px;
            height: 32px;
            background: transparent;
            border: 1px solid var(--soma-border-color, rgba(255, 255, 255, 0.1));
            border-radius: var(--soma-radius-sm, 4px);
            color: var(--soma-text-dim, #64748b);
            font-size: 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }

        .action-btn:hover {
            background: var(--soma-surface-elevated, rgba(51, 65, 85, 0.9));
            color: var(--soma-text-main, #e2e8f0);
        }

        .loading, .empty-state, .error {
            padding: var(--soma-spacing-xl, 32px);
            text-align: center;
        }

        .empty-state {
            color: var(--soma-text-dim, #64748b);
        }

        .error {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid var(--soma-danger, #ef4444);
            border-radius: var(--soma-radius-md, 8px);
            color: var(--soma-danger, #ef4444);
        }

        .form-grid {
            display: grid;
            gap: var(--soma-spacing-md, 16px);
        }
    `;

    @state() private _tenants: Tenant[] = [];
    @state() private _filteredTenants: Tenant[] = [];
    @state() private _isLoading = true;
    @state() private _error: string | null = null;
    @state() private _filter: 'all' | 'active' | 'suspended' = 'all';
    @state() private _searchQuery = '';
    @state() private _showCreateModal = false;
    @state() private _createForm: CreateTenantRequest = {
        name: '',
        slug: '',
        owner_email: '',
        subscription_tier: 'free'
    };

    connectedCallback() {
        super.connectedCallback();
        this._loadTenants();
    }

    render() {
        return html`
            <div class="page-header">
                <div class="header-left">
                    <h1>Tenants Management</h1>
                    <p>${this._tenants.length} tenants registered</p>
                </div>
                <div class="header-actions">
                    <soma-button @click=${() => this._showCreateModal = true}>
                        + Create Tenant
                    </soma-button>
                </div>
            </div>

            <div class="toolbar">
                <soma-input
                    class="search-input"
                    placeholder="Search tenants..."
                    .value=${this._searchQuery}
                    @soma-input=${(e: CustomEvent) => this._handleSearch(e.detail.value)}
                ></soma-input>

                <div class="filter-group">
                    <button 
                        class="filter-btn ${this._filter === 'all' ? 'active' : ''}"
                        @click=${() => this._setFilter('all')}
                    >All</button>
                    <button 
                        class="filter-btn ${this._filter === 'active' ? 'active' : ''}"
                        @click=${() => this._setFilter('active')}
                    >Active</button>
                    <button 
                        class="filter-btn ${this._filter === 'suspended' ? 'active' : ''}"
                        @click=${() => this._setFilter('suspended')}
                    >Suspended</button>
                </div>
            </div>

            ${this._error ? html`
                <div class="error">${this._error}</div>
            ` : ''}

            <div class="tenants-table">
                <div class="table-header">
                    <div>Tenant</div>
                    <div>Plan</div>
                    <div>Agents</div>
                    <div>Users</div>
                    <div>Status</div>
                    <div>Actions</div>
                </div>

                ${this._isLoading ? html`
                    <div class="loading">Loading tenants...</div>
                ` : this._filteredTenants.length === 0 ? html`
                    <div class="empty-state">No tenants found</div>
                ` : this._filteredTenants.map(tenant => this._renderTenantRow(tenant))}
            </div>

            ${this._showCreateModal ? this._renderCreateModal() : ''}
        `;
    }

    private _renderTenantRow(tenant: Tenant) {
        return html`
            <div class="table-row">
                <div class="tenant-cell">
                    <div class="tenant-avatar">${this._getInitials(tenant.name)}</div>
                    <div class="tenant-details">
                        <div class="tenant-name">${tenant.name}</div>
                        <div class="tenant-email">${tenant.owner_email}</div>
                    </div>
                </div>
                <div>
                    <span class="tier-badge ${tenant.subscription_tier}">${tenant.subscription_tier}</span>
                </div>
                <div>
                    <div class="usage-text">${tenant.agent_count}</div>
                    <div class="usage-limit">/ ${tenant.agent_limit === -1 ? '∞' : tenant.agent_limit}</div>
                </div>
                <div>
                    <div class="usage-text">${tenant.user_count}</div>
                    <div class="usage-limit">/ ${tenant.user_limit === -1 ? '∞' : tenant.user_limit}</div>
                </div>
                <div>
                    <span class="status-badge">
                        <span class="status-dot ${tenant.status}"></span>
                        ${tenant.status}
                    </span>
                </div>
                <div class="actions-cell">
                    <button class="action-btn" title="Enter Tenant" @click=${() => this._enterTenant(tenant.id)}>
                        🚪
                    </button>
                    <button class="action-btn" title="Edit" @click=${() => this._editTenant(tenant)}>
                        ✏️
                    </button>
                    <button class="action-btn" title="${tenant.status === 'active' ? 'Suspend' : 'Activate'}" 
                        @click=${() => this._toggleTenantStatus(tenant)}>
                        ${tenant.status === 'active' ? '⏸️' : '▶️'}
                    </button>
                </div>
            </div>
        `;
    }

    private _renderCreateModal() {
        return html`
            <soma-modal 
                title="Create New Tenant" 
                @close=${() => this._showCreateModal = false}
            >
                <div class="form-grid">
                    <soma-input
                        label="Organization Name"
                        placeholder="Enter organization name"
                        .value=${this._createForm.name}
                        @soma-input=${(e: CustomEvent) => this._createForm = { ...this._createForm, name: e.detail.value }}
                        required
                    ></soma-input>

                    <soma-input
                        label="Slug (URL identifier)"
                        placeholder="organization-slug"
                        .value=${this._createForm.slug}
                        @soma-input=${(e: CustomEvent) => this._createForm = { ...this._createForm, slug: e.detail.value }}
                        required
                    ></soma-input>

                    <soma-input
                        label="Owner Email"
                        type="email"
                        placeholder="owner@example.com"
                        .value=${this._createForm.owner_email}
                        @soma-input=${(e: CustomEvent) => this._createForm = { ...this._createForm, owner_email: e.detail.value }}
                        required
                    ></soma-input>

                    <soma-select
                        label="Subscription Tier"
                        .value=${this._createForm.subscription_tier}
                        .options=${[
                { value: 'free', label: 'Free' },
                { value: 'starter', label: 'Starter - $49/mo' },
                { value: 'team', label: 'Team - $199/mo' },
                { value: 'enterprise', label: 'Enterprise - Custom' }
            ]}
                        @soma-change=${(e: CustomEvent) => this._createForm = { ...this._createForm, subscription_tier: e.detail.value }}
                    ></soma-select>
                </div>

                <div slot="footer">
                    <soma-button variant="secondary" @click=${() => this._showCreateModal = false}>
                        Cancel
                    </soma-button>
                    <soma-button @click=${this._createTenant}>
                        Create Tenant
                    </soma-button>
                </div>
            </soma-modal>
        `;
    }

    // ========== DATA OPERATIONS ==========

    private async _loadTenants() {
        this._isLoading = true;
        this._error = null;

        try {
            const response = await apiClient.get<{ tenants: Tenant[] }>('/saas/tenants');
            this._tenants = response.tenants;
            this._applyFilters();
        } catch (error) {
            this._error = error instanceof Error ? error.message : 'Failed to load tenants';
        } finally {
            this._isLoading = false;
        }
    }

    private async _createTenant() {
        try {
            // Create tenant in our system
            const tenant = await apiClient.post<Tenant>('/saas/tenants', this._createForm);

            // Create corresponding customer in Lago
            await lagoService.createCustomer({
                external_id: tenant.id,
                name: tenant.name,
                email: this._createForm.owner_email
            });

            // Create subscription in Lago
            await lagoService.createSubscription({
                external_customer_id: tenant.id,
                plan_code: this._createForm.subscription_tier,
                external_id: `sub_${tenant.id}`
            });

            this._showCreateModal = false;
            this._createForm = { name: '', slug: '', owner_email: '', subscription_tier: 'free' };
            await this._loadTenants();

        } catch (error) {
            this._error = error instanceof Error ? error.message : 'Failed to create tenant';
        }
    }

    private async _toggleTenantStatus(tenant: Tenant) {
        try {
            const action = tenant.status === 'active' ? 'suspend' : 'activate';
            await apiClient.post(`/saas/tenants/${tenant.id}/${action}`, {});
            await this._loadTenants();
        } catch (error) {
            this._error = error instanceof Error ? error.message : 'Failed to update tenant status';
        }
    }

    private _enterTenant(tenantId: string) {
        this.dispatchEvent(new CustomEvent('enter-tenant', {
            bubbles: true,
            composed: true,
            detail: { tenantId }
        }));
    }

    private _editTenant(tenant: Tenant) {
        // TODO: Open edit modal
        console.log('Edit tenant:', tenant);
    }

    // ========== FILTERING ==========

    private _handleSearch(query: string) {
        this._searchQuery = query;
        this._applyFilters();
    }

    private _setFilter(filter: 'all' | 'active' | 'suspended') {
        this._filter = filter;
        this._applyFilters();
    }

    private _applyFilters() {
        let filtered = [...this._tenants];

        // Apply status filter
        if (this._filter !== 'all') {
            filtered = filtered.filter(t => t.status === this._filter);
        }

        // Apply search
        if (this._searchQuery) {
            const query = this._searchQuery.toLowerCase();
            filtered = filtered.filter(t =>
                t.name.toLowerCase().includes(query) ||
                t.owner_email.toLowerCase().includes(query) ||
                t.slug.toLowerCase().includes(query)
            );
        }

        this._filteredTenants = filtered;
    }

    // ========== HELPERS ==========

    private _getInitials(name: string): string {
        return name
            .split(' ')
            .map(word => word[0])
            .join('')
            .toUpperCase()
            .slice(0, 2);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-tenants': SomaTenants;
    }
}
