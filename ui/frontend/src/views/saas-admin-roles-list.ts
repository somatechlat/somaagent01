/**
 * SAAS Admin Roles List View
 * Management interface for Roles & Permissions
 *
 * SRS Reference: Section 9.2
 * VIBE COMPLIANT:
 * - Real Lit 3.x Web Component
 * - Uses shared components
 * - Material Icons
 * - Permission Matrix UI
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import '../components/saas-data-table.js';
import '../components/saas-glass-modal.js';
import '../components/saas-form-field.js';
import '../components/saas-status-badge.js';
import '../components/saas-action-menu.js';
import '../components/saas-toggle.js';
import type { TableColumn } from '../components/saas-data-table.js';

interface Role {
    id: string;
    name: string;
    code: string;
    level: 'platform' | 'tenant' | 'agent';
    users: number;
    permissions: number;
    description: string;
}

@customElement('saas-admin-roles-list')
export class SaasAdminRolesList extends LitElement {
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

        /* Matrix Styles */
        .matrix-container {
            border: 1px solid var(--saas-border-light);
            border-radius: 8px;
            overflow: hidden;
            margin-top: 16px;
        }

        .matrix-header {
            background: var(--saas-bg-active);
            padding: 8px 16px;
            font-weight: 600;
            font-size: 13px;
            display: flex;
            justify-content: space-between;
        }

        .matrix-group {
            border-bottom: 1px solid var(--saas-border-light);
        }

        .matrix-group-title {
            padding: 8px 16px;
            font-weight: 600;
            font-size: 11px;
            color: var(--saas-text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            background: var(--saas-bg-page);
        }

        .matrix-row {
            display: flex;
            align-items: center;
            padding: 8px 16px;
            border-bottom: 1px solid var(--saas-border-light);
            font-size: 13px;
        }

        .matrix-row:last-child {
            border-bottom: none;
        }

        .matrix-row:hover {
            background: var(--saas-bg-hover);
        }

        .perm-check {
            margin-right: 12px;
        }

        .perm-code {
            font-family: var(--saas-font-mono);
            font-size: 12px;
            color: var(--saas-text-secondary);
            width: 160px;
        }
        
        .perm-desc {
            flex: 1;
        }

        .section-tabs {
            display: flex;
            gap: 24px;
            border-bottom: 1px solid var(--saas-border-light);
            margin-bottom: 24px;
        }

        .tab {
            padding: 12px 0;
            font-size: 14px;
            color: var(--saas-text-secondary);
            cursor: pointer;
            border-bottom: 2px solid transparent;
        }

        .tab.active {
            color: var(--saas-text-primary);
            font-weight: 500;
            border-bottom-color: var(--saas-accent);
        }
    `;

    @state() private _roles: Role[] = [
        { id: '1', name: 'SAAS Super Admin', code: 'saas_superadmin', level: 'platform', users: 2, permissions: 45, description: 'Full access to everything' },
        { id: '2', name: 'SAAS Support', code: 'saas_support', level: 'platform', users: 5, permissions: 12, description: 'Support ticket access only' },
        { id: '3', name: 'Tenant SysAdmin', code: 'sysadmin', level: 'tenant', users: 124, permissions: 32, description: 'Full tenant control' },
        { id: '4', name: 'Tenant Admin', code: 'admin', level: 'tenant', users: 340, permissions: 24, description: 'Agent management' },
        { id: '5', name: 'Developer', code: 'developer', level: 'agent', users: 890, permissions: 18, description: 'DEV access' },
        { id: '6', name: 'Trainer', code: 'trainer', level: 'agent', users: 45, permissions: 15, description: 'TRN access' },
    ];

    @state() private _activeTab = 'platform';
    @state() private _showModal = false;

    private _columns: TableColumn[] = [
        { key: 'name', label: 'Role Name', sortable: true, width: '25%' },
        {
            key: 'code',
            label: 'Code',
            width: '20%',
            render: (val) => html`<code style="font-size: 12px; background: var(--saas-bg-active); padding: 2px 4px; border-radius: 4px">${val}</code>`
        },
        { key: 'users', label: 'Users', width: '10%', align: 'center' },
        { key: 'permissions', label: 'Perms', width: '10%', align: 'center' },
        { key: 'description', label: 'Description', width: '30%' },
        {
            key: 'actions',
            label: '',
            width: '40px',
            align: 'right',
            render: (val, row) => html`
                <saas-action-menu
                    .actions=${[
                    { id: 'edit', label: 'Edit Permissions', icon: 'lock_open' },
                    { id: 'users', label: 'View Users', icon: 'group' },
                    { id: 'delete', label: 'Delete', icon: 'delete', variant: 'danger' }
                ]}
                ></saas-action-menu>
            `
        }
    ];

    /* Sample Matrix Data */
    private _matrix = [
        {
            group: 'Chat & Memory',
            perms: [
                { code: 'chat:send', desc: 'Send chat messages', checked: true },
                { code: 'chat:view_history', desc: 'View conversation history', checked: true },
                { code: 'memory:read', desc: 'Read from SomaBrain', checked: true },
                { code: 'memory:write', desc: 'Write to SomaBrain', checked: true },
                { code: 'memory:delete', desc: 'Delete memories', checked: false }
            ]
        },
        {
            group: 'Tools',
            perms: [
                { code: 'tools:execute', desc: 'Execute approved tools', checked: true },
                { code: 'tools:code_exec', desc: 'Execute code snippets', checked: true },
                { code: 'tools:browser', desc: 'Use browser agent', checked: true },
                { code: 'tools:debug', desc: 'Access debug tools', checked: true },
                { code: 'tools:configure', desc: 'Configure tool settings', checked: false }
            ]
        }
    ];

    render() {
        return html`
            <div class="header">
                <div class="title-area">
                    <h1>Roles & Permissions</h1>
                    <div class="subtitle">Configure access controls for Platform, Tenants, and Agents</div>
                </div>
                <button class="btn-primary" @click=${() => this._showModal = true}>
                    <span class="material-symbols-outlined" style="font-size: 18px">add</span>
                    Create Role
                </button>
            </div>

            <div class="section-tabs">
                <div class="tab ${this._activeTab === 'platform' ? 'active' : ''}" @click=${() => this._activeTab = 'platform'}>Platform Roles</div>
                <div class="tab ${this._activeTab === 'tenant' ? 'active' : ''}" @click=${() => this._activeTab = 'tenant'}>Tenant Roles</div>
                <div class="tab ${this._activeTab === 'agent' ? 'active' : ''}" @click=${() => this._activeTab = 'agent'}>Agent Roles</div>
            </div>

            <saas-data-table
                .columns=${this._columns}
                .data=${this._roles.filter(r => r.level === this._activeTab)}
            ></saas-data-table>

            <saas-glass-modal
                ?open=${this._showModal}
                title="Edit Role Permissions"
                size="lg"
                @saas-modal-close=${() => this._showModal = false}
            >
                <div>
                    <div style="display: flex; gap: 16px; margin-bottom: 24px">
                        <saas-form-field label="Role Name" value="Developer" style="flex: 1"></saas-form-field>
                        <saas-form-field label="Role Code" value="developer" disabled style="flex: 1"></saas-form-field>
                    </div>

                    <div style="margin-bottom: 16px">
                        <p style="font-size: 13px; font-weight: 600; margin-bottom: 8px">Agent Modes Allowed</p>
                        <div style="display: flex; gap: 16px">
                            <saas-toggle label="STD" checked></saas-toggle>
                            <saas-toggle label="DEV" checked></saas-toggle>
                            <saas-toggle label="TRN"></saas-toggle>
                            <saas-toggle label="ADM"></saas-toggle>
                            <saas-toggle label="RO"></saas-toggle>
                        </div>
                    </div>

                    <div class="matrix-container">
                        <div class="matrix-header">
                            <span>PERMISSION MATRIX</span>
                            <span style="color: var(--saas-accent); cursor: pointer">Select All</span>
                        </div>
                        
                        ${this._matrix.map(group => html`
                            <div class="matrix-group">
                                <div class="matrix-group-title">${group.group}</div>
                                ${group.perms.map(perm => html`
                                    <div class="matrix-row">
                                        <div class="perm-check">
                                            <input type="checkbox" ?checked=${perm.checked}>
                                        </div>
                                        <div class="perm-code">${perm.code}</div>
                                        <div class="perm-desc">${perm.desc}</div>
                                    </div>
                                `)}
                            </div>
                        `)}
                    </div>
                </div>

                <div slot="footer" style="display: flex; justify-content: flex-end; gap: 8px">
                    <button class="btn-secondary" @click=${() => this._showModal = false} style="
                        padding: 8px 16px; 
                        background: transparent; 
                        border: 1px solid var(--saas-border-light); 
                        border-radius: 8px;
                        cursor: pointer;
                    ">Cancel</button>
                    <button class="btn-primary">Save Changes</button>
                </div>
            </saas-glass-modal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-admin-roles-list': SaasAdminRolesList;
    }
}
