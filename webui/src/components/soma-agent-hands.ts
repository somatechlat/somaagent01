/**
 * soma-agent-hands — per-Agent Hands tools table (UI-S-03).
 *
 * Columns: name · tier · policy (auto|approval|deny) · enable toggle · remove.
 * Data: GET /api/v2/tools + GET /api/v2/tools/catalog (apiClient baseUrl /api/v2).
 * Policy save: PATCH /api/v2/agents/{agentId}/capsule { tool_policy }.
 *
 * Honesty (SOMA LAW — no mocks):
 * - Tools list GATED when either tools API is missing.
 * - Tier renders "—" when the API does not return a tier. Never invented.
 * - Policy cells render "—" until tool_policy is readable or the operator sets
 *   one. Policy save GATED when the capsule PATCH is missing.
 * - Remove is present-but-disabled: no capability-unlink HTTP route exists.
 *
 * UI labels: Agent, Hands, Tools — never Capsule. API paths may use capsule.
 * All visual styling uses `--skin-*` tokens only.
 */

import { LitElement, html, css, nothing, PropertyValues } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { apiClient, ApiError } from '../services/api-client.js';
import { workspaceStore } from '../stores/workspace-store.js';
import './soma-tool-policy-modal.js';
import type { ToolExecutionPolicy, ToolPolicySaveDetail } from './soma-tool-policy-modal.js';

/** GET /tools — ToolsListResponse */
interface ToolInfo {
    name: string;
    description?: string | null;
    parameters?: Record<string, unknown> | null;
    /** Optional; present only if the API starts returning it. */
    tier?: number | string | null;
}

interface ToolsListResponse {
    tools: ToolInfo[];
    count: number;
}

/** GET /tools/catalog — list[ToolCatalogItem] */
interface ToolCatalogItem {
    name: string;
    description?: string | null;
    category?: string | null;
    enabled: boolean;
    tier?: number | string | null;
}

/** Capsule tool_policy JSON (API field name; not shown in UI labels). */
interface ToolPolicyBuckets {
    auto_execute?: string[];
    approval_required?: string[];
    denied?: string[];
}

interface CapsulePolicyResponse {
    tool_policy?: ToolPolicyBuckets | null;
}

export interface HandsToolRow {
    name: string;
    description: string;
    /** null = API did not return a tier. Rendered as "—". */
    tier: number | string | null;
    /** null = unknown (not yet set, not readable). Rendered as "—". */
    policy: ToolExecutionPolicy | null;
    enabled: boolean;
}

type LoadStatus = 'idle' | 'loading' | 'ready' | 'empty' | 'error' | 'gated';

const GATED_TOOLS_REASON = 'Tools API is not available on this deployment.';
const GATED_POLICY_REASON = 'Tool policy API is not available on this deployment.';
const GATED_REMOVE_REASON = 'No tool remove API on this deployment.';

@customElement('soma-agent-hands')
export class SomaAgentHands extends LitElement {
    /** Explicit agent id. Falls back to workspaceStore.activeAgentId. */
    @property({ type: String, attribute: 'agent-id' }) agentId: string | null = null;

    @state() private _rows: HandsToolRow[] = [];
    @state() private _status: LoadStatus = 'idle';
    @state() private _error = '';
    @state() private _toolsGated = false;
    @state() private _policyGated = false;
    @state() private _savingPolicy = false;
    @state() private _filter = '';
    @state() private _modalOpen = false;
    @state() private _modalTool = '';
    @state() private _modalExecution: ToolExecutionPolicy = 'approval';
    @state() private _modalScope = 'kit';
    @state() private _modalReason = '';
    @state() private _modalBlocked = '';

    /** Resolved policy buckets awaiting / after PATCH. */
    @state() private _policy: ToolPolicyBuckets = {};

    private _unsubscribe: (() => void) | null = null;
    private _storeAgentId: string | null = null;

    static styles = css`
        :host {
            display: block;
            font-family: var(--skin-font-sans);
            color: var(--skin-color-text-primary);
        }

        .panel {
            background: var(--skin-color-bg-card);
            border: 1px solid var(--skin-color-border);
            border-radius: var(--skin-radius-lg);
            overflow: hidden;
        }

        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: var(--skin-space-md);
            padding: var(--skin-space-md) var(--skin-space-lg);
            border-bottom: 1px solid var(--skin-color-border-subtle);
        }

        .title {
            margin: 0;
            font-size: var(--skin-text-lg);
            font-weight: var(--skin-weight-semibold);
        }

        .subtitle {
            margin: var(--skin-space-xs) 0 0;
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-muted);
        }

        .filter {
            min-width: 180px;
            font-family: inherit;
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-primary);
            background: var(--skin-color-bg-base);
            border: 1px solid var(--skin-color-border);
            border-radius: var(--skin-radius-md);
            padding: var(--skin-space-xs) var(--skin-space-sm);
        }

        .filter:focus {
            outline: none;
            border-color: var(--skin-color-accent);
            box-shadow: 0 0 0 var(--skin-focus-ring-width) var(--skin-focus-ring);
        }

        .banner {
            margin: var(--skin-space-md) var(--skin-space-lg) 0;
            padding: var(--skin-space-sm) var(--skin-space-md);
            border-radius: var(--skin-radius-md);
            border: 1px solid var(--skin-color-warning);
            background: color-mix(in srgb, var(--skin-color-warning) 14%, transparent);
            color: var(--skin-color-warning-text);
            font-size: var(--skin-text-xs);
        }

        .banner.error {
            border-color: var(--skin-color-danger);
            background: color-mix(in srgb, var(--skin-color-danger) 14%, transparent);
            color: var(--skin-color-danger-text);
        }

        .table-wrap {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th {
            text-align: left;
            padding: var(--skin-space-sm) var(--skin-space-md);
            font-size: var(--skin-text-xs);
            font-weight: var(--skin-weight-semibold);
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: var(--skin-color-text-muted);
            background: var(--skin-color-bg-hover);
            border-bottom: 1px solid var(--skin-color-border);
            white-space: nowrap;
        }

        td {
            padding: var(--skin-space-sm) var(--skin-space-md);
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-primary);
            border-bottom: 1px solid var(--skin-color-border-subtle);
            vertical-align: middle;
        }

        tr:last-child td {
            border-bottom: none;
        }

        tbody tr:hover td {
            background: var(--skin-color-bg-hover);
        }

        .name-cell {
            display: flex;
            flex-direction: column;
            gap: 2px;
            min-width: 140px;
        }

        .tool-name {
            font-weight: var(--skin-weight-medium);
            font-family: var(--skin-font-mono);
            font-size: var(--skin-text-sm);
        }

        .tool-desc {
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-muted);
            max-width: 280px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .dash {
            color: var(--skin-color-text-muted);
        }

        .policy-btn {
            border: 1px solid var(--skin-color-border);
            background: var(--skin-color-bg-base);
            color: var(--skin-color-text-primary);
            border-radius: var(--skin-radius-md);
            font-family: inherit;
            font-size: var(--skin-text-xs);
            font-weight: var(--skin-weight-medium);
            padding: var(--skin-space-xs) var(--skin-space-sm);
            cursor: pointer;
            min-width: 88px;
            text-align: left;
        }

        .policy-btn:hover:not(:disabled) {
            background: var(--skin-color-bg-hover);
            border-color: var(--skin-color-border-strong);
        }

        .policy-btn:disabled {
            opacity: 0.55;
            cursor: not-allowed;
        }

        .policy-btn.auto {
            border-color: var(--skin-color-success);
            color: var(--skin-color-success);
        }

        .policy-btn.approval {
            border-color: var(--skin-color-warning);
            color: var(--skin-color-warning);
        }

        .policy-btn.deny {
            border-color: var(--skin-color-danger);
            color: var(--skin-color-danger);
        }

        .policy-btn:disabled.auto {
            border-color: var(--skin-color-border);
            color: var(--skin-color-text-muted);
        }

        .policy-btn:disabled.approval {
            border-color: var(--skin-color-border);
            color: var(--skin-color-text-muted);
        }

        .policy-btn:disabled.deny {
            border-color: var(--skin-color-border);
            color: var(--skin-color-text-muted);
        }

        .policy-label {
            text-transform: capitalize;
        }

        .toggle {
            position: relative;
            width: 40px;
            height: 22px;
            border-radius: var(--skin-radius-full);
            border: 1px solid var(--skin-color-border);
            background: var(--skin-color-bg-active);
            cursor: pointer;
            padding: 0;
            transition: background var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .toggle.on {
            background: var(--skin-color-success);
            border-color: var(--skin-color-success);
        }

        .toggle:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .toggle-knob {
            position: absolute;
            top: 2px;
            left: 2px;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: var(--skin-color-bg-card);
            box-shadow: var(--skin-shadow-sm);
            transition: transform var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .toggle.on .toggle-knob {
            transform: translateX(18px);
        }

        .actions {
            display: flex;
            gap: var(--skin-space-xs);
            align-items: center;
        }

        .icon-btn {
            border: 1px solid var(--skin-color-border);
            background: var(--skin-color-bg-base);
            color: var(--skin-color-text-secondary);
            border-radius: var(--skin-radius-md);
            width: 30px;
            height: 30px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 16px;
            line-height: 1;
        }

        .icon-btn:hover:not(:disabled) {
            background: var(--skin-color-bg-hover);
            color: var(--skin-color-danger);
            border-color: var(--skin-color-danger);
        }

        .icon-btn:disabled {
            opacity: 0.45;
            cursor: not-allowed;
        }

        .state {
            padding: var(--skin-space-2xl) var(--skin-space-lg);
            text-align: center;
            color: var(--skin-color-text-muted);
            font-size: var(--skin-text-sm);
        }

        .state.error {
            color: var(--skin-color-danger);
        }

        .gated-chip {
            display: inline-block;
            margin-left: var(--skin-space-xs);
            padding: 2px 6px;
            border-radius: var(--skin-radius-sm);
            border: 1px solid var(--skin-color-warning);
            color: var(--skin-color-warning-text);
            background: color-mix(in srgb, var(--skin-color-warning) 16%, transparent);
            font-size: var(--skin-text-xs);
            font-weight: var(--skin-weight-semibold);
            letter-spacing: 0.04em;
        }
    `;

    override connectedCallback() {
        super.connectedCallback();
        this._unsubscribe = workspaceStore.subscribe(() => {
            const next = workspaceStore.state.activeAgentId;
            if (next !== this._storeAgentId) {
                this._storeAgentId = next;
                void this._loadPolicy();
            }
        });
        this._storeAgentId = workspaceStore.state.activeAgentId;
    }

    override disconnectedCallback() {
        super.disconnectedCallback();
        this._unsubscribe?.();
        this._unsubscribe = null;
    }

    override firstUpdated() {
        void this._loadAll();
    }

    override updated(changed: PropertyValues<this>) {
        if (changed.has('agentId')) {
            void this._loadPolicy();
        }
    }

    private get _activeAgentId(): string | null {
        return this.agentId ?? this._storeAgentId;
    }

    private async _loadAll() {
        await Promise.all([this._loadTools(), this._loadPolicy()]);
    }

    private async _loadTools() {
        this._status = 'loading';
        this._error = '';
        this._toolsGated = false;
        try {
            const [list, catalog] = await Promise.all([
                apiClient.get<ToolsListResponse>('/tools'),
                apiClient.get<ToolCatalogItem[]>('/tools/catalog'),
            ]);

            const byName = new Map<string, HandsToolRow>();
            for (const t of list?.tools ?? []) {
                if (!t?.name) continue;
                byName.set(t.name, {
                    name: t.name,
                    description: t.description ?? '',
                    tier: t.tier ?? null,
                    policy: null,
                    enabled: true,
                });
            }
            for (const c of catalog ?? []) {
                if (!c?.name) continue;
                const existing = byName.get(c.name);
                if (existing) {
                    existing.enabled = c.enabled;
                    if (existing.tier === null && c.tier !== undefined && c.tier !== null) {
                        existing.tier = c.tier;
                    }
                    if (!existing.description && c.description) {
                        existing.description = c.description;
                    }
                } else {
                    byName.set(c.name, {
                        name: c.name,
                        description: c.description ?? '',
                        tier: c.tier ?? null,
                        policy: null,
                        enabled: c.enabled,
                    });
                }
            }

            this._rows = [...byName.values()].sort((a, b) => a.name.localeCompare(b.name));
            this._applyPolicyToRows();
            this._status = this._rows.length === 0 ? 'empty' : 'ready';
        } catch (e) {
            if (e instanceof ApiError && (e.status === 404 || e.status === 405)) {
                this._toolsGated = true;
                this._status = 'gated';
                this._error = GATED_TOOLS_REASON;
                this._rows = [];
                return;
            }
            this._status = 'error';
            this._error = e instanceof Error ? e.message : 'Failed to load tools';
            this._rows = [];
        }
    }

    private async _loadPolicy() {
        const agentId = this._activeAgentId;
        if (!agentId) {
            this._policy = {};
            this._applyPolicyToRows();
            return;
        }
        try {
            const data = await apiClient.get<CapsulePolicyResponse>(
                `/agents/${encodeURIComponent(agentId)}/capsule`
            );
            const raw = data?.tool_policy;
            if (raw && typeof raw === 'object') {
                this._policy = {
                    auto_execute: [...(raw.auto_execute ?? [])],
                    approval_required: [...(raw.approval_required ?? [])],
                    denied: [...(raw.denied ?? [])],
                };
                this._policyGated = false;
            } else {
                // Endpoint live but tool_policy not exposed — cells stay "—".
                this._policy = {};
                this._policyGated = false;
            }
            this._applyPolicyToRows();
        } catch (e) {
            if (e instanceof ApiError && (e.status === 404 || e.status === 405)) {
                this._policyGated = true;
                this._policy = {};
                this._applyPolicyToRows();
                return;
            }
            // Non-404: leave policy unknown; do not invent buckets.
            this._policy = {};
            this._applyPolicyToRows();
        }
    }

    private _applyPolicyToRows() {
        const policyOf = (name: string): ToolExecutionPolicy | null => {
            if (this._policy.denied?.includes(name)) return 'deny';
            if (this._policy.auto_execute?.includes(name)) return 'auto';
            if (this._policy.approval_required?.includes(name)) return 'approval';
            return null;
        };
        this._rows = this._rows.map((r) => ({ ...r, policy: policyOf(r.name) }));
    }

    private _policyBucketsFromRows(): ToolPolicyBuckets {
        const auto_execute: string[] = [];
        const approval_required: string[] = [];
        const denied: string[] = [];
        for (const r of this._rows) {
            if (r.policy === 'auto') auto_execute.push(r.name);
            else if (r.policy === 'approval') approval_required.push(r.name);
            else if (r.policy === 'deny') denied.push(r.name);
        }
        // Preserve any bucket names not currently listed in the table.
        for (const name of this._policy.auto_execute ?? []) {
            if (!this._rows.some((r) => r.name === name) && !auto_execute.includes(name)) {
                auto_execute.push(name);
            }
        }
        for (const name of this._policy.approval_required ?? []) {
            if (!this._rows.some((r) => r.name === name) && !approval_required.includes(name)) {
                approval_required.push(name);
            }
        }
        for (const name of this._policy.denied ?? []) {
            if (!this._rows.some((r) => r.name === name) && !denied.includes(name)) {
                denied.push(name);
            }
        }
        return { auto_execute, approval_required, denied };
    }

    private async _savePolicy() {
        const agentId = this._activeAgentId;
        if (!agentId) {
            this._error = 'No Agent selected.';
            this._status = this._rows.length ? 'ready' : 'empty';
            return;
        }
        this._savingPolicy = true;
        try {
            const tool_policy = this._policyBucketsFromRows();
            await apiClient.patch(`/agents/${encodeURIComponent(agentId)}/capsule`, {
                tool_policy,
            });
            this._policy = tool_policy;
            this._policyGated = false;
            this._error = '';
        } catch (e) {
            if (e instanceof ApiError && (e.status === 404 || e.status === 405)) {
                this._policyGated = true;
                this._error = GATED_POLICY_REASON;
                return;
            }
            this._error = e instanceof Error ? e.message : 'Failed to save tool policy';
        } finally {
            this._savingPolicy = false;
        }
    }

    private async _toggleEnabled(row: HandsToolRow) {
        const next = !row.enabled;
        // Optimistic UI is a lie on failure — update only after the API accepts.
        try {
            await apiClient.put(`/tools/catalog/${encodeURIComponent(row.name)}`, {
                name: row.name,
                description: row.description,
                category: 'general',
                enabled: next,
            });
            this._rows = this._rows.map((r) =>
                r.name === row.name ? { ...r, enabled: next } : r
            );
        } catch (e) {
            this._error = e instanceof Error ? e.message : `Failed to update ${row.name}`;
        }
    }

    private _openPolicy(row: HandsToolRow) {
        this._modalTool = row.name;
        this._modalExecution = row.policy ?? 'approval';
        this._modalScope = 'kit';
        this._modalReason = '';
        this._modalBlocked = this._policyGated ? GATED_POLICY_REASON : '';
        this._modalOpen = true;
    }

    private async _onPolicySave(e: CustomEvent<ToolPolicySaveDetail>) {
        e.stopPropagation();
        const { toolName, execution } = e.detail;
        this._rows = this._rows.map((r) =>
            r.name === toolName ? { ...r, policy: execution } : r
        );
        await this._savePolicy();
    }

    private _filteredRows(): HandsToolRow[] {
        const q = this._filter.trim().toLowerCase();
        if (!q) return this._rows;
        return this._rows.filter(
            (r) =>
                r.name.toLowerCase().includes(q) ||
                r.description.toLowerCase().includes(q)
        );
    }

    private _renderTier(tier: number | string | null) {
        if (tier === null || tier === undefined || tier === '') {
            return html`<span class="dash" title="Tier is not returned by the Tools API">—</span>`;
        }
        return html`<span>${tier}</span>`;
    }

    private _renderPolicyCell(row: HandsToolRow) {
        const disabled = this._policyGated;
        const cls = row.policy ?? '';
        const label = row.policy ?? '—';
        const title = disabled
            ? GATED_POLICY_REASON
            : row.policy
                ? `Policy: ${row.policy}`
                : 'Policy not set on this Agent';
        return html`
            <button
                type="button"
                class="policy-btn ${cls}"
                title=${title}
                ?disabled=${disabled || this._savingPolicy}
                @click=${() => this._openPolicy(row)}
            >
                <span class="policy-label">${label}</span>
            </button>
        `;
    }

    override render() {
        const rows = this._filteredRows();
        return html`
            <div class="panel">
                <div class="header">
                    <div>
                        <h2 class="title">Hands</h2>
                        <p class="subtitle">Tools on this Agent · policy and enablement</p>
                    </div>
                    <input
                        class="filter"
                        type="search"
                        placeholder="Filter tools"
                        aria-label="Filter tools"
                        .value=${this._filter}
                        @input=${(e: Event) => {
                            this._filter = (e.target as HTMLInputElement).value;
                        }}
                    />
                </div>

                ${this._toolsGated
                    ? html`
                          <p class="banner">
                              ${GATED_TOOLS_REASON}
                              <span class="gated-chip">GATED</span>
                          </p>
                      `
                    : nothing}
                ${this._policyGated && !this._toolsGated
                    ? html`
                          <p class="banner">
                              ${GATED_POLICY_REASON}
                              <span class="gated-chip">GATED</span>
                          </p>
                      `
                    : nothing}
                ${this._error && !this._toolsGated
                    ? html`<p class="banner error">${this._error}</p>`
                    : nothing}

                ${this._status === 'loading'
                    ? html`<div class="state">Loading tools…</div>`
                    : this._status === 'gated'
                        ? html`<div class="state">
                              Tools table is GATED — ${GATED_TOOLS_REASON}
                          </div>`
                        : this._status === 'error'
                            ? html`<div class="state error">${this._error}</div>`
                            : this._status === 'empty'
                                ? html`<div class="state">No tools on this deployment.</div>`
                                : html`
                                      <div class="table-wrap">
                                          <table>
                                              <thead>
                                                  <tr>
                                                      <th>Name</th>
                                                      <th>Tier</th>
                                                      <th>Policy</th>
                                                      <th>Enable</th>
                                                      <th>Actions</th>
                                                  </tr>
                                              </thead>
                                              <tbody>
                                                  ${rows.map((row) => html`
                                                      <tr>
                                                          <td>
                                                              <div class="name-cell">
                                                                  <span class="tool-name">${row.name}</span>
                                                                  ${row.description
                                                                      ? html`<span class="tool-desc" title=${row.description}>${row.description}</span>`
                                                                      : nothing}
                                                              </div>
                                                          </td>
                                                          <td>${this._renderTier(row.tier)}</td>
                                                          <td>${this._renderPolicyCell(row)}</td>
                                                          <td>
                                                              <button
                                                                  type="button"
                                                                  class="toggle ${row.enabled ? 'on' : ''}"
                                                                  role="switch"
                                                                  aria-checked=${row.enabled ? 'true' : 'false'}
                                                                  aria-label=${row.enabled
                                                                      ? `Disable ${row.name}`
                                                                      : `Enable ${row.name}`}
                                                                  @click=${() => this._toggleEnabled(row)}
                                                              >
                                                                  <span class="toggle-knob"></span>
                                                              </button>
                                                          </td>
                                                          <td>
                                                              <div class="actions">
                                                                  <button
                                                                      type="button"
                                                                      class="icon-btn"
                                                                      title=${GATED_REMOVE_REASON}
                                                                      aria-label=${`Remove ${row.name} — ${GATED_REMOVE_REASON}`}
                                                                      disabled
                                                                  >
                                                                      ×
                                                                  </button>
                                                              </div>
                                                          </td>
                                                      </tr>
                                                  `)}
                                              </tbody>
                                          </table>
                                      </div>
                                  `}
            </div>

            <soma-tool-policy-modal
                .open=${this._modalOpen}
                .toolName=${this._modalTool}
                .execution=${this._modalExecution}
                .scope=${this._modalScope}
                .reason=${this._modalReason}
                .blockedReason=${this._modalBlocked}
                @soma-tool-policy-save=${this._onPolicySave}
                @soma-tool-policy-close=${() => {
                    this._modalOpen = false;
                }}
            ></soma-tool-policy-modal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-agent-hands': SomaAgentHands;
    }
}
