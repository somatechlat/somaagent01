/**
 * Role Matrix — one permission matrix + the folded-in permissions list.
 *
 * Backed by GET /aaas/settings/roles (each role carries its granted permission
 * names) and PATCH /aaas/settings/roles/{id} which requires `org:assign_roles`.
 * The deleted /permissions/* router used to mint fabricated CRUD; this screen
 * never talks to it. Verb names come from the role rows the catalog returns —
 * the UI does not invent a permission vocabulary.
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import '../components/saas-sidebar.js';

interface RoleOut {
    id: string;
    name: string;
    description: string;
    permissions: string[];
    user_count?: number;
}

const PROVISIONED_ROLES = new Set(['sysadmin', 'agent_owner']);

@customElement('saas-role-matrix')
export class SaasRoleMatrix extends LitElement {
    static styles = css`
        :host {
            display: flex;
            height: 100vh;
            background: var(--saas-bg-page, #f5f5f5);
            font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            color: var(--saas-text-primary, #1a1a1a);
        }
        * { box-sizing: border-box; }
        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-size: 20px; line-height: 1; display: inline-block;
        }
        .sidebar { width: 260px; background: var(--saas-bg-card, #fff); border-right: 1px solid var(--saas-border-light, #e0e0e0); flex-shrink: 0; }
        .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
        .header {
            display: flex; align-items: center; justify-content: space-between;
            padding: 16px 24px; background: var(--saas-bg-card, #fff);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }
        .header-title { font-size: 18px; font-weight: 600; margin: 0; }
        .header-subtitle { font-size: 13px; color: var(--saas-text-secondary, #666); margin: 4px 0 0; }
        .btn {
            display: inline-flex; align-items: center; gap: 8px;
            padding: 10px 16px; border-radius: 8px; font-size: 13px; font-weight: 500;
            cursor: pointer; border: 1px solid var(--saas-border-light, #e0e0e0);
            background: var(--saas-bg-card, #fff); color: var(--saas-text-primary, #1a1a1a);
        }
        .btn.primary { background: #1a1a1a; color: #fff; border-color: #1a1a1a; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .content { flex: 1; overflow: auto; padding: 20px 24px; }
        .notice {
            border: 1px solid var(--saas-border-light, #e0e0e0);
            background: var(--saas-bg-card, #fff);
            border-radius: 10px; padding: 14px 16px; margin-bottom: 16px;
            font-size: 13px; line-height: 1.5;
        }
        .error-banner {
            background: #fee2e2; color: #b91c1c; border: 1px solid #fecaca;
            border-radius: 8px; padding: 12px 14px; margin-bottom: 16px; font-size: 13px;
        }
        .loading { color: var(--saas-text-secondary, #666); padding: 24px; }
        table { width: 100%; border-collapse: collapse; background: var(--saas-bg-card, #fff);
            border: 1px solid var(--saas-border-light, #e0e0e0); border-radius: 10px; overflow: hidden; }
        th, td { padding: 10px 12px; border-bottom: 1px solid var(--saas-border-light, #eee); font-size: 12px; text-align: left; vertical-align: top; }
        th { background: var(--saas-bg-page, #f5f5f5); font-size: 11px; text-transform: uppercase; letter-spacing: 0.4px; color: var(--saas-text-secondary, #666); }
        tr:last-child td { border-bottom: none; }
        .category-row td { background: var(--saas-bg-page, #f5f5f5); font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.4px; }
        .perm-name { font-family: ui-monospace, monospace; font-size: 12px; display: block; }
        .perm-desc { color: var(--saas-text-secondary, #666); font-size: 11px; display: block; margin-top: 2px; }
        .toggle-cell { text-align: center; }
        .toggle {
            display: inline-block; width: 18px; height: 18px; border-radius: 4px;
            border: 1px solid var(--saas-border-light, #ccc); cursor: pointer; background: #fff;
        }
        .toggle.active { background: #1a1a1a; border-color: #1a1a1a; }
        .toggle.locked { opacity: 0.45; cursor: not-allowed; }
        .role-col-locked { opacity: 0.7; }
        .muted { color: var(--saas-text-muted, #999); font-size: 12px; }
    `;

    @state() private roles: RoleOut[] = [];
    /** permission name -> set of role ids that grant it */
    @state() private grants: Map<string, Set<string>> = new Map();
    @state() private original: Map<string, Set<string>> = new Map();
    @state() private allPermissions: string[] = [];
    @state() private loading = true;
    @state() private saving = false;
    @state() private dirty = false;
    @state() private error = '';
    @state() private canAssignRoles = false;

    async connectedCallback() {
        super.connectedCallback();
        await this.loadData();
    }

    private async loadData() {
        this.loading = true;
        this.error = '';
        try {
            const [roles, me] = await Promise.all([
                apiClient.get<RoleOut[]>('/aaas/settings/roles'),
                apiClient.get<{ permissions?: string[] }>('/auth/me'),
            ]);
            this.roles = roles || [];
            this.canAssignRoles = (me.permissions || []).includes('org:assign_roles');

            const grants = new Map<string, Set<string>>();
            const perms = new Set<string>();
            for (const role of this.roles) {
                for (const p of role.permissions || []) {
                    perms.add(p);
                    if (!grants.has(p)) grants.set(p, new Set());
                    grants.get(p)!.add(role.id);
                }
            }
            this.allPermissions = Array.from(perms).sort();
            this.grants = grants;
            this.original = new Map(Array.from(grants.entries()).map(([k, v]) => [k, new Set(v)]));
            this.dirty = false;
        } catch (err) {
            this.error = `Couldn't load the role matrix. ${err instanceof Error ? err.message : err}`;
        } finally {
            this.loading = false;
        }
    }

    private isLocked(roleId: string): boolean {
        return PROVISIONED_ROLES.has(roleId) || !this.canAssignRoles;
    }

    private toggle(roleId: string, perm: string) {
        if (this.isLocked(roleId)) return;
        const next = new Map(Array.from(this.grants.entries()).map(([k, v]) => [k, new Set(v)]));
        const set = next.get(perm) || new Set<string>();
        if (set.has(roleId)) set.delete(roleId);
        else set.add(roleId);
        next.set(perm, set);
        this.grants = next;
        this.checkDirty();
    }

    private checkDirty() {
        for (const perm of this.allPermissions) {
            const a = this.grants.get(perm) || new Set();
            const b = this.original.get(perm) || new Set();
            if (a.size !== b.size) { this.dirty = true; return; }
            for (const id of a) { if (!b.has(id)) { this.dirty = true; return; } }
        }
        this.dirty = false;
    }

    private revert() {
        this.grants = new Map(Array.from(this.original.entries()).map(([k, v]) => [k, new Set(v)]));
        this.dirty = false;
        this.error = '';
    }

    private async save() {
        this.saving = true;
        this.error = '';
        try {
            for (const role of this.roles) {
                if (this.isLocked(role.id)) continue;
                const before = new Set(role.permissions || []);
                const after = new Set(
                    this.allPermissions.filter(p => (this.grants.get(p) || new Set()).has(role.id))
                );
                let changed = before.size !== after.size;
                if (!changed) {
                    for (const p of before) { if (!after.has(p)) { changed = true; break; } }
                }
                if (!changed) continue;
                await apiClient.patch(`/aaas/settings/roles/${role.id}`, {
                    permissions: Array.from(after).sort(),
                });
            }
            await this.loadData();
        } catch (err) {
            this.error = `Failed to save role grants. ${err instanceof Error ? err.message : err}`;
        } finally {
            this.saving = false;
        }
    }

    private byCategory(): Map<string, string[]> {
        const groups = new Map<string, string[]>();
        for (const perm of this.allPermissions) {
            const cat = perm.includes(':') ? perm.split(':', 1)[0] : 'other';
            if (!groups.has(cat)) groups.set(cat, []);
            groups.get(cat)!.push(perm);
        }
        return groups;
    }

    render() {
        return html`
            <aside class="sidebar">
                <saas-sidebar active-route="/platform/role-matrix"></saas-sidebar>
            </aside>
            <main class="main">
                <header class="header">
                    <div>
                        <h1 class="header-title">Permission Matrix</h1>
                        <p class="header-subtitle">
                            Role → permission grants. Provisioned roles are locked.
                            Saving requires <code>org:assign_roles</code>.
                        </p>
                    </div>
                    <div>
                        <button class="btn" ?disabled=${!this.dirty} @click=${() => this.revert()}>
                            <span class="material-symbols-outlined">undo</span> Revert
                        </button>
                        <button
                            class="btn primary"
                            ?disabled=${!this.dirty || this.saving || !this.canAssignRoles}
                            title=${this.canAssignRoles ? 'Save role grants' : 'Requires org:assign_roles'}
                            @click=${() => this.save()}
                        >
                            <span class="material-symbols-outlined">${this.saving ? 'hourglass_empty' : 'save'}</span>
                            ${this.saving ? 'Saving…' : 'Save Changes'}
                        </button>
                    </div>
                </header>

                ${this.error ? html`<div class="error-banner">${this.error}</div>` : nothing}
                ${!this.canAssignRoles
                    ? html`<div class="notice">
                        You don't have access to change role grants. Requires the
                        <strong>org:assign_roles</strong> permission. The matrix below is read-only.
                    </div>`
                    : nothing}

                <div class="content">
                    ${this.loading
                        ? html`<div class="loading">Loading role matrix…</div>`
                        : this.roles.length === 0
                            ? html`<div class="loading">No roles are configured on this deployment.</div>`
                            : html`
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Permission</th>
                                            ${this.roles.map(role => html`
                                                <th class=${PROVISIONED_ROLES.has(role.id) ? 'role-col-locked' : ''}>
                                                    ${role.name || role.id}
                                                    ${PROVISIONED_ROLES.has(role.id)
                                                        ? html`<div class="muted">locked</div>`
                                                        : html`<div class="muted">${role.id}</div>`}
                                                </th>
                                            `)}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${Array.from(this.byCategory().entries()).map(([cat, perms]) => html`
                                            <tr class="category-row">
                                                <td colspan=${this.roles.length + 1}>${cat}</td>
                                            </tr>
                                            ${perms.map(perm => html`
                                                <tr>
                                                    <td>
                                                        <span class="perm-name">${perm}</span>
                                                    </td>
                                                    ${this.roles.map(role => {
                                                        const on = (this.grants.get(perm) || new Set()).has(role.id);
                                                        const locked = this.isLocked(role.id);
                                                        return html`
                                                            <td class="toggle-cell">
                                                                <span
                                                                    class="toggle ${on ? 'active' : ''} ${locked ? 'locked' : ''}"
                                                                    title=${locked
                                                                        ? (PROVISIONED_ROLES.has(role.id)
                                                                            ? 'Provisioned role — locked'
                                                                            : 'Requires org:assign_roles')
                                                                        : (on ? 'Revoke' : 'Grant')}
                                                                    @click=${() => this.toggle(role.id, perm)}
                                                                ></span>
                                                            </td>
                                                        `;
                                                    })}
                                                </tr>
                                            `)}
                                        `)}
                                    </tbody>
                                </table>
                                <p class="muted" style="margin-top: 12px;">
                                    ${this.allPermissions.length} permissions carried by
                                    ${this.roles.length} roles. Verb names are whatever the
                                    catalog attached to each role — this UI does not invent verbs.
                                </p>
                            `}
                </div>
            </main>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-role-matrix': SaasRoleMatrix;
    }
}
