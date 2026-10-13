/**
 * SomaAgent01 — Tool-call timeline (process-group equivalent, CH-11 / C2).
 *
 * Renders collapsible tool-call steps bound to the WS tool event stream:
 *   tool.call            → step created (name, index)
 *   tool.delta           → arguments accumulate (arguments_delta)
 *   tool.done            → result / status / duration finalize the step
 *   tool.approval_request→ approval_required (approve / deny actions)
 *
 * Accepts an array of ToolCallStep via the `steps` property.
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { glassCard } from '../styles/glass.js';
import { moduleBase } from '../styles/module-base.js';

export type ToolStepStatus =
    | 'pending'
    | 'executing'
    | 'executed'
    | 'error'
    | 'denied'
    | 'approval_required'
    | 'invalid_arguments';

export interface ToolCallStep {
    /** Stable id: tool_call_id when present, else `idx:{iteration}:{index}`. */
    id: string;
    name: string;
    status: ToolStepStatus;
    iteration?: number;
    index?: number;
    /** Parsed arguments object (best-effort from streamed fragments). */
    arguments?: Record<string, unknown> | null;
    /** Raw accumulated arguments text (what the model streamed). */
    argumentsText?: string;
    result?: unknown;
    ok?: boolean;
    error?: string | null;
    durationMs?: number;
}

@customElement('soma-tool-timeline')
export class SomaToolTimeline extends LitElement {
    @property({ type: Array }) steps: ToolCallStep[] = [];

    @state() private _expanded: Record<string, boolean> = {};
    @state() private _acting: Record<string, boolean> = {};

    static styles = [
        glassCard,
        moduleBase,
        css`
        :host {
            display: block;
            width: 100%;
        }

        .timeline {
            display: flex;
            flex-direction: column;
            gap: var(--skin-space-xs);
            width: 100%;
        }

        .step {
            border: var(--skin-border-width) solid var(--skin-color-border-subtle);
            border-radius: var(--skin-radius-lg);
            background: var(--skin-glass-bg);
            overflow: hidden;
            transition: border-color var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .step:hover {
            border-color: color-mix(in srgb, var(--skin-color-accent) 22%, transparent);
        }

        .step-header {
            display: flex;
            align-items: center;
            gap: var(--skin-space-sm);
            padding: var(--skin-space-sm) var(--skin-space-md);
            cursor: pointer;
            user-select: none;
            transition: background var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .step-header:hover {
            background: var(--skin-color-bg-hover);
        }

        .step-header:focus-visible {
            outline: var(--skin-focus-ring-width) solid var(--skin-focus-ring);
            outline-offset: calc(-1 * var(--skin-focus-ring-offset));
        }

        .chevron {
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-secondary);
            width: var(--skin-space-sm);
            flex-shrink: 0;
            transition: transform var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .chevron.open {
            transform: rotate(90deg);
        }

        .status-dot {
            width: var(--skin-space-xs);
            height: var(--skin-space-xs);
            border-radius: var(--skin-radius-full);
            flex-shrink: 0;
            background: var(--skin-color-text-secondary);
        }

        .status-dot.pending {
            background: var(--skin-color-info);
            animation: pulse 1.2s ease-in-out infinite;
        }

        .status-dot.executing {
            background: var(--skin-color-warning);
            animation: pulse 1.2s ease-in-out infinite;
        }

        .status-dot.executed {
            background: var(--skin-color-success);
        }

        .status-dot.error,
        .status-dot.denied,
        .status-dot.invalid_arguments {
            background: var(--skin-color-danger);
        }

        .status-dot.approval_required {
            background: var(--skin-color-warning);
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.35; }
        }

        @media (prefers-reduced-motion: reduce) {
            .status-dot.pending,
            .status-dot.executing {
                animation: none;
            }
            .chevron {
                transition: none;
            }
        }

        .step-name {
            font-family: var(--skin-font-mono);
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-primary);
            font-weight: var(--skin-weight-medium);
            flex: 1;
            min-width: 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .step-meta {
            display: flex;
            align-items: center;
            gap: var(--skin-space-sm);
            flex-shrink: 0;
        }

        .status-label {
            font-size: var(--skin-text-xs);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 2px var(--skin-space-xs);
            border-radius: var(--skin-radius-full);
            background: var(--skin-color-bg-hover);
            border: var(--skin-border-width) solid var(--skin-color-border-subtle);
            color: var(--skin-color-text-secondary);
        }

        .status-label.executed {
            color: var(--skin-color-success);
            border-color: color-mix(in srgb, var(--skin-color-success) 28%, transparent);
        }

        .status-label.error,
        .status-label.denied,
        .status-label.invalid_arguments {
            color: var(--skin-color-danger);
            border-color: color-mix(in srgb, var(--skin-color-danger) 30%, transparent);
        }

        .status-label.approval_required,
        .status-label.executing {
            color: var(--skin-color-warning);
            border-color: color-mix(in srgb, var(--skin-color-warning) 30%, transparent);
        }

        .duration {
            font-family: var(--skin-font-mono);
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-secondary);
            font-variant-numeric: tabular-nums;
        }

        .step-body {
            padding: 0 var(--skin-space-md) var(--skin-space-md) var(--skin-space-xl);
            display: flex;
            flex-direction: column;
            gap: var(--skin-space-sm);
            border-top: var(--skin-border-width) solid var(--skin-color-border-subtle);
            padding-top: var(--skin-space-sm);
        }

        .section-label {
            font-size: var(--skin-text-xs);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--skin-color-text-secondary);
            margin-bottom: var(--skin-space-xs);
        }

        pre {
            margin: 0;
            padding: var(--skin-space-sm) var(--skin-space-sm);
            background: var(--skin-color-bg-base);
            border: var(--skin-border-width) solid var(--skin-color-border-subtle);
            border-radius: var(--skin-radius-md);
            font-family: var(--skin-font-mono);
            font-size: var(--skin-text-xs);
            line-height: var(--skin-leading-relaxed);
            color: var(--skin-color-text-primary);
            max-height: 14rem;
            overflow: auto;
            white-space: pre-wrap;
            word-break: break-word;
        }

        .error-text {
            color: var(--skin-color-danger);
        }

        .approval-row {
            display: flex;
            gap: var(--skin-space-sm);
            padding-top: var(--skin-space-xs);
        }

        .approval-btn {
            padding: var(--skin-space-xs) var(--skin-space-md);
            border-radius: var(--skin-radius-full);
            border: var(--skin-border-width) solid var(--skin-color-border);
            background: var(--skin-color-bg-hover);
            color: var(--skin-color-text-primary);
            font-size: var(--skin-text-sm);
            cursor: pointer;
            transition: all var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .approval-btn:hover:not(:disabled) {
            background: var(--skin-color-bg-active);
        }

        .approval-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .approval-btn.approve {
            border-color: color-mix(in srgb, var(--skin-color-success) 50%, transparent);
            color: var(--skin-color-success);
        }

        .approval-btn.approve:hover:not(:disabled) {
            background: color-mix(in srgb, var(--skin-color-success) 12%, transparent);
        }

        .approval-btn.deny {
            border-color: color-mix(in srgb, var(--skin-color-danger) 50%, transparent);
            color: var(--skin-color-danger);
        }

        .approval-btn.deny:hover:not(:disabled) {
            background: color-mix(in srgb, var(--skin-color-danger) 12%, transparent);
        }

        .empty {
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-secondary);
            padding: var(--skin-space-xs) 0;
        }

        .memory-id {
            font-family: var(--skin-font-mono);
            font-size: var(--skin-text-xs);
            padding: 2px var(--skin-space-xs);
            border-radius: var(--skin-radius-full);
            border: var(--skin-border-width) solid color-mix(in srgb, var(--skin-color-info) 40%, transparent);
            color: var(--skin-color-info);
            max-width: 11.25rem;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            flex-shrink: 0;
        }
    `,
    ];

    private _toggle(id: string) {
        this._expanded = { ...this._expanded, [id]: !this._expanded[id] };
    }

    private _formatJson(value: unknown): string {
        if (value == null) return '—';
        if (typeof value === 'string') {
            try {
                return JSON.stringify(JSON.parse(value), null, 2);
            } catch {
                return value;
            }
        }
        try {
            return JSON.stringify(value, null, 2);
        } catch {
            return String(value);
        }
    }

    /** Arguments view: prefer the parsed object, fall back to raw streamed text. */
    private _argsText(step: ToolCallStep): string {
        if (step.arguments && Object.keys(step.arguments).length > 0) {
            return this._formatJson(step.arguments);
        }
        if (step.argumentsText) {
            return this._formatJson(step.argumentsText);
        }
        return '—';
    }

    private _onApproval(step: ToolCallStep, approved: boolean, e: Event) {
        e.stopPropagation();
        if (this._acting[step.id]) return;
        this._acting = { ...this._acting, [step.id]: true };
        this.dispatchEvent(new CustomEvent('tool-approval', {
            detail: {
                toolCallId: step.id,
                name: step.name,
                approved,
                arguments: step.arguments ?? null,
            },
            bubbles: true,
            composed: true,
        }));
    }

    private _memoryId(step: ToolCallStep): string {
        const r = step.result;
        if (r && typeof r === 'object' && 'memory_id' in r) {
            return String((r as Record<string, unknown>).memory_id || '');
        }
        return '';
    }

    private _renderStep(step: ToolCallStep) {
        const open = !!this._expanded[step.id];
        const needsApproval = step.status === 'approval_required';
        const acted = !!this._acting[step.id];
        const memoryId = this._memoryId(step);

        return html`
            <div class="step">
                <div
                    class="step-header"
                    role="button"
                    tabindex="0"
                    aria-expanded=${open ? 'true' : 'false'}
                    @click=${() => this._toggle(step.id)}
                    @keydown=${(e: KeyboardEvent) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            this._toggle(step.id);
                        }
                    }}
                >
                    <span class="chevron ${open ? 'open' : ''} material-symbols-outlined" aria-hidden="true">play_arrow</span>
                    <span class="status-dot ${step.status}"></span>
                    <span class="step-name">${step.name || 'tool'}</span>
                    ${memoryId ? html`
                        <span class="memory-id" title="Memory ID ${memoryId}">ID ${memoryId}</span>
                    ` : nothing}
                    <span class="step-meta">
                        ${step.durationMs != null ? html`
                            <span class="duration">${step.durationMs}ms</span>
                        ` : nothing}
                        <span class="status-label ${step.status}">${step.status.replace('_', ' ')}</span>
                    </span>
                </div>
                ${open ? html`
                    <div class="step-body">
                        ${memoryId ? html`
                            <div>
                                <div class="section-label">Memory ID</div>
                                <pre>${memoryId}</pre>
                            </div>
                        ` : nothing}
                        <div>
                            <div class="section-label">Arguments</div>
                            <pre>${this._argsText(step)}</pre>
                        </div>
                        ${step.result != null || step.error ? html`
                            <div>
                                <div class="section-label">Result</div>
                                <pre class="${step.ok === false || step.error ? 'error-text' : ''}">${
                                    step.error
                                        ? step.error
                                        : this._formatJson(step.result)
                                }</pre>
                            </div>
                        ` : nothing}
                        ${needsApproval ? html`
                            <div class="approval-row">
                                <button
                                    class="approval-btn approve"
                                    ?disabled=${acted}
                                    @click=${(e: Event) => this._onApproval(step, true, e)}
                                >Approve</button>
                                <button
                                    class="approval-btn deny"
                                    ?disabled=${acted}
                                    @click=${(e: Event) => this._onApproval(step, false, e)}
                                >Deny</button>
                            </div>
                        ` : nothing}
                    </div>
                ` : nothing}
            </div>
        `;
    }

    render() {
        if (!this.steps || this.steps.length === 0) {
            return html`<div class="empty">No tool calls</div>`;
        }
        return html`
            <div class="timeline">
                ${this.steps.map((step) => this._renderStep(step))}
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-tool-timeline': SomaToolTimeline;
    }
}
