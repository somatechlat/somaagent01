/**
 * Brain Manager — connection, modulators, mode, IQ knobs, sleep, diagnostics.
 *
 * Product label is "Brain" (naming law). Domain/code keep Capsule / capsule_id.
 *
 * Real endpoints only (SOMA LAW — no mocks, no invented routes):
 *   Connection   GET  /core/settings/somabrain
 *                GET  /core/brain-connector          (Test / status badge)
 *   Modulators   GET  /somabrain/cognitive/state/{agentId}
 *                PATCH /agents/{agentId}/capsule     neuromodulator_baseline
 *   IQ knobs     GET/PUT /core/agentiq/{capsuleId}   persona_config.knobs
 *                (CM-04 said PATCH capsule for knobs; CapsuleConfigUpdate has
 *                 no persona_config field — control-map X-01 binds the live
 *                 AgentIQ PUT. Never invent a knobs body on the capsule PATCH.)
 *   Sleep        GET  /somabrain/cognitive/sleep/status/{agentId}
 *                POST /somabrain/cognitive/sleep/{agentId}
 *   Diagnostics  GET  /core/brain-connector · /memory/status
 *                GET  /somabrain/brain/status/{agentId}
 *
 * Neuromodulators render raw server values only — no invented % meters
 * (REQ-UIX-010 / CM-04 SB-60). Apply is GATED on cognitive:edit from /auth/me.
 */

import { LitElement, html, css, nothing } from 'lit';
import { glassCard } from '../styles/glass.js';
import { moduleBase } from '../styles/module-base.js';
import { customElement, property, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';

/** SomaBrain physiological clamp ranges (admin/agents/services/somabrain_integration.py). */
const NEUROMOD_RANGES: Record<string, { min: number; max: number; step: number }> = {
    dopamine: { min: 0, max: 0.8, step: 0.01 },
    serotonin: { min: 0, max: 1, step: 0.01 },
    noradrenaline: { min: 0, max: 0.1, step: 0.001 },
    norepinephrine: { min: 0, max: 0.1, step: 0.001 },
    acetylcholine: { min: 0, max: 0.5, step: 0.01 },
};

/** UI slots → server keys. NE accepts either live key the stack has used. */
const MODULATOR_SLOTS = [
    { id: 'DA', label: 'DA', keys: ['dopamine'] },
    { id: '5-HT', label: '5-HT', keys: ['serotonin'] },
    { id: 'NE', label: 'NE', keys: ['noradrenaline', 'norepinephrine'] },
    { id: 'ACh', label: 'ACh', keys: ['acetylcholine'] },
] as const;

const MODES = [
    { id: 'STD', name: 'Standard' },
    { id: 'DEV', name: 'Developer' },
    { id: 'TRN', name: 'Training' },
    { id: 'ADM', name: 'Admin' },
] as const;

type ModeId = (typeof MODES)[number]['id'];

interface BrainConnectorHealth {
    connected: boolean;
    circuit: string;
    base_url?: string;
    last_success_at?: number | null;
    last_error?: string | null;
    latency_ms?: number | null;
}

interface SomabrainSettingsValues {
    url: string;
    namespace: string;
    retention_days: number;
}

interface CapsuleLite {
    agent_id: string;
    capsule_id: string;
    neuromodulator_baseline: Record<string, number>;
}

interface AgentIQPayload {
    capsule_id: string;
    knobs: Record<string, unknown>;
    derived: Record<string, unknown>;
    response_styles: string[];
}

interface SleepStatus {
    state: string;
    is_sleeping: boolean | null;
    last_sleep: string | null;
    next_scheduled: string | null;
}

interface MemoryStatus {
    state: string;
    summary: string;
    read_ok: boolean;
    write_ok: boolean;
    degraded: boolean;
    circuit: string;
    brain_status: string;
    reason: string;
}

interface BrainStatus {
    status: string;
    degradation_level?: string;
    degraded?: boolean;
}

@customElement('soma-brain-manager')
export class SomaBrainManager extends LitElement {
    static styles = [
        glassCard,
        moduleBase,
        css`
        :host {
            display: block;
            color: var(--skin-color-text-primary);
            font-family: var(--skin-font-sans);
            font-size: var(--skin-text-base);
        }

        * {
            box-sizing: border-box;
        }

        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: var(--skin-text-xl);
            line-height: 1;
            display: inline-block;
            -webkit-font-smoothing: antialiased;
        }

        .card {
            background: var(--skin-color-bg-card);
            border: var(--skin-border-width) solid var(--skin-color-border));
            border-radius: var(--skin-radius-lg);
            padding: var(--skin-space-lg);
            margin-bottom: var(--skin-space-lg);
        }

        .card-title {
            font-size: var(--skin-text-lg);
            font-weight: var(--skin-weight-semibold);
            margin: 0 0 var(--skin-space-xs) 0;
            display: flex;
            align-items: center;
            gap: var(--skin-space-sm);
        }

        .card-title .material-symbols-outlined {
            color: var(--skin-color-text-secondary);
        }

        .card-desc {
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-secondary);
            margin: 0 0 var(--skin-space-lg) 0;
            line-height: var(--skin-leading-normal);
        }

        .grid-2 {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: var(--skin-space-md);
        }

        @media (max-width: 720px) {
            .grid-2 {
                grid-template-columns: 1fr;
            }
        }

        .field {
            margin-bottom: var(--skin-space-md);
        }

        .field:last-child {
            margin-bottom: 0;
        }

        .label {
            display: block;
            font-size: var(--skin-text-sm);
            font-weight: var(--skin-weight-medium);
            margin-bottom: var(--skin-space-xs);
        }

        .input {
            width: 100%;
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs) * 0.5) calc(var(--skin-space-md) - var(--skin-space-xs) * 0.5);
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid var(--skin-color-border));
            font-size: var(--skin-text-base);
            background: var(--skin-color-bg-base);
            color: var(--skin-color-text-primary);
        }

        .input:focus {
            outline: var(--skin-focus-ring-width) solid var(--skin-focus-ring);
            outline-offset: var(--skin-focus-ring-offset);
        }

        .input:disabled {
            background: var(--skin-color-bg-hover);
            cursor: not-allowed;
            color: var(--skin-color-text-muted);
        }

        .hint {
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-muted);
            margin-top: var(--skin-space-xs);
        }

        .row {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: var(--skin-space-sm);
        }

        .row-between {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: var(--skin-space-sm);
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: var(--skin-space-xs);
            padding: var(--skin-space-sm) var(--skin-space-md);
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid var(--skin-color-border));
            background: var(--skin-color-bg-base);
            color: var(--skin-color-text-primary);
            font-size: var(--skin-text-sm);
            font-weight: var(--skin-weight-medium);
            cursor: pointer;
            transition: background var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .btn:hover:not(:disabled) {
            background: var(--skin-color-bg-hover);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .btn.primary {
            background: var(--skin-color-accent);
            border-color: var(--skin-color-accent);
            color: var(--skin-color-accent-text);
        }

        .btn.primary:hover:not(:disabled) {
            background: var(--skin-color-accent-hover);
        }

        .btn .material-symbols-outlined {
            font-size: var(--skin-text-lg);
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: calc(var(--skin-space-sm) * 0.75);
            padding: var(--skin-space-xs) calc(var(--skin-space-sm) + var(--skin-space-xs) * 0.5);
            border-radius: var(--skin-radius-full);
            font-size: var(--skin-text-xs);
            font-weight: var(--skin-weight-semibold);
            border: var(--skin-border-width) solid var(--skin-color-border));
        }

        .badge .dot {
            width: var(--skin-space-sm);
            height: var(--skin-space-sm);
            border-radius: var(--skin-radius-full);
        }

        .badge.ok {
            background: color-mix(in srgb, var(--skin-color-success) 12%, transparent);
            color: var(--skin-color-success);
        }

        .badge.ok .dot {
            background: var(--skin-color-success);
        }

        .badge.warn {
            background: color-mix(in srgb, var(--skin-color-warning) 12%, transparent);
            color: var(--skin-color-warning);
        }

        .badge.warn .dot {
            background: var(--skin-color-warning);
        }

        .badge.danger {
            background: color-mix(in srgb, var(--skin-color-danger) 12%, transparent);
            color: var(--skin-color-danger);
        }

        .badge.danger .dot {
            background: var(--skin-color-danger);
        }

        .badge.neutral {
            background: var(--skin-color-bg-hover);
            color: var(--skin-color-text-secondary);
        }

        .badge.neutral .dot {
            background: var(--skin-color-text-muted);
        }

        .status-line {
            display: flex;
            flex-wrap: wrap;
            gap: var(--skin-space-md);
            padding: var(--skin-space-md);
            border-radius: var(--skin-radius-md);
            background: var(--skin-color-bg-hover);
            border: var(--skin-border-width) solid var(--skin-color-border));
            margin-bottom: var(--skin-space-md);
        }

        .stat {
            display: flex;
            flex-direction: column;
            gap: var(--skin-space-xs);
            min-width: calc(var(--skin-space-2xl) * 2 + var(--skin-space-xs));
        }

        .stat-k {
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-muted);
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .stat-v {
            font-size: var(--skin-text-sm);
            font-weight: var(--skin-weight-medium);
            font-variant-numeric: tabular-nums;
        }

        /* Modulators — raw values, number + slider. No % meters. */
        .mod-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: var(--skin-space-md);
        }

        @media (max-width: 720px) {
            .mod-grid {
                grid-template-columns: 1fr;
            }
        }

        .mod-card {
            padding: var(--skin-space-md);
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid var(--skin-color-border));
            background: var(--skin-color-bg-base);
        }

        .mod-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: var(--skin-space-sm);
        }

        .mod-name {
            font-size: var(--skin-text-xs);
            font-weight: var(--skin-weight-bold);
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--skin-color-accent);
        }

        .mod-value {
            font-size: var(--skin-text-lg);
            font-weight: var(--skin-weight-semibold);
            font-variant-numeric: tabular-nums;
        }

        .mod-controls {
            display: grid;
            grid-template-columns: 1fr calc(var(--skin-space-2xl) + var(--skin-space-xl) + var(--skin-space-md));
            gap: var(--skin-space-sm);
            align-items: center;
        }

        input[type='range'] {
            -webkit-appearance: none;
            appearance: none;
            width: 100%;
            height: calc(var(--skin-space-sm) * 0.75);
            border-radius: var(--skin-radius-full);
            background: var(--skin-color-border-subtle);
            outline: none;
        }

        input[type='range']::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: var(--skin-space-md);
            height: var(--skin-space-md);
            border-radius: var(--skin-radius-full);
            background: var(--skin-color-accent);
            border: var(--skin-border-width) solid var(--skin-color-bg-base);
            cursor: pointer;
        }

        input[type='range']:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .mod-help {
            margin-top: var(--skin-space-xs);
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-muted);
        }

        .gated {
            margin-top: var(--skin-space-sm);
            padding: var(--skin-space-sm) var(--skin-space-md);
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid var(--skin-color-warning);
            background: color-mix(in srgb, var(--skin-color-warning) 10%, transparent);
            color: var(--skin-color-text-primary);
            font-size: var(--skin-text-sm);
        }

        .error-banner {
            padding: var(--skin-space-sm) var(--skin-space-md);
            border-radius: var(--skin-radius-md);
            background: color-mix(in srgb, var(--skin-color-danger) 10%, transparent);
            border: var(--skin-border-width) solid var(--skin-color-danger);
            color: var(--skin-color-danger);
            font-size: var(--skin-text-sm);
            margin-bottom: var(--skin-space-md);
        }

        .ok-note {
            font-size: var(--skin-text-sm);
            color: var(--skin-color-success);
            margin: var(--skin-space-sm) 0 0 0;
        }

        .muted {
            color: var(--skin-color-text-muted);
            font-size: var(--skin-text-sm);
        }

        .loading {
            padding: var(--skin-space-lg);
            color: var(--skin-color-text-muted);
            font-size: var(--skin-text-sm);
        }

        .knob-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: var(--skin-space-md);
        }

        @media (max-width: 900px) {
            .knob-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }

        .knob-card {
            padding: var(--skin-space-md);
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid var(--skin-color-border));
            background: var(--skin-color-bg-base);
        }

        .knob-name {
            font-size: var(--skin-text-xs);
            font-weight: var(--skin-weight-semibold);
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: var(--skin-color-text-secondary);
            margin-bottom: var(--skin-space-xs);
        }

        .knob-value {
            font-size: var(--skin-text-xl);
            font-weight: var(--skin-weight-semibold);
            font-variant-numeric: tabular-nums;
            margin-bottom: var(--skin-space-sm);
        }

        .diag-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(calc(var(--skin-space-2xl) * 3 + var(--skin-space-lg) + var(--skin-space-md)), 1fr));
            gap: var(--skin-space-md);
        }

        .diag-item {
            padding: var(--skin-space-md);
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid var(--skin-color-border));
            background: var(--skin-color-bg-hover);
        }

        .diag-k {
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-muted);
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: var(--skin-space-xs);
        }

        .diag-v {
            font-size: var(--skin-text-sm);
            font-weight: var(--skin-weight-medium);
        }

        .chip-gated {
            display: inline-flex;
            align-items: center;
            gap: var(--skin-space-xs);
            padding: var(--skin-space-xs) var(--skin-space-sm);
            border-radius: var(--skin-radius-full);
            border: var(--skin-border-width) solid var(--skin-color-border));
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-secondary);
            background: var(--skin-color-bg-hover);
        }
    `
    ];

    /** Agent whose capsule / cognitive state this manager drives. */
    @property({ type: String, attribute: 'agent-id' }) agentId = '';

    /** Controlled agent mode. Emits `set-mode` on change. */
    @property({ type: String }) mode: ModeId = 'STD';

    /** Caller may edit connection settings (system:configure). */
    @property({ type: Boolean, attribute: 'can-edit-settings' }) canEditSettings = false;

    @state() private _loading = true;
    @state() private _permissions: string[] = [];
    @state() private _conn: BrainConnectorHealth | null = null;
    @state() private _connError = '';
    @state() private _testing = false;
    @state() private _settings: SomabrainSettingsValues = {
        url: '',
        namespace: '',
        retention_days: 365,
    };
    @state() private _settingsError = '';

    @state() private _capsule: CapsuleLite | null = null;
    @state() private _mods: Record<string, number> = {};
    @state() private _modsSnapshot: Record<string, number> = {};
    @state() private _modsDirty = false;
    @state() private _modsBusy = false;
    @state() private _modsMessage = '';
    @state() private _modsError = '';

    @state() private _knobs: {
        intelligence_level: number;
        autonomy_level: number;
        resource_budget: number;
        response_style: string;
    } | null = null;
    @state() private _knobsSnapshot: {
        intelligence_level: number;
        autonomy_level: number;
        resource_budget: number;
        response_style: string;
    } | null = null;
    @state() private _knobsStyles: string[] = [];
    @state() private _knobsDirty = false;
    @state() private _knobsBusy = false;
    @state() private _knobsMessage = '';

    @state() private _sleep: SleepStatus | null = null;
    @state() private _sleepBusy = false;
    @state() private _sleepMessage = '';

    @state() private _memory: MemoryStatus | null = null;
    @state() private _brainStatus: BrainStatus | null = null;

    private _unsubscribe: (() => void) | null = null;

    get canEditCognitive(): boolean {
        return this._permissions.includes('cognitive:edit');
    }

    private get _resolvedAgentId(): string {
        if (this.agentId) return this.agentId;
        return (
            sessionStorage.getItem('soma_agent_id') ||
            localStorage.getItem('soma_agent_id') ||
            ''
        );
    }

    override connectedCallback() {
        super.connectedCallback();
        void this._bootstrap();
    }

    disconnectedCallback() {
        this._unsubscribe?.();
        this._unsubscribe = null;
        super.disconnectedCallback();
    }

    override updated(changed: Map<string, unknown>) {
        if (changed.has('agentId')) {
            void this._loadAgentScoped();
        }
    }

    private async _bootstrap() {
        this._loading = true;
        await Promise.all([
            this._loadPermissions(),
            this._loadConnection(),
            this._loadAgentScoped(),
        ]);
        this._loading = false;
    }

    private async _loadPermissions() {
        try {
            const me = await apiClient.get<{ permissions?: string[] }>('/auth/me');
            this._permissions = me.permissions ?? [];
        } catch {
            // Fail closed: no permission grant is invented.
            this._permissions = [];
        }
    }

    private async _loadConnection() {
        this._settingsError = '';
        this._connError = '';
        const [settingsRes, connRes] = await Promise.allSettled([
            apiClient.get<{ values?: Partial<SomabrainSettingsValues> }>(
                '/core/settings/somabrain',
            ),
            apiClient.get<BrainConnectorHealth>('/core/brain-connector'),
        ]);
        if (settingsRes.status === 'fulfilled') {
            const v = settingsRes.value?.values ?? {};
            this._settings = {
                url: String(v.url ?? ''),
                namespace: String(v.namespace ?? ''),
                retention_days: Number(v.retention_days ?? 365),
            };
        } else {
            this._settingsError =
                settingsRes.reason instanceof Error
                    ? settingsRes.reason.message
                    : String(settingsRes.reason);
        }
        if (connRes.status === 'fulfilled') {
            this._conn = connRes.value;
            this._connError = '';
        } else {
            this._conn = null;
            this._connError =
                connRes.reason instanceof Error
                    ? connRes.reason.message
                    : String(connRes.reason);
        }
    }

    /** Test = re-probe the live connector health route. Not a browser ping. */
    private async _testConnection() {
        this._testing = true;
        this._connError = '';
        try {
            this._conn = await apiClient.get<BrainConnectorHealth>('/core/brain-connector');
        } catch (error) {
            this._conn = null;
            this._connError = error instanceof Error ? error.message : String(error);
        } finally {
            this._testing = false;
        }
    }

    private async _loadAgentScoped() {
        const agentId = this._resolvedAgentId;
        if (!agentId) {
            this._capsule = null;
            this._mods = {};
            this._modsSnapshot = {};
            this._knobs = null;
            this._sleep = null;
            this._memory = null;
            this._brainStatus = null;
            return;
        }
        await Promise.all([
            this._loadCapsule(agentId),
            this._loadSleep(agentId),
            this._loadDiagnostics(agentId),
        ]);
    }

    private async _loadCapsule(agentId: string) {
        try {
            const capsule = await apiClient.get<CapsuleLite>(
                `/agents/${agentId}/capsule`,
            );
            this._capsule = capsule;
            const baseline = { ...(capsule.neuromodulator_baseline ?? {}) };
            this._mods = baseline;
            this._modsSnapshot = { ...baseline };
            this._modsDirty = false;
            if (capsule.capsule_id) {
                await this._loadKnobs(capsule.capsule_id);
            }
        } catch (error) {
            this._capsule = null;
            this._modsError = error instanceof Error ? error.message : String(error);
        }
    }

    private async _loadKnobs(capsuleId: string) {
        try {
            const payload = await apiClient.get<AgentIQPayload>(
                `/core/agentiq/${capsuleId}`,
            );
            const k = payload.knobs ?? {};
            const next = {
                intelligence_level: Number(k.intelligence_level ?? 1),
                autonomy_level: Number(k.autonomy_level ?? 1),
                resource_budget: Number(k.resource_budget ?? 0),
                response_style: String(k.response_style ?? 'balanced'),
            };
            this._knobs = next;
            this._knobsSnapshot = { ...next };
            this._knobsDirty = false;
            this._knobsStyles = payload.response_styles ?? [];
        } catch (error) {
            this._knobs = null;
            this._knobsMessage =
                error instanceof Error ? error.message : String(error);
        }
    }

    private async _loadSleep(agentId: string) {
        try {
            this._sleep = await apiClient.get<SleepStatus>(
                `/somabrain/cognitive/sleep/status/${agentId}`,
            );
        } catch {
            this._sleep = null;
        }
    }

    private async _loadDiagnostics(agentId: string) {
        const [mem, brain] = await Promise.allSettled([
            apiClient.get<MemoryStatus>('/memory/status'),
            apiClient.get<BrainStatus>(`/somabrain/brain/status/${agentId}`),
        ]);
        this._memory = mem.status === 'fulfilled' ? mem.value : null;
        this._brainStatus = brain.status === 'fulfilled' ? brain.value : null;
    }

    // ── Modulators ─────────────────────────────────────────────────────────

    private _slotValue(slotKeys: readonly string[]): number | null {
        for (const key of slotKeys) {
            const v = this._mods[key];
            if (typeof v === 'number' && Number.isFinite(v)) return v;
        }
        return null;
    }

    private _slotKey(slotKeys: readonly string[]): string {
        for (const key of slotKeys) {
            if (typeof this._mods[key] === 'number') return key;
        }
        return slotKeys[0];
    }

    private _setMod(slotKeys: readonly string[], raw: string) {
        if (!this.canEditCognitive) return;
        const key = this._slotKey(slotKeys);
        const n = Number(raw);
        if (!Number.isFinite(n)) return;
        this._mods = { ...this._mods, [key]: n };
        this._modsDirty = true;
        this._modsMessage = '';
        this._modsError = '';
    }

    private _resetMods() {
        this._mods = { ...this._modsSnapshot };
        this._modsDirty = false;
        this._modsMessage = 'Reverted to the last saved baseline.';
    }

    /**
     * Apply writes the capsule neuromodulator_baseline (the authority chat
     * loads). Requires cognitive:edit — otherwise GATED, never a silent no-op.
     */
    private async _applyMods() {
        const agentId = this._resolvedAgentId;
        if (!agentId) {
            this._modsError = 'No agent selected — modulators cannot be applied.';
            return;
        }
        if (!this.canEditCognitive) {
            this._modsError = 'Requires cognitive:edit';
            return;
        }
        this._modsBusy = true;
        this._modsError = '';
        this._modsMessage = '';
        try {
            await apiClient.patch(`/agents/${agentId}/capsule`, {
                neuromodulator_baseline: { ...this._mods },
            });
            this._modsSnapshot = { ...this._mods };
            this._modsDirty = false;
            this._modsMessage = 'Modulators applied.';
            this.dispatchEvent(
                new CustomEvent('apply-modulators', {
                    bubbles: true,
                    composed: true,
                    detail: {
                        agentId,
                        neuromodulator_baseline: { ...this._mods },
                    },
                }),
            );
            await this._loadCapsule(agentId);
        } catch (error) {
            this._modsError = error instanceof Error ? error.message : String(error);
        } finally {
            this._modsBusy = false;
        }
    }

    // ── Mode ───────────────────────────────────────────────────────────────

    private _onModeChange(e: Event) {
        const value = (e.target as HTMLSelectElement).value as ModeId;
        this.mode = value;
        this.dispatchEvent(
            new CustomEvent('set-mode', {
                bubbles: true,
                composed: true,
                detail: { mode: value },
            }),
        );
    }

    // ── IQ knobs ───────────────────────────────────────────────────────────

    private _setKnob(
        key: 'intelligence_level' | 'autonomy_level' | 'resource_budget' | 'response_style',
        value: number | string,
    ) {
        if (!this._knobs) return;
        this._knobs = { ...this._knobs, [key]: value } as typeof this._knobs;
        this._knobsDirty = true;
        this._knobsMessage = '';
    }

    private _resetKnobs() {
        if (!this._knobsSnapshot) return;
        this._knobs = { ...this._knobsSnapshot };
        this._knobsDirty = false;
        this._knobsMessage = 'Reverted to the last saved knobs.';
    }

    /**
     * Persist knobs on the Capsule via the live AgentIQ PUT
     * (`PUT /core/agentiq/{capsule_id}` → `persona_config.knobs`).
     * CapsuleConfigUpdate cannot carry knobs (no persona_config field).
     */
    private async _saveKnobs() {
        const capsuleId = this._capsule?.capsule_id;
        if (!capsuleId || !this._knobs) {
            this._knobsMessage = 'No capsule selected — cannot save knobs.';
            return;
        }
        this._knobsBusy = true;
        this._knobsMessage = '';
        try {
            const payload = await apiClient.put<AgentIQPayload>(
                `/core/agentiq/${capsuleId}`,
                {
                    intelligence_level: this._knobs.intelligence_level,
                    autonomy_level: this._knobs.autonomy_level,
                    resource_budget: this._knobs.resource_budget,
                    response_style: this._knobs.response_style,
                },
            );
            const k = payload.knobs ?? {};
            const next = {
                intelligence_level: Number(k.intelligence_level ?? this._knobs.intelligence_level),
                autonomy_level: Number(k.autonomy_level ?? this._knobs.autonomy_level),
                resource_budget: Number(k.resource_budget ?? this._knobs.resource_budget),
                response_style: String(k.response_style ?? this._knobs.response_style),
            };
            this._knobs = next;
            this._knobsSnapshot = { ...next };
            this._knobsDirty = false;
            this._knobsStyles = payload.response_styles ?? this._knobsStyles;
            this._knobsMessage = 'Knobs saved.';
            this.dispatchEvent(
                new CustomEvent('save-knobs', {
                    bubbles: true,
                    composed: true,
                    detail: { capsuleId, knobs: next },
                }),
            );
        } catch (error) {
            this._knobsMessage = error instanceof Error ? error.message : String(error);
        } finally {
            this._knobsBusy = false;
        }
    }

    // ── Sleep ──────────────────────────────────────────────────────────────

    private async _runSleep() {
        const agentId = this._resolvedAgentId;
        if (!agentId) {
            this._sleepMessage = 'No agent selected — sleep cycle was not triggered.';
            return;
        }
        this._sleepBusy = true;
        this._sleepMessage = '';
        try {
            await apiClient.post(`/somabrain/cognitive/sleep/${agentId}`, {
                duration_minutes: 5,
                consolidate_memory: true,
            });
            this._sleepMessage = 'Sleep cycle triggered.';
            await this._loadSleep(agentId);
        } catch (error) {
            this._sleepMessage = error instanceof Error ? error.message : String(error);
        } finally {
            this._sleepBusy = false;
        }
    }

    // ── Render helpers ─────────────────────────────────────────────────────

    private _connBadge() {
        if (!this._conn) {
            if (this._connError) {
                return html`<span class="badge danger" data-testid="brain-conn-badge"
                    ><span class="dot"></span>unavailable</span
                >`;
            }
            return html`<span class="badge neutral" data-testid="brain-conn-badge"
                ><span class="dot"></span>unknown</span
            >`;
        }
        const { connected, circuit } = this._conn;
        if (connected && circuit === 'closed') {
            return html`<span class="badge ok" data-testid="brain-conn-badge"
                ><span class="dot"></span>ok</span
            >`;
        }
        if (circuit === 'open' || (!connected && circuit === 'half_open')) {
            return html`<span class="badge warn" data-testid="brain-conn-badge"
                ><span class="dot"></span>degraded</span
            >`;
        }
        return html`<span class="badge danger" data-testid="brain-conn-badge"
            ><span class="dot"></span>unavailable</span
        >`;
    }

    private _formatTs(ts?: number | null): string {
        if (typeof ts !== 'number' || ts <= 0) return '—';
        return new Date(ts * (ts < 1e12 ? 1000 : 1)).toLocaleString();
    }

    private _modCard(slot: (typeof MODULATOR_SLOTS)[number]) {
        const key = this._slotKey(slot.keys);
        const range = NEUROMOD_RANGES[key] ?? { min: 0, max: 1, step: 0.01 };
        const value = this._slotValue(slot.keys);
        const disabled = !this.canEditCognitive;
        return html`
            <div class="mod-card" data-slot=${slot.id}>
                <div class="mod-head">
                    <span class="mod-name">${slot.label}</span>
                    <span class="mod-value" data-testid="mod-${slot.id}"
                        >${value === null ? '—' : String(value)}</span
                    >
                </div>
                <div class="mod-controls">
                    <input
                        type="range"
                        min=${range.min}
                        max=${range.max}
                        step=${range.step}
                        .value=${value === null ? String(range.min) : String(value)}
                        ?disabled=${disabled}
                        title=${disabled ? 'Requires cognitive:edit' : slot.label}
                        @input=${(e: Event) =>
                            this._setMod(slot.keys, (e.target as HTMLInputElement).value)}
                    />
                    <input
                        class="input"
                        type="number"
                        min=${range.min}
                        max=${range.max}
                        step=${range.step}
                        .value=${value === null ? '' : String(value)}
                        ?disabled=${disabled}
                        title=${disabled ? 'Requires cognitive:edit' : slot.label}
                        @change=${(e: Event) =>
                            this._setMod(slot.keys, (e.target as HTMLInputElement).value)}
                    />
                </div>
                <div class="mod-help">
                    raw value · range ${range.min}–${range.max}
                </div>
            </div>
        `;
    }

    override render() {
        if (this._loading) {
            return html`<div class="loading" role="status">Loading Brain…</div>`;
        }

        const agentId = this._resolvedAgentId;
        const sleep = this._sleep;
        const mem = this._memory;
        const brain = this._brainStatus;

        return html`
            <!-- Connection -->
            <div class="card" data-section="brain-connection">
                <h3 class="card-title">
                    <span class="material-symbols-outlined">cable</span>
                    Connection
                </h3>
                <p class="card-desc">
                    Operator Brain endpoint and connector health. Test re-probes
                    GET /api/v2/core/brain-connector — not a browser ping.
                </p>

                ${this._settingsError
                    ? html`<div class="error-banner" role="alert">${this._settingsError}</div>`
                    : nothing}
                ${this._connError
                    ? html`<div class="error-banner" role="alert">${this._connError}</div>`
                    : nothing}

                <div class="grid-2">
                    <div class="field">
                        <label class="label" for="bm-url">URL</label>
                        <input
                            id="bm-url"
                            class="input"
                            type="url"
                            data-control="brain-url"
                            .value=${this._settings.url}
                            readonly
                        />
                        <div class="hint">SOMABRAIN_URL · edit on Settings › Brain</div>
                    </div>
                    <div class="field">
                        <label class="label" for="bm-ns">Namespace</label>
                        <input
                            id="bm-ns"
                            class="input"
                            type="text"
                            data-control="brain-namespace"
                            .value=${this._settings.namespace}
                            readonly
                        />
                        <div class="hint">SOMABRAIN_NAMESPACE · edit on Settings › Brain</div>
                    </div>
                    <div class="field">
                        <label class="label" for="bm-retention">Retention (days)</label>
                        <input
                            id="bm-retention"
                            class="input"
                            type="number"
                            min="1"
                            data-control="brain-retention"
                            .value=${String(this._settings.retention_days)}
                            readonly
                        />
                        <div class="hint">edit on Settings › Brain</div>
                    </div>
                    <div class="field">
                        <span class="label">Status</span>
                        <div class="row" data-testid="brain-status-badge">
                            ${this._connBadge()}
                            <span class="muted"
                                >circuit ${this._conn?.circuit ?? '—'}</span
                            >
                        </div>
                    </div>
                </div>

                <div class="row" style="margin-top: var(--skin-space-md, 16px)">
                    <button
                        class="btn"
                        data-control="brain-test"
                        ?disabled=${this._testing}
                        @click=${this._testConnection}
                    >
                        <span class="material-symbols-outlined">network_check</span>
                        ${this._testing ? 'Testing…' : 'Test'}
                    </button>
                </div>
            </div>

            <!-- Modulators -->
            <div class="card" data-section="brain-modulators">
                <h3 class="card-title">
                    <span class="material-symbols-outlined">neurology</span>
                    Modulators
                </h3>
                <p class="card-desc">
                    Raw neuromodulator values from the capsule baseline. No
                    percentage meters — the server sends numbers without a scale
                    (REQ-UIX-010). Apply writes
                    <code>neuromodulator_baseline</code> via
                    PATCH /api/v2/agents/{agentId}/capsule.
                </p>

                ${!agentId
                    ? html`<p class="muted">No agent selected — modulators are not loaded.</p>`
                    : html`
                          ${this._modsError
                              ? html`<div class="error-banner" role="alert">${this._modsError}</div>`
                              : nothing}
                          <div class="mod-grid">
                              ${MODULATOR_SLOTS.map((slot) => this._modCard(slot))}
                          </div>
                          ${!this.canEditCognitive
                              ? html`<div class="gated" role="status">Requires cognitive:edit</div>`
                              : html`
                                    <div
                                        class="row-between"
                                        style="margin-top: var(--skin-space-md, 16px)"
                                    >
                                        <button
                                            class="btn"
                                            data-control="mods-reset"
                                            ?disabled=${!this._modsDirty || this._modsBusy}
                                            @click=${this._resetMods}
                                        >
                                            Reset all
                                        </button>
                                        <button
                                            class="btn primary"
                                            data-control="mods-apply"
                                            ?disabled=${!this._modsDirty || this._modsBusy}
                                            @click=${this._applyMods}
                                        >
                                            ${this._modsBusy ? 'Applying…' : 'Apply modulators'}
                                        </button>
                                    </div>
                                    ${this._modsMessage
                                        ? html`<p class="ok-note" role="status">${this._modsMessage}</p>`
                                        : nothing}
                                `}
                      `}
            </div>

            <!-- Mode -->
            <div class="card" data-section="brain-mode">
                <h3 class="card-title">
                    <span class="material-symbols-outlined">tune</span>
                    Mode
                </h3>
                <p class="card-desc">
                    Agent run mode. Selection emits <code>set-mode</code> — the
                    chat turn carries the mode id (STD / DEV / TRN / ADM).
                </p>
                <div class="field" style="max-width: 320px">
                    <label class="label" for="bm-mode">Mode</label>
                    <select
                        id="bm-mode"
                        class="input"
                        data-control="brain-mode-select"
                        .value=${this.mode}
                        @change=${this._onModeChange}
                    >
                        ${MODES.map(
                            (m) =>
                                html`<option value=${m.id} ?selected=${this.mode === m.id}>
                                    ${m.name}
                                </option>`,
                        )}
                    </select>
                </div>
            </div>

            <!-- IQ knobs -->
            <div class="card" data-section="brain-iq">
                <h3 class="card-title">
                    <span class="material-symbols-outlined">psychology</span>
                    IQ
                </h3>
                <p class="card-desc">
                    Per-agent knobs stored on the agent. Save writes
                    <code>persona_config.knobs</code> via
                    PUT /api/v2/core/agentiq/{capsule_id} — the live knobs route.
                    Derived settings stay server-side.
                </p>

                ${!this._knobs
                    ? html`<p class="muted">
                          ${agentId
                              ? 'Loading knobs…'
                              : 'No agent selected — knobs are not loaded.'}
                      </p>`
                    : html`
                          <div class="knob-grid">
                              <div class="knob-card">
                                  <div class="knob-name">Intelligence</div>
                                  <div class="knob-value">${this._knobs.intelligence_level}</div>
                                  <input
                                      type="range"
                                      min="1"
                                      max="10"
                                      step="1"
                                      .value=${String(this._knobs.intelligence_level)}
                                      @input=${(e: Event) =>
                                          this._setKnob(
                                              'intelligence_level',
                                              Number((e.target as HTMLInputElement).value),
                                          )}
                                  />
                              </div>
                              <div class="knob-card">
                                  <div class="knob-name">Autonomy</div>
                                  <div class="knob-value">${this._knobs.autonomy_level}</div>
                                  <input
                                      type="range"
                                      min="1"
                                      max="10"
                                      step="1"
                                      .value=${String(this._knobs.autonomy_level)}
                                      @input=${(e: Event) =>
                                          this._setKnob(
                                              'autonomy_level',
                                              Number((e.target as HTMLInputElement).value),
                                          )}
                                  />
                              </div>
                              <div class="knob-card">
                                  <div class="knob-name">Resource</div>
                                  <div class="knob-value">${this._knobs.resource_budget}</div>
                                  <input
                                      class="input"
                                      type="number"
                                      min="0"
                                      step="0.01"
                                      .value=${String(this._knobs.resource_budget)}
                                      @change=${(e: Event) =>
                                          this._setKnob(
                                              'resource_budget',
                                              Number((e.target as HTMLInputElement).value),
                                          )}
                                  />
                              </div>
                              <div class="knob-card">
                                  <div class="knob-name">Style</div>
                                  <div class="knob-value" style="font-size: var(--skin-text-base, 14px)">
                                      ${this._knobs.response_style}
                                  </div>
                                  <select
                                      class="input"
                                      .value=${this._knobs.response_style}
                                      @change=${(e: Event) =>
                                          this._setKnob(
                                              'response_style',
                                              (e.target as HTMLSelectElement).value,
                                          )}
                                  >
                                      ${(this._knobsStyles.length
                                          ? this._knobsStyles
                                          : [this._knobs.response_style]
                                      ).map(
                                          (s) =>
                                              html`<option
                                                  value=${s}
                                                  ?selected=${this._knobs!.response_style === s}
                                              >
                                                  ${s}
                                              </option>`,
                                      )}
                                  </select>
                              </div>
                          </div>
                          <div
                              class="row-between"
                              style="margin-top: var(--skin-space-md, 16px)"
                          >
                              <button
                                  class="btn"
                                  data-control="knobs-reset"
                                  ?disabled=${!this._knobsDirty || this._knobsBusy}
                                  @click=${this._resetKnobs}
                              >
                                  Reset knobs
                              </button>
                              <button
                                  class="btn primary"
                                  data-control="knobs-save"
                                  ?disabled=${!this._knobsDirty || this._knobsBusy}
                                  @click=${this._saveKnobs}
                              >
                                  ${this._knobsBusy ? 'Saving…' : 'Save knobs'}
                              </button>
                          </div>
                          ${this._knobsMessage
                              ? html`<p class="ok-note" role="status">${this._knobsMessage}</p>`
                              : nothing}
                      `}
            </div>

            <!-- Sleep -->
            <div class="card" data-section="brain-sleep">
                <h3 class="card-title">
                    <span class="material-symbols-outlined">bedtime</span>
                    Sleep
                </h3>
                <p class="card-desc">
                    Real sleep state from GET
                    /api/v2/somabrain/cognitive/sleep/status/{agent_id}. No
                    invented REM/deep phases.
                </p>
                <div class="status-line">
                    <div class="stat">
                        <span class="stat-k">state</span>
                        <span class="stat-v" data-testid="sleep-state"
                            >${sleep?.state ?? '—'}</span
                        >
                    </div>
                    <div class="stat">
                        <span class="stat-k">sleeping</span>
                        <span class="stat-v"
                            >${sleep?.is_sleeping === null || sleep?.is_sleeping === undefined
                                ? '—'
                                : sleep.is_sleeping
                                  ? 'yes'
                                  : 'no'}</span
                        >
                    </div>
                    <div class="stat">
                        <span class="stat-k">last sleep</span>
                        <span class="stat-v">${sleep?.last_sleep ?? '—'}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-k">next scheduled</span>
                        <span class="stat-v">${sleep?.next_scheduled ?? '—'}</span>
                    </div>
                </div>
                <div class="row">
                    <button
                        class="btn primary"
                        data-control="sleep-run"
                        ?disabled=${this._sleepBusy || !agentId}
                        title=${agentId ? 'Trigger sleep cycle' : 'No agent selected'}
                        @click=${this._runSleep}
                    >
                        <span class="material-symbols-outlined">bedtime</span>
                        ${this._sleepBusy ? 'Running…' : 'Run consolidation'}
                    </button>
                    ${this._sleepMessage
                        ? html`<span class="muted" role="status">${this._sleepMessage}</span>`
                        : nothing}
                </div>
            </div>

            <!-- Diagnostics -->
            <div class="card" data-section="brain-diagnostics">
                <h3 class="card-title">
                    <span class="material-symbols-outlined">monitoring</span>
                    Diagnostics
                </h3>
                <p class="card-desc">
                    Read-only probes. Values render only when a live route
                    reports them.
                </p>
                <div class="diag-grid">
                    <div class="diag-item">
                        <div class="diag-k">memory</div>
                        <div class="diag-v" data-testid="diag-memory">
                            ${mem
                                ? html`${mem.state} · ${mem.summary}`
                                : html`<span class="muted">—</span>`}
                        </div>
                    </div>
                    <div class="diag-item">
                        <div class="diag-k">sfm circuit</div>
                        <div class="diag-v" data-testid="diag-circuit">
                            ${this._conn?.circuit ?? (this._connError ? 'unavailable' : '—')}
                        </div>
                    </div>
                    <div class="diag-item">
                        <div class="diag-k">latency</div>
                        <div class="diag-v">
                            ${typeof this._conn?.latency_ms === 'number'
                                ? html`${this._conn.latency_ms} ms`
                                : html`<span class="muted">—</span>`}
                        </div>
                    </div>
                    <div class="diag-item">
                        <div class="diag-k">last success</div>
                        <div class="diag-v">
                            ${this._formatTs(this._conn?.last_success_at)}
                        </div>
                    </div>
                    <div class="diag-item">
                        <div class="diag-k">degradation</div>
                        <div class="diag-v">
                            ${brain?.degradation_level ?? (brain?.degraded ? 'degraded' : '—')}
                        </div>
                    </div>
                    <div class="diag-item">
                        <div class="diag-k">planner</div>
                        <div class="diag-v">
                            <span class="chip-gated">GATED · feature flag</span>
                        </div>
                    </div>
                </div>
                <div class="row" style="margin-top: var(--skin-space-md, 16px)">
                    <button
                        class="btn"
                        data-control="open-memory"
                        @click=${() =>
                            window.dispatchEvent(
                                new CustomEvent('soma-navigate', { detail: { route: '/memory' } }),
                            )}
                    >
                        <span class="material-symbols-outlined">folder</span>
                        Open Memory
                    </button>
                    <button
                        class="btn"
                        data-control="open-cognitive"
                        @click=${() =>
                            window.dispatchEvent(
                                new CustomEvent('soma-navigate', {
                                    detail: { route: '/cognitive' },
                                }),
                            )}
                    >
                        <span class="material-symbols-outlined">neurology</span>
                        Open Cognitive
                    </button>
                </div>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-brain-manager': SomaBrainManager;
    }
}
