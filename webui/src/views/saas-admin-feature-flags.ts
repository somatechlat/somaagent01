/**
 * SAAS Admin Feature Flags View
 * Rollout control for platform features.
 *
 * Backed by /api/v2/aaas/features/flags. The previous version of this view
 * rendered five hardcoded flags with a fabricated `key` and a fabricated
 * `scope` column (global / tier / tenant), and offered "Create Flag",
 * "Configure Overrides", "Edit Definition" and "Delete" actions. None of
 * those endpoints exist — the only write is PATCH, which flips a feature's
 * `is_active`. This view reads the real AaasFeature catalog and flips that
 * flag, nothing more.
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import '../components/saas-data-table.js';
import '../components/saas-glass-modal.js';
import '../components/saas-form-field.js';
import '../components/saas-select.js';
import '../components/saas-status-badge.js';
import '../components/saas-action-menu.js';
import type { TableColumn } from '../components/saas-data-table.js';
import { apiClient, getData } from '../services/api-client.js';

/** Matches admin.aaas.api.schemas.FeatureFlagOut — no invented fields. */
interface FeatureFlag {
    id: string;
    code: string;
    name: string;
    description: string;
    enabled: boolean;
    created_at: string;
    updated_at: string;
}

@customElement('saas-admin-feature-flags')
export class SaasAdminFeatureFlags extends LitElement {
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

        /* Override toggle styles for table */
        .table-toggle {
            transform: scale(0.8);
            transform-origin: left center;
        }
    `;

    @state() private _flags: FeatureFlag[] = [];
    @state() private _loading = true;
    @state() private _error: string | null = null;

    connectedCallback() {
        super.connectedCallback();
        this._load();
    }

    private async _load() {
        this._loading = true;
        this._error = null;
        try {
            const rows = await apiClient.get<FeatureFlag[]>('/aaas/features/flags');
            this._flags = getData<FeatureFlag[]>(rows) ?? (Array.isArray(rows) ? rows : []);
        } catch (e) {
            this._error = e instanceof Error ? e.message : String(e);
            this._flags = [];
        } finally {
            this._loading = false;
        }
    }

    private async _setEnabled(row: FeatureFlag, enabled: boolean) {
        try {
            await apiClient.patch(`/aaas/features/flags/${encodeURIComponent(row.id)}`, { enabled });
            await this._load();
        } catch (e) {
            this._error = e instanceof Error ? e.message : String(e);
        }
    }

    private _formatTs(value: string): string {
        const t = new Date(value).getTime();
        return Number.isNaN(t) ? value : new Date(value).toLocaleString();
    }

    private _columns: TableColumn[] = [
        { key: 'name', label: 'Feature Name', sortable: true, width: '22%' },
        {
            key: 'code',
            label: 'Code',
            width: '16%',
            render: (val) => html`<code style="font-size: 12px; background: var(--saas-bg-active); padding: 2px 4px; border-radius: 4px">${val}</code>`
        },
        { key: 'description', label: 'Description', width: '32%' },
        {
            key: 'enabled',
            label: 'Global State',
            width: '16%',
            render: (val, row) => html`
                <div style="display: flex; align-items: center; gap: 8px">
                    <saas-toggle
                        .checked=${Boolean(val)}
                        class="table-toggle"
                        @saas-change=${(e: CustomEvent) => this._setEnabled(row as unknown as FeatureFlag, Boolean(e.detail?.checked))}
                    ></saas-toggle>
                    <span style="font-size: 12px; font-weight: 500">${val ? 'ON' : 'OFF'}</span>
                </div>
            `
        },
        {
            key: 'updated_at',
            label: 'Updated',
            width: '14%',
            render: (val) => html`${this._formatTs(val as string)}`
        }
    ];

    render() {
        return html`
            <div class="header">
                <div class="title-area">
                    <h1>Feature Flags</h1>
                    <div class="subtitle">Manage system-wide capabilities and rollouts</div>
                </div>
            </div>

            ${this._error ? html`
                <div class="state-banner state-error">Failed to load feature flags: ${this._error}</div>
            ` : nothing}

            ${this._loading
                ? html`<div class="state-banner state-empty">Loading feature flags…</div>`
                : this._flags.length === 0
                    ? html`<div class="state-banner state-empty">No features are registered.</div>`
                    : html`
                        <saas-data-table
                            .columns=${this._columns}
                            .data=${this._flags}
                        ></saas-data-table>
                    `
            }
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-admin-feature-flags': SaasAdminFeatureFlags;
    }
}
