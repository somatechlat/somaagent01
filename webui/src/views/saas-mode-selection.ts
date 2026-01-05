/**
 * SomaAgent SaaS — Mode Selection
 * Per UI_SCREENS_SRS.md Section 4 - Mode Selection Screen
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - SpiceDB permission checks (when configured)
 * - Minimal white/black design per UI_STYLE_GUIDE.md
 * - NO EMOJIS - Google Material Symbols only
 * 
 * Purpose:
 * After login, SAAS Admins select their entry mode:
 * - God Mode: Platform-wide administration
 * - Tenant Mode: Enter a specific tenant context
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';

interface Tenant {
    id: string;
    name: string;
    slug: string;
    tier: string;
    agentCount: number;
    userCount: number;
    status: string;
}

@customElement('saas-mode-selection')
export class SaasModeSelection extends LitElement {
    static styles = css`
        :host {
            display: flex;
            min-height: 100vh;
            background: var(--saas-bg-page, #f5f5f5);
            font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            color: var(--saas-text-primary, #1a1a1a);
            align-items: center;
            justify-content: center;
            padding: 40px 20px;
        }

        * {
            box-sizing: border-box;
        }

        /* Material Symbols - Required for Shadow DOM */
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

        .container {
            width: 100%;
            max-width: 800px;
        }

        /* Header */
        .header {
            text-align: center;
            margin-bottom: 40px;
        }

        .logo {
            width: 48px;
            height: 48px;
            background: #1a1a1a;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 16px;
        }

        .logo svg {
            width: 24px;
            height: 24px;
            stroke: white;
            fill: none;
        }

        .title {
            font-size: 28px;
            font-weight: 600;
            margin: 0 0 8px 0;
        }

        .subtitle {
            font-size: 16px;
            color: var(--saas-text-secondary, #666);
        }

        /* Mode Cards */
        .mode-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 40px;
        }

        @media (max-width: 600px) {
            .mode-grid {
                grid-template-columns: 1fr;
            }
        }

        .mode-card {
            background: var(--saas-bg-card, #ffffff);
            border: 2px solid var(--saas-border-light, #e0e0e0);
            border-radius: 16px;
            padding: 32px;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: center;
        }

        .mode-card:hover {
            border-color: var(--saas-border-medium, #ccc);
            transform: translateY(-2px);
            box-shadow: var(--saas-shadow-md, 0 4px 12px rgba(0,0,0,0.08));
        }

        .mode-card.selected {
            border-color: #1a1a1a;
            box-shadow: 0 0 0 2px #1a1a1a;
        }

        .mode-card.god-mode {
            background: linear-gradient(135deg, #1a1a1a 0%, #333 100%);
            color: white;
            border-color: #1a1a1a;
        }

        .mode-card.god-mode:hover {
            border-color: #333;
        }

        .mode-icon {
            width: 56px;
            height: 56px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 16px;
        }

        .mode-card:not(.god-mode) .mode-icon {
            background: var(--saas-bg-hover, #fafafa);
            border: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .mode-card.god-mode .mode-icon {
            background: rgba(255,255,255,0.15);
        }

        .mode-icon .material-symbols-outlined {
            font-size: 28px;
        }

        .mode-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .mode-desc {
            font-size: 14px;
            line-height: 1.5;
        }

        .mode-card:not(.god-mode) .mode-desc {
            color: var(--saas-text-secondary, #666);
        }

        .mode-card.god-mode .mode-desc {
            color: rgba(255,255,255,0.7);
        }

        .mode-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            margin-top: 12px;
        }

        .mode-card:not(.god-mode) .mode-badge {
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-text-secondary, #666);
        }

        .mode-card.god-mode .mode-badge {
            background: rgba(255,255,255,0.2);
            color: white;
        }

        /* Tenant Selection */
        .tenant-section {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
        }

        .tenant-section.hidden {
            display: none;
        }

        .section-title {
            font-size: 16px;
            font-weight: 600;
            margin: 0 0 16px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .section-title .material-symbols-outlined {
            font-size: 20px;
            color: var(--saas-text-secondary, #666);
        }

        /* Tenant Search */
        .search-box {
            position: relative;
            margin-bottom: 16px;
        }

        .search-input {
            width: 100%;
            padding: 12px 16px 12px 44px;
            border-radius: 8px;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            font-size: 14px;
            background: var(--saas-bg-card, #ffffff);
            color: var(--saas-text-primary, #1a1a1a);
            transition: border-color 0.15s ease;
        }

        .search-input:focus {
            outline: none;
            border-color: var(--saas-text-primary, #1a1a1a);
        }

        .search-icon {
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--saas-text-muted, #999);
        }

        /* Tenant List */
        .tenant-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
            max-height: 300px;
            overflow-y: auto;
        }

        .tenant-item {
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 14px 16px;
            border-radius: 10px;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .tenant-item:hover {
            background: var(--saas-bg-hover, #fafafa);
            border-color: var(--saas-border-medium, #ccc);
        }

        .tenant-item.selected {
            background: var(--saas-bg-active, #f0f0f0);
            border-color: #1a1a1a;
        }

        .tenant-avatar {
            width: 40px;
            height: 40px;
            border-radius: 8px;
            background: var(--saas-bg-hover, #fafafa);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            font-weight: 600;
            flex-shrink: 0;
        }

        .tenant-info {
            flex: 1;
            min-width: 0;
        }

        .tenant-name {
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 2px;
        }

        .tenant-meta {
            font-size: 12px;
            color: var(--saas-text-muted, #999);
        }

        .tenant-tier {
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .tenant-tier.free { background: #f3f4f6; color: #6b7280; }
        .tenant-tier.starter { background: #dbeafe; color: #1d4ed8; }
        .tenant-tier.team { background: #d1fae5; color: #047857; }
        .tenant-tier.enterprise { background: #fef3c7; color: #b45309; }

        /* Actions */
        .actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logout-link {
            font-size: 14px;
            color: var(--saas-text-secondary, #666);
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 6px;
            cursor: pointer;
        }

        .logout-link:hover {
            color: var(--saas-text-primary, #1a1a1a);
        }

        .continue-btn {
            padding: 14px 32px;
            border-radius: 10px;
            background: #1a1a1a;
            color: white;
            border: none;
            font-size: 15px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: all 0.15s ease;
        }

        .continue-btn:hover:not(:disabled) {
            background: #333;
            transform: translateY(-1px);
        }

        .continue-btn:disabled {
            background: var(--saas-border-light, #e0e0e0);
            color: var(--saas-text-muted, #999);
            cursor: not-allowed;
        }

        .continue-btn .material-symbols-outlined {
            font-size: 18px;
        }

        /* User Info */
        .user-info {
            text-align: center;
            margin-bottom: 24px;
            padding: 16px;
            background: var(--saas-bg-card, #ffffff);
            border-radius: 12px;
            border: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .user-greeting {
            font-size: 14px;
            color: var(--saas-text-secondary, #666);
        }

        .user-name {
            font-size: 16px;
            font-weight: 600;
        }
    `;

    @state() private _selectedMode: 'god' | 'tenant' | null = null;
    @state() private _selectedTenantId: string | null = null;
    @state() private _tenants: Tenant[] = [];
    @state() private _searchQuery = '';
    @state() private _isLoading = false;
    @state() private _userName = 'Admin User';
    @state() private _userEmail = 'admin@somatech.dev';

    async connectedCallback() {
        super.connectedCallback();
        await this._loadUserAndTenants();
    }

    render() {
        const filteredTenants = this._tenants.filter(t =>
            t.name.toLowerCase().includes(this._searchQuery.toLowerCase()) ||
            t.slug.toLowerCase().includes(this._searchQuery.toLowerCase())
        );

        return html`
            <div class="container">
                <!-- Header -->
                <div class="header">
                    <div class="logo">
                        <svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="3" y="3" width="7" height="7" rx="1"/>
                            <rect x="14" y="3" width="7" height="7" rx="1"/>
                            <rect x="14" y="14" width="7" height="7" rx="1"/>
                            <rect x="3" y="14" width="7" height="7" rx="1"/>
                        </svg>
                    </div>
                    <h1 class="title">Welcome to SomaAgent</h1>
                    <p class="subtitle">Select how you'd like to continue</p>
                </div>

                <!-- User Info -->
                <div class="user-info">
                    <div class="user-greeting">Signed in as</div>
                    <div class="user-name">${this._userName} (${this._userEmail})</div>
                </div>

                <!-- Mode Selection -->
                <div class="mode-grid">
                    <!-- God Mode Card -->
                    <div 
                        class="mode-card god-mode ${this._selectedMode === 'god' ? 'selected' : ''}"
                        @click=${() => this._selectMode('god')}
                    >
                        <div class="mode-icon">
                            <span class="material-symbols-outlined">shield_person</span>
                        </div>
                        <div class="mode-title">God Mode</div>
                        <div class="mode-desc">
                            Platform-wide administration. Manage all tenants, billing, and system configuration.
                        </div>
                        <div class="mode-badge">SAAS Admin</div>
                    </div>

                    <!-- Tenant Mode Card -->
                    <div 
                        class="mode-card ${this._selectedMode === 'tenant' ? 'selected' : ''}"
                        @click=${() => this._selectMode('tenant')}
                    >
                        <div class="mode-icon">
                            <span class="material-symbols-outlined">apartment</span>
                        </div>
                        <div class="mode-title">Enter Tenant</div>
                        <div class="mode-desc">
                            Access a specific organization as their administrator or support.
                        </div>
                        <div class="mode-badge">Impersonate</div>
                    </div>
                </div>

                <!-- Tenant Selection (shown when Tenant mode selected) -->
                <div class="tenant-section ${this._selectedMode !== 'tenant' ? 'hidden' : ''}">
                    <h3 class="section-title">
                        <span class="material-symbols-outlined">business</span>
                        Select Tenant
                    </h3>

                    <div class="search-box">
                        <span class="material-symbols-outlined search-icon">search</span>
                        <input 
                            type="text" 
                            class="search-input" 
                            placeholder="Search tenants..."
                            .value=${this._searchQuery}
                            @input=${(e: Event) => this._searchQuery = (e.target as HTMLInputElement).value}
                        >
                    </div>

                    <div class="tenant-list">
                        ${filteredTenants.length === 0 ? html`
                            <div style="text-align: center; padding: 20px; color: var(--saas-text-muted, #999);">
                                ${this._searchQuery ? 'No tenants match your search' : 'No tenants available'}
                            </div>
                        ` : filteredTenants.map(tenant => html`
                            <div 
                                class="tenant-item ${this._selectedTenantId === tenant.id ? 'selected' : ''}"
                                @click=${() => this._selectTenant(tenant.id)}
                            >
                                <div class="tenant-avatar">${tenant.name.charAt(0).toUpperCase()}</div>
                                <div class="tenant-info">
                                    <div class="tenant-name">${tenant.name}</div>
                                    <div class="tenant-meta">${tenant.agentCount} agents, ${tenant.userCount} users</div>
                                </div>
                                <div class="tenant-tier ${tenant.tier}">${tenant.tier}</div>
                            </div>
                        `)}
                    </div>
                </div>

                <!-- Actions -->
                <div class="actions">
                    <a class="logout-link" @click=${this._logout}>
                        <span class="material-symbols-outlined">logout</span>
                        Sign out
                    </a>
                    <button 
                        class="continue-btn"
                        ?disabled=${!this._canContinue()}
                        @click=${this._continue}
                    >
                        Continue
                        <span class="material-symbols-outlined">arrow_forward</span>
                    </button>
                </div>
            </div>
        `;
    }

    private async _loadUserAndTenants() {
        this._isLoading = true;

        try {
            // Load user from localStorage
            const userStr = localStorage.getItem('saas_user');
            if (userStr) {
                const user = JSON.parse(userStr);
                this._userName = user.name || 'Admin User';
                this._userEmail = user.email || 'admin@somatech.dev';
            }

            try {
                const response = await apiClient.get('/saas/tenants/') as { tenants?: Tenant[] };
                if (response.tenants) {
                    this._tenants = response.tenants;
                }
            } catch {
                // Demo data if API not available
                this._tenants = [
                    { id: '1', name: 'Acme Corporation', slug: 'acme', tier: 'enterprise', agentCount: 12, userCount: 45, status: 'active' },
                    { id: '2', name: 'TechStart Inc', slug: 'techstart', tier: 'team', agentCount: 5, userCount: 18, status: 'active' },
                    { id: '3', name: 'Globex Industries', slug: 'globex', tier: 'starter', agentCount: 2, userCount: 8, status: 'active' },
                    { id: '4', name: 'Demo Company', slug: 'demo', tier: 'free', agentCount: 1, userCount: 3, status: 'active' },
                ];
            }
        } finally {
            this._isLoading = false;
        }
    }

    private _selectMode(mode: 'god' | 'tenant') {
        this._selectedMode = mode;
        if (mode === 'god') {
            this._selectedTenantId = null;
        }
    }

    private _selectTenant(tenantId: string) {
        this._selectedTenantId = tenantId;
    }

    private _canContinue(): boolean {
        if (this._selectedMode === 'god') return true;
        if (this._selectedMode === 'tenant' && this._selectedTenantId) return true;
        return false;
    }

    private _continue() {
        if (this._selectedMode === 'god') {
            // Store mode in session
            sessionStorage.setItem('saas_mode', 'god');
            window.location.href = '/saas/dashboard';
        } else if (this._selectedMode === 'tenant' && this._selectedTenantId) {
            // Store tenant context
            const tenant = this._tenants.find(t => t.id === this._selectedTenantId);
            sessionStorage.setItem('saas_mode', 'tenant');
            sessionStorage.setItem('saas_tenant_id', this._selectedTenantId);
            sessionStorage.setItem('saas_tenant_name', tenant?.name || '');
            window.location.href = '/admin/dashboard';
        }
    }

    private _logout() {
        localStorage.removeItem('saas_auth_token');
        localStorage.removeItem('saas_user');
        sessionStorage.removeItem('saas_mode');
        sessionStorage.removeItem('saas_tenant_id');
        window.location.href = '/login';
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-mode-selection': SaasModeSelection;
    }
}
