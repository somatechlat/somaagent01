/**
 * Chat settings modal — CS-01..CS-30 (glass).
 *
 * Contract (plan §0.6): props `open`, `value ChatPrefs` · events `save`,
 * `reset`, `close`. Save persists via chat-prefs (localStorage) and
 * broadcasts window event `soma-chat-prefs` so open chat re-renders live.
 *
 * Persistence honesty: the server user-preferences route is not wired.
 * Save writes local storage and the status line states that truthfully —
 * it never claims a remote save that did not happen.
 *
 * All visual styling uses `--skin-*` tokens only (Skin SDK vocabulary).
 */

import { LitElement, html, css, nothing, PropertyValues } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import {
    BUBBLE_STYLE_OPTIONS,
    DEFAULT_CHAT_PREFS,
    DENSITY_OPTIONS,
    FONT_SIZE_OPTIONS,
    MAX_REASONING_LINES,
    MIN_REASONING_LINES,
    REASONING_STYLE_OPTIONS,
    REASONING_VISIBILITY_OPTIONS,
    TOOL_ARGS_OPTIONS,
    TOOL_ICON_KEYS,
    TOOL_ICON_LABELS,
    type ChatPrefs,
    type ToolIconKey,
    emitChatPrefs,
    loadChatPrefs,
    normalizeChatPrefs,
    saveChatPrefs,
} from '../services/chat-prefs.js';
import './soma-glass-modal.js';

type SaveStatus = 'idle' | 'saved' | 'error';

function titleCase(v: string): string {
    return v
        .split(/[_\s-]+/)
        .map((p) => (p.length ? p[0].toUpperCase() + p.slice(1) : p))
        .join(' ');
}

@customElement('soma-chat-settings')
export class SomaChatSettings extends LitElement {
    @property({ type: Boolean, reflect: true }) open = false;
    /** Controlled prefs. When null, the modal seeds from localStorage. */
    @property({ type: Object }) value: ChatPrefs | null = null;

    @state() private _draft: ChatPrefs = normalizeChatPrefs(null);
    @state() private _status: SaveStatus = 'idle';
    @state() private _statusDetail = '';

    static styles = css`
        :host {
            display: contents;
            font-family: var(--skin-font-sans);
        }

        .form {
            display: flex;
            flex-direction: column;
            gap: var(--skin-space-lg);
            color: var(--skin-color-text-primary);
        }

        .section {
            display: flex;
            flex-direction: column;
            gap: var(--skin-space-md);
        }

        .section-title {
            margin: 0;
            font-size: var(--skin-text-xs);
            font-weight: var(--skin-weight-semibold);
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--skin-color-text-muted);
            border-bottom: 1px solid var(--skin-color-border-subtle);
            padding-bottom: var(--skin-space-xs);
        }

        .row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: var(--skin-space-md);
        }

        @media (max-width: 640px) {
            .row {
                grid-template-columns: 1fr;
            }
        }

        .field {
            display: flex;
            flex-direction: column;
            gap: var(--skin-space-xs);
            min-width: 0;
        }

        .field-label {
            font-size: var(--skin-text-sm);
            font-weight: var(--skin-weight-medium);
            color: var(--skin-color-text-secondary);
        }

        .field-id {
            color: var(--skin-color-text-muted);
            font-family: var(--skin-font-mono);
            font-size: var(--skin-text-xs);
            margin-left: var(--skin-space-xs);
        }

        select,
        input[type='number'] {
            appearance: none;
            width: 100%;
            box-sizing: border-box;
            padding: var(--skin-space-sm) var(--skin-space-md);
            font-family: var(--skin-font-sans);
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-primary);
            background: var(--skin-color-bg-base);
            border: 1px solid var(--skin-color-border);
            border-radius: var(--skin-radius-md);
        }

        select:focus-visible,
        input[type='number']:focus-visible,
        .check:focus-visible,
        .chip:focus-visible,
        .btn:focus-visible,
        .step-btn:focus-visible {
            outline: var(--skin-focus-ring-width) solid var(--skin-focus-ring);
            outline-offset: var(--skin-focus-ring-offset);
        }

        .toggle-row {
            display: flex;
            align-items: center;
            gap: var(--skin-space-sm);
            min-height: 32px;
            cursor: pointer;
            user-select: none;
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-primary);
        }

        .toggle-row input {
            width: 16px;
            height: 16px;
            accent-color: var(--skin-color-accent);
            cursor: pointer;
        }

        .checks {
            display: flex;
            flex-wrap: wrap;
            gap: var(--skin-space-sm);
        }

        .chip {
            display: inline-flex;
            align-items: center;
            gap: var(--skin-space-xs);
            padding: var(--skin-space-xs) var(--skin-space-sm);
            border: 1px solid var(--skin-color-border);
            border-radius: var(--skin-radius-full);
            background: var(--skin-color-bg-base);
            color: var(--skin-color-text-secondary);
            font-family: var(--skin-font-mono);
            font-size: var(--skin-text-xs);
            cursor: pointer;
        }

        .chip[data-on='true'] {
            border-color: var(--skin-color-accent);
            background: var(--skin-color-bg-active);
            color: var(--skin-color-text-primary);
        }

        .chip input {
            accent-color: var(--skin-color-accent);
            margin: 0;
        }

        .stepper {
            display: inline-flex;
            align-items: center;
            gap: var(--skin-space-sm);
        }

        .stepper input[type='number'] {
            width: 5.5rem;
            text-align: center;
        }

        .step-btn {
            width: 32px;
            height: 32px;
            border-radius: var(--skin-radius-md);
            border: 1px solid var(--skin-color-border);
            background: var(--skin-color-bg-hover);
            color: var(--skin-color-text-primary);
            font-family: var(--skin-font-sans);
            font-size: var(--skin-text-base);
            cursor: pointer;
        }

        .step-btn:hover {
            background: var(--skin-color-bg-active);
        }

        .step-btn:disabled {
            opacity: 0.45;
            cursor: not-allowed;
        }

        .actions {
            display: flex;
            flex-wrap: wrap;
            gap: var(--skin-space-sm);
            justify-content: flex-end;
            align-items: center;
            padding-top: var(--skin-space-sm);
            border-top: 1px solid var(--skin-color-border-subtle);
        }

        .status {
            flex: 1 1 auto;
            min-width: 12rem;
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-muted);
        }

        .status[data-kind='saved'] {
            color: var(--skin-color-success);
        }

        .status[data-kind='error'] {
            color: var(--skin-color-danger);
        }

        .btn {
            border-radius: var(--skin-radius-md);
            border: 1px solid var(--skin-color-border);
            background: var(--skin-color-bg-hover);
            color: var(--skin-color-text-primary);
            font-family: var(--skin-font-sans);
            font-size: var(--skin-text-sm);
            font-weight: var(--skin-weight-medium);
            padding: var(--skin-space-sm) var(--skin-space-md);
            cursor: pointer;
        }

        .btn:hover {
            background: var(--skin-color-bg-active);
        }

        .btn.primary {
            background: var(--skin-color-accent);
            border-color: var(--skin-color-accent);
            color: var(--skin-color-accent-text);
        }

        .btn.primary:hover {
            background: var(--skin-color-accent-hover);
            border-color: var(--skin-color-accent-hover);
        }

        .btn.ghost {
            background: transparent;
        }

        .hint {
            margin: 0;
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-muted);
            line-height: var(--skin-leading-normal);
        }

        @media (prefers-reduced-motion: reduce) {
            .btn,
            .chip,
            .step-btn {
                transition: none;
            }
        }
    `;

    connectedCallback(): void {
        super.connectedCallback();
        this._seedDraft();
    }

    willUpdate(changed: PropertyValues<this>): void {
        if (changed.has('open') && this.open) {
            this._seedDraft();
            this._status = 'idle';
            this._statusDetail = '';
        }
        if (changed.has('value') && this.value && !this.open) {
            this._draft = normalizeChatPrefs(this.value);
        }
    }

    private _seedDraft(): void {
        this._draft = normalizeChatPrefs(this.value ?? loadChatPrefs());
    }

    private _patch(partial: Partial<ChatPrefs>): void {
        this._draft = normalizeChatPrefs({ ...this._draft, ...partial });
    }

    private _patchToolIcon(key: ToolIconKey, on: boolean): void {
        this._draft = normalizeChatPrefs({
            ...this._draft,
            toolIcons: { ...this._draft.toolIcons, [key]: on },
        });
    }

    /** Open the modal and re-seed the draft (CS-30 companion). */
    show(): void {
        this.open = true;
    }

    /** CS-30 — close without saving. */
    close(): void {
        this.open = false;
        this.dispatchEvent(new CustomEvent('close', { bubbles: true, composed: true }));
    }

    /** CS-28 — draft back to defaults (does not persist until Save). */
    reset(): void {
        this._draft = normalizeChatPrefs(DEFAULT_CHAT_PREFS);
        this._status = 'idle';
        this._statusDetail = '';
        this.dispatchEvent(new CustomEvent('reset', { bubbles: true, composed: true }));
    }

    /** CS-29 — persist + broadcast + close. */
    save(): void {
        try {
            const written = saveChatPrefs(this._draft);
            this._draft = written;
            emitChatPrefs(written);
            this._status = 'saved';
            this._statusDetail = 'Saved to this browser (server preferences API not connected).';
            this.dispatchEvent(
                new CustomEvent('save', {
                    detail: { prefs: written, persisted: 'local' },
                    bubbles: true,
                    composed: true,
                }),
            );
            this.open = false;
        } catch (err) {
            this._status = 'error';
            this._statusDetail =
                err instanceof Error ? `Save failed: ${err.message}` : 'Save failed: storage unavailable.';
        }
    }

    private _onSelect<K extends keyof ChatPrefs>(key: K) {
        return (e: Event) => {
            const el = e.target as HTMLSelectElement;
            const raw = el.value;
            if (key === 'fontSize') {
                const n = Number(raw);
                this._patch({ [key]: n } as Partial<ChatPrefs>);
                return;
            }
            this._patch({ [key]: raw } as Partial<ChatPrefs>);
        };
    }

    private _onCheck(key: keyof ChatPrefs) {
        return (e: Event) => {
            const el = e.target as HTMLInputElement;
            this._patch({ [key]: el.checked } as Partial<ChatPrefs>);
        };
    }

    private _selectField(
        id: string,
        label: string,
        value: string,
        options: readonly { value: string; label: string }[],
        onChange: (e: Event) => void,
    ) {
        return html`
            <div class="field">
                <label class="field-label" for=${id}>${label}<span class="field-id">${id}</span></label>
                <select id=${id} .value=${value} @change=${onChange}>
                    ${options.map(
                        (o) => html`<option value=${o.value} ?selected=${o.value === value}>${o.label}</option>`,
                    )}
                </select>
            </div>
        `;
    }

    private _toggleField(id: string, label: string, checked: boolean, onChange: (e: Event) => void) {
        return html`
            <label class="toggle-row" for=${id}>
                <input id=${id} type="checkbox" .checked=${checked} @change=${onChange} />
                <span>${label} <span class="field-id">${id}</span></span>
            </label>
        `;
    }

    private _renderVisual(): unknown {
        const d = this._draft;
        return html`
            <section class="section" aria-labelledby="cs-visual">
                <h3 class="section-title" id="cs-visual">Visual</h3>
                <div class="row">
                    ${this._selectField(
                        'CS-01',
                        'Message density',
                        d.density,
                        DENSITY_OPTIONS.map((v) => ({ value: v, label: titleCase(v) })),
                        this._onSelect('density'),
                    )}
                    ${this._selectField(
                        'CS-02',
                        'Bubble style',
                        d.bubbleStyle,
                        BUBBLE_STYLE_OPTIONS.map((v) => ({ value: v, label: titleCase(v) })),
                        this._onSelect('bubbleStyle'),
                    )}
                </div>
                <div class="row">
                    ${this._selectField(
                        'CS-03',
                        'Font size',
                        String(d.fontSize),
                        FONT_SIZE_OPTIONS.map((v) => ({ value: String(v), label: `${v}` })),
                        this._onSelect('fontSize'),
                    )}
                    ${this._selectField(
                        'CS-08',
                        'Show reasoning',
                        d.showReasoning,
                        REASONING_VISIBILITY_OPTIONS.map((v) => ({
                            value: v,
                            label: titleCase(v),
                        })),
                        this._onSelect('showReasoning'),
                    )}
                </div>
                <div class="row">
                    ${this._toggleField('CS-04', 'Show timestamps', d.showTimestamps, this._onCheck('showTimestamps'))}
                    ${this._toggleField('CS-05', 'Show avatars', d.showAvatars, this._onCheck('showAvatars'))}
                </div>
                <div class="row">
                    ${this._toggleField('CS-06', 'Show confidence', d.showConfidence, this._onCheck('showConfidence'))}
                    ${this._toggleField('CS-07', 'Show model chip', d.showModelChip, this._onCheck('showModelChip'))}
                </div>
            </section>
        `;
    }

    private _renderCot(): unknown {
        const d = this._draft;
        return html`
            <section class="section" aria-labelledby="cs-cot">
                <h3 class="section-title" id="cs-cot">Chain of thought</h3>
                <div class="row">
                    ${this._selectField(
                        'CS-09',
                        'Reasoning style',
                        d.reasoningStyle,
                        REASONING_STYLE_OPTIONS.map((v) => ({ value: v, label: titleCase(v) })),
                        this._onSelect('reasoningStyle'),
                    )}
                    <div class="field">
                        <span class="field-label">Max reasoning lines <span class="field-id">CS-10</span></span>
                        <div class="stepper">
                            <button
                                class="step-btn"
                                type="button"
                                aria-label="Decrease max reasoning lines"
                                ?disabled=${d.maxReasoningLines <= MIN_REASONING_LINES}
                                @click=${() =>
                                    this._patch({
                                        maxReasoningLines: Math.max(
                                            MIN_REASONING_LINES,
                                            d.maxReasoningLines - 1,
                                        ),
                                    })}
                            >
                                −
                            </button>
                            <input
                                type="number"
                                min=${MIN_REASONING_LINES}
                                max=${MAX_REASONING_LINES}
                                .value=${String(d.maxReasoningLines)}
                                @change=${(e: Event) => {
                                    const n = Number((e.target as HTMLInputElement).value);
                                    this._patch({
                                        maxReasoningLines: Math.min(
                                            MAX_REASONING_LINES,
                                            Math.max(MIN_REASONING_LINES, Math.round(n) || MIN_REASONING_LINES),
                                        ),
                                    });
                                }}
                            />
                            <button
                                class="step-btn"
                                type="button"
                                aria-label="Increase max reasoning lines"
                                ?disabled=${d.maxReasoningLines >= MAX_REASONING_LINES}
                                @click=${() =>
                                    this._patch({
                                        maxReasoningLines: Math.min(
                                            MAX_REASONING_LINES,
                                            d.maxReasoningLines + 1,
                                        ),
                                    })}
                            >
                                +
                            </button>
                        </div>
                    </div>
                </div>
                <div class="row">
                    ${this._toggleField('CS-11', 'Show token usage', d.showTokenUsage, this._onCheck('showTokenUsage'))}
                    ${this._toggleField('CS-12', 'Show latency', d.showLatency, this._onCheck('showLatency'))}
                </div>
            </section>
        `;
    }

    private _renderTools(): unknown {
        const d = this._draft;
        return html`
            <section class="section" aria-labelledby="cs-tools">
                <h3 class="section-title" id="cs-tools">Tools on chat</h3>
                <div class="field">
                    <span class="field-label">Icon strip <span class="field-id">CS-13…20</span></span>
                    <div class="checks" role="group" aria-label="Tool icon strip">
                        ${TOOL_ICON_KEYS.map((key, i) => html`
                            <label class="chip" data-on=${d.toolIcons[key] ? 'true' : 'false'}>
                                <input
                                    type="checkbox"
                                    .checked=${d.toolIcons[key]}
                                    @change=${(e: Event) =>
                                        this._patchToolIcon(key, (e.target as HTMLInputElement).checked)}
                                />
                                ${TOOL_ICON_LABELS[key]}
                                <span class="field-id">CS-${String(13 + i).padStart(2, '0')}</span>
                            </label>
                        `)}
                    </div>
                </div>
                <div class="row">
                    ${this._selectField(
                        'CS-21',
                        'Show tool args',
                        d.showToolArgs,
                        TOOL_ARGS_OPTIONS.map((v) => ({ value: v, label: titleCase(v) })),
                        this._onSelect('showToolArgs'),
                    )}
                    ${this._toggleField(
                        'CS-22',
                        'Highlight failures',
                        d.highlightFailures,
                        this._onCheck('highlightFailures'),
                    )}
                </div>
                <div class="row">
                    ${this._toggleField(
                        'CS-23',
                        'Auto-expand HITL',
                        d.autoExpandHitl,
                        this._onCheck('autoExpandHitl'),
                    )}
                </div>
            </section>
        `;
    }

    private _renderStream(): unknown {
        const d = this._draft;
        return html`
            <section class="section" aria-labelledby="cs-stream">
                <h3 class="section-title" id="cs-stream">Stream / send</h3>
                <div class="row">
                    ${this._toggleField('CS-24', 'Stream tokens', d.streamTokens, this._onCheck('streamTokens'))}
                    ${this._toggleField('CS-25', 'Enter sends', d.enterSends, this._onCheck('enterSends'))}
                </div>
                <div class="row">
                    ${this._toggleField('CS-26', 'Sound on done', d.soundOnDone, this._onCheck('soundOnDone'))}
                    ${this._toggleField(
                        'CS-27',
                        'Notify on long job',
                        d.notifyOnLongJob,
                        this._onCheck('notifyOnLongJob'),
                    )}
                </div>
            </section>
        `;
    }

    private _renderActions(): unknown {
        return html`
            <div class="actions">
                <p class="status" data-kind=${this._status} role="status">
                    ${this._statusDetail ||
                    'Preferences apply live to the open chat after Save. Stored in this browser.'}
                </p>
                <button class="btn ghost" type="button" @click=${this.reset}>↺ Reset</button>
                <button class="btn ghost" type="button" @click=${this.close}>Cancel</button>
                <button class="btn primary" type="button" @click=${this.save}>Save &amp; apply</button>
            </div>
        `;
    }

    render() {
        return html`
            <soma-glass-modal
                .open=${this.open}
                title="Chat settings"
                subtitle="CS-01…CS-30 · density · CoT · tools · stream"
                size="lg"
                @soma-modal-close=${() => {
                    this.open = false;
                    this.dispatchEvent(new CustomEvent('close', { bubbles: true, composed: true }));
                }}
            >
                <div class="form">
                    ${this._renderVisual()}
                    ${this._renderCot()}
                    ${this._renderTools()}
                    ${this._renderStream()}
                    ${this._renderActions()}
                </div>
            </soma-glass-modal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-chat-settings': SomaChatSettings;
    }
}
