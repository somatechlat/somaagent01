/**
 * SAAS Admin Models List View
 * Management interface for AI Models (Chat & Embedding)
 *
 * SRS Reference: Section 9.1
 * VIBE COMPLIANT:
 * - Real Lit 3.x Web Component
 * - Uses shared components (data-table, form-field, select, toggle)
 * - Material Icons
 * - Light/dark theme support
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import '../components/saas-data-table.js';
import '../components/saas-glass-modal.js';
import '../components/saas-form-field.js';
import '../components/saas-select.js';
import '../components/saas-toggle.js';
import '../components/saas-status-badge.js';
import '../components/saas-action-menu.js';
import type { TableColumn } from '../components/saas-data-table.js';

interface Model {
    id: string;
    name: string;
    provider: string;
    type: 'chat' | 'embedding' | 'utility';
    contextWindow: string;
    hasVision: boolean;
    status: 'active' | 'deprecated' | 'beta';
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

        .controls {
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
        }

        .search-input {
            width: 300px;
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
            transition: background 150ms;
        }

        .btn-primary:hover {
            background: var(--saas-accent-hover, #333333);
        }

        .form-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        .form-section-title {
            grid-column: 1 / -1;
            font-size: 14px;
            font-weight: 600;
            color: var(--saas-text-primary);
            margin-top: 8px;
            margin-bottom: 8px;
            padding-bottom: 4px;
            border-bottom: 1px solid var(--saas-border-light);
        }

        .checkbox-group {
            grid-column: 1 / -1;
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }
    `;

    @state() private _models: Model[] = [
        { id: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI', type: 'chat', contextWindow: '128K', hasVision: true, status: 'active' },
        { id: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet', provider: 'Anthropic', type: 'chat', contextWindow: '200K', hasVision: true, status: 'active' },
        { id: 'gemini-1-5-pro', name: 'Gemini 1.5 Pro', provider: 'Google', type: 'chat', contextWindow: '2M', hasVision: true, status: 'active' },
        { id: 'text-embedding-3-large', name: 'Text Embedding 3 Large', provider: 'OpenAI', type: 'embedding', contextWindow: '8K', hasVision: false, status: 'active' },
        { id: 'gemma-2-9b', name: 'Gemma 2 9B', provider: 'Google', type: 'chat', contextWindow: '8K', hasVision: false, status: 'beta' },
    ];

    @state() private _showModal = false;
    @state() private _search = '';
    @state() private _selectedProvider = '';

    private _columns: TableColumn[] = [
        { key: 'name', label: 'Model Name', sortable: true, width: '25%' },
        { key: 'provider', label: 'Provider', sortable: true, width: '15%' },
        {
            key: 'type',
            label: 'Type',
            sortable: true,
            width: '15%',
            render: (val) => html`
                <span style="text-transform: capitalize">${val}</span>
            `
        },
        { key: 'contextWindow', label: 'Context', width: '10%' },
        {
            key: 'hasVision',
            label: 'Vision',
            width: '10%',
            align: 'center',
            render: (val) => val ? html`<span class="material-symbols-outlined" style="font-size: 18px; color: var(--saas-status-success)">check_circle</span>` : '—'
        },
        {
            key: 'status',
            label: 'Status',
            width: '15%',
            render: (val) => html`
                <saas-status-badge 
                    variant=${val === 'active' ? 'success' : val === 'beta' ? 'warning' : 'neutral'}
                    size="sm"
                    dot
                >${val}</saas-status-badge>
            `
        },
        {
            key: 'actions',
            label: '',
            width: '40px',
            align: 'right',
            render: (val, row) => html`
                <saas-action-menu
                    .actions=${[
                    { id: 'edit', label: 'Edit', icon: 'edit' },
                    { id: 'toggle', label: row.status === 'active' ? 'Disable' : 'Enable', icon: row.status === 'active' ? 'block' : 'check_circle' },
                    { id: 'delete', label: 'Delete', icon: 'delete', variant: 'danger' }
                ]}
                    @saas-action=${(e: CustomEvent) => this._handleAction(e, row)}
                ></saas-action-menu>
            `
        }
    ];

    private _handleAction(e: CustomEvent, row: any) {
        console.log('Action:', e.detail.action, 'Row:', row);
        // Implement real actions here
    }

    render() {
        return html`
            <div class="header">
                <div class="title-area">
                    <h1>Model Catalog</h1>
                    <div class="subtitle">Manage AI models, providers, and capabilities</div>
                </div>
                <button class="btn-primary" @click=${() => this._showModal = true}>
                    <span class="material-symbols-outlined" style="font-size: 18px">add</span>
                    Add Model
                </button>
            </div>

            <div class="controls">
                <saas-form-field
                    class="search-input"
                    placeholder="Search models..."
                    style="margin-bottom: 0"
                    @saas-input=${(e: CustomEvent) => this._search = e.detail.value}
                ></saas-form-field>

                <saas-select
                    placeholder="All Providers"
                    style="width: 200px; margin-bottom: 0"
                    .options=${[
                { label: 'All Providers', value: '' },
                { label: 'OpenAI', value: 'OpenAI' },
                { label: 'Anthropic', value: 'Anthropic' },
                { label: 'Google', value: 'Google' }
            ]}
                    @saas-change=${(e: CustomEvent) => this._selectedProvider = e.detail.value}
                ></saas-select>
            </div>

            <saas-data-table
                .columns=${this._columns}
                .data=${this._models.filter(m =>
                (!this._search || m.name.toLowerCase().includes(this._search.toLowerCase())) &&
                (!this._selectedProvider || m.provider === this._selectedProvider)
            )}
            ></saas-data-table>

            <saas-glass-modal
                ?open=${this._showModal}
                title="Add Model to Catalog"
                size="md"
                @saas-modal-close=${() => this._showModal = false}
            >
                <div class="form-grid">
                    <saas-select
                        label="Provider"
                        placeholder="Select Provider"
                        .options=${[
                { label: 'OpenAI', value: 'openai', icon: 'smart_toy' },
                { label: 'Anthropic', value: 'anthropic', icon: 'psychology' },
                { label: 'Google', value: 'google', icon: 'search' },
                { label: 'Mistral', value: 'mistral', icon: 'wind_power' }
            ]}
                    ></saas-select>

                    <saas-form-field
                        label="Model ID"
                        placeholder="e.g. gpt-4o"
                        required
                    ></saas-form-field>

                    <saas-form-field
                        label="Display Name"
                        placeholder="e.g. GPT-4o"
                        required
                    ></saas-form-field>

                    <saas-select
                        label="Type"
                        placeholder="Select Type"
                        .options=${[
                { label: 'Chat Model', value: 'chat' },
                { label: 'Embedding Model', value: 'embedding' },
                { label: 'Utility Model', value: 'utility' }
            ]}
                    ></saas-select>

                    <saas-form-field
                        label="Context Window"
                        placeholder="e.g. 128K"
                        type="text"
                    ></saas-form-field>

                    <saas-form-field
                        label="Max Output Tokens"
                        placeholder="e.g. 4096"
                        type="number"
                    ></saas-form-field>

                    <div class="form-section-title">Capabilities</div>
                    
                    <div class="checkbox-group">
                        <saas-toggle label="Vision Support" description="Can process images"></saas-toggle>
                        <saas-toggle label="Function Calling" description="Can execute tools"></saas-toggle>
                        <saas-toggle label="JSON Mode" description="Structured output"></saas-toggle>
                    </div>

                    <div class="form-section-title">Rate Limits</div>

                    <saas-form-field
                        label="RPM (Requests/Min)"
                        placeholder="500"
                        type="number"
                    ></saas-form-field>

                    <saas-form-field
                        label="TPM (Tokens/Min)"
                        placeholder="30000"
                        type="number"
                    ></saas-form-field>
                </div>

                <div slot="footer" style="display: flex; justify-content: flex-end; gap: 8px">
                    <button class="btn-secondary" @click=${() => this._showModal = false} style="
                        padding: 8px 16px; 
                        background: transparent; 
                        border: 1px solid var(--saas-border-light); 
                        border-radius: 8px;
                        cursor: pointer;
                    ">Cancel</button>
                    <button class="btn-primary">Add Model</button>
                </div>
            </saas-glass-modal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-admin-models-list': SaasAdminModelsList;
    }
}
