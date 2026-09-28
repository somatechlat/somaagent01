/**
 * Tenant Security & Branding Settings Tab
 * Renders brand color / custom domain and authentication settings.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { TenantSettings } from '../controllers/tenant-settings-controller.js';
import '../components/saas-permission-guard.js';
import '../components/saas-toggle.js';

export interface TenantSettingChangeDetail {
  path: string;
  value: unknown;
}

@customElement('saas-tenant-security-settings')
export class SaasTenantSecuritySettings extends LitElement {
  static styles = css`
    :host {
      display: block;
    }

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

    .form-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: var(--saas-spacing-md, 16px);
      margin-bottom: var(--saas-spacing-md, 16px);
    }

    .form-row.single {
      grid-template-columns: 1fr;
    }

    .form-row:last-child {
      margin-bottom: 0;
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
  `;

  @property({ type: Object })
  settings!: TenantSettings;

  @property({ type: String })
  activeTab: 'branding' | 'security' = 'security';

  render() {
    return html`
      ${this.activeTab === 'branding' ? this._renderBranding() : ''}
      ${this.activeTab === 'security' ? this._renderSecurity() : ''}
    `;
  }

  private _renderBranding() {
    const s = this.settings;
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
                <input
                  type="color"
                  .value=${s.branding.primaryColor}
                  @input=${(e: Event) =>
                    this._emitChange(
                      'branding.primaryColor',
                      (e.target as HTMLInputElement).value
                    )}
                />
                <input
                  class="form-input"
                  type="text"
                  .value=${s.branding.primaryColor}
                  style="flex: 1;"
                />
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">Accent Color</label>
              <div style="display: flex; gap: 8px; align-items: center;">
                <input
                  type="color"
                  .value=${s.branding.accentColor}
                  @input=${(e: Event) =>
                    this._emitChange(
                      'branding.accentColor',
                      (e.target as HTMLInputElement).value
                    )}
                />
                <input
                  class="form-input"
                  type="text"
                  .value=${s.branding.accentColor}
                  style="flex: 1;"
                />
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
                <input
                  class="form-input"
                  type="text"
                  placeholder="agents.yourcompany.com"
                  .value=${s.branding.customDomain || ''}
                />
                <span class="form-sublabel"
                  >Requires DNS CNAME setup. Contact support for
                  instructions.</span
                >
              </div>
            </div>
          </div>
        </div>
      </saas-permission-guard>
    `;
  }

  private _renderSecurity() {
    const s = this.settings;
    return html`
      <div class="section">
        <div class="section-header">
          <span class="section-title">Authentication</span>
        </div>
        <div class="section-content">
          <div class="toggle-row">
            <div class="toggle-info">
              <span class="toggle-label">Require MFA for all users</span>
              <span class="toggle-description"
                >Users must set up 2FA before accessing the platform</span
              >
            </div>
            <saas-toggle
              ?checked=${s.security.mfaRequired}
              @change=${(e: CustomEvent) =>
                this._emitChange('security.mfaRequired', e.detail.checked)}
            ></saas-toggle>
          </div>

          <div class="toggle-row">
            <div class="toggle-info">
              <span class="toggle-label">Enable SSO (Enterprise)</span>
              <span class="toggle-description"
                >Allow users to sign in with your identity provider</span
              >
            </div>
            <saas-toggle
              ?checked=${s.security.ssoEnabled}
              @change=${(e: CustomEvent) =>
                this._emitChange('security.ssoEnabled', e.detail.checked)}
            ></saas-toggle>
          </div>

          <div class="form-row" style="margin-top: 16px;">
            <div class="form-group">
              <label class="form-label">Session Timeout (minutes)</label>
              <select
                class="form-input"
                .value=${String(s.security.sessionTimeout)}
                @change=${(e: Event) =>
                  this._emitChange(
                    'security.sessionTimeout',
                    parseInt((e.target as HTMLSelectElement).value)
                  )}
              >
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

  private _emitChange(path: string, value: unknown): void {
    this.dispatchEvent(
      new CustomEvent<TenantSettingChangeDetail>('tenant-setting-change', {
        detail: { path, value },
        bubbles: true,
        composed: true,
      })
    );
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'saas-tenant-security-settings': SaasTenantSecuritySettings;
  }
}
