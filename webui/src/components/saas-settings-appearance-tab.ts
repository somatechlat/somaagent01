/**
 * Settings Appearance Tab
 * Feature flags, backup/export, and danger zone.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { FeatureFlags } from '../controllers/settings-controller.js';

export interface FeatureFlagChangeDetail {
  flag: keyof FeatureFlags;
}

@customElement('saas-settings-appearance-tab')
export class SaasSettingsAppearanceTab extends LitElement {
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

    /* Danger zone */
    .danger-zone {
      border-color: var(--saas-status-danger, #ef4444);
    }

    .danger-zone .section-title {
      color: var(--saas-status-danger, #ef4444);
    }

    .danger-btn {
      padding: 10px 20px;
      border-radius: 8px;
      background: var(--saas-status-danger, #ef4444);
      color: white;
      border: none;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.1s ease;
    }

    .danger-btn:hover {
      background: #dc2626;
    }
  `;

  @property({ type: Object })
  featureFlags!: FeatureFlags;

  render() {
    return html`
      <!-- Feature Flags -->
      <div class="section">
        <h3 class="section-title">
          <span class="material-symbols-outlined">toggle_on</span>
          Feature Flags
        </h3>
        <p class="section-desc">Enable or disable agent capabilities.</p>

        <div class="toggle-row">
          <div>
            <div class="toggle-label">Memory</div>
            <div class="toggle-desc">Enable SomaBrain memory integration</div>
          </div>
          <label class="toggle-switch">
            <input
              type="checkbox"
              .checked=${this.featureFlags.memoryEnabled}
              @change=${() => this._emitFlagChange('memoryEnabled')}
            />
            <span class="toggle-slider"></span>
          </label>
        </div>

        <div class="toggle-row">
          <div>
            <div class="toggle-label">Tools</div>
            <div class="toggle-desc">Enable tool execution</div>
          </div>
          <label class="toggle-switch">
            <input
              type="checkbox"
              .checked=${this.featureFlags.toolsEnabled}
              @change=${() => this._emitFlagChange('toolsEnabled')}
            />
            <span class="toggle-slider"></span>
          </label>
        </div>

        <div class="toggle-row">
          <div>
            <div class="toggle-label">Voice</div>
            <div class="toggle-desc">Enable voice interaction</div>
          </div>
          <label class="toggle-switch">
            <input
              type="checkbox"
              .checked=${this.featureFlags.voiceEnabled}
              @change=${() => this._emitFlagChange('voiceEnabled')}
            />
            <span class="toggle-slider"></span>
          </label>
        </div>
      </div>

      <!-- Backup & Restore -->
      <div class="section">
        <h3 class="section-title">
          <span class="material-symbols-outlined">backup</span>
          Backup & Restore
        </h3>
        <p class="section-desc">Export and import agent configuration.</p>

        <div style="display: flex; gap: 12px;">
          <button class="api-key-action" @click=${this._emitExportConfig}>
            <span
              class="material-symbols-outlined"
              style="font-size: 14px; vertical-align: middle; margin-right: 4px;"
              >download</span
            >
            Export Config
          </button>
          <button class="api-key-action">
            <span
              class="material-symbols-outlined"
              style="font-size: 14px; vertical-align: middle; margin-right: 4px;"
              >upload</span
            >
            Import Config
          </button>
        </div>
      </div>

      <!-- Danger Zone -->
      <div class="section danger-zone">
        <h3 class="section-title">
          <span class="material-symbols-outlined">warning</span>
          Danger Zone
        </h3>
        <p class="section-desc">Irreversible actions. Proceed with caution.</p>

        <button class="danger-btn">
          <span
            class="material-symbols-outlined"
            style="font-size: 16px; vertical-align: middle; margin-right: 6px;"
            >delete_forever</span
          >
          Reset All Settings
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

  private _emitExportConfig(): void {
    this.dispatchEvent(
      new CustomEvent('export-config', {
        bubbles: true,
        composed: true,
      })
    );
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'saas-settings-appearance-tab': SaasSettingsAppearanceTab;
  }
}
