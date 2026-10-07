/**
 * SomaAgent Soma — Channels Settings (D7 / BR-05)
 * WhatsApp / Telegram / Email Capsule module + Channel configuration.
 *
 * VIBE: real APIs only, write-only tokens, fail-closed empty states.
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import '../components/soma-status-badge.js';
import '../components/soma-button.js';

type ChannelKind = 'whatsapp' | 'telegram' | 'email' | 'slack' | 'web';

interface ChannelRow {
    id: string;
    kind: ChannelKind;
    status: string;
    config: Record<string, unknown>;
    capsule_id: string | null;
    created_at: string;
}

interface ModuleRow {
    name: string;
    title: string;
    enabled: boolean;
    always_enabled: boolean;
    feature_flag: string | null;
}

@customElement('soma-settings-channels')
export class SomaSettingsChannels extends LitElement {
    static styles = css`
        :host {
            display: block;
            padding: 24px;
            max-width: 960px;
            color: var(--soma-text-primary, #1a1a1a);
            font-family: var(--soma-font-sans, system-ui, sans-serif);
        }
        h1 { font-size: 22px; margin: 0 0 8px; }
        h2 { font-size: 16px; margin: 28px 0 12px; }
        .muted { color: var(--soma-text-secondary, #666); font-size: 13px; }
        .card {
            border: 1px solid var(--soma-border-light, #e0e0e0);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
            background: var(--soma-bg-card, #fff);
        }
        .row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
        .grow { flex: 1; min-width: 180px; }
        label { display: block; font-size: 12px; font-weight: 600; margin-bottom: 4px; }
        input, select, textarea {
            width: 100%;
            padding: 8px 10px;
            border: 1px solid var(--soma-border-light, #ddd);
            border-radius: 6px;
            background: var(--soma-bg-input, #fff);
            color: inherit;
            font: inherit;
        }
        .actions { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
        .empty { padding: 24px; text-align: center; color: var(--soma-text-secondary, #666); }
        .error { color: var(--soma-danger, #b91c1c); margin: 8px 0; }
        .ok { color: var(--soma-success, #15803d); margin: 8px 0; }
    `;

    @state() private _channels: ChannelRow[] = [];
    @state() private _modules: ModuleRow[] = [];
    @state() private _error = '';
    @state() private _notice = '';
    @state() private _kind: ChannelKind = 'whatsapp';
    @state() private _capsuleId = '';
    @state() private _botToken = '';
    @state() private _mode = 'poll';
    @state() private _allowed = '';
    @state() private _groupMode = 'mention';
    @state() private _loading = false;

    connectedCallback() {
        super.connectedCallback();
        void this._load();
    }

    private async _load() {
        this._loading = true;
        this._error = '';
        try {
            const [channels, modules] = await Promise.all([
                apiClient.get('/bridges/channels') as Promise<{ channels?: ChannelRow[] } | ChannelRow[]>,
                apiClient.get('/modules') as Promise<{ modules?: ModuleRow[] } | ModuleRow[]>,
            ]);
            const chList = Array.isArray(channels) ? channels : channels.channels ?? [];
            const modList = Array.isArray(modules) ? modules : modules.modules ?? [];
            this._channels = chList;
            this._modules = modList.filter((m) =>
                ['mod_whatsapp', 'mod_telegram', 'mod_email'].includes(m.name),
            );
        } catch (e) {
            this._error = e instanceof Error ? e.message : 'Failed to load channels';
        } finally {
            this._loading = false;
        }
    }

    private async _createChannel() {
        this._error = '';
        this._notice = '';
        try {
            const config: Record<string, unknown> = {};
            if (this._kind === 'telegram') {
                if (this._botToken) config.bot_token = this._botToken;
                config.mode = this._mode;
                config.group_mode = this._groupMode;
                if (this._allowed) {
                    config.allowed_users = this._allowed.split(',').map((s) => s.trim()).filter(Boolean);
                }
            } else if (this._kind === 'whatsapp') {
                config.mode = this._mode === 'webhook' ? 'cloud' : 'baileys';
                if (this._allowed) {
                    config.allowed_numbers = this._allowed.split(',').map((s) => s.trim()).filter(Boolean);
                }
            }
            await apiClient.post('/bridges/channels', {
                kind: this._kind,
                status: 'pending',
                capsule_id: this._capsuleId || null,
                config,
            });
            this._botToken = '';
            this._notice = 'Channel created';
            await this._load();
        } catch (e) {
            this._error = e instanceof Error ? e.message : 'Create failed';
        }
    }

    private async _moduleToggle(name: string, enable: boolean) {
        this._error = '';
        try {
            await apiClient.post(`/modules/${name}/${enable ? 'enable' : 'disable'}`, {});
            await this._load();
        } catch (e) {
            this._error = e instanceof Error ? e.message : 'Toggle failed';
        }
    }

    private async _lifecycle(id: string, action: 'start' | 'stop' | 'test') {
        this._error = '';
        this._notice = '';
        try {
            const res = (await apiClient.post(
                `/bridges/channels/${id}/${action}`,
                {},
            )) as { message?: string; ok?: boolean };
            this._notice = res?.message || `${action} completed`;
            await this._load();
        } catch (e) {
            this._error = e instanceof Error ? e.message : `${action} failed`;
        }
    }

    private async _deleteChannel(id: string) {
        if (!confirm('Delete this channel?')) return;
        try {
            await apiClient.delete(`/bridges/channels/${id}`);
            await this._load();
        } catch (e) {
            this._error = e instanceof Error ? e.message : 'Delete failed';
        }
    }

    render() {
        return html`
            <h1>Channels</h1>
            <p class="muted">
                Messaging Capsule modules — WhatsApp, Telegram, Email. Credentials are
                write-only; unbound channels fail closed.
            </p>
            ${this._error ? html`<div class="error">${this._error}</div>` : nothing}
            ${this._notice ? html`<div class="ok">${this._notice}</div>` : nothing}

            <h2>Capsule Modules</h2>
            ${this._modules.length === 0
                ? html`<div class="empty">No channel modules registered</div>`
                : this._modules.map(
                      (m) => html`
                          <div class="card row">
                              <div class="grow">
                                  <strong>${m.title || m.name}</strong>
                                  <div class="muted">
                                      ${m.name}${m.feature_flag ? ` · flag ${m.feature_flag}` : ''}
                                  </div>
                              </div>
                              <soma-status-badge
                                  .status=${m.enabled ? 'active' : 'disabled'}
                              ></soma-status-badge>
                              ${m.always_enabled
                                  ? nothing
                                  : html`<soma-button
                                        @click=${() => this._moduleToggle(m.name, !m.enabled)}
                                        >${m.enabled ? 'Disable' : 'Enable'}</soma-button
                                    >`}
                          </div>
                      `,
                  )}

            <h2>Add Channel</h2>
            <div class="card">
                <div class="row">
                    <div class="grow">
                        <label>Kind</label>
                        <select .value=${this._kind} @change=${(e: Event) => {
                            this._kind = (e.target as HTMLSelectElement).value as ChannelKind;
                        }}>
                            <option value="whatsapp">WhatsApp</option>
                            <option value="telegram">Telegram</option>
                            <option value="email">Email</option>
                        </select>
                    </div>
                    <div class="grow">
                        <label>Capsule ID (required for dispatch)</label>
                        <input
                            .value=${this._capsuleId}
                            @input=${(e: Event) => {
                                this._capsuleId = (e.target as HTMLInputElement).value;
                            }}
                            placeholder="uuid"
                        />
                    </div>
                    <div class="grow">
                        <label>Mode</label>
                        <select .value=${this._mode} @change=${(e: Event) => {
                            this._mode = (e.target as HTMLSelectElement).value;
                        }}>
                            <option value="poll">poll / baileys</option>
                            <option value="webhook">webhook / cloud</option>
                        </select>
                    </div>
                </div>
                ${this._kind === 'telegram'
                    ? html`
                          <div class="row" style="margin-top:12px">
                              <div class="grow">
                                  <label>Bot token (write-only)</label>
                                  <input
                                      type="password"
                                      .value=${this._botToken}
                                      @input=${(e: Event) => {
                                          this._botToken = (e.target as HTMLInputElement).value;
                                      }}
                                      placeholder="123456:ABC..."
                                  />
                              </div>
                              <div class="grow">
                                  <label>Group mode</label>
                                  <select .value=${this._groupMode} @change=${(e: Event) => {
                                      this._groupMode = (e.target as HTMLSelectElement).value;
                                  }}>
                                      <option value="mention">mention</option>
                                      <option value="all">all</option>
                                      <option value="off">off</option>
                                  </select>
                              </div>
                          </div>
                      `
                    : nothing}
                <div class="row" style="margin-top:12px">
                    <div class="grow">
                        <label>Allowlist (comma-separated users/numbers)</label>
                        <input
                            .value=${this._allowed}
                            @input=${(e: Event) => {
                                this._allowed = (e.target as HTMLInputElement).value;
                            }}
                            placeholder="empty = allow all"
                        />
                    </div>
                </div>
                <div class="actions">
                    <soma-button @click=${() => this._createChannel()}>Create channel</soma-button>
                </div>
            </div>

            <h2>Configured Channels</h2>
            ${this._loading
                ? html`<div class="empty">Loading…</div>`
                : this._channels.length === 0
                  ? html`<div class="empty">No channels yet</div>`
                  : this._channels.map(
                        (c) => html`
                            <div class="card row">
                                <div class="grow">
                                    <strong>${c.kind}</strong>
                                    <div class="muted">
                                        ${c.id.slice(0, 8)} · capsule
                                        ${c.capsule_id ? c.capsule_id.slice(0, 8) : 'unbound'}
                                    </div>
                                </div>
                                <soma-status-badge .status=${c.status}></soma-status-badge>
                                <div class="actions">
                                    <soma-button @click=${() => this._lifecycle(c.id, 'test')}
                                        >Test</soma-button
                                    >
                                    <soma-button @click=${() => this._lifecycle(c.id, 'start')}
                                        >Start</soma-button
                                    >
                                    <soma-button @click=${() => this._lifecycle(c.id, 'stop')}
                                        >Stop</soma-button
                                    >
                                    <soma-button @click=${() => this._deleteChannel(c.id)}
                                        >Delete</soma-button
                                    >
                                </div>
                            </div>
                        `,
                    )}
        `;
    }
}
