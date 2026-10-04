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
 * Every control on this screen is either wired to a real API or is absent.
 * A disabled control carries its blocking reason in a title attribute and in
 * a visible inline element (SOMA-01-UIUX-001.md §2.3). Secrets are write-only:
 * this screen never renders a key value or fragment.
 *
 * Settings Tabs:
 * - Agent: Models hub (→ /settings/models)
 * - External: Vault-backed provider keys, MCP client flag
 * - Connectivity: Voice feature flag
 * - System: Feature flags, config export
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';

type SettingsTab = 'agent' | 'external' | 'connectivity' | 'system';

interface BackendFlag {
    key: string;
    enabled: boolean;
    description?: string;
}

interface FeatureFlags {
    voiceEnabled: boolean;
    memoryEnabled: boolean;
    toolsEnabled: boolean;
    mcpEnabled: boolean;
}

interface BackendFlagsResponse {
    flags: BackendFlag[];
    total: number;
}

interface AuthMe {
    id: string;
    tenant_id?: string;
    username?: string;
    email?: string;
    name?: string;
    role?: string;
    roles?: string[];
    permissions?: string[];
}

/** Write-only Vault key status. Never carries key material. */
interface SecretProviderStatus {
    provider: string;
    configured: boolean;
}

interface SecretKeyWriteResult {
    provider: string;
    configured: boolean;
    saved: boolean;
    detail: string;
}

/** Frontend toggle name → backend flag name (/api/v2/config/flags). */
const FEATURE_FLAG_KEYS = {
    voiceEnabled: 'voice',
    memoryEnabled: 'memory',
    toolsEnabled: 'tools',
    mcpEnabled: 'mcp',
} as const;

/**
 * Legacy action names that the catalog maps onto a catalog permission.
 * Mirrors ACTION_ALIASES in admin/core/authz.py — a translation table, not a
 * second vocabulary. An action grants exactly what its target grants.
 */
const ACTION_ALIASES: Record<string, string> = {
    'settings:read': 'system:view',
    'settings:write': 'system:configure',
    'settings:edit': 'system:configure',
};

/** Blocking reason shown whenever a control is disabled for lack of permission. */
const DISABLED_REASON =
    'Requires system:configure. Your role cannot change platform settings.';

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
            gap: 16px;
        }

        .header-title {
            font-size: 18px;
            font-weight: 600;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .save-status {
            font-size: 12px;
            max-width: 360px;
            text-align: right;
        }

        .save-status.ok {
            color: #047857;
        }

        .save-status.error {
            color: #b91c1c;
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

        /* Settings Sections */
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

        /* Form Controls */
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

        .form-hint {
            font-size: 12px;
            color: var(--saas-text-muted, #999);
            margin-top: 6px;
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

        .toggle-switch input:disabled + .toggle-slider {
            cursor: not-allowed;
            opacity: 0.5;
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

        .api-key-action:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* Provider key write rows */
        .provider-key-row {
            display: grid;
            grid-template-columns: 180px 1fr auto auto;
            gap: 12px;
            align-items: end;
            padding: 12px;
            background: var(--saas-bg-hover, #fafafa);
            border-radius: 8px;
            margin-bottom: 12px;
        }

        .provider-key-row:last-child {
            margin-bottom: 0;
        }

        .provider-key-meta {
            display: flex;
            flex-direction: column;
            gap: 4px;
            padding-bottom: 8px;
        }

        .provider-key-name {
            font-size: 14px;
            font-weight: 500;
        }

        .provider-key-state {
            font-size: 12px;
            color: var(--saas-text-secondary, #666);
        }

        .provider-key-actions {
            display: flex;
            gap: 8px;
        }

        @media (max-width: 900px) {
            .provider-key-row {
                grid-template-columns: 1fr;
            }
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

        /* Permission blocking reason (SOMA-01-UIUX-001.md §2.3) */
        .disabled-reason {
            font-size: 12px;
            color: var(--saas-status-danger, #b91c1c);
            margin: 12px 0 0 0;
        }

        /* Flash message (same pattern as saas-settings-models.ts) */
        .toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 1000;
            padding: 12px 18px;
            border-radius: 8px;
            font-size: 13px;
            background: #1a1a1a;
            color: #fff;
            max-width: 420px;
        }

        .toast.error {
            background: #b91c1c;
        }

        .toast.ok {
            background: #047857;
        }

        .honest-note {
            font-size: 13px;
            color: var(--saas-text-secondary, #666);
            margin: 16px 0 0 0;
        }
    `;

    @state() private _activeTab: SettingsTab = 'agent';
    @state() private _isDirty = false;
    @state() private _isSaving = false;

    /** Identity from GET /api/v2/auth/me. */
    @state() private _role = '';
    @state() private _roles: string[] = [];
    @state() private _permissions: string[] = [];

    // Feature flags state (mirrors /api/v2/config/flags; upserted on save)
    @state() private _featureFlags: FeatureFlags = {
        voiceEnabled: true,
        memoryEnabled: true,
        toolsEnabled: true,
        mcpEnabled: false,
    };

    /** Vault-backed provider key status. Write-only: never holds key material. */
    @state() private _secretProviders: SecretProviderStatus[] = [];
    @state() private _secretDrafts: Record<string, string> = {};
    @state() private _secretsLoaded = false;

    @state() private _message: { kind: 'ok' | 'error'; text: string } | null = null;
    @state() private _saveStatus: { kind: 'ok' | 'error'; text: string } | null = null;

    private _tabs: { id: SettingsTab; label: string; icon: string }[] = [
        { id: 'agent', label: 'Agent', icon: 'smart_toy' },
        { id: 'external', label: 'External', icon: 'key' },
        { id: 'connectivity', label: 'Connectivity', icon: 'cable' },
        { id: 'system', label: 'System', icon: 'settings' },
    ];

    /**
     * True iff the caller holds system:configure.
     *
     * Read from the returned permission list, never guessed from the role name.
     * Legacy action names are resolved through the catalog translation table
     * (admin/core/authz.py ACTION_ALIASES) so an old grant means exactly what
     * its catalog target means, nothing more.
     */
    private get _canEditSettings(): boolean {
        return this._permissions.some((p) => {
            const resolved = ACTION_ALIASES[p] ?? p;
            return resolved === 'system:configure';
        });
    }

    override willUpdate() {
        this.setAttribute('data-can-edit', this._canEditSettings ? 'true' : 'false');
    }

    render() {
        return html`
            <!-- Sidebar -->
            <aside class="sidebar">
                <div class="sidebar-header">
                    <h1 class="sidebar-title">Settings</h1>
                    <p class="sidebar-subtitle">Agent configuration</p>
                </div>

                <div class="tab-list">
                    ${this._tabs.map(tab => html`
                        <button
                            class="tab-item ${this._activeTab === tab.id ? 'active' : ''}"
                            @click=${() => this._setTab(tab.id)}
                        >
                            <span class="material-symbols-outlined">${tab.icon}</span>
                            ${tab.label}
                        </button>
                    `)}
                </div>

                <button class="back-btn" @click=${() => window.location.href = '/chat'}>
                    <span class="material-symbols-outlined">arrow_back</span> Back to Chat
                </button>
            </aside>

            <!-- Main Content -->
            <main class="main" data-can-edit=${this._canEditSettings ? 'true' : 'false'}>
                <header class="header">
                    <h2 class="header-title">${this._getTabTitle()}</h2>
                    <div class="header-actions">
                        ${this._saveStatus
                            ? html`<div class="save-status ${this._saveStatus.kind}" role="status">${this._saveStatus.text}</div>`
                            : null}
                        ${!this._canEditSettings
                            ? html`<div class="disabled-reason" style="margin: 0; max-width: 280px; text-align: right;" role="status">${DISABLED_REASON}</div>`
                            : null}
                        <button
                            class="save-btn"
                            data-control="save"
                            title=${!this._canEditSettings
                                ? DISABLED_REASON
                                : this._isSaving
                                    ? 'Saving…'
                                    : this._isDirty
                                        ? 'Save Changes'
                                        : 'No unsaved changes'}
                            ?disabled=${!this._canEditSettings || !this._isDirty || this._isSaving}
                            @click=${this._saveSettings}
                        >
                            <span class="material-symbols-outlined">save</span>
                            ${this._isSaving ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>
                </header>

                <div class="content">
                    ${this._renderTabContent()}
                </div>
            </main>

            ${this._message
                ? html`<div class="toast ${this._message.kind}" role="status">${this._message.text}</div>`
                : null}
        `;
    }

    private _renderDisabledReason() {
        if (this._canEditSettings) return null;
        return html`<p class="disabled-reason">${DISABLED_REASON}</p>`;
    }

    private _renderTabContent() {
        switch (this._activeTab) {
            case 'agent':
                return this._renderAgentTab();
            case 'external':
                return this._renderExternalTab();
            case 'connectivity':
                return this._renderConnectivityTab();
            case 'system':
                return this._renderSystemTab();
        }
    }

    private _renderAgentTab() {
        return html`
            <!-- Models hub card → full Models settings screen (real route) -->
            <div class="section" style="cursor: pointer;" @click=${() => this._openModels()}>
                <h3 class="section-title">
                    <span class="material-symbols-outlined">smart_toy</span>
                    Models
                    <span class="material-symbols-outlined" style="margin-left: auto;">chevron_right</span>
                </h3>
                <p class="section-desc">
                    Providers, API keys, model presets, and Chat / Utility / Embedding slots.
                    Opens the full Models settings screen.
                </p>
                <div class="api-key-row">
                    <span class="api-key-name">Providers</span>
                    <span class="api-key-value">OpenAI, Anthropic, Google, Groq, Ollama, custom OpenAI-compatible</span>
                </div>
                <div class="api-key-row">
                    <span class="api-key-name">Slots</span>
                    <span class="api-key-value">Chat / Utility / Embedding — Capsule or tenant defaults</span>
                </div>
                <div class="api-key-row">
                    <span class="api-key-name">Keys</span>
                    <span class="api-key-value">Vault-backed, write-only (never echoed)</span>
                </div>
                <button
                    class="add-btn"
                    style="margin-top: 16px;"
                    @click=${(e: Event) => { e.stopPropagation(); this._openModels(); }}
                >
                    <span class="material-symbols-outlined">settings_suggest</span>
                    Open Models Settings
                </button>
            </div>
        `;
    }

    private _openModels() {
        window.dispatchEvent(new CustomEvent('saas-navigate', { detail: { route: '/settings/models' } }));
    }

    private _renderExternalTab() {
        return html`
            <div class="section">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">vpn_key</span>
                    API Keys
                </h3>
                <p class="section-desc">
                    Provider API keys live on the Models settings screen, next to the
                    provider and the models that use each key. They are stored in Vault,
                    write-only, and never echoed back.
                </p>
                <button
                    class="add-btn"
                    @click=${() => this._openModels()}
                >
                    <span class="material-symbols-outlined">settings_suggest</span>
                    Open Models Settings
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
<label class="toggle-switch">
                        <input
                            type="checkbox"
                            data-control="feature-flag-mcp"
                            .checked=${this._featureFlags.mcpEnabled}
                            title=${this._canEditSettings ? 'MCP Client' : DISABLED_REASON}
                            ?disabled=${!this._canEditSettings}
                            @change=${() => this._toggleFlag('mcpEnabled')}>
                        <span class="toggle-slider"></span>
                    </label>
                </div>

                ${this._renderDisabledReason()}

                <p class="honest-note">No MCP server registry is exposed by this deployment.</p>
            </div>

            <!-- The real full surface for providers, keys and slots -->
            <div class="section">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">settings_suggest</span>
                    Providers
                </h3>
                <p class="section-desc">
                    Models, provider keys, slots and presets are managed on the Models settings screen.
                </p>
                <button class="add-btn" @click=${() => this._openModels()}>
                    <span class="material-symbols-outlined">open_in_new</span>
                    Manage providers, keys and slots
                </button>
            </div>
        `;
    }

    private _renderConnectivityTab() {
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
                            data-control="feature-flag-voice"
                            .checked=${this._featureFlags.voiceEnabled}
                            title=${this._canEditSettings ? 'Voice Features' : DISABLED_REASON}
                            ?disabled=${!this._canEditSettings}
                            @change=${() => this._toggleFlag('voiceEnabled')}>
                        <span class="toggle-slider"></span>
                    </label>
                </div>

                ${this._renderDisabledReason()}
            </div>
        `;
    }

    private _renderSystemTab() {
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
                            data-control="feature-flag-memory"
                            .checked=${this._featureFlags.memoryEnabled}
                            title=${this._canEditSettings ? 'Memory' : DISABLED_REASON}
                            ?disabled=${!this._canEditSettings}
                            @change=${() => this._toggleFlag('memoryEnabled')}>
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
                            data-control="feature-flag-tools"
                            .checked=${this._featureFlags.toolsEnabled}
                            title=${this._canEditSettings ? 'Tools' : DISABLED_REASON}
                            ?disabled=${!this._canEditSettings}
                            @change=${() => this._toggleFlag('toolsEnabled')}>
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
                            data-control="feature-flag-voice"
                            .checked=${this._featureFlags.voiceEnabled}
                            title=${this._canEditSettings ? 'Voice' : DISABLED_REASON}
                            ?disabled=${!this._canEditSettings}
                            @change=${() => this._toggleFlag('voiceEnabled')}>
                        <span class="toggle-slider"></span>
                    </label>
                </div>

                ${this._renderDisabledReason()}
            </div>

            <!-- Export -->
            <div class="section">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">backup</span>
                    Backup
                </h3>
                <p class="section-desc">
                    Export the feature flags loaded from the server and provider key status
                    (configured booleans only — never key material).
                </p>

                <button
                    class="api-key-action"
                    data-control="export-config"
                    @click=${this._exportConfig}
                >
                    <span class="material-symbols-outlined" style="font-size: 14px; vertical-align: middle; margin-right: 4px;">download</span>
                    Export Config
                </button>
            </div>
        `;
    }

    private _getTabTitle(): string {
        const tab = this._tabs.find(t => t.id === this._activeTab);
        return tab?.label + ' Settings' || 'Settings';
    }

    private _setTab(tab: SettingsTab) {
        this._activeTab = tab;
    }

    override async firstUpdated() {
        await Promise.all([
            this._loadIdentity(),
            this._loadFeatureFlags(),
            this._loadSecretProviders(),
        ]);
    }

    /** Resolve the caller's real permissions from GET /api/v2/auth/me. */
    private async _loadIdentity() {
        try {
            const me = await apiClient.get<AuthMe>('/auth/me');
            this._role = me.role ?? '';
            this._roles = me.roles ?? [];
            this._permissions = me.permissions ?? [];
        } catch (error) {
            // Fail closed: without a permission list nothing is editable.
            this._role = '';
            this._roles = [];
            this._permissions = [];
            this._flash('error', `Failed to load your permissions: ${error instanceof Error ? error.message : error}`);
        }
    }

    /** Load persisted feature flags so the toggles show real state. */
    private async _loadFeatureFlags() {
        try {
            const response = await apiClient.get<BackendFlagsResponse>('/config/flags');
            const byKey = new Map((response.flags ?? []).map(f => [f.key, f.enabled]));
            this._featureFlags = {
                voiceEnabled: byKey.get(FEATURE_FLAG_KEYS.voiceEnabled) ?? this._featureFlags.voiceEnabled,
                memoryEnabled: byKey.get(FEATURE_FLAG_KEYS.memoryEnabled) ?? this._featureFlags.memoryEnabled,
                toolsEnabled: byKey.get(FEATURE_FLAG_KEYS.toolsEnabled) ?? this._featureFlags.toolsEnabled,
                mcpEnabled: byKey.get(FEATURE_FLAG_KEYS.mcpEnabled) ?? this._featureFlags.mcpEnabled,
            };
        } catch (error) {
            this._flash('error', `Failed to load feature flags: ${error instanceof Error ? error.message : error}`);
        }
    }

    /**
     * Load write-only Vault key status. The API returns provider + configured
     * only — never a key value or fragment.
     */
    private async _loadSecretProviders() {
        try {
            const rows = await apiClient.get<SecretProviderStatus[]>('/secrets/providers');
            this._secretProviders = rows ?? [];
            this._secretsLoaded = true;
        } catch (error) {
            this._secretProviders = [];
            this._secretsLoaded = false;
            this._flash('error', `Failed to load secret providers: ${error instanceof Error ? error.message : error}`);
        }
    }

    private _flash(kind: 'ok' | 'error', text: string) {
        this._message = { kind, text };
        window.setTimeout(() => {
            if (this._message?.text === text) this._message = null;
        }, 5000);
    }

    private _toggleFlag(flag: keyof typeof this._featureFlags) {
        if (!this._canEditSettings) return;
        this._featureFlags = {
            ...this._featureFlags,
            [flag]: !this._featureFlags[flag]
        };
        this._isDirty = true;
        this._saveStatus = null;
    }

    private async _saveSettings() {
        if (!this._canEditSettings) return;
        this._isSaving = true;
        this._saveStatus = null;
        try {
            await this._saveFeatureFlags();
            this._isDirty = false;
            this._saveStatus = { kind: 'ok', text: 'Settings saved.' };
        } catch (error) {
            const text = error instanceof Error ? error.message : String(error);
            this._saveStatus = { kind: 'error', text: `Failed to save settings: ${text}` };
        } finally {
            this._isSaving = false;
        }
    }

    /**
     * Persist feature flags to the real flag API (/api/v2/config/flags).
     *
     * Flags are upserted: PATCH when the flag already exists, POST when it does
     * not. The API takes key/enabled as query parameters, not a JSON body.
     */
    private async _saveFeatureFlags() {
        const existing = await apiClient.get<BackendFlagsResponse>('/config/flags');
        const known = new Set((existing.flags ?? []).map(f => f.key));

        const jobs: Promise<unknown>[] = [];
        for (const [frontendKey, backendKey] of Object.entries(FEATURE_FLAG_KEYS)) {
            const enabled = this._featureFlags[frontendKey as keyof FeatureFlags];
            if (known.has(backendKey)) {
                jobs.push(
                    apiClient.patch(`/config/flags/${backendKey}?enabled=${enabled}`, {})
                );
            } else {
                jobs.push(
                    apiClient.post(`/config/flags?key=${backendKey}&enabled=${enabled}`, {})
                );
            }
        }
        await Promise.all(jobs);
    }

    /** Write-only key save. The draft is cleared after a successful write. */
    private _exportConfig() {
        const config: Record<string, unknown> = {
            featureFlags: {
                [FEATURE_FLAG_KEYS.voiceEnabled]: this._featureFlags.voiceEnabled,
                [FEATURE_FLAG_KEYS.memoryEnabled]: this._featureFlags.memoryEnabled,
                [FEATURE_FLAG_KEYS.toolsEnabled]: this._featureFlags.toolsEnabled,
                [FEATURE_FLAG_KEYS.mcpEnabled]: this._featureFlags.mcpEnabled,
            },
            exportedAt: new Date().toISOString(),
        };
        if (this._secretsLoaded) {
            config.secretProviders = this._secretProviders.map(p => ({
                provider: p.provider,
                configured: p.configured,
            }));
        }
        const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'agent-config.json';
        a.click();
        URL.revokeObjectURL(url);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-settings': SaasSettings;
    }
}
