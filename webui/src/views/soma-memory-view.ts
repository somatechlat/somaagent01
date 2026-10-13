/**
 * SomaAgent Soma — Memory View
 * Per AGENT_USER_UI_SRS.md Section 8 and UI_SCREENS_SRS.md
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - SomaBrain API integration
 * - Minimal white/black design per UI_STYLE_GUIDE.md
 * - NO EMOJIS - Google Material Symbols only
 */

import { LitElement, html, css, nothing } from 'lit';
import { glassCard } from '../styles/glass.js';
import { moduleBase } from '../styles/module-base.js';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';

export interface Memory {
    id: string;
    /** Present only when the server sent a known kind. Never invented. */
    type?: 'conversation' | 'fact' | 'episode' | 'semantic';
    content: string;
    summary?: string;
    tags: string[];
    score?: number;
    /** Present only when the server sent a non-empty created_at. */
    timestamp?: string;
    coord?: string;
    metadata?: Record<string, unknown>;
}

type MemoryFilter = 'all' | 'conversation' | 'fact' | 'episode' | 'semantic';
type MemorySort = 'newest' | 'oldest' | 'relevance';

type SomaMemoryHit = {
    text?: string;
    content?: string | Record<string, unknown>;
    coord?: string;
    score?: number;
    store?: string;
    created_at?: string;
    kind?: string;
};

function mapSomaHit(raw: SomaMemoryHit, index: number): Memory {
    const payloadContent = typeof raw.content === 'object' && raw.content !== null ? raw.content : null;
    const text =
        raw.text ||
        (typeof raw.content === 'string' ? raw.content : '') ||
        (payloadContent ? String((payloadContent as Record<string, unknown>).text ?? (payloadContent as Record<string, unknown>).content ?? '') : '');
    // Kind is taken only from the server. A missing kind stays missing —
    // defaulting it to 'episodic' invents a classification.
    const rawKind = raw.kind ?? (payloadContent as Record<string, unknown> | null)?.kind;
    const kind = typeof rawKind === 'string' ? rawKind : '';
    const type: Memory['type'] | undefined =
        kind === 'semantic' || kind === 'fact' ? 'semantic' :
        kind === 'episode' || kind === 'episodic' ? 'episode' :
        kind === 'conversation' ? 'conversation' : undefined;
    const createdAt = typeof raw.created_at === 'string' ? raw.created_at : '';
    return {
        id: raw.coord || `mem-${index}`,
        type,
        content: text,
        tags: [],
        score: typeof raw.score === 'number' ? raw.score : undefined,
        // A missing created_at is not "now". Leave it absent and render "—".
        timestamp: createdAt || undefined,
        coord: raw.coord,
    };
}

@customElement('soma-memory-view')
export class SomaMemoryView extends LitElement {
    static styles = [
        glassCard,
        moduleBase,
        css`
        :host {
            display: flex;
            height: 100vh;
            background: var(--skin-color-bg-void);
            font-family: var(--skin-font-sans);
            color: var(--skin-color-text-primary);
        }

        * {
            box-sizing: border-box;
        }

        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: var(--skin-text-xl);
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            -webkit-font-feature-settings: 'liga';
            -webkit-font-smoothing: antialiased;
        }

        /* ========================================
           SIDEBAR
           ======================================== */
        .sidebar {
            width: calc(var(--skin-space-2xl) * 5 + var(--skin-space-xl));
            background: var(--skin-color-bg-card);
            border-right: var(--skin-border-width) solid var(--skin-color-border);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            padding: var(--skin-space-lg) calc(var(--skin-space-md) + var(--skin-space-xs));
        }

        .sidebar-header {
            margin-bottom: var(--skin-space-lg);
        }

        .sidebar-title {
            font-size: var(--skin-text-xl);
            font-weight: var(--skin-weight-semibold);
            margin: 0 0 var(--skin-space-xs) 0;
        }

        .sidebar-subtitle {
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-secondary);
        }

        /* Search */
        .search-box {
            position: relative;
            margin-bottom: calc(var(--skin-space-md) + var(--skin-space-xs));
        }

        .search-input {
            width: 100%;
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs) * 0.5) calc(var(--skin-space-md) - var(--skin-space-xs) * 0.5) calc(var(--skin-space-sm) + var(--skin-space-xs) * 0.5) calc(var(--skin-space-xl) + var(--skin-space-sm) + var(--skin-space-xs) * 0.5);
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid var(--skin-color-border);
            font-size: var(--skin-text-base);
            background: var(--skin-color-bg-card);
            color: var(--skin-color-text-primary);
            transition: border-color var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .search-input:focus {
            outline: none;
            border-color: var(--skin-color-accent);
        }

        .search-icon {
            position: absolute;
            left: calc(var(--skin-space-sm) + var(--skin-space-xs));
            top: 50%;
            transform: translateY(-50%);
            color: var(--skin-color-text-muted);
            font-size: var(--skin-text-xl);
        }

        /* Filters */
        .filter-section {
            margin-bottom: var(--skin-space-lg);
        }

        .filter-label {
            font-size: var(--skin-text-xs);
            text-transform: uppercase;
            color: var(--skin-color-text-muted);
            font-weight: var(--skin-weight-semibold);
            letter-spacing: 0.035em;
            margin-bottom: calc(var(--skin-space-sm) + var(--skin-space-xs) * 0.5);
        }

        .filter-options {
            display: flex;
            flex-wrap: wrap;
            gap: var(--skin-space-sm);
        }

        .filter-chip {
            padding: calc(var(--skin-space-sm) * 0.75) calc(var(--skin-space-sm) + var(--skin-space-xs));
            border-radius: var(--skin-radius-xl);
            background: var(--skin-color-bg-hover);
            border: var(--skin-border-width) solid var(--skin-color-border);
            font-size: var(--skin-text-sm);
            cursor: pointer;
            transition: all var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .filter-chip:hover {
            border-color: var(--skin-color-border-strong);
        }

        .filter-chip.active {
            background: var(--skin-color-accent);
            color: var(--skin-color-accent-text);
            border-color: var(--skin-color-accent);
        }

        /* Sort */
        .sort-select {
            width: 100%;
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs) * 0.5) calc(var(--skin-space-md) - var(--skin-space-xs) * 0.5);
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid var(--skin-color-border);
            font-size: var(--skin-text-base);
            background: var(--skin-color-bg-card);
            color: var(--skin-color-text-primary);
            cursor: pointer;
        }

        /* Stats */
        .stats {
            margin-top: auto;
            padding-top: calc(var(--skin-space-md) + var(--skin-space-xs));
            border-top: var(--skin-border-width) solid var(--skin-color-border);
        }

        .stat-row {
            display: flex;
            justify-content: space-between;
            padding: var(--skin-space-sm) 0;
            font-size: var(--skin-text-sm);
        }

        .stat-label {
            color: var(--skin-color-text-secondary);
        }

        .stat-value {
            font-weight: var(--skin-weight-semibold);
        }

        .stat-value.queued {
            color: var(--skin-color-warning-text);
        }

        /* MEMORY DASHBOARD (UI-S-04 §3.7) */
        .memory-dashboard {
            margin-top: auto;
            padding-top: var(--skin-space-md);
            border-top: var(--skin-border-width) solid var(--skin-color-border);
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: var(--skin-space-sm);
        }

        .dash-tile {
            display: flex;
            flex-direction: column;
            gap: var(--skin-space-xs);
            padding: var(--skin-space-sm) calc(var(--skin-space-sm) + var(--skin-space-xs) * 0.5);
            border: var(--skin-border-width) solid var(--skin-color-border);
            border-radius: var(--skin-radius-md);
            background: var(--skin-color-bg-hover);
        }

        .dash-value {
            font-size: var(--skin-text-lg);
            font-weight: var(--skin-weight-semibold);
            line-height: 1.2;
        }

        .dash-value.gated {
            color: var(--skin-color-text-muted);
        }

        .dash-value.queued {
            color: var(--skin-color-warning-text);
        }

        .dash-label {
            font-size: var(--skin-text-xs);
            font-weight: var(--skin-weight-semibold);
            letter-spacing: 0.04em;
            text-transform: uppercase;
            color: var(--skin-color-text-secondary);
        }

        .dash-note {
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-muted);
        }

        .dash-footnote {
            grid-column: 1 / -1;
            margin: var(--skin-space-xs) 0 0;
            font-size: var(--skin-text-xs);
            line-height: 1.4;
            color: var(--skin-color-text-muted);
        }

        /* Remember… form (UI-S-04 action 12) */
        .remember-form {
            margin: calc(var(--skin-space-sm) + var(--skin-space-xs)) 0;
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs));
            border: var(--skin-border-width) solid var(--skin-color-border);
            border-radius: var(--skin-radius-md);
            background: var(--skin-color-bg-hover);
            display: flex;
            flex-direction: column;
            gap: var(--skin-space-sm);
        }

        .remember-form textarea {
            width: 100%;
            min-height: calc(var(--skin-space-2xl) + var(--skin-space-md));
            resize: vertical;
            padding: var(--skin-space-sm) calc(var(--skin-space-sm) + var(--skin-space-xs) * 0.5);
            border: var(--skin-border-width) solid var(--skin-color-border);
            border-radius: var(--skin-radius-md);
            font: inherit;
            font-size: var(--skin-text-sm);
            background: var(--skin-color-bg-base);
            color: var(--skin-color-text-primary);
        }

        .remember-actions {
            display: flex;
            gap: var(--skin-space-sm);
            align-items: center;
        }

        .remember-status {
            font-size: var(--skin-text-xs);
        }

        .remember-status.ok {
            color: var(--skin-color-success);
        }

        .remember-status.err {
            color: var(--skin-color-danger);
        }

        .probe-btn {
            margin-top: var(--skin-space-sm);
            width: 100%;
            padding: var(--skin-space-sm) calc(var(--skin-space-sm) + var(--skin-space-xs) * 0.5);
            border: var(--skin-border-width) solid var(--skin-color-border);
            border-radius: var(--skin-radius-md);
            background: var(--skin-color-bg-base);
            color: var(--skin-color-text-primary);
            font: inherit;
            font-size: var(--skin-text-xs);
            font-weight: var(--skin-weight-semibold);
            cursor: pointer;
        }

        .probe-btn:hover {
            background: var(--skin-color-bg-hover);
        }

        .memory-queued-banner {
            display: flex;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs) * 0.5);
            align-items: flex-start;
            margin: calc(var(--skin-space-sm) + var(--skin-space-xs)) 0 var(--skin-space-xs);
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs) * 0.5) calc(var(--skin-space-sm) + var(--skin-space-xs));
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid color-mix(in srgb, var(--skin-color-warning) 45%, transparent);
            background: color-mix(in srgb, var(--skin-color-warning) 12%, transparent);
            color: var(--skin-color-warning-text);
            font-size: var(--skin-text-xs);
            line-height: 1.4;
        }

        .memory-queued-banner .material-symbols-outlined {
            font-size: var(--skin-text-xl);
            color: var(--skin-color-warning);
            margin-top: var(--skin-border-width);
        }

        .memory-queued-banner strong {
            display: block;
            color: var(--skin-color-warning-text);
            margin-bottom: var(--skin-space-xs);
        }

        .memory-queued-banner p {
            margin: 0;
        }

        .queued-pill {
            display: inline-flex;
            align-items: center;
            gap: var(--skin-space-xs);
            margin-right: var(--skin-space-sm);
            padding: var(--skin-space-xs) var(--skin-space-sm);
            border-radius: var(--skin-radius-full);
            font-size: var(--skin-text-xs);
            font-weight: var(--skin-weight-semibold);
            color: var(--skin-color-warning-text);
            border: var(--skin-border-width) solid color-mix(in srgb, var(--skin-color-warning) 50%, transparent);
            background: color-mix(in srgb, var(--skin-color-warning) 15%, transparent);
        }

        .memory-unavailable-bar {
            margin: 0 0 var(--skin-space-md);
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs)) var(--skin-space-md);
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid color-mix(in srgb, var(--skin-color-warning) 40%, transparent);
            background: color-mix(in srgb, var(--skin-color-warning) 10%, transparent);
            color: var(--skin-color-warning-text);
            font-size: var(--skin-text-sm);
        }

        .empty-state.unavailable .empty-icon.warn {
            background: color-mix(in srgb, var(--skin-color-warning) 15%, transparent);
            color: var(--skin-color-warning);
        }

        .empty-state.unavailable .empty-title {
            color: var(--skin-color-warning-text);
        }

        .empty-state .action-btn {
            margin-top: var(--skin-space-md);
        }

        /* Back Button */
        .back-btn {
            display: flex;
            align-items: center;
            gap: var(--skin-space-sm);
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs) * 0.5) calc(var(--skin-space-md) - var(--skin-space-xs) * 0.5);
            border-radius: var(--skin-radius-md);
            background: transparent;
            border: var(--skin-border-width) solid var(--skin-color-border);
            font-size: var(--skin-text-base);
            cursor: pointer;
            color: var(--skin-color-text-primary);
            margin-top: var(--skin-space-md);
            transition: all var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .back-btn:hover {
            background: var(--skin-color-bg-hover);
        }

        /* ========================================
           MAIN CONTENT
           ======================================== */
        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        /* Header */
        .header {
            padding: var(--skin-space-md) var(--skin-space-lg);
            background: var(--skin-color-bg-card);
            border-bottom: var(--skin-border-width) solid var(--skin-color-border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs));
        }

        .result-count {
            font-size: var(--skin-text-base);
            color: var(--skin-color-text-secondary);
        }

        .header-actions {
            display: flex;
            gap: var(--skin-space-sm);
        }

        .action-btn {
            padding: var(--skin-space-sm) var(--skin-space-md);
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid var(--skin-color-border);
            background: var(--skin-color-bg-card);
            font-size: var(--skin-text-sm);
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: calc(var(--skin-space-sm) * 0.75);
            transition: all var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .action-btn:hover {
            background: var(--skin-color-bg-hover);
        }

        .action-btn.primary {
            background: var(--skin-color-accent);
            color: var(--skin-color-accent-text);
            border-color: var(--skin-color-accent);
        }

        .action-btn.primary:hover {
            background: var(--skin-color-accent-hover);
        }

        .action-btn .material-symbols-outlined {
            font-size: var(--skin-text-xl);
        }

        /* Memory Grid */
        .memory-grid {
            flex: 1;
            overflow-y: auto;
            padding: var(--skin-space-lg);
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(calc(var(--skin-space-2xl) * 6 + var(--skin-space-md)), 1fr));
            gap: var(--skin-space-md);
            align-content: start;
        }

        /* Memory Card */
        .memory-card {
            background: var(--skin-color-bg-card);
            border: var(--skin-border-width) solid var(--skin-color-border);
            border-radius: var(--skin-radius-lg);
            padding: calc(var(--skin-space-md) + var(--skin-space-xs));
            cursor: pointer;
            transition: all var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .memory-card:hover {
            border-color: var(--skin-color-border-strong);
            box-shadow: var(--skin-shadow-sm));
        }

        .memory-card.selected {
            border-color: var(--skin-color-accent);
            box-shadow: 0 0 0 var(--skin-focus-ring-width) var(--skin-focus-ring);
        }

        .memory-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            margin-bottom: calc(var(--skin-space-sm) + var(--skin-space-xs));
        }

        .memory-type {
            display: flex;
            align-items: center;
            gap: calc(var(--skin-space-sm) * 0.75);
        }

        .type-icon {
            width: calc(var(--skin-space-lg) + var(--skin-space-xs));
            height: calc(var(--skin-space-lg) + var(--skin-space-xs));
            border-radius: var(--skin-radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .type-icon .material-symbols-outlined {
            font-size: var(--skin-text-lg);
        }

        .type-icon.conversation { background: color-mix(in srgb, var(--skin-color-info) 18%, transparent); color: var(--skin-color-info); }
        .type-icon.fact { background: color-mix(in srgb, var(--skin-color-warning) 22%, transparent); color: var(--skin-color-warning-text); }
        .type-icon.episode { background: color-mix(in srgb, var(--skin-color-info) 18%, transparent); color: var(--skin-color-info); }
        .type-icon.semantic { background: color-mix(in srgb, var(--skin-color-success) 18%, transparent); color: var(--skin-color-success); }

        .type-label {
            font-size: var(--skin-text-xs);
            font-weight: var(--skin-weight-medium);
            text-transform: capitalize;
            color: var(--skin-color-text-secondary);
        }

        .memory-score {
            font-size: var(--skin-text-xs);
            font-weight: var(--skin-weight-semibold);
            padding: var(--skin-space-xs) var(--skin-space-sm);
            border-radius: var(--skin-radius-sm);
            background: var(--skin-color-bg-hover);
        }

        .memory-content {
            font-size: var(--skin-text-base);
            line-height: 1.6;
            color: var(--skin-color-text-primary);
            margin-bottom: calc(var(--skin-space-sm) + var(--skin-space-xs));
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .memory-tags {
            display: flex;
            flex-wrap: wrap;
            gap: calc(var(--skin-space-sm) * 0.75);
            margin-bottom: calc(var(--skin-space-sm) + var(--skin-space-xs));
        }

        .tag {
            padding: var(--skin-space-xs) var(--skin-space-sm);
            border-radius: var(--skin-radius-sm);
            background: var(--skin-color-bg-hover);
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-secondary);
        }

        .memory-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-muted);
        }

        .memory-actions {
            display: flex;
            gap: var(--skin-space-xs);
        }

        .memory-action {
            width: calc(var(--skin-space-lg) + var(--skin-space-xs));
            height: calc(var(--skin-space-lg) + var(--skin-space-xs));
            border-radius: var(--skin-radius-md);
            background: transparent;
            border: none;
            color: var(--skin-color-text-muted);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .memory-action:hover {
            background: var(--skin-color-bg-hover);
            color: var(--skin-color-text-primary);
        }

        .memory-action.danger:hover {
            color: var(--skin-color-danger);
        }

        .memory-action .material-symbols-outlined {
            font-size: var(--skin-text-lg);
        }

        /* Empty State */
        .empty-state {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: calc(var(--skin-space-xl) + var(--skin-space-sm));
        }

        .empty-icon {
            width: calc(var(--skin-space-2xl) + var(--skin-space-md));
            height: calc(var(--skin-space-2xl) + var(--skin-space-md));
            background: var(--skin-color-bg-hover);
            border-radius: var(--skin-radius-xl);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: calc(var(--skin-space-md) + var(--skin-space-xs));
        }

        .empty-icon .material-symbols-outlined {
            font-size: var(--skin-text-2xl);
            color: var(--skin-color-text-secondary);
        }

        .empty-title {
            font-size: var(--skin-text-xl);
            font-weight: var(--skin-weight-semibold);
            margin-bottom: var(--skin-space-sm);
        }

        .empty-desc {
            font-size: var(--skin-text-base);
            color: var(--skin-color-text-secondary);
            max-width: calc(var(--skin-space-2xl) * 6 + var(--skin-space-md));
        }

        /* Loading */
        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: calc(var(--skin-space-2xl) + var(--skin-space-sm) + var(--skin-space-xs));
        }

        .spinner {
            width: var(--skin-space-xl);
            height: var(--skin-space-xl);
            border: calc(var(--skin-border-width) * 3) solid var(--skin-color-border);
            border-top-color: var(--skin-color-text-primary);
            border-radius: var(--skin-radius-full);
            animation: spin var(--skin-motion-slow) linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    `
    ];

    @state() private _memories: Memory[] = [];
    @state() private _isLoading = false;
    @state() private _searchQuery = '';
    @state() private _filter: MemoryFilter = 'all';
    @state() private _sort: MemorySort = 'newest';
    @state() private _selectedMemory: Memory | null = null;
    /** Absent until the server reports a total. A failed load is not zero. */
    @state() private _totalCount: number | null = null;
    /** True when the last list/recall failed (brain down). Not “zero memories”. */
    @state() private _memoryUnavailable = false;
    /** Hits returned by the last recall probe. Null = no probe run this session. */
    @state() private _recallHits: number | null = null;
    /** UI-S-04 #4 — this-turn filter from `?turn=current`. */
    @state() private _thisTurnOnly = false;
    /** Remember… form open (UI-S-04 action 12). */
    @state() private _rememberOpen = false;
    @state() private _rememberText = '';
    @state() private _rememberStatus = '';
    @state() private _rememberOk = true;

    async connectedCallback() {
        super.connectedCallback();
        this._thisTurnOnly =
            new URLSearchParams(window.location.search).get('turn') === 'current';
        await this._loadMemories();
    }

    render() {
        return html`
            <!-- Sidebar -->
            <aside class="sidebar">
                <div class="sidebar-header">
                    <h1 class="sidebar-title">Memory</h1>
                    <p class="sidebar-subtitle">Browse agent knowledge</p>
                    ${this._memoryUnavailable
                        ? html`<div class="memory-queued-banner" role="status">
                              <span class="material-symbols-outlined">cloud_off</span>
                              <div>
                                  <strong>Memory unavailable</strong>
                                  <p>New chat messages are <em>queued</em> and will sync when the brain is back.</p>
                              </div>
                          </div>`
                        : nothing}
                </div>

                <!-- Search (UI-S-04 #1) + Run probe (#2) -->
                <div class="search-box">
                    <span class="material-symbols-outlined search-icon">search</span>
                    <input 
                        type="text" 
                        class="search-input" 
                        placeholder="Search recall..."
                        .value=${this._searchQuery}
                        @input=${this._handleSearch}
                        @keydown=${this._handleSearchKeydown}
                    >
                </div>
                <button
                    class="probe-btn"
                    @click=${this._performSearch}
                    ?disabled=${this._isLoading}
                >
                    Run probe
                </button>

                <!-- This-turn filter (UI-S-04 #4) — present when ?turn=current.
                     [clear] returns to the full list. -->
                ${this._thisTurnOnly
                    ? html`
                          <div class="filter-section">
                              <div class="filter-label">Filter</div>
                              <div class="filter-options">
                                  <button
                                      class="filter-chip active"
                                      @click=${this._clearThisTurn}
                                      title="Clear the this-turn filter"
                                  >
                                      this turn <span class="material-symbols-outlined" aria-hidden="true">close</span>
                                  </button>
                              </div>
                          </div>
                      `
                    : nothing}

                <!-- Remember… (UI-S-04 action 12) → POST /api/v2/memory/save -->
                ${this._rememberOpen
                    ? html`
                          <div class="remember-form" role="form" aria-label="Remember">
                              <label class="filter-label" for="remember-text">Remember…</label>
                              <textarea
                                  id="remember-text"
                                  .value=${this._rememberText}
                                  @input=${(e: Event) => {
                                      this._rememberText = (e.target as HTMLTextAreaElement).value;
                                  }}
                                  placeholder="Text to store as a memory"
                              ></textarea>
                              <div class="remember-actions">
                                  <button
                                      class="action-btn primary"
                                      @click=${this._submitRemember}
                                      ?disabled=${!this._rememberText.trim() || this._isLoading}
                                  >
                                      Store
                                  </button>
                                  <button
                                      class="action-btn"
                                      @click=${() => {
                                          this._rememberOpen = false;
                                          this._rememberText = '';
                                          this._rememberStatus = '';
                                      }}
                                  >
                                      Cancel
                                  </button>
                                  ${this._rememberStatus
                                      ? html`<span
                                            class="remember-status ${this._rememberOk ? 'ok' : 'err'}"
                                            role="status"
                                            >${this._rememberStatus}</span
                                        >`
                                      : nothing}
                              </div>
                          </div>
                      `
                    : nothing}

                <!-- Filter by Type -->
                <div class="filter-section">
                    <div class="filter-label">Filter by Type</div>
                    <div class="filter-options">
                        ${(['all', 'conversation', 'fact', 'episode', 'semantic'] as MemoryFilter[]).map(f => html`
                            <button 
                                class="filter-chip ${this._filter === f ? 'active' : ''}"
                                @click=${() => this._setFilter(f)}
                            >
                                ${f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
                            </button>
                        `)}
                    </div>
                </div>

                <!-- Sort -->
                <div class="filter-section">
                    <div class="filter-label">Sort By</div>
                    <select class="sort-select" @change=${this._handleSort}>
                        <option value="newest" ?selected=${this._sort === 'newest'}>Newest First</option>
                        <option value="oldest" ?selected=${this._sort === 'oldest'}>Oldest First</option>
                        <option value="relevance" ?selected=${this._sort === 'relevance'}>Relevance</option>
                    </select>
                </div>

                <!-- MEMORY DASHBOARD (UI-S-04 §3.7). API numbers only.
                     WM / LTM have no count API — they render "—" / GATED until
                     one ships. Never 0, never a guess. No storage-used figure
                     exists in any memory API; a "2.4 GB" tile was fabricated. -->
                <div class="memory-dashboard" role="group" aria-label="Memory dashboard">
                    <div class="dash-tile">
                        <span class="dash-value gated" title="No count API — shown as — until one ships. Never 0.">—</span>
                        <span class="dash-label">WM</span>
                        <span class="dash-note">GATED</span>
                    </div>
                    <div class="dash-tile">
                        <span class="dash-value gated" title="No count API — shown as — until one ships. Never 0.">—</span>
                        <span class="dash-label">LTM</span>
                        <span class="dash-note">GATED</span>
                    </div>
                    <div class="dash-tile">
                        <span class="dash-value ${this._memoryUnavailable ? 'queued' : ''}">${
                            this._recallHits ?? '—'
                        }</span>
                        <span class="dash-label">recall</span>
                        <span class="dash-note">${this._recallHits == null ? 'no probe' : 'this probe'}</span>
                    </div>
                    <div class="dash-tile">
                        <span class="dash-value ${this._memoryUnavailable ? 'queued' : ''}">${
                            this._memoryUnavailable ? 'queued' : (this._totalCount ?? '—')
                        }</span>
                        <span class="dash-label">list</span>
                        <span class="dash-note">GET /memory/</span>
                    </div>
                    <p class="dash-footnote">
                        No count API — WM / LTM show <b>—</b> until one ships. Never 0, never a guess.
                    </p>
                </div>

                <!-- Back Button -->
                <button class="back-btn" @click=${() => window.location.href = '/chat'}>
                    <span class="material-symbols-outlined">arrow_back</span> Back to Chat
                </button>
            </aside>

            <!-- Main Content -->
            <main class="main">
                <header class="header">
                    <div class="header-left">
                        <span class="result-count">
                            ${this._memoryUnavailable
                                ? html`<span class="queued-pill"><span class="material-symbols-outlined" aria-hidden="true">schedule</span> Queued</span> ${this._visibleMemories.length} shown`
                                : `${this._visibleMemories.length} memories`}
                        </span>
                    </div>
                    <div class="header-actions">
                        <button
                            class="action-btn"
                            @click=${() => {
                                this._rememberOpen = !this._rememberOpen;
                                this._rememberStatus = '';
                            }}
                            aria-expanded=${this._rememberOpen ? 'true' : 'false'}
                        >
                            <span class="material-symbols-outlined">add</span> Remember…
                        </button>
                        <button class="action-btn" @click=${this._exportMemories}>
                            <span class="material-symbols-outlined">download</span> Export
                        </button>
                        <button class="action-btn primary" @click=${this._refreshMemories}>
                            <span class="material-symbols-outlined">refresh</span> Refresh
                        </button>
                    </div>
                </header>

                ${this._memoryUnavailable
                    ? html`<div class="memory-unavailable-bar">
                          Memory is offline. Chat keeps working — new writes stay in the agent queue until the brain reconnects.
                      </div>`
                    : nothing}
                ${this._isLoading ? html`
                    <div class="loading">
                        <div class="spinner"></div>
                    </div>
                ` : this._visibleMemories.length === 0
                    ? this._renderEmptyState()
                    : html`
                    <div class="memory-grid">
                        ${this._visibleMemories.map(memory => this._renderMemoryCard(memory))}
                    </div>
                `}
            </main>
        `;
    }

    private _renderEmptyState() {
        if (this._memoryUnavailable) {
            return html`
                <div class="empty-state unavailable">
                    <div class="empty-icon warn"><span class="material-symbols-outlined">cloud_off</span></div>
                    <div class="empty-title">Memory unavailable — queued</div>
                    <div class="empty-desc">
                        The brain is not reachable right now. Existing memories cannot be listed.
                        Chat still works: new messages are <strong>queued</strong> and will sync when memory is back.
                    </div>
                    <button class="action-btn primary" @click=${this._refreshMemories}>
                        <span class="material-symbols-outlined">refresh</span> Try again
                    </button>
                </div>
            `;
        }
        return html`
            <div class="empty-state">
                <div class="empty-icon"><span class="material-symbols-outlined">psychology</span></div>
                <div class="empty-title">No Memories Found</div>
                <div class="empty-desc">
                    ${this._searchQuery
                ? `No memories match "${this._searchQuery}"`
                : 'Start chatting with the agent to create memories.'}
                </div>
            </div>
        `;
    }

    private _renderMemoryCard(memory: Memory) {
        const typeIcons: Record<string, string> = {
            conversation: 'chat',
            fact: 'article',
            episode: 'event',
            semantic: 'hub',
        };

        const date = memory.timestamp
            ? new Date(memory.timestamp).toLocaleDateString()
            : '—';

        return html`
            <div
                class="memory-card ${this._selectedMemory?.id === memory.id ? 'selected' : ''}"
                @click=${() => this._selectMemory(memory)}
            >
                <div class="memory-header">
                    <div class="memory-type">
                        ${memory.type
                            ? html`
                        <div class="type-icon ${memory.type}">
                            <span class="material-symbols-outlined">${typeIcons[memory.type] || 'description'}</span>
                        </div>
                        <span class="type-label">${memory.type}</span>`
                            : html`
                        <div class="type-icon">
                            <span class="material-symbols-outlined">description</span>
                        </div>
                        <span class="type-label">untyped</span>`}
                    </div>
                    <span class="memory-score">${typeof memory.score === 'number' ? String(memory.score) : '—'}</span>
                </div>

                <div class="memory-content">
                    ${memory.summary || memory.content}
                </div>

                ${memory.tags.length > 0 ? html`
                    <div class="memory-tags">
                        ${memory.tags.map(tag => html`
                            <span class="tag">${tag}</span>
                        `)}
                    </div>
                ` : ''}

                <div class="memory-footer">
                    <span>${date}</span>
                    <div class="memory-actions">
                        <button class="memory-action" @click=${(e: Event) => this._copyMemory(e, memory)} title="Copy">
                            <span class="material-symbols-outlined">content_copy</span>
                        </button>
                        <button class="memory-action danger" @click=${(e: Event) => this._deleteMemory(e, memory)} title="Delete">
                            <span class="material-symbols-outlined">delete</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    private async _loadMemories() {
        this._isLoading = true;

        try {
            // SomaBrain-backed list via Agent API — GET /api/v2/memory/
            const response = await apiClient.get('/memory/') as {
                memories?: SomaMemoryHit[];
                total?: number;
            };
            const hits = Array.isArray(response?.memories) ? response.memories : [];
            this._memories = hits.map(mapSomaHit);
            // UI-S-04: `total` comes from the server only. Absent → `—`, never a
            // guess derived from the rows we happened to receive.
            this._totalCount = typeof response.total === 'number' ? response.total : null;
            this._memoryUnavailable = false;
        } catch (error) {
            // Failure is not zero memories — mark unavailable / queued.
            console.error('Failed to load memories:', error);
            this._memories = [];
            this._totalCount = null;
            this._memoryUnavailable = true;
        } finally {
            this._isLoading = false;
        }
    }

    private _handleSearch(e: Event) {
        this._searchQuery = (e.target as HTMLInputElement).value;
    }

    private _handleSearchKeydown(e: KeyboardEvent) {
        if (e.key === 'Enter') {
            this._performSearch();
        }
    }

    private async _performSearch() {
        if (!this._searchQuery.trim()) {
            this._recallHits = null;
            await this._loadMemories();
            return;
        }

        this._isLoading = true;
        try {
            // SomaBrain semantic recall via Agent API. `top_k` is omitted so
            // the server applies its declaration-site default
            // (MemoryRecallIn.top_k in admin/memory/api/memory.py). A
            // client-side top_k would be a call-site retrieval limit.
            const response = await apiClient.post('/memory/recall', {
                query: this._searchQuery,
            }) as { memories?: SomaMemoryHit[] };
            const hits = Array.isArray(response?.memories) ? response.memories : [];
            this._memories = hits.map(mapSomaHit);
            // Recall hit count is its own dashboard figure (UI-S-04 #7).
            // It is not the list total and must not overwrite it.
            this._recallHits = this._memories.length;
        } catch (error) {
            console.error('Search failed:', error);
        } finally {
            this._isLoading = false;
        }
    }

    /** Filter chips act on the server-provided type. 'all' is everything;
     *  a type chip matches only rows the server typed as that kind. */
    private get _visibleMemories(): Memory[] {
        if (this._filter === 'all') return this._memories;
        return this._memories.filter(m => m.type === this._filter);
    }

    private _setFilter(filter: MemoryFilter) {
        this._filter = filter;
    }

    /** UI-S-04 #4 — [clear] drops ?turn=current and returns to the full list. */
    private _clearThisTurn(): void {
        this._thisTurnOnly = false;
        const url = new URL(window.location.href);
        url.searchParams.delete('turn');
        window.history.replaceState(null, '', url.pathname + url.search);
        void this._loadMemories();
    }

    private _handleSort(e: Event) {
        this._sort = (e.target as HTMLSelectElement).value as MemorySort;
        // Re-sort memories
        const sorted = [...this._memories].sort((a, b) => {
            const ta = a.timestamp ? new Date(a.timestamp).getTime() : Number.NaN;
            const tb = b.timestamp ? new Date(b.timestamp).getTime() : Number.NaN;
            if (this._sort === 'newest') {
                // Missing timestamps sort last; NaN comparisons are false.
                return (Number.isNaN(tb) ? -Infinity : tb) - (Number.isNaN(ta) ? -Infinity : ta);
            } else if (this._sort === 'oldest') {
                return (Number.isNaN(ta) ? Infinity : ta) - (Number.isNaN(tb) ? Infinity : tb);
            } else {
                // Relevance. A missing score sorts last without inventing a
                // sentinel value for it.
                const sa = typeof a.score === 'number' ? a.score : Number.NEGATIVE_INFINITY;
                const sb = typeof b.score === 'number' ? b.score : Number.NEGATIVE_INFINITY;
                return sb - sa;
            }
        });
        this._memories = sorted;
    }

    private _selectMemory(memory: Memory) {
        this._selectedMemory = this._selectedMemory?.id === memory.id ? null : memory;
    }

    private _copyMemory(e: Event, memory: Memory) {
        e.stopPropagation();
        navigator.clipboard.writeText(memory.content);
    }

    private async _deleteMemory(e: Event, memory: Memory) {
        e.stopPropagation();
        if (!memory.coord) {
            console.error('Cannot delete memory without coord');
            return;
        }
        if (confirm('Delete this memory?')) {
            try {
                // SomaBrain forget — POST /api/v2/memory/forget
                await apiClient.post('/memory/forget', { coord: memory.coord });
                this._memories = this._memories.filter(m => m.id !== memory.id);
                // Decrement a known server total; do not invent one we never had.
                if (typeof this._totalCount === 'number') {
                    this._totalCount = Math.max(0, this._totalCount - 1);
                }
            } catch (error) {
                console.error('Failed to delete memory:', error);
            }
        }
    }

    /**
     * UI-S-04 action 12 — store a memory.
     * Live contract is `POST /api/v2/memory/save` `MemorySaveIn {text}`.
     * The mockup named this `/memory/remember`; the mounted router path is
     * the source of truth (admin/memory/api/memory.py:184).
     */
    private async _submitRemember(): Promise<void> {
        const text = this._rememberText.trim();
        if (!text) return;
        this._isLoading = true;
        try {
            const res = await apiClient.post<{ saved?: boolean; memory_id?: string }>(
                '/memory/save',
                { text },
            );
            if (res && res.saved === false) {
                this._rememberOk = false;
                this._rememberStatus = 'Server did not save the memory.';
                return;
            }
            this._rememberOk = true;
            this._rememberStatus = 'Stored.';
            this._rememberText = '';
            this._rememberOpen = false;
            await this._loadMemories();
        } catch (error) {
            this._rememberOk = false;
            this._rememberStatus =
                error instanceof Error ? error.message : 'Could not store the memory.';
        } finally {
            this._isLoading = false;
        }
    }

    private _exportMemories() {
        const data = JSON.stringify(this._memories, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'memories-export.json';
        a.click();
        URL.revokeObjectURL(url);
    }

    private async _refreshMemories() {
        await this._loadMemories();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-memory-view': SomaMemoryView;
    }
}
