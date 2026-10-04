/**
 * Roles list — the one role catalogue screen.
 *
 * Backed by GET /aaas/settings/roles (PlatformConfig Global Defaults) and
 * GET /auth/me for the caller's real permissions. The deleted /permissions/*
 * router used to mint fabricated CRUD; this view never talks to it.
 *
 * System / provisioned roles are locked. The real authority to rewrite what a
 * role grants is `org:assign_roles` (admin/aaas/api/settings.py update_role).
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import '../components/saas-status-badge.js';

interface RoleRow {
    id: string;
    name: string;
    description: string;
    permissions: string[];
    user_count: number;
}

/** Roles established at install / break-glass. Never assignable, never editable. */
const PROVISIONED_ROLES = new Set(['sysadmin', 'agent_owner']);

@customElement('saas-admin-roles-list')
export class SaasAdminRolesList extends LitElement {
    static styles = css`
        :host {
            display: block;
            height: 100vh;
            overflow-y: auto;
            padding: 24px;
            background: var(--saas-bg-page, #f5f5f5);
            color: var(--saas-text-primary, #1a1a1a);
            font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
        }
        * { box-sizing: border-box; }
        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-size: 20px;
            line-height: 1;
            display: inline-block;
        }
        h1 { font-size: 24px; margin: 0 0 4px; }
        .subtitle { color: var(--saas-text-secondary, #666); margin: 0 0 20px; font-size: 13px; }
        .notice {
            border: 1px solid var(--saas-border-light, #e0e0e0);
            background: var(--saas-bg-card, #fff);
            border-radius: 10px;
            padding: 14px 16px;
            margin-bottom: 20px;
            font-size: 13px;
            line-height: 1.5;
        }
        table { width: 100%; border-collapse: collapse; background: var(--saas-bg-card, #fff);
            border: 1px solid var(--saas-border-light, #e0e0e0); border-radius: 10px; overflow: hidden; }
        th, td { text-align: left; padding: 12px 14px; border-bottom: 1px solid var(--saas-border-light, #eee); font-size: 13px; vertical-align: top; }
        th { font-size: 11px; text-transform: uppercase; letter-spacing: 0.4px; color: var(--saas-text-secondary, #666); }
        tr:last-child td { border-bottom: none; }
        .muted { color: var(--saas-text-muted, #999); font-size: 12px; }
        .perm-list { margin: 0; padding-left: 16px; }
        .perm-list li { margin: 2px 0; font-family: ui-monospace, monospace; font-size: 11px; }
        .error { color: #b91c1c; background: #fee2e2; border: 1px solid #fecaca; border-radius: 8px; padding: 12px 14px; margin-bottom: 16px; }
        .actions { display: flex; gap: 8px; }
        a.link {
            color: inherit; font-size: 12px; text-decoration: underline;
            background: none; border: none; cursor: pointer; padding: 0;
        }
    `;

    @state() private _roles: RoleRow[] = [];
    @state() private _loading = true;
    @state() private _error = '';
    @state() private _canAssignRoles = false;

    async connectedCallback() {
        super.connectedCallback();
        await this._load();
    }

    private async _load() {
        this._loading = true;
        this._error = '';
        try {
            const [roles, me] = await Promise.all([
                apiClient.get<RoleRow[]>('/aaas/settings/roles'),
                apiClient.get<{ permissions?: string[] }>('/auth/me'),
            ]);
            this._roles = roles || [];
            this._canAssignRoles = (me.permissions || []).includes('org:assign_roles');
        } catch (err) {
            this._error = `Couldn't load roles. ${err instanceof Error ? err.message : err}`;
            this._roles = [];
        } finally {
            this._loading = false;
        }
    }

    render() {
        return html`
            <h1>Roles</h1>
            <p class="subtitle">
                Catalogue roles and the permissions each one grants.
                Authority is <code>admin.core.authz</code>; this screen reads it, it does not invent verbs.
            </p>

            <div class="notice">
                Editing what a role grants requires <strong>org:assign_roles</strong>.
                ${this._canAssignRoles
                    ? html`You hold that permission. Open the <a class="link" href="/platform/role-matrix" @click=${this._goMatrix}>permission matrix</a> to change grants.`
                    : html`You do not hold it, so grants are read-only here.`}
                Provisioned roles (<code>sysadmin</code>, <code>agent_owner</code>) are locked:
                they are established at install, never assigned from inside an organization.
            </div>

            ${this._error ? html`<div class="error">${this._error}</div>` : nothing}

            ${this._loading
                ? html`<p class="muted">Loading roles…</p>`
                : this._roles.length === 0
                    ? html`<p class="muted">No roles are configured on this deployment.</p>`
                    : html`
                        <table>
                            <thead>
                                <tr>
                                    <th>Role</th>
                                    <th>Provisioned</th>
                                    <th>Users</th>
                                    <th>Permissions</th>
                                    <th>Description</th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                ${this._roles.map(r => {
                                    const locked = PROVISIONED_ROLES.has(r.id);
                                    return html`
                                        <tr>
                                            <td>
                                                <strong>${r.name || r.id}</strong>
                                                <div class="muted">${r.id}</div>
                                            </td>
                                            <td>
                                                ${locked
                                                    ? html`<saas-status-badge variant="info" size="sm">locked</saas-status-badge>`
                                                    : html`<span class="muted">assignable</span>`}
                                            </td>
                                            <td>${r.user_count ?? 0}</td>
                                            <td>
                                                <ul class="perm-list">
                                                    ${(r.permissions || []).map(p => html`<li>${p}</li>`)}
                                                </ul>
                                            </td>
                                            <td>${r.description || '—'}</td>
                                            <td>
                                                <div class="actions">
                                                    <a class="link" href="/platform/role-matrix" @click=${this._goMatrix}>Matrix</a>
                                                </div>
                                            </td>
                                        </tr>
                                    `;
                                })}
                            </tbody>
                        </table>
                    `}
        `;
    }

    private _goMatrix = (e: Event) => {
        e.preventDefault();
        window.dispatchEvent(new CustomEvent('saas-navigate', { detail: { route: '/platform/role-matrix' } }));
    };
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-admin-roles-list': SaasAdminRolesList;
    }
}
