/**
 * SomaAgent01 — Chat message bubble (CH-12 / C2).
 *
 * Role-styled bubble with markdown-ish text, collapsible tool timeline,
 * copy action, timestamps, streaming cursor, and inline error state.
 * Tool timeline binds to WS tool.* payloads via ToolCallStep[] (see
 * saas-tool-timeline.ts for the WS → step mapping).
 */

import { LitElement, html, css, nothing, PropertyValues } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { unsafeHTML } from 'lit/directives/unsafe-html.js';
import type { ToolCallStep } from './saas-tool-timeline.js';
import { renderMarkdown, formatTime, formatBytes } from '../utils/markdown.js';
import './saas-tool-timeline.js';

export type MessageRole = 'user' | 'assistant' | 'system';

@customElement('saas-message')
export class SaasMessage extends LitElement {
    /** Message role. Deliberately not `role` — that is the native ARIA attribute. */
    @property({ type: String, attribute: 'message-role' }) messageRole: MessageRole = 'assistant';
    @property({ type: String }) text = '';
    @property({ type: String }) timestamp = '';
    @property({ type: Array }) tools: ToolCallStep[] = [];
    @property({ type: Boolean }) streaming = false;
    @property({ type: Boolean }) stopped = false;
    @property({ type: Number }) confidence?: number;
    /** Inline error for this message (not a global banner). */
    @property({ type: String }) error = '';
    /** Optional attachment chips: {name, type, size} */
    @property({ type: Array }) attachments: { name: string; type?: string; size?: number }[] = [];

    @state() private _copied = false;
    @state() private _toolsExpanded = true;

    private _renderedHtml = '';

    static styles = css`
        :host {
            display: block;
            max-width: min(85%, 820px);
        }

        :host([message-role='user']) {
            align-self: flex-end;
        }

        :host([message-role='system']) {
            align-self: center;
            max-width: 90%;
        }

        .bubble {
            padding: 12px 16px;
            border-radius: var(--aaas-radius-lg, 12px);
            font-size: 14px;
            line-height: 1.65;
            word-wrap: break-word;
            overflow-wrap: anywhere;
            position: relative;
        }

        :host([message-role='user']) .bubble {
            background: var(--aaas-accent, #e8e4dc);
            color: var(--aaas-text-inverse, #1a1a1a);
            border: 1px solid var(--aaas-border-color, rgba(255,255,255,0.06));
            border-bottom-right-radius: 4px;
        }

        :host([message-role='assistant']) .bubble {
            background: var(--aaas-bg-card, #1e1e1e);
            color: var(--aaas-text-main, #e2e8f0);
            border: 1px solid var(--aaas-border-color, rgba(255,255,255,0.06));
            border-bottom-left-radius: 4px;
        }

        :host([message-role='system']) .bubble {
            background: transparent;
            color: var(--aaas-text-dim, #64748b);
            font-size: 12px;
            border: 1px dashed var(--aaas-border-color, rgba(255,255,255,0.06));
            border-radius: var(--aaas-radius-full, 9999px);
            padding: 6px 14px;
        }

        /* ---------- markdown ---------- */
        .text {
            white-space: normal;
        }

        .text:empty {
            display: none;
        }

        .text :deep(p) {
            margin: 0 0 0.7em;
        }

        .text :deep(p:last-child) {
            margin-bottom: 0;
        }

        .text :deep(.md-h) {
            margin: 0.6em 0 0.35em;
            font-weight: 600;
            line-height: 1.3;
        }

        .text :deep(.md-h1) { font-size: 1.35em; }
        .text :deep(.md-h2) { font-size: 1.2em; }
        .text :deep(.md-h3) { font-size: 1.08em; }
        .text :deep(.md-h4),
        .text :deep(.md-h5),
        .text :deep(.md-h6) { font-size: 1em; }

        .text :deep(.md-ul),
        .text :deep(.md-ol) {
            margin: 0 0 0.7em;
            padding-left: 1.35em;
        }

        .text :deep(li) {
            margin: 0.2em 0;
        }

        .text :deep(.md-quote) {
            margin: 0 0 0.7em;
            padding: 4px 12px;
            border-left: 3px solid var(--aaas-accent, #e8e4dc);
            color: var(--aaas-text-secondary, #a1a1a1);
            opacity: 0.95;
        }

        .text :deep(.md-hr) {
            border: none;
            border-top: 1px solid var(--aaas-border-color, rgba(255,255,255,0.06));
            margin: 0.9em 0;
        }

        .text :deep(.md-code) {
            font-family: var(--aaas-font-mono, 'JetBrains Mono', monospace);
            font-size: 0.88em;
            padding: 0.12em 0.38em;
            border-radius: var(--aaas-radius-sm, 4px);
            background: var(--aaas-bg-void, #f5f5f5);
            border: 1px solid var(--aaas-border-color, rgba(255,255,255,0.06));
        }

        :host([message-role='user']) .text :deep(.md-code) {
            background: rgba(0, 0, 0, 0.14);
            border-color: rgba(0, 0, 0, 0.12);
        }

        .text :deep(.md-pre) {
            margin: 0 0 0.7em;
            padding: 10px 12px;
            background: var(--aaas-bg-void, #f5f5f5);
            border: 1px solid var(--aaas-border-color, rgba(255,255,255,0.06));
            border-radius: var(--aaas-radius-md, 8px);
            overflow-x: auto;
        }

        .text :deep(.md-codeblock) {
            font-family: var(--aaas-font-mono, 'JetBrains Mono', monospace);
            font-size: 12px;
            line-height: 1.55;
            color: var(--aaas-text-main, #e2e8f0);
            white-space: pre;
        }

        .text :deep(.md-link) {
            color: var(--aaas-info, #3b82f6);
            text-decoration: underline;
            text-underline-offset: 2px;
        }

        :host([message-role='user']) .text :deep(.md-link) {
            color: inherit;
        }

        /* ---------- streaming cursor ---------- */
        .cursor {
            display: inline-block;
            width: 7px;
            height: 14px;
            margin-left: 2px;
            vertical-align: text-bottom;
            background: var(--aaas-accent, #e8e4dc);
            animation: blink 1s step-end infinite;
        }

        @keyframes blink {
            50% { opacity: 0; }
        }

        /* ---------- tools ---------- */
        .tools {
            margin-bottom: 10px;
        }

        .tools-toggle {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 3px 8px;
            margin-bottom: 6px;
            border-radius: var(--aaas-radius-full, 9999px);
            border: 1px solid var(--aaas-border-color, rgba(255,255,255,0.06));
            background: var(--aaas-bg-void, #f5f5f5);
            color: var(--aaas-text-dim, #64748b);
            font-size: 11px;
            cursor: pointer;
            transition: color 120ms ease, background 120ms ease;
        }

        .tools-toggle:hover {
            color: var(--aaas-text-main, #e2e8f0);
            background: var(--aaas-bg-hover, #141414);
        }

        .tools-toggle:focus-visible {
            outline: 2px solid var(--aaas-info, #3b82f6);
            outline-offset: 1px;
        }

        .tools-toggle .chev {
            font-size: 10px;
            transition: transform 120ms ease;
        }

        .tools-toggle .chev.open {
            transform: rotate(90deg);
        }

        /* ---------- attachments ---------- */
        .attachments {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 8px;
        }

        .attachment-chip {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 4px 9px;
            border-radius: var(--aaas-radius-md, 8px);
            background: var(--aaas-bg-void, #f5f5f5);
            border: 1px solid var(--aaas-border-color, rgba(255,255,255,0.06));
            font-size: 11px;
            color: var(--aaas-text-secondary, #a1a1a1);
            max-width: 220px;
        }

        .attachment-chip .name {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        :host([message-role='user']) .attachment-chip {
            background: rgba(0, 0, 0, 0.12);
            border-color: rgba(0, 0, 0, 0.1);
            color: inherit;
        }

        /* ---------- inline error ---------- */
        .inline-error {
            display: flex;
            align-items: flex-start;
            gap: 8px;
            margin-top: 8px;
            padding: 8px 10px;
            border-radius: var(--aaas-radius-md, 8px);
            background: rgba(239, 68, 68, 0.12);
            border: 1px solid rgba(239, 68, 68, 0.32);
            color: var(--aaas-danger, #ef4444);
            font-size: 12px;
            line-height: 1.45;
        }

        .inline-error .icon {
            font-size: 14px;
            line-height: 1.3;
            flex-shrink: 0;
        }

        /* ---------- footer ---------- */
        .footer {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 8px;
            min-height: 18px;
        }

        .time {
            font-size: 11px;
            color: var(--aaas-text-dim, #64748b);
        }

        :host([message-role='user']) .time {
            opacity: 0.7;
        }

        .stopped-badge {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.4px;
            color: var(--aaas-warning, #eab308);
            border: 1px solid var(--aaas-warning, #eab308);
            border-radius: var(--aaas-radius-sm, 4px);
            padding: 1px 6px;
        }

        .confidence-wrap {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            color: var(--aaas-text-dim, #64748b);
        }

        .confidence-bar {
            width: 56px;
            height: 3px;
            background: var(--aaas-bg-void, #f5f5f5);
            border-radius: var(--aaas-radius-full, 9999px);
            overflow: hidden;
        }

        .confidence-fill {
            height: 100%;
            background: var(--aaas-success, #22c55e);
            border-radius: var(--aaas-radius-full, 9999px);
        }

        .actions {
            margin-left: auto;
            display: flex;
            gap: 4px;
        }

        .action-btn {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 2px 8px;
            border-radius: var(--aaas-radius-sm, 4px);
            border: none;
            background: transparent;
            color: var(--aaas-text-dim, #64748b);
            font-size: 11px;
            cursor: pointer;
            transition: all 120ms ease;
        }

        .action-btn:hover {
            background: var(--aaas-bg-hover, #141414);
            color: var(--aaas-text-main, #e2e8f0);
        }

        .action-btn:focus-visible {
            outline: 2px solid var(--aaas-info, #3b82f6);
            outline-offset: 1px;
        }

        :host([message-role='user']) .action-btn {
            color: inherit;
            opacity: 0.7;
        }

        :host([message-role='user']) .action-btn:hover {
            opacity: 1;
            background: rgba(0, 0, 0, 0.1);
        }
    `;

    protected willUpdate(changed: PropertyValues) {
        if (changed.has('text') || changed.has('messageRole')) {
            // User bubbles stay plain text — no markdown surface for user input.
            this._renderedHtml = this.messageRole === 'user'
                ? ''
                : renderMarkdown(this.text);
        }
    }

    private async _copy() {
        const payload = this.text || '';
        if (!payload) return;
        try {
            await navigator.clipboard.writeText(payload);
            this._copied = true;
            setTimeout(() => {
                this._copied = false;
            }, 1500);
        } catch (err) {
            console.warn('[SaasMessage] clipboard write failed', err);
        }
    }

    private _toggleTools() {
        this._toolsExpanded = !this._toolsExpanded;
    }

    private _formatTime(iso: string): string {
        return formatTime(iso);
    }

    render() {
        const hasTools = this.tools && this.tools.length > 0;
        const showFooter =
            !!this.timestamp ||
            this.stopped ||
            this.confidence != null ||
            this.messageRole === 'assistant' ||
            this.messageRole === 'user';

        return html`
            <div class="bubble">
                ${hasTools ? html`
                    <div class="tools">
                        <button
                            class="tools-toggle"
                            @click=${this._toggleTools}
                            aria-expanded=${this._toolsExpanded ? 'true' : 'false'}
                            title=${this._toolsExpanded ? 'Collapse tool activity' : 'Expand tool activity'}
                        >
                            <span class="chev ${this._toolsExpanded ? 'open' : ''}">▶</span>
                            <span>${this.tools.length} tool${this.tools.length === 1 ? '' : 's'}</span>
                        </button>
                        ${this._toolsExpanded ? html`
                            <saas-tool-timeline .steps=${this.tools}></saas-tool-timeline>
                        ` : nothing}
                    </div>
                ` : nothing}
                <slot name="tools"></slot>

                ${this.attachments.length > 0 ? html`
                    <div class="attachments">
                        ${this.attachments.map((a) => html`
                            <span class="attachment-chip" title=${a.name}>
                                <span class="material-symbols-outlined" style="font-size:14px">attach_file</span>
                                <span class="name">${a.name}</span>
                                ${a.size ? html`<span>${formatBytes(a.size)}</span>` : nothing}
                            </span>
                        `)}
                    </div>
                ` : nothing}

                ${this.messageRole === 'user'
                    ? html`<div class="text">${this.text}</div>`
                    : html`<div class="text">${unsafeHTML(this._renderedHtml)}</div>`}
                ${this.streaming ? html`<span class="cursor" aria-hidden="true"></span>` : nothing}

                ${this.error ? html`
                    <div class="inline-error" role="alert">
                        <span class="material-symbols-outlined icon">error</span>
                        <span>${this.error}</span>
                    </div>
                ` : nothing}

                ${showFooter ? html`
                    <div class="footer">
                        ${this.timestamp ? html`<span class="time">${this._formatTime(this.timestamp)}</span>` : nothing}
                        ${this.stopped ? html`<span class="stopped-badge">stopped</span>` : nothing}
                        ${this.confidence != null ? html`
                            <span class="confidence-wrap" title="Response confidence">
                                <span class="confidence-bar">
                                    <span class="confidence-fill" style="width:${Math.round(this.confidence * 100)}%"></span>
                                </span>
                                <span>${Math.round(this.confidence * 100)}%</span>
                            </span>
                        ` : nothing}
                        ${this.messageRole !== 'system' && this.text ? html`
                            <div class="actions">
                                <button
                                    class="action-btn"
                                    @click=${this._copy}
                                    title="Copy message text"
                                    aria-label="Copy message text"
                                >
                                    <span class="material-symbols-outlined" style="font-size:13px">
                                        ${this._copied ? 'check' : 'content_copy'}
                                    </span>
                                    ${this._copied ? 'Copied' : 'Copy'}
                                </button>
                            </div>
                        ` : nothing}
                    </div>
                ` : nothing}
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-message': SaasMessage;
    }
}
