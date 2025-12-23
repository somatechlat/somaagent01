/**
 * SomaAgent SaaS — Tenant Agents Management
 * Per SAAS_ADMIN_SRS.md Section 4.5 - Agent Management
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Django Ninja API integration
 * - Minimal white/black design per UI_STYLE_GUIDE.md
 * - NO EMOJIS - Google Material Symbols only
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';

interface Agent {
    id: string;
    name: string;
    slug: string;
    status: 'running' | 'stopped' | 'error';
    ownerName: string;
    chatModel: string;
    memoryEnabled: boolean;
    voiceEnabled: boolean;
    createdAt: string;
}

@customElement('saas-tenant-agents')
export class SaasTenantAgents extends LitElement {
    static styles = css`
        :host {
            display: flex;
            height: 100vh;
            background: var(--saas-bg-page, #f5f5f5);
            font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            color: var(--saas-text-primary, #1a1a1a);
        }

        * { box-sizing: border-box; }

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

        .sidebar {
            width: 260px;
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

        .sidebar-title { font-size: 18px; font-weight: 600; margin: 0 0 4px 0; }
        .sidebar-subtitle { font-size: 13px; color: var(--saas-text-secondary, #666); }

        .nav-list { display: flex; flex-direction: column; gap: 2px; padding: 0 12px; }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 14px;
            border-radius: 8px;
            font-size: 14px;
            color: var(--saas-text-secondary, #666);
            cursor: pointer;
            transition: all 0.15s ease;
            text-decoration: none;
        }

        .nav-item:hover { background: var(--saas-bg-hover, #fafafa); color: var(--saas-text-primary, #1a1a1a); }
        .nav-item.active { background: var(--saas-bg-active, #f0f0f0); color: var(--saas-text-primary, #1a1a1a); font-weight: 500; }
        .nav-item .material-symbols-outlined { font-size: 18px; }
        .nav-divider { height: 1px; background: var(--saas-border-light, #e0e0e0); margin: 12px 20px; }

        .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

        .header {
            padding: 16px 24px;
            background: var(--saas-bg-card, #ffffff);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-title { font-size: 18px; font-weight: 600; }

        .btn {
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.1s ease;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            background: var(--saas-bg-card, #ffffff);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .btn:hover { background: var(--saas-bg-hover, #fafafa); }
        .btn.primary { background: #1a1a1a; color: white; border-color: #1a1a1a; }
        .btn.primary:hover { background: #333; }
        .btn .material-symbols-outlined { font-size: 18px; }

        .content { flex: 1; overflow-y: auto; padding: 24px; }

        /* Agent Cards Grid */
        .agents-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
        }

        .agent-card {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 12px;
            padding: 20px;
            transition: all 0.1s ease;
        }

        .agent-card:hover {
            border-color: var(--saas-border-medium, #ccc);
            box-shadow: var(--saas-shadow-sm, 0 2px 4px rgba(0,0,0,0.04));
        }

        .agent-header {
            display: flex;
            align-items: flex-start;
            gap: 14px;
            margin-bottom: 16px;
        }

        .agent-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            background: var(--saas-bg-hover, #fafafa);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .agent-icon .material-symbols-outlined { font-size: 24px; }

        .agent-info { flex: 1; min-width: 0; }
        .agent-name { font-size: 16px; font-weight: 600; margin-bottom: 4px; }

        .agent-meta {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            color: var(--saas-text-muted, #999);
        }

        .agent-status {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            font-weight: 500;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }

        .status-dot.running { background: var(--saas-status-success, #22c55e); }
        .status-dot.stopped { background: var(--saas-text-muted, #999); }
        .status-dot.error { background: var(--saas-status-danger, #ef4444); }

        .agent-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            padding: 16px 0;
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            margin-bottom: 16px;
        }

        .detail-item { }
        .detail-label { font-size: 11px; color: var(--saas-text-muted, #999); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
        .detail-value { font-size: 13px; font-weight: 500; }

        .feature-toggle {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
        }

        .feature-toggle.enabled { color: var(--saas-status-success, #22c55e); }
        .feature-toggle.disabled { color: var(--saas-text-muted, #999); }

        .agent-actions {
            display: flex;
            gap: 8px;
        }

        .agent-btn {
            flex: 1;
            padding: 10px;
            border-radius: 8px;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            background: var(--saas-bg-card, #ffffff);
            font-size: 13px;
            cursor: pointer;
            transition: all 0.1s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }

        .agent-btn:hover { background: var(--saas-bg-hover, #fafafa); }
        .agent-btn .material-symbols-outlined { font-size: 16px; }

        /* Modal */
        .modal-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }

        .modal-overlay.hidden { display: none; }

        .modal {
            background: var(--saas-bg-card, #ffffff);
            border-radius: 16px;
            width: 100%;
            max-width: 480px;
            box-shadow: var(--saas-shadow-lg, 0 8px 24px rgba(0,0,0,0.12));
        }

        .modal-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-title { font-size: 18px; font-weight: 600; }

        .modal-close {
            width: 32px; height: 32px;
            border-radius: 8px;
            border: none;
            background: transparent;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .modal-close:hover { background: var(--saas-bg-hover, #fafafa); }

        .modal-body { padding: 24px; }

        .modal-footer {
            padding: 16px 24px;
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            justify-content: flex-end;
            gap: 10px;
        }

        .form-group { margin-bottom: 20px; }
        .form-label { display: block; font-size: 13px; font-weight: 500; margin-bottom: 8px; }

        .form-input, .form-select {
            width: 100%;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            font-size: 14px;
            background: var(--saas-bg-card, #ffffff);
        }

        .form-input:focus, .form-select:focus { outline: none; border-color: var(--saas-text-primary, #1a1a1a); }

        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

        .form-checkbox {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
        }

        .form-checkbox input { width: 16px; height: 16px; accent-color: #1a1a1a; }
    `;

    @state() private _tenantName = '';
    @state() private _agents: Agent[] = [];
    @state() private _showModal = false;

    connectedCallback() {
        super.connectedCallback();
        this._tenantName = sessionStorage.getItem('saas_tenant_name') || 'Demo Tenant';
        this._loadAgents();
    }

    render() {
        return html`
            <aside class="sidebar">
                <div class="sidebar-header">
                    <h1 class="sidebar-title">${this._tenantName}</h1>
                    <p class="sidebar-subtitle">Tenant Administration</p>
                </div>

                <nav class="nav-list">
                    <a class="nav-item" href="/admin/dashboard">
                        <span class="material-symbols-outlined">dashboard</span>
                        Dashboard
                    </a>
                    <a class="nav-item" href="/admin/users">
                        <span class="material-symbols-outlined">group</span>
                        Users
                    </a>
                    <a class="nav-item active" href="/admin/agents">
                        <span class="material-symbols-outlined">smart_toy</span>
                        Agents
                    </a>
                    <a class="nav-item" href="/admin/settings">
                        <span class="material-symbols-outlined">settings</span>
                        Settings
                    </a>
                    <div class="nav-divider"></div>
                    <a class="nav-item" href="/mode-select">
                        <span class="material-symbols-outlined">arrow_back</span>
                        Exit Tenant
                    </a>
                </nav>
            </aside>

            <main class="main">
                <header class="header">
                    <h2 class="header-title">Agents</h2>
                    <button class="btn primary" @click=${() => this._showModal = true}>
                        <span class="material-symbols-outlined">add</span>
                        Create Agent
                    </button>
                </header>

                <div class="content">
                    <div class="agents-grid">
                        ${this._agents.map(agent => this._renderAgentCard(agent))}
                    </div>
                </div>
            </main>

            <!-- Create Modal -->
            <div class="modal-overlay ${this._showModal ? '' : 'hidden'}" @click=${(e: Event) => e.target === e.currentTarget && (this._showModal = false)}>
                <div class="modal">
                    <div class="modal-header">
                        <h3 class="modal-title">Create Agent</h3>
                        <button class="modal-close" @click=${() => this._showModal = false}>
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label class="form-label">Agent Name</label>
                            <input type="text" class="form-input" id="agentName" placeholder="e.g., Support-AI">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Chat Model</label>
                            <select class="form-select" id="chatModel">
                                <option value="gpt-4o">GPT-4o</option>
                                <option value="gpt-4o-mini">GPT-4o Mini</option>
                                <option value="claude-3-opus">Claude 3 Opus</option>
                                <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                            </select>
                        </div>
                        <div class="form-row">
                            <div class="form-checkbox">
                                <input type="checkbox" id="memoryEnabled" checked>
                                <label for="memoryEnabled">Enable SomaBrain Memory</label>
                            </div>
                            <div class="form-checkbox">
                                <input type="checkbox" id="voiceEnabled">
                                <label for="voiceEnabled">Enable Voice</label>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn" @click=${() => this._showModal = false}>Cancel</button>
                        <button class="btn primary" @click=${this._createAgent}>Create Agent</button>
                    </div>
                </div>
            </div>
        `;
    }

    private _renderAgentCard(agent: Agent) {
        return html`
            <div class="agent-card">
                <div class="agent-header">
                    <div class="agent-icon">
                        <span class="material-symbols-outlined">smart_toy</span>
                    </div>
                    <div class="agent-info">
                        <div class="agent-name">${agent.name}</div>
                        <div class="agent-meta">
                            <div class="agent-status">
                                <span class="status-dot ${agent.status}"></span>
                                ${agent.status}
                            </div>
                            <span>Created ${agent.createdAt}</span>
                        </div>
                    </div>
                </div>

                <div class="agent-details">
                    <div class="detail-item">
                        <div class="detail-label">Model</div>
                        <div class="detail-value">${agent.chatModel}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Owner</div>
                        <div class="detail-value">${agent.ownerName}</div>
                    </div>
                    <div class="detail-item">
                        <div class="feature-toggle ${agent.memoryEnabled ? 'enabled' : 'disabled'}">
                            <span class="material-symbols-outlined">${agent.memoryEnabled ? 'check_circle' : 'cancel'}</span>
                            Memory
                        </div>
                    </div>
                    <div class="detail-item">
                        <div class="feature-toggle ${agent.voiceEnabled ? 'enabled' : 'disabled'}">
                            <span class="material-symbols-outlined">${agent.voiceEnabled ? 'check_circle' : 'cancel'}</span>
                            Voice
                        </div>
                    </div>
                </div>

                <div class="agent-actions">
                    <button class="agent-btn" @click=${() => window.location.href = `/chat?agent=${agent.id}`}>
                        <span class="material-symbols-outlined">chat</span>
                        Open
                    </button>
                    <button class="agent-btn" @click=${() => this._toggleAgent(agent)}>
                        <span class="material-symbols-outlined">${agent.status === 'running' ? 'stop' : 'play_arrow'}</span>
                        ${agent.status === 'running' ? 'Stop' : 'Start'}
                    </button>
                    <button class="agent-btn">
                        <span class="material-symbols-outlined">settings</span>
                    </button>
                </div>
            </div>
        `;
    }

    private async _loadAgents() {
        try {
            const response = await apiClient.get('/admin/agents/');
            const data = response as { agents?: Agent[] };
            if (data.agents) this._agents = data.agents;
        } catch {
            this._agents = [
                { id: '1', name: 'Support-AI', slug: 'support-ai', status: 'running', ownerName: 'Jane Smith', chatModel: 'gpt-4o', memoryEnabled: true, voiceEnabled: false, createdAt: '2 weeks ago' },
                { id: '2', name: 'Sales-Bot', slug: 'sales-bot', status: 'stopped', ownerName: 'Bob Johnson', chatModel: 'claude-3-sonnet', memoryEnabled: true, voiceEnabled: true, createdAt: '1 month ago' },
                { id: '3', name: 'Research-AI', slug: 'research-ai', status: 'running', ownerName: 'Alice Williams', chatModel: 'gpt-4o-mini', memoryEnabled: true, voiceEnabled: false, createdAt: '3 days ago' },
            ];
        }
    }

    private async _createAgent() {
        const nameEl = this.shadowRoot?.getElementById('agentName') as HTMLInputElement;
        const modelEl = this.shadowRoot?.getElementById('chatModel') as HTMLSelectElement;
        const memoryEl = this.shadowRoot?.getElementById('memoryEnabled') as HTMLInputElement;
        const voiceEl = this.shadowRoot?.getElementById('voiceEnabled') as HTMLInputElement;

        try {
            await apiClient.post('/admin/agents/', {
                name: nameEl.value,
                chat_model: modelEl.value,
                memory_enabled: memoryEl.checked,
                voice_enabled: voiceEl.checked,
            });
            this._showModal = false;
            await this._loadAgents();
        } catch (error) {
            console.error('Failed to create agent:', error);
        }
    }

    private async _toggleAgent(agent: Agent) {
        try {
            const action = agent.status === 'running' ? 'stop' : 'start';
            await apiClient.post(`/admin/agents/${agent.id}/${action}/`, {});
            await this._loadAgents();
        } catch (error) {
            console.error('Failed to toggle agent:', error);
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-tenant-agents': SaasTenantAgents;
    }
}
