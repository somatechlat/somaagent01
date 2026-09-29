/**
 * Tenant General Settings Tab
 * Renders organization profile and billing summary.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type {
  TenantQuota,
  TenantSettings,
} from '../controllers/tenant-settings-controller.js';
export interface TenantSettingChangeDetail {
  path: string;
  value: unknown;
}

@customElement('saas-tenant-general-settings')
export class SaasTenantGeneralSettings extends LitElement {
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

    .logo-section {
      display: flex;
      align-items: center;
      gap: var(--saas-spacing-lg, 24px);
      margin-bottom: 24px;
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

    .btn {
      padding: 10px 20px;
      border-radius: var(--saas-radius-md, 8px);
      font-size: var(--saas-text-sm, 13px);
      font-weight: 500;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .btn-secondary {
      background: var(--saas-bg-card, #ffffff);
      color: var(--saas-text-primary, #1a1a1a);
      border: 1px solid var(--saas-border, #e0e0e0);
    }

    .btn-secondary:hover {
      background: var(--saas-bg-surface, #fafafa);
    }

    .status-icon {
      font-size: 8px;
      line-height: 1;
      vertical-align: middle;
    }

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
  `;

  @property({ type: Object })
  settings!: TenantSettings;

  render() {
    const s = this.settings;
    return html`
      <div class="section">
        <div class="section-header">
          <span class="section-title">Organization Profile</span>
        </div>
        <div class="section-content">
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Organization Name *</label>
              <input
                class="form-input"
                type="text"
                .value=${s.name}
                @input=${(e: Event) =>
                  this._emitChange(
                    'name',
                    (e.target as HTMLInputElement).value
                  )}
              />
            </div>
            <div class="form-group">
              <label class="form-label">URL Slug</label>
              <input
                class="form-input"
                type="text"
                .value=${s.slug}
                disabled
              />
              <span class="form-sublabel">Cannot be changed after creation</span>
            </div>
          </div>

          <div class="form-row single">
            <div class="form-group">
              <label class="form-label">Billing Email *</label>
              <input
                class="form-input"
                type="email"
                .value=${s.billingEmail ?? ''}
                @input=${(e: Event) =>
                  this._emitChange(
                    'billingEmail',
                    (e.target as HTMLInputElement).value
                  )}
              />
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
            <span class="tier-name"
              ><span
                class="material-symbols-outlined status-icon"
                style="color: #eab308;"
                >circle</span
              >
              ${s.tier.name}</span
            >
            <span class="tier-price"
              >${s.mrr > 0
                ? `$${s.mrr.toLocaleString('en-US', {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 2,
                  })}/month`
                : '—'}</span
            >
            <span style="color: #22c55e;"
              ><span class="material-symbols-outlined" style="font-size: 12px;"
                >check_circle</span
              >
              Active</span
            >
          </div>

          <div class="quota-grid">
            ${this._renderQuota('Agents', s.quotas.agents)}
            ${this._renderQuota('Users', s.quotas.users)}
          </div>
        </div>
      </div>
    `;
  }

  /**
   * One usage counter.
   *
   * TenantOut reports the live counts but no per-resource ceiling, so `limit`
   * is null. Drawing `3/0` and a bar that divides by zero would invent a
   * quota the system does not have — the ceiling is shown as — and no bar is
   * drawn, exactly as an unmeasured figure should be.
   */
  private _renderQuota(label: string, q: TenantQuota) {
    const hasCeiling = typeof q.limit === 'number' && q.limit > 0;
    return html`
      <div class="quota-item">
        <div class="quota-label">${label}</div>
        <div class="quota-value">
          ${q.used}${hasCeiling ? `/${q.limit}` : ''}
          ${hasCeiling ? '' : html`<span style="color: var(--saas-text-muted, #999)">&nbsp;— no ceiling</span>`}
        </div>
        ${hasCeiling
          ? html`
              <div class="quota-bar">
                <div
                  class="quota-fill ${this._getQuotaClass(q.used, q.limit as number)}"
                  style="width: ${Math.min(100, (q.used / (q.limit as number)) * 100)}%"
                ></div>
              </div>
            `
          : ''}
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

  private _getQuotaClass(used: number, limit: number): string {
    const pct = (used / limit) * 100;
    if (pct >= 90) return 'danger';
    if (pct >= 75) return 'warning';
    return '';
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'saas-tenant-general-settings': SaasTenantGeneralSettings;
  }
}
