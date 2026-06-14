/**
 * SomaAgent SaaS — Settings View
 * Per AGENT_USER_UI_SRS.md Section 6 and UI_SCREENS_SRS.md
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Django Ninja API integration
 * - Minimal white/black design per UI_STYLE_GUIDE.md
 * - NO EMOJIS - Google Material Symbols only
 *
 * Settings Tabs:
 * - Agent: Chat/Utility/Browser/Embedding Model settings, Memory/SomaBrain
 * - External: API Keys, MCP Client/Server, A2A
 * - Connectivity: Voice/Speech, Proxy, SSE
 * - System: Feature Flags, Auth, Backup, Secrets
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { SettingsController } from '../controllers/settings-controller.js';
import '../components/saas-settings-profile-tab.js';
import '../components/saas-settings-security-tab.js';
import '../components/saas-settings-notifications-tab.js';
import '../components/saas-settings-appearance-tab.js';
import type { ChatModelChangeDetail, UtilityModelChangeDetail } from '../components/saas-settings-profile-tab.js';
import type { FeatureFlagChangeDetail as SecurityFeatureFlagChangeDetail } from '../components/saas-settings-security-tab.js';
import type { FeatureFlagChangeDetail as NotificationsFeatureFlagChangeDetail } from '../components/saas-settings-notifications-tab.js';
import type { FeatureFlagChangeDetail as AppearanceFeatureFlagChangeDetail } from '../components/saas-settings-appearance-tab.js';

type SettingsTab = 'agent' | 'external' | 'connectivity' | 'system';

@customElement('saas-settings')
export class SaasSettings extends LitElement {
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
      width: 240px;
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
      font-size: 20px;
      font-weight: 600;
      margin: 0 0 4px 0;
    }

    .sidebar-subtitle {
      font-size: 13px;
      color: var(--saas-text-secondary, #666);
    }

    /* Tabs */
    .tab-list {
      display: flex;
      flex-direction: column;
      gap: 4px;
      padding: 0 12px;
    }

    .tab-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 14px;
      border-radius: 8px;
      font-size: 14px;
      color: var(--saas-text-secondary, #666);
      cursor: pointer;
      transition: all 0.15s ease;
      border: none;
      background: transparent;
      width: 100%;
      text-align: left;
    }

    .tab-item:hover {
      background: var(--saas-bg-hover, #fafafa);
      color: var(--saas-text-primary, #1a1a1a);
    }

    .tab-item.active {
      background: var(--saas-bg-active, #f0f0f0);
      color: var(--saas-text-primary, #1a1a1a);
      font-weight: 500;
    }

    .tab-item .material-symbols-outlined {
      font-size: 18px;
    }

    /* Back Button */
    .back-btn {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 20px;
      margin-top: auto;
      font-size: 14px;
      color: var(--saas-text-secondary, #666);
      cursor: pointer;
      transition: all 0.1s ease;
      border: none;
      background: transparent;
    }

    .back-btn:hover {
      color: var(--saas-text-primary, #1a1a1a);
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

    .save-btn {
      padding: 10px 20px;
      border-radius: 8px;
      background: #1a1a1a;
      color: white;
      border: none;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.1s ease;
    }

    .save-btn:hover {
      background: #333;
    }

    .save-btn:disabled {
      background: var(--saas-border-light, #e0e0e0);
      color: var(--saas-text-muted, #999);
      cursor: not-allowed;
    }

    .save-btn .material-symbols-outlined {
      font-size: 18px;
    }

    /* Content Area */
    .content {
      flex: 1;
      overflow-y: auto;
      padding: 24px;
    }
  `;

  private _settings = new SettingsController(this);

  @state() private _activeTab: SettingsTab = 'agent';

  private _tabs: { id: SettingsTab; label: string; icon: string }[] = [
    { id: 'agent', label: 'Agent', icon: 'smart_toy' },
    { id: 'external', label: 'External', icon: 'key' },
    { id: 'connectivity', label: 'Connectivity', icon: 'cable' },
    { id: 'system', label: 'System', icon: 'settings' },
  ];

  render() {
    return html`
      <!-- Sidebar -->
      <aside class="sidebar">
        <div class="sidebar-header">
          <h1 class="sidebar-title">Settings</h1>
          <p class="sidebar-subtitle">Agent configuration</p>
        </div>

        <div class="tab-list">
          ${this._tabs.map(
            tab => html`
              <button
                class="tab-item ${this._activeTab === tab.id ? 'active' : ''}"
                @click=${() => this._setTab(tab.id)}
              >
                <span class="material-symbols-outlined">${tab.icon}</span>
                ${tab.label}
              </button>
            `
          )}
        </div>

        <button class="back-btn" @click=${() => (window.location.href = '/chat')}>
          <span class="material-symbols-outlined">arrow_back</span> Back to Chat
        </button>
      </aside>

      <!-- Main Content -->
      <main class="main">
        <header class="header">
          <h2 class="header-title">${this._getTabTitle()}</h2>
          <button
            class="save-btn"
            ?disabled=${!this._settings.isDirty || this._settings.isSaving}
            @click=${() => this._settings.saveSettings()}
          >
            <span class="material-symbols-outlined">save</span>
            ${this._settings.isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </header>

        <div class="content">
          ${this._renderTabContent()}
        </div>
      </main>
    `;
  }

  private _renderTabContent() {
    switch (this._activeTab) {
      case 'agent':
        return html`
          <saas-settings-profile-tab
            .chatModel=${this._settings.chatModel}
            .utilityModel=${this._settings.utilityModel}
            @chat-model-change=${this._handleChatModelChange}
            @utility-model-change=${this._handleUtilityModelChange}
          ></saas-settings-profile-tab>
        `;
      case 'external':
        return html`
          <saas-settings-security-tab
            .featureFlags=${this._settings.featureFlags}
            @feature-flag-change=${this._handleSecurityFeatureFlagChange}
          ></saas-settings-security-tab>
        `;
      case 'connectivity':
        return html`
          <saas-settings-notifications-tab
            .featureFlags=${this._settings.featureFlags}
            @feature-flag-change=${this._handleNotificationsFeatureFlagChange}
          ></saas-settings-notifications-tab>
        `;
      case 'system':
        return html`
          <saas-settings-appearance-tab
            .featureFlags=${this._settings.featureFlags}
            @feature-flag-change=${this._handleAppearanceFeatureFlagChange}
            @export-config=${() => this._settings.exportConfig()}
          ></saas-settings-appearance-tab>
        `;
    }
  }

  private _getTabTitle(): string {
    const tab = this._tabs.find(t => t.id === this._activeTab);
    return tab?.label + ' Settings' || 'Settings';
  }

  private _setTab(tab: SettingsTab) {
    this._activeTab = tab;
  }

  private _handleChatModelChange(e: CustomEvent<ChatModelChangeDetail>) {
    this._settings.updateChatModel(e.detail.field, e.detail.value);
  }

  private _handleUtilityModelChange(e: CustomEvent<UtilityModelChangeDetail>) {
    this._settings.updateUtilityModel(e.detail.field, e.detail.value);
  }

  private _handleSecurityFeatureFlagChange(e: CustomEvent<SecurityFeatureFlagChangeDetail>) {
    this._settings.toggleFlag(e.detail.flag);
  }

  private _handleNotificationsFeatureFlagChange(e: CustomEvent<NotificationsFeatureFlagChangeDetail>) {
    this._settings.toggleFlag(e.detail.flag);
  }

  private _handleAppearanceFeatureFlagChange(e: CustomEvent<AppearanceFeatureFlagChangeDetail>) {
    this._settings.toggleFlag(e.detail.flag);
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'saas-settings': SaasSettings;
  }
}
