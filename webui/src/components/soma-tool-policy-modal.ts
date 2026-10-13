/**
 * soma-tool-policy-modal — per-tool execution policy editor.
 *
 * Opens from Hands (soma-agent-hands) and emits one save event carrying
 * execution (auto | approval | deny), scope, and reason. The parent maps
 * execution into the Agent API `tool_policy` buckets on PATCH
 * `/agents/{agentId}/capsule`.
 *
 * UI labels say Agent / Hands / Tools — never Capsule. API paths may use
 * capsule. All visual styling uses `--skin-*` tokens only.
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

/** Execution buckets matching Capsule tool_policy keys (API shape). */
export type ToolExecutionPolicy = 'auto' | 'approval' | 'deny';

export interface ToolPolicySaveDetail {
    toolName: string;
    execution: ToolExecutionPolicy;
    scope: string;
    reason: string;
}

const EXECUTION_OPTIONS: { value: ToolExecutionPolicy; label: string; hint: string }[] = [
    { value: 'auto', label: 'Auto', hint: 'Runs without a human gate' },
    { value: 'approval', label: 'Approval', hint: 'Requires a human before run' },
    { value: 'deny', label: 'Deny', hint: 'Never runs' },
];

const SCOPE_OPTIONS = ['kit', 'venv', 'net'] as const;

@customElement('soma-tool-policy-modal')
export class SomaToolPolicyModal extends LitElement {
    @property({ type: Boolean, reflect: true }) open = false;
    @property({ type: String, attribute: 'tool-name' }) toolName = '';
    @property({ type: String }) execution: ToolExecutionPolicy = 'approval';
    @property({ type: String }) scope: string = 'kit';
    @property({ type: String }) reason = '';
    /** Present-but-disabled when the parent cannot persist policy (REQ-UIX-020). */
    @property({ type: String, attribute: 'blocked-reason' }) blockedReason = '';

    @state() private _draftExecution: ToolExecutionPolicy = 'approval';
    @state() private _draftScope = 'kit';
    @state() private _draftReason = '';

    static styles = css`
        :host {
            display: contents;
            font-family: var(--skin-font-sans);
        }

        .backdrop {
            position: fixed;
            inset: 0;
            background: color-mix(in srgb, var(--skin-color-bg-void) 72%, transparent);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: var(--skin-space-lg);
            z-index: 220;
            opacity: 0;
            visibility: hidden;
            transition: opacity var(--skin-motion-normal) var(--skin-motion-ease),
                visibility var(--skin-motion-normal) var(--skin-motion-ease);
        }

        .backdrop.open {
            opacity: 1;
            visibility: visible;
        }

        .modal {
            width: min(420px, 100%);
            background: var(--skin-color-bg-card);
            border: 1px solid var(--skin-color-border);
            border-radius: var(--skin-radius-lg);
            box-shadow: var(--skin-shadow-overlay);
            display: flex;
            flex-direction: column;
            max-height: calc(100vh - 48px);
            overflow: hidden;
            transform: scale(0.97) translateY(8px);
            transition: transform var(--skin-motion-normal) var(--skin-motion-ease);
        }

        .backdrop.open .modal {
            transform: scale(1) translateY(0);
        }

        .header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: var(--skin-space-md);
            padding: var(--skin-space-lg);
            border-bottom: 1px solid var(--skin-color-border-subtle);
        }

        .title {
            margin: 0;
            font-size: var(--skin-text-lg);
            font-weight: var(--skin-weight-semibold);
            color: var(--skin-color-text-primary);
        }

        .subtitle {
            margin: var(--skin-space-xs) 0 0;
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-secondary);
            word-break: break-all;
        }

        .close-btn {
            width: 32px;
            height: 32px;
            border-radius: var(--skin-radius-md);
            border: 1px solid var(--skin-color-border);
            background: var(--skin-color-bg-base);
            color: var(--skin-color-text-secondary);
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            line-height: 1;
            flex-shrink: 0;
        }

        .close-btn:hover {
            background: var(--skin-color-bg-hover);
            color: var(--skin-color-text-primary);
        }

        .body {
            padding: var(--skin-space-lg);
            display: flex;
            flex-direction: column;
            gap: var(--skin-space-md);
            overflow-y: auto;
        }

        .field {
            display: flex;
            flex-direction: column;
            gap: var(--skin-space-xs);
        }

        .field-label {
            font-size: var(--skin-text-xs);
            font-weight: var(--skin-weight-semibold);
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: var(--skin-color-text-muted);
        }

        .exec-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: var(--skin-space-sm);
        }

        .exec-option {
            border: 1px solid var(--skin-color-border);
            background: var(--skin-color-bg-base);
            color: var(--skin-color-text-secondary);
            border-radius: var(--skin-radius-md);
            padding: var(--skin-space-sm) var(--skin-space-xs);
            cursor: pointer;
            font-family: inherit;
            font-size: var(--skin-text-sm);
            font-weight: var(--skin-weight-medium);
            text-align: center;
            transition: background var(--skin-motion-fast) var(--skin-motion-ease),
                border-color var(--skin-motion-fast) var(--skin-motion-ease),
                color var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .exec-option:hover {
            background: var(--skin-color-bg-hover);
            color: var(--skin-color-text-primary);
        }

        .exec-option.selected {
            background: var(--skin-color-accent);
            border-color: var(--skin-color-accent);
            color: var(--skin-color-accent-text);
        }

        .exec-option.selected.deny {
            background: var(--skin-color-danger);
            border-color: var(--skin-color-danger);
            color: var(--skin-color-danger-text);
        }

        .exec-option.selected.approval {
            background: var(--skin-color-warning);
            border-color: var(--skin-color-warning);
            color: var(--skin-color-warning-text);
        }

        .exec-option.selected.auto {
            background: var(--skin-color-success);
            border-color: var(--skin-color-success);
            color: var(--skin-color-success-text);
        }

        .exec-hint {
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-muted);
            margin: 0;
        }

        select,
        textarea {
            width: 100%;
            box-sizing: border-box;
            font-family: inherit;
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-primary);
            background: var(--skin-color-bg-base);
            border: 1px solid var(--skin-color-border);
            border-radius: var(--skin-radius-md);
            padding: var(--skin-space-sm) var(--skin-space-md);
        }

        select:focus,
        textarea:focus,
        .exec-option:focus-visible,
        .close-btn:focus-visible,
        .btn:focus-visible {
            outline: none;
            border-color: var(--skin-color-accent);
            box-shadow: 0 0 0 var(--skin-focus-ring-width) var(--skin-focus-ring);
        }

        textarea {
            min-height: 72px;
            resize: vertical;
        }

        .blocked {
            margin: 0;
            padding: var(--skin-space-sm) var(--skin-space-md);
            border-radius: var(--skin-radius-md);
            border: 1px solid var(--skin-color-warning);
            background: color-mix(in srgb, var(--skin-color-warning) 14%, transparent);
            color: var(--skin-color-warning-text);
            font-size: var(--skin-text-xs);
        }

        .footer {
            display: flex;
            justify-content: flex-end;
            gap: var(--skin-space-sm);
            padding: var(--skin-space-md) var(--skin-space-lg);
            border-top: 1px solid var(--skin-color-border-subtle);
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
    `;

    override update(changed: Map<string, unknown>) {
        if (changed.has('open') && this.open) {
            this._draftExecution = this.execution;
            this._draftScope = this.scope;
            this._draftReason = this.reason;
        }
        super.update(changed);
    }

    override render() {
        const blocked = this.blockedReason.trim().length > 0;
        return html`
            <div
                class="backdrop ${this.open ? 'open' : ''}"
                @click=${this._onBackdrop}
                role="dialog"
                aria-modal="true"
                aria-labelledby="tool-policy-title"
                aria-hidden=${this.open ? 'false' : 'true'}
            >
                <div class="modal" @click=${(e: Event) => e.stopPropagation()}>
                    <header class="header">
                        <div>
                            <h2 class="title" id="tool-policy-title">Tool policy</h2>
                            <p class="subtitle">${this.toolName || 'Tool'}</p>
                        </div>
                        <button class="close-btn" type="button" @click=${this._onCancel} aria-label="Close">
                            ×
                        </button>
                    </header>
                    <div class="body">
                        ${blocked
                            ? html`<p class="blocked">${this.blockedReason}</p>`
                            : nothing}
                        <div class="field">
                            <span class="field-label">Execution</span>
                            <div class="exec-row" role="radiogroup" aria-label="Execution policy">
                                ${EXECUTION_OPTIONS.map((opt) => html`
                                    <button
                                        type="button"
                                        class="exec-option ${opt.value} ${this._draftExecution === opt.value ? 'selected' : ''}"
                                        role="radio"
                                        aria-checked=${this._draftExecution === opt.value ? 'true' : 'false'}
                                        ?disabled=${blocked}
                                        @click=${() => this._draftExecution = opt.value}
                                    >
                                        ${opt.label}
                                    </button>
                                `)}
                            </div>
                            <p class="exec-hint">
                                ${(EXECUTION_OPTIONS.find((o) => o.value === this._draftExecution) ?? EXECUTION_OPTIONS[1]).hint}
                            </p>
                        </div>
                        <div class="field">
                            <label class="field-label" for="tool-policy-scope">Scope</label>
                            <select
                                id="tool-policy-scope"
                                .value=${this._draftScope}
                                ?disabled=${blocked}
                                @change=${(e: Event) => {
                                    this._draftScope = (e.target as HTMLSelectElement).value;
                                }}
                            >
                                ${SCOPE_OPTIONS.map((s) => html`
                                    <option value=${s} ?selected=${this._draftScope === s}>${s}</option>
                                `)}
                                ${!SCOPE_OPTIONS.includes(this._draftScope as (typeof SCOPE_OPTIONS)[number])
                                    ? html`<option value=${this._draftScope} selected>${this._draftScope}</option>`
                                    : nothing}
                            </select>
                        </div>
                        <div class="field">
                            <label class="field-label" for="tool-policy-reason">Reason</label>
                            <textarea
                                id="tool-policy-reason"
                                .value=${this._draftReason}
                                ?disabled=${blocked}
                                placeholder="Why this execution policy"
                                @input=${(e: Event) => {
                                    this._draftReason = (e.target as HTMLTextAreaElement).value;
                                }}
                            ></textarea>
                        </div>
                    </div>
                    <footer class="footer">
                        <button class="btn" type="button" @click=${this._onCancel}>Cancel</button>
                        <button
                            class="btn primary"
                            type="button"
                            ?disabled=${blocked}
                            @click=${this._onSave}
                        >
                            Save
                        </button>
                    </footer>
                </div>
            </div>
        `;
    }

    private _onBackdrop = () => {
        this._close();
    };

    private _onCancel = () => {
        this._close();
    };

    private _close() {
        this.open = false;
        this.dispatchEvent(new CustomEvent('soma-tool-policy-close', {
            bubbles: true,
            composed: true,
            detail: { toolName: this.toolName },
        }));
    }

    private _onSave = () => {
        if (this.blockedReason.trim().length > 0) return;
        const detail: ToolPolicySaveDetail = {
            toolName: this.toolName,
            execution: this._draftExecution,
            scope: this._draftScope,
            reason: this._draftReason,
        };
        this.dispatchEvent(new CustomEvent('soma-tool-policy-save', {
            bubbles: true,
            composed: true,
            detail,
        }));
        this.open = false;
    };
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-tool-policy-modal': SomaToolPolicyModal;
    }
}
