/**
 * SAAS Admin API Keys View
 * Management interface for Platform API Keys (LLMs, Services)
 *
 * SRS Reference: Section 9.4
 * VIBE COMPLIANT:
 * - Real Lit 3.x Web Component
 * - Shared components
 * - Material Icons
 * - Secure display (masked keys)
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

interface ApiKey {
    id: string;
    provider: string;
    keyMasked: string;
    type: 'llm' | 'service';
    status: 'valid' | 'expired' | 'missing';
    lastUsed?: string;
}

@customElement('saas-admin-api-keys')
export class SaasAdminApiKeys extends LitElement {
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

        .warning-banner {
            background: rgba(234, 179, 8, 0.1);
            border: 1px solid rgba(234, 179, 8, 0.3);
            color: var(--saas-text-primary);
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
    `;

    @state() private _keys: ApiKey[] = [
        { id: '1', provider: 'OpenAI', keyMasked: 'sk-proj-****...8x9K', type: 'llm', status: 'valid', lastUsed: 'Just now' },
        { id: '2', provider: 'Anthropic', keyMasked: 'sk-ant-****...JKL2', type: 'llm', status: 'valid', lastUsed: '5m ago' },
        { id: '3', provider: 'Google', keyMasked: 'AIzaSy****...mnop', type: 'llm', status: 'valid', lastUsed: '1h ago' },
        { id: '4', provider: 'Groq', keyMasked: 'gsk_****...qrst', type: 'llm', status: 'expired', lastUsed: '2d ago' },
        { id: '5', provider: 'Serper', keyMasked: '****...xyz', type: 'service', status: 'valid', lastUsed: 'Just now' },
        { id: '6', provider: 'Lago', keyMasked: 'lago_****...abc', type: 'service', status: 'valid', lastUsed: '1d ago' },
    ];

    @state() private _showModal = false;

    private _columns: TableColumn[] = [
        {
            key: 'provider',
            label: 'Provider',
            sortable: true,
            width: '20%',
            render: (val, row) => html`
                <div style="display: flex; align-items: center; gap: 8px">
                    <span class="material-symbols-outlined" style="font-size: 20px; color: ${row.status === 'valid' ? 'var(--saas-status-success)' : 'var(--saas-text-muted)'}">
                        ${row.type === 'llm' ? 'smart_toy' : 'dns'}
                    </span>
                    <span style="font-weight: 500">${val}</span>
                </div>
            `
        },
        {
            key: 'keyMasked',
            label: 'Key',
            width: '25%',
            render: (val) => html`<code style="font-size: 12px; color: var(--saas-text-secondary)">${val}</code>`
        },
        {
            key: 'status',
            label: 'Status',
            width: '15%',
            render: (val) => html`
                <saas-status-badge 
                    variant=${val === 'valid' ? 'success' : val === 'expired' ? 'warning' : 'danger'}
                    size="sm"
                    dot
                >${val}</saas-status-badge>
            `
        },
        { key: 'lastUsed', label: 'Last Used', width: '15%' },
        {
            key: 'actions',
            label: '',
            width: '40px',
            align: 'right',
            render: (val, row) => html`
                <saas-action-menu
                    .actions=${[
                    { id: 'edit', label: 'Rotate Key', icon: 'refresh' },
                    { id: 'test', label: 'Test Connection', icon: 'network_check' },
                    { id: 'delete', label: 'Remove', icon: 'delete', variant: 'danger' }
                ]}
                ></saas-action-menu>
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
                <button class="btn-primary" @click=${() => this._showModal = true}>
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

            <h3 style="margin-bottom: 16px; font-size: 14px; color: var(--saas-text-secondary); text-transform: uppercase; letter-spacing: 0.5px">LLM Providers</h3>
            <saas-data-table
                .columns=${this._columns}
                .data=${this._keys.filter(k => k.type === 'llm')}
                style="margin-bottom: 32px"
            ></saas-data-table>

            <h3 style="margin-bottom: 16px; font-size: 14px; color: var(--saas-text-secondary); text-transform: uppercase; letter-spacing: 0.5px">Services</h3>
            <saas-data-table
                .columns=${this._columns}
                .data=${this._keys.filter(k => k.type === 'service')}
            ></saas-data-table>

            <saas-glass-modal
                ?open=${this._showModal}
                title="Add API Key"
                size="md"
                @saas-modal-close=${() => this._showModal = false}
            >
                <div style="display: flex; flex-direction: column; gap: 16px">
                    <saas-select
                        label="Provider"
                        placeholder="Select Provider"
                        .options=${[
                { label: 'OpenAI', value: 'openai', icon: 'smart_toy' },
                { label: 'Anthropic', value: 'anthropic', icon: 'psychology' },
                { label: 'Google', value: 'google', icon: 'search' },
                { label: 'Serper', value: 'serper', icon: 'search_check' },
                { label: 'Lago', value: 'lago', icon: 'payments' }
            ]}
                    ></saas-select>

                    <saas-form-field
                        label="API Key"
                        placeholder="sk-..."
                        type="password"
                        required
                        helper="Keys are stored securely in Secret Manager"
                    ></saas-form-field>

                    <saas-toggle
                        label="Active immediately"
                        checked
                    ></saas-toggle>
                </div>

                <div slot="footer" style="display: flex; justify-content: flex-end; gap: 8px">
                    <button class="btn-secondary" @click=${() => this._showModal = false} style="
                        padding: 8px 16px; 
                        background: transparent; 
                        border: 1px solid var(--saas-border-light); 
                        border-radius: 8px;
                        cursor: pointer;
                    ">Cancel</button>
                    <button class="btn-primary">Safe & Verify</button>
                </div>
            </saas-glass-modal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-admin-api-keys': SaasAdminApiKeys;
    }
}
