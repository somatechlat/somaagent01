/**
 * SomaAgent01 — SomaBrain Cognitive Panel
 *
 * Shows the live cognitive state of the selected agent and can trigger a
 * sleep cycle. Everything on screen comes from the API — there are no
 * defaults, thresholds or status labels baked into this file.
 *
 * Sources (see `admin/somabrain/cognitive.py`, `core_brain.py`):
 *   GET  /somabrain/status/{agent_id}       → neuromodulators, memory_stats,
 *                                             adaptation_params, is_sleeping,
 *                                             degradation_level
 *   GET  /somabrain/sleep/status/{agent_id} → is_sleeping, last_sleep,
 *                                             next_scheduled
 *   POST /somabrain/sleep/{agent_id}        → run a consolidation cycle
 *
 * Removed rather than kept as decoration:
 *   - "Force Wake". `GET /somabrain/wake/{agent_id}` answers 501
 *     ("SomaBrainClient has no wake endpoint"), so the button could only
 *     ever fail.
 *   - The "Memory Config" section (Retention days / Archival days / Snapshot
 *     hours). No endpoint reads or writes those keys; the 30 / 365 / 24
 *     shown previously were literals in this file, not configuration.
 *   - Per-neuromodulator status words ("active", "stable", "alert",
 *     "focused"). They came from thresholds like `> 0.5` that this file
 *     invented. The value is the measurement; the label was not.
 *   - A hardcoded "Connected" badge. Connection state is `degraded` from
 *     the API, not a constant.
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import { workspaceStore } from '../stores/workspace-store.js';

interface BrainStatus {
    agent_id: string;
    status: string;
    is_sleeping: boolean;
    neuromodulators: Record<string, number>;
    memory_stats: Record<string, unknown>;
    adaptation_params: Record<string, unknown>;
    last_activity: string | null;
    degradation_level: string;
    degraded: boolean;
}

interface SleepStatus {
    agent_id: string;
    is_sleeping: boolean;
    last_sleep: string | null;
    next_scheduled: string | null;
    degraded: boolean;
}

@customElement('saas-brain-panel')
export class SaasBrainPanel extends LitElement {
    @state() private _agentId: string | null = null;
    @state() private _brain: BrainStatus | null = null;
    @state() private _sleep: SleepStatus | null = null;
    @state() private _loading = true;
    @state() private _error: string | null = null;
    @state() private _sleeping = false;
    /** Minutes requested for the next sleep cycle. Left empty until typed. */
    @state() private _sleepMinutes: string = '';

    private _unsubscribe: (() => void) | null = null;

    static styles = css`
        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: 20px;
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            -webkit-font-feature-settings: 'liga';
            -webkit-font-smoothing: antialiased;
        }
        :host {
            display: block;
        }

        .header {
            font-size: 14px;
            font-weight: 600;
            color: var(--aaas-text-primary, #ffffff);
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .connection-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            font-weight: 500;
            color: var(--aaas-text-muted, #999);
        }

        .dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--aaas-text-muted, #999);
        }

        .dot.ok {
            background: var(--aaas-success, #22c55e);
        }

        .dot.warn {
            background: var(--aaas-warning, #f59e0b);
        }

        .section {
            margin-bottom: 20px;
        }

        .section-title {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--aaas-text-muted, #999);
            margin-bottom: 10px;
        }

        .stat-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
        }

        .stat-label {
            font-size: 12px;
            color: var(--aaas-text-muted, #999);
        }

        .stat-value {
            font-size: 12px;
            color: var(--aaas-text-primary, #fff);
            font-variant-numeric: tabular-nums;
            text-align: right;
            word-break: break-all;
        }

        .empty {
            padding: 24px 0;
            font-size: 13px;
            color: var(--aaas-text-muted, #999);
        }

        .error {
            padding: 12px;
            border-radius: 8px;
            background: rgba(220, 38, 38, 0.12);
            color: #f87171;
            font-size: 12px;
            margin-bottom: 12px;
        }

        .field {
            margin-bottom: 12px;
        }

        .field-label {
            display: block;
            font-size: 11px;
            color: var(--aaas-text-muted, #999);
            margin-bottom: 4px;
        }

        .field-input {
            width: 100%;
            background: var(--aaas-bg-surface, rgba(255,255,255,0.04));
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.08));
            border-radius: 8px;
            color: var(--aaas-text-primary, #fff);
            font-size: 13px;
            padding: 8px 10px;
        }

        .field-input:focus {
            outline: none;
            border-color: var(--aaas-accent, #3b82f6);
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 14px;
            border-radius: 8px;
            font-size: 12px;
            cursor: pointer;
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.12));
            background: transparent;
            color: var(--aaas-text-primary, #fff);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .btn-primary {
            background: var(--aaas-accent, #3b82f6);
            border-color: var(--aaas-accent, #3b82f6);
            color: #fff;
        }
    `;

    connectedCallback() {
        super.connectedCallback();
        this._unsubscribe = workspaceStore.subscribe(() => {
            const next = workspaceStore.state.activeAgentId;
            if (next !== this._agentId) {
                this._agentId = next;
                void this._load();
            }
        });
        this._agentId = workspaceStore.state.activeAgentId;
        void this._load();
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this._unsubscribe?.();
        this._unsubscribe = null;
    }

    private async _load() {
        if (!this._agentId) {
            this._brain = null;
            this._sleep = null;
            this._loading = false;
            this._error = null;
            return;
        }
        this._loading = true;
        this._error = null;
        try {
            const [brain, sleep] = await Promise.all([
                apiClient.get<BrainStatus>(`/somabrain/status/${this._agentId}`),
                apiClient.get<SleepStatus>(
                    `/somabrain/sleep/status/${this._agentId}`
                ),
            ]);
            this._brain = brain;
            this._sleep = sleep;
        } catch (e) {
            console.error('Failed to load brain state:', e);
            this._brain = null;
            this._sleep = null;
            this._error =
                e instanceof Error ? e.message : 'Failed to load brain state';
        } finally {
            this._loading = false;
        }
    }

    /**
     * Run a consolidation cycle. `duration_minutes` is sent only when the
     * operator set one — otherwise the API's own default applies, rather
     * than this file quietly choosing a number on their behalf.
     */
    private async _triggerSleep() {
        if (!this._agentId) return;
        this._sleeping = true;
        try {
            const body: {
                duration_minutes?: number;
            } = {};
            const minutes = Number(this._sleepMinutes);
            if (this._sleepMinutes !== '' && Number.isFinite(minutes) && minutes > 0) {
                body.duration_minutes = minutes;
            }
            await apiClient.post(`/somabrain/sleep/${this._agentId}`, body);
            await this._load();
        } catch (e) {
            console.error('Failed to trigger sleep:', e);
            this._error =
                e instanceof Error ? e.message : 'Failed to trigger sleep';
        } finally {
            this._sleeping = false;
        }
    }

    render() {
        if (!this._agentId) {
            return html`<div class="empty">
                Select an agent to view its cognitive state.
            </div>`;
        }
        if (this._loading) {
            return html`<div class="empty">Loading cognitive state...</div>`;
        }

        const brain = this._brain;

        return html`
            <div class="header">
                <span>SomaBrain</span>
                <span class="connection-badge">
                    <span
                        class="dot ${brain && !brain.degraded
                            ? 'ok'
                            : brain
                              ? 'warn'
                              : ''}"
                    ></span>
                    ${!brain
                        ? 'Unavailable'
                        : brain.degraded
                          ? `Degraded (${brain.degradation_level})`
                          : brain.status}
                </span>
            </div>

            ${this._error ? html`<div class="error">${this._error}</div>` : nothing}
            ${!brain
                ? html`<div class="empty">
                      No cognitive state available for this agent.
                  </div>`
                : html`
                      <div class="section">
                          <div class="section-title">Cognitive State</div>
                          ${Object.entries(brain.neuromodulators ?? {}).length ===
                          0
                              ? html`<div class="empty">
                                    No neuromodulator readings reported.
                                </div>`
                              : Object.entries(
                                    brain.neuromodulators ?? {}
                                ).map(
                                    ([name, value]) => html`
                                        <div class="stat-row">
                                            <span class="stat-label"
                                                >${name}</span
                                            >
                                            <span class="stat-value"
                                                >${Number(value).toFixed(4)}</span
                                            >
                                        </div>
                                    `
                                )}
                      </div>

                      <div class="section">
                          <div class="section-title">Memory</div>
                          ${Object.entries(brain.memory_stats ?? {}).length ===
                          0
                              ? html`<div class="empty">
                                    No memory statistics reported.
                                </div>`
                              : Object.entries(brain.memory_stats ?? {}).map(
                                    ([k, v]) => html`
                                        <div class="stat-row">
                                            <span class="stat-label">${k}</span>
                                            <span class="stat-value"
                                                >${typeof v === 'object'
                                                    ? JSON.stringify(v)
                                                    : String(v)}</span
                                            >
                                        </div>
                                    `
                                )}
                      </div>

                      <div class="section">
                          <div class="section-title">Adaptation</div>
                          ${Object.entries(brain.adaptation_params ?? {})
                              .length === 0
                              ? html`<div class="empty">
                                    No adaptation parameters reported.
                                </div>`
                              : Object.entries(
                                    brain.adaptation_params ?? {}
                                ).map(
                                    ([k, v]) => html`
                                        <div class="stat-row">
                                            <span class="stat-label">${k}</span>
                                            <span class="stat-value"
                                                >${typeof v === 'object'
                                                    ? JSON.stringify(v)
                                                    : String(v)}</span
                                            >
                                        </div>
                                    `
                                )}
                      </div>
                  `}

            <div class="section">
                <div class="section-title">Sleep Cycle</div>
                ${this._sleep
                    ? html`
                          <div class="stat-row">
                              <span class="stat-label">Status</span>
                              <span class="stat-value"
                                  >${this._sleep.is_sleeping
                                      ? 'Sleeping'
                                      : 'Awake'}</span
                              >
                          </div>
                          <div class="stat-row">
                              <span class="stat-label">Last Sleep</span>
                              <span class="stat-value"
                                  >${this._sleep.last_sleep
                                      ? new Date(
                                            this._sleep.last_sleep
                                        ).toLocaleString()
                                      : '—'}</span
                              >
                          </div>
                          <div class="stat-row">
                              <span class="stat-label">Next Scheduled</span>
                              <span class="stat-value"
                                  >${this._sleep.next_scheduled
                                      ? new Date(
                                            this._sleep.next_scheduled
                                        ).toLocaleString()
                                      : '—'}</span
                              >
                          </div>
                      `
                    : html`<div class="empty">No sleep status available.</div>`}

                <div class="field" style="margin-top:12px;">
                    <label class="field-label"
                        >Duration (minutes) — leave empty to use the server
                        default</label
                    >
                    <input
                        class="field-input"
                        type="number"
                        min="1"
                        .value=${this._sleepMinutes}
                        @input=${(e: Event) =>
                            (this._sleepMinutes = (
                                e.target as HTMLInputElement
                            ).value)}
                    />
                </div>
                <button
                    class="btn btn-primary"
                    ?disabled=${this._sleeping || !this._agentId}
                    @click=${() => void this._triggerSleep()}
                >
                    <span class="material-symbols-outlined">bedtime</span>
                    ${this._sleeping ? 'Running...' : 'Trigger Sleep'}
                </button>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-brain-panel': SaasBrainPanel;
    }
}
