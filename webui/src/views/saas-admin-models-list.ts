/**
 * SAAS Admin Models List View
 * Catalog of the LLM models the platform has configured.
 *
 * Backed by /api/v2/aaas/settings/models. The previous version of this view
 * rendered five hardcoded models with fabricated `type`, `contextWindow`,
 * `hasVision` and `status` fields, and an "Add Model" dialog that invented
 * context windows, output-token caps and capability toggles. No such fields
 * exist on ModelConfig, and there is no create endpoint — the catalog is
 * seeded in PlatformConfig and only its enablement, defaults and rate limit
 * are editable. This view reads that store and patches only the fields the
 * backend actually accepts.
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import '../components/saas-data-table.js';
import '../components/saas-form-field.js';
import '../components/saas-select.js';
import '../components/saas-status-badge.js';
import '../components/saas-action-menu.js';
import type { TableColumn } from '../components/saas-data-table.js';
import { apiClient, getData } from '../services/api-client.js';

/** Matches admin.aaas.api.schemas.ModelConfigOut — no invented fields. */
interface ModelConfig {
    id: string;
    provider: string;
    model_name: string;
    display_name: string;
    enabled: boolean;
    default_for_chat: boolean;
    default_for_completion: boolean;
    rate_limit: number | null;
}

@customElement('saas-admin-models-list')
export class SaasAdminModelsList extends LitElement {
    static styles = css`
        :host {
            display: block;
            padding: var(--saas-space-lg, 24px);
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--saas-space-lg, 24px);
        }

        .title-area h1 {
            font-size: var(--saas-text-2xl, 28px);
            font-weight: var(--saas-font-semibold, 600);
            color: var(--saas-text-primary, #1a1a1a);
            margin: 0;
        }

        .subtitle {
            font-size: var(--saas-text-sm, 13px);
            color: var(--saas-text-secondary, #666666);
            margin-top: 4px;
        }

        .btn-primary {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            background: var(--saas-accent, #1a1a1a);
            color: var(--saas-text-inverse, #ffffff);
            border: none;
            border-radius: var(--saas-radius-md, 8px);
            font-size: var(--saas-text-sm, 13px);
            font-weight: var(--saas-font-medium, 500);
            cursor: pointer;
        }

        .controls {
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
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
            color: var(--saas-status-danger, #dc2626);
        }

        .state-empty {
            background: var(--saas-bg-active, #f5f5f5);
            border: 1px solid var(--saas-border-light, #e5e5e5);
            color: var(--saas-text-secondary, #666666);
        }
    `;

    @state() private _models: ModelConfig[] = [];
    @state() private _loading = true;
    @state() private _error: string | null = null;
    @state() private _search = '';
    @state() private _selectedProvider = '';

    connectedCallback() {
        super.connectedCallback();
        this._load();
    }

    private async _load() {
        this._loading = true;
        this._error = null;
        try {
            const rows = await apiClient.get<ModelConfig[]>('/aaas/settings/models');
            this._models = getData<ModelConfig[]>(rows) ?? (Array.isArray(rows) ? rows : []);
        } catch (e) {
            this._error = e instanceof Error ? e.message : String(e);
            this._models = [];
        } finally {
            this._loading = false;
        }
    }

    private async _patch(row: ModelConfig, body: Partial<Pick<ModelConfig, 'enabled' | 'default_for_chat' | 'default_for_completion' | 'rate_limit'>>) {
        try {
            await apiClient.patch(`/aaas/settings/models/${encodeURIComponent(row.id)}`, body);
            await this._load();
        } catch (e) {
            this._error = e instanceof Error ? e.message : String(e);
        }
    }

    private _handleAction(e: CustomEvent, row: ModelConfig) {
        const action = e.detail?.action;
        if (action === 'toggle') {
            this._patch(row, { enabled: !row.enabled });
        } else if (action === 'default_chat') {
            this._patch(row, { default_for_chat: !row.default_for_chat });
        } else if (action === 'default_completion') {
            this._patch(row, { default_for_completion: !row.default_for_completion });
        }
    }

    private _columns: TableColumn[] = [
        { key: 'display_name', label: 'Model', sortable: true, width: '25%' },
        { key: 'provider', label: 'Provider', sortable: true, width: '15%' },
        {
            key: 'model_name',
            label: 'Model ID',
            width: '22%',
            render: (val) => html`<code style="font-size: 12px; color: var(--saas-text-secondary)">${val}</code>`
        },
        {
            key: 'default_for_chat',
            label: 'Chat default',
            width: '11%',
            align: 'center',
            render: (val) => val
                ? html`<span class="material-symbols-outlined" style="font-size: 18px; color: var(--saas-status-success)">check_circle</span>`
                : html`<span style="color: var(--saas-text-muted)">—</span>`
        },
        {
            key: 'default_for_completion',
            label: 'Completion default',
            width: '11%',
            align: 'center',
            render: (val) => val
                ? html`<span class="material-symbols-outlined" style="font-size: 18px; color: var(--saas-status-success)">check_circle</span>`
                : html`<span style="color: var(--saas-text-muted)">—</span>`
        },
        {
            key: 'rate_limit',
            label: 'Rate limit',
            width: '10%',
            render: (val) => html`${val === null || val === undefined ? '—' : `${val}/min`}`
        },
        {
            key: 'enabled',
            label: 'Status',
            width: '12%',
            render: (val) => html`
                <saas-status-badge
                    variant=${val ? 'success' : 'neutral'}
                    size="sm"
                    dot
                >${val ? 'enabled' : 'disabled'}</saas-status-badge>
            `
        },
        {
            key: 'actions',
            label: '',
            width: '40px',
            align: 'right',
            render: (_val, row) => html`
                <saas-action-menu
                    .actions=${[
                        {
                            id: 'toggle',
                            label: (row as unknown as ModelConfig).enabled ? 'Disable' : 'Enable',
                            icon: (row as unknown as ModelConfig).enabled ? 'block' : 'check_circle'
                        },
                        {
                            id: 'default_chat',
                            label: (row as unknown as ModelConfig).default_for_chat ? 'Unset chat default' : 'Set as chat default',
                            icon: 'chat'
                        },
                        {
                            id: 'default_completion',
                            label: (row as unknown as ModelConfig).default_for_completion ? 'Unset completion default' : 'Set as completion default',
                            icon: 'bolt'
                        }
                    ]}
                    @saas-action=${(e: CustomEvent) => this._handleAction(e, row as unknown as ModelConfig)}
                ></saas-action-menu>
            `
        }
    ];

    render() {
        const providers = Array.from(new Set(this._models.map(m => m.provider))).sort();
        const filtered = this._models.filter(m =>
            (!this._search || m.display_name.toLowerCase().includes(this._search.toLowerCase()) || m.model_name.toLowerCase().includes(this._search.toLowerCase())) &&
            (!this._selectedProvider || m.provider === this._selectedProvider)
        );

        return html`
            <div class="header">
                <div class="title-area">
                    <h1>Model Catalog</h1>
                    <div class="subtitle">Manage AI models, providers, and capabilities</div>
                </div>
            </div>

            <div class="controls">
                <saas-form-field
                    class="search-input"
                    placeholder="Search models..."
                    style="margin-bottom: 0"
                    @saas-input=${(e: CustomEvent) => { this._search = e.detail?.value ?? ''; }}
                ></saas-form-field>

                <saas-select
                    placeholder="All Providers"
                    style="width: 200px; margin-bottom: 0"
                    .options=${[
                        { label: 'All Providers', value: '' },
                        ...providers.map(p => ({ label: p, value: p }))
                    ]}
                    @saas-change=${(e: CustomEvent) => { this._selectedProvider = e.detail?.value ?? ''; }}
                ></saas-select>
            </div>

            ${this._error ? html`
                <div class="state-banner state-error">Failed to load models: ${this._error}</div>
            ` : nothing}

            ${this._loading
                ? html`<div class="state-banner state-empty">Loading model catalog…</div>`
                : filtered.length === 0
                    ? html`<div class="state-banner state-empty">No models match.</div>`
                    : html`
                        <saas-data-table
                            .columns=${this._columns}
                            .data=${filtered}
                        ></saas-data-table>
                    `
            }
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-admin-models-list': SaasAdminModelsList;
    }
}
