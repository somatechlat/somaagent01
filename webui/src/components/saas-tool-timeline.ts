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

@customElement('saas-tool-timeline')
export class SaasToolTimeline extends LitElement {
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
            border: 1px solid var(--aaas-border-color, rgba(255,255,255,0.06));
            border-radius: var(--aaas-radius-md, 8px);
            background: var(--aaas-bg-void, #f5f5f5);
            overflow: hidden;
        }

        .step-header {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 10px;
            cursor: pointer;
            user-select: none;
            transition: background 100ms ease;
        }

        .step-header:hover {
            background: var(--aaas-bg-hover, #141414);
        }

        .chevron {
            font-size: 12px;
            color: var(--aaas-text-dim, #6b6b6b);
            width: 12px;
            flex-shrink: 0;
            transition: transform 120ms ease;
        }

        .chevron.open {
            transform: rotate(90deg);
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            flex-shrink: 0;
            background: var(--aaas-text-dim, #6b6b6b);
        }

        .status-dot.pending {
            background: var(--aaas-info, #3b82f6);
            animation: pulse 1.2s ease-in-out infinite;
        }

        .status-dot.executing {
            background: var(--aaas-warning, #eab308);
            animation: pulse 1.2s ease-in-out infinite;
        }

        .status-dot.executed {
            background: var(--aaas-success, #22c55e);
        }

        .status-dot.error,
        .status-dot.denied,
        .status-dot.invalid_arguments {
            background: var(--aaas-danger, #ef4444);
        }

        .status-dot.approval_required {
            background: var(--aaas-warning, #eab308);
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.35; }
        }

        .step-name {
            font-family: var(--aaas-font-mono, 'JetBrains Mono', monospace);
            font-size: 12px;
            color: var(--aaas-text-bright, #f8fafc);
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
            letter-spacing: 0.4px;
            padding: 2px 6px;
            border-radius: var(--aaas-radius-sm, 4px);
            background: var(--aaas-bg-base, #1e293b);
            color: var(--aaas-text-dim, #6b6b6b);
        }

        .status-label.executed {
            color: var(--aaas-success, #22c55e);
        }

        .status-label.error,
        .status-label.denied,
        .status-label.invalid_arguments {
            color: var(--aaas-danger, #ef4444);
        }

        .status-label.approval_required,
        .status-label.executing {
            color: var(--aaas-warning, #eab308);
        }

        .duration {
            font-family: var(--aaas-font-mono, 'JetBrains Mono', monospace);
            font-size: 10px;
            color: var(--aaas-text-dim, #6b6b6b);
        }

        .step-body {
            padding: 0 10px 10px 30px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            border-top: 1px solid var(--aaas-border-color, rgba(255,255,255,0.06));
            padding-top: 8px;
        }

        .section-label {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--aaas-text-dim, #6b6b6b);
            margin-bottom: 2px;
        }

        pre {
            margin: 0;
            padding: 8px 10px;
            background: var(--aaas-bg-base, #1e293b);
            border-radius: var(--aaas-radius-sm, 4px);
            font-family: var(--aaas-font-mono, 'JetBrains Mono', monospace);
            font-size: 11px;
            line-height: 1.5;
            color: var(--aaas-text-main, #e2e8f0);
            max-height: 220px;
            overflow: auto;
            white-space: pre-wrap;
            word-break: break-word;
        }

        .error-text {
            color: var(--aaas-danger, #ef4444);
        }

        .approval-row {
            display: flex;
            gap: 8px;
            padding-top: 4px;
        }

        .approval-btn {
            padding: 5px 14px;
            border-radius: var(--aaas-radius-md, 8px);
            border: 1px solid var(--aaas-border-hover, rgba(255,255,255,0.1));
            background: var(--aaas-bg-base, #1e293b);
            color: var(--aaas-text-main, #e2e8f0);
            font-size: 12px;
            cursor: pointer;
            transition: all 120ms ease;
        }

        .approval-btn:hover:not(:disabled) {
            background: var(--aaas-surface-hover, rgba(51,65,85,0.9));
        }

        .approval-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .approval-btn.approve {
            border-color: var(--aaas-success, #22c55e);
            color: var(--aaas-success, #22c55e);
        }

        .approval-btn.deny {
            border-color: var(--aaas-danger, #ef4444);
            color: var(--aaas-danger, #ef4444);
        }

        .empty {
            font-size: 12px;
            color: var(--aaas-text-dim, #6b6b6b);
            padding: 4px 0;
        }

        .memory-id {
            font-family: var(--aaas-font-mono, 'JetBrains Mono', monospace);
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid var(--aaas-info, #3b82f6);
            color: var(--aaas-info, #3b82f6);
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
                <div class="step-header" @click=${() => this._toggle(step.id)}>
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
        'saas-tool-timeline': SaasToolTimeline;
    }
}
