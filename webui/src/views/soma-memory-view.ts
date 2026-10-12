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
    static styles = css`
        :host {
            display: flex;
            height: 100vh;
            background: var(--soma-bg-page, #f5f5f5);
            font-family: var(--soma-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            color: var(--soma-text-primary, #1a1a1a);
        }

        * {
            box-sizing: border-box;
        }

        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: 20px;
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
            width: 280px;
            background: var(--soma-bg-card, #ffffff);
            border-right: 1px solid var(--soma-border-light, #e0e0e0);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            padding: 24px 20px;
        }

        .sidebar-header {
            margin-bottom: 24px;
        }

        .sidebar-title {
            font-size: 20px;
            font-weight: 600;
            margin: 0 0 4px 0;
        }

        .sidebar-subtitle {
            font-size: 13px;
            color: var(--soma-text-secondary, #666);
        }

        /* Search */
        .search-box {
            position: relative;
            margin-bottom: 20px;
        }

        .search-input {
            width: 100%;
            padding: 10px 14px 10px 42px;
            border-radius: 8px;
            border: 1px solid var(--soma-border-light, #e0e0e0);
            font-size: 14px;
            background: var(--soma-bg-card, #ffffff);
            color: var(--soma-text-primary, #1a1a1a);
            transition: border-color 0.15s ease;
        }

        .search-input:focus {
            outline: none;
            border-color: var(--soma-text-primary, #1a1a1a);
        }

        .search-icon {
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--soma-text-muted, #999);
            font-size: 18px;
        }

        /* Filters */
        .filter-section {
            margin-bottom: 24px;
        }

        .filter-label {
            font-size: 11px;
            text-transform: uppercase;
            color: var(--soma-text-muted, #999);
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }

        .filter-options {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .filter-chip {
            padding: 6px 12px;
            border-radius: 16px;
            background: var(--soma-bg-hover, #fafafa);
            border: 1px solid var(--soma-border-light, #e0e0e0);
            font-size: 13px;
            cursor: pointer;
            transition: all 0.1s ease;
        }

        .filter-chip:hover {
            border-color: var(--soma-border-medium, #ccc);
        }

        .filter-chip.active {
            background: #1a1a1a;
            color: white;
            border-color: #1a1a1a;
        }

        /* Sort */
        .sort-select {
            width: 100%;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid var(--soma-border-light, #e0e0e0);
            font-size: 14px;
            background: var(--soma-bg-card, #ffffff);
            color: var(--soma-text-primary, #1a1a1a);
            cursor: pointer;
        }

        /* Stats */
        .stats {
            margin-top: auto;
            padding-top: 20px;
            border-top: 1px solid var(--soma-border-light, #e0e0e0);
        }

        .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            font-size: 13px;
        }

        .stat-label {
            color: var(--soma-text-secondary, #666);
        }

        .stat-value {
            font-weight: 600;
        }

        .stat-value.queued {
            color: #b45309;
        }

        /* MEMORY DASHBOARD (UI-S-04 §3.7) */
        .memory-dashboard {
            margin-top: auto;
            padding-top: 16px;
            border-top: 1px solid var(--soma-border-light, #e0e0e0);
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }

        .dash-tile {
            display: flex;
            flex-direction: column;
            gap: 2px;
            padding: 8px 10px;
            border: 1px solid var(--soma-border-light, #e0e0e0);
            border-radius: 8px;
            background: var(--soma-bg-hover, #fafafa);
        }

        .dash-value {
            font-size: 16px;
            font-weight: 650;
            line-height: 1.2;
        }

        .dash-value.gated {
            color: var(--soma-text-muted, #999);
        }

        .dash-value.queued {
            color: #b45309;
        }

        .dash-label {
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            color: var(--soma-text-secondary, #666);
        }

        .dash-note {
            font-size: 10px;
            color: var(--soma-text-muted, #999);
        }

        .dash-footnote {
            grid-column: 1 / -1;
            margin: 2px 0 0;
            font-size: 10px;
            line-height: 1.4;
            color: var(--soma-text-muted, #999);
        }

        /* Remember… form (UI-S-04 action 12) */
        .remember-form {
            margin: 12px 0;
            padding: 12px;
            border: 1px solid var(--soma-border-light, #e0e0e0);
            border-radius: 10px;
            background: var(--soma-bg-hover, #fafafa);
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .remember-form textarea {
            width: 100%;
            min-height: 64px;
            resize: vertical;
            padding: 8px 10px;
            border: 1px solid var(--soma-border-light, #e0e0e0);
            border-radius: 8px;
            font: inherit;
            font-size: 13px;
            background: #fff;
            color: var(--soma-text-primary, #1a1a1a);
        }

        .remember-actions {
            display: flex;
            gap: 8px;
            align-items: center;
        }

        .remember-status {
            font-size: 12px;
        }

        .remember-status.ok {
            color: #047857;
        }

        .remember-status.err {
            color: #b91c1c;
        }

        .probe-btn {
            margin-top: 8px;
            width: 100%;
            padding: 8px 10px;
            border: 1px solid var(--soma-border-light, #e0e0e0);
            border-radius: 8px;
            background: #fff;
            color: var(--soma-text-primary, #1a1a1a);
            font: inherit;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
        }

        .probe-btn:hover {
            background: var(--soma-bg-hover, #fafafa);
        }

        .memory-queued-banner {
            display: flex;
            gap: 10px;
            align-items: flex-start;
            margin: 12px 0 4px;
            padding: 10px 12px;
            border-radius: 10px;
            border: 1px solid rgba(245, 158, 11, 0.45);
            background: rgba(245, 158, 11, 0.12);
            color: #92400e;
            font-size: 12px;
            line-height: 1.4;
        }

        .memory-queued-banner .material-symbols-outlined {
            font-size: 18px;
            color: #d97706;
            margin-top: 1px;
        }

        .memory-queued-banner strong {
            display: block;
            color: #b45309;
            margin-bottom: 2px;
        }

        .memory-queued-banner p {
            margin: 0;
        }

        .queued-pill {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            margin-right: 8px;
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 600;
            color: #b45309;
            border: 1px solid rgba(245, 158, 11, 0.5);
            background: rgba(245, 158, 11, 0.15);
        }

        .memory-unavailable-bar {
            margin: 0 0 16px;
            padding: 12px 16px;
            border-radius: 10px;
            border: 1px solid rgba(245, 158, 11, 0.4);
            background: rgba(245, 158, 11, 0.1);
            color: #92400e;
            font-size: 13px;
        }

        .empty-state.unavailable .empty-icon.warn {
            background: rgba(245, 158, 11, 0.15);
            color: #d97706;
        }

        .empty-state.unavailable .empty-title {
            color: #b45309;
        }

        .empty-state .action-btn {
            margin-top: 16px;
        }

        /* Back Button */
        .back-btn {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 14px;
            border-radius: 8px;
            background: transparent;
            border: 1px solid var(--soma-border-light, #e0e0e0);
            font-size: 14px;
            cursor: pointer;
            color: var(--soma-text-primary, #1a1a1a);
            margin-top: 16px;
            transition: all 0.1s ease;
        }

        .back-btn:hover {
            background: var(--soma-bg-hover, #fafafa);
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
            padding: 16px 24px;
            background: var(--soma-bg-card, #ffffff);
            border-bottom: 1px solid var(--soma-border-light, #e0e0e0);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .result-count {
            font-size: 14px;
            color: var(--soma-text-secondary, #666);
        }

        .header-actions {
            display: flex;
            gap: 8px;
        }

        .action-btn {
            padding: 8px 16px;
            border-radius: 8px;
            border: 1px solid var(--soma-border-light, #e0e0e0);
            background: var(--soma-bg-card, #ffffff);
            font-size: 13px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.1s ease;
        }

        .action-btn:hover {
            background: var(--soma-bg-hover, #fafafa);
        }

        .action-btn.primary {
            background: #1a1a1a;
            color: white;
            border-color: #1a1a1a;
        }

        .action-btn.primary:hover {
            background: #333;
        }

        .action-btn .material-symbols-outlined {
            font-size: 18px;
        }

        /* Memory Grid */
        .memory-grid {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 16px;
            align-content: start;
        }

        /* Memory Card */
        .memory-card {
            background: var(--soma-bg-card, #ffffff);
            border: 1px solid var(--soma-border-light, #e0e0e0);
            border-radius: 12px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .memory-card:hover {
            border-color: var(--soma-border-medium, #ccc);
            box-shadow: var(--soma-shadow-sm, 0 2px 4px rgba(0,0,0,0.04));
        }

        .memory-card.selected {
            border-color: #1a1a1a;
            box-shadow: 0 0 0 1px #1a1a1a;
        }

        .memory-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            margin-bottom: 12px;
        }

        .memory-type {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .type-icon {
            width: 28px;
            height: 28px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .type-icon .material-symbols-outlined {
            font-size: 16px;
        }

        .type-icon.conversation { background: #e0f2fe; color: #0369a1; }
        .type-icon.fact { background: #fef3c7; color: #b45309; }
        .type-icon.episode { background: #e0e7ff; color: #4338ca; }
        .type-icon.semantic { background: #d1fae5; color: #047857; }

        .type-label {
            font-size: 12px;
            font-weight: 500;
            text-transform: capitalize;
            color: var(--soma-text-secondary, #666);
        }

        .memory-score {
            font-size: 12px;
            font-weight: 600;
            padding: 4px 8px;
            border-radius: 4px;
            background: var(--soma-bg-hover, #fafafa);
        }

        .memory-content {
            font-size: 14px;
            line-height: 1.6;
            color: var(--soma-text-primary, #1a1a1a);
            margin-bottom: 12px;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .memory-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 12px;
        }

        .tag {
            padding: 4px 8px;
            border-radius: 4px;
            background: var(--soma-bg-hover, #fafafa);
            font-size: 11px;
            color: var(--soma-text-secondary, #666);
        }

        .memory-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            color: var(--soma-text-muted, #999);
        }

        .memory-actions {
            display: flex;
            gap: 4px;
        }

        .memory-action {
            width: 28px;
            height: 28px;
            border-radius: 6px;
            background: transparent;
            border: none;
            color: var(--soma-text-muted, #999);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.1s ease;
        }

        .memory-action:hover {
            background: var(--soma-bg-hover, #fafafa);
            color: var(--soma-text-primary, #1a1a1a);
        }

        .memory-action.danger:hover {
            color: var(--soma-status-danger, #ef4444);
        }

        .memory-action .material-symbols-outlined {
            font-size: 16px;
        }

        /* Empty State */
        .empty-state {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 40px;
        }

        .empty-icon {
            width: 64px;
            height: 64px;
            background: var(--soma-bg-hover, #fafafa);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 20px;
        }

        .empty-icon .material-symbols-outlined {
            font-size: 28px;
            color: var(--soma-text-secondary, #666);
        }

        .empty-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .empty-desc {
            font-size: 14px;
            color: var(--soma-text-secondary, #666);
            max-width: 320px;
        }

        /* Loading */
        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 60px;
        }

        .spinner {
            width: 32px;
            height: 32px;
            border: 3px solid var(--soma-border-light, #e0e0e0);
            border-top-color: #1a1a1a;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    `;

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
                                      this turn ✕
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
                                ? html`<span class="queued-pill">● Queued</span> ${this._visibleMemories.length} shown`
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
