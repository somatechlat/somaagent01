/**
 * Settings — SomaBrain (UI-S-56)
 *
 * Connection knobs the operator layer owns:
 *   GET/PUT /api/v2/core/settings/somabrain
 *   → url · namespace · retention_days · sleep_interval · consolidation_enabled
 *
 * Connector health is read-only:
 *   GET /api/v2/core/brain-connector
 *
 * Secrets (memory HTTP token) live in Vault — never a field here.
 * BrainSetting tunables have no agent proxy — editors are omitted (UI-S-56 gaps).
 *
 * VIBE: Lit 3.x · Material Symbols · no emoji · no invented endpoints.
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import { glassCard } from '../styles/glass.js';
import { moduleBase } from '../styles/module-base.js';
import '../components/soma-brain-manager.js';

interface SomabrainSettingsValues {
    url: string;
    namespace: string;
    retention_days: number;
    sleep_interval: number;
    consolidation_enabled: boolean;
}

interface SettingsResponse {
    entity: string;
    values: Partial<SomabrainSettingsValues>;
    source: string;
    last_modified?: string | null;
}

interface BrainConnectorHealth {
    connected: boolean;
    circuit: string;
    base_url?: string;
    last_success_at?: number | null;
    last_error?: string | null;
    latency_ms?: number | null;
}

/** Blocking reason when the caller cannot change platform settings. */
const DISABLED_REASON =
    'Requires system:configure. Your role cannot change platform settings.';

const SETTINGS_PATH = '/core/settings/somabrain';
const CONNECTOR_PATH = '/core/brain-connector';

@customElement('soma-settings-somabrain')
export class SomaSettingsSomaBrain extends LitElement {
    static styles = [
        glassCard,
        moduleBase,
        css`
        :host {
            display: block;
            color: var(--skin-color-text-primary);
            font-family: var(--skin-font-sans);
        }

        * {
            box-sizing: border-box;
        }

        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: calc(var(--skin-space-md) + var(--skin-space-xs));
            line-height: 1;
            display: inline-block;
            -webkit-font-smoothing: antialiased;
        }

        .section {
            background: var(--skin-color-bg-card);
            border: var(--skin-border-width) solid var(--skin-color-border);
            border-radius: var(--skin-radius-lg);
            padding: var(--skin-space-lg);
            margin-bottom: calc(var(--skin-space-md) + var(--skin-space-xs));
        }

        .section-title {
            font-size: var(--skin-text-lg);
            font-weight: var(--skin-weight-semibold);
            margin: 0 0 var(--skin-space-sm) 0;
            display: flex;
            align-items: center;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs) / 2);
        }

        .section-title .material-symbols-outlined {
            color: var(--skin-color-text-secondary);
        }

        .section-desc {
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-secondary);
            margin: 0 0 calc(var(--skin-space-md) + var(--skin-space-xs)) 0;
        }

        .form-group {
            margin-bottom: calc(var(--skin-space-md) + var(--skin-space-xs));
        }

        .form-group:last-child {
            margin-bottom: 0;
        }

        .form-label {
            display: block;
            font-size: var(--skin-text-sm);
            font-weight: var(--skin-weight-medium);
            margin-bottom: var(--skin-space-sm);
            color: var(--skin-color-text-primary);
        }

        .form-input {
            width: 100%;
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs) / 2) calc(var(--skin-space-md) - var(--skin-space-xs) / 2);
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid var(--skin-color-border);
            font-size: var(--skin-text-base);
            background: var(--skin-color-bg-card);
            color: var(--skin-color-text-primary);
            transition: border-color var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .form-input:focus {
            outline: none;
            border-color: var(--skin-color-text-primary);
        }

        .form-input:disabled {
            background: var(--skin-color-bg-hover);
            cursor: not-allowed;
        }

        .form-hint {
            font-size: calc(var(--skin-text-xs) + var(--skin-text-xs) / 11);
            color: var(--skin-color-text-muted);
            margin-top: calc(var(--skin-space-xs) * 1.5);
        }

        .toggle-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs)) 0;
            border-top: var(--skin-border-width) solid var(--skin-color-border);
            margin-top: var(--skin-space-xs);
        }

        .toggle-label {
            font-size: var(--skin-text-base);
        }

        .toggle-desc {
            font-size: calc(var(--skin-text-xs) + var(--skin-text-xs) / 11);
            color: var(--skin-color-text-secondary);
            margin-top: var(--skin-space-xs);
        }

        .toggle-switch {
            position: relative;
            width: calc(var(--skin-space-2xl) - var(--skin-space-xs));
            height: var(--skin-space-lg);
        }

        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }

        .toggle-slider {
            position: absolute;
            cursor: pointer;
            inset: 0;
            background-color: var(--skin-color-border);
            transition: var(--skin-motion-normal);
            border-radius: var(--skin-space-lg);
        }

        .toggle-slider:before {
            position: absolute;
            content: "";
            height: calc(var(--skin-space-md) + var(--skin-space-xs) / 2);
            width: calc(var(--skin-space-md) + var(--skin-space-xs) / 2);
            left: calc(var(--skin-space-xs) * 0.75);
            bottom: calc(var(--skin-space-xs) * 0.75);
            background-color: var(--skin-color-bg-card);
            transition: var(--skin-motion-normal);
            border-radius: 50%;
        }

        .toggle-switch input:checked + .toggle-slider {
            background-color: var(--skin-color-accent);
        }

        .toggle-switch input:checked + .toggle-slider:before {
            transform: translateX(calc(var(--skin-space-md) + var(--skin-space-xs)));
        }

        .toggle-switch input:disabled + .toggle-slider {
            cursor: not-allowed;
            opacity: 0.5;
        }

        /* Status */
        .status-row {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs)) calc(var(--skin-space-md) + var(--skin-space-xs));
            padding: calc(var(--skin-space-md) - var(--skin-space-xs) / 2) var(--skin-space-md);
            border-radius: var(--skin-radius-md);
            background: var(--skin-color-bg-hover);
            border: var(--skin-border-width) solid var(--skin-color-border);
        }

        .status-item {
            display: flex;
            align-items: center;
            gap: var(--skin-space-sm);
            font-size: var(--skin-text-sm);
        }

        .status-label {
            color: var(--skin-color-text-secondary);
        }

        .status-value {
            font-weight: var(--skin-weight-medium);
        }

        .status-dot {
            width: calc(var(--skin-space-sm) + var(--skin-space-xs) / 2);
            height: calc(var(--skin-space-sm) + var(--skin-space-xs) / 2);
            border-radius: 50%;
            flex-shrink: 0;
        }

        .status-dot.ok {
            background: var(--skin-color-success);
        }

        .status-dot.degraded {
            background: var(--skin-color-warning);
        }

        .status-dot.unavailable {
            background: var(--skin-color-danger);
        }

        .status-dot.unknown {
            background: var(--skin-color-text-muted);
        }

        .status-error {
            width: 100%;
            font-size: calc(var(--skin-text-xs) + var(--skin-text-xs) / 11);
            color: var(--skin-color-danger);
            margin: 0;
        }

        .link-row {
            display: flex;
            flex-wrap: wrap;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs));
            margin-top: var(--skin-space-md);
        }

        .link-btn {
            display: inline-flex;
            align-items: center;
            gap: var(--skin-space-sm);
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs) / 2) var(--skin-space-md);
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid var(--skin-color-border);
            background: var(--skin-color-bg-card);
            color: var(--skin-color-text-primary);
            font-size: var(--skin-text-sm);
            font-weight: var(--skin-weight-medium);
            cursor: pointer;
            transition: all calc(var(--skin-motion-fast) * 2 / 3) var(--skin-motion-ease);
        }

        .link-btn:hover {
            background: var(--skin-color-bg-hover);
        }

        .link-btn .material-symbols-outlined {
            font-size: var(--skin-text-lg);
        }

        .honest-note {
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-secondary);
            margin: var(--skin-space-md) 0 0 0;
            line-height: var(--skin-leading-normal);
        }

        .disabled-reason {
            font-size: calc(var(--skin-text-xs) + var(--skin-text-xs) / 11);
            color: var(--skin-color-danger);
            margin: calc(var(--skin-space-sm) + var(--skin-space-xs)) 0 0 0;
        }

        .loading {
            padding: var(--skin-space-lg);
            color: var(--skin-color-text-muted);
            font-size: var(--skin-text-sm);
        }

        .error-banner {
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs)) var(--skin-space-md);
            border-radius: var(--skin-radius-md);
            background: color-mix(in srgb, var(--skin-color-danger) 10%, transparent);
            border: var(--skin-border-width) solid color-mix(in srgb, var(--skin-color-danger) 30%, transparent);
            color: var(--skin-color-danger);
            font-size: var(--skin-text-sm);
            margin-bottom: var(--skin-space-md);
        }

        .meta-line {
            font-size: calc(var(--skin-text-xs) + var(--skin-text-xs) / 11);
            color: var(--skin-color-text-muted);
            margin-top: calc(var(--skin-space-sm) + var(--skin-space-xs));
        }
    `,
    ];

    /** Caller may edit platform settings (system:configure / settings:edit). */
    @property({ type: Boolean }) canEdit = false;

    @state() private _loading = true;
    @state() private _loadError = '';
    @state() private _saveError = '';
    @state() private _saved = false;
    @state() private _dirty = false;
    @state() private _saving = false;
    @state() private _source = '';
    @state() private _values: SomabrainSettingsValues = {
        url: '',
        namespace: '',
        retention_days: 365,
        sleep_interval: 21600,
        consolidation_enabled: true,
    };
    @state() private _connector: BrainConnectorHealth | null = null;
    @state() private _connectorError = '';

    /** True when any field differs from the last loaded snapshot. */
    get isDirty(): boolean {
        return this._dirty;
    }

    override connectedCallback() {
        super.connectedCallback();
        void this._load();
    }

    /** PUT edited values. Returns true on success. Shell Save calls this. */
    async save(): Promise<boolean> {
        if (!this.canEdit || !this._dirty || this._saving) return false;
        this._saving = true;
        this._saveError = '';
        this._saved = false;
        try {
            await apiClient.put(SETTINGS_PATH, {
                values: {
                    url: this._values.url,
                    namespace: this._values.namespace,
                    retention_days: Number(this._values.retention_days),
                    sleep_interval: Number(this._values.sleep_interval),
                    consolidation_enabled: this._values.consolidation_enabled,
                },
            });
            this._dirty = false;
            this._saved = true;
            this._emitDirty();
            await this._loadSettings();
            await this._loadConnector();
            return true;
        } catch (error) {
            const text = error instanceof Error ? error.message : String(error);
            this._saveError = `Couldn't save SomaBrain settings. ${text}`;
            return false;
        } finally {
            this._saving = false;
        }
    }

    private _emitDirty() {
        this.dispatchEvent(
            new CustomEvent('soma-settings-dirty', {
                bubbles: true,
                composed: true,
                detail: { entity: 'somabrain', dirty: this._dirty },
            }),
        );
    }

    private async _load(): Promise<void> {
        this._loading = true;
        this._loadError = '';
        await Promise.all([this._loadSettings(), this._loadConnector()]);
        this._loading = false;
    }

    private async _loadSettings(): Promise<void> {
        try {
            const res = await apiClient.get<SettingsResponse>(SETTINGS_PATH);
            const v = res?.values ?? {};
            this._source = res?.source ?? '';
            this._values = {
                url: String(v.url ?? ''),
                namespace: String(v.namespace ?? ''),
                retention_days: Number(v.retention_days ?? 365),
                sleep_interval: Number(v.sleep_interval ?? 21600),
                consolidation_enabled: v.consolidation_enabled !== false,
            };
            this._dirty = false;
            this._emitDirty();
        } catch (error) {
            this._loadError = `Couldn't load SomaBrain settings. ${
                error instanceof Error ? error.message : String(error)
            }`;
        }
    }

    private async _loadConnector(): Promise<void> {
        this._connectorError = '';
        try {
            this._connector = await apiClient.get<BrainConnectorHealth>(CONNECTOR_PATH);
        } catch (error) {
            this._connector = null;
            this._connectorError =
                error instanceof Error ? error.message : String(error);
        }
    }

    private _setField(key: keyof SomabrainSettingsValues, raw: string | boolean) {
        if (!this.canEdit) return;
        let value: string | number | boolean = raw;
        if (key === 'retention_days' || key === 'sleep_interval') {
            const n = Number(raw);
            value = Number.isFinite(n) ? n : 0;
        }
        this._values = { ...this._values, [key]: value } as SomabrainSettingsValues;
        this._dirty = true;
        this._saved = false;
        this._saveError = '';
        this._emitDirty();
    }

    private _revert() {
        void this._loadSettings();
        this._saveError = '';
        this._saved = false;
    }

    private _openRoute(route: string) {
        window.dispatchEvent(
            new CustomEvent('soma-navigate', { detail: { route } }),
        );
    }

    private _connectorStatus(): {
        label: string;
        className: string;
        note: string;
    } {
        if (!this._connector) {
            if (this._connectorError) {
                return {
                    label: 'unavailable',
                    className: 'unavailable',
                    note: 'SomaBrain unreachable. Chat continues; memory may queue.',
                };
            }
            return { label: 'unknown', className: 'unknown', note: '' };
        }
        const { connected, circuit } = this._connector;
        if (connected && circuit === 'closed') {
            return { label: 'ok', className: 'ok', note: '' };
        }
        if (circuit === 'open' || (!connected && circuit === 'half_open')) {
            return {
                label: 'degraded',
                className: 'degraded',
                note: 'SomaBrain unreachable. Chat continues; memory may queue.',
            };
        }
        return {
            label: 'unavailable',
            className: 'unavailable',
            note: 'SomaBrain unreachable. Chat continues; memory may queue.',
        };
    }

    private _formatLastSuccess(ts?: number | null): string {
        if (typeof ts !== 'number' || ts <= 0) return '—';
        return new Date(ts * (ts < 1e12 ? 1000 : 1)).toLocaleString();
    }

    override render() {
        if (this._loading) {
            return html`<div class="section loading" role="status">Loading SomaBrain settings…</div>`;
        }

        const status = this._connectorStatus();
        const editTitle = this.canEdit ? 'Edit' : DISABLED_REASON;

        return html`
            <!-- Connection -->
            <div class="section" data-section="somabrain-connection">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">psychology</span>
                    Brain connection
                </h3>
                <p class="section-desc">
                    Operator-owned SomaBrain endpoint and retention. Edits save to
                    InfrastructureConfig via GET/PUT /api/v2/core/settings/somabrain.
                </p>

                ${this._loadError
                    ? html`<div class="error-banner" role="alert">${this._loadError}</div>`
                    : null}
                ${this._saveError
                    ? html`<div class="error-banner" role="alert">${this._saveError}</div>`
                    : null}
                ${this._saved && !this._saveError
                    ? html`<div class="meta-line" role="status">Settings saved.</div>`
                    : null}

                <div class="form-group">
                    <label class="form-label" for="sb-url">URL</label>
                    <input
                        id="sb-url"
                        class="form-input"
                        type="url"
                        data-control="somabrain-url"
                        placeholder="https://brain.example.internal"
                        .value=${this._values.url}
                        title=${editTitle}
                        ?disabled=${!this.canEdit}
                        @input=${(e: Event) =>
                            this._setField('url', (e.target as HTMLInputElement).value)}
                    />
                    <div class="form-hint">Maps to SOMABRAIN_URL (chain name on the settings row).</div>
                </div>

                <div class="form-group">
                    <label class="form-label" for="sb-ns">Namespace</label>
                    <input
                        id="sb-ns"
                        class="form-input"
                        type="text"
                        data-control="somabrain-namespace"
                        .value=${this._values.namespace}
                        title=${editTitle}
                        ?disabled=${!this.canEdit}
                        @input=${(e: Event) =>
                            this._setField('namespace', (e.target as HTMLInputElement).value)}
                    />
                    <div class="form-hint">Maps to SOMABRAIN_NAMESPACE.</div>
                </div>

                <div class="form-group">
                    <label class="form-label" for="sb-retention">Retention (days)</label>
                    <input
                        id="sb-retention"
                        class="form-input"
                        type="number"
                        min="1"
                        data-control="somabrain-retention_days"
                        .value=${String(this._values.retention_days)}
                        title=${editTitle}
                        ?disabled=${!this.canEdit}
                        @input=${(e: Event) =>
                            this._setField('retention_days', (e.target as HTMLInputElement).value)}
                    />
                </div>

                <div class="form-group">
                    <label class="form-label" for="sb-sleep">Sleep interval (seconds)</label>
                    <input
                        id="sb-sleep"
                        class="form-input"
                        type="number"
                        min="0"
                        data-control="somabrain-sleep_interval"
                        .value=${String(this._values.sleep_interval)}
                        title=${editTitle}
                        ?disabled=${!this.canEdit}
                        @input=${(e: Event) =>
                            this._setField('sleep_interval', (e.target as HTMLInputElement).value)}
                    />
                    <div class="form-hint">Maps to the settings field only — not a Temporal schedule.</div>
                </div>

                <div class="toggle-row">
                    <div>
                        <div class="toggle-label">Consolidation</div>
                        <div class="toggle-desc">Enable memory consolidation (consolidation_enabled)</div>
                    </div>
                    <label class="toggle-switch">
                        <input
                            type="checkbox"
                            data-control="somabrain-consolidation_enabled"
                            .checked=${this._values.consolidation_enabled}
                            title=${editTitle}
                            ?disabled=${!this.canEdit}
                            @change=${(e: Event) =>
                                this._setField(
                                    'consolidation_enabled',
                                    (e.target as HTMLInputElement).checked,
                                )}
                        />
                        <span class="toggle-slider"></span>
                    </label>
                </div>

                ${!this.canEdit
                    ? html`<p class="disabled-reason" role="status">${DISABLED_REASON}</p>`
                    : html`
                        <div class="link-row">
                            <button
                                class="link-btn"
                                data-control="somabrain-revert"
                                ?disabled=${!this._dirty || this._saving}
                                @click=${this._revert}
                            >
                                <span class="material-symbols-outlined">undo</span>
                                Revert
                            </button>
                        </div>
                    `}

                ${this._source
                    ? html`<p class="meta-line">Source: ${this._source}</p>`
                    : nothing}
            </div>

            <!-- Status (read-only) -->
            <div class="section" data-section="somabrain-status">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">cable</span>
                    Connector status
                </h3>
                <p class="section-desc">
                    Read-only health from GET /api/v2/core/brain-connector
                    (circuit + ping). Not a browser probe of SomaBrain.
                </p>

                <div class="status-row" data-status="brain-connector">
                    <div class="status-item">
                        <span class="status-dot ${status.className}" aria-hidden="true"></span>
                        <span class="status-label">connector</span>
                        <span class="status-value" data-testid="connector-state">${status.label}</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">circuit</span>
                        <span class="status-value">${this._connector?.circuit ?? '—'}</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">last success</span>
                        <span class="status-value">${this._formatLastSuccess(this._connector?.last_success_at)}</span>
                    </div>
                    ${typeof this._connector?.latency_ms === 'number'
                        ? html`
                            <div class="status-item">
                                <span class="status-label">latency</span>
                                <span class="status-value">${this._connector.latency_ms} ms</span>
                            </div>
                        `
                        : null}
                    ${this._connector?.base_url
                        ? html`
                            <div class="status-item">
                                <span class="status-label">base</span>
                                <span class="status-value">${this._connector.base_url}</span>
                            </div>
                        `
                        : null}
                    ${status.note
                        ? html`<p class="status-error" role="status">${status.note}</p>`
                        : null}
                    ${!status.note && this._connector?.last_error
                        ? html`<p class="status-error" role="status">${this._connector.last_error}</p>`
                        : null}
                    ${this._connectorError && !status.note
                        ? html`<p class="status-error" role="status">${this._connectorError}</p>`
                        : null}
                </div>

                <div class="link-row">
                    <button
                        class="link-btn"
                        data-control="open-memory"
                        @click=${() => this._openRoute('/memory')}
                    >
                        <span class="material-symbols-outlined">folder</span>
                        Open /memory
                    </button>
                    <button
                        class="link-btn"
                        data-control="open-cognitive"
                        @click=${() => this._openRoute('/cognitive')}
                    >
                        <span class="material-symbols-outlined">neurology</span>
                        Open /cognitive
                    </button>
                </div>
            </div>

            <!-- Honest gaps (UI-S-56) -->
            <div class="section" data-section="somabrain-gaps">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">info</span>
                    Not available as fields
                </h3>
                <p class="honest-note" data-note="vault-token">
                    Memory token lives in Vault — set in Vault, not editable here.
                </p>
                <p class="honest-note" data-note="cognitive-knobs">
                    Cognitive knobs are per-agent on /cognitive.
                </p>
                <p class="honest-note" data-note="temporal-host">
                    Temporal host is deploy env, not this form.
                </p>
                <p class="honest-note" data-note="brainsetting-gap">
                    BrainSetting tunables have no agent API proxy to brain
                    /brain-settings — editors are omitted rather than invented.
                    Manage those on the SomaBrain service.
                </p>
                <p class="honest-note" data-note="not-on-screen">
                    Kafka reward topic, SFM URL (memory entity), and OPA policy
                    editor are not on this screen.
                </p>
            </div>

            <!-- Brain manager (embedded live surface) -->
            <div class="section" data-section="brain-manager">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">neurology</span>
                    Brain
                </h3>
                <p class="section-desc">
                    Live Brain manager — modulators, mode, IQ knobs, sleep, and
                    diagnostics. Connection knobs above stay the operator write
                    path.
                </p>
                <soma-brain-manager></soma-brain-manager>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-settings-somabrain': SomaSettingsSomaBrain;
    }
}
