/**
 * Tenant Settings View
 * Organization profile and configuration.
 *
 * Route: /admin/settings
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Django Ninja API integration
 * - Multi-tab navigation
 *
 * PERSONAS APPLIED:
 * - 🔒 Security Auditor: SSO, MFA policy
 * - 🎨 UX Consultant: Tab organization
 * - 🏗️ Django Architect: Settings structure
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';

import '../components/saas-permission-guard.js';
import '../components/saas-toggle.js';
import '../components/saas-form-field.js';

interface TenantSettings {
    id: string;
    name: string;
    slug: string;
    logoUrl?: string;
    billingEmail: string;
    tier: {
        id: string;
        name: string;
        slug: string;
    };
    status: 'active' | 'suspended' | 'pending';
    quotas: {
        agents: { used: number; limit: number };
        users: { used: number; limit: number };
        storage: { used: number; limit: number };
    };
    branding: {
        primaryColor: string;
        accentColor: string;
        customDomain?: string;
    };
    security: {
        mfaRequired: boolean;
        ssoEnabled: boolean;
        ssoProvider?: string;
        sessionTimeout: number;
    };
    featureOverrides: Record<string, boolean>;
}

type SettingsTab = 'general' | 'branding' | 'security' | 'features' | 'apikeys' | 'danger';

@customElement('saas-tenant-settings')
export class SaasTenantSettings extends LitElement {
    static styles = css`
    :host {
      display: block;
      min-height: 100vh;
      background: var(--saas-bg-page, #f5f5f5);
    }

    .settings-page {
      max-width: 900px;
      margin: 0 auto;
      padding: var(--saas-spacing-xl, 32px);
    }

    .page-header {
      margin-bottom: var(--saas-spacing-lg, 24px);
    }

    .page-title {
      font-size: var(--saas-text-2xl, 24px);
      font-weight: 700;
      color: var(--saas-text-primary, #1a1a1a);
      margin: 0 0 4px;
    }

    .page-subtitle {
      font-size: var(--saas-text-sm, 13px);
      color: var(--saas-text-secondary, #666666);
    }

    /* Tabs */
    .tabs {
      display: flex;
      gap: 4px;
      margin-bottom: var(--saas-spacing-lg, 24px);
      border-bottom: 1px solid var(--saas-border, #e0e0e0);
    }

    .tab {
      padding: 12px 20px;
      font-size: var(--saas-text-sm, 13px);
      font-weight: 500;
      color: var(--saas-text-secondary, #666666);
      background: none;
      border: none;
      border-bottom: 2px solid transparent;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .tab:hover {
      color: var(--saas-text-primary, #1a1a1a);
    }

    .tab.active {
      color: var(--saas-accent, #2563eb);
      border-bottom-color: var(--saas-accent, #2563eb);
    }

    .tab.danger {
      color: #dc2626;
    }

    /* Section */
    .section {
      background: var(--saas-bg-card, #ffffff);
      border: 1px solid var(--saas-border, #e0e0e0);
      border-radius: var(--saas-radius-lg, 12px);
      margin-bottom: var(--saas-spacing-lg, 24px);
    }

    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: var(--saas-spacing-md, 16px) var(--saas-spacing-lg, 24px);
      border-bottom: 1px solid var(--saas-border, #e0e0e0);
    }

    .section-title {
      font-size: var(--saas-text-md, 16px);
      font-weight: 600;
      color: var(--saas-text-primary, #1a1a1a);
    }

    .section-content {
      padding: var(--saas-spacing-lg, 24px);
    }

    /* Form */
    .form-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: var(--saas-spacing-md, 16px);
      margin-bottom: var(--saas-spacing-md, 16px);
    }

    .form-row.single {
      grid-template-columns: 1fr;
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .form-label {
      font-size: var(--saas-text-sm, 13px);
      font-weight: 500;
      color: var(--saas-text-primary, #1a1a1a);
    }

    .form-sublabel {
      font-size: var(--saas-text-xs, 11px);
      color: var(--saas-text-muted, #999999);
    }

    .form-input {
      padding: 10px 12px;
      background: var(--saas-bg-input, #ffffff);
      border: 1px solid var(--saas-border, #e0e0e0);
      border-radius: var(--saas-radius-md, 8px);
      font-size: var(--saas-text-base, 14px);
      color: var(--saas-text-primary, #1a1a1a);
    }

    .form-input:focus {
      outline: none;
      border-color: var(--saas-accent, #2563eb);
    }

    .form-input:disabled {
      background: var(--saas-bg-surface, #fafafa);
      color: var(--saas-text-muted, #999999);
    }

    /* Logo Upload */
    .logo-section {
      display: flex;
      align-items: center;
      gap: var(--saas-spacing-lg, 24px);
    }

    .logo-preview {
      width: 80px;
      height: 80px;
      border-radius: var(--saas-radius-md, 8px);
      background: var(--saas-bg-surface, #fafafa);
      border: 1px dashed var(--saas-border, #e0e0e0);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 32px;
      overflow: hidden;
    }

    .logo-preview img {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }

    /* Quota Display */
    .quota-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: var(--saas-spacing-md, 16px);
    }

    .quota-item {
      background: var(--saas-bg-surface, #fafafa);
      border-radius: var(--saas-radius-md, 8px);
      padding: var(--saas-spacing-md, 16px);
    }

    .quota-label {
      font-size: var(--saas-text-xs, 11px);
      font-weight: 600;
      text-transform: uppercase;
      color: var(--saas-text-muted, #999999);
      margin-bottom: var(--saas-spacing-xs, 4px);
    }

    .quota-value {
      font-size: var(--saas-text-lg, 18px);
      font-weight: 600;
      color: var(--saas-text-primary, #1a1a1a);
    }

    .quota-bar {
      height: 4px;
      background: var(--saas-border, #e0e0e0);
      border-radius: 2px;
      margin-top: var(--saas-spacing-sm, 8px);
      overflow: hidden;
    }

    .quota-fill {
      height: 100%;
      background: var(--saas-accent, #2563eb);
      border-radius: 2px;
      transition: width 0.3s ease;
    }

    .quota-fill.warning {
      background: #f59e0b;
    }

    .quota-fill.danger {
      background: #dc2626;
    }

    /* Tier Badge */
    .tier-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      background: var(--saas-bg-surface, #fafafa);
      border: 1px solid var(--saas-border, #e0e0e0);
      border-radius: var(--saas-radius-md, 8px);
    }

    .tier-name {
      font-weight: 600;
      color: var(--saas-text-primary, #1a1a1a);
    }

    .tier-price {
      font-size: var(--saas-text-sm, 13px);
      color: var(--saas-text-secondary, #666666);
    }

    /* Buttons */
    .btn {
      padding: 10px 20px;
      border-radius: var(--saas-radius-md, 8px);
      font-size: var(--saas-text-sm, 13px);
      font-weight: 500;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .btn-primary {
      background: var(--saas-accent, #2563eb);
      color: white;
      border: none;
    }

    .btn-primary:hover {
      background: #1d4ed8;
    }

    .btn-secondary {
      background: var(--saas-bg-card, #ffffff);
      color: var(--saas-text-primary, #1a1a1a);
      border: 1px solid var(--saas-border, #e0e0e0);
    }

    .btn-secondary:hover {
      background: var(--saas-bg-surface, #fafafa);
    }

    .btn-danger {
      background: #dc2626;
      color: white;
      border: none;
    }

    .btn-danger:hover {
      background: #b91c1c;
    }

    .btn-outline-danger {
      background: transparent;
      color: #dc2626;
      border: 1px solid #dc2626;
    }

    .btn-outline-danger:hover {
      background: #dc2626;
      color: white;
    }

    /* Toggle Row */
    .toggle-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: var(--saas-spacing-md, 16px) 0;
      border-bottom: 1px solid var(--saas-border, #e0e0e0);
    }

    .toggle-row:last-child {
      border-bottom: none;
    }

    .toggle-info {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .toggle-label {
      font-size: var(--saas-text-base, 14px);
      color: var(--saas-text-primary, #1a1a1a);
    }

    .toggle-description {
      font-size: var(--saas-text-xs, 11px);
      color: var(--saas-text-muted, #999999);
    }

    /* Danger Zone */
    .danger-section {
      border-color: #fecaca;
    }

    .danger-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: var(--saas-spacing-md, 16px) 0;
      border-bottom: 1px solid #fecaca;
    }

    .danger-item:last-child {
      border-bottom: none;
    }

    /* Save Bar */
    .save-bar {
      position: sticky;
      bottom: 0;
      background: var(--saas-bg-card, #ffffff);
      border-top: 1px solid var(--saas-border, #e0e0e0);
      padding: var(--saas-spacing-md, 16px) var(--saas-spacing-lg, 24px);
      display: flex;
      justify-content: flex-end;
      gap: var(--saas-spacing-sm, 8px);
    }

    .loading {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: var(--saas-spacing-2xl, 48px);
      color: var(--saas-text-muted, #999999);
    }
  `;

    @state() private settings: TenantSettings | null = null;
    @state() private loading = true;
    @state() private saving = false;
    @state() private activeTab: SettingsTab = 'general';
    @state() private dirty = false;

    connectedCallback() {
        super.connectedCallback();
        this._loadSettings();
    }

    private async _loadSettings() {
        this.loading = true;
        try {
            const token = localStorage.getItem('saas_auth_token');
            const res = await fetch('/api/v2/admin/settings', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.ok) {
                const data = await res.json();
                this.settings = data.data || data;
            } else {
                // Demo data fallback
                this.settings = this._getDemoSettings();
            }
        } catch (e) {
            console.error('Failed to load settings:', e);
            this.settings = this._getDemoSettings();
        } finally {
            this.loading = false;
        }
    }

    private _getDemoSettings(): TenantSettings {
        return {
            id: 'tenant-001',
            name: 'Acme Corporation',
            slug: 'acme-corp',
            billingEmail: 'billing@acme.com',
            tier: { id: 'tier-team', name: 'Team', slug: 'team' },
            status: 'active',
            quotas: {
                agents: { used: 5, limit: 25 },
                users: { used: 45, limit: 50 },
                storage: { used: 12, limit: 50 },
            },
            branding: {
                primaryColor: '#2563eb',
                accentColor: '#3b82f6',
            },
            security: {
                mfaRequired: false,
                ssoEnabled: false,
                sessionTimeout: 30,
            },
            featureOverrides: {},
        };
    }

    private async _saveSettings() {
        if (!this.settings) return;
        this.saving = true;
        try {
            const token = localStorage.getItem('saas_auth_token');
            const res = await fetch('/api/v2/admin/settings', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.settings),
            });

            if (res.ok) {
                this.dirty = false;
                this.dispatchEvent(new CustomEvent('show-toast', {
                    detail: { type: 'success', message: 'Settings saved successfully' },
                    bubbles: true,
                    composed: true,
                }));
            }
        } catch (e) {
            console.error('Failed to save:', e);
        } finally {
            this.saving = false;
        }
    }

    private _updateSetting(path: string, value: any) {
        if (!this.settings) return;
        const parts = path.split('.');
        let obj: any = this.settings;
        for (let i = 0; i < parts.length - 1; i++) {
            obj = obj[parts[i]];
        }
        obj[parts[parts.length - 1]] = value;
        this.dirty = true;
        this.requestUpdate();
    }

    private _getQuotaClass(used: number, limit: number): string {
        const pct = (used / limit) * 100;
        if (pct >= 90) return 'danger';
        if (pct >= 75) return 'warning';
        return '';
    }

    render() {
        if (this.loading) {
            return html`<div class="loading">Loading settings...</div>`;
        }

        if (!this.settings) {
            return html`<div class="loading">Failed to load settings</div>`;
        }

        return html`
      <div class="settings-page">
        <div class="page-header">
          <h1 class="page-title">🟠 Tenant Settings</h1>
          <p class="page-subtitle">Manage your organization profile and configuration</p>
        </div>

        <div class="tabs">
          <button class="tab ${this.activeTab === 'general' ? 'active' : ''}" 
                  @click=${() => this.activeTab = 'general'}>General</button>
          <button class="tab ${this.activeTab === 'branding' ? 'active' : ''}"
                  @click=${() => this.activeTab = 'branding'}>Branding</button>
          <button class="tab ${this.activeTab === 'security' ? 'active' : ''}"
                  @click=${() => this.activeTab = 'security'}>Security</button>
          <button class="tab ${this.activeTab === 'features' ? 'active' : ''}"
                  @click=${() => this.activeTab = 'features'}>Features</button>
          <button class="tab ${this.activeTab === 'apikeys' ? 'active' : ''}"
                  @click=${() => this.activeTab = 'apikeys'}>API Keys</button>
          <button class="tab danger ${this.activeTab === 'danger' ? 'active' : ''}"
                  @click=${() => this.activeTab = 'danger'}>Danger Zone</button>
        </div>

        ${this.activeTab === 'general' ? this._renderGeneralTab() : ''}
        ${this.activeTab === 'branding' ? this._renderBrandingTab() : ''}
        ${this.activeTab === 'security' ? this._renderSecurityTab() : ''}
        ${this.activeTab === 'features' ? this._renderFeaturesTab() : ''}
        ${this.activeTab === 'apikeys' ? this._renderApiKeysTab() : ''}
        ${this.activeTab === 'danger' ? this._renderDangerTab() : ''}

        ${this.dirty ? html`
          <div class="save-bar">
            <button class="btn btn-secondary" @click=${() => this._loadSettings()}>Cancel</button>
            <button class="btn btn-primary" ?disabled=${this.saving} @click=${this._saveSettings}>
              ${this.saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        ` : ''}
      </div>
    `;
    }

    private _renderGeneralTab() {
        const s = this.settings!;
        return html`
      <div class="section">
        <div class="section-header">
          <span class="section-title">Organization Profile</span>
        </div>
        <div class="section-content">
          <div class="logo-section" style="margin-bottom: 24px;">
            <div class="logo-preview">
              ${s.logoUrl ? html`<img src="${s.logoUrl}" alt="Logo">` : '📁'}
            </div>
            <div>
              <button class="btn btn-secondary">Upload Logo</button>
              <p class="form-sublabel" style="margin-top: 8px;">Recommended: 256x256 PNG, max 500KB</p>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Organization Name *</label>
              <input class="form-input" type="text" .value=${s.name}
                     @input=${(e: Event) => this._updateSetting('name', (e.target as HTMLInputElement).value)}>
            </div>
            <div class="form-group">
              <label class="form-label">URL Slug</label>
              <input class="form-input" type="text" .value=${s.slug} disabled>
              <span class="form-sublabel">Cannot be changed after creation</span>
            </div>
          </div>

          <div class="form-row single">
            <div class="form-group">
              <label class="form-label">Billing Email *</label>
              <input class="form-input" type="email" .value=${s.billingEmail}
                     @input=${(e: Event) => this._updateSetting('billingEmail', (e.target as HTMLInputElement).value)}>
            </div>
          </div>
        </div>
      </div>

      <div class="section">
        <div class="section-header">
          <span class="section-title">Subscription</span>
          <button class="btn btn-secondary">Upgrade Plan</button>
        </div>
        <div class="section-content">
          <div class="tier-badge" style="margin-bottom: 24px;">
            <span class="tier-name">🟡 ${s.tier.name}</span>
            <span class="tier-price">$99/month</span>
            <span style="color: #22c55e;">✅ Active</span>
          </div>

          <div class="quota-grid">
            <div class="quota-item">
              <div class="quota-label">Agents</div>
              <div class="quota-value">${s.quotas.agents.used}/${s.quotas.agents.limit}</div>
              <div class="quota-bar">
                <div class="quota-fill ${this._getQuotaClass(s.quotas.agents.used, s.quotas.agents.limit)}"
                     style="width: ${(s.quotas.agents.used / s.quotas.agents.limit) * 100}%"></div>
              </div>
            </div>
            <div class="quota-item">
              <div class="quota-label">Users</div>
              <div class="quota-value">${s.quotas.users.used}/${s.quotas.users.limit}</div>
              <div class="quota-bar">
                <div class="quota-fill ${this._getQuotaClass(s.quotas.users.used, s.quotas.users.limit)}"
                     style="width: ${(s.quotas.users.used / s.quotas.users.limit) * 100}%"></div>
              </div>
            </div>
            <div class="quota-item">
              <div class="quota-label">Storage (GB)</div>
              <div class="quota-value">${s.quotas.storage.used}/${s.quotas.storage.limit}</div>
              <div class="quota-bar">
                <div class="quota-fill ${this._getQuotaClass(s.quotas.storage.used, s.quotas.storage.limit)}"
                     style="width: ${(s.quotas.storage.used / s.quotas.storage.limit) * 100}%"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
    }

    private _renderBrandingTab() {
        const s = this.settings!;
        return html`
      <div class="section">
        <div class="section-header">
          <span class="section-title">Brand Colors</span>
        </div>
        <div class="section-content">
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Primary Color</label>
              <div style="display: flex; gap: 8px; align-items: center;">
                <input type="color" .value=${s.branding.primaryColor}
                       @input=${(e: Event) => this._updateSetting('branding.primaryColor', (e.target as HTMLInputElement).value)}>
                <input class="form-input" type="text" .value=${s.branding.primaryColor} style="flex: 1;">
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">Accent Color</label>
              <div style="display: flex; gap: 8px; align-items: center;">
                <input type="color" .value=${s.branding.accentColor}
                       @input=${(e: Event) => this._updateSetting('branding.accentColor', (e.target as HTMLInputElement).value)}>
                <input class="form-input" type="text" .value=${s.branding.accentColor} style="flex: 1;">
              </div>
            </div>
          </div>
        </div>
      </div>

      <saas-permission-guard permission="tenant:custom_domain" fallback="message">
        <div class="section">
          <div class="section-header">
            <span class="section-title">Custom Domain</span>
          </div>
          <div class="section-content">
            <div class="form-row single">
              <div class="form-group">
                <label class="form-label">Custom Domain</label>
                <input class="form-input" type="text" placeholder="agents.yourcompany.com"
                       .value=${s.branding.customDomain || ''}>
                <span class="form-sublabel">Requires DNS CNAME setup. Contact support for instructions.</span>
              </div>
            </div>
          </div>
        </div>
      </saas-permission-guard>
    `;
    }

    private _renderSecurityTab() {
        const s = this.settings!;
        return html`
      <div class="section">
        <div class="section-header">
          <span class="section-title">Authentication</span>
        </div>
        <div class="section-content">
          <div class="toggle-row">
            <div class="toggle-info">
              <span class="toggle-label">Require MFA for all users</span>
              <span class="toggle-description">Users must set up 2FA before accessing the platform</span>
            </div>
            <saas-toggle
              ?checked=${s.security.mfaRequired}
              @change=${(e: CustomEvent) => this._updateSetting('security.mfaRequired', e.detail.checked)}
            ></saas-toggle>
          </div>

          <div class="toggle-row">
            <div class="toggle-info">
              <span class="toggle-label">Enable SSO (Enterprise)</span>
              <span class="toggle-description">Allow users to sign in with your identity provider</span>
            </div>
            <saas-toggle
              ?checked=${s.security.ssoEnabled}
              @change=${(e: CustomEvent) => this._updateSetting('security.ssoEnabled', e.detail.checked)}
            ></saas-toggle>
          </div>

          <div class="form-row" style="margin-top: 16px;">
            <div class="form-group">
              <label class="form-label">Session Timeout (minutes)</label>
              <select class="form-input" .value=${String(s.security.sessionTimeout)}
                      @change=${(e: Event) => this._updateSetting('security.sessionTimeout', parseInt((e.target as HTMLSelectElement).value))}>
                <option value="15">15 minutes</option>
                <option value="30">30 minutes</option>
                <option value="60">1 hour</option>
                <option value="120">2 hours</option>
                <option value="480">8 hours</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    `;
    }

    private _renderFeaturesTab() {
        return html`
      <div class="section">
        <div class="section-header">
          <span class="section-title">Feature Overrides</span>
        </div>
        <div class="section-content">
          <p style="color: var(--saas-text-secondary); margin-bottom: 16px;">
            Toggle features for your organization. You can only disable features included in your tier, not enable new ones.
          </p>

          <div class="toggle-row">
            <div class="toggle-info">
              <span class="toggle-label">Memory</span>
              <span class="toggle-description">Long-term agent memory with SomaBrain</span>
            </div>
            <span style="color: #22c55e;">✅ Enabled by Tier</span>
          </div>

          <div class="toggle-row">
            <div class="toggle-info">
              <span class="toggle-label">Voice</span>
              <span class="toggle-description">Speech-to-text and text-to-speech capabilities</span>
            </div>
            <span style="color: #22c55e;">✅ Enabled by Tier</span>
          </div>

          <div class="toggle-row">
            <div class="toggle-info">
              <span class="toggle-label">MCP Tools</span>
              <span class="toggle-description">Connect external tools via MCP protocol</span>
            </div>
            <span style="color: #22c55e;">✅ Enabled by Tier</span>
          </div>

          <div class="toggle-row">
            <div class="toggle-info">
              <span class="toggle-label">Agent Delegation</span>
              <span class="toggle-description">Allow agents to spawn sub-agents</span>
            </div>
            <span style="color: var(--saas-text-muted);">⚪ Not in Tier (Enterprise)</span>
          </div>
        </div>
      </div>
    `;
    }

    private _renderApiKeysTab() {
        return html`
      <saas-permission-guard permission="apikey:read" fallback="message">
        <div class="section">
          <div class="section-header">
            <span class="section-title">API Keys</span>
            <button class="btn btn-primary">+ Create Key</button>
          </div>
          <div class="section-content">
            <p style="color: var(--saas-text-secondary);">
              API keys allow programmatic access to your tenant's resources.
            </p>
            <div style="text-align: center; padding: 48px; color: var(--saas-text-muted);">
              No API keys created yet. Click "Create Key" to generate one.
            </div>
          </div>
        </div>
      </saas-permission-guard>
    `;
    }

    private _renderDangerTab() {
        return html`
      <div class="section danger-section" style="border-color: #fecaca;">
        <div class="section-header" style="background: #fef2f2;">
          <span class="section-title" style="color: #dc2626;">⚠️ Danger Zone</span>
        </div>
        <div class="section-content">
          <div class="danger-item">
            <div>
              <div style="font-weight: 600; margin-bottom: 4px;">Export All Data</div>
              <div style="font-size: 12px; color: var(--saas-text-secondary);">
                Download all organization data including users, agents, and conversations.
              </div>
            </div>
            <button class="btn btn-outline-danger">Export Data</button>
          </div>

          <div class="danger-item">
            <div>
              <div style="font-weight: 600; margin-bottom: 4px;">Archive Organization</div>
              <div style="font-size: 12px; color: var(--saas-text-secondary);">
                Disable all access but retain data. Can be reactivated by SAAS Admin.
              </div>
            </div>
            <button class="btn btn-outline-danger">Archive</button>
          </div>

          <div class="danger-item">
            <div>
              <div style="font-weight: 600; margin-bottom: 4px;">Delete Organization</div>
              <div style="font-size: 12px; color: var(--saas-text-secondary);">
                Permanently delete this organization and all associated data. This cannot be undone.
              </div>
            </div>
            <button class="btn btn-danger">Delete Organization</button>
          </div>
        </div>
      </div>
    `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-tenant-settings': SaasTenantSettings;
    }
}
