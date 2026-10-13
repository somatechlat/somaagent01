/**
 * Collapsible chain-of-thought block (CS-08 / CS-09 / CS-10).
 *
 * Honesty law: renders ONLY content the server/WS actually supplied.
 * Empty content → nothing is drawn (never invent steps). When the provider
 * forces hidden reasoning, pass `note` and leave content empty — the block
 * shows the gated note instead of fake CoT.
 *
 * Formats: steps (numbered) · prose (paragraphs) · raw (monospace).
 * `maxLines` clamps the body while collapsed; expand reveals the full body.
 */

import { LitElement, html, css, nothing, PropertyValues } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

export type ReasoningFormat = 'steps' | 'prose' | 'raw';
export type ReasoningMode = 'off' | 'collapsed' | 'expanded';

export const REASONING_FORMATS: readonly ReasoningFormat[] = ['steps', 'prose', 'raw'] as const;
export const REASONING_MODES: readonly ReasoningMode[] = ['off', 'collapsed', 'expanded'] as const;

const MIN_CLAMP_LINES = 4;
const MAX_CLAMP_LINES = 64;
const DEFAULT_CLAMP_LINES = 12;

@customElement('soma-reasoning-block')
export class SomaReasoningBlock extends LitElement {
    /** CS-09 — how the supplied reasoning is rendered. */
    @property({ type: String }) format: ReasoningFormat = 'steps';
    /** CS-08 — Off hides the block entirely, Collapsed/Expanded set the open state. */
    @property({ type: String }) mode: ReasoningMode = 'collapsed';
    /** Numbered steps for `format="steps"`. */
    @property({ type: Array }) steps: string[] = [];
    /** Prose / raw body when not using `steps`. */
    @property({ type: String }) text = '';
    /** CS-10 — collapsed body line clamp. */
    @property({ type: Number }) maxLines = DEFAULT_CLAMP_LINES;
    /**
     * Honest gated note when reasoning is unavailable (e.g. server forced
     * `reasoning_format:"hidden"`). Shown instead of inventing content.
     */
    @property({ type: String }) note = '';

    @state() private _userExpanded = false;

    static styles = css`
        :host {
            display: block;
            width: 100%;
            font-family: var(--skin-font-sans);
            color: var(--skin-color-text-secondary);
        }

        :host([hidden]) {
            display: none;
        }

        .shell {
            border: 1px solid var(--skin-color-border);
            border-radius: var(--skin-radius-md);
            background: var(--skin-color-bg-card);
            overflow: hidden;
        }

        .header {
            display: flex;
            align-items: center;
            gap: var(--skin-space-sm);
            padding: var(--skin-space-sm) var(--skin-space-md);
            cursor: pointer;
            user-select: none;
            color: var(--skin-color-text-muted);
            font-size: var(--skin-text-xs);
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }

        .header:focus-visible {
            outline: var(--skin-focus-ring-width) solid var(--skin-focus-ring);
            outline-offset: var(--skin-focus-ring-offset);
        }

        .dot {
            width: 6px;
            height: 6px;
            border-radius: var(--skin-radius-full);
            background: var(--skin-color-accent);
            flex-shrink: 0;
        }

        .label {
            flex: 1;
            min-width: 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .action {
            border: 1px solid var(--skin-color-border);
            background: var(--skin-color-bg-hover);
            color: var(--skin-color-text-secondary);
            border-radius: var(--skin-radius-sm);
            font-family: var(--skin-font-sans);
            font-size: var(--skin-text-xs);
            padding: 2px var(--skin-space-sm);
            cursor: pointer;
        }

        .action:hover {
            background: var(--skin-color-bg-active);
            color: var(--skin-color-text-primary);
        }

        .action:focus-visible {
            outline: var(--skin-focus-ring-width) solid var(--skin-focus-ring);
            outline-offset: var(--skin-focus-ring-offset);
        }

        .body {
            padding: 0 var(--skin-space-md) var(--skin-space-md);
            font-size: var(--skin-text-sm);
            line-height: var(--skin-leading-relaxed);
            color: var(--skin-color-text-secondary);
        }

        .body.clamped {
            display: -webkit-box;
            -webkit-box-orient: vertical;
            -webkit-line-clamp: var(--cot-clamp, 12);
            overflow: hidden;
        }

        .steps {
            margin: 0;
            padding-left: 1.25em;
        }

        .steps li {
            margin: 0 0 var(--skin-space-xs);
        }

        .prose p {
            margin: 0 0 var(--skin-space-sm);
        }

        .prose p:last-child {
            margin-bottom: 0;
        }

        .raw {
            margin: 0;
            font-family: var(--skin-font-mono);
            font-size: var(--skin-text-xs);
            white-space: pre-wrap;
            word-break: break-word;
        }

        .note {
            margin: 0;
            padding: var(--skin-space-sm) var(--skin-space-md);
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-muted);
            border-top: 1px solid var(--skin-color-border-subtle);
        }

        .empty {
            margin: 0;
            padding: var(--skin-space-md);
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-muted);
        }

        @media (prefers-reduced-motion: reduce) {
            .shell {
                transition: none;
            }
        }
    `;

    connectedCallback(): void {
        super.connectedCallback();
        this._userExpanded = this.mode === 'expanded';
    }

    willUpdate(changed: PropertyValues<this>): void {
        if (changed.has('mode')) {
            this._userExpanded = this.mode === 'expanded';
        }
        if (changed.has('maxLines')) {
            const n = Math.round(Number(this.maxLines) || DEFAULT_CLAMP_LINES);
            const clamped = Math.min(MAX_CLAMP_LINES, Math.max(MIN_CLAMP_LINES, n));
            this.style.setProperty('--cot-clamp', String(clamped));
        }
    }

    private get _hasContent(): boolean {
        if (this.format === 'steps') {
            return this.steps.some((s) => typeof s === 'string' && s.trim().length > 0);
        }
        return this.text.trim().length > 0;
    }

    private get _isExpanded(): boolean {
        return this.mode === 'expanded' || this._userExpanded;
    }

    private get _stateLabel(): string {
        return this._isExpanded ? 'expanded' : 'collapsed';
    }

    private _toggle = (): void => {
        if (this.mode === 'expanded') return;
        this._userExpanded = !this._userExpanded;
        this.dispatchEvent(
            new CustomEvent('soma-reasoning-toggle', {
                detail: { expanded: this._isExpanded },
                bubbles: true,
                composed: true,
            }),
        );
    };

    private _renderBody(): unknown {
        if (this.format === 'steps') {
            const items = this.steps
                .map((s) => (typeof s === 'string' ? s.trim() : ''))
                .filter((s) => s.length > 0);
            return html`<ol class="steps">
                ${items.map((s) => html`<li>${s}</li>`)}
            </ol>`;
        }
        if (this.format === 'raw') {
            return html`<pre class="raw">${this.text}</pre>`;
        }
        const paras = this.text
            .split(/\n{2,}/)
            .map((p) => p.trim())
            .filter((p) => p.length > 0);
        return html`<div class="prose">
            ${paras.map((p) => html`<p>${p}</p>`)}
        </div>`;
    }

    render() {
        if (this.mode === 'off') return nothing;

        if (!this._hasContent) {
            if (this.note.trim().length === 0) return nothing;
            return html`
                <div class="shell">
                    <p class="note" role="note">${this.note}</p>
                </div>
            `;
        }

        const expanded = this._isExpanded;
        return html`
            <div class="shell">
                <div
                    class="header"
                    role="button"
                    tabindex="0"
                    aria-expanded=${expanded ? 'true' : 'false'}
                    @click=${this._toggle}
                    @keydown=${(e: KeyboardEvent) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            this._toggle();
                        }
                    }}
                >
                    <span class="dot" aria-hidden="true"></span>
                    <span class="label">reasoning · ${this._stateLabel}</span>
                    <button
                        class="action"
                        type="button"
                        @click=${(e: Event) => {
                            e.stopPropagation();
                            this._toggle();
                        }}
                    >
                        ${expanded ? 'collapse' : 'expand'}
                    </button>
                </div>
                <div class="body ${expanded ? '' : 'clamped'}" style="--cot-clamp: ${this.maxLines}">
                    ${this._renderBody()}
                </div>
                ${this.note.trim().length > 0
                    ? html`<p class="note" role="note">${this.note}</p>`
                    : nothing}
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-reasoning-block': SomaReasoningBlock;
    }
}
