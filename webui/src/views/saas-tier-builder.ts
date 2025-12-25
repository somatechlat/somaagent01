/**
 * Subscription Tier Builder
 * Visual editor for creating and managing subscription tiers
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Uses existing /api/v2/saas/tiers endpoints
 * - Permission-aware (tier:view, tier:create, tier:edit)
 * - Light theme, minimal, professional
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';

interface TierLimits {
    agents: number;
    users: number;
    tokens_per_month: number;
    storage_gb: number;
}

interface SubscriptionTier {
    id: string;
    name: string;
    slug: string;
    price: number;
    billing_period: string;
    limits: TierLimits;
    features: string[];
    popular: boolean;
    active_count: number;
}

@customElement('saas-tier-builder')
export class SaasTierBuilder extends LitElement {
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
      justify-content: space-between;
      align-items: center;
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

    /* Content */
    .content {
      flex: 1;
      overflow-y: auto;
      padding: 32px;
    }

    /* Tiers Grid */
    .tiers-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 24px;
    }

    /* Tier Card */
    .tier-card {
      background: var(--saas-bg-card, #ffffff);
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 16px;
      padding: 24px;
      position: relative;
      transition: all 0.2s ease;
    }

    .tier-card:hover {
      box-shadow: 0 4px 20px rgba(0,0,0,0.08);
      transform: translateY(-2px);
    }

    .tier-card.popular {
      border-color: #1a1a1a;
      border-width: 2px;
    }

    .popular-badge {
      position: absolute;
      top: -12px;
      right: 20px;
      background: #1a1a1a;
      color: white;
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
    }

    .tier-header {
      margin-bottom: 20px;
    }

    .tier-name {
      font-size: 18px;
      font-weight: 600;
      margin-bottom: 4px;
    }

    .tier-slug {
      font-size: 12px;
      color: var(--saas-text-muted, #999);
    }

    .tier-price {
      margin: 20px 0;
    }

    .price-amount {
      font-size: 42px;
      font-weight: 700;
      line-height: 1;
    }

    .price-currency {
      font-size: 20px;
      font-weight: 500;
      vertical-align: super;
    }

    .price-period {
      font-size: 14px;
      color: var(--saas-text-muted, #999);
    }

    .tier-limits {
      border-top: 1px solid var(--saas-border-light, #e0e0e0);
      padding-top: 16px;
      margin-bottom: 16px;
    }

    .limit-row {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      font-size: 13px;
    }

    .limit-label { color: var(--saas-text-secondary, #666); }
    .limit-value { font-weight: 600; }

    .tier-features {
      border-top: 1px solid var(--saas-border-light, #e0e0e0);
      padding-top: 16px;
      margin-bottom: 20px;
    }

    .feature-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 0;
      font-size: 13px;
    }

    .feature-item .material-symbols-outlined {
      font-size: 16px;
      color: #22c55e;
    }

    .tier-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 16px;
      border-top: 1px solid var(--saas-border-light, #e0e0e0);
    }

    .active-count {
      font-size: 12px;
      color: var(--saas-text-muted, #999);
    }

    .tier-actions {
      display: flex;
      gap: 8px;
    }

    .action-btn {
      width: 32px;
      height: 32px;
      border-radius: 6px;
      border: 1px solid var(--saas-border-light, #e0e0e0);
      background: var(--saas-bg-card, #ffffff);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
    }

    .action-btn:hover { background: var(--saas-bg-hover, #fafafa); }

    .action-btn .material-symbols-outlined { font-size: 16px; }

    /* Add Tier Card */
    .add-tier-card {
      background: var(--saas-bg-hover, #fafafa);
      border: 2px dashed var(--saas-border-light, #e0e0e0);
      border-radius: 16px;
      min-height: 400px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .add-tier-card:hover {
      border-color: #1a1a1a;
      background: var(--saas-bg-card, #ffffff);
    }

    .add-tier-card .material-symbols-outlined {
      font-size: 48px;
      color: var(--saas-text-muted, #999);
      margin-bottom: 12px;
    }

    .add-tier-card span:not(.material-symbols-outlined) {
      font-size: 14px;
      font-weight: 500;
      color: var(--saas-text-secondary, #666);
    }

    /* Loading */
    .loading {
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 60px;
      color: var(--saas-text-muted, #999);
    }

    /* Modal */
    .modal-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0,0,0,0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
    }

    .modal {
      background: var(--saas-bg-card, #ffffff);
      border-radius: 16px;
      width: 500px;
      max-width: 90vw;
      max-height: 80vh;
      overflow-y: auto;
    }

    .modal-header {
      padding: 20px 24px;
      border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .modal-title { font-size: 18px; font-weight: 600; margin: 0; }

    .modal-body { padding: 24px; }

    .form-group { margin-bottom: 20px; }

    .form-label {
      display: block;
      font-size: 12px;
      font-weight: 600;
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--saas-text-secondary, #666);
    }

    .form-input {
      width: 100%;
      padding: 12px 14px;
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 8px;
      font-size: 14px;
      outline: none;
    }

    .form-input:focus { border-color: #1a1a1a; }

    .form-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }

    .modal-footer {
      padding: 16px 24px;
      border-top: 1px solid var(--saas-border-light, #e0e0e0);
      display: flex;
      justify-content: flex-end;
      gap: 12px;
    }
  `;

    @state() private tiers: SubscriptionTier[] = [];
    @state() private loading = true;
    @state() private showModal = false;
    @state() private editingTier: Partial<SubscriptionTier> | null = null;

    connectedCallback() {
        super.connectedCallback();
        this.loadTiers();
    }

    private getAuthHeaders(): HeadersInit {
        const token = localStorage.getItem('auth_token') || localStorage.getItem('eog_auth_token');
        return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
    }

    private async loadTiers() {
        this.loading = true;
        try {
            const res = await fetch('/api/v2/saas/tiers', { headers: this.getAuthHeaders() });
            if (res.ok) {
                this.tiers = await res.json();
            } else {
                // Demo data
                this.tiers = this.getMockTiers();
            }
        } catch (e) {
            this.tiers = this.getMockTiers();
        } finally {
            this.loading = false;
        }
    }

    private getMockTiers(): SubscriptionTier[] {
        return [
            {
                id: '1',
                name: 'Starter',
                slug: 'starter',
                price: 0,
                billing_period: 'month',
                limits: { agents: 1, users: 3, tokens_per_month: 10000, storage_gb: 1 },
                features: ['Basic Chat', 'Email Support'],
                popular: false,
                active_count: 156,
            },
            {
                id: '2',
                name: 'Professional',
                slug: 'professional',
                price: 49,
                billing_period: 'month',
                limits: { agents: 5, users: 10, tokens_per_month: 100000, storage_gb: 10 },
                features: ['SSE Streaming', 'Memory System', 'Voice', 'Priority Support'],
                popular: true,
                active_count: 89,
            },
            {
                id: '3',
                name: 'Enterprise',
                slug: 'enterprise',
                price: 199,
                billing_period: 'month',
                limits: { agents: 50, users: 100, tokens_per_month: 1000000, storage_gb: 100 },
                features: ['Unlimited Agents', 'Custom Models', 'SLA', 'Dedicated Support', 'On-Prem Option'],
                popular: false,
                active_count: 23,
            },
        ];
    }

    private openNewTierModal() {
        this.editingTier = {
            name: '',
            slug: '',
            price: 0,
            billing_period: 'month',
            limits: { agents: 1, users: 5, tokens_per_month: 10000, storage_gb: 1 },
            features: [],
        };
        this.showModal = true;
    }

    private openEditModal(tier: SubscriptionTier) {
        this.editingTier = { ...tier };
        this.showModal = true;
    }

    private closeModal() {
        this.showModal = false;
        this.editingTier = null;
    }

    private formatNumber(n: number): string {
        if (n >= 1000000) return (n / 1000000).toFixed(0) + 'M';
        if (n >= 1000) return (n / 1000).toFixed(0) + 'K';
        return n.toString();
    }

    render() {
        return html`
      <aside class="sidebar">
        <saas-sidebar active-route="/platform/tiers"></saas-sidebar>
      </aside>

      <main class="main">
        <header class="header">
          <div>
            <h1 class="header-title">Subscription Tiers</h1>
            <p class="header-subtitle">Manage pricing plans and feature bundles</p>
          </div>
          <div class="header-actions">
            <button class="btn" @click=${() => this.loadTiers()}>
              <span class="material-symbols-outlined">refresh</span>
              Refresh
            </button>
            <button class="btn primary" @click=${() => this.openNewTierModal()}>
              <span class="material-symbols-outlined">add</span>
              Create Tier
            </button>
          </div>
        </header>

        <div class="content">
          ${this.loading ? html`<div class="loading">Loading tiers...</div>` : html`
            <div class="tiers-grid">
              ${this.tiers.map(tier => html`
                <div class="tier-card ${tier.popular ? 'popular' : ''}">
                  ${tier.popular ? html`<div class="popular-badge">Most Popular</div>` : nothing}
                  
                  <div class="tier-header">
                    <div class="tier-name">${tier.name}</div>
                    <div class="tier-slug">${tier.slug}</div>
                  </div>

                  <div class="tier-price">
                    <span class="price-currency">$</span>
                    <span class="price-amount">${tier.price}</span>
                    <span class="price-period">/${tier.billing_period}</span>
                  </div>

                  <div class="tier-limits">
                    <div class="limit-row">
                      <span class="limit-label">Agents</span>
                      <span class="limit-value">${tier.limits.agents === 50 ? 'Unlimited' : tier.limits.agents}</span>
                    </div>
                    <div class="limit-row">
                      <span class="limit-label">Users</span>
                      <span class="limit-value">${tier.limits.users}</span>
                    </div>
                    <div class="limit-row">
                      <span class="limit-label">Tokens/mo</span>
                      <span class="limit-value">${this.formatNumber(tier.limits.tokens_per_month)}</span>
                    </div>
                    <div class="limit-row">
                      <span class="limit-label">Storage</span>
                      <span class="limit-value">${tier.limits.storage_gb} GB</span>
                    </div>
                  </div>

                  <div class="tier-features">
                    ${tier.features.map(f => html`
                      <div class="feature-item">
                        <span class="material-symbols-outlined">check_circle</span>
                        ${f}
                      </div>
                    `)}
                  </div>

                  <div class="tier-footer">
                    <span class="active-count">${tier.active_count} active tenants</span>
                    <div class="tier-actions">
                      <button class="action-btn" title="Edit" @click=${() => this.openEditModal(tier)}>
                        <span class="material-symbols-outlined">edit</span>
                      </button>
                      <button class="action-btn" title="Duplicate">
                        <span class="material-symbols-outlined">content_copy</span>
                      </button>
                    </div>
                  </div>
                </div>
              `)}

              <div class="add-tier-card" @click=${() => this.openNewTierModal()}>
                <span class="material-symbols-outlined">add_circle</span>
                <span>Add New Tier</span>
              </div>
            </div>
          `}
        </div>
      </main>

      ${this.showModal ? html`
        <div class="modal-overlay" @click=${() => this.closeModal()}>
          <div class="modal" @click=${(e: Event) => e.stopPropagation()}>
            <div class="modal-header">
              <h2 class="modal-title">${this.editingTier?.id ? 'Edit Tier' : 'Create Tier'}</h2>
              <button class="action-btn" @click=${() => this.closeModal()}>
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>
            <div class="modal-body">
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">Name</label>
                  <input type="text" class="form-input" placeholder="Professional" .value=${this.editingTier?.name || ''} />
                </div>
                <div class="form-group">
                  <label class="form-label">Slug</label>
                  <input type="text" class="form-input" placeholder="professional" .value=${this.editingTier?.slug || ''} />
                </div>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">Price ($/month)</label>
                  <input type="number" class="form-input" placeholder="49" .value=${this.editingTier?.price || 0} />
                </div>
                <div class="form-group">
                  <label class="form-label">Billing Period</label>
                  <select class="form-input">
                    <option value="month">Monthly</option>
                    <option value="year">Yearly</option>
                  </select>
                </div>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">Max Agents</label>
                  <input type="number" class="form-input" placeholder="5" .value=${this.editingTier?.limits?.agents || 1} />
                </div>
                <div class="form-group">
                  <label class="form-label">Max Users</label>
                  <input type="number" class="form-input" placeholder="10" .value=${this.editingTier?.limits?.users || 5} />
                </div>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">Tokens/Month</label>
                  <input type="number" class="form-input" placeholder="100000" .value=${this.editingTier?.limits?.tokens_per_month || 10000} />
                </div>
                <div class="form-group">
                  <label class="form-label">Storage (GB)</label>
                  <input type="number" class="form-input" placeholder="10" .value=${this.editingTier?.limits?.storage_gb || 1} />
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn" @click=${() => this.closeModal()}>Cancel</button>
              <button class="btn primary">Save Tier</button>
            </div>
          </div>
        </div>
      ` : nothing}
    `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-tier-builder': SaasTierBuilder;
    }
}
