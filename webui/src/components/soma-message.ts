/**
 * SomaAgent01 — Chat message bubble (CH-12 / C2).
 *
 * Role-styled bubble with markdown-ish text, collapsible tool timeline,
 * copy action, timestamps, streaming cursor, and inline error state.
 * Tool timeline binds to WS tool.* payloads via ToolCallStep[] (see
 * soma-tool-timeline.ts for the WS → step mapping).
 */

import { LitElement, html, css, nothing, PropertyValues } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { unsafeHTML } from 'lit/directives/unsafe-html.js';
import type { ToolCallStep } from './soma-tool-timeline.js';
import { renderMarkdown, renderCodeBlock, bindCodeCopy, formatTime, formatBytes } from '../utils/markdown.js';
import './soma-tool-timeline.js';

export type MessageRole = 'user' | 'assistant' | 'system';

@customElement('soma-message')
export class SomaMessage extends LitElement {
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
            max-width: min(88%, 860px);
            animation: msgIn 220ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
        }

        @keyframes msgIn {
            from {
                opacity: 0;
                transform: translateY(10px) scale(0.97) blur(4px);
                filter: blur(4px);
            }
            to {
                opacity: 1;
                transform: none;
                filter: blur(0);
            }
        }

        @media (prefers-reduced-motion: reduce) {
            :host {
                animation: none;
            }
        }

        :host([message-role='user']) {
            align-self: flex-end;
        }

        :host([message-role='system']) {
            align-self: center;
            max-width: 92%;
        }

        .bubble {
            padding: 14px 18px;
            border-radius: 16px;
            font-size: 14.5px;
            line-height: 1.7;
            word-wrap: break-word;
            overflow-wrap: anywhere;
            position: relative;
            overflow: hidden;
        }

        :host([message-role='user']) .bubble {
            background: linear-gradient(135deg, #FF4D00 0%, #FF6A28 55%, #E64500 100%);
            color: #F8FAFC;
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-bottom-right-radius: 6px;
            backdrop-filter: blur(18px) saturate(140%);
            -webkit-backdrop-filter: blur(18px) saturate(140%);
            box-shadow:
                0 1px 0 rgba(255, 255, 255, 0.12) inset,
                0 8px 28px rgba(59, 130, 246, 0.28);
        }

        :host([message-role='assistant']) .bubble {
            background:
                linear-gradient(145deg, rgba(26, 26, 26, 0.82) 0%, rgba(17, 17, 17, 0.92) 100%);
            color: #E8EDF7;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-bottom-left-radius: 6px;
            backdrop-filter: blur(22px) saturate(130%);
            -webkit-backdrop-filter: blur(22px) saturate(130%);
            box-shadow:
                0 1px 0 rgba(255, 255, 255, 0.05) inset,
                0 12px 32px rgba(0, 0, 0, 0.35),
                0 0 0 1px rgba(59, 130, 246, 0.04);
        }

        :host([message-role='system']) .bubble {
            background: #1A1A1A;
            color: #94a3b8;
            font-size: 12px;
            border: 1px dashed rgba(148, 163, 184, 0.28);
            border-radius: 999px;
            padding: 6px 14px;
            box-shadow: none;
        }

        /* ---------- markdown body ---------- */
        .text {
            white-space: normal;
        }

        .text:empty {
            display: none;
        }

        .text :deep(p) {
            margin: 0 0 0.75em;
        }

        .text :deep(p:last-child) {
            margin-bottom: 0;
        }

        .text :deep(.md-h) {
            margin: 0.85em 0 0.4em;
            font-weight: 650;
            line-height: 1.25;
            letter-spacing: -0.01em;
        }

        .text :deep(.md-h1) {
            font-size: 1.4em;
            background: linear-gradient(90deg, #FF4D00, #FF7A3D);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        :host([message-role='user']) .text :deep(.md-h1) {
            background: none;
            color: #fff;
        }

        .text :deep(.md-h2) { font-size: 1.22em; color: #dbeafe; }
        .text :deep(.md-h3) { font-size: 1.1em; color: #e2e8f0; }
        .text :deep(.md-h4),
        .text :deep(.md-h5),
        .text :deep(.md-h6) {
            font-size: 1em;
            color: #cbd5e1;
            text-transform: none;
        }

        :host([message-role='user']) .text :deep(.md-h),
        :host([message-role='user']) .text :deep(.md-h2),
        :host([message-role='user']) .text :deep(.md-h3) {
            color: #fff;
        }

        .text :deep(strong),
        .text :deep(b) {
            font-weight: 650;
            color: #fff;
        }

        :host([message-role='user']) .text :deep(strong) {
            color: #fff;
        }

        .text :deep(em),
        .text :deep(i) {
            opacity: 0.92;
        }

        .text :deep(.md-ul),
        .text :deep(.md-ol) {
            margin: 0 0 0.75em;
            padding-left: 1.25em;
        }

        .text :deep(li) {
            margin: 0.28em 0;
            padding-left: 0.15em;
        }

        .text :deep(.md-ul) {
            list-style: none;
        }

        .text :deep(.md-ul > li) {
            position: relative;
        }

        .text :deep(.md-ul > li::before) {
            content: '';
            position: absolute;
            left: -0.9em;
            top: 0.62em;
            width: 6px;
            height: 6px;
            border-radius: 999px;
            background: #FF4D00;
        }

        :host([message-role='user']) .text :deep(.md-ul > li::before) {
            background: rgba(255, 255, 255, 0.75);
        }

        .text :deep(.md-quote) {
            margin: 0 0 0.8em;
            padding: 10px 14px;
            border-left: 3px solid transparent;
            border-image: linear-gradient(180deg, #FF4D00, #FF7A3D) 1;
            border-radius: 0 12px 12px 0;
            background: linear-gradient(135deg, rgba(255, 77, 0, 0.1), rgba(255, 122, 61, 0.08));
            color: #CBD5E1;
            font-style: italic;
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
        }

        :host([message-role='user']) .text :deep(.md-quote) {
            background: rgba(255, 255, 255, 0.12);
            border-left-color: rgba(255, 255, 255, 0.7);
            color: #fff;
        }

        .text :deep(.md-hr) {
            border: none;
            height: 1px;
            margin: 1em 0;
            background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.35), transparent);
        }

        .text :deep(.md-code) {
            font-family: var(--aaas-font-mono, ui-monospace, 'SF Mono', Menlo, monospace);
            font-size: 0.86em;
            padding: 0.14em 0.42em;
            border-radius: 6px;
            background: #0A0A0A;
            border: 1px solid #2A2A2A;
            color: #FFD0BA;
        }

        :host([message-role='user']) .text :deep(.md-code) {
            background: rgba(0, 0, 0, 0.22);
            border-color: rgba(255, 255, 255, 0.18);
            color: #e0e7ff;
        }

        .text :deep(.md-pre) {
            margin: 0 0 0.85em;
            padding: 12px 14px;
            background: #0A0A0A;
            border: 1px solid #2A2A2A;
            border-radius: 12px;
            overflow-x: auto;
        }

        .text :deep(.md-codeblock-wrap) {
            margin: 0 0 0.9em;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            overflow: hidden;
            background: rgba(10, 10, 10, 0.72);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            box-shadow: 0 10px 28px rgba(0, 0, 0, 0.35);
        }

        .text :deep(.md-codeblock-bar) {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            padding: 7px 12px;
            background: linear-gradient(90deg, #1A1A1A, #111111);
            border-bottom: 1px solid #2A2A2A;
        }

        .text :deep(.md-codeblock-lang) {
            font-family: var(--aaas-font-mono, ui-monospace, monospace);
            font-size: 11px;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            color: #FF7A3D;
        }

        .text :deep(.md-copy-btn) {
            border: 1px solid rgba(148, 163, 184, 0.25);
            background: #1A1A1A;
            color: #cbd5e1;
            font-size: 11px;
            line-height: 1;
            padding: 5px 10px;
            border-radius: 8px;
            cursor: pointer;
            transition: background 120ms ease, color 120ms ease, border-color 120ms ease;
        }

        .text :deep(.md-copy-btn:hover) {
            background: rgba(255, 77, 0, 0.28);
            border-color: #FF4D00;
            color: #e0e7ff;
        }

        .text :deep(.md-codeblock-wrap .md-pre) {
            margin: 0;
            border: 0;
            border-radius: 0;
            background: transparent;
            box-shadow: none;
        }

        .text :deep(.md-codeblock) {
            font-family: var(--aaas-font-mono, ui-monospace, 'SF Mono', Menlo, monospace);
            font-size: 12.5px;
            line-height: 1.6;
            color: #e2e8f0;
            white-space: pre;
        }

        .text :deep(.md-link) {
            color: #FFB088;
            text-decoration: underline;
            text-underline-offset: 3px;
            text-decoration-thickness: 1px;
        }

        .text :deep(.md-link:hover) {
            color: #FFD0BA;
        }

        :host([message-role='user']) .text :deep(.md-link) {
            color: #fff;
        }

        /* tables / cards / generic HTML the model emits */
        .text :deep(table) {
            width: 100%;
            border-collapse: collapse;
            margin: 0 0 0.85em;
            font-size: 13px;
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid #2A2A2A;
        }

        .text :deep(th),
        .text :deep(td) {
            padding: 8px 10px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.12);
            text-align: left;
        }

        .text :deep(th) {
            background: #1A1A1A;
            color: #e2e8f0;
            font-weight: 600;
        }

        .text :deep(tr:last-child td) {
            border-bottom: 0;
        }

        .text :deep(pre),
        .text :deep(code) {
            font-family: var(--aaas-font-mono, ui-monospace, monospace);
        }

        .text :deep(img) {
            max-width: 100%;
            border-radius: 10px;
            margin: 0.4em 0;
        }


        /* ---------- media / documents ---------- */
        .attachments {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 12px;
        }

        .attachment-chip {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            border-radius: 12px;
            background: rgba(18, 18, 18, 0.72);
            border: 1px solid rgba(255, 255, 255, 0.1);
            font-size: 12px;
            color: #E5E5E5;
            max-width: 260px;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.22);
        }

        .attachment-chip .name {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .attachment-chip .kind {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: #FF7A3D;
        }

        :host([message-role='user']) .attachment-chip {
            background: rgba(255, 255, 255, 0.14);
            border-color: rgba(255, 255, 255, 0.22);
            color: #FFFFFF;
        }

        .text :deep(.md-img),
        .text :deep(img) {
            display: block;
            max-width: min(100%, 520px);
            border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin: 10px 0;
            box-shadow: 0 14px 36px rgba(0, 0, 0, 0.35);
        }

        .text :deep(.md-file-card),
        .text :deep(.file-card) {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 10px 0;
            padding: 12px 14px;
            border-radius: 14px;
            background: linear-gradient(145deg, rgba(18, 18, 18, 0.9), rgba(10, 10, 10, 0.85));
            border: 1px solid rgba(255, 77, 0, 0.18);
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.3);
        }

        .text :deep(.file-card .icon) {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: grid;
            place-items: center;
            background: rgba(255, 77, 0, 0.14);
            color: #FF4D00;
            font-size: 20px;
        }

        .text :deep(.file-card .meta) {
            display: flex;
            flex-direction: column;
            gap: 2px;
            min-width: 0;
        }

        .text :deep(.file-card .title) {
            color: #FFFFFF;
            font-size: 13px;
            font-weight: 600;
        }

        .text :deep(.file-card .sub) {
            color: #94A3B8;
            font-size: 11px;
        }

        /* streaming cursor */

        .cursor {
            display: inline-block;
            width: 8px;
            height: 15px;
            margin-left: 3px;
            vertical-align: text-bottom;
            border-radius: 2px;
            background: linear-gradient(180deg, #FF4D00, #FF7A3D);
            animation: blink 1s step-end infinite;
        }

        @keyframes blink {
            50% {
                opacity: 0;
            }
        }

        /* ---------- tools ---------- */
        .tools {
            margin-bottom: 10px;
        }

        .tools-toggle {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 10px;
            margin-bottom: 8px;
            border-radius: 999px;
            border: 1px solid #2A2A2A;
            background: #1A1A1A;
            color: #94a3b8;
            font-size: 11.5px;
            cursor: pointer;
            transition: color 140ms ease, background 140ms ease, border-color 140ms ease;
        }

        .tools-toggle:hover {
            color: #e2e8f0;
            background: #1A1A1A;
            border-color: #FF4D00;
        }

        .tools-toggle:focus-visible {
            outline: 2px solid #60a5fa;
            outline-offset: 2px;
        }

        .tools-toggle .chev {
            font-size: 11px;
            transition: transform 160ms ease;
        }

        .tools-toggle .chev.open {
            transform: rotate(90deg);
        }

        /* ---------- attachments ---------- */
        .attachments {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 10px;
        }

        .attachment-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 10px;
            border-radius: 10px;
            background: #1A1A1A;
            border: 1px solid #2A2A2A;
            font-size: 11.5px;
            color: #cbd5e1;
            max-width: 220px;
        }

        .attachment-chip .name {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        :host([message-role='user']) .attachment-chip {
            background: rgba(0, 0, 0, 0.18);
            border-color: rgba(255, 255, 255, 0.18);
            color: #fff;
        }

        /* ---------- inline error ---------- */
        .inline-error {
            display: flex;
            align-items: flex-start;
            gap: 8px;
            margin-top: 10px;
            padding: 10px 12px;
            border-radius: 10px;
            background: rgba(239, 68, 68, 0.12);
            border: 1px solid rgba(239, 68, 68, 0.35);
            color: #fca5a5;
            font-size: 12.5px;
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
            color: #64748b;
        }

        :host([message-role='user']) .time {
            opacity: 0.75;
        }

        .stopped-badge {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.4px;
            color: #fbbf24;
            border: 1px solid rgba(251, 191, 36, 0.45);
            border-radius: 6px;
            padding: 1px 6px;
        }

        .confidence-wrap {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            color: #64748b;
        }

        .confidence-bar {
            width: 56px;
            height: 3px;
            background: rgba(148, 163, 184, 0.2);
            border-radius: 999px;
            overflow: hidden;
        }

        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, #10B981, #34D399);
            border-radius: 999px;
        }

        .actions {
            margin-left: auto;
            display: flex;
            gap: 4px;
            opacity: 0;
            transition: opacity 140ms ease;
        }

        :host(:hover) .actions,
        :host(:focus-within) .actions {
            opacity: 1;
        }

        .action-btn {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 3px 8px;
            border-radius: 8px;
            border: none;
            background: transparent;
            color: #64748b;
            font-size: 11px;
            cursor: pointer;
            transition: all 120ms ease;
        }

        .action-btn:hover {
            background: #1A1A1A;
            color: #e2e8f0;
        }

        .action-btn:focus-visible {
            outline: 2px solid #60a5fa;
            outline-offset: 1px;
        }
    `;

    protected willUpdate(changed: PropertyValues) {
        if (changed.has('text') || changed.has('messageRole')) {
            // User bubbles stay plain text — no markdown surface for user input.
            // Assistant bubbles render through the onCodeBlock hook so every
            // fenced block gets a language chip and a working copy button.
            this._renderedHtml = this.messageRole === 'user'
                ? ''
                : renderMarkdown(this.text, { onCodeBlock: renderCodeBlock });
        }
    }

    private _unbindCodeCopy: (() => void) | null = null;

    override connectedCallback() {
        super.connectedCallback();
        // Delegated copy: markdown HTML is injected via unsafeHTML, so the
        // button cannot carry a Lit listener. Bind one handler on the host.
        this._unbindCodeCopy = bindCodeCopy(this);
    }

    override disconnectedCallback() {
        this._unbindCodeCopy?.();
        this._unbindCodeCopy = null;
        super.disconnectedCallback();
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
            console.warn('[SomaMessage] clipboard write failed', err);
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
                            <soma-tool-timeline .steps=${this.tools}></soma-tool-timeline>
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
        'soma-message': SomaMessage;
    }
}
