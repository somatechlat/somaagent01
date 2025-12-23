/**
 * SAAS Admin Feature Flags View
 * Management interface for global and tenant-level feature flags
 *
 * SRS Reference: Section 9.3
 * VIBE COMPLIANT:
 * - Real Lit 3.x Web Component
 * - Shared components
 * - Material Icons
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import '../components/saas-data-table.js';
import '../components/saas-glass-modal.js';
import '../components/saas-toggle.js';
import '../components/saas-status-badge.js';
import '../components/saas-action-menu.js';
import type { TableColumn } from '../components/saas-data-table.js';

interface FeatureFlag {
    id: string;
    key: string;
    name: string;
    description: string;
    status: 'on' | 'off' | 'beta';
    scope: 'global' | 'tenant' | 'tier';
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

        /* Override toggle styles for table */
        .table-toggle {
            transform: scale(0.8);
            transform-origin: left center;
        }
    `;

    @state() private _flags: FeatureFlag[] = [
        { id: '1', key: 'sse_enabled', name: 'SSE Streaming', description: 'Enable Server-Sent Events', status: 'on', scope: 'global' },
        { id: '2', key: 'embeddings_ingest', name: 'Embedding Pipeline', description: 'RAG Ingestion', status: 'on', scope: 'global' },
        { id: '3', key: 'semantic_recall', name: 'Semantic Recall', description: 'SomaBrain integration', status: 'on', scope: 'global' },
        { id: '4', key: 'audio_support', name: 'Audio Support', description: 'Voice subsystem', status: 'off', scope: 'tier' },
        { id: '5', key: 'mcp_server', name: 'MCP Server Mode', description: 'Expose MCP server', status: 'beta', scope: 'tenant' },
    ];

    private _columns: TableColumn[] = [
        { key: 'name', label: 'Feature Name', sortable: true, width: '20%' },
        {
            key: 'key',
            label: 'Key',
            width: '20%',
            render: (val) => html`<code style="font-size: 12px; background: var(--saas-bg-active); padding: 2px 4px; border-radius: 4px">${val}</code>`
        },
        { key: 'description', label: 'Description', width: '30%' },
        {
            key: 'status',
            label: 'Global State',
            width: '15%',
            render: (val, row) => html`
                <div style="display: flex; align-items: center; gap: 8px">
                    <saas-toggle .checked=${val === 'on'} class="table-toggle"></saas-toggle>
                    <span style="font-size: 12px; font-weight: 500">${(val as string).toUpperCase()}</span>
                </div>
            `
        },
        {
            key: 'scope',
            label: 'Scope',
            width: '10%',
            render: (val) => html`
                <saas-status-badge 
                    variant=${val === 'global' ? 'info' : 'neutral'}
                    size="sm"
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
                    { id: 'configure', label: 'Configure Overrides', icon: 'settings' },
                    { id: 'edit', label: 'Edit Definition', icon: 'edit' },
                    { id: 'delete', label: 'Delete', icon: 'delete', variant: 'danger' }
                ]}
                ></saas-action-menu>
            `
        }
    ];

    render() {
        return html`
            <div class="header">
                <div class="title-area">
                    <h1>Feature Flags</h1>
                    <div class="subtitle">Manage system-wide capabilities and rollouts</div>
                </div>
                <button class="btn-primary">
                    <span class="material-symbols-outlined" style="font-size: 18px">add</span>
                    Create Flag
                </button>
            </div>

            <saas-data-table
                .columns=${this._columns}
                .data=${this._flags}
            ></saas-data-table>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-admin-feature-flags': SaasAdminFeatureFlags;
    }
}
