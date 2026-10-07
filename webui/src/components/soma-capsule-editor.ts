/**
 * SomaAgent01 — Capsule Editor
 *
 * Edits the four PERSONALITY-category fields a capsule actually stores, via
 * `GET`/`PATCH /agents/{agent_id}/capsule` (`CapsuleConfigOut` /
 * `CapsuleConfigUpdate`). Those four are the whole capsule surface the API
 * exposes — see `admin/core/helpers/capsule_settings.py`, which classifies
 * exactly `system_prompt`, `personality_traits`, `neuromodulator_baseline`
 * and `learning_config` as PERSONALITY.
 *
 * A previous version of this component shipped five tabs (Soul, Body, Hands,
 * Memory, Governance) whose content was invented: hardcoded model names
 * ("claude-3-sonnet-20240229", "dall-e-3", "kokoro"), a recall limit of 50, a
 * similarity threshold of 0.75, a "default-constitution-v1" constitution, and
 * a green "Certified (Ed25519)" claim that nothing in this system can make.
 * None of it was stored or readable. It is gone rather than kept as decoration.
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import { workspaceStore } from '../stores/workspace-store.js';

interface CapsuleConfig {
    agent_id: string;
    capsule_id: string;
    name: string;
    description: string | null;
    status: string;
    system_prompt: string;
    personality_traits: Record<string, number>;
    neuromodulator_baseline: Record<string, number>;
    learning_config: Record<string, unknown>;
}

@customElement('soma-capsule-editor')
export class SomaCapsuleEditor extends LitElement {
    @state() private _activeTab: 'soul' | 'learning' = 'soul';
    @state() private _capsule: CapsuleConfig | null = null;
    @state() private _loading = true;
    @state() private _error: string | null = null;
    @state() private _saving = false;
    @state() private _dirty = false;
    @state() private _agentId: string | null = null;

    // Editable buffers. Start empty — they are filled from the API response,
    // never from a guess about what a capsule "should" look like.
    @state() private _systemPrompt = '';
    @state() private _personality: Record<string, number> = {};
    @state() private _neuromodulators: Record<string, number> = {};
    @state() private _learning: Record<string, unknown> = {};

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

        .capsule-name {
            font-size: 13px;
            color: var(--aaas-text-muted, #999999);
            font-weight: 400;
        }

        .tabs {
            display: flex;
            gap: 4px;
            margin-bottom: 16px;
            border-bottom: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            padding-bottom: 8px;
        }

        .tab-btn {
            background: none;
            border: none;
            color: var(--aaas-text-muted, #999);
            font-size: 12px;
            padding: 6px 12px;
            cursor: pointer;
            border-radius: 6px;
        }

        .tab-btn.active {
            background: var(--aaas-bg-surface, rgba(255,255,255,0.06));
            color: var(--aaas-text-primary, #fff);
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

        textarea {
            width: 100%;
            min-height: 120px;
            background: var(--aaas-bg-surface, rgba(255,255,255,0.04));
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.08));
            border-radius: 8px;
            color: var(--aaas-text-primary, #fff);
            font-size: 13px;
            padding: 10px;
            resize: vertical;
            font-family: inherit;
        }

        textarea:focus {
            outline: none;
            border-color: var(--aaas-accent, #3b82f6);
        }

        .slider-row {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 10px;
        }

        .slider-label {
            width: 120px;
            font-size: 12px;
            color: var(--aaas-text-muted, #999);
            text-transform: capitalize;
        }

        .slider-track {
            flex: 1;
            height: 4px;
            background: var(--aaas-border-light, rgba(255,255,255,0.08));
            border-radius: 2px;
            overflow: hidden;
        }

        .slider-fill {
            height: 100%;
            background: var(--aaas-accent, #3b82f6);
            border-radius: 2px;
        }

        .slider-value {
            width: 36px;
            text-align: right;
            font-size: 12px;
            color: var(--aaas-text-primary, #fff);
            font-variant-numeric: tabular-nums;
        }

        .neuro-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }

        .neuro-card {
            background: var(--aaas-bg-surface, rgba(255,255,255,0.04));
            border-radius: 8px;
            padding: 12px;
        }

        .neuro-name {
            font-size: 11px;
            color: var(--aaas-text-muted, #999);
            margin-bottom: 4px;
            text-transform: capitalize;
        }

        .neuro-value {
            font-size: 18px;
            font-weight: 600;
            color: var(--aaas-text-primary, #fff);
            margin-bottom: 6px;
            font-variant-numeric: tabular-nums;
        }

        .neuro-bar {
            height: 3px;
            background: var(--aaas-border-light, rgba(255,255,255,0.08));
            border-radius: 2px;
            overflow: hidden;
        }

        .neuro-fill {
            height: 100%;
            border-radius: 2px;
        }

        .actions {
            display: flex;
            gap: 8px;
            margin-top: 20px;
            padding-top: 16px;
            border-top: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
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

        .btn-danger {
            border-color: #dc2626;
            color: #dc2626;
        }

        .empty {
            padding: 24px 0;
            font-size: 13px;
            color: var(--aaas-text-muted, #999);
        }

        .learning-row {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            padding: 8px 0;
            border-bottom: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            font-size: 12px;
        }

        .learning-key {
            color: var(--aaas-text-muted, #999);
        }

        .learning-val {
            color: var(--aaas-text-primary, #fff);
            font-variant-numeric: tabular-nums;
            word-break: break-all;
            text-align: right;
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
            this._capsule = null;
            this._loading = false;
            this._error = null;
            return;
        }
        this._loading = true;
        this._error = null;
        try {
            const data = await apiClient.get<CapsuleConfig>(
                `/agents/${this._agentId}/capsule`
            );
            this._capsule = data;
            this._systemPrompt = data.system_prompt ?? '';
            this._personality = { ...(data.personality_traits ?? {}) };
            this._neuromodulators = { ...(data.neuromodulator_baseline ?? {}) };
            this._learning = { ...(data.learning_config ?? {}) };
            this._dirty = false;
        } catch (e) {
            console.error('Failed to load capsule:', e);
            this._capsule = null;
            this._error =
                e instanceof Error ? e.message : 'Failed to load capsule';
        } finally {
            this._loading = false;
        }
    }

    private async _save() {
        if (!this._agentId || !this._capsule) return;
        this._saving = true;
        try {
            await apiClient.patch(`/agents/${this._agentId}/capsule`, {
                system_prompt: this._systemPrompt,
                personality_traits: this._personality,
                neuromodulator_baseline: this._neuromodulators,
                learning_config: this._learning,
            });
            this._dirty = false;
            await this._load();
        } catch (e) {
            console.error('Failed to save capsule:', e);
            this._error =
                e instanceof Error ? e.message : 'Failed to save capsule';
        } finally {
            this._saving = false;
        }
    }

    /**
     * Soft-archive the agent. The API is `POST /agents/{agent_id}/archive`;
     * it is destructive from the operator's side, so it confirms first.
     */
    private async _archive() {
        if (!this._agentId || !this._capsule) return;
        if (!confirm(`Archive agent ${this._capsule.name}?`)) return;
        try {
            await apiClient.post(`/agents/${this._agentId}/archive`, {});
            await this._load();
        } catch (e) {
            console.error('Failed to archive agent:', e);
            this._error =
                e instanceof Error ? e.message : 'Failed to archive agent';
        }
    }

    /**
     * Download the loaded capsule as JSON. Purely client-side — it exports
     * exactly what the API returned, and makes no claim about signing or
     * certification.
     */
    private _export() {
        if (!this._capsule) return;
        const blob = new Blob([JSON.stringify(this._capsule, null, 2)], {
            type: 'application/json',
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${this._capsule.name || 'capsule'}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    render() {
        if (!this._agentId) {
            return html`<div class="empty">
                Select an agent to edit its capsule.
            </div>`;
        }
        if (this._loading) {
            return html`<div class="empty">Loading capsule...</div>`;
        }
        if (!this._capsule) {
            return html`<div class="empty">
                ${this._error ?? 'No capsule found for this agent.'}
            </div>`;
        }

        return html`
            <div class="header">
                <span>Capsule Editor</span>
                <span class="capsule-name"
                    >${this._capsule.name || this._capsule.capsule_id}</span
                >
            </div>

            <div class="tabs">
                <button
                    class="tab-btn ${this._activeTab === 'soul' ? 'active' : ''}"
                    @click=${() => (this._activeTab = 'soul')}
                >
                    Persona
                </button>
                <button
                    class="tab-btn ${this._activeTab === 'learning' ? 'active' : ''}"
                    @click=${() => (this._activeTab = 'learning')}
                >
                    Learning
                </button>
            </div>

            ${this._activeTab === 'soul' ? this._renderPersona() : ''}
            ${this._activeTab === 'learning' ? this._renderLearning() : ''}

            <div class="actions">
                <button
                    class="btn btn-primary"
                    ?disabled=${this._saving || !this._dirty}
                    @click=${() => void this._save()}
                >
                    <span class="material-symbols-outlined">save</span>
                    ${this._saving ? 'Saving...' : 'Save'}
                </button>
                <button class="btn" @click=${() => void this._load()}>
                    Cancel
                </button>
                <button class="btn" @click=${() => this._export()}>
                    <span class="material-symbols-outlined">download</span>
                    Export
                </button>
                <button class="btn btn-danger" @click=${() => void this._archive()}>
                    <span class="material-symbols-outlined">archive</span>
                    Archive
                </button>
            </div>
        `;
    }

    private _renderPersona() {
        return html`
            <div class="section">
                <div class="section-title">System Prompt</div>
                <textarea
                    .value=${this._systemPrompt}
                    @input=${(e: Event) => {
                        this._systemPrompt = (
                            e.target as HTMLTextAreaElement
                        ).value;
                        this._dirty = true;
                    }}
                ></textarea>
            </div>

            <div class="section">
                <div class="section-title">Personality Traits</div>
                ${Object.keys(this._personality).length === 0
                    ? html`<div class="empty">
                          This capsule stores no personality traits.
                      </div>`
                    : Object.entries(this._personality).map(
                          ([trait, value]) => html`
                              <div class="slider-row">
                                  <span class="slider-label">${trait}</span>
                                  <div class="slider-track">
                                      <div
                                          class="slider-fill"
                                          style="width: ${Math.max(
                                              0,
                                              Math.min(100, (value / 10) * 100)
                                          )}%"
                                      ></div>
                                  </div>
                                  <span class="slider-value"
                                      >${Number(value).toFixed(1)}</span
                                  >
                              </div>
                          `
                      )}
            </div>

            <div class="section">
                <div class="section-title">Neuromodulator Baseline</div>
                ${Object.keys(this._neuromodulators).length === 0
                    ? html`<div class="empty">
                          This capsule stores no neuromodulator baseline.
                      </div>`
                    : html`
                          <div class="neuro-grid">
                              ${Object.entries(this._neuromodulators).map(
                                  ([name, value]) => html`
                                      <div class="neuro-card">
                                          <div class="neuro-name">${name}</div>
                                          <div class="neuro-value">
                                              ${Number(value).toFixed(2)}
                                          </div>
                                          <div class="neuro-bar">
                                              <div
                                                  class="neuro-fill"
                                                  style="width: ${Math.max(
                                                      0,
                                                      Math.min(100, value * 100)
                                                  )}%; background: ${value > 0.7
                                                      ? 'var(--aaas-success, #22c55e)'
                                                      : value > 0.4
                                                        ? 'var(--aaas-warning, #f59e0b)'
                                                        : 'var(--aaas-info, #3b82f6)'}"
                                              ></div>
                                          </div>
                                      </div>
                                  `
                              )}
                          </div>
                      `}
            </div>
        `;
    }

    /**
     * `learning_config` is a free-form JSON object on the model — it has no
     * fixed schema this UI can rely on. Render whatever keys the capsule
     * actually stored; render nothing when it stores none. Inventing a
     * "Recall Limit" and "Similarity Threshold" here would put numbers on
     * screen that no endpoint reads or writes.
     */
    private _renderLearning() {
        const entries = Object.entries(this._learning);
        return html`
            <div class="section">
                <div class="section-title">Learning Config</div>
                ${entries.length === 0
                    ? html`<div class="empty">
                          This capsule stores no learning configuration.
                      </div>`
                    : entries.map(
                          ([key, value]) => html`
                              <div class="learning-row">
                                  <span class="learning-key">${key}</span>
                                  <span class="learning-val"
                                      >${typeof value === 'object'
                                          ? JSON.stringify(value)
                                          : String(value)}</span
                                  >
                              </div>
                          `
                      )}
            </div>
            ${this._error
                ? html`<div class="empty" style="color: #dc2626">
                      ${this._error}
                  </div>`
                : nothing}
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-capsule-editor': SomaCapsuleEditor;
    }
}
