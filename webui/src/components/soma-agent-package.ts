/**
 * soma-agent-package — Agent package Export / Import panel (UI-S-56 family).
 *
 * Include checkboxes follow the export manifest contract (PK-02). Secrets
 * (integration keys) are never packaged — that checkbox is present-but-locked
 * off with an honesty note (PK-05).
 *
 * Export/import bind to live HTTP only. When no route answers, the controls
 * stay GATED with the fixed reason "No export API on this deployment" —
 * never a fake download of empty JSON.
 *
 * UI labels: Agent package, Agent, Tools — never Capsule. API paths may use
 * capsule. All visual styling uses `--skin-*` tokens only.
 */

import { LitElement, html, css, nothing, PropertyValues } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { apiClient, ApiError } from '../services/api-client.js';
import { workspaceStore } from '../stores/workspace-store.js';

export type PackageIncludeKey =
    | 'tools_policy'
    | 'memory_config'
    | 'brain_models'
    | 'persona'
    | 'skins'
    | 'integrations_keys'
    | 'chat_history';

interface IncludeOption {
    key: PackageIncludeKey;
    label: string;
    /** Secrets are never exported. Locked off regardless of operator input. */
    lockedOff: boolean;
    note?: string;
}

const INCLUDE_OPTIONS: IncludeOption[] = [
    { key: 'tools_policy', label: 'Tools + policy', lockedOff: false },
    { key: 'memory_config', label: 'Memory config', lockedOff: false },
    { key: 'brain_models', label: 'Brain models', lockedOff: false },
    { key: 'persona', label: 'Persona', lockedOff: false },
    { key: 'skins', label: 'Skins', lockedOff: false },
    {
        key: 'integrations_keys',
        label: 'Integration keys',
        lockedOff: true,
        note: 'Secrets are never written to an Agent package.',
    },
    { key: 'chat_history', label: 'Chat history', lockedOff: false },
];

const GATED_EXPORT_REASON = 'No export API on this deployment';
const GATED_IMPORT_REASON = 'No export API on this deployment';

type ApiPresence = 'unknown' | 'probing' | 'present' | 'absent';

@customElement('soma-agent-package')
export class SomaAgentPackage extends LitElement {
    @property({ type: String, attribute: 'agent-id' }) agentId: string | null = null;
    @property({ type: String, attribute: 'agent-name' }) agentName = '';

    @state() private _include: Record<PackageIncludeKey, boolean> = {
        tools_policy: true,
        memory_config: true,
        brain_models: true,
        persona: true,
        skins: true,
        integrations_keys: false,
        chat_history: false,
    };
    @state() private _exportApi: ApiPresence = 'unknown';
    @state() private _importApi: ApiPresence = 'unknown';
    @state() private _busy = false;
    @state() private _message = '';
    @state() private _messageKind: 'info' | 'error' | 'gated' = 'info';

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

        .body {
            padding: var(--skin-space-lg);
            display: flex;
            flex-direction: column;
            gap: var(--skin-space-lg);
        }

        .section-title {
            margin: 0 0 var(--skin-space-sm);
            font-size: var(--skin-text-xs);
            font-weight: var(--skin-weight-semibold);
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: var(--skin-color-text-muted);
        }

        .checks {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: var(--skin-space-sm);
        }

        .check {
            display: flex;
            align-items: flex-start;
            gap: var(--skin-space-sm);
            padding: var(--skin-space-sm);
            border: 1px solid var(--skin-color-border);
            border-radius: var(--skin-radius-md);
            background: var(--skin-color-bg-base);
            cursor: pointer;
        }

        .check.locked {
            opacity: 0.72;
            cursor: not-allowed;
        }

        .check input {
            margin-top: 2px;
            accent-color: var(--skin-color-accent);
        }

        .check-text {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .check-label {
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-primary);
            font-weight: var(--skin-weight-medium);
        }

        .check-note {
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-muted);
        }

        .secrets-note {
            margin: 0;
            font-size: var(--skin-text-xs);
            color: var(--skin-color-warning-text);
            background: color-mix(in srgb, var(--skin-color-warning) 14%, transparent);
            border: 1px solid var(--skin-color-warning);
            border-radius: var(--skin-radius-md);
            padding: var(--skin-space-sm) var(--skin-space-md);
        }

        .format {
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-secondary);
            margin: 0;
        }

        .format code {
            font-family: var(--skin-font-mono);
            color: var(--skin-color-text-primary);
        }

        .actions {
            display: flex;
            flex-wrap: wrap;
            gap: var(--skin-space-sm);
        }

        .btn {
            border-radius: var(--skin-radius-md);
            border: 1px solid var(--skin-color-border);
            background: var(--skin-color-bg-base);
            color: var(--skin-color-text-primary);
            font-family: inherit;
            font-size: var(--skin-text-sm);
            font-weight: var(--skin-weight-medium);
            padding: var(--skin-space-sm) var(--skin-space-lg);
            cursor: pointer;
        }

        .btn:hover:not(:disabled) {
            background: var(--skin-color-bg-hover);
        }

        .btn.primary {
            background: var(--skin-color-accent);
            border-color: var(--skin-color-accent);
            color: var(--skin-color-accent-text);
        }

        .btn.primary:hover:not(:disabled) {
            background: var(--skin-color-accent-hover);
            border-color: var(--skin-color-accent-hover);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .banner {
            margin: 0;
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

        .banner.info {
            border-color: var(--skin-color-border);
            background: var(--skin-color-bg-hover);
            color: var(--skin-color-text-secondary);
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

        .hidden-file {
            display: none;
        }
    `;

    override connectedCallback() {
        super.connectedCallback();
        this._unsubscribe = workspaceStore.subscribe(() => {
            const next = workspaceStore.state.activeAgentId;
            if (next !== this._storeAgentId) {
                this._storeAgentId = next;
                void this._probeApis();
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
        void this._probeApis();
    }

    override updated(changed: PropertyValues<this>) {
        if (changed.has('agentId')) {
            void this._probeApis();
        }
    }

    private get _activeAgentId(): string | null {
        return this.agentId ?? this._storeAgentId;
    }

    /**
     * Probe the planned export/import routes. Code is truth: a 404/405 means
     * this deployment has no package API and the controls stay GATED.
     */
    private async _probeApis() {
        const agentId = this._activeAgentId;
        if (!agentId) {
            this._exportApi = 'absent';
            this._importApi = 'absent';
            this._message = GATED_EXPORT_REASON;
            this._messageKind = 'gated';
            return;
        }
        this._exportApi = 'probing';
        this._importApi = 'probing';
        try {
            await apiClient.get(`/agents/${encodeURIComponent(agentId)}/export`);
            this._exportApi = 'present';
            this._importApi = 'present';
            this._message = '';
            this._messageKind = 'info';
        } catch (e) {
            if (e instanceof ApiError && (e.status === 404 || e.status === 405)) {
                this._exportApi = 'absent';
                this._importApi = 'absent';
                this._message = GATED_EXPORT_REASON;
                this._messageKind = 'gated';
                return;
            }
            // Auth/other errors: route may exist. Do not claim GATED.
            if (e instanceof ApiError && (e.status === 401 || e.status === 403)) {
                this._exportApi = 'present';
                this._importApi = 'present';
                this._message = e.message;
                this._messageKind = 'error';
                return;
            }
            this._exportApi = 'absent';
            this._importApi = 'absent';
            this._message = GATED_EXPORT_REASON;
            this._messageKind = 'gated';
        }
    }

    private get _exportGated(): boolean {
        return this._exportApi !== 'present';
    }

    private get _importGated(): boolean {
        return this._importApi !== 'present';
    }

    private _setInclude(key: PackageIncludeKey, on: boolean) {
        const opt = INCLUDE_OPTIONS.find((o) => o.key === key);
        if (opt?.lockedOff) return;
        this._include = { ...this._include, [key]: on };
    }

    private async _export() {
        const agentId = this._activeAgentId;
        if (!agentId || this._exportGated || this._busy) return;
        this._busy = true;
        this._message = '';
        try {
            const include = INCLUDE_OPTIONS.filter(
                (o) => !o.lockedOff && this._include[o.key]
            ).map((o) => o.key);
            const payload = await apiClient.get<unknown>(
                `/agents/${encodeURIComponent(agentId)}/export?include=${encodeURIComponent(include.join(','))}`
            );
            const blob = new Blob([JSON.stringify(payload, null, 2)], {
                type: 'application/json',
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            const base = (this.agentName || agentId || 'agent').replace(/[^\w.-]+/g, '_');
            a.href = url;
            a.download = `${base}.soma-agent`;
            a.click();
            URL.revokeObjectURL(url);
            this._message = 'Agent package exported.';
            this._messageKind = 'info';
        } catch (e) {
            if (e instanceof ApiError && (e.status === 404 || e.status === 405)) {
                this._exportApi = 'absent';
                this._importApi = 'absent';
                this._message = GATED_EXPORT_REASON;
                this._messageKind = 'gated';
                return;
            }
            this._message = e instanceof Error ? e.message : 'Export failed';
            this._messageKind = 'error';
        } finally {
            this._busy = false;
        }
    }

    private _pickImportFile() {
        if (this._importGated || this._busy) return;
        void this.shadowRoot?.querySelector<HTMLInputElement>('#agent-package-file')?.click();
    }

    private async _onImportFile(e: Event) {
        const input = e.target as HTMLInputElement;
        const file = input.files?.[0];
        input.value = '';
        const agentId = this._activeAgentId;
        if (!file || !agentId || this._importGated || this._busy) return;
        this._busy = true;
        this._message = '';
        try {
            const text = await file.text();
            let body: unknown;
            try {
                body = JSON.parse(text);
            } catch {
                this._message = 'Not a valid Agent package file.';
                this._messageKind = 'error';
                return;
            }
            await apiClient.post(`/agents/import`, body);
            this._message = 'Agent package imported.';
            this._messageKind = 'info';
        } catch (err) {
            if (err instanceof ApiError && (err.status === 404 || err.status === 405)) {
                this._exportApi = 'absent';
                this._importApi = 'absent';
                this._message = GATED_IMPORT_REASON;
                this._messageKind = 'gated';
                return;
            }
            this._message = err instanceof Error ? err.message : 'Import failed';
            this._messageKind = 'error';
        } finally {
            this._busy = false;
        }
    }

    override render() {
        const gated = this._exportGated;
        return html`
            <div class="panel">
                <div class="header">
                    <h2 class="title">Agent package</h2>
                    <p class="subtitle">
                        ${this.agentName
                            ? html`Agent: ${this.agentName}`
                            : html`Export / import this Agent's configuration`}
                    </p>
                </div>
                <div class="body">
                    ${gated
                        ? html`
                              <p class="banner">
                                  ${GATED_EXPORT_REASON}
                                  <span class="gated-chip">GATED</span>
                              </p>
                          `
                        : nothing}
                    ${this._message && !gated
                        ? html`
                              <p
                                  class="banner ${this._messageKind === 'error'
                                      ? 'error'
                                      : this._messageKind === 'gated'
                                          ? ''
                                          : 'info'}"
                              >
                                  ${this._message}
                                  ${this._messageKind === 'gated'
                                      ? html`<span class="gated-chip">GATED</span>`
                                      : nothing}
                              </p>
                          `
                        : nothing}
                    ${this._message && gated && this._messageKind === 'error'
                        ? html`<p class="banner error">${this._message}</p>`
                        : nothing}

                    <section>
                        <h3 class="section-title">Include</h3>
                        <div class="checks">
                            ${INCLUDE_OPTIONS.map((opt) => html`
                                <label class="check ${opt.lockedOff ? 'locked' : ''}">
                                    <input
                                        type="checkbox"
                                        .checked=${opt.lockedOff ? false : this._include[opt.key]}
                                        ?disabled=${opt.lockedOff || gated}
                                        @change=${(e: Event) => {
                                            this._setInclude(
                                                opt.key,
                                                (e.target as HTMLInputElement).checked
                                            );
                                        }}
                                    />
                                    <span class="check-text">
                                        <span class="check-label">${opt.label}</span>
                                        ${opt.note
                                            ? html`<span class="check-note">${opt.note}</span>`
                                            : nothing}
                                    </span>
                                </label>
                            `)}
                        </div>
                    </section>

                    <p class="secrets-note">
                        PK-05 · Integration keys and credentials are never written into an Agent
                        package. Rotate secrets after import.
                    </p>

                    <p class="format">
                        Format: <code>.soma-agent</code> (JSON)
                    </p>

                    <div class="actions">
                        <button
                            class="btn primary"
                            type="button"
                            ?disabled=${gated || this._busy}
                            title=${gated ? GATED_EXPORT_REASON : 'Export agent package'}
                            @click=${this._export}
                        >
                            Export
                        </button>
                        <button
                            class="btn"
                            type="button"
                            ?disabled=${this._importGated || this._busy}
                            title=${this._importGated
                                ? GATED_IMPORT_REASON
                                : 'Import agent package'}
                            @click=${this._pickImportFile}
                        >
                            Import
                        </button>
                        <input
                            id="agent-package-file"
                            class="hidden-file"
                            type="file"
                            accept=".soma-agent,.json,application/json"
                            @change=${this._onImportFile}
                        />
                    </div>

                    ${this._importGated && !gated
                        ? html`
                              <p class="banner">
                                  ${GATED_IMPORT_REASON}
                                  <span class="gated-chip">GATED</span>
                              </p>
                          `
                        : nothing}
                </div>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-agent-package': SomaAgentPackage;
    }
}
