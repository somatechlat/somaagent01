/**
 * SomaAgent Soma — Settings View
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
 * Settings Tabs (one shell):
 * Agent · Models · Voice · Interface · Tools · Integrations · Advanced
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import { applyTheme, getTheme } from '../services/theme-boot.js';
import { getLocale, setLocale } from '../i18n/index.js';
import { glassCard } from '../styles/glass.js';
import { moduleBase } from '../styles/module-base.js';
import '../components/settings-form.js';
import './soma-settings-models.js';
import './soma-settings-somabrain.js';
import '../components/soma-agent-iq.js';
import '../components/soma-skin-gallery.js';
import type { SomaSettingsSomaBrain } from './soma-settings-somabrain.js';

type SettingsTab =
    | 'agent'
    | 'models'
    | 'voice'
    | 'interface'
    | 'tools'
    | 'external'
    | 'somabrain'
    | 'connectivity'
    | 'system';

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

@customElement('soma-settings')
export class SomaSettings extends LitElement {
    static styles = [
        glassCard,
        moduleBase,
        css`
        :host {
            display: flex;
            height: 100vh;
            background: var(--skin-color-bg-void);
            font-family: var(--skin-font-sans);
            color: var(--skin-color-text-primary);
        }

        * {
            box-sizing: border-box;
        }

        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: calc(var(--skin-space-md) + var(--skin-space-xs));
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
            width: calc(var(--skin-space-md) * 15);
            background: var(--skin-color-bg-card);
            border-right: var(--skin-border-width) solid var(--skin-color-border);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            padding: var(--skin-space-lg) 0;
        }

        .sidebar-header {
            padding: 0 calc(var(--skin-space-md) + var(--skin-space-xs)) calc(var(--skin-space-md) + var(--skin-space-xs));
            border-bottom: var(--skin-border-width) solid var(--skin-color-border);
            margin-bottom: var(--skin-space-md);
        }

        .sidebar-title {
            font-size: calc(var(--skin-space-md) + var(--skin-space-xs));
            font-weight: var(--skin-weight-semibold);
            margin: 0 0 var(--skin-space-xs) 0;
        }

        .sidebar-subtitle {
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-secondary);
        }

        /* Tabs */
        .tab-list {
            display: flex;
            flex-direction: column;
            gap: var(--skin-space-xs);
            padding: 0 calc(var(--skin-space-sm) + var(--skin-space-xs));
        }

        .tab-item {
            display: flex;
            align-items: center;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs));
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs)) calc(var(--skin-space-md) - var(--skin-space-xs) / 2);
            border-radius: var(--skin-radius-md);
            font-size: var(--skin-text-base);
            color: var(--skin-color-text-secondary);
            cursor: pointer;
            transition: all var(--skin-motion-fast) var(--skin-motion-ease);
            border: none;
            background: transparent;
            width: 100%;
            text-align: left;
        }

        .tab-item:hover {
            background: var(--skin-color-bg-hover);
            color: var(--skin-color-text-primary);
        }

        .tab-item.active {
            background: var(--skin-color-bg-active);
            color: var(--skin-color-text-primary);
            font-weight: var(--skin-weight-medium);
        }

        .tab-item .material-symbols-outlined {
            font-size: calc(var(--skin-space-md) + var(--skin-space-xs) / 2);
        }

        /* Back Button */
        .back-btn {
            display: flex;
            align-items: center;
            gap: var(--skin-space-sm);
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs)) calc(var(--skin-space-md) + var(--skin-space-xs));
            margin-top: auto;
            font-size: var(--skin-text-base);
            color: var(--skin-color-text-secondary);
            cursor: pointer;
            transition: all calc(var(--skin-motion-fast) * 2 / 3) var(--skin-motion-ease);
            border: none;
            background: transparent;
        }

        .back-btn:hover {
            color: var(--skin-color-text-primary);
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
            padding: var(--skin-space-md) var(--skin-space-lg);
            background: var(--skin-color-bg-card);
            border-bottom: var(--skin-border-width) solid var(--skin-color-border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: var(--skin-space-md);
        }

        .header-title {
            font-size: calc(var(--skin-space-md) + var(--skin-space-xs) / 2);
            font-weight: var(--skin-weight-semibold);
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs));
        }

        .save-status {
            font-size: calc(var(--skin-text-xs) + var(--skin-text-xs) / 11);
            max-width: calc(var(--skin-space-md) * 22.5);
            text-align: right;
        }

        .save-status.ok {
            color: var(--skin-color-success);
        }

        .save-status.error {
            color: var(--skin-color-danger);
        }

        .save-btn {
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs) / 2) calc(var(--skin-space-md) + var(--skin-space-xs));
            border-radius: var(--skin-radius-md);
            background: var(--skin-color-accent);
            color: var(--skin-color-accent-text);
            border: none;
            font-size: var(--skin-text-base);
            font-weight: var(--skin-weight-medium);
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: var(--skin-space-sm);
            transition: all calc(var(--skin-motion-fast) * 2 / 3) var(--skin-motion-ease);
        }

        .save-btn:hover {
            background: var(--skin-color-accent-hover);
        }

        .save-btn:disabled {
            background: var(--skin-color-border);
            color: var(--skin-color-text-muted);
            cursor: not-allowed;
        }

        .save-btn .material-symbols-outlined {
            font-size: calc(var(--skin-space-md) + var(--skin-space-xs) / 2);
        }

        /* Content Area */
        .content {
            flex: 1;
            overflow-y: auto;
            padding: var(--skin-space-lg);
        }

        /* Settings Sections */
        .section {
            background: var(--skin-color-bg-card);
            border: var(--skin-border-width) solid var(--skin-color-border);
            border-radius: var(--skin-radius-lg);
            padding: var(--skin-space-lg);
            margin-bottom: calc(var(--skin-space-md) + var(--skin-space-xs));
        }

        .section-title {
            font-size: var(--skin-text-lg);
            font-weight: var(--skin-weight-semibold);
            margin: 0 0 var(--skin-space-md) 0;
            display: flex;
            align-items: center;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs) / 2);
        }

        .section-title .material-symbols-outlined {
            font-size: calc(var(--skin-space-md) + var(--skin-space-xs));
            color: var(--skin-color-text-secondary);
        }

        .section-desc {
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-secondary);
            margin-bottom: calc(var(--skin-space-md) + var(--skin-space-xs));
        }

        /* Form Controls */
        .form-group {
            margin-bottom: calc(var(--skin-space-md) + var(--skin-space-xs));
        }

        .form-group:last-child {
            margin-bottom: 0;
        }

        .form-label {
            display: block;
            font-size: var(--skin-text-sm);
            font-weight: var(--skin-weight-medium);
            margin-bottom: var(--skin-space-sm);
            color: var(--skin-color-text-primary);
        }

        .form-input,
        .form-select {
            width: 100%;
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs) / 2) calc(var(--skin-space-md) - var(--skin-space-xs) / 2);
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid var(--skin-color-border);
            font-size: var(--skin-text-base);
            background: var(--skin-color-bg-card);
            color: var(--skin-color-text-primary);
            transition: border-color var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .form-input:focus,
        .form-select:focus {
            outline: none;
            border-color: var(--skin-color-text-primary);
        }

        .form-hint {
            font-size: calc(var(--skin-text-xs) + var(--skin-text-xs) / 11);
            color: var(--skin-color-text-muted);
            margin-top: calc(var(--skin-space-xs) * 1.5);
        }

        /* Toggle Switch */
        .toggle-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs)) 0;
            border-bottom: var(--skin-border-width) solid var(--skin-color-border);
        }

        .toggle-row:last-child {
            border-bottom: none;
        }

        .toggle-label {
            font-size: var(--skin-text-base);
        }

        .toggle-desc {
            font-size: calc(var(--skin-text-xs) + var(--skin-text-xs) / 11);
            color: var(--skin-color-text-secondary);
            margin-top: var(--skin-space-xs);
        }

        .toggle-switch {
            position: relative;
            width: calc(var(--skin-space-2xl) - var(--skin-space-xs));
            height: var(--skin-space-lg);
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
            background-color: var(--skin-color-border);
            transition: var(--skin-motion-normal);
            border-radius: var(--skin-space-lg);
        }

        .toggle-slider:before {
            position: absolute;
            content: "";
            height: calc(var(--skin-space-md) + var(--skin-space-xs) / 2);
            width: calc(var(--skin-space-md) + var(--skin-space-xs) / 2);
            left: calc(var(--skin-space-xs) * 0.75);
            bottom: calc(var(--skin-space-xs) * 0.75);
            background-color: var(--skin-color-bg-card);
            transition: var(--skin-motion-normal);
            border-radius: 50%;
        }

        .toggle-switch input:checked + .toggle-slider {
            background-color: var(--skin-color-accent);
        }

        .toggle-switch input:checked + .toggle-slider:before {
            transform: translateX(calc(var(--skin-space-md) + var(--skin-space-xs)));
        }

        .toggle-switch input:disabled + .toggle-slider {
            cursor: not-allowed;
            opacity: 0.5;
        }

        /* API Key Row */
        .api-key-row {
            display: flex;
            align-items: center;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs));
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs));
            background: var(--skin-color-bg-hover);
            border-radius: var(--skin-radius-md);
            margin-bottom: calc(var(--skin-space-sm) + var(--skin-space-xs));
        }

        .api-key-row:last-child {
            margin-bottom: 0;
        }

        .api-key-name {
            flex: 1;
            font-size: var(--skin-text-base);
            font-weight: var(--skin-weight-medium);
        }

        .api-key-value {
            flex: 2;
            font-family: var(--skin-font-mono);
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-secondary);
        }

        .api-key-status {
            padding: var(--skin-space-xs) var(--skin-space-sm);
            border-radius: var(--skin-radius-sm);
            font-size: var(--skin-text-xs);
            font-weight: var(--skin-weight-semibold);
        }

        .api-key-status.active {
            background: color-mix(in srgb, var(--skin-color-success) 18%, var(--skin-color-bg-card));
            color: var(--skin-color-success);
        }

        .api-key-status.missing {
            background: color-mix(in srgb, var(--skin-color-danger) 12%, var(--skin-color-bg-card));
            color: var(--skin-color-danger);
        }

        .api-key-action {
            padding: calc(var(--skin-space-xs) * 1.5) calc(var(--skin-space-sm) + var(--skin-space-xs));
            border-radius: calc(var(--skin-space-xs) * 1.5);
            border: var(--skin-border-width) solid var(--skin-color-border);
            background: var(--skin-color-bg-card);
            font-size: calc(var(--skin-text-xs) + var(--skin-text-xs) / 11);
            cursor: pointer;
            transition: all calc(var(--skin-motion-fast) * 2 / 3) var(--skin-motion-ease);
        }

        .api-key-action:hover {
            border-color: var(--skin-color-border-strong);
        }

        .api-key-action:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* Provider key write rows */
        .provider-key-row {
            display: grid;
            grid-template-columns: calc(var(--skin-space-md) * 11.25) 1fr auto auto;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs));
            align-items: end;
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs));
            background: var(--skin-color-bg-hover);
            border-radius: var(--skin-radius-md);
            margin-bottom: calc(var(--skin-space-sm) + var(--skin-space-xs));
        }

        .provider-key-row:last-child {
            margin-bottom: 0;
        }

        .provider-key-meta {
            display: flex;
            flex-direction: column;
            gap: var(--skin-space-xs);
            padding-bottom: var(--skin-space-sm);
        }

        .provider-key-name {
            font-size: var(--skin-text-base);
            font-weight: var(--skin-weight-medium);
        }

        .provider-key-state {
            font-size: calc(var(--skin-text-xs) + var(--skin-text-xs) / 11);
            color: var(--skin-color-text-secondary);
        }

        .provider-key-actions {
            display: flex;
            gap: var(--skin-space-sm);
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
            gap: var(--skin-space-sm);
            width: 100%;
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs));
            border: calc(var(--skin-space-xs) / 2) dashed var(--skin-color-border);
            border-radius: var(--skin-radius-md);
            background: transparent;
            color: var(--skin-color-text-secondary);
            font-size: var(--skin-text-base);
            cursor: pointer;
            transition: all calc(var(--skin-motion-fast) * 2 / 3) var(--skin-motion-ease);
        }

        .add-btn:hover {
            border-color: var(--skin-color-border-strong);
            color: var(--skin-color-text-primary);
        }

        /* Permission blocking reason (SOMA-01-UIUX-001.md §2.3) */
        .disabled-reason {
            font-size: calc(var(--skin-text-xs) + var(--skin-text-xs) / 11);
            color: var(--skin-color-danger);
            margin: calc(var(--skin-space-sm) + var(--skin-space-xs)) 0 0 0;
        }

        /* Flash message (same pattern as soma-settings-models.ts) */
        .toast {
            position: fixed;
            bottom: var(--skin-space-lg);
            right: var(--skin-space-lg);
            z-index: var(--skin-z-toast);
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs)) calc(var(--skin-space-md) + var(--skin-space-xs) / 2);
            border-radius: var(--skin-radius-md);
            font-size: var(--skin-text-sm);
            background: var(--skin-color-accent);
            color: var(--skin-color-accent-text);
            max-width: calc(var(--skin-space-md) * 26.25);
        }

        .toast.error {
            background: var(--skin-color-danger);
        }

        .toast.ok {
            background: var(--skin-color-success);
        }

        .honest-note {
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-secondary);
            margin: var(--skin-space-md) 0 0 0;
        }
    `,
    ];

    @state() private _activeTab: SettingsTab = 'agent';
    /** Capsule for AgentIQ knobs (Settings › Agent). */
    @state() private _activeCapsuleId = '';

    /** Deep-link tab from the route (/settings/models, /settings/channels). */
    @property({ type: String, attribute: 'active-tab' }) activeTab = '';
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

    /** Configurable services, from GET /api/v2/core/settings/ — never a local list. */
    @state() private _entities: { entity: string; name: string; icon: string }[] = [];
    @state() private _entitiesError = '';

    /** Live tool catalog (Capability). */
    @state() private _tools: { name: string; description: string; enabled: boolean }[] = [];
    @state() private _toolsError = '';

    private _tabs: { id: SettingsTab; label: string; icon: string }[] = [
        { id: 'agent', label: 'Agent', icon: 'smart_toy' },
        { id: 'models', label: 'Models', icon: 'deployed_code' },
        { id: 'voice', label: 'Voice', icon: 'graphic_eq' },
        { id: 'interface', label: 'Interface', icon: 'palette' },
        { id: 'tools', label: 'Tools', icon: 'build' },
        { id: 'external', label: 'Integrations', icon: 'key' },
        { id: 'somabrain', label: 'SomaBrain', icon: 'psychology' },
        { id: 'connectivity', label: 'Connectivity', icon: 'cable' },
        { id: 'system', label: 'Advanced', icon: 'settings' },
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
                            ? html`<div class="disabled-reason" style="margin: 0; max-width: calc(var(--skin-space-md) * 17.5); text-align: right;" role="status">${DISABLED_REASON}</div>`
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
            case 'models':
                return this._renderModelsTab();
            case 'voice':
                return this._renderVoiceTab();
            case 'interface':
                return this._renderInterfaceTab();
            case 'tools':
                return this._renderToolsTab();
            case 'external':
                return this._renderExternalTab();
            case 'somabrain':
                return this._renderSomabrainTab();
            case 'connectivity':
                return this._renderConnectivityTab();
            case 'system':
                return this._renderSystemTab();
        }
    }

    /**
     * UI-S-56: Connection form + connector status + route links + honest gaps.
     * Dirty state and PUT live on the child; shell Save delegates to it.
     */
    private _renderSomabrainTab() {
        return html`
            <soma-settings-somabrain
                .canEdit=${this._canEditSettings}
                @soma-settings-dirty=${this._onSomabrainDirty}
            ></soma-settings-somabrain>
        `;
    }

    private _somabrainPanel(): SomaSettingsSomaBrain | null {
        return this.shadowRoot?.querySelector('soma-settings-somabrain') ?? null;
    }

    private _onSomabrainDirty(e: Event) {
        const detail = (e as CustomEvent<{ dirty?: boolean }>).detail;
        if (typeof detail?.dirty === 'boolean' && this._activeTab === 'somabrain') {
            this._isDirty = detail.dirty;
            if (!detail.dirty) {
                this._saveStatus = null;
            }
        }
    }

    private _renderModelsTab() {
        return html`
            <div class="section" style="padding: 0; border: none; background: transparent;">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">deployed_code</span>
                    Models
                </h3>
                <p class="section-desc">
                    Whole model cards with Activate, Custom URL, Load models, and Vault keys.
                    Used for: Chat / Help / Memory.
                </p>
                <soma-settings-models></soma-settings-models>
            </div>
        `;
    }

    private _renderVoiceTab() {
        return html`
            <div class="section">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">graphic_eq</span>
                    Voice
                </h3>
                <p class="section-desc">
                    How the agent speaks and listens. Personas, speech-to-text, and text-to-speech.
                </p>
                <button
                    class="save-btn"
                    @click=${() =>
                        window.dispatchEvent(
                            new CustomEvent('soma-navigate', { detail: { route: '/voice/personas' } }),
                        )}
                >
                    <span class="material-symbols-outlined">mic</span>
                    Open voice settings
                </button>
            </div>
        `;
    }

    private _renderInterfaceTab() {
        return html`
            <div class="section">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">palette</span>
                    Interface
                </h3>
                <p class="section-desc">
                    Theme, language, and how the workspace looks on this device.
                </p>

                <div class="toggle-row">
                    <div>
                        <div class="toggle-label">Theme</div>
                        <div class="toggle-desc">Dark (default) or Light</div>
                    </div>
                    <select
                        data-control="interface-theme"
                        .value=${getTheme()}
                        title=${this._canEditSettings ? 'Theme' : DISABLED_REASON}
                        ?disabled=${!this._canEditSettings}
                        @change=${(e: Event) => this._setInterface('theme', e)}
                    >
                        <option value="dark">Dark</option>
                        <option value="light">Light</option>
                    </select>
                </div>

                <div class="toggle-row" style="display:block">
                    <div class="toggle-label" style="margin-bottom: var(--skin-space-sm)">Skins</div>
                    <soma-skin-gallery></soma-skin-gallery>
                </div>

                <div class="toggle-row">
                    <div>
                        <div class="toggle-label">Language</div>
                        <div class="toggle-desc">Language for this interface</div>
                    </div>
                    <select
                        data-control="interface-language"
                        .value=${getLocale()}
                        title=${this._canEditSettings ? 'Language' : DISABLED_REASON}
                        ?disabled=${!this._canEditSettings}
                        @change=${(e: Event) => this._setInterface('language', e)}
                    >
                        <option value="en">English</option>
                        <option value="es">Español</option>
                    </select>
                </div>

                <div class="toggle-row">
                    <div>
                        <div class="toggle-label">Timezone</div>
                        <div class="toggle-desc">Shown in timestamps</div>
                    </div>
                    <select
                        data-control="interface-timezone"
                        title=${this._canEditSettings ? 'Timezone' : DISABLED_REASON}
                        ?disabled=${!this._canEditSettings}
                        @change=${(e: Event) => this._setInterface('timezone', e)}
                    >
                        <option value="UTC">UTC</option>
                        <option value="America/Guayaquil">America/Guayaquil</option>
                        <option value="America/New_York">America/New_York</option>
                        <option value="Europe/Madrid">Europe/Madrid</option>
                    </select>
                </div>

                <p class="honest-note">
                    Density, clock, and panel defaults use this device until the server exposes
                    those preferences.
                </p>

                ${this._renderDisabledReason()}
            </div>
        `;
    }

    private _setInterface(key: string, e: Event) {
        const select = e.target as HTMLSelectElement;
        const prefs = JSON.parse(localStorage.getItem('soma_interface') || '{}');
        prefs[key] = select.value;
        localStorage.setItem('soma_interface', JSON.stringify(prefs));
        if (key === 'theme') {
            applyTheme(select.value === 'light' ? 'light' : 'dark');
        }
        if (key === 'language') {
            // One source: i18n owns soma_locale + html lang (SOMA-UI-I18N-001).
            setLocale(select.value);
        }
        this._isDirty = true;
    }

    private _renderToolsTab() {
        return html`
            <div class="section">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">build</span>
                    Tools
                </h3>
                <p class="section-desc">
                    Capabilities the agent can call. Names and enable state come from the live
                    tool catalog.
                </p>

                ${this._toolsError
                    ? html`<p class="disabled-reason" role="status">${this._toolsError}</p>`
                    : this._tools.length === 0
                        ? html`<p class="honest-note" role="status">No tools returned by the server.</p>`
                        : this._tools.map(
                              (t) => html`
                                  <div class="toggle-row">
                                      <div>
                                          <div class="toggle-label">${t.name}</div>
                                          <div class="toggle-desc">${t.description || 'No description'}</div>
                                      </div>
                                      <label class="toggle-switch">
                                          <input
                                              type="checkbox"
                                              data-control="tool-${t.name}"
                                              .checked=${t.enabled}
                                              title=${this._canEditSettings ? t.name : DISABLED_REASON}
                                              ?disabled=${!this._canEditSettings}
                                              @change=${() => this._toggleTool(t.name)}>
                                          <span class="toggle-slider"></span>
                                      </label>
                                  </div>
                              `,
                          )}

                ${this._renderDisabledReason()}
            </div>
        `;
    }

    private async _loadCapsuleId(): Promise<void> {
        try {
            const data = await apiClient.get<{ agents?: { agent_id: string; capsule_id?: string }[] }>('/agents/');
            const first = data?.agents?.[0];
            if (first?.capsule_id) this._activeCapsuleId = first.capsule_id;
        } catch {
            /* AgentIQ shows its own empty state */
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
                    Whole model cards: Activate, Custom URL, Load models, Vault keys,
                    Used for Chat / Help / Memory. Opens the full Models screen.
                </p>
                <div class="api-key-row">
                    <span class="api-key-name">Providers</span>
                    <span class="api-key-value">OpenAI, Anthropic, Google, Groq, Ollama, custom OpenAI-compatible</span>
                </div>
                <div class="api-key-row">
                    <span class="api-key-name">Used for</span>
                    <span class="api-key-value">Chat / Help / Memory — Agent or tenant defaults</span>
                </div>
                <div class="api-key-row">
                    <span class="api-key-name">Keys</span>
                    <span class="api-key-value">Vault-backed, write-only (never echoed)</span>
                </div>
                <button
                    class="add-btn"
                    style="margin-top: var(--skin-space-md);"
                    @click=${(e: Event) => { e.stopPropagation(); this._openModels(); }}
                >
                    <span class="material-symbols-outlined">settings_suggest</span>
                    Open Models Settings
                </button>
            </div>

            <!-- AgentIQ knobs: agent configuration, not chat chrome -->
            <div class="section" style="margin-top: var(--skin-space-md);">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">tune</span>
                    Agent knobs (IQ)
                </h3>
                <p class="section-desc">
                    Personality knobs for this capsule. Persisted to Capsule.persona_config.knobs.
                    Derived values below are computed by the server.
                </p>
                <soma-agent-iq .capsuleId=${this._activeCapsuleId || ''}></soma-agent-iq>
            </div>
        `;
    }

    private _openModels() {
        window.dispatchEvent(new CustomEvent('soma-navigate', { detail: { route: '/settings/models' } }));
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

            <!-- The real full surface for providers, keys, and model setup -->
            <div class="section">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">settings_suggest</span>
                    Providers
                </h3>
                <p class="section-desc">
                    Models, provider keys, and Chat / Help / Memory bindings are managed on the Models screen.
                </p>
                <button class="add-btn" @click=${() => this._openModels()}>
                    <span class="material-symbols-outlined">open_in_new</span>
                    Manage providers, keys, and model setup
                </button>
            </div>
        `;
    }

    private _renderConnectivityTab() {
        return html`
            <div class="section">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">cable</span>
                    Service endpoints
                </h3>
                <p class="section-desc">
                    Every service URL and behaviour knob is an administrator parameter.
                    Edits save to InfrastructureConfig (the operator layer) and take
                    effect without a rebuild — including repointing the memory lane.
                </p>

                ${this._entitiesError
                    ? html`<p class="disabled-reason" role="status">${this._entitiesError}</p>`
                    : this._entities.length === 0
                        ? html`<p class="honest-note" role="status">No configurable services returned by the server.</p>`
                        : this._entities.map(
                              (e) => html`
                                  <settings-form
                                      entity=${e.entity}
                                      .permissions=${this._permissions}
                                      style="margin: var(--skin-space-md) 0 var(--skin-space-lg);"
                                  ></settings-form>
                              `
                          )}
            </div>

            <!-- Voice Settings -->
            <div class="section">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">mic</span>
                    Voice / Speech
                </h3>
                <p class="section-desc">Enable or disable voice input and output.</p>

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
                    <span class="material-symbols-outlined" style="font-size: var(--skin-text-base); vertical-align: middle; margin-right: var(--skin-space-xs);">download</span>
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
        // Leaving SomaBrain drops its form dirty bit so shell Save cannot
        // PUT connection fields while another tab is active.
        if (this._activeTab === 'somabrain' && tab !== 'somabrain') {
            this._isDirty = false;
        }
        this._activeTab = tab;
        if (tab === 'somabrain') {
            this._isDirty = this._somabrainPanel()?.isDirty ?? false;
        }
    }

    override async firstUpdated() {
        if (this.activeTab === 'models' || this.activeTab === 'external' || this.activeTab === 'voice'
            || this.activeTab === 'interface' || this.activeTab === 'tools' || this.activeTab === 'system'
            || this.activeTab === 'agent' || this.activeTab === 'connectivity'
            || this.activeTab === 'somabrain') {
            this._activeTab = this.activeTab;
        }
        await Promise.all([
            this._loadIdentity(),
            this._loadFeatureFlags(),
            this._loadSecretProviders(),
            this._loadEntities(),
            this._loadTools(),
            this._loadCapsuleId(),
        ]);
    }

    /** Tool catalog from GET /api/v2/tools/catalog (Capability). */
    private async _loadTools() {
        try {
            const rows = await apiClient.get<{ name: string; description?: string; category?: string; enabled: boolean }[]>(
                '/tools/catalog'
            );
            this._tools = (rows ?? []).map((t) => ({
                name: t.name,
                description: t.description ?? '',
                enabled: t.enabled,
            }));
            this._toolsError = '';
        } catch (error) {
            this._tools = [];
            this._toolsError = `Failed to load tools: ${error instanceof Error ? error.message : error}`;
        }
    }

    private async _toggleTool(name: string) {
        const tool = this._tools.find((t) => t.name === name);
        if (!tool) return;
        const next = !tool.enabled;
        try {
            await apiClient.put(`/tools/catalog/${encodeURIComponent(name)}`, {
                name,
                description: tool.description,
                category: 'general',
                enabled: next,
            });
            this._tools = this._tools.map((t) => (t.name === name ? { ...t, enabled: next } : t));
        } catch (error) {
            this._flash('error', `Failed to update ${name}: ${error instanceof Error ? error.message : error}`);
        }
    }

    /** The configurable-service inventory is server-owned. */
    private async _loadEntities() {
        try {
            const rows = await apiClient.get<{ entity: string; name: string; icon: string }[]>(
                '/core/settings/'
            );
            this._entities = rows ?? [];
            this._entitiesError = '';
        } catch (error) {
            this._entities = [];
            this._entitiesError = `Failed to load service settings: ${error instanceof Error ? error.message : error}`;
        }
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
            // SomaBrain owns its own PUT — do not double-write feature flags
            // when the operator is only editing that form.
            if (this._activeTab === 'somabrain') {
                const panel = this._somabrainPanel();
                if (!panel) {
                    throw new Error('SomaBrain panel is not mounted');
                }
                const ok = await panel.save();
                if (!ok) {
                    this._saveStatus = {
                        kind: 'error',
                        text: panel.isDirty
                            ? "Couldn't save SomaBrain settings."
                            : 'No unsaved SomaBrain changes.',
                    };
                    return;
                }
                this._isDirty = false;
                this._saveStatus = { kind: 'ok', text: 'SomaBrain settings saved.' };
                return;
            }

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
        'soma-settings': SomaSettings;
    }
}
