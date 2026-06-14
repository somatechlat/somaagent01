/**
 * Settings Notifications Tab
 * Voice, speech, and proxy configuration.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { FeatureFlags } from '../controllers/settings-controller.js';

export interface FeatureFlagChangeDetail {
  flag: keyof FeatureFlags;
}

@customElement('saas-settings-notifications-tab')
export class SaasSettingsNotificationsTab extends LitElement {
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

    .settings-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 20px;
    }

    @media (max-width: 800px) {
      .settings-grid {
        grid-template-columns: 1fr;
      }
    }

    .form-group {
      margin-bottom: 20px;
    }

    .form-group:last-child {
      margin-bottom: 0;
    }

    .form-label {
      display: block;
      font-size: 13px;
      font-weight: 500;
      margin-bottom: 8px;
      color: var(--saas-text-primary, #1a1a1a);
    }

    .form-input,
    .form-select {
      width: 100%;
      padding: 10px 14px;
      border-radius: 8px;
      border: 1px solid var(--saas-border-light, #e0e0e0);
      font-size: 14px;
      background: var(--saas-bg-card, #ffffff);
      color: var(--saas-text-primary, #1a1a1a);
      transition: border-color 0.15s ease;
    }

    .form-input:focus,
    .form-select:focus {
      outline: none;
      border-color: var(--saas-text-primary, #1a1a1a);
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
      <!-- Voice Settings -->
      <div class="section">
        <h3 class="section-title">
          <span class="material-symbols-outlined">mic</span>
          Voice / Speech
        </h3>
        <p class="section-desc">Configure voice input and output.</p>

        <div class="toggle-row">
          <div>
            <div class="toggle-label">Voice Features</div>
            <div class="toggle-desc">Enable voice input and output</div>
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

        <div class="settings-grid" style="margin-top: 20px;">
          <div class="form-group">
            <label class="form-label">STT Provider</label>
            <select class="form-select">
              <option value="whisper">Whisper (Local)</option>
              <option value="deepgram">Deepgram</option>
              <option value="google">Google Speech</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">TTS Provider</label>
            <select class="form-select">
              <option value="kokoro">Kokoro (Local)</option>
              <option value="elevenlabs">ElevenLabs</option>
              <option value="openai">OpenAI TTS</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Proxy Settings -->
      <div class="section">
        <h3 class="section-title">
          <span class="material-symbols-outlined">router</span>
          Proxy / Network
        </h3>
        <p class="section-desc">Network and proxy configuration.</p>

        <div class="form-group">
          <label class="form-label">HTTP Proxy</label>
          <input type="text" class="form-input" placeholder="http://proxy.example.com:8080" />
        </div>
        <div class="form-group">
          <label class="form-label">HTTPS Proxy</label>
          <input type="text" class="form-input" placeholder="https://proxy.example.com:8080" />
        </div>
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
    'saas-settings-notifications-tab': SaasSettingsNotificationsTab;
  }
}
