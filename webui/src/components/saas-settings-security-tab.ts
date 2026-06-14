/**
 * Settings Security Tab
 * API keys and MCP configuration.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { FeatureFlags } from '../controllers/settings-controller.js';

export interface FeatureFlagChangeDetail {
  flag: keyof FeatureFlags;
}

@customElement('saas-settings-security-tab')
export class SaasSettingsSecurityTab extends LitElement {
  static styles = css`
    :host {
      display: block;
    }

    * {
      box-sizing: border-box;
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
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 20px;
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

    .section-desc {
      font-size: 13px;
      color: var(--saas-text-secondary, #666);
      margin-bottom: 20px;
    }

    /* API Key Row */
    .api-key-row {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px;
      background: var(--saas-bg-hover, #fafafa);
      border-radius: 8px;
      margin-bottom: 12px;
    }

    .api-key-row:last-child {
      margin-bottom: 0;
    }

    .api-key-name {
      flex: 1;
      font-size: 14px;
      font-weight: 500;
    }

    .api-key-value {
      flex: 2;
      font-family: monospace;
      font-size: 13px;
      color: var(--saas-text-secondary, #666);
    }

    .api-key-status {
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 600;
    }

    .api-key-status.active {
      background: #d1fae5;
      color: #047857;
    }

    .api-key-status.missing {
      background: #fee2e2;
      color: #b91c1c;
    }

    .api-key-action {
      padding: 6px 12px;
      border-radius: 6px;
      border: 1px solid var(--saas-border-light, #e0e0e0);
      background: white;
      font-size: 12px;
      cursor: pointer;
      transition: all 0.1s ease;
    }

    .api-key-action:hover {
      border-color: var(--saas-border-medium, #ccc);
    }

    /* Add button */
    .add-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      width: 100%;
      padding: 12px;
      border: 2px dashed var(--saas-border-light, #e0e0e0);
      border-radius: 8px;
      background: transparent;
      color: var(--saas-text-secondary, #666);
      font-size: 14px;
      cursor: pointer;
      transition: all 0.1s ease;
    }

    .add-btn:hover {
      border-color: var(--saas-border-medium, #ccc);
      color: var(--saas-text-primary, #1a1a1a);
    }

    /* Toggle Switch */
    .toggle-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 0;
      border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
    }

    .toggle-row:last-child {
      border-bottom: none;
    }

    .toggle-label {
      font-size: 14px;
    }

    .toggle-desc {
      font-size: 12px;
      color: var(--saas-text-secondary, #666);
      margin-top: 4px;
    }

    .toggle-switch {
      position: relative;
      width: 44px;
      height: 24px;
    }

    .toggle-switch input {
      opacity: 0;
      width: 0;
      height: 0;
    }

    .toggle-slider {
      position: absolute;
      cursor: pointer;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-color: var(--saas-border-light, #e0e0e0);
      transition: 0.2s;
      border-radius: 24px;
    }

    .toggle-slider:before {
      position: absolute;
      content: "";
      height: 18px;
      width: 18px;
      left: 3px;
      bottom: 3px;
      background-color: white;
      transition: 0.2s;
      border-radius: 50%;
    }

    .toggle-switch input:checked + .toggle-slider {
      background-color: #1a1a1a;
    }

    .toggle-switch input:checked + .toggle-slider:before {
      transform: translateX(20px);
    }
  `;

  @property({ type: Object })
  featureFlags!: FeatureFlags;

  render() {
    return html`
      <!-- API Keys -->
      <div class="section">
        <h3 class="section-title">
          <span class="material-symbols-outlined">vpn_key</span>
          API Keys
        </h3>
        <p class="section-desc">Manage external service credentials.</p>

        <div class="api-key-row">
          <span class="api-key-name">OpenAI</span>
          <span class="api-key-value">sk-****...****aBcD</span>
          <span class="api-key-status active">Active</span>
          <button class="api-key-action">Edit</button>
        </div>
        <div class="api-key-row">
          <span class="api-key-name">Anthropic</span>
          <span class="api-key-value">sk-ant-****...****xYz</span>
          <span class="api-key-status active">Active</span>
          <button class="api-key-action">Edit</button>
        </div>
        <div class="api-key-row">
          <span class="api-key-name">Serper (Search)</span>
          <span class="api-key-value">—</span>
          <span class="api-key-status missing">Missing</span>
          <button class="api-key-action">Add</button>
        </div>

        <button class="add-btn">
          <span class="material-symbols-outlined">add</span>
          Add API Key
        </button>
      </div>

      <!-- MCP Configuration -->
      <div class="section">
        <h3 class="section-title">
          <span class="material-symbols-outlined">hub</span>
          MCP Configuration
        </h3>
        <p class="section-desc">Model Context Protocol connections.</p>

        <div class="toggle-row">
          <div>
            <div class="toggle-label">MCP Client</div>
            <div class="toggle-desc">Connect to external MCP servers</div>
          </div>
          <label class="toggle-switch">
            <input
              type="checkbox"
              .checked=${this.featureFlags.mcpEnabled}
              @change=${() => this._emitFlagChange('mcpEnabled')}
            />
            <span class="toggle-slider"></span>
          </label>
        </div>

        <button class="add-btn" style="margin-top: 16px;">
          <span class="material-symbols-outlined">add</span>
          Add MCP Server
        </button>
      </div>
    `;
  }

  private _emitFlagChange(flag: keyof FeatureFlags): void {
    this.dispatchEvent(
      new CustomEvent<FeatureFlagChangeDetail>('feature-flag-change', {
        detail: { flag },
        bubbles: true,
        composed: true,
      })
    );
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'saas-settings-security-tab': SaasSettingsSecurityTab;
  }
}
