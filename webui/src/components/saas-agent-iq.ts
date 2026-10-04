/**
 * AgentIQ strip — knobs, derived readouts, 5 context lanes.
 *
 * Derived settings are NEVER computed here. They come from the server
 * (`admin.core.agentiq.derivation.derive_all_settings`). Until an endpoint
 * returns them the readouts show "—", not a guess.
 *
 * The five context lanes (admin/core/context/lanes.py) are shown as the real
 * allocation buckets. Percentages only appear when the server reports them.
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { iqStore, type IQKnobs, type DerivedSettings } from '../stores/iq-store.js';

const LANES = [
    { id: 'system', label: 'System', desc: 'Base prompt' },
    { id: 'history', label: 'History', desc: 'Conversation history' },
    { id: 'memory', label: 'Memory', desc: 'SomaBrain recall' },
    { id: 'tools', label: 'Tools', desc: 'Tool descriptions' },
    { id: 'buffer', label: 'Buffer', desc: 'User message' },
] as const;

const STYLES = ['precise', 'balanced', 'creative'];

@customElement('saas-agent-iq')
export class SaasAgentIq extends LitElement {
    static styles = css`
        :host {
            display: block;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            background: var(--saas-bg-card, #fff);
            padding: 10px 16px;
            font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            color: var(--saas-text-primary, #1a1a1a);
            font-size: 12px;
        }
        * { box-sizing: border-box; }
        .row { display: flex; flex-wrap: wrap; gap: 16px; align-items: center; }
        .group { display: flex; align-items: center; gap: 8px; }
        .label { color: var(--saas-text-secondary, #666); font-size: 11px; text-transform: uppercase; letter-spacing: 0.4px; }
        .knob {
            display: flex; align-items: center; gap: 6px;
        }
        input[type="range"] { width: 90px; }
        input[type="number"] { width: 70px; padding: 4px 6px; border: 1px solid var(--saas-border-light, #ddd); border-radius: 6px; }
        select { padding: 4px 6px; border: 1px solid var(--saas-border-light, #ddd); border-radius: 6px; background: #fff; }
        .derived {
            display: flex; flex-wrap: wrap; gap: 10px;
            margin-top: 8px; padding-top: 8px;
            border-top: 1px dashed var(--saas-border-light, #e5e5e5);
        }
        .chip {
            display: inline-flex; align-items: center; gap: 4px;
            padding: 2px 8px; border-radius: 999px;
            background: var(--saas-bg-hover, #f5f5f5);
            border: 1px solid var(--saas-border-light, #e5e5e5);
            font-variant-numeric: tabular-nums;
        }
        .chip .k { color: var(--saas-text-secondary, #666); }
        .lanes {
            display: flex; flex-wrap: wrap; gap: 8px;
            margin-top: 8px; padding-top: 8px;
            border-top: 1px dashed var(--saas-border-light, #e5e5e5);
        }
        .lane {
            display: inline-flex; flex-direction: column; gap: 2px;
            padding: 4px 10px; border-radius: 8px;
            border: 1px solid var(--saas-border-light, #e5e5e5);
            background: var(--saas-bg-hover, #fafafa);
            min-width: 96px;
        }
        .lane .name { font-weight: 600; }
        .lane .desc { color: var(--saas-text-secondary, #666); font-size: 10px; }
        .lane .pct { font-variant-numeric: tabular-nums; color: var(--saas-text-secondary, #666); }
        .btn {
            padding: 4px 10px; border-radius: 6px; font-size: 11px;
            border: 1px solid var(--saas-border-light, #ddd); background: #fff; cursor: pointer;
        }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn.primary { background: #1a1a1a; color: #fff; border-color: #1a1a1a; }
        .muted { color: var(--saas-text-muted, #999); }
        .blocked {
            margin-top: 6px; color: var(--saas-text-secondary, #666);
            font-size: 11px;
        }
    `;

    @state() private _knobs = iqStore.knobs;
    @state() private _derived = iqStore.derived;
    @state() private _dirty = iqStore.dirty;
    @state() private _busy = false;
    @state() private _message = '';

    connectedCallback() {
        super.connectedCallback();
        iqStore.subscribe(() => {
            this._knobs = iqStore.knobs;
            this._derived = iqStore.derived;
            this._dirty = iqStore.dirty;
        });
    }

    private _setKnob(key: keyof IQKnobs, value: number | string) {
        iqStore.setKnob(key, value as never);
    }

    private async _save() {
        this._busy = true;
        this._message = '';
        try {
            // No HTTP endpoint exposes Capsule.persona_config.knobs on this
            // deployment. Saving would be a lie, so the control stays disabled
            // until one exists. See the blocked note below.
            this._message = 'Knob persistence has no API endpoint on this deployment.';
        } finally {
            this._busy = false;
        }
    }

    private _reset() {
        iqStore.resetToSaved();
        this._message = 'Reverted to the last saved knobs.';
    }

    private _chip(key: string, value: string | number | boolean | null | undefined) {
        return html`<span class="chip"><span class="k">${key}</span><span>${value === undefined || value === null ? '—' : String(value)}</span></span>`;
    }

    render() {
        const knobs = this._knobs;
        const d = this._derived;
        return html`
            <div class="row">
                <div class="group">
                    <span class="label">AgentIQ</span>
                </div>

                ${knobs ? html`
                    <div class="knob">
                        <span class="muted">IQ</span>
                        <input type="range" min="1" max="10" step="1"
                            .value=${String(knobs.intelligence_level)}
                            @input=${(e: Event) => this._setKnob('intelligence_level', Number((e.target as HTMLInputElement).value))}>
                        <strong>${knobs.intelligence_level}</strong>
                    </div>
                    <div class="knob">
                        <span class="muted">AUTO</span>
                        <input type="range" min="1" max="10" step="1"
                            .value=${String(knobs.autonomy_level)}
                            @input=${(e: Event) => this._setKnob('autonomy_level', Number((e.target as HTMLInputElement).value))}>
                        <strong>${knobs.autonomy_level}</strong>
                    </div>
                    <div class="knob">
                        <span class="muted">BUDGET</span>
                        <input type="number" min="0.01" max="1" step="0.01"
                            .value=${String(knobs.resource_budget)}
                            @change=${(e: Event) => this._setKnob('resource_budget', Number((e.target as HTMLInputElement).value))}>
                    </div>
                    <div class="knob">
                        <span class="muted">STYLE</span>
                        <select
                            .value=${knobs.response_style}
                            @change=${(e: Event) => this._setKnob('response_style', (e.target as HTMLSelectElement).value)}
                        >
                            ${STYLES.map(s => html`<option value=${s} ?selected=${knobs.response_style === s}>${s}</option>`)}
                        </select>
                    </div>
                    <button class="btn" ?disabled=${!this._dirty} @click=${this._reset}>Reset to saved</button>
                    <button class="btn primary" ?disabled=${true} title="No API endpoint writes Capsule.persona_config.knobs">Save</button>
                ` : html`<span class="muted">Knobs not loaded.</span>`}

                ${this._message ? html`<span class="muted">${this._message}</span>` : nothing}
            </div>

            <div class="blocked">
                Knob writes are blocked: this deployment exposes no HTTP endpoint for
                <code>Capsule.persona_config.knobs</code>. Derived settings below are
                whatever the server computed — never recomputed in the browser.
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

            <div class="lanes" title="5-lane context builder (admin/core/context/lanes.py)">
                ${LANES.map(l => html`
                    <div class="lane">
                        <span class="name">${l.label}</span>
                        <span class="desc">${l.desc}</span>
                        <span class="pct">share set by the governor</span>
                    </div>
                `)}
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-agent-iq': SaasAgentIq;
    }
}
