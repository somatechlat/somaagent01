/**
 * SomaAgent01 — Chat message bubble (CH-12 / C2).
 *
 * Role-styled bubble with markdown-ish text, collapsible tool timeline,
 * copy action, timestamps, streaming cursor, and inline error state.
 * Tool timeline binds to WS tool.* payloads via ToolCallStep[] (see
 * soma-tool-timeline.ts for the WS → step mapping).
 *
 * Attachments with a real filesv2 `file_id` resolve a download URL and
 * render as media (image / audio / video) or a download card. Attachments
 * without one, or whose URL cannot be resolved, render an honest
 * "preview unavailable" card — never a broken frame.
 */

import { LitElement, html, css, nothing, PropertyValues } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { unsafeHTML } from 'lit/directives/unsafe-html.js';
import type { ToolCallStep } from './soma-tool-timeline.js';
import { renderMarkdown, renderCodeBlock, bindCodeCopy, formatTime, formatBytes } from '../utils/markdown.js';
import { apiClient } from '../services/api-client.js';
import { attachmentIcon } from '../utils/file-icons.js';
import {
    CHAT_PREFS_EVENT,
    getChatPrefs,
    type ChatPrefs,
    type ToolIconKey,
} from '../services/chat-prefs.js';
import './soma-tool-timeline.js';

/** Material icon for a file attachment — delegated to shared util (no emojis). */

function isImageAttachment(name: string, type?: string): boolean {
    const t = (type || '').toLowerCase();
    return t.startsWith('image/') || /\.(png|jpe?g|gif|webp|avif|bmp)$/.test((name || '').toLowerCase());
}

function isAudioAttachment(name: string, type?: string): boolean {
    const t = (type || '').toLowerCase();
    return t.startsWith('audio/') || /\.(mp3|wav|ogg|m4a|flac)$/.test((name || '').toLowerCase());
}

function isVideoAttachment(name: string, type?: string): boolean {
    const t = (type || '').toLowerCase();
    return t.startsWith('video/') || /\.(mp4|webm|mov|mkv)$/.test((name || '').toLowerCase());
}

export type MessageRole = 'user' | 'assistant' | 'system';

/** Turn chips from `chat.turn_meta` — only fields the server sent. */
export interface MessageTurnMeta {
    model?: string;
    memoryHits?: { text?: string; score?: number | null; kind?: string | null }[];
    contextTokens?: number;
    contextWindow?: number;
}

interface AttachmentInput {
    name: string;
    type?: string;
    size?: number;
    file_id?: string;
}

/** Resolved media URL state per attachment (honest, never guessed). */
interface AttachmentMedia {
    url: string | null;
    /** 'ok' | 'pending' | 'unavailable' */
    state: 'pending' | 'ok' | 'unavailable';
}

@customElement('soma-message')
export class SomaMessage extends LitElement {
    /** Message role. Deliberately not `role` — that is the native ARIA attribute. */
    @property({ type: String, attribute: 'message-role' }) messageRole: MessageRole = 'assistant';
    @property({ type: String }) text = '';
    @property({ type: String }) timestamp = '';
    @property({ type: Array }) tools: ToolCallStep[] = [];
    @property({ type: Boolean }) streaming = false;
    /** True while waiting for the first token — renders a typing indicator. */
    @property({ type: Boolean }) thinking = false;
    @property({ type: Boolean }) stopped = false;
    @property({ type: Number }) confidence?: number;
    /** Inline error for this message (not a global banner). */
    @property({ type: String }) error = '';
    /** Optional attachment chips: {name, type, size, file_id} */
    @property({ type: Array }) attachments: AttachmentInput[] = [];
    /** turn_meta chips for the turn that produced this bubble. */
    @property({ type: Object }) turnMeta?: MessageTurnMeta;

    @state() private _copied = false;
    @state() private _toolsExpanded = true;
    @state() private _media: Record<string, AttachmentMedia> = {};
    @state() private _prefs: ChatPrefs = getChatPrefs();
    private _prefsOff?: () => void;

    private _renderedHtml = '';
    private _mediaRequested = new Set<string>();

    static styles = css`
        :host {
            display: block;
            max-width: min(88%, 860px);
            animation: msgIn 240ms cubic-bezier(0.22, 0.85, 0.25, 1) both;
        }

        @keyframes msgIn {
            from {
                opacity: 0;
                transform: translateY(8px) scale(0.985);
            }
            to {
                opacity: 1;
                transform: none;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            :host {
                animation: none;
            }
            .cursor {
                animation: none;
                opacity: 1;
            }
            .tools-toggle .chev,
            .action-btn,
            .tools-toggle {
                transition: none;
            }
        }

        :host([message-role='user']) {
            align-self: flex-end;
        }

        :host([message-role='system']) {
            align-self: center;
            max-width: 92%;
        }

        /* ---------- bubble ---------- */
        .bubble {
            padding: 14px 18px;
            border-radius: 18px;
            font-size: 14.5px;
            line-height: 1.72;
            letter-spacing: 0.005em;
            word-wrap: break-word;
            overflow-wrap: anywhere;
            position: relative;
        }

        :host([message-role='user']) .bubble {
            background: linear-gradient(145deg, #FF5A14 0%, #FF6E30 48%, #E84800 100%);
            color: #FFF7F3;
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-bottom-right-radius: 7px;
            box-shadow:
                0 1px 0 rgba(255, 255, 255, 0.14) inset,
                0 8px 22px rgba(232, 72, 0, 0.28),
                0 2px 6px rgba(0, 0, 0, 0.12);
        }

        :host([message-role='assistant']) .bubble {
            background: linear-gradient(160deg, rgba(28, 28, 30, 0.94) 0%, rgba(18, 18, 20, 0.97) 100%);
            color: #EAEFF7;
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-bottom-left-radius: 7px;
            box-shadow:
                0 1px 0 rgba(255, 255, 255, 0.04) inset,
                0 10px 28px rgba(0, 0, 0, 0.32),
                0 1px 3px rgba(0, 0, 0, 0.18);
        }

        :host([message-role='system']) .bubble {
            background: rgba(26, 26, 28, 0.9);
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
            margin: 0 0 0.78em;
        }

        .text :deep(p:last-child) {
            margin-bottom: 0;
        }

        .text :deep(.md-h) {
            margin: 0.9em 0 0.42em;
            font-weight: 650;
            line-height: 1.28;
            letter-spacing: -0.012em;
        }

        .text :deep(.md-h1) {
            font-size: 1.38em;
            background: linear-gradient(92deg, #FF5A14, #FF8A52);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        :host([message-role='user']) .text :deep(.md-h1) {
            background: none;
            color: #fff;
        }

        .text :deep(.md-h2) { font-size: 1.2em; color: #dce8f8; }
        .text :deep(.md-h3) { font-size: 1.08em; color: #e4ecf6; }
        .text :deep(.md-h4),
        .text :deep(.md-h5),
        .text :deep(.md-h6) {
            font-size: 1em;
            color: #c9d4e2;
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
            margin: 0 0 0.78em;
            padding-left: 1.25em;
        }

        .text :deep(li) {
            margin: 0.3em 0;
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
            top: 0.64em;
            width: 6px;
            height: 6px;
            border-radius: 999px;
            background: #FF5A14;
        }

        :host([message-role='user']) .text :deep(.md-ul > li::before) {
            background: rgba(255, 255, 255, 0.78);
        }

        .text :deep(.md-quote) {
            margin: 0 0 0.85em;
            padding: 10px 14px;
            border-left: 3px solid #FF5A14;
            border-radius: 0 12px 12px 0;
            background: rgba(255, 90, 20, 0.08);
            color: #C8D2E0;
            font-style: italic;
        }

        :host([message-role='user']) .text :deep(.md-quote) {
            background: rgba(255, 255, 255, 0.12);
            border-left-color: rgba(255, 255, 255, 0.7);
            color: #fff;
        }

        .text :deep(.md-hr) {
            border: none;
            height: 1px;
            margin: 1.05em 0;
            background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.32), transparent);
        }

        .text :deep(.md-code) {
            font-family: var(--platform-font-mono, ui-monospace, 'SF Mono', Menlo, monospace);
            font-size: 0.86em;
            padding: 0.14em 0.42em;
            border-radius: 6px;
            background: #0C0C0E;
            border: 1px solid #2A2A2E;
            color: #FFD0BA;
        }

        :host([message-role='user']) .text :deep(.md-code) {
            background: rgba(0, 0, 0, 0.22);
            border-color: rgba(255, 255, 255, 0.18);
            color: #ffe8dc;
        }

        .text :deep(.md-pre) {
            margin: 0 0 0.85em;
            padding: 12px 14px;
            background: #0A0A0C;
            border: 1px solid #2A2A2E;
            border-radius: 12px;
            overflow-x: auto;
        }

        .text :deep(.md-codeblock-wrap) {
            margin: 0 0 0.95em;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            overflow: hidden;
            background: rgba(10, 10, 12, 0.92);
            box-shadow: 0 10px 26px rgba(0, 0, 0, 0.28);
        }

        .text :deep(.md-codeblock-bar) {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            padding: 7px 12px;
            background: linear-gradient(90deg, #1A1A1E, #121216);
            border-bottom: 1px solid #2A2A2E;
        }

        .text :deep(.md-codeblock-lang) {
            font-family: var(--platform-font-mono, ui-monospace, monospace);
            font-size: 11px;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: #FF8A52;
        }

        .text :deep(.md-copy-btn) {
            border: 1px solid rgba(148, 163, 184, 0.25);
            background: #1A1A1E;
            color: #cbd5e1;
            font-size: 11px;
            line-height: 1;
            padding: 5px 10px;
            border-radius: 8px;
            cursor: pointer;
            transition: background 120ms ease, color 120ms ease, border-color 120ms ease;
        }

        .text :deep(.md-copy-btn:hover) {
            background: rgba(255, 90, 20, 0.22);
            border-color: #FF5A14;
            color: #ffe8dc;
        }

        .text :deep(.md-codeblock-wrap .md-pre) {
            margin: 0;
            border: 0;
            border-radius: 0;
            background: transparent;
            box-shadow: none;
        }

        .text :deep(.md-codeblock) {
            font-family: var(--platform-font-mono, ui-monospace, 'SF Mono', Menlo, monospace);
            font-size: 12.5px;
            line-height: 1.62;
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
            margin: 0 0 0.9em;
            font-size: 13px;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #2A2A2E;
        }

        .text :deep(th),
        .text :deep(td) {
            padding: 8px 10px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.12);
            text-align: left;
        }

        .text :deep(th) {
            background: #1A1A1E;
            color: #e2e8f0;
            font-weight: 600;
        }

        .text :deep(tr:last-child td) {
            border-bottom: 0;
        }

        .text :deep(pre),
        .text :deep(code) {
            font-family: var(--platform-font-mono, ui-monospace, monospace);
        }

        .text :deep(img) {
            max-width: 100%;
            border-radius: 12px;
            margin: 0.4em 0;
        }

        /* ---------- turn chips (model / recall / ctx) ---------- */
        .turn-chips {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 6px;
            margin-bottom: 10px;
        }

        .chip {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 3px 9px;
            border-radius: 999px;
            font-size: 11px;
            line-height: 1.35;
            letter-spacing: 0.01em;
            border: 1px solid rgba(255, 255, 255, 0.08);
            background: rgba(255, 255, 255, 0.04);
            color: #A8B4C4;
            white-space: nowrap;
            max-width: 220px;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .chip .material-symbols-outlined {
            font-size: 13px;
            opacity: 0.85;
        }

        .chip.model {
            border-color: rgba(16, 185, 129, 0.35);
            color: #6EE7B7;
        }

        .chip.model .live {
            font-size: 9px;
            font-weight: 700;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            color: #10B981;
            border: 1px solid rgba(16, 185, 129, 0.5);
            border-radius: 999px;
            padding: 0 5px;
        }

        .chip.recall {
            border-color: rgba(59, 130, 246, 0.32);
            color: #93C5FD;
        }

        .chip.ctx-ok { border-color: rgba(16, 185, 129, 0.3); color: #6EE7B7; }
        .chip.ctx-mid { border-color: rgba(251, 191, 36, 0.32); color: #FCD34D; }
        .chip.ctx-high { border-color: rgba(248, 113, 113, 0.35); color: #FCA5A5; }

        .chip-hit {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 10px;
            border-radius: 10px;
            font-size: 11px;
            line-height: 1.4;
            border: 1px solid rgba(59, 130, 246, 0.22);
            background: rgba(59, 130, 246, 0.08);
            color: #B6C8DE;
            max-width: 100%;
        }

        .chip-hit .score {
            flex-shrink: 0;
            font-variant-numeric: tabular-nums;
            color: #93C5FD;
            font-weight: 600;
        }

        .chip-hit .hit-text {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            min-width: 0;
        }

        /* ---------- media / documents ---------- */
        .attachments {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 12px;
        }

        .attachment-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }

        .attachment-card {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 0;
            padding: 10px 12px;
            border-radius: 14px;
            max-width: 300px;
            background: rgba(18, 18, 20, 0.92);
            border: 1px solid rgba(255, 90, 20, 0.2);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.22);
            color: #E8E8EC;
        }

        .attachment-card.is-image {
            border-color: rgba(52, 211, 153, 0.26);
        }

        .attachment-card.is-unavailable {
            border-color: rgba(148, 163, 184, 0.22);
            border-style: dashed;
            opacity: 0.92;
        }

        .attachment-card .file-icon {
            flex: 0 0 auto;
            width: 40px;
            height: 40px;
            border-radius: 11px;
            display: grid;
            place-items: center;
            background: rgba(255, 90, 20, 0.13);
            color: #FF8A52;
        }

        .attachment-card.is-image .file-icon {
            background: rgba(52, 211, 153, 0.13);
            color: #34d399;
        }

        .attachment-card.is-unavailable .file-icon {
            background: rgba(148, 163, 184, 0.12);
            color: #94a3b8;
        }

        .attachment-card .file-icon .material-symbols-outlined {
            font-size: 20px;
        }

        .attachment-card .file-meta {
            display: flex;
            flex-direction: column;
            gap: 2px;
            min-width: 0;
        }

        .attachment-card .name {
            font-size: 12px;
            font-weight: 600;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            color: #F5F5F7;
        }

        .attachment-card .sub {
            font-size: 11px;
            color: #A3A3AC;
            text-transform: lowercase;
            letter-spacing: 0.02em;
        }

        .attachment-card a.download {
            color: #FFB088;
            font-size: 11px;
            text-decoration: underline;
            text-underline-offset: 2px;
        }

        .media-frame {
            margin: 0;
            border-radius: 14px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.08);
            background: rgba(10, 10, 12, 0.6);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.28);
            max-width: min(100%, 520px);
        }

        .media-frame img {
            display: block;
            width: 100%;
            max-height: 420px;
            object-fit: contain;
            background: #0A0A0C;
        }

        .media-frame audio {
            display: block;
            width: min(100%, 420px);
            padding: 12px 14px;
        }

        .media-frame video {
            display: block;
            width: 100%;
            max-height: 420px;
            background: #000;
        }

        .media-frame figcaption {
            padding: 8px 12px;
            font-size: 11px;
            color: #94A3B8;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .media-frame figcaption .name {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            color: #E2E8F0;
            font-weight: 500;
        }

        .media-pending {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 14px;
            border-radius: 12px;
            border: 1px dashed rgba(148, 163, 184, 0.25);
            color: #94A3B8;
            font-size: 12px;
        }

        :host([message-role='user']) .attachment-card {
            background: rgba(255, 255, 255, 0.12);
            border-color: rgba(255, 255, 255, 0.22);
            color: #fff;
        }

        :host([message-role='user']) .attachment-card .name {
            color: #fff;
        }

        :host([message-role='user']) .attachment-card .sub {
            color: rgba(255, 255, 255, 0.72);
        }

        :host([message-role='user']) .attachment-card .file-icon {
            background: rgba(255, 255, 255, 0.16);
            color: #fff;
        }

        /* ---------- typing / thinking ---------- */
        .typing {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 6px 2px 2px;
        }

        .typing span {
            width: 7px;
            height: 7px;
            border-radius: 999px;
            background: #FF8A52;
            opacity: 0.35;
            animation: typingPulse 1.2s ease-in-out infinite;
        }

        .typing span:nth-child(2) { animation-delay: 0.15s; }
        .typing span:nth-child(3) { animation-delay: 0.3s; }

        @keyframes typingPulse {
            0%, 100% { opacity: 0.3; transform: translateY(0); }
            50% { opacity: 1; transform: translateY(-2px); }
        }

        @media (prefers-reduced-motion: reduce) {
            .typing span {
                animation: none;
                opacity: 0.7;
            }
        }

        /* streaming cursor */
        .cursor {
            display: inline-block;
            width: 7px;
            height: 1.05em;
            margin-left: 3px;
            vertical-align: text-bottom;
            border-radius: 2px;
            background: linear-gradient(180deg, #FF5A14, #FF8A52);
            animation: blink 1s step-end infinite;
        }

        @keyframes blink {
            50% {
                opacity: 0;
            }
        }

        /* ---------- tools ---------- */
        .tools {
            margin-bottom: 12px;
        }

        .tools-toggle {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 11px;
            margin-bottom: 8px;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            background: rgba(255, 255, 255, 0.04);
            color: #94a3b8;
            font-size: 11.5px;
            cursor: pointer;
            transition: color 140ms ease, background 140ms ease, border-color 140ms ease;
        }

        .tools-toggle:hover {
            color: #e2e8f0;
            background: rgba(255, 90, 20, 0.1);
            border-color: rgba(255, 90, 20, 0.45);
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

        /* ---------- inline error ---------- */
        .inline-error {
            display: flex;
            align-items: flex-start;
            gap: 8px;
            margin-top: 10px;
            padding: 10px 12px;
            border-radius: 12px;
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.32);
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
            margin-top: 10px;
            min-height: 18px;
        }

        .time {
            font-size: 11px;
            color: #64748b;
            font-variant-numeric: tabular-nums;
        }

        :host([message-role='user']) .time {
            opacity: 0.78;
        }

        .stopped-badge {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.45px;
            color: #fbbf24;
            border: 1px solid rgba(251, 191, 36, 0.4);
            border-radius: 6px;
            padding: 1px 7px;
        }

        .confidence-wrap {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            color: #64748b;
            font-variant-numeric: tabular-nums;
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
            background: rgba(255, 255, 255, 0.06);
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
        if (changed.has('attachments')) {
            this._resolveMedia();
        }
    }

    private _unbindCodeCopy: (() => void) | null = null;

    override connectedCallback() {
        super.connectedCallback();
        // Delegated copy: markdown HTML is injected via unsafeHTML, so the
        // button cannot carry a Lit listener. Bind one handler on the host.
        this._unbindCodeCopy = bindCodeCopy(this);
        this._prefs = getChatPrefs();
        this._prefsOff = (() => {
            const on = () => {
                this._prefs = getChatPrefs();
            };
            window.addEventListener(CHAT_PREFS_EVENT, on);
            return () => window.removeEventListener(CHAT_PREFS_EVENT, on);
        })();
    }

    override disconnectedCallback() {
        this._unbindCodeCopy?.();
        this._unbindCodeCopy = null;
        this._prefsOff?.();
        this._prefsOff = undefined;
        super.disconnectedCallback();
    }

    /** Tool steps the user allowed in Chat settings (CS-13..20). */
    private _visibleTools(): ToolCallStep[] {
        const tools = this.tools ?? [];
        const icons = this._prefs.toolIcons;
        return tools.filter((t) => {
            const name = (t.name || '').toLowerCase();
            for (const key of Object.keys(icons) as ToolIconKey[]) {
                if (!icons[key]) continue;
                if (name.includes(key) || key.includes(name)) return true;
            }
            // Unknown tool names still show when any tool icon is enabled.
            return Object.values(icons).some(Boolean);
        });
    }

    /**
     * Resolve a download URL for attachments that carry a real filesv2 id.
     * Failures land in an honest `unavailable` state — never a broken frame.
     */
    private _resolveMedia() {
        const list = this.attachments ?? [];
        for (const a of list) {
            const key = a.file_id || `local:${a.name}`;
            if (this._mediaRequested.has(key)) continue;
            this._mediaRequested.add(key);

            if (!a.file_id) {
                // No filesv2 id — the bytes were never accepted. Chip only.
                this._media = { ...this._media, [key]: { url: null, state: 'unavailable' } };
                continue;
            }

            this._media = { ...this._media, [key]: { url: null, state: 'pending' } };
            void apiClient
                .get<{ download_url?: string }>(`/filesv2/${a.file_id}/download-url`)
                .then((res) => {
                    const url = res?.download_url;
                    if (typeof url === 'string' && url.length > 0) {
                        this._media = {
                            ...this._media,
                            [key]: { url, state: 'ok' },
                        };
                    } else {
                        this._media = {
                            ...this._media,
                            [key]: { url: null, state: 'unavailable' },
                        };
                    }
                })
                .catch(() => {
                    this._media = {
                        ...this._media,
                        [key]: { url: null, state: 'unavailable' },
                    };
                });
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
            console.warn('[SomaMessage] clipboard write failed', err);
        }
    }

    private _toggleTools() {
        this._toolsExpanded = !this._toolsExpanded;
    }

    private _formatTime(iso: string): string {
        return formatTime(iso);
    }

    private _ctxClass(meta: MessageTurnMeta): string {
        if (!meta.contextTokens || !meta.contextWindow) return '';
        const pct = Math.round((meta.contextTokens / meta.contextWindow) * 100);
        if (!Number.isFinite(pct)) return '';
        if (pct >= 80) return 'ctx-high';
        if (pct >= 50) return 'ctx-mid';
        return 'ctx-ok';
    }

    /** Beautiful chip row for turn_meta — only fields the server sent + prefs. */
    private _renderTurnChips() {
        const meta = this.turnMeta;
        if (!meta) return nothing;
        const p = this._prefs;
        const hasAnything =
            (p.showModelChip && meta.model) ||
            (meta.memoryHits && meta.memoryHits.length > 0) ||
            (p.showTokenUsage && meta.contextTokens);
        if (!hasAnything) return nothing;

        const hits = meta.memoryHits ?? [];
        const top = hits[0];
        const ctxPct =
            meta.contextTokens && meta.contextWindow
                ? Math.round((meta.contextTokens / meta.contextWindow) * 100)
                : null;

        return html`
            <div class="turn-chips" role="group" aria-label="Turn metadata">
                ${p.showModelChip && meta.model
                    ? html`<span class="chip model" title="Model serving this turn">
                          <span class="material-symbols-outlined">memory</span>
                          ${meta.model}
                      </span>`
                    : nothing}
                ${hits.length > 0 && p.toolIcons.memory
                    ? html`<span class="chip recall" title="Memory hits recalled this turn">
                          <span class="material-symbols-outlined">psychology</span>
                          recall ${hits.length}
                      </span>`
                    : nothing}
                ${p.showTokenUsage && ctxPct != null && meta.contextTokens && meta.contextWindow
                    ? html`<span
                          class="chip ${this._ctxClass(meta)}"
                          title="Context fill — ${meta.contextTokens} of ${meta.contextWindow} tokens"
                      >
                          <span class="material-symbols-outlined">data_object</span>
                          CTX ${ctxPct}%
                      </span>`
                    : p.showTokenUsage && meta.contextTokens
                      ? html`<span class="chip" title="Context tokens (model window unknown)">
                            <span class="material-symbols-outlined">data_object</span>
                            ${meta.contextTokens} tok
                        </span>`
                      : nothing}
            </div>
            ${top && top.text && p.toolIcons.memory
                ? html`<div class="turn-chips">
                      <span class="chip-hit" title="Top memory hit this turn">
                          <span class="score"
                              >${typeof top.score === 'number'
                                  ? top.score.toFixed(2)
                                  : '—'}</span
                          >
                          <span class="hit-text">${top.text}</span>
                      </span>
                  </div>`
                : nothing}
        `;
    }

    /** One attachment: media frame when resolvable, honest card otherwise. */
    private _renderAttachment(a: AttachmentInput) {
        const key = a.file_id || `local:${a.name}`;
        const media = this._media[key];
        const isImage = isImageAttachment(a.name, a.type);
        const isAudio = isAudioAttachment(a.name, a.type);
        const isVideo = isVideoAttachment(a.name, a.type);
        const icon = attachmentIcon(a.name, a.type);
        const sub = `${(a.type || 'file').split('/').pop() || 'file'}${
            a.size ? ` · ${formatBytes(a.size)}` : ''
        }`;

        if (media?.state === 'pending') {
            return html`
                <div class="media-pending" title=${a.name}>
                    <span class="material-symbols-outlined" aria-hidden="true">hourglass_top</span>
                    <span>Preparing preview…</span>
                </div>
            `;
        }

        if (media?.state === 'ok' && media.url && (isImage || isAudio || isVideo)) {
            return html`
                <figure class="media-frame">
                    ${isImage
                        ? html`<img src=${media.url} alt=${a.name} loading="lazy" />`
                        : nothing}
                    ${isAudio
                        ? html`<audio src=${media.url} controls preload="metadata"></audio>`
                        : nothing}
                    ${isVideo
                        ? html`<video src=${media.url} controls preload="metadata"></video>`
                        : nothing}
                    <figcaption>
                        <span class="material-symbols-outlined" aria-hidden="true" style="font-size:14px"
                            >${icon}</span
                        >
                        <span class="name">${a.name}</span>
                        <span>${sub}</span>
                    </figcaption>
                </figure>
            `;
        }

        // Resolved but not media (pdf/zip/…) → download card.
        if (media?.state === 'ok' && media.url) {
            return html`
                <figure class="attachment-card">
                    <span class="file-icon" aria-hidden="true">
                        <span class="material-symbols-outlined">${icon}</span>
                    </span>
                    <figcaption class="file-meta">
                        <span class="name">${a.name}</span>
                        <span class="sub">${sub}</span>
                        <a class="download" href=${media.url} download=${a.name}>Download</a>
                    </figcaption>
                </figure>
            `;
        }

        // No file_id, or the download URL could not be resolved — honest card.
        return html`
            <figure class="attachment-card is-unavailable ${isImage ? 'is-image' : ''}" title=${a.name}>
                <span class="file-icon" aria-hidden="true">
                    <span class="material-symbols-outlined">${icon}</span>
                </span>
                <figcaption class="file-meta">
                    <span class="name">${a.name}</span>
                    <span class="sub">${a.file_id ? 'Preview unavailable' : 'Not uploaded'} · ${sub}</span>
                </figcaption>
            </figure>
        `;
    }

    render() {
        const visibleTools = this._visibleTools();
        const hasTools = visibleTools.length > 0;
        const hasAttachments = this.attachments && this.attachments.length > 0;
        const showFooter =
            !!this.timestamp ||
            this.stopped ||
            this.confidence != null ||
            this.messageRole === 'assistant' ||
            this.messageRole === 'user';

        return html`
            <div class="bubble" role="article" aria-label=${`${this.messageRole} message`}>
                ${this._renderTurnChips()}

                ${hasTools ? html`
                    <div class="tools">
                        <button
                            class="tools-toggle"
                            @click=${this._toggleTools}
                            aria-expanded=${this._toolsExpanded ? 'true' : 'false'}
                            title=${this._toolsExpanded ? 'Collapse tool activity' : 'Expand tool activity'}
                        >
                            <span class="chev ${this._toolsExpanded ? 'open' : ''}">▶</span>
                            <span>${visibleTools.length} tool${visibleTools.length === 1 ? '' : 's'}</span>
                        </button>
                        ${this._toolsExpanded ? html`
                            <soma-tool-timeline .steps=${visibleTools}></soma-tool-timeline>
                        ` : nothing}
                    </div>
                ` : nothing}
                <slot name="tools"></slot>

                ${hasAttachments ? html`
                    <div class="attachments">
                        <div class="attachment-grid">
                            ${this.attachments.map((a) => this._renderAttachment(a))}
                        </div>
                    </div>
                ` : nothing}

                ${this.thinking && !this.text
                    ? html`<div class="typing" role="status" aria-label="Assistant is thinking">
                          <span></span><span></span><span></span>
                      </div>`
                    : nothing}

                ${this.messageRole === 'user'
                    ? html`<div class="text">${this.text}</div>`
                    : html`<div class="text" aria-live=${this.streaming ? 'polite' : 'off'}>${unsafeHTML(this._renderedHtml)}</div>`}
                ${this.streaming && this.text ? html`<span class="cursor" aria-hidden="true"></span>` : nothing}

                ${this.error ? html`
                    <div class="inline-error" role="alert">
                        <span class="material-symbols-outlined icon">error</span>
                        <span>${this.error}</span>
                    </div>
                ` : nothing}

                ${showFooter ? html`
                    <div class="footer">
                        ${this.timestamp && this._prefs.showTimestamps ? html`<span class="time">${this._formatTime(this.timestamp)}</span>` : nothing}
                        ${this.stopped ? html`<span class="stopped-badge">stopped</span>` : nothing}
                        ${this.confidence != null && this._prefs.showConfidence ? html`
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
