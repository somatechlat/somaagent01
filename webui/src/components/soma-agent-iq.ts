/**
 * AgentIQ strip — knobs, derived readouts, 5 context lanes.
 *
 * Derived settings are NEVER computed here. They come from the server
 * (`GET /api/v2/core/agentiq/{capsule_id}` → `admin.core.agentiq.derivation`).
 * Until the server returns them the readouts show "—", not a guess.
 *
 * Knob writes go to `PUT /api/v2/core/agentiq/{capsule_id}`, which persists
 * `Capsule.persona_config.knobs` and returns freshly derived settings.
 *
 * The five context lanes (admin/core/context/lanes.py) are shown as the real
 * allocation buckets. Percentages only appear when the server reports them.
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import { iqStore, type IQKnobs, type DerivedSettings } from '../stores/iq-store.js';

const LANES = [
    { id: 'system', label: 'System', desc: 'Base prompt', color: '#60A5FA' },
    { id: 'history', label: 'History', desc: 'Conversation history', color: '#34D399' },
    { id: 'memory', label: 'Memory', desc: 'SomaBrain recall', color: '#FF4D00' },
    { id: 'tools', label: 'Tools', desc: 'Tool descriptions', color: '#A78BFA' },
    { id: 'buffer', label: 'Buffer', desc: 'User message', color: '#FBBF24' },
] as const;

interface AgentIQPayload {
    capsule_id: string;
    knobs: Record<string, unknown>;
    derived: Record<string, unknown>;
    response_styles: string[];
    lanes?: Record<string, number>;
}

@customElement('soma-agent-iq')
export class SomaAgentIq extends LitElement {
    static styles = css`
        :host {
            display: block;
            background: transparent;
            color: #E5E5E5;
            font-family: var(--soma-font, 'Inter', -apple-system, BlinkMacSystemFont, sans-serif);
            font-size: 13px;
        }

        * {
            box-sizing: border-box;
        }

        .iq-shell {
            display: grid;
            gap: 12px;
        }

        /* ── knobs ─────────────────────────────────────────── */
        .knobs {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 8px;
        }

        @media (max-width: 820px) {
            .knobs {
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 6px;
            }
        }

        .knob-card {
            position: relative;
            padding: 10px 12px 10px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            background: linear-gradient(160deg, rgba(18, 18, 18, 0.88), rgba(10, 10, 10, 0.92));
            box-shadow:
                0 1px 0 rgba(255, 255, 255, 0.05) inset,
                0 12px 28px rgba(0, 0, 0, 0.28);
            overflow: hidden;
        }

        .knob-card::before {
            content: '';
            position: absolute;
            inset: 0 0 auto 0;
            height: 2px;
            background: linear-gradient(90deg, #FF4D00, #FF7A3D);
            opacity: 0.85;
        }

        .knob-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 6px;
            margin-bottom: 8px;
        }

        .knob-name {
            font-size: 9px;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: #FF7A3D;
        }

        .knob-value {
            font-size: 15px;
            font-weight: 650;
            color: #FFFFFF;
            font-variant-numeric: tabular-nums;
            line-height: 1;
        }

        .knob-help {
            margin-top: 6px;
            font-size: 9.5px;
            color: #7C8797;
            line-height: 1.3;
        }

        input[type='range'] {
            -webkit-appearance: none;
            appearance: none;
            width: 100%;
            height: 4px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.1);
            outline: none;
        }

        input[type='range']::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 13px;
            height: 13px;
            border-radius: 50%;
            background: linear-gradient(145deg, #FF7A3D, #FF4D00);
            border: 2px solid #0A0A0A;
            box-shadow: 0 2px 10px rgba(255, 77, 0, 0.45);
            cursor: pointer;
        }

        input[type='number'],
        select {
            width: 100%;
            padding: 6px 8px;
            border-radius: 8px;
            font-size: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            background: rgba(10, 10, 10, 0.8);
            color: #FFFFFF;
            font-size: 13px;
        }

        input[type='number']:focus,
        select:focus {
            outline: 2px solid rgba(255, 77, 0, 0.55);
            outline-offset: 1px;
        }

        /* ── section heads ─────────────────────────────────── */
        .sec {
            display: grid;
            gap: 10px;
        }

        .sec-head {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .sec-title {
            font-size: 10px;
            font-weight: 650;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: #94A3B8;
        }

        .sec-line {
            flex: 1;
            height: 1px;
            background: linear-gradient(90deg, rgba(255, 77, 0, 0.35), transparent);
        }

        /* ── derived chips ─────────────────────────────────── */
        .derived {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .chip {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 4px 8px;
            border-radius: 999px;
            background: rgba(18, 18, 18, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.08);
            font-variant-numeric: tabular-nums;
        }

        .chip .k {
            font-size: 10px;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            color: #94A3B8;
        }

        .chip .v {
            color: #FFD0BA;
            font-size: 11px;
            font-weight: 560;
        }

        /* ── lanes ─────────────────────────────────────────── */
        .lanes {
            display: grid;
            gap: 8px;
        }

        .lane {
            display: grid;
            grid-template-columns: 58px 1fr 36px;
            gap: 8px;
            align-items: center;
        }

        .lane-dot {
            display: inline-block;
            width: 7px;
            height: 7px;
            border-radius: 999px;
            margin-right: 5px;
            vertical-align: middle;
        }

        .lane .name {
            font-size: 10px;
            color: #C4C4C4;
            font-weight: 550;
        }

        .lane .desc {
            display: none;
        }

        .lane-track {
            height: 8px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.06);
            overflow: hidden;
        }

        .lane-fill {
            height: 100%;
            border-radius: inherit;
            transition: width 220ms cubic-bezier(0.2, 0.8, 0.2, 1);
        }

        .lane .pct {
            font-size: 11px;
            color: #94A3B8;
            font-variant-numeric: tabular-nums;
            text-align: right;
        }

        /* ── actions ───────────────────────────────────────── */
        .actions {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 10px;
        }

        .btn {
            border: 1px solid rgba(255, 255, 255, 0.12);
            background: rgba(18, 18, 18, 0.85);
            color: #E5E5E5;
            border-radius: 10px;
            padding: 7px 12px;
            font-size: 11px;
            cursor: pointer;
            transition: transform 120ms ease, background 120ms ease, border-color 120ms ease;
        }

        .btn:hover {
            transform: translateY(-1px);
            border-color: rgba(255, 77, 0, 0.4);
        }

        .btn:disabled {
            opacity: 0.45;
            cursor: not-allowed;
            transform: none;
        }

        .btn.primary {
            border: 0;
            background: linear-gradient(135deg, #FF4D00, #E64500);
            color: #FFFFFF;
            box-shadow: 0 10px 24px rgba(255, 77, 0, 0.28);
            font-weight: 600;
        }

        .btn.primary:hover {
            box-shadow: 0 14px 30px rgba(255, 77, 0, 0.36);
        }

        .muted {
            color: #94A3B8;
            font-size: 11.5px;
        }

        .blocked {
            margin-top: 2px;
            color: #64748B;
            font-size: 10.5px;
            line-height: 1.45;
        }

        .blocked code {
            color: #FFB088;
            font-family: var(--soma-font-mono, ui-monospace, monospace);
            font-size: 10px;
        }
    `;

    /** Capsule whose persona_config.knobs this strip edits. */
    @property({ type: String, attribute: 'capsule-id' }) capsuleId = '';

    @state() private _knobs = iqStore.knobs;
    @state() private _derived = iqStore.derived;
    @state() private _dirty = iqStore.dirty;
    @state() private _busy = false;
    @state() private _message = '';
    /** Allowed response_style values, from the server lookup table. */
    @state() private _styles: string[] = [];
    /** Lane allocation shares from `admin.core.context.lanes` via AgentIQ GET. */
    @state() private _lanes: Record<string, number> | null = null;

    private _unsubscribe: (() => void) | null = null;

    connectedCallback() {
        super.connectedCallback();
        this._unsubscribe = iqStore.subscribe(() => {
            this._knobs = iqStore.knobs;
            this._derived = iqStore.derived;
            this._dirty = iqStore.dirty;
        });
        if (this.capsuleId) {
            void this._load();
        }
    }

    disconnectedCallback() {
        this._unsubscribe?.();
        this._unsubscribe = null;
        super.disconnectedCallback();
    }

    override updated(changed: Map<string, unknown>) {
        if (changed.has('capsuleId') && this.capsuleId) {
            void this._load();
        }
    }

    private async _load() {
        if (!this.capsuleId) {
            this._message = 'No capsule selected — knobs are not loaded.';
            return;
        }
        this._busy = true;
        this._message = '';
        try {
            const payload = await apiClient.get<AgentIQPayload>(
                `/core/agentiq/${this.capsuleId}`
            );
            this._styles = payload.response_styles ?? [];
            this._lanes = payload.lanes ?? null;
            iqStore.setFromServer(
                payload.knobs as never,
                payload.derived as never
            );
            iqStore.markSaved();
            this._message = '';
        } catch (error) {
            this._message = `Failed to load AgentIQ: ${error instanceof Error ? error.message : error}`;
        } finally {
            this._busy = false;
        }
    }

    private _setKnob(key: keyof IQKnobs, value: number | string) {
        iqStore.setKnob(key, value as never);
    }

    private async _save() {
        if (!this.capsuleId) {
            this._message = 'No capsule selected — cannot save knobs.';
            return;
        }
        const knobs = iqStore.knobs;
        if (!knobs) {
            this._message = 'Knobs are not loaded.';
            return;
        }
        this._busy = true;
        this._message = '';
        try {
            const payload = await apiClient.put<AgentIQPayload>(
                `/core/agentiq/${this.capsuleId}`,
                {
                    intelligence_level: knobs.intelligence_level,
                    autonomy_level: knobs.autonomy_level,
                    resource_budget: knobs.resource_budget,
                    response_style: knobs.response_style,
                }
            );
            this._styles = payload.response_styles ?? this._styles;
            this._lanes = payload.lanes ?? this._lanes;
            iqStore.setFromServer(payload.knobs as never, payload.derived as never);
            iqStore.markSaved();
            this._message = 'Knobs saved. Derived settings recomputed by the server.';
        } catch (error) {
            this._message = `Failed to save knobs: ${error instanceof Error ? error.message : error}`;
        } finally {
            this._busy = false;
        }
    }

    private _reset() {
        iqStore.resetToSaved();
        this._message = 'Reverted to the last saved knobs.';
    }

    private _chip(key: string, value: string | number | boolean | null | undefined) {
        return html`
            <span class="chip">
                <span class="k">${key}</span>
                <span class="v">${value === undefined || value === null ? '—' : String(value)}</span>
            </span>
        `;
    }

    render() {
        const knobs = this._knobs;
        const d = this._derived;
        return html`
            <div class="iq-shell">
                ${knobs
                    ? html`
                          <div class="knobs">
                              <div class="knob-card">
                                  <div class="knob-top">
                                      <span class="knob-name">IQ</span>
                                      <span class="knob-value">${knobs.intelligence_level}</span>
                                  </div>
                                  <input
                                      type="range"
                                      min="1"
                                      max="10"
                                      step="1"
                                      .value=${String(knobs.intelligence_level)}
                                      @input=${(e: Event) =>
                                          this._setKnob(
                                              'intelligence_level',
                                              Number((e.target as HTMLInputElement).value),
                                          )}
                                  />
                                  <div class="knob-help">How sharp the model thinks · 1–10</div>
                              </div>

                              <div class="knob-card">
                                  <div class="knob-top">
                                      <span class="knob-name">AUTO</span>
                                      <span class="knob-value">${knobs.autonomy_level}</span>
                                  </div>
                                  <input
                                      type="range"
                                      min="1"
                                      max="10"
                                      step="1"
                                      .value=${String(knobs.autonomy_level)}
                                      @input=${(e: Event) =>
                                          this._setKnob(
                                              'autonomy_level',
                                              Number((e.target as HTMLInputElement).value),
                                          )}
                                  />
                                  <div class="knob-help">Guided ←→ free to act · 1–10</div>
                              </div>

                              <div class="knob-card">
                                  <div class="knob-top">
                                      <span class="knob-name">BUDGET</span>
                                      <span class="knob-value">${knobs.resource_budget}</span>
                                  </div>
                                  <input
                                      type="number"
                                      min="0.01"
                                      max="1"
                                      step="0.01"
                                      .value=${String(knobs.resource_budget)}
                                      @change=${(e: Event) =>
                                          this._setKnob(
                                              'resource_budget',
                                              Number((e.target as HTMLInputElement).value),
                                          )}
                                  />
                                  <div class="knob-help">Effort / cost share · 0.01–1</div>
                              </div>

                              <div class="knob-card">
                                  <div class="knob-top">
                                      <span class="knob-name">STYLE</span>
                                      <span class="knob-value" style="font-size:12px">${knobs.response_style}</span>
                                  </div>
                                  <select
                                      .value=${knobs.response_style}
                                      @change=${(e: Event) =>
                                          this._setKnob(
                                              'response_style',
                                              (e.target as HTMLSelectElement).value,
                                          )}
                                  >
                                      ${(this._styles.length ? this._styles : [knobs.response_style]).map(
                                          (s) =>
                                              html`<option value=${s} ?selected=${knobs.response_style === s}>
                                                  ${s}
                                              </option>`,
                                      )}
                                  </select>
                                  <div class="knob-help">Tone of replies</div>
                              </div>
                          </div>
                      `
                    : html`<div class="muted">
                          ${this.capsuleId ? 'Loading knobs…' : 'No capsule selected — open a chat with an agent.'}
                      </div>`}

                <div class="sec">
                    <div class="sec-head">
                        <span class="sec-title">Derived · server</span>
                        <span class="sec-line"></span>
                    </div>
                    <div class="derived">
                        ${this._chip('temperature', d?.temperature)}
                        ${this._chip('max_tokens', d?.max_tokens)}
                        ${this._chip('model_tier', d?.model_tier)}
                        ${this._chip('tool_approval', d?.tool_approval)}
                        ${this._chip('require_hitl', d?.require_hitl)}
                        ${this._chip('egress', d?.egress_allowed)}
                        ${this._chip('recall_limit', d?.recall_limit)}
                        ${this._chip('brain_query', d?.brain_query_enabled)}
                        ${this._chip('token_limit', d?.token_limit)}
                        ${this._chip('style', d?.response_style)}
                    </div>
                </div>

                <div class="sec">
                    <div class="sec-head">
                        <span class="sec-title">Context lanes</span>
                        <span class="sec-line"></span>
                    </div>
                    <div class="lanes" title="5-lane context builder (admin/core/context/lanes.py)">
                        ${LANES.map((l) => {
                            const raw = this._lanes && typeof this._lanes[l.id] === 'number' ? this._lanes[l.id] : null;
                            const pct = raw === null ? 0 : raw <= 1 ? raw * 100 : raw;
                            return html`
                                <div class="lane">
                                    <span class="name"><i class="lane-dot" style="background:${l.color}"></i>${l.label}</span>
                                    <span class="lane-track">
                                        <span
                                            class="lane-fill"
                                            style="width:${Math.max(0, Math.min(100, pct))}%;background:linear-gradient(90deg, ${l.color}, ${l.color}CC);box-shadow:0 0 8px ${l.color}55"
                                        ></span>
                                    </span>
                                    <span class="pct">${raw === null ? '—' : `${pct.toFixed(0)}%`}</span>
                                </div>
                            `;
                        })}
                    </div>
                </div>

                <div class="actions">
                    <button class="btn" ?disabled=${!this._dirty || this._busy} @click=${this._reset}>
                        Reset to saved
                    </button>
                    <button
                        class="btn primary"
                        data-control="save-iq"
                        ?disabled=${!this._dirty || this._busy || !this.capsuleId}
                        title=${this.capsuleId
                            ? 'Persist knobs on the Capsule and recompute derived settings'
                            : 'No capsule selected'}
                        @click=${this._save}
                    >
                        Save
                    </button>
                    ${this._message ? html`<span class="muted">${this._message}</span>` : nothing}
                </div>

                <div class="blocked">
                    Knobs persist to <code>Capsule.persona_config.knobs</code> via
                    <code>PUT /api/v2/core/agentiq/{capsule_id}</code>. Derived values are computed by the
                    server only.
                </div>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-agent-iq': SomaAgentIq;
    }
}
