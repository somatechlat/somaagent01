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
import { glassCard } from '../styles/glass.js';
import { moduleBase } from '../styles/module-base.js';
import { renderMarkdown, renderCodeBlock, bindCodeCopy, formatTime, formatBytes } from '../utils/markdown.js';
import { apiClient } from '../services/api-client.js';
import { attachmentIcon } from '../utils/file-icons.js';
import { t } from '../i18n/index.js';
import { pushToast } from './soma-toast-stack.js';
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

/**
 * Bubble action contract (CH-11 / CH-35 / operator 2026-10-14).
 * Parent (`soma-chat`) wires these to the live WS `chat.message` path.
 *
 * Operator law (2026-10-14):
 * - Copy (content_copy) — always, handled in-bubble via clipboard.
 * - Retry (refresh) — ONLY when the turn failed / stopped / errored.
 * - Fork (call_split) — user + assistant; honest refusal when no API.
 * - NO Edit on already-sent messages. Drafts only — not this bubble.
 * - Icon-only buttons (aria-label + title). No emoji. No text buttons.
 */
export type MessageActionKind = 'retry' | 'fork';

export interface MessageActionDetail {
    action: MessageActionKind;
    messageId: string;
    role: MessageRole;
}

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
    /** Stable row id from the parent so Retry/Fork can correlate. */
    @property({ type: String, attribute: 'message-id' }) messageId = '';
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

    static styles = [
        glassCard,
        moduleBase,
        css`
        :host {
            display: block;
            max-width: min(88%, 54rem);
            animation: msgIn var(--skin-motion-slow) var(--skin-motion-ease) both;
        }

        @keyframes msgIn {
            from {
                opacity: 0;
                transform: translateY(var(--skin-space-sm)) scale(0.985);
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
            padding: var(--skin-space-md) var(--skin-space-lg);
            border-radius: var(--skin-radius-xl);
            font-size: var(--skin-text-base);
            line-height: var(--skin-leading-relaxed);
            letter-spacing: 0.005em;
            word-wrap: break-word;
            overflow-wrap: anywhere;
            position: relative;
        }

        :host([message-role='user']) .bubble {
            background: linear-gradient(
                145deg,
                var(--skin-color-accent) 0%,
                var(--skin-color-accent-hover) 48%,
                var(--skin-color-accent) 100%
            );
            color: var(--skin-color-accent-text);
            border: var(--skin-border-width) solid color-mix(in srgb, var(--skin-color-text-inverse) 16%, transparent);
            border-bottom-right-radius: var(--skin-radius-md);
            box-shadow: var(--skin-shadow-md);
        }

        :host([message-role='assistant']) .bubble {
            background: var(--skin-glass-bg);
            color: var(--skin-color-text-primary);
            border: var(--skin-border-width) solid var(--skin-color-border-subtle);
            border-bottom-left-radius: var(--skin-radius-md);
            box-shadow: var(--skin-shadow-lg);
        }

        :host([message-role='system']) .bubble {
            background: var(--skin-color-bg-card);
            color: var(--skin-color-text-secondary);
            font-size: var(--skin-text-sm);
            border: var(--skin-border-width) dashed color-mix(in srgb, var(--skin-color-text-secondary) 28%, transparent);
            border-radius: var(--skin-radius-full);
            padding: var(--skin-space-xs) var(--skin-space-md);
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
            font-weight: var(--skin-weight-semibold);
            line-height: var(--skin-leading-tight);
            letter-spacing: -0.012em;
        }

        .text :deep(.md-h1) {
            font-size: 1.38em;
            /* Solid fallback first — gradient clip is progressive enhancement (C-05). */
            color: var(--skin-color-text-primary);
            background: linear-gradient(92deg, var(--skin-color-accent), var(--skin-color-accent-hover));
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        :host([message-role='user']) .text :deep(.md-h1) {
            background: none;
            color: var(--skin-color-accent-text);
            -webkit-text-fill-color: var(--skin-color-accent-text);
        }

        .text :deep(.md-h2) { font-size: 1.2em; color: var(--skin-color-text-primary); }
        .text :deep(.md-h3) { font-size: 1.08em; color: var(--skin-color-text-primary); }
        .text :deep(.md-h4),
        .text :deep(.md-h5),
        .text :deep(.md-h6) {
            font-size: 1em;
            color: var(--skin-color-text-secondary);
            text-transform: none;
        }

        :host([message-role='user']) .text :deep(.md-h),
        :host([message-role='user']) .text :deep(.md-h2),
        :host([message-role='user']) .text :deep(.md-h3) {
            color: var(--skin-color-accent-text);
        }

        .text :deep(strong),
        .text :deep(b) {
            font-weight: var(--skin-weight-semibold);
            color: var(--skin-color-text-primary);
        }

        :host([message-role='user']) .text :deep(strong) {
            color: var(--skin-color-accent-text);
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
            width: var(--skin-space-xs);
            height: var(--skin-space-xs);
            border-radius: var(--skin-radius-full);
            background: var(--skin-color-accent);
        }

        :host([message-role='user']) .text :deep(.md-ul > li::before) {
            background: color-mix(in srgb, var(--skin-color-accent-text) 78%, transparent);
        }

        .text :deep(.md-quote) {
            margin: 0 0 0.85em;
            padding: var(--skin-space-sm) var(--skin-space-md);
            border-left: var(--skin-border-width) solid var(--skin-color-accent);
            border-radius: 0 var(--skin-radius-lg) var(--skin-radius-lg) 0;
            background: color-mix(in srgb, var(--skin-color-accent) 8%, transparent);
            color: var(--skin-color-text-secondary);
            font-style: italic;
        }

        :host([message-role='user']) .text :deep(.md-quote) {
            background: color-mix(in srgb, var(--skin-color-accent-text) 12%, transparent);
            border-left-color: color-mix(in srgb, var(--skin-color-accent-text) 70%, transparent);
            color: var(--skin-color-accent-text);
        }

        .text :deep(.md-hr) {
            border: none;
            height: var(--skin-border-width);
            margin: 1.05em 0;
            background: linear-gradient(
                90deg,
                transparent,
                color-mix(in srgb, var(--skin-color-text-secondary) 32%, transparent),
                transparent
            );
        }

        .text :deep(.md-code) {
            font-family: var(--skin-font-mono);
            font-size: 0.86em;
            padding: 0.14em 0.42em;
            border-radius: var(--skin-radius-sm);
            background: var(--skin-color-bg-base);
            border: var(--skin-border-width) solid var(--skin-color-border);
            /* text-link aliases accent (= user-bubble fill) — never use it for code. */
            color: var(--skin-color-text-primary);
        }

        :host([message-role='user']) .text :deep(.md-code) {
            background: color-mix(in srgb, var(--skin-color-bg-void) 22%, transparent);
            border-color: color-mix(in srgb, var(--skin-color-accent-text) 18%, transparent);
            color: var(--skin-color-accent-text);
        }

        .text :deep(.md-pre) {
            margin: 0 0 0.85em;
            padding: var(--skin-space-sm) var(--skin-space-md);
            background: var(--skin-color-bg-base);
            border: var(--skin-border-width) solid var(--skin-color-border);
            border-radius: var(--skin-radius-lg);
            overflow-x: auto;
        }

        .text :deep(.md-codeblock-wrap) {
            margin: 0 0 0.95em;
            border: var(--skin-border-width) solid var(--skin-color-border-subtle);
            border-radius: var(--skin-radius-lg);
            overflow: hidden;
            background: var(--skin-color-bg-base);
            box-shadow: var(--skin-shadow-md);
        }

        .text :deep(.md-codeblock-bar) {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: var(--skin-space-sm);
            padding: var(--skin-space-xs) var(--skin-space-md);
            background: var(--skin-color-bg-hover);
            border-bottom: var(--skin-border-width) solid var(--skin-color-border);
        }

        .text :deep(.md-codeblock-lang) {
            font-family: var(--skin-font-mono);
            font-size: var(--skin-text-xs);
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: var(--skin-color-text-link);
        }

        .text :deep(.md-copy-btn) {
            border: var(--skin-border-width) solid var(--skin-color-border);
            background: var(--skin-color-bg-card);
            color: var(--skin-color-text-secondary);
            font-size: var(--skin-text-xs);
            line-height: 1;
            padding: var(--skin-space-xs) var(--skin-space-sm);
            border-radius: var(--skin-radius-md);
            cursor: pointer;
            transition:
                background var(--skin-motion-fast) var(--skin-motion-ease),
                color var(--skin-motion-fast) var(--skin-motion-ease),
                border-color var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .text :deep(.md-copy-btn:hover) {
            background: color-mix(in srgb, var(--skin-color-accent) 22%, transparent);
            border-color: var(--skin-color-accent);
            color: var(--skin-color-text-primary);
        }

        .text :deep(.md-codeblock-wrap .md-pre) {
            margin: 0;
            border: 0;
            border-radius: 0;
            background: transparent;
            box-shadow: none;
        }

        .text :deep(.md-codeblock) {
            font-family: var(--skin-font-mono);
            font-size: var(--skin-text-sm);
            line-height: var(--skin-leading-relaxed);
            color: var(--skin-color-text-primary);
            white-space: pre;
        }

        .text :deep(.md-link) {
            color: var(--skin-color-text-link);
            text-decoration: underline;
            text-underline-offset: var(--skin-border-width);
            text-decoration-thickness: var(--skin-border-width);
        }

        .text :deep(.md-link:hover) {
            color: var(--skin-color-accent-hover);
        }

        :host([message-role='user']) .text :deep(.md-link) {
            color: var(--skin-color-accent-text);
        }

        /* tables / cards / generic HTML the model emits */
        .text :deep(table) {
            width: 100%;
            border-collapse: collapse;
            margin: 0 0 0.9em;
            font-size: var(--skin-text-sm);
            border-radius: var(--skin-radius-lg);
            overflow: hidden;
            border: var(--skin-border-width) solid var(--skin-color-border);
        }

        .text :deep(th),
        .text :deep(td) {
            padding: var(--skin-space-sm) var(--skin-space-sm);
            border-bottom: var(--skin-border-width) solid var(--skin-color-border-subtle);
            text-align: left;
        }

        .text :deep(th) {
            background: var(--skin-color-bg-hover);
            color: var(--skin-color-text-primary);
            font-weight: var(--skin-weight-semibold);
        }

        .text :deep(tr:last-child td) {
            border-bottom: 0;
        }

        .text :deep(pre),
        .text :deep(code) {
            font-family: var(--skin-font-mono);
        }

        .text :deep(img) {
            max-width: 100%;
            border-radius: var(--skin-radius-lg);
            margin: 0.4em 0;
        }

        /* ---------- turn chips (model / recall / ctx) ---------- */
        .turn-chips {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: var(--skin-space-xs);
            margin-bottom: var(--skin-space-sm);
        }

        .chip {
            display: inline-flex;
            align-items: center;
            gap: var(--skin-space-xs);
            padding: var(--skin-space-xs) var(--skin-space-sm);
            border-radius: var(--skin-radius-full);
            font-size: var(--skin-text-xs);
            line-height: var(--skin-leading-tight);
            letter-spacing: 0.01em;
            border: var(--skin-border-width) solid var(--skin-color-border-subtle);
            background: var(--skin-color-bg-hover);
            color: var(--skin-color-text-secondary);
            white-space: nowrap;
            max-width: 14rem;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .chip .material-symbols-outlined {
            font-size: var(--skin-text-xs);
            opacity: 0.85;
        }

        .chip.model {
            border-color: color-mix(in srgb, var(--skin-color-success) 35%, transparent);
            color: var(--skin-color-success);
        }

        .chip.model .live {
            font-size: var(--skin-text-xs);
            font-weight: var(--skin-weight-bold);
            letter-spacing: 0.07em;
            text-transform: uppercase;
            color: var(--skin-color-success);
            border: var(--skin-border-width) solid color-mix(in srgb, var(--skin-color-success) 50%, transparent);
            border-radius: var(--skin-radius-full);
            padding: 0 var(--skin-space-xs);
        }

        .chip.recall {
            border-color: color-mix(in srgb, var(--skin-color-info) 32%, transparent);
            color: var(--skin-color-info);
        }

        .chip.ctx-ok {
            border-color: color-mix(in srgb, var(--skin-color-success) 30%, transparent);
            color: var(--skin-color-success);
        }
        .chip.ctx-mid {
            border-color: color-mix(in srgb, var(--skin-color-warning) 32%, transparent);
            color: var(--skin-color-warning);
        }
        .chip.ctx-high {
            border-color: color-mix(in srgb, var(--skin-color-danger) 35%, transparent);
            color: var(--skin-color-danger);
        }

        .chip-hit {
            display: inline-flex;
            align-items: center;
            gap: var(--skin-space-xs);
            padding: var(--skin-space-xs) var(--skin-space-sm);
            border-radius: var(--skin-radius-md);
            font-size: var(--skin-text-xs);
            line-height: var(--skin-leading-normal);
            border: var(--skin-border-width) solid color-mix(in srgb, var(--skin-color-info) 22%, transparent);
            background: color-mix(in srgb, var(--skin-color-info) 8%, transparent);
            color: var(--skin-color-text-secondary);
            max-width: 100%;
        }

        .chip-hit .score {
            flex-shrink: 0;
            font-variant-numeric: tabular-nums;
            color: var(--skin-color-info);
            font-weight: var(--skin-weight-semibold);
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
            gap: var(--skin-space-sm);
            margin-bottom: var(--skin-space-md);
        }

        .attachment-grid {
            display: flex;
            flex-wrap: wrap;
            gap: var(--skin-space-sm);
        }

        .attachment-card {
            display: flex;
            align-items: center;
            gap: var(--skin-space-md);
            margin: 0;
            padding: var(--skin-space-sm) var(--skin-space-md);
            border-radius: var(--skin-radius-lg);
            max-width: 18.75rem;
            background: var(--skin-color-bg-card);
            border: var(--skin-border-width) solid var(--skin-color-border);
            box-shadow: var(--skin-shadow-md);
            color: var(--skin-color-text-primary);
        }

        .attachment-card.is-image {
            border-color: color-mix(in srgb, var(--skin-color-success) 26%, transparent);
        }

        .attachment-card.is-unavailable {
            border-color: color-mix(in srgb, var(--skin-color-text-muted) 22%, transparent);
            border-style: dashed;
            opacity: 0.92;
        }

        .attachment-card .file-icon {
            flex: 0 0 auto;
            width: var(--skin-space-xl);
            height: var(--skin-space-xl);
            border-radius: var(--skin-radius-md);
            display: grid;
            place-items: center;
            background: color-mix(in srgb, var(--skin-color-accent) 13%, transparent);
            color: var(--skin-color-accent);
        }

        .attachment-card.is-image .file-icon {
            background: color-mix(in srgb, var(--skin-color-success) 13%, transparent);
            color: var(--skin-color-success);
        }

        .attachment-card.is-unavailable .file-icon {
            background: color-mix(in srgb, var(--skin-color-text-muted) 12%, transparent);
            color: var(--skin-color-text-muted);
        }

        .attachment-card .file-icon .material-symbols-outlined {
            font-size: var(--skin-text-xl);
        }

        .attachment-card .file-meta {
            display: flex;
            flex-direction: column;
            gap: 2px;
            min-width: 0;
        }

        .attachment-card .name {
            font-size: var(--skin-text-sm);
            font-weight: var(--skin-weight-semibold);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            color: var(--skin-color-text-primary);
        }

        .attachment-card .sub {
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-muted);
            text-transform: lowercase;
            letter-spacing: 0.02em;
        }

        .attachment-card a.download {
            color: var(--skin-color-text-link);
            font-size: var(--skin-text-xs);
            text-decoration: underline;
            text-underline-offset: 2px;
        }

        .media-frame {
            margin: 0;
            border-radius: var(--skin-radius-lg);
            overflow: hidden;
            border: var(--skin-border-width) solid var(--skin-color-border-subtle);
            background: var(--skin-color-bg-base);
            box-shadow: var(--skin-shadow-lg);
            max-width: min(100%, 32.5rem);
        }

        .media-frame img {
            display: block;
            width: 100%;
            max-height: 26.25rem;
            object-fit: contain;
            background: var(--skin-color-bg-base);
        }

        .media-frame audio {
            display: block;
            width: min(100%, 26.25rem);
            padding: var(--skin-space-sm) var(--skin-space-md);
        }

        .media-frame video {
            display: block;
            width: 100%;
            max-height: 26.25rem;
            background: var(--skin-color-bg-void);
        }

        .media-frame figcaption {
            padding: var(--skin-space-sm) var(--skin-space-md);
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-secondary);
            border-top: var(--skin-border-width) solid var(--skin-color-border-subtle);
            display: flex;
            align-items: center;
            gap: var(--skin-space-sm);
        }

        .media-frame figcaption .name {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            color: var(--skin-color-text-primary);
            font-weight: var(--skin-weight-medium);
        }

        :host([message-role='user']) .attachment-card {
            background: color-mix(in srgb, var(--skin-color-text-inverse) 12%, transparent);
            border-color: color-mix(in srgb, var(--skin-color-text-inverse) 22%, transparent);
            color: var(--skin-color-text-inverse);
        }

        :host([message-role='user']) .attachment-card .name {
            color: var(--skin-color-text-inverse);
        }

        :host([message-role='user']) .attachment-card .sub {
            color: color-mix(in srgb, var(--skin-color-text-inverse) 72%, transparent);
        }

        :host([message-role='user']) .attachment-card .file-icon {
            background: color-mix(in srgb, var(--skin-color-text-inverse) 16%, transparent);
            color: var(--skin-color-text-inverse);
        }

        /* ---------- typing / thinking ---------- */
        .typing {
            display: inline-flex;
            align-items: center;
            gap: var(--skin-space-xs);
            padding: var(--skin-space-xs) 2px 2px;
        }

        .typing span {
            width: var(--skin-space-sm);
            height: var(--skin-space-sm);
            border-radius: var(--skin-radius-full);
            background: var(--skin-color-accent);
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
            width: var(--skin-space-sm);
            height: 1.05em;
            margin-left: var(--skin-space-xs);
            vertical-align: text-bottom;
            border-radius: var(--skin-radius-sm);
            background: linear-gradient(180deg, var(--skin-color-accent), var(--skin-color-accent-hover));
            animation: blink 1s step-end infinite;
        }

        @keyframes blink {
            50% {
                opacity: 0;
            }
        }

        /* ---------- tools ---------- */
        .tools {
            margin-bottom: var(--skin-space-md);
        }

        .tools-toggle {
            display: inline-flex;
            align-items: center;
            gap: var(--skin-space-xs);
            padding: var(--skin-space-xs) var(--skin-space-sm);
            margin-bottom: var(--skin-space-sm);
            border-radius: var(--skin-radius-full);
            border: var(--skin-border-width) solid var(--skin-color-border-subtle);
            background: var(--skin-color-bg-hover);
            color: var(--skin-color-text-secondary);
            font-size: var(--skin-text-xs);
            cursor: pointer;
            transition:
                color var(--skin-motion-fast) var(--skin-motion-ease),
                background var(--skin-motion-fast) var(--skin-motion-ease),
                border-color var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .tools-toggle:hover {
            color: var(--skin-color-text-primary);
            background: color-mix(in srgb, var(--skin-color-accent) 10%, transparent);
            border-color: color-mix(in srgb, var(--skin-color-accent) 45%, transparent);
        }

        .tools-toggle:focus-visible {
            outline: var(--skin-focus-ring-width) solid var(--skin-focus-ring);
            outline-offset: var(--skin-focus-ring-offset);
        }

        .tools-toggle .chev {
            font-size: var(--skin-text-xs);
            transition: transform var(--skin-motion-fast) var(--skin-motion-ease);
        }

        /* expand_more points down; open flips it up. */
        .tools-toggle .chev.open {
            transform: rotate(180deg);
        }

        /* ---------- inline error ---------- */
        .inline-error {
            display: flex;
            align-items: flex-start;
            gap: var(--skin-space-sm);
            margin-top: var(--skin-space-sm);
            padding: var(--skin-space-sm) var(--skin-space-md);
            border-radius: var(--skin-radius-lg);
            background: color-mix(in srgb, var(--skin-color-danger) 10%, transparent);
            border: var(--skin-border-width) solid color-mix(in srgb, var(--skin-color-danger) 32%, transparent);
            color: var(--skin-color-danger);
            font-size: var(--skin-text-sm);
            line-height: var(--skin-leading-normal);
        }

        .inline-error .icon {
            font-size: var(--skin-text-sm);
            line-height: var(--skin-leading-tight);
            flex-shrink: 0;
        }

        /* ---------- footer ---------- */
        .footer {
            display: flex;
            align-items: center;
            gap: var(--skin-space-sm);
            margin-top: var(--skin-space-sm);
            min-height: var(--skin-space-lg);
        }

        .time {
            font-size: var(--skin-text-xs);
            /* AA on glass — muted fails 4.5:1 in light. */
            color: var(--skin-color-text-secondary);
            font-variant-numeric: tabular-nums;
        }

        :host([message-role='user']) .time {
            color: var(--skin-color-accent-text);
            opacity: 0.88;
        }

        .stopped-badge {
            font-size: var(--skin-text-xs);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            /* AA: soft warning fill + primary text (never bare warning-on-glass). */
            color: var(--skin-color-text-primary);
            background: color-mix(in srgb, var(--skin-color-warning) 20%, var(--skin-color-bg-card));
            border: var(--skin-border-width) solid var(--skin-color-warning);
            border-radius: var(--skin-radius-sm);
            padding: 1px var(--skin-space-xs);
        }

        .confidence-wrap {
            display: flex;
            align-items: center;
            gap: var(--skin-space-xs);
            font-size: var(--skin-text-xs);
            /* AA on glass — muted fails 4.5:1 in light. */
            color: var(--skin-color-text-secondary);
            font-variant-numeric: tabular-nums;
        }

        .confidence-bar {
            width: var(--skin-space-2xl);
            height: var(--skin-space-xs);
            background: color-mix(in srgb, var(--skin-color-text-secondary) 20%, transparent);
            border-radius: var(--skin-radius-full);
            overflow: hidden;
        }

        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--skin-color-success), var(--skin-color-success));
            border-radius: var(--skin-radius-full);
        }

        .actions {
            margin-left: auto;
            display: flex;
            gap: var(--skin-space-xs);
            opacity: 0;
            transition: opacity var(--skin-motion-fast) var(--skin-motion-ease);
        }

        :host(:hover) .actions,
        :host(:focus-within) .actions {
            opacity: 1;
        }

        /* Touch devices have no hover — actions must stay reachable (A-04). */
        @media (hover: none) {
            .actions {
                opacity: 1;
            }
        }

        .action-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            /* Icon-only (operator 2026-10-14): square hit target ≥ 24px (WCAG 2.2 AA). */
            width: 1.75rem;
            height: 1.75rem;
            padding: 0;
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid transparent;
            background: transparent;
            /* AA: secondary, never muted-on-glass. */
            color: var(--skin-color-text-secondary);
            font-size: var(--skin-text-xs);
            cursor: pointer;
            transition:
                background var(--skin-motion-fast) var(--skin-motion-ease),
                color var(--skin-motion-fast) var(--skin-motion-ease),
                border-color var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .action-btn .material-symbols-outlined {
            font-size: var(--skin-text-sm);
            line-height: 1;
            pointer-events: none;
        }

        :host([message-role='user']) .action-btn {
            color: var(--skin-color-accent-text);
        }

        .action-btn:hover {
            background: var(--skin-color-bg-hover);
            color: var(--skin-color-text-primary);
            border-color: var(--skin-color-border-subtle);
        }

        :host([message-role='user']) .action-btn:hover {
            background: color-mix(in srgb, var(--skin-color-accent-text) 14%, transparent);
            color: var(--skin-color-accent-text);
            border-color: color-mix(in srgb, var(--skin-color-accent-text) 28%, transparent);
        }

        .action-btn:focus-visible {
            outline: var(--skin-focus-ring-width) solid var(--skin-focus-ring);
            outline-offset: var(--skin-focus-ring-offset);
        }

        .action-btn:disabled {
            opacity: 0.55;
            cursor: not-allowed;
        }
    `,
    ];

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
     * Resolve media for attachments with a real filesv2 id.
     * Images stream from /content (same-origin). Failures → icon card,
     * never a stuck "Preparing preview" spinner.
     */
    private _resolveMedia() {
        const list = this.attachments ?? [];
        for (const a of list) {
            const key = a.file_id || `local:${a.name}`;
            if (this._mediaRequested.has(key)) continue;
            this._mediaRequested.add(key);

            if (!a.file_id) {
                this._media = { ...this._media, [key]: { url: null, state: 'unavailable' } };
                continue;
            }

            const contentUrl = `/api/v2/filesv2/${encodeURIComponent(a.file_id)}/content`;
            const isImg = isImageAttachment(a.name, a.type);

            if (isImg) {
                // Direct stream — no JSON hop, no spinner.
                this._media = { ...this._media, [key]: { url: contentUrl, state: 'ok' } };
                continue;
            }

            // Non-media: resolve signed download URL (or local /content).
            this._media = { ...this._media, [key]: { url: contentUrl, state: 'ok' } };
            void apiClient
                .get<{ download_url?: string }>(`/filesv2/${a.file_id}/download-url`)
                .then((res) => {
                    const url = res?.download_url;
                    if (typeof url === 'string' && url.length > 0) {
                        this._media = {
                            ...this._media,
                            [key]: { url, state: 'ok' },
                        };
                    }
                })
                .catch(() => {
                    // Keep the content URL fallback — never blank forever.
                    this._media = {
                        ...this._media,
                        [key]: { url: contentUrl, state: 'ok' },
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
            // HR-02: failure is visible, never a silent console warn.
            pushToast({ kind: 'error', message: t('message.copyFailed') });
        }
    }

    private _emitAction(action: MessageActionKind) {
        this.dispatchEvent(
            new CustomEvent<MessageActionDetail>('soma-message-action', {
                detail: {
                    action,
                    messageId: this.messageId,
                    role: this.messageRole,
                },
                bubbles: true,
                composed: true,
            }),
        );
    }

    /**
     * Retry is gated to failed / stopped / errored turns only (operator
     * 2026-10-14). A healthy completed turn has no retry control.
     */
    private get _canRetry(): boolean {
        if (this.streaming || this.thinking) return false;
        return !!this.error || !!this.stopped;
    }

    /** Fork is offered on user + assistant bubbles with content to branch from. */
    private get _canFork(): boolean {
        return this.messageRole !== 'system' && !!this.text;
    }

    private _retry() {
        this._emitAction('retry');
    }

    private _fork() {
        this._emitAction('fork');
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
                    ? html`<span class="chip model" title=${t('message.modelChip')}>
                          <span class="material-symbols-outlined">smart_toy</span>
                          ${meta.model}
                      </span>`
                    : nothing}
                ${hits.length > 0 && p.toolIcons.memory
                    ? html`<span class="chip recall" title=${t('message.recallChip')}>
                          <span class="material-symbols-outlined">psychology</span>
                          recall ${hits.length}
                      </span>`
                    : nothing}
                ${p.showTokenUsage && ctxPct != null && meta.contextTokens && meta.contextWindow
                    ? html`<span
                          class="chip ${this._ctxClass(meta)}"
                          title="${t('message.ctxChip')} — ${meta.contextTokens} / ${meta.contextWindow}"
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
            // Brief load only — icon card immediately if no URL yet.
            return html`
                <figure class="attachment-card" title=${a.name}>
                    <span class="file-icon" aria-hidden="true">
                        <span class="material-symbols-outlined">${icon}</span>
                    </span>
                    <figcaption class="file-meta">
                        <span class="name">${a.name}</span>
                        <span class="sub">${sub}</span>
                    </figcaption>
                </figure>
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
                        <span class="material-symbols-outlined" aria-hidden="true" style="font-size: var(--skin-text-sm)"
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
                        <a class="download" href=${media.url} download=${a.name}>${t('message.download')}</a>
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
                    <span class="sub">${a.file_id ? t('message.previewUnavailable') : t('message.notUploaded')} · ${sub}</span>
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
        const showCopy = !!this.text;
        const showRetry = this._canRetry;
        const showFork = this._canFork;
        const showActions = showCopy || showRetry || showFork;

        return html`
            <div class="bubble" role="article" aria-label=${`${this.messageRole} message`}>
                ${this._renderTurnChips()}

                ${hasTools ? html`
                    <div class="tools">
                        <button
                            class="tools-toggle"
                            @click=${this._toggleTools}
                            aria-expanded=${this._toolsExpanded ? 'true' : 'false'}
                            title=${this._toolsExpanded ? t('message.collapseTools') : t('message.expandTools')}
                        >
                            <span class="chev ${this._toolsExpanded ? 'open' : ''} material-symbols-outlined" aria-hidden="true">expand_more</span>
                            <span>${t('message.toolsCount')} (${visibleTools.length})</span>
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
                        ${this.stopped ? html`<span class="stopped-badge">${t('message.stopped')}</span>` : nothing}
                        ${this.confidence != null && this._prefs.showConfidence ? html`
                            <span class="confidence-wrap" title="Response confidence">
                                <span class="confidence-bar">
                                    <span class="confidence-fill" style="width:${Math.round(this.confidence * 100)}%"></span>
                                </span>
                                <span>${Math.round(this.confidence * 100)}%</span>
                            </span>
                        ` : nothing}
                        ${showActions ? html`
                            <div class="actions" role="group" aria-label=${t('message.actions')}>
                                ${showCopy ? html`
                                    <button
                                        class="action-btn"
                                        @click=${this._copy}
                                        title=${this._copied ? t('message.copied') : t('message.copyMessage')}
                                        aria-label=${this._copied ? t('message.copied') : t('message.copyMessage')}
                                    >
                                        <span class="material-symbols-outlined" aria-hidden="true">
                                            ${this._copied ? 'check' : 'content_copy'}
                                        </span>
                                    </button>
                                ` : nothing}
                                ${showRetry ? html`
                                    <button
                                        class="action-btn"
                                        @click=${this._retry}
                                        title=${t('message.retryHint')}
                                        aria-label=${t('message.retry')}
                                    >
                                        <span class="material-symbols-outlined" aria-hidden="true">refresh</span>
                                    </button>
                                ` : nothing}
                                ${showFork ? html`
                                    <button
                                        class="action-btn"
                                        @click=${this._fork}
                                        title=${t('message.forkHint')}
                                        aria-label=${t('message.fork')}
                                    >
                                        <span class="material-symbols-outlined" aria-hidden="true">call_split</span>
                                    </button>
                                ` : nothing}
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
