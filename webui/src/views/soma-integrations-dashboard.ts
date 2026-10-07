/**
 * Platform Integrations Dashboard
 * Manage external service connections: Keycloak, SMTP, OpenAI, S3
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Uses /api/v2/aaas/integrations endpoints
 * - Permission-aware (platform:view_settings, platform:manage_settings)
 * - Per SRS-SOMA-INTEGRATIONS.md
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';

interface Integration {
    provider: string;
    name: string;
    icon: string;
    connected: boolean;
    status: string;
    status_message?: string;
    last_check?: string;
    last_24h_events: number;
}

interface TestResult {
    provider: string;
    success: boolean;
    message: string;
    latency_ms: number;
}

@customElement('soma-integrations-dashboard')
export class SomaIntegrationsDashboard extends LitElement {
    static styles = css`
    :host {
      display: flex;
      height: 100vh;
      background: var(--soma-bg-page, #f5f5f5);
      font-family: var(--soma-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
      color: var(--soma-text-primary, #1a1a1a);
    }

    * { box-sizing: border-box; }

    .material-symbols-outlined {
      font-family: 'Material Symbols Outlined';
      font-weight: normal;
      font-style: normal;
      font-size: 20px;
      line-height: 1;
      display: inline-block;
    }

    .sidebar { width: 260px; background: #fff; border-right: 1px solid #e0e0e0; flex-shrink: 0; }
    .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

    .header {
      padding: 20px 32px;
      background: #fff;
      border-bottom: 1px solid #e0e0e0;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .header-title { font-size: 22px; font-weight: 600; margin: 0; }
    .header-subtitle { font-size: 13px; color: #999; margin: 4px 0 0 0; }

    .btn {
      padding: 10px 18px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      border: 1px solid #e0e0e0;
      background: #fff;
      transition: all 0.1s ease;
    }

    .btn:hover { background: #fafafa; }

    .content { flex: 1; overflow-y: auto; padding: 32px; }

    /* Integration Cards Grid */
    .integrations-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 24px;
    }

    .integration-card {
      background: #fff;
      border: 1px solid #e0e0e0;
      border-radius: 12px;
      padding: 24px;
      transition: all 0.2s ease;
    }

    .integration-card:hover {
      box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }

    .integration-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 16px;
    }

    .integration-icon {
      font-size: 32px;
      margin-right: 12px;
    }

    .integration-title { font-size: 16px; font-weight: 600; }

    .status-badge {
      padding: 4px 10px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
    }

    .status-connected { background: #dcfce7; color: #166534; }
    .status-error { background: #fee2e2; color: #991b1b; }
    .status-unconfigured { background: #f3f4f6; color: #6b7280; }

    .integration-stats {
      display: flex;
      gap: 16px;
      margin-bottom: 16px;
      font-size: 12px;
      color: #666;
    }

    .stat { display: flex; align-items: center; gap: 4px; }

    .integration-message {
      font-size: 12px;
      color: #666;
      margin-bottom: 16px;
      padding: 8px 12px;
      background: #f9fafb;
      border-radius: 6px;
    }

    .integration-actions {
      display: flex;
      gap: 8px;
    }

    .action-btn {
      padding: 8px 14px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      border: 1px solid #e0e0e0;
      background: #fff;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .action-btn:hover { background: #fafafa; }
    .action-btn.primary { background: #1a1a1a; color: #fff; border-color: #1a1a1a; }
    .action-btn.primary:hover { background: #333; }

    .action-btn .material-symbols-outlined { font-size: 16px; }

    /* Test Result Toast */
    .toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      padding: 16px 24px;
      border-radius: 8px;
      background: #1a1a1a;
      color: #fff;
      font-size: 13px;
      display: flex;
      align-items: center;
      gap: 12px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 1000;
    }

    .toast.success { background: #166534; }
    .toast.error { background: #991b1b; }

    .loading { display: flex; justify-content: center; align-items: center; padding: 60px; color: #999; }

    .config-panel {
      margin-top: 12px;
      padding: 14px;
      border: 1px solid var(--soma-border, #e0e0e0);
      border-radius: 8px;
      background: var(--soma-bg-surface, #fafafa);
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .config-loading { color: var(--soma-text-muted, #999); font-size: 13px; }
    .config-field { display: flex; flex-direction: column; gap: 4px; }
    .config-label { font-size: 12px; font-weight: 600; color: var(--soma-text-secondary, #666); }
    .config-input {
      padding: 8px 10px;
      border: 1px solid var(--soma-border, #e0e0e0);
      border-radius: 6px;
      font-size: 13px;
      background: var(--soma-bg-input, #fff);
      color: var(--soma-text-primary, #1a1a1a);
    }
    .config-input:focus { outline: none; border-color: var(--soma-accent, #2563eb); }
    .config-hint { font-size: 11px; color: var(--soma-text-muted, #999); }
    .config-actions { display: flex; justify-content: flex-end; }
  `;

    @state() private integrations: Integration[] = [];
    @state() private loading = true;
    @state() private error: string | null = null;
    @state() private testing: string | null = null;
    @state() private toast: { message: string; type: string } | null = null;

    /** Provider whose config panel is open, or null when every card is closed. */
    @state() private configuring: string | null = null;
    @state() private configLoading = false;
    @state() private saving = false;
    /** Form state for the open panel. `apiKey` is empty until the operator types. */
    @state() private draft: { endpoint: string; apiKey: string; apiKeyMasked: string | null } = {
        endpoint: '',
        apiKey: '',
        apiKeyMasked: null,
    };

    connectedCallback() {
        super.connectedCallback();
        this.loadIntegrations();
    }

    private async loadIntegrations() {
        this.loading = true;
        this.error = null;
        try {
            const res = await fetch('/api/v2/aaas/integrations', { credentials: 'include' });
            if (res.ok) {
                this.integrations = await res.json();
            } else {
                this.integrations = [];
                this.error = `Failed to load integrations (HTTP ${res.status})`;
            }
        } catch {
            this.integrations = [];
            this.error = 'Failed to load integrations';
        } finally {
            this.loading = false;
        }
    }

    private async testConnection(provider: string) {
        this.testing = provider;
        try {
            const res = await fetch(`/api/v2/aaas/integrations/${provider}/test`, {
                method: 'POST',
                credentials: 'include',
            });
            const result: TestResult = await res.json();
            this.showToast(result.success ? `${result.message} (${result.latency_ms}ms)` : result.message, result.success ? 'success' : 'error');
            this.loadIntegrations();
        } catch (e) {
            this.showToast('Connection test failed', 'error');
        } finally {
            this.testing = null;
        }
    }

    private showToast(message: string, type: string) {
        this.toast = { message, type };
        setTimeout(() => { this.toast = null; }, 4000);
    }

    /**
     * Load a provider's configuration and open its panel.
     *
     * GET returns the secret only as `api_key_masked` (e.g. "sk-...4f3d") —
     * the plaintext never comes back, so the field starts empty and the
     * masked value is shown as the placeholder. Leaving it empty on save
     * keeps the stored key.
     */
    private async openConfig(provider: string) {
        if (this.configuring === provider) {
            this.configuring = null;
            return;
        }
        this.configuring = provider;
        this.configLoading = true;
        this.draft = { endpoint: '', apiKey: '', apiKeyMasked: null };
        try {
            const res = await fetch(`/api/v2/aaas/integrations/${provider}`, {
                credentials: 'include',
            });
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}`);
            }
            const cfg: {
                endpoint?: string | null;
                api_key_masked?: string | null;
            } = await res.json();
            this.draft = {
                endpoint: cfg.endpoint ?? '',
                apiKey: '',
                apiKeyMasked: cfg.api_key_masked ?? null,
            };
        } catch {
            this.showToast('Failed to load integration settings', 'error');
            this.configuring = null;
        } finally {
            this.configLoading = false;
        }
    }

    /**
     * Persist the panel. `api_key` is sent only when a new value was typed:
     * sending an empty string would be read by the API as "set the key to
     * empty", not "leave it alone".
     */
    private async saveConfig(provider: string) {
        this.saving = true;
        try {
            const body: { endpoint?: string; api_key?: string } = {};
            if (this.draft.endpoint) {
                body.endpoint = this.draft.endpoint;
            }
            if (this.draft.apiKey) {
                body.api_key = this.draft.apiKey;
            }
            const res = await fetch(`/api/v2/aaas/integrations/${provider}`, {
                method: 'PUT',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            if (!res.ok) {
                const detail = await res.text();
                throw new Error(detail || `HTTP ${res.status}`);
            }
            this.showToast('Integration settings saved', 'success');
            this.configuring = null;
            this.draft = { endpoint: '', apiKey: '', apiKeyMasked: null };
            await this.loadIntegrations();
        } catch (e) {
            this.showToast(e instanceof Error ? e.message : 'Failed to save settings', 'error');
        } finally {
            this.saving = false;
        }
    }

    private getStatusClass(status: string): string {
        if (status === 'connected') return 'status-connected';
        if (status === 'error') return 'status-error';
        return 'status-unconfigured';
    }

    render() {
        return html`
      <aside class="sidebar">
        <soma-sidebar active-route="/platform/integrations"></soma-sidebar>
      </aside>

      <main class="main">
        <header class="header">
          <div>
            <h1 class="header-title">🔌 Platform Integrations</h1>
            <p class="header-subtitle">Manage external service connections</p>
          </div>
          <button class="btn" @click=${() => this.loadIntegrations()}>
            <span class="material-symbols-outlined">refresh</span>
            Refresh
          </button>
        </header>

        <div class="content">
          ${this.loading ? html`<div class="loading">Loading integrations...</div>` : html`
            ${this.error ? html`<div class="loading">${this.error}</div>` : nothing}
            <div class="integrations-grid">
              ${this.integrations.map(int => html`
                <div class="integration-card">
                  <div class="integration-header">
                    <div style="display: flex; align-items: center;">
                      <span class="integration-icon">${int.icon}</span>
                      <span class="integration-title">${int.name}</span>
                    </div>
                    <span class="status-badge ${this.getStatusClass(int.status)}">
                      ${int.status === 'connected' ? '✓ Connected' : int.status === 'error' ? '✗ Error' : 'Not Configured'}
                    </span>
                  </div>

                  <div class="integration-stats">
                    <div class="stat">
                      <span class="material-symbols-outlined" style="font-size: 14px;">event</span>
                      ${int.last_24h_events} events (24h)
                    </div>
                    ${int.last_check ? html`
                      <div class="stat">
                        <span class="material-symbols-outlined" style="font-size: 14px;">update</span>
                        Last check: ${new Date(int.last_check).toLocaleTimeString()}
                      </div>
                    ` : nothing}
                  </div>

                  ${int.status_message ? html`
                    <div class="integration-message">${int.status_message}</div>
                  ` : nothing}

                  <div class="integration-actions">
                    <button class="action-btn" @click=${() => this.testConnection(int.provider)} ?disabled=${this.testing === int.provider}>
                      <span class="material-symbols-outlined">${this.testing === int.provider ? 'hourglass_top' : 'cable'}</span>
                      ${this.testing === int.provider ? 'Testing...' : 'Test'}
                    </button>
                    <button class="action-btn primary" @click=${() => this.openConfig(int.provider)} ?disabled=${this.configLoading}>
                      <span class="material-symbols-outlined">settings</span>
                      ${this.configuring === int.provider ? 'Close' : 'Configure'}
                    </button>
                  </div>

                  ${this.configuring === int.provider ? html`
                    <div class="config-panel">
                      ${this.configLoading ? html`<div class="config-loading">Loading settings...</div>` : html`
                        <div class="config-field">
                          <label class="config-label">Endpoint</label>
                          <input class="config-input" type="url" placeholder="https://"
                            .value=${this.draft.endpoint}
                            @input=${(e: Event) => this.draft = { ...this.draft, endpoint: (e.target as HTMLInputElement).value }}>
                        </div>
                        <div class="config-field">
                          <label class="config-label">API key</label>
                          <input class="config-input" type="password" autocomplete="new-password"
                            placeholder=${this.draft.apiKeyMasked ?? 'Not set'}
                            .value=${this.draft.apiKey}
                            @input=${(e: Event) => this.draft = { ...this.draft, apiKey: (e.target as HTMLInputElement).value }}>
                          <span class="config-hint">
                            ${this.draft.apiKeyMasked
                              ? `Currently ${this.draft.apiKeyMasked}. Leave blank to keep it.`
                              : 'No key stored yet.'}
                          </span>
                        </div>
                        <div class="config-actions">
                          <button class="action-btn primary" ?disabled=${this.saving}
                            @click=${() => this.saveConfig(int.provider)}>
                            <span class="material-symbols-outlined">save</span>
                            ${this.saving ? 'Saving...' : 'Save'}
                          </button>
                        </div>
                      `}
                    </div>
                  ` : nothing}
                </div>
              `)}
            </div>
          `}
        </div>
      </main>

      ${this.toast ? html`
        <div class="toast ${this.toast.type}">
          <span class="material-symbols-outlined">${this.toast.type === 'success' ? 'check_circle' : 'error'}</span>
          ${this.toast.message}
        </div>
      ` : nothing}
    `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-integrations-dashboard': SomaIntegrationsDashboard;
    }
}
