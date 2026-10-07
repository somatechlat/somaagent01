/**
 * SOMA Admin API Keys View
 * Management interface for Platform API Keys (LLMs, Services)
 *
 * SRS Reference: Section 9.4
 *
 * Backed by /api/v2/aaas/settings/api-keys. The previous version of this
 * view rendered five hardcoded keys with fabricated `type`, `keyMasked` and
 * `status` fields, offered a "Safe & Verify" button that did nothing, and
 * claimed "Keys are stored securely in Secret Manager". Nothing in this
 * system talks to a Secret Manager — secrets live in Vault — and the create
 * endpoint generates the key server-side. This version reads and writes the
 * real store and shows the generated key exactly once, which is the only
 * time the backend will ever return it.
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import '../components/soma-data-table.js';
import '../components/soma-glass-modal.js';
import '../components/soma-form-field.js';
import '../components/soma-select.js';
import '../components/soma-status-badge.js';
import '../components/soma-action-menu.js';
import type { TableColumn } from '../components/soma-data-table.js';
import { apiClient, getData } from '../services/api-client.js';

/** Matches admin.aaas.api.schemas.ApiKeyOut — no invented fields. */
interface ApiKey {
    id: string;
    name: string;
    prefix: string;
    tenant_id: string | null;
    created_at: string;
    last_used: string | null;
    expires_at: string | null;
}

/** Shape returned by POST /aaas/settings/api-keys — `key` only exists once. */
interface ApiKeyCreated {
    id: string;
    name: string;
    prefix: string;
    key: string;
    message: string;
}

@customElement('soma-admin-api-keys')
export class SomaAdminApiKeys extends LitElement {
    static styles = css`
        :host {
            display: block;
            padding: var(--soma-space-lg, 24px);
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--soma-space-lg, 24px);
        }

        .title-area h1 {
            font-size: var(--soma-text-2xl, 28px);
            font-weight: var(--soma-font-semibold, 600);
            color: var(--soma-text-primary, #1a1a1a);
            margin: 0;
        }

        .subtitle {
            font-size: var(--soma-text-sm, 13px);
            color: var(--soma-text-secondary, #666666);
            margin-top: 4px;
        }

        .btn-primary {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            background: var(--soma-accent, #1a1a1a);
            color: var(--soma-text-inverse, #ffffff);
            border: none;
            border-radius: var(--soma-radius-md, 8px);
            font-size: var(--soma-text-sm, 13px);
            font-weight: var(--soma-font-medium, 500);
            cursor: pointer;
        }

        .warning-banner {
            background: rgba(234, 179, 8, 0.1);
            border: 1px solid rgba(234, 179, 8, 0.3);
            color: var(--soma-text-primary);
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 24px;
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .icon-warning {
            color: #eab308;
            font-family: 'Material Symbols Outlined';
            font-size: 20px;
        }

        .state-banner {
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 24px;
            font-size: 13px;
        }

        .state-error {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: var(--soma-status-danger, #dc2626);
        }

        .state-empty {
            background: var(--soma-bg-active, #f5f5f5);
            border: 1px solid var(--soma-border-light, #e5e5e5);
            color: var(--soma-text-secondary, #666666);
        }

        .generated-key {
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            font-size: 13px;
            background: var(--soma-bg-active, #f5f5f5);
            border: 1px solid var(--soma-border-light, #e5e5e5);
            border-radius: 8px;
            padding: 12px;
            word-break: break-all;
        }
    `;

    @state() private _keys: ApiKey[] = [];
    @state() private _loading = true;
    @state() private _error: string | null = null;
    @state() private _showCreateModal = false;
    @state() private _created: ApiKeyCreated | null = null;
    @state() private _newName = '';
    @state() private _newTenantId = '';
    @state() private _newExpiresInDays = '';

    connectedCallback() {
        super.connectedCallback();
        this._load();
    }

    private async _load() {
        this._loading = true;
        this._error = null;
        try {
            const rows = await apiClient.get<ApiKey[]>('/aaas/settings/api-keys');
            this._keys = getData<ApiKey[]>(rows) ?? (Array.isArray(rows) ? rows : []);
        } catch (e) {
            this._error = e instanceof Error ? e.message : String(e);
            this._keys = [];
        } finally {
            this._loading = false;
        }
    }

    private _formatTs(value: string | null): string {
        if (!value) return '—';
        const t = new Date(value).getTime();
        return Number.isNaN(t) ? value : new Date(value).toLocaleString();
    }

    private async _create() {
        const name = this._newName.trim();
        if (!name) return;

        const body: Record<string, unknown> = { name };
        const tenantId = this._newTenantId.trim();
        if (tenantId) body.tenant_id = tenantId;
        const days = parseInt(this._newExpiresInDays, 10);
        if (!Number.isNaN(days) && days > 0) body.expires_in_days = days;

        try {
            const created = await apiClient.post<ApiKeyCreated>('/aaas/settings/api-keys', body);
            this._created = created;
            this._showCreateModal = false;
            this._newName = '';
            this._newTenantId = '';
            this._newExpiresInDays = '';
            await this._load();
        } catch (e) {
            this._error = e instanceof Error ? e.message : String(e);
        }
    }

    private async _revoke(row: ApiKey) {
        try {
            await apiClient.delete(`/aaas/settings/api-keys/${row.id}`);
            await this._load();
        } catch (e) {
            this._error = e instanceof Error ? e.message : String(e);
        }
    }

    private _columns: TableColumn[] = [
        {
            key: 'name',
            label: 'Name',
            sortable: true,
            width: '22%',
            render: (val) => html`<span style="font-weight: 500">${val}</span>`
        },
        {
            key: 'prefix',
            label: 'Prefix',
            width: '14%',
            render: (val) => html`<code style="font-size: 12px; color: var(--soma-text-secondary)">${val}…</code>`
        },
        {
            key: 'tenant_id',
            label: 'Tenant',
            width: '16%',
            render: (val) => html`<span style="font-size: 12px; color: var(--soma-text-secondary)">${val ?? 'platform'}</span>`
        },
        {
            // ApiKeyOut has no status field. An expired/active verdict from
            // the client clock would invent server state (a revoked but
            // unexpired key would show "active"). Render the real expiry.
            key: 'expires_at',
            label: 'Expires',
            width: '12%',
            render: (val) => html`${this._formatTs(val as string | null)}`
        },
        { key: 'created_at', label: 'Created', width: '14%', render: (val) => html`${this._formatTs(val as string)}` },
        { key: 'last_used', label: 'Last Used', width: '14%', render: (val) => html`${this._formatTs(val as string)}` },
        {
            key: 'actions',
            label: '',
            width: '40px',
            align: 'right',
            render: (_val, row) => html`
                <soma-action-menu
                    .actions=${[
                        { id: 'revoke', label: 'Revoke', icon: 'delete', variant: 'danger' }
                    ]}
                    @soma-action=${(e: CustomEvent) => {
                        if (e.detail?.action === 'revoke') this._revoke(row as unknown as ApiKey);
                    }}
                ></soma-action-menu>
            `
        }
    ];

    render() {
        return html`
            <div class="header">
                <div class="title-area">
                    <h1>Platform API Keys</h1>
                    <div class="subtitle">Manage credentials for external AI providers and services</div>
                </div>
                <button class="btn-primary" @click=${() => { this._showCreateModal = true; }}>
                    <span class="material-symbols-outlined" style="font-size: 18px">add</span>
                    Add Key
                </button>
            </div>

            <div class="warning-banner">
                <span class="icon-warning">warning</span>
                <div>
                    <strong>Security Note:</strong> These are platform-wide keys. Tenant-specific keys should be configured in Tenant Settings.
                </div>
            </div>

            ${this._error ? html`
                <div class="state-banner state-error">Failed to load API keys: ${this._error}</div>
            ` : nothing}

            ${this._loading
                ? html`<div class="state-banner state-empty">Loading API keys…</div>`
                : this._keys.length === 0
                    ? html`<div class="state-banner state-empty">No active API keys.</div>`
                    : html`
                        <soma-data-table
                            .columns=${this._columns}
                            .data=${this._keys}
                        ></soma-data-table>
                    `
            }

            <soma-glass-modal
                ?open=${this._showCreateModal}
                title="Generate API Key"
                size="md"
                @soma-modal-close=${() => { this._showCreateModal = false; }}
            >
                <div style="display: flex; flex-direction: column; gap: 16px">
                    <soma-form-field
                        label="Name"
                        placeholder="e.g. production-gateway"
                        required
                        .value=${this._newName}
                        @soma-input=${(e: CustomEvent) => { this._newName = e.detail?.value ?? ''; }}
                        helper="A label you will recognise in this list."
                    ></soma-form-field>

                    <soma-form-field
                        label="Tenant ID"
                        placeholder="Leave blank for a platform-wide key"
                        .value=${this._newTenantId}
                        @soma-input=${(e: CustomEvent) => { this._newTenantId = e.detail?.value ?? ''; }}
                    ></soma-form-field>

                    <soma-form-field
                        label="Expires in days"
                        placeholder="Leave blank to never expire"
                        type="number"
                        .value=${this._newExpiresInDays}
                        @soma-input=${(e: CustomEvent) => { this._newExpiresInDays = e.detail?.value ?? ''; }}
                    ></soma-form-field>

                    <div style="font-size: 12px; color: var(--soma-text-secondary)">
                        The key is generated by the server and shown once. Only a one-way hash and an
                        8-character prefix are stored, so it cannot be recovered after this dialog.
                    </div>
                </div>

                <div slot="footer" style="display: flex; justify-content: flex-end; gap: 8px">
                    <button class="btn-secondary" @click=${() => { this._showCreateModal = false; }} style="
                        padding: 8px 16px;
                        background: transparent;
                        border: 1px solid var(--soma-border-light);
                        border-radius: 8px;
                        cursor: pointer;
                    ">Cancel</button>
                    <button class="btn-primary" @click=${() => this._create()}>Generate Key</button>
                </div>
            </soma-glass-modal>

            <soma-glass-modal
                ?open=${this._created !== null}
                title="Copy this key now"
                size="md"
                @soma-modal-close=${() => { this._created = null; }}
            >
                ${this._created ? html`
                    <div style="display: flex; flex-direction: column; gap: 16px">
                        <div class="warning-banner" style="margin-bottom: 0">
                            <span class="icon-warning">warning</span>
                            <div>${this._created.message}</div>
                        </div>
                        <div class="generated-key">${this._created.key}</div>
                    </div>
                    <div slot="footer" style="display: flex; justify-content: flex-end; gap: 8px">
                        <button class="btn-primary" @click=${() => {
                            navigator.clipboard?.writeText(this._created?.key ?? '');
                        }}>Copy</button>
                        <button class="btn-secondary" @click=${() => { this._created = null; }} style="
                            padding: 8px 16px;
                            background: transparent;
                            border: 1px solid var(--soma-border-light);
                            border-radius: 8px;
                            cursor: pointer;
                        ">Done</button>
                    </div>
                ` : nothing}
            </soma-glass-modal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-admin-api-keys': SomaAdminApiKeys;
    }
}
