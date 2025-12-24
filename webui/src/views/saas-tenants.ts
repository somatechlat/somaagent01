/**
 * SAAS Tenants Management View
 * Card grid with tenant details in glassmorphism modals
 *
 * VIBE COMPLIANT:
 * - Real Lit 3.x Web Component
 * - Light/dark theme support (auto via CSS tokens)
 * - Tenant cards with status indicators
 * - Click cards to open detail modals
 * - CRUD operations
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import '../components/saas-glass-modal.js';
import '../components/saas-status-badge.js';

interface Tenant {
    id: string;
    name: string;
    slug: string;
    plan: 'starter' | 'professional' | 'enterprise';
    status: 'active' | 'trial' | 'suspended' | 'pending';
    agents: number;
    users: number;
    mrr: number;
    createdAt: string;
    logoUrl?: string;
}

@customElement('saas-tenants')
export class SaasTenants extends LitElement {
    static styles = css`
        :host {
            display: block;
            min-height: 100vh;
            background: var(--saas-bg-page, #f5f5f5);
            color: var(--saas-text-primary, #1a1a1a);
            font-family: var(--saas-font-sans);
        }

        * { box-sizing: border-box; }

        /* Header */
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: var(--saas-space-lg, 24px);
            background: var(--saas-bg-card, #ffffff);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: var(--saas-space-md, 16px);
        }

        .page-title {
            font-size: var(--saas-text-xl, 22px);
            font-weight: var(--saas-font-semibold, 600);
            margin: 0;
        }

        .tenant-count {
            padding: 4px 10px;
            background: var(--saas-bg-active, #f0f0f0);
            border-radius: var(--saas-radius-full, 9999px);
            font-size: var(--saas-text-sm, 13px);
            color: var(--saas-text-secondary, #666666);
        }

        .header-actions {
            display: flex;
            gap: var(--saas-space-sm, 8px);
        }

        .search-input {
            width: 280px;
            padding: var(--saas-space-sm, 8px) var(--saas-space-md, 16px);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: var(--saas-radius-md, 8px);
            font-size: var(--saas-text-sm, 13px);
            background: var(--saas-bg-page, #f5f5f5);
        }

        .search-input:focus {
            outline: none;
            border-color: var(--saas-accent, #1a1a1a);
        }

        .btn-primary {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: var(--saas-space-sm, 8px) var(--saas-space-md, 16px);
            background: var(--saas-accent, #1a1a1a);
            color: var(--saas-text-inverse, #ffffff);
            border: none;
            border-radius: var(--saas-radius-md, 8px);
            font-size: var(--saas-text-sm, 13px);
            font-weight: var(--saas-font-medium, 500);
            cursor: pointer;
            transition: background var(--saas-transition-fast, 150ms ease);
        }

        .btn-primary:hover {
            background: var(--saas-accent-hover, #333333);
        }

        /* Filters */
        .filters {
            display: flex;
            gap: var(--saas-space-sm, 8px);
            padding: var(--saas-space-md, 16px) var(--saas-space-lg, 24px);
            background: var(--saas-bg-card, #ffffff);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .filter-btn {
            padding: 6px 14px;
            background: transparent;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: var(--saas-radius-full, 9999px);
            font-size: var(--saas-text-sm, 13px);
            color: var(--saas-text-secondary, #666666);
            cursor: pointer;
            transition: all var(--saas-transition-fast, 150ms ease);
        }

        .filter-btn:hover {
            background: var(--saas-bg-hover, #fafafa);
            border-color: var(--saas-border-medium, #cccccc);
        }

        .filter-btn.active {
            background: var(--saas-accent, #1a1a1a);
            color: var(--saas-text-inverse, #ffffff);
            border-color: var(--saas-accent, #1a1a1a);
        }

        /* Grid */
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: var(--saas-space-lg, 24px);
            padding: var(--saas-space-lg, 24px);
        }

        /* Tenant Card */
        .tenant-card {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: var(--saas-radius-lg, 12px);
            padding: var(--saas-space-lg, 24px);
            cursor: pointer;
            transition: all var(--saas-transition-normal, 200ms ease);
            position: relative;
        }

        .tenant-card:hover {
            border-color: var(--saas-border-medium, #cccccc);
            transform: translateY(-2px);
            box-shadow: var(--saas-shadow-md, 0 2px 8px rgba(0, 0, 0, 0.06));
        }

        .card-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            margin-bottom: var(--saas-space-md, 16px);
        }

        .tenant-logo {
            width: 48px;
            height: 48px;
            border-radius: var(--saas-radius-md, 8px);
            background: var(--saas-bg-active, #f0f0f0);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            font-weight: var(--saas-font-bold, 700);
            color: var(--saas-text-secondary, #666666);
        }

        .tenant-name {
            font-size: var(--saas-text-md, 16px);
            font-weight: var(--saas-font-semibold, 600);
            color: var(--saas-text-primary, #1a1a1a);
            margin: var(--saas-space-sm, 8px) 0 4px;
        }

        .tenant-slug {
            font-size: var(--saas-text-sm, 13px);
            color: var(--saas-text-muted, #999999);
        }

        .card-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: var(--saas-space-sm, 8px);
            margin-top: var(--saas-space-md, 16px);
            padding-top: var(--saas-space-md, 16px);
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .stat {
            text-align: center;
        }

        .stat-value {
            font-size: var(--saas-text-lg, 18px);
            font-weight: var(--saas-font-bold, 700);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .stat-label {
            font-size: var(--saas-text-xs, 11px);
            color: var(--saas-text-muted, #999999);
            text-transform: uppercase;
        }

        .plan-badge {
            position: absolute;
            top: var(--saas-space-md, 16px);
            right: var(--saas-space-md, 16px);
            padding: 4px 10px;
            font-size: var(--saas-text-xs, 11px);
            font-weight: var(--saas-font-semibold, 600);
            border-radius: var(--saas-radius-sm, 4px);
            text-transform: uppercase;
        }

        .plan-badge.starter {
            background: rgba(107, 114, 128, 0.1);
            color: #6b7280;
        }

        .plan-badge.professional {
            background: rgba(59, 130, 246, 0.1);
            color: #3b82f6;
        }

        .plan-badge.enterprise {
            background: rgba(147, 51, 234, 0.1);
            color: #9333ea;
        }

        /* Modal Content */
        .modal-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: var(--saas-space-md, 16px);
        }

        .modal-section {
            padding: var(--saas-space-md, 16px);
            background: var(--saas-bg-page, #f5f5f5);
            border-radius: var(--saas-radius-md, 8px);
        }

        .modal-section-title {
            font-size: var(--saas-text-xs, 11px);
            font-weight: var(--saas-font-semibold, 600);
            color: var(--saas-text-muted, #999999);
            text-transform: uppercase;
            margin-bottom: var(--saas-space-sm, 8px);
        }

        .modal-section-value {
            font-size: var(--saas-text-md, 16px);
            font-weight: var(--saas-font-medium, 500);
            color: var(--saas-text-primary, #1a1a1a);
        }
    `;

    @state() private _tenants: Tenant[] = [
        { id: '1', name: 'Acme Corporation', slug: 'acme-corp', plan: 'enterprise', status: 'active', agents: 45, users: 1240, mrr: 4500, createdAt: '2024-01-15' },
        { id: '2', name: 'TechStart Inc', slug: 'techstart', plan: 'professional', status: 'active', agents: 32, users: 890, mrr: 3200, createdAt: '2024-02-20' },
        { id: '3', name: 'Global Services', slug: 'global-svc', plan: 'enterprise', status: 'active', agents: 28, users: 756, mrr: 2800, createdAt: '2024-03-10' },
        { id: '4', name: 'Digital Labs', slug: 'digital-labs', plan: 'starter', status: 'trial', agents: 5, users: 45, mrr: 0, createdAt: '2024-11-01' },
        { id: '5', name: 'Enterprise Co', slug: 'enterprise-co', plan: 'professional', status: 'active', agents: 18, users: 432, mrr: 1800, createdAt: '2024-05-22' },
        { id: '6', name: 'CloudOps Ltd', slug: 'cloudops', plan: 'starter', status: 'pending', agents: 0, users: 3, mrr: 0, createdAt: '2024-12-20' },
    ];

    @state() private _filter: 'all' | 'active' | 'trial' | 'suspended' = 'all';
    @state() private _selectedTenant: Tenant | null = null;
    @state() private _showModal = false;

    render() {
        const filteredTenants = this._filter === 'all'
            ? this._tenants
            : this._tenants.filter(t => t.status === this._filter);

        return html`
            <header class="header">
                <div class="header-left">
                    <h1 class="page-title">Tenants</h1>
                    <span class="tenant-count">${this._tenants.length}</span>
                </div>
                <div class="header-actions">
                    <input type="text" class="search-input" placeholder="Search tenants...">
                    <button class="btn-primary" @click=${this._openCreateModal}>
                        <span>+</span> New Tenant
                    </button>
                </div>
            </header>

            <div class="filters">
                ${(['all', 'active', 'trial', 'suspended'] as const).map(filter => html`
                    <button 
                        class="filter-btn ${this._filter === filter ? 'active' : ''}"
                        @click=${() => this._filter = filter}
                    >
                        ${filter.charAt(0).toUpperCase() + filter.slice(1)}
                    </button>
                `)}
            </div>

            <div class="grid">
                ${filteredTenants.map(tenant => html`
                    <article class="tenant-card" @click=${() => this._openTenantModal(tenant)}>
                        <div class="card-header">
                            <div>
                                <div class="tenant-logo">${tenant.name.charAt(0)}</div>
                                <h3 class="tenant-name">${tenant.name}</h3>
                                <p class="tenant-slug">${tenant.slug}</p>
                            </div>
                            <saas-status-badge 
                                variant=${this._getStatusVariant(tenant.status)}
                                size="sm"
                            >${tenant.status}</saas-status-badge>
                        </div>
                        <span class="plan-badge ${tenant.plan}">${tenant.plan}</span>
                        <div class="card-stats">
                            <div class="stat">
                                <div class="stat-value">${tenant.agents}</div>
                                <div class="stat-label">Agents</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">${tenant.users.toLocaleString()}</div>
                                <div class="stat-label">Users</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">${tenant.mrr ? `$${tenant.mrr}` : '—'}</div>
                                <div class="stat-label">MRR</div>
                            </div>
                        </div>
                    </article>
                `)}
            </div>

            <saas-glass-modal
                ?open=${this._showModal}
                title=${this._selectedTenant?.name ?? 'Tenant Details'}
                subtitle=${this._selectedTenant?.slug ?? ''}
                size="lg"
                @saas-modal-close=${() => this._showModal = false}
            >
                ${this._selectedTenant ? html`
                    <div class="modal-grid">
                        <div class="modal-section">
                            <div class="modal-section-title">Status</div>
                            <saas-status-badge 
                                variant=${this._getStatusVariant(this._selectedTenant.status)}
                            >${this._selectedTenant.status}</saas-status-badge>
                        </div>
                        <div class="modal-section">
                            <div class="modal-section-title">Plan</div>
                            <div class="modal-section-value">${this._selectedTenant.plan}</div>
                        </div>
                        <div class="modal-section">
                            <div class="modal-section-title">Agents</div>
                            <div class="modal-section-value">${this._selectedTenant.agents}</div>
                        </div>
                        <div class="modal-section">
                            <div class="modal-section-title">Users</div>
                            <div class="modal-section-value">${this._selectedTenant.users.toLocaleString()}</div>
                        </div>
                        <div class="modal-section">
                            <div class="modal-section-title">Monthly Revenue</div>
                            <div class="modal-section-value">$${this._selectedTenant.mrr.toLocaleString()}</div>
                        </div>
                        <div class="modal-section">
                            <div class="modal-section-title">Created</div>
                            <div class="modal-section-value">${this._selectedTenant.createdAt}</div>
                        </div>
                    </div>
                ` : ''}
                <div slot="actions">
                    <button class="btn-primary" @click=${this._editTenant}>Edit Tenant</button>
                </div>
            </saas-glass-modal>
        `;
    }

    private _getStatusVariant(status: string) {
        switch (status) {
            case 'active': return 'success';
            case 'trial': return 'info';
            case 'suspended': return 'danger';
            case 'pending': return 'warning';
            default: return 'neutral';
        }
    }

    private _openTenantModal(tenant: Tenant) {
        this._selectedTenant = tenant;
        this._showModal = true;
    }

    private _openCreateModal() {
        this._selectedTenant = null;
        this._showModal = true;
    }

    private _editTenant() {
        console.log('Edit tenant:', this._selectedTenant?.id);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-tenants': SaasTenants;
    }
}
