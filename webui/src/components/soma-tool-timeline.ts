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

    static styles = css`
        :host {
            display: block;
            width: 100%;
        }

        .timeline {
            display: flex;
            flex-direction: column;
            gap: 6px;
            width: 100%;
        }

        .step {
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 12px;
            background: rgba(12, 12, 14, 0.72);
            overflow: hidden;
            transition: border-color 140ms ease;
        }

        .step:hover {
            border-color: rgba(255, 90, 20, 0.22);
        }

        .step-header {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 11px;
            cursor: pointer;
            user-select: none;
            transition: background 120ms ease;
        }

        .step-header:hover {
            background: rgba(255, 255, 255, 0.03);
        }

        .step-header:focus-visible {
            outline: 2px solid #60a5fa;
            outline-offset: -2px;
        }

        .chevron {
            font-size: 11px;
            color: var(--platform-text-dim, #6b6b6b);
            width: 12px;
            flex-shrink: 0;
            transition: transform 140ms ease;
        }

        .chevron.open {
            transform: rotate(90deg);
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            flex-shrink: 0;
            background: var(--platform-text-dim, #6b6b6b);
        }

        .status-dot.pending {
            background: var(--platform-info, #3b82f6);
            animation: pulse 1.2s ease-in-out infinite;
        }

        .status-dot.executing {
            background: var(--platform-warning, #eab308);
            animation: pulse 1.2s ease-in-out infinite;
        }

        .status-dot.executed {
            background: var(--platform-success, #22c55e);
        }

        .status-dot.error,
        .status-dot.denied,
        .status-dot.invalid_arguments {
            background: var(--platform-danger, #ef4444);
        }

        .status-dot.approval_required {
            background: var(--platform-warning, #eab308);
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
            font-family: var(--platform-font-mono, 'JetBrains Mono', ui-monospace, monospace);
            font-size: 12px;
            color: var(--platform-text-bright, #f8fafc);
            font-weight: 500;
            flex: 1;
            min-width: 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .step-meta {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-shrink: 0;
        }

        .status-label {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.45px;
            padding: 2px 7px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.06);
            color: var(--platform-text-dim, #6b6b6b);
        }

        .status-label.executed {
            color: var(--platform-success, #22c55e);
            border-color: rgba(34, 197, 94, 0.28);
        }

        .status-label.error,
        .status-label.denied,
        .status-label.invalid_arguments {
            color: var(--platform-danger, #ef4444);
            border-color: rgba(239, 68, 68, 0.3);
        }

        .status-label.approval_required,
        .status-label.executing {
            color: var(--platform-warning, #eab308);
            border-color: rgba(234, 179, 8, 0.3);
        }

        .duration {
            font-family: var(--platform-font-mono, 'JetBrains Mono', ui-monospace, monospace);
            font-size: 10px;
            color: var(--platform-text-dim, #6b6b6b);
            font-variant-numeric: tabular-nums;
        }

        .step-body {
            padding: 0 11px 11px 30px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            padding-top: 9px;
        }

        .section-label {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--platform-text-dim, #6b6b6b);
            margin-bottom: 3px;
        }

        pre {
            margin: 0;
            padding: 8px 10px;
            background: rgba(8, 8, 10, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            font-family: var(--platform-font-mono, 'JetBrains Mono', ui-monospace, monospace);
            font-size: 11px;
            line-height: 1.55;
            color: var(--platform-text-main, #e2e8f0);
            max-height: 220px;
            overflow: auto;
            white-space: pre-wrap;
            word-break: break-word;
        }

        .error-text {
            color: var(--platform-danger, #ef4444);
        }

        .approval-row {
            display: flex;
            gap: 8px;
            padding-top: 4px;
        }

        .approval-btn {
            padding: 5px 14px;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            background: rgba(255, 255, 255, 0.04);
            color: var(--platform-text-main, #e2e8f0);
            font-size: 12px;
            cursor: pointer;
            transition: all 120ms ease;
        }

        .approval-btn:hover:not(:disabled) {
            background: rgba(255, 255, 255, 0.08);
        }

        .approval-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .approval-btn.approve {
            border-color: rgba(34, 197, 94, 0.5);
            color: var(--platform-success, #22c55e);
        }

        .approval-btn.approve:hover:not(:disabled) {
            background: rgba(34, 197, 94, 0.12);
        }

        .approval-btn.deny {
            border-color: rgba(239, 68, 68, 0.5);
            color: var(--platform-danger, #ef4444);
        }

        .approval-btn.deny:hover:not(:disabled) {
            background: rgba(239, 68, 68, 0.12);
        }

        .empty {
            font-size: 12px;
            color: var(--platform-text-dim, #6b6b6b);
            padding: 4px 0;
        }

        .memory-id {
            font-family: var(--platform-font-mono, 'JetBrains Mono', ui-monospace, monospace);
            font-size: 10px;
            padding: 2px 7px;
            border-radius: 999px;
            border: 1px solid rgba(59, 130, 246, 0.4);
            color: var(--platform-info, #3b82f6);
            max-width: 180px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            flex-shrink: 0;
        }
    `;

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
                    <span class="chevron ${open ? 'open' : ''}">▶</span>
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
