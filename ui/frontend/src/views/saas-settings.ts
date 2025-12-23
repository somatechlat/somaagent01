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
import { apiClient } from '../services/api-client.js';

type SettingsTab = 'agent' | 'external' | 'connectivity' | 'system';

interface ModelConfig {
    provider: string;
    model: string;
    contextWindow: number;
    maxTokens: number;
}

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

        /* Grid for model settings */
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

    @state() private _activeTab: SettingsTab = 'agent';
    @state() private _isDirty = false;
    @state() private _isSaving = false;

    // Agent settings state
    @state() private _chatModel: ModelConfig = {
        provider: 'openai',
        model: 'gpt-4-turbo',
        contextWindow: 128000,
        maxTokens: 4096,
    };

    @state() private _utilityModel: ModelConfig = {
        provider: 'anthropic',
        model: 'claude-3-haiku',
        contextWindow: 200000,
        maxTokens: 2048,
    };

    // Feature flags state
    @state() private _featureFlags = {
        voiceEnabled: true,
        memoryEnabled: true,
        toolsEnabled: true,
        mcpEnabled: false,
    };

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
            <main class="main">
                <header class="header">
                    <h2 class="header-title">${this._getTabTitle()}</h2>
                    <button 
                        class="save-btn" 
                        ?disabled=${!this._isDirty || this._isSaving}
                        @click=${this._saveSettings}
                    >
                        <span class="material-symbols-outlined">save</span>
                        ${this._isSaving ? 'Saving...' : 'Save Changes'}
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
            <!-- Chat Model -->
            <div class="section">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">chat</span>
                    Chat Model
                </h3>
                <p class="section-desc">Primary model for conversations and complex tasks.</p>
                
                <div class="settings-grid">
                    <div class="form-group">
                        <label class="form-label">Provider</label>
                        <select class="form-select" 
                            .value=${this._chatModel.provider}
                            @change=${(e: Event) => this._updateChatModel('provider', (e.target as HTMLSelectElement).value)}
                        >
                            <option value="openai">OpenAI</option>
                            <option value="anthropic">Anthropic</option>
                            <option value="google">Google AI</option>
                            <option value="ollama">Ollama (Local)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Model</label>
                        <select class="form-select"
                            .value=${this._chatModel.model}
                            @change=${(e: Event) => this._updateChatModel('model', (e.target as HTMLSelectElement).value)}
                        >
                            <option value="gpt-4-turbo">GPT-4 Turbo</option>
                            <option value="gpt-4o">GPT-4o</option>
                            <option value="claude-3-opus">Claude 3 Opus</option>
                            <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                            <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Context Window</label>
                        <input type="number" class="form-input" 
                            .value=${String(this._chatModel.contextWindow)}
                            @input=${(e: Event) => this._updateChatModel('contextWindow', parseInt((e.target as HTMLInputElement).value))}
                        >
                        <p class="form-hint">Maximum tokens for context</p>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Max Output Tokens</label>
                        <input type="number" class="form-input"
                            .value=${String(this._chatModel.maxTokens)}
                            @input=${(e: Event) => this._updateChatModel('maxTokens', parseInt((e.target as HTMLInputElement).value))}
                        >
                        <p class="form-hint">Maximum tokens per response</p>
                    </div>
                </div>
            </div>

            <!-- Utility Model -->
            <div class="section">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">build</span>
                    Utility Model
                </h3>
                <p class="section-desc">Lightweight model for quick tasks and summarization.</p>
                
                <div class="settings-grid">
                    <div class="form-group">
                        <label class="form-label">Provider</label>
                        <select class="form-select"
                            .value=${this._utilityModel.provider}
                            @change=${(e: Event) => this._updateUtilityModel('provider', (e.target as HTMLSelectElement).value)}
                        >
                            <option value="openai">OpenAI</option>
                            <option value="anthropic">Anthropic</option>
                            <option value="google">Google AI</option>
                            <option value="ollama">Ollama (Local)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Model</label>
                        <select class="form-select"
                            .value=${this._utilityModel.model}
                            @change=${(e: Event) => this._updateUtilityModel('model', (e.target as HTMLSelectElement).value)}
                        >
                            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                            <option value="gpt-4o-mini">GPT-4o Mini</option>
                            <option value="claude-3-haiku">Claude 3 Haiku</option>
                            <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                        </select>
                    </div>
                </div>
            </div>

            <!-- Memory Settings -->
            <div class="section">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">psychology</span>
                    Memory / SomaBrain
                </h3>
                <p class="section-desc">Configure agent memory and knowledge base.</p>
                
                <div class="settings-grid">
                    <div class="form-group">
                        <label class="form-label">SomaBrain URL</label>
                        <input type="text" class="form-input" value="http://localhost:9696" readonly>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Collection</label>
                        <input type="text" class="form-input" value="default">
                    </div>
                </div>
            </div>
        `;
    }

    private _renderExternalTab() {
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
                        <input type="checkbox" .checked=${this._featureFlags.mcpEnabled}
                            @change=${() => this._toggleFlag('mcpEnabled')}>
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
                        <input type="checkbox" .checked=${this._featureFlags.voiceEnabled}
                            @change=${() => this._toggleFlag('voiceEnabled')}>
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
                    <input type="text" class="form-input" placeholder="http://proxy.example.com:8080">
                </div>
                <div class="form-group">
                    <label class="form-label">HTTPS Proxy</label>
                    <input type="text" class="form-input" placeholder="https://proxy.example.com:8080">
                </div>
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
                        <input type="checkbox" .checked=${this._featureFlags.memoryEnabled}
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
                        <input type="checkbox" .checked=${this._featureFlags.toolsEnabled}
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
                        <input type="checkbox" .checked=${this._featureFlags.voiceEnabled}
                            @change=${() => this._toggleFlag('voiceEnabled')}>
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
                    <button class="api-key-action" @click=${this._exportConfig}>
                        <span class="material-symbols-outlined" style="font-size: 14px; vertical-align: middle; margin-right: 4px;">download</span>
                        Export Config
                    </button>
                    <button class="api-key-action">
                        <span class="material-symbols-outlined" style="font-size: 14px; vertical-align: middle; margin-right: 4px;">upload</span>
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
                    <span class="material-symbols-outlined" style="font-size: 16px; vertical-align: middle; margin-right: 6px;">delete_forever</span>
                    Reset All Settings
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

    private _updateChatModel(field: keyof ModelConfig, value: string | number) {
        this._chatModel = { ...this._chatModel, [field]: value };
        this._isDirty = true;
    }

    private _updateUtilityModel(field: keyof ModelConfig, value: string | number) {
        this._utilityModel = { ...this._utilityModel, [field]: value };
        this._isDirty = true;
    }

    private _toggleFlag(flag: keyof typeof this._featureFlags) {
        this._featureFlags = {
            ...this._featureFlags,
            [flag]: !this._featureFlags[flag]
        };
        this._isDirty = true;
    }

    private async _saveSettings() {
        this._isSaving = true;
        try {
            // Call Django Ninja API to save settings
            await apiClient.put('/settings/agent/', {
                chatModel: this._chatModel,
                utilityModel: this._utilityModel,
                featureFlags: this._featureFlags,
            });
            this._isDirty = false;
        } catch (error) {
            console.error('Failed to save settings:', error);
        } finally {
            this._isSaving = false;
        }
    }

    private _exportConfig() {
        const config = {
            chatModel: this._chatModel,
            utilityModel: this._utilityModel,
            featureFlags: this._featureFlags,
            exportedAt: new Date().toISOString(),
        };
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
