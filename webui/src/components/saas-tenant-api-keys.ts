/**
 * Tenant API Keys Tab
 * Renders API key management placeholder.
 */

import { LitElement, html, css } from 'lit';
import { customElement } from 'lit/decorators.js';
import '../components/saas-permission-guard.js';

@customElement('saas-tenant-api-keys')
export class SaasTenantApiKeys extends LitElement {
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

    .btn {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 10px 20px;
      border-radius: var(--saas-radius-md, 8px);
      font-size: var(--saas-text-sm, 13px);
      font-weight: 500;
      cursor: pointer;
      transition: all 0.15s ease;
      border: none;
    }

    .btn-primary {
      background: var(--saas-accent, #2563eb);
      color: white;
    }

    .btn-primary:hover {
      background: #1d4ed8;
    }
  `;

  render() {
    return html`
      <saas-permission-guard permission="apikey:read" fallback="message">
        <div class="section">
          <div class="section-header">
            <span class="section-title">API Keys</span>
            <button class="btn btn-primary">
              <span class="material-symbols-outlined">add</span> Create Key
            </button>
          </div>
          <div class="section-content">
            <p style="color: var(--saas-text-secondary);">
              API keys allow programmatic access to your tenant's resources.
            </p>
            <div
              style="text-align: center; padding: 48px; color: var(--saas-text-muted);"
            >
              No API keys created yet. Click "Create Key" to generate one.
            </div>
          </div>
        </div>
      </saas-permission-guard>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'saas-tenant-api-keys': SaasTenantApiKeys;
  }
}
