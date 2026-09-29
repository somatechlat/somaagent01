/**
 * Tenant Settings View
 * Organization profile, subscription, and lifecycle actions.
 *
 * Route: /admin/settings
 *
 * Every control here is backed by a real endpoint:
 * - profile fields → `PATCH /aaas/tenants/{id}`
 * - plan change    → `POST /aaas/billing/tenant/{id}/upgrade`
 * - archive        → `POST /aaas/tenants/{id}/suspend`
 * - delete         → `DELETE /aaas/tenants/{id}` (soft: status becomes churned)
 *
 * There is no organization-data export endpoint in this system, so no export
 * control is rendered. Fabricating one that downloads nothing would be worse
 * than not offering it.
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import {
  TenantSettingsController,
  type SettingsTab,
} from '../controllers/tenant-settings-controller.js';
import type {
  TenantSettingChangeDetail,
  TenantPlanChangeDetail,
} from '../components/saas-tenant-general-settings.js';

import '../components/saas-tenant-general-settings.js';

@customElement('saas-tenant-settings')
export class SaasTenantSettings extends LitElement {
  static styles = css`
    .status-icon {
      font-size: 8px;
      line-height: 1;
      vertical-align: middle;
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

  private controller = new TenantSettingsController(this);

  @state()
  private activeTab: SettingsTab = 'general';

  connectedCallback() {
    super.connectedCallback();
    this.controller.loadSettings();
  }

  render() {
    if (this.controller.loading) {
      return html`<div class="loading">Loading settings...</div>`;
    }

    if (!this.controller.settings) {
      return html`<div class="loading">Failed to load settings</div>`;
    }

    const s = this.controller.settings;

    return html`
      <div class="settings-page">
        <div class="page-header">
          <h1 class="page-title">
            <span class="material-symbols-outlined">domain</span> Tenant
            Settings
          </h1>
          <p class="page-subtitle">
            Manage your organization profile and configuration
          </p>
        </div>

        <div class="tabs">
          <button
            class="tab ${this.activeTab === 'general' ? 'active' : ''}"
            @click=${() => (this.activeTab = 'general')}
          >
            General
          </button>
          <button
            class="tab danger ${this.activeTab === 'danger' ? 'active' : ''}"
            @click=${() => (this.activeTab = 'danger')}
          >
            Danger Zone
          </button>
        </div>

        ${this.activeTab === 'general'
          ? html`
              <saas-tenant-general-settings
                .settings=${s}
                .tiers=${this.controller.tiers}
                .busy=${this.controller.busy}
                @tenant-setting-change=${this._onSettingChange}
                @tenant-plan-change=${this._onPlanChange}
              ></saas-tenant-general-settings>
            `
          : ''}
        ${this.activeTab === 'danger' ? this._renderDangerTab() : ''}

        ${this.controller.dirty
          ? html`
              <div class="save-bar">
                <button
                  class="btn btn-secondary"
                  @click=${() => this.controller.loadSettings()}
                >
                  Cancel
                </button>
                <button
                  class="btn btn-primary"
                  ?disabled=${this.controller.saving}
                  @click=${() => this.controller.saveSettings()}
                >
                  ${this.controller.saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            `
          : ''}
      </div>
    `;
  }

  private _onSettingChange(e: CustomEvent<TenantSettingChangeDetail>) {
    e.stopPropagation();
    this.controller.updateSetting(e.detail.path, e.detail.value);
  }

  private _renderDangerTab() {
    const s = this.controller.settings;
    const busy = this.controller.busy;
    return html`
      <div class="section danger-section" style="border-color: #fecaca;">
        <div class="section-header" style="background: #fef2f2;">
          <span class="section-title" style="color: #dc2626;"
            ><span class="material-symbols-outlined">warning</span> Danger
            Zone</span
          >
        </div>
        <div class="section-content">
          <div class="danger-item">
            <div>
              <div style="font-weight: 600; margin-bottom: 4px;">
                Archive Organization
              </div>
              <div style="font-size: 12px; color: var(--saas-text-secondary);">
                Suspend access and pause every agent under
                ${s?.name ?? 'this organization'}. Data is retained and the
                organization can be reactivated.
              </div>
            </div>
            <button
              class="btn btn-outline-danger"
              ?disabled=${busy ||
              s?.status === 'suspended' ||
              s?.status === 'churned'}
              @click=${this._onArchive}
            >
              ${busy ? 'Working...' : 'Archive'}
            </button>
          </div>

          <div class="danger-item">
            <div>
              <div style="font-weight: 600; margin-bottom: 4px;">
                Delete Organization
              </div>
              <div style="font-size: 12px; color: var(--saas-text-secondary);">
                Marks this organization as churned. The record is kept for
                billing history and is not erased — this cannot be undone from
                here.
              </div>
            </div>
            <button
              class="btn btn-danger"
              ?disabled=${busy || s?.status === 'churned'}
              @click=${this._onDelete}
            >
              ${busy ? 'Working...' : 'Delete Organization'}
            </button>
          </div>
        </div>
      </div>
    `;
  }

  private _onPlanChange = (e: CustomEvent<TenantPlanChangeDetail>) => {
    e.stopPropagation();
    const { tierId } = e.detail;
    const s = this.controller.settings;
    const target = this.controller.tiers.find((t) => t.id === tierId);
    if (!target) return;
    const current = s?.tier.name ?? s?.tier.slug ?? 'the current plan';
    if (
      !confirm(
        `Change ${s?.name ?? 'this organization'} from ${current} to ${target.name}?`
      )
    ) {
      return;
    }
    void this.controller.upgradeTier(tierId);
  };

  private _onArchive = () => {
    const s = this.controller.settings;
    if (
      !confirm(
        `Archive ${s?.name ?? 'this organization'}? All agents under it will be paused and access disabled.`
      )
    ) {
      return;
    }
    void this.controller.suspendTenant();
  };

  private _onDelete = () => {
    const s = this.controller.settings;
    if (
      !confirm(
        `Delete ${s?.name ?? 'this organization'}? It will be marked as churned. This cannot be undone from here.`
      )
    ) {
      return;
    }
    void this.controller.deleteTenant();
  };
}

declare global {
  interface HTMLElementTagNameMap {
    'saas-tenant-settings': SaasTenantSettings;
  }
}
