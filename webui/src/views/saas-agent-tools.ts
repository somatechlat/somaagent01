/**
 * Agent Tools & Capabilities Screen
 *
 * Route: /agents/:id/tools
 * Enables/disables tools for a specific agent.
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient, ApiError } from '../services/api-client.js';

import '../components/saas-sidebar.js';

interface ToolInfo {
    name: string;
    description: string;
    input_schema?: Record<string, unknown> | null;
}

interface AgentToolsConfig {
    agent_id: string;
    available_tools: ToolInfo[];
    enabled_tools: string[];
}

@customElement('saas-agent-tools')
export class SaasAgentTools extends LitElement {
    static styles = css`
        :host {
            display: flex;
            height: 100vh;
            background: var(--aaas-bg-void, #0f172a);
            font-family: var(--aaas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            color: var(--aaas-text-main, #e2e8f0);
        }

        * { box-sizing: border-box; }

        .sidebar {
            width: var(--aaas-sidebar-width, 260px);
            flex-shrink: 0;
        }

        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .header {
            height: var(--aaas-header-height, 64px);
            padding: 0 28px;
            border-bottom: 1px solid var(--aaas-border-color, rgba(255, 255, 255, 0.05));
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header-title {
            font-size: var(--aaas-text-xl, 18px);
            font-weight: 600;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .header-subtitle {
            font-size: var(--aaas-text-xs, 11px);
            color: var(--aaas-text-dim, #64748b);
            margin: 2px 0 0 0;
        }

        .save-btn {
            background: var(--aaas-accent, #3b82f6);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: var(--aaas-radius-md, 8px);
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .save-btn:hover {
            background: var(--aaas-primary-hover, #2563eb);
        }

        .save-btn:disabled {
            background: #475569;
            cursor: not-allowed;
        }

        .content {
            flex: 1;
            overflow-y: auto;
            padding: 28px;
        }

        .form {
            max-width: 960px;
            margin: 0 auto;
        }

        .section {
            background: var(--aaas-surface, rgba(30, 41, 59, 0.85));
            border: 1px solid var(--aaas-border-color, rgba(255, 255, 255, 0.05));
            border-radius: var(--aaas-radius-lg, 12px);
            margin-bottom: 20px;
            overflow: hidden;
        }

        .section-header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--aaas-border-color, rgba(255, 255, 255, 0.05));
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .section-title {
            font-size: 14px;
            font-weight: 600;
            margin: 0;
        }

        .section-desc {
            font-size: 12px;
            color: var(--aaas-text-dim, #64748b);
            margin: 4px 0 0 0;
        }

        .tool-list {
            display: flex;
            flex-direction: column;
        }

        .tool-item {
            padding: 16px 20px;
            border-bottom: 1px solid var(--aaas-border-color, rgba(255, 255, 255, 0.05));
            display: flex;
            align-items: flex-start;
            gap: 16px;
            transition: background 0.15s ease;
        }

        .tool-item:last-child {
            border-bottom: none;
        }

        .tool-item:hover {
            background: rgba(255, 255, 255, 0.02);
        }

        .tool-toggle {
            margin-top: 2px;
            width: 40px;
            height: 22px;
            border-radius: 11px;
            background: var(--aaas-border-color, rgba(255, 255, 255, 0.15));
            position: relative;
            cursor: pointer;
            flex-shrink: 0;
            transition: background 0.2s ease;
        }

        .tool-toggle.enabled {
            background: var(--aaas-success, #22c55e);
        }

        .tool-toggle::after {
            content: '';
            position: absolute;
            top: 2px;
            left: 2px;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: white;
            transition: transform 0.2s ease;
        }

        .tool-toggle.enabled::after {
            transform: translateX(18px);
        }

        .tool-body {
            flex: 1;
        }

        .tool-name {
            font-size: 14px;
            font-weight: 600;
            margin: 0 0 4px 0;
        }

        .tool-desc {
            font-size: 12px;
            color: var(--aaas-text-dim, #64748b);
            line-height: 1.5;
            margin: 0 0 8px 0;
        }

        .tool-schema {
            font-size: 11px;
            color: var(--aaas-text-muted, #94a3b8);
            background: rgba(15, 23, 42, 0.5);
            padding: 8px;
            border-radius: 6px;
            overflow-x: auto;
            font-family: var(--aaas-font-mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace);
        }

        .loading, .empty-state, .error-banner {
            padding: 40px;
            text-align: center;
            color: var(--aaas-text-dim, #64748b);
        }

        .error-banner {
            color: #fca5a5;
            background: rgba(239, 68, 68, 0.1);
            border-radius: var(--aaas-radius-md, 8px);
            margin-bottom: 20px;
        }
    `;

    @state() private agentId = '';
    @state() private tools: ToolInfo[] = [];
    @state() private enabled = new Set<string>();
    @state() private loading = true;
    @state() private saving = false;
    @state() private error = '';
    @state() private saveError = '';

    connectedCallback() {
        super.connectedCallback();
        const id = this._parseAgentId();
        if (id) {
            this.agentId = id;
            this._loadTools();
        } else {
            this.error = 'No agent ID provided in URL.';
            this.loading = false;
        }
    }

    private _parseAgentId(): string {
        const match = window.location.pathname.match(/^\/agents\/([^/]+)\/tools$/);
        return match?.[1] || '';
    }

    private async _loadTools() {
        this.loading = true;
        this.error = '';
        try {
            const data = await apiClient.get<AgentToolsConfig>(`/agents/${this.agentId}/tools`);
            this.tools = data.available_tools || [];
            this.enabled = new Set(data.enabled_tools || []);
        } catch (e) {
            this.error = e instanceof ApiError ? e.message : 'Failed to load agent tools.';
        }
        this.loading = false;
    }

    private _toggleTool(name: string) {
        const next = new Set(this.enabled);
        if (next.has(name)) {
            next.delete(name);
        } else {
            next.add(name);
        }
        this.enabled = next;
    }

    private async _save() {
        this.saving = true;
        this.saveError = '';
        try {
            const data = await apiClient.patch<AgentToolsConfig>(`/agents/${this.agentId}/tools`, {
                tools: Array.from(this.enabled),
            });
            this.enabled = new Set(data.enabled_tools || []);
        } catch (e) {
            this.saveError = e instanceof ApiError ? e.message : 'Failed to save tools.';
        }
        this.saving = false;
    }

    private _schemaSummary(schema?: Record<string, unknown> | null): string {
        if (!schema) return 'No parameters';
        const properties = (schema.properties || {}) as Record<string, unknown>;
        const required = (schema.required || []) as string[];
        const params = Object.entries(properties).map(([name, def]) => {
            const type = (def as Record<string, unknown>).type || 'any';
            const req = required.includes(name) ? '*' : '';
            return `${name}${req}: ${type}`;
        });
        return params.length ? params.join(', ') : 'No parameters';
    }

    render() {
        return html`
            <saas-sidebar class="sidebar"></saas-sidebar>

            <main class="main">
                <header class="header">
                    <div>
                        <h1 class="header-title">
                            <span class="material-symbols-outlined">construction</span>
                            Tools & Capabilities
                        </h1>
                        <p class="header-subtitle">Agent ${this.agentId}</p>
                    </div>
                    <button
                        class="save-btn"
                        @click=${this._save}
                        ?disabled=${this.saving || this.loading}
                    >
                        <span class="material-symbols-outlined">save</span>
                        ${this.saving ? 'Saving...' : 'Save Tools'}
                    </button>
                </header>

                <div class="content">
                    <div class="form">
                        ${this.saveError
                            ? html`<div class="error-banner">${this.saveError}</div>`
                            : ''}

                        <div class="section">
                            <div class="section-header">
                                <div>
                                    <h2 class="section-title">Available Tools</h2>
                                    <p class="section-desc">
                                        Enable the tools this agent is allowed to use during conversations.
                                    </p>
                                </div>
                            </div>

                            ${this.loading
                                ? html`<div class="loading">Loading tools...</div>`
                                : this.error
                                  ? html`<div class="error-banner">${this.error}</div>`
                                  : this.tools.length === 0
                                    ? html`<div class="empty-state">No tools available.</div>`
                                    : html`
                                          <div class="tool-list">
                                              ${this.tools.map(
                                                  (tool) => html`
                                                      <div class="tool-item">
                                                          <div
                                                              class="tool-toggle ${this.enabled.has(
                                                                  tool.name
                                                              )
                                                                  ? 'enabled'
                                                                  : ''}"
                                                              @click=${() =>
                                                                  this._toggleTool(tool.name)}
                                                              role="switch"
                                                              aria-checked=${this.enabled.has(
                                                                  tool.name
                                                              )}
                                                          ></div>
                                                          <div class="tool-body">
                                                              <h3 class="tool-name">
                                                                  ${tool.name}
                                                              </h3>
                                                              <p class="tool-desc">
                                                                  ${tool.description}
                                                              </p>
                                                              <div class="tool-schema">
                                                                  ${this._schemaSummary(
                                                                      tool.input_schema
                                                                  )}
                                                              </div>
                                                          </div>
                                                      </div>
                                                  `
                                              )}
                                          </div>
                                      `}
                        </div>
                    </div>
                </div>
            </main>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-agent-tools': SaasAgentTools;
    }
}
