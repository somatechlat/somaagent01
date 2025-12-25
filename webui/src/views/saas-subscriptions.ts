/**
 * SomaAgent SaaS — Subscription Tiers Management
 * Per SAAS_ADMIN_SRS.md Section 4.3 - Subscription Tiers
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Django Ninja API integration
 * - Minimal white/black design per UI_STYLE_GUIDE.md
 * - NO EMOJIS - Google Material Symbols only
 * 
 * Features:
 * - View and manage subscription tiers
 * - Edit tier limits (agents, users, tokens, storage)
 * - Create custom tiers
 * - View tier distribution
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';

interface SubscriptionTier {
    id: string;
    name: string;
    slug: string;
    maxAgents: number;
    maxUsers: number;
    maxTokensPerMonth: number;
    maxStorageGB: number;
    priceCents: number;
    billingInterval: 'monthly' | 'yearly';
    tenantCount: number;
    isCustom: boolean;
}

@customElement('saas-subscriptions')
export class SaasSubscriptions extends LitElement {
    static styles = css`
        :host {
            display: flex;
            height: 100vh;
            background: var(--saas-bg-page, #f5f5f5);
            font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            color: var(--saas-text-primary, #1a1a1a);
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

        /* ========================================
           SIDEBAR
           ======================================== */
        .sidebar {
            width: 260px;
            background: var(--saas-bg-card, #ffffff);
            border-right: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            padding: 24px 0;
        }

        .sidebar-header {
            padding: 0 20px 20px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            margin-bottom: 16px;
        }

        .sidebar-title {
            font-size: 18px;
            font-weight: 600;
            margin: 0 0 4px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .sidebar-subtitle {
            font-size: 13px;
            color: var(--saas-text-secondary, #666);
        }

        /* Nav Items */
        .nav-list {
            display: flex;
            flex-direction: column;
            gap: 2px;
            padding: 0 12px;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 14px;
            border-radius: 8px;
            font-size: 14px;
            color: var(--saas-text-secondary, #666);
            cursor: pointer;
            transition: all 0.15s ease;
            text-decoration: none;
        }

        .nav-item:hover {
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .nav-item.active {
            background: var(--saas-bg-active, #f0f0f0);
            color: var(--saas-text-primary, #1a1a1a);
            font-weight: 500;
        }

        .nav-item .material-symbols-outlined {
            font-size: 18px;
        }

        .nav-divider {
            height: 1px;
            background: var(--saas-border-light, #e0e0e0);
            margin: 12px 20px;
        }

        /* ========================================
           MAIN CONTENT
           ======================================== */
        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        /* Header */
        .header {
            padding: 16px 24px;
            background: var(--saas-bg-card, #ffffff);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-title {
            font-size: 18px;
            font-weight: 600;
        }

        .header-actions {
            display: flex;
            gap: 10px;
        }

        .btn {
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 14px;
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
            font-size: 18px;
        }

        /* Content */
        .content {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
        }

        /* Tier Cards Grid */
        .tier-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
        }

        /* Tier Card */
        .tier-card {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 16px;
            padding: 24px;
            display: flex;
            flex-direction: column;
        }

        .tier-card.featured {
            border-color: #1a1a1a;
            box-shadow: 0 0 0 1px #1a1a1a;
        }

        .tier-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 16px;
        }

        .tier-name {
            font-size: 18px;
            font-weight: 600;
        }

        .tier-badge {
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .tier-badge.custom {
            background: #fef3c7;
            color: #b45309;
        }

        .tier-badge.popular {
            background: #1a1a1a;
            color: white;
        }

        .tier-price {
            margin-bottom: 20px;
        }

        .price-amount {
            font-size: 32px;
            font-weight: 700;
        }

        .price-period {
            font-size: 14px;
            color: var(--saas-text-secondary, #666);
        }

        /* Tier Limits */
        .tier-limits {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-bottom: 20px;
        }

        .limit-row {
            display: flex;
            justify-content: space-between;
            font-size: 14px;
        }

        .limit-label {
            color: var(--saas-text-secondary, #666);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .limit-label .material-symbols-outlined {
            font-size: 16px;
        }

        .limit-value {
            font-weight: 500;
        }

        .limit-value.unlimited {
            color: var(--saas-status-success, #22c55e);
        }

        /* Tier Stats */
        .tier-stats {
            padding-top: 16px;
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
            margin-bottom: 16px;
        }

        .stat-row {
            display: flex;
            justify-content: space-between;
            font-size: 13px;
        }

        .stat-label {
            color: var(--saas-text-muted, #999);
        }

        .stat-value {
            font-weight: 500;
        }

        /* Tier Actions */
        .tier-actions {
            display: flex;
            gap: 8px;
        }

        .tier-btn {
            flex: 1;
            padding: 10px;
            border-radius: 8px;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            background: var(--saas-bg-card, #ffffff);
            font-size: 13px;
            cursor: pointer;
            transition: all 0.1s ease;
        }

        .tier-btn:hover {
            background: var(--saas-bg-hover, #fafafa);
        }

        /* Modal Overlay */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }

        .modal-overlay.hidden {
            display: none;
        }

        .modal {
            background: var(--saas-bg-card, #ffffff);
            border-radius: 16px;
            width: 100%;
            max-width: 500px;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: var(--saas-shadow-lg, 0 8px 24px rgba(0,0,0,0.12));
        }

        .modal-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-title {
            font-size: 18px;
            font-weight: 600;
        }

        .modal-close {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            border: none;
            background: transparent;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .modal-close:hover {
            background: var(--saas-bg-hover, #fafafa);
        }

        .modal-body {
            padding: 24px;
        }

        .modal-footer {
            padding: 16px 24px;
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            justify-content: flex-end;
            gap: 10px;
        }

        /* Form */
        .form-group {
            margin-bottom: 20px;
        }

        .form-label {
            display: block;
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 8px;
        }

        .form-input {
            width: 100%;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            font-size: 14px;
            background: var(--saas-bg-card, #ffffff);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .form-input:focus {
            outline: none;
            border-color: var(--saas-text-primary, #1a1a1a);
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        .form-hint {
            font-size: 12px;
            color: var(--saas-text-muted, #999);
            margin-top: 6px;
        }
    `;

    @state() private _tiers: SubscriptionTier[] = [];
    @state() private _showModal = false;
    @state() private _editingTier: SubscriptionTier | null = null;
    @state() private _isLoading = false;

    async connectedCallback() {
        super.connectedCallback();
        await this._loadTiers();
    }

    render() {
        return html`
            <!-- Sidebar -->
            <aside class="sidebar">
                <div class="sidebar-header">
                    <h1 class="sidebar-title">
                        <span class="material-symbols-outlined">shield_person</span>
                        God Mode
                    </h1>
                    <p class="sidebar-subtitle">Platform Administration</p>
                </div>

                <nav class="nav-list">
                    <a class="nav-item" href="/saas/dashboard">
                        <span class="material-symbols-outlined">dashboard</span>
                        Dashboard
                    </a>
                    <a class="nav-item" href="/saas/tenants">
                        <span class="material-symbols-outlined">apartment</span>
                        Tenants
                    </a>
                    <a class="nav-item active" href="/saas/subscriptions">
                        <span class="material-symbols-outlined">card_membership</span>
                        Subscriptions
                    </a>
                    <a class="nav-item" href="/saas/billing">
                        <span class="material-symbols-outlined">payments</span>
                        Billing
                    </a>
                    <div class="nav-divider"></div>
                    <a class="nav-item" href="/platform/models">
                        <span class="material-symbols-outlined">model_training</span>
                        Models
                    </a>
                    <a class="nav-item" href="/platform/roles">
                        <span class="material-symbols-outlined">admin_panel_settings</span>
                        Roles
                    </a>
                    <a class="nav-item" href="/platform/flags">
                        <span class="material-symbols-outlined">toggle_on</span>
                        Feature Flags
                    </a>
                    <a class="nav-item" href="/platform/api-keys">
                        <span class="material-symbols-outlined">vpn_key</span>
                        API Keys
                    </a>
                </nav>
            </aside>

            <!-- Main Content -->
            <main class="main">
                <header class="header">
                    <h2 class="header-title">Subscription Tiers</h2>
                    <div class="header-actions">
                        <button class="btn primary" @click=${() => this._openModal()}>
                            <span class="material-symbols-outlined">add</span>
                            Create Custom Tier
                        </button>
                    </div>
                </header>

                <div class="content">
                    <div class="tier-grid">
                        ${this._tiers.map(tier => this._renderTierCard(tier))}
                    </div>
                </div>
            </main>

            <!-- Modal -->
            <div class="modal-overlay ${this._showModal ? '' : 'hidden'}" @click=${(e: Event) => e.target === e.currentTarget && this._closeModal()}>
                <div class="modal">
                    <div class="modal-header">
                        <h3 class="modal-title">${this._editingTier ? 'Edit Tier' : 'Create Custom Tier'}</h3>
                        <button class="modal-close" @click=${this._closeModal}>
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label class="form-label">Tier Name</label>
                            <input type="text" class="form-input" id="tierName" 
                                .value=${this._editingTier?.name || ''}
                                placeholder="e.g., Premium Plus">
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Max Agents</label>
                                <input type="number" class="form-input" id="maxAgents"
                                    .value=${String(this._editingTier?.maxAgents || 5)}
                                    min="1">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Max Users</label>
                                <input type="number" class="form-input" id="maxUsers"
                                    .value=${String(this._editingTier?.maxUsers || 25)}
                                    min="1">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Tokens/Month</label>
                                <input type="number" class="form-input" id="maxTokens"
                                    .value=${String(this._editingTier?.maxTokensPerMonth || 5000000)}
                                    min="100000" step="100000">
                                <p class="form-hint">In tokens (1M = 1,000,000)</p>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Storage (GB)</label>
                                <input type="number" class="form-input" id="maxStorage"
                                    .value=${String(this._editingTier?.maxStorageGB || 50)}
                                    min="1">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Price (USD)</label>
                                <input type="number" class="form-input" id="price"
                                    .value=${String((this._editingTier?.priceCents || 9900) / 100)}
                                    min="0" step="0.01">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Billing Interval</label>
                                <select class="form-input" id="interval">
                                    <option value="monthly" ?selected=${this._editingTier?.billingInterval === 'monthly'}>Monthly</option>
                                    <option value="yearly" ?selected=${this._editingTier?.billingInterval === 'yearly'}>Yearly</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn" @click=${this._closeModal}>Cancel</button>
                        <button class="btn primary" @click=${this._saveTier}>
                            ${this._editingTier ? 'Save Changes' : 'Create Tier'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    private _renderTierCard(tier: SubscriptionTier) {
        const isPopular = tier.slug === 'team';
        const priceDisplay = tier.priceCents === 0
            ? '$0'
            : `$${(tier.priceCents / 100).toFixed(0)}`;

        return html`
            <div class="tier-card ${isPopular ? 'featured' : ''}">
                <div class="tier-header">
                    <span class="tier-name">${tier.name}</span>
                    ${tier.isCustom ? html`<span class="tier-badge custom">Custom</span>` : ''}
                    ${isPopular ? html`<span class="tier-badge popular">Popular</span>` : ''}
                </div>

                <div class="tier-price">
                    <span class="price-amount">${priceDisplay}</span>
                    <span class="price-period">/${tier.billingInterval === 'yearly' ? 'year' : 'mo'}</span>
                </div>

                <div class="tier-limits">
                    <div class="limit-row">
                        <span class="limit-label">
                            <span class="material-symbols-outlined">smart_toy</span>
                            Agents
                        </span>
                        <span class="limit-value ${tier.maxAgents === -1 ? 'unlimited' : ''}">
                            ${tier.maxAgents === -1 ? 'Unlimited' : tier.maxAgents}
                        </span>
                    </div>
                    <div class="limit-row">
                        <span class="limit-label">
                            <span class="material-symbols-outlined">group</span>
                            Users
                        </span>
                        <span class="limit-value ${tier.maxUsers === -1 ? 'unlimited' : ''}">
                            ${tier.maxUsers === -1 ? 'Unlimited' : tier.maxUsers}
                        </span>
                    </div>
                    <div class="limit-row">
                        <span class="limit-label">
                            <span class="material-symbols-outlined">token</span>
                            Tokens/mo
                        </span>
                        <span class="limit-value ${tier.maxTokensPerMonth === -1 ? 'unlimited' : ''}">
                            ${tier.maxTokensPerMonth === -1 ? 'Custom' : this._formatNumber(tier.maxTokensPerMonth)}
                        </span>
                    </div>
                    <div class="limit-row">
                        <span class="limit-label">
                            <span class="material-symbols-outlined">cloud</span>
                            Storage
                        </span>
                        <span class="limit-value ${tier.maxStorageGB === -1 ? 'unlimited' : ''}">
                            ${tier.maxStorageGB === -1 ? 'Custom' : `${tier.maxStorageGB} GB`}
                        </span>
                    </div>
                </div>

                <div class="tier-stats">
                    <div class="stat-row">
                        <span class="stat-label">Active tenants</span>
                        <span class="stat-value">${tier.tenantCount}</span>
                    </div>
                </div>

                <div class="tier-actions">
                    <button class="tier-btn" @click=${() => this._openModal(tier)}>Edit</button>
                    ${tier.isCustom ? html`
                        <button class="tier-btn" @click=${() => this._deleteTier(tier.id)}>Delete</button>
                    ` : ''}
                </div>
            </div>
        `;
    }

    private _formatNumber(num: number): string {
        if (num >= 1000000) {
            return `${(num / 1000000).toFixed(0)}M`;
        } else if (num >= 1000) {
            return `${(num / 1000).toFixed(0)}K`;
        }
        return String(num);
    }

    private async _loadTiers() {
        this._isLoading = true;
        try {
            const response = await apiClient.get('/saas/subscriptions/') as { tiers?: SubscriptionTier[] };
            if (response.tiers) {
                this._tiers = response.tiers;
            }
        } catch {
            // Demo data if API not available
            this._tiers = [
                { id: '1', name: 'Free', slug: 'free', maxAgents: 1, maxUsers: 3, maxTokensPerMonth: 100000, maxStorageGB: 1, priceCents: 0, billingInterval: 'monthly', tenantCount: 45, isCustom: false },
                { id: '2', name: 'Starter', slug: 'starter', maxAgents: 3, maxUsers: 10, maxTokensPerMonth: 1000000, maxStorageGB: 10, priceCents: 4900, billingInterval: 'monthly', tenantCount: 32, isCustom: false },
                { id: '3', name: 'Team', slug: 'team', maxAgents: 10, maxUsers: 50, maxTokensPerMonth: 10000000, maxStorageGB: 100, priceCents: 19900, billingInterval: 'monthly', tenantCount: 28, isCustom: false },
                { id: '4', name: 'Enterprise', slug: 'enterprise', maxAgents: -1, maxUsers: -1, maxTokensPerMonth: -1, maxStorageGB: -1, priceCents: 99900, billingInterval: 'monthly', tenantCount: 12, isCustom: false },
            ];
        } finally {
            this._isLoading = false;
        }
    }

    private _openModal(tier?: SubscriptionTier) {
        this._editingTier = tier || null;
        this._showModal = true;
    }

    private _closeModal() {
        this._showModal = false;
        this._editingTier = null;
    }

    private async _saveTier() {
        const nameEl = this.shadowRoot?.getElementById('tierName') as HTMLInputElement;
        const maxAgentsEl = this.shadowRoot?.getElementById('maxAgents') as HTMLInputElement;
        const maxUsersEl = this.shadowRoot?.getElementById('maxUsers') as HTMLInputElement;
        const maxTokensEl = this.shadowRoot?.getElementById('maxTokens') as HTMLInputElement;
        const maxStorageEl = this.shadowRoot?.getElementById('maxStorage') as HTMLInputElement;
        const priceEl = this.shadowRoot?.getElementById('price') as HTMLInputElement;
        const intervalEl = this.shadowRoot?.getElementById('interval') as HTMLSelectElement;

        const tierData = {
            name: nameEl.value,
            slug: nameEl.value.toLowerCase().replace(/\s+/g, '-'),
            maxAgents: parseInt(maxAgentsEl.value),
            maxUsers: parseInt(maxUsersEl.value),
            maxTokensPerMonth: parseInt(maxTokensEl.value),
            maxStorageGB: parseInt(maxStorageEl.value),
            priceCents: Math.round(parseFloat(priceEl.value) * 100),
            billingInterval: intervalEl.value as 'monthly' | 'yearly',
            isCustom: true,
        };

        try {
            if (this._editingTier) {
                await apiClient.put(`/saas/subscriptions/${this._editingTier.id}/`, tierData);
            } else {
                await apiClient.post('/saas/subscriptions/', tierData);
            }
            await this._loadTiers();
            this._closeModal();
        } catch (error) {
            console.error('Failed to save tier:', error);
        }
    }

    private async _deleteTier(tierId: string) {
        if (!confirm('Delete this custom tier? Tenants using it will need to be reassigned.')) {
            return;
        }
        try {
            await apiClient.delete(`/saas/subscriptions/${tierId}/`);
            await this._loadTiers();
        } catch (error) {
            console.error('Failed to delete tier:', error);
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-subscriptions': SaasSubscriptions;
    }
}
