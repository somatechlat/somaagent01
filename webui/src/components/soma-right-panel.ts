/**
 * SomaAgent01 — Right Panel surface registry (UI-X-01 … UI-X-08)
 *
 * One typed registry carries every right-rail surface specified in
 * SOMA-01-UIUX-001 §6. A surface that is not available renders
 * present-but-disabled with its blocking reason (REQ-UIX-020). Gated
 * surfaces stay on the rail; the banned placeholder phrase of §2.3 never appears.
 *
 * Backing (honest, no fabricated data):
 *   UI-X-01 Files    — GET /api/v2/filesv2/
 *   UI-X-02 Tools    — GET /api/v2/tools + live tool.* WS frames
 *   UI-X-03 Browser  — gated: no browser slot on /llm/slots, no viewport backend
 *   UI-X-04 Editor   — read-only view of a file opened from UI-X-01
 *   UI-X-05 Debug    — real WS frame ring buffer (websocket-client.ts)
 *   UI-X-06 Capsule  — <soma-capsule-editor>
 *   UI-X-07 Brain    — <soma-cognitive-panel>
 *   UI-X-08 Desktop  — GATED (REQ-UIX-007), fixed blocking reason
 */

import { LitElement, html, css, nothing, TemplateResult } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { workspaceStore } from '../stores/workspace-store.js';
import { apiClient, ApiError } from '../services/api-client.js';
import { wsFrameLog, onWsFrame, type WsFrame } from '../services/websocket-client.js';
import './soma-capsule-editor.js';
import '../views/soma-cognitive-panel.js';

// ---------------------------------------------------------------------------
// Registry (UI-C-014 order)
// ---------------------------------------------------------------------------

export type SurfaceKey =
    | 'files'
    | 'tools'
    | 'browser'
    | 'editor'
    | 'debug'
    | 'capsule'
    | 'brain'
    | 'desktop';

export interface SurfaceDef {
    key: SurfaceKey;
    /** Spec identifier from SOMA-01-UIUX-001 §6 */
    id: string;
    /** Material Symbols ligature */
    icon: string;
    label: string;
    /**
     * REQ-UIX-020: a surface that is not available SHALL render
     * present-but-disabled with its blocking reason. Absent = available.
     */
    blockedReason?: string;
}

export const SURFACES: SurfaceDef[] = [
    { key: 'files', id: 'UI-X-01', icon: 'folder', label: 'Files' },
    { key: 'tools', id: 'UI-X-02', icon: 'construction', label: 'Tools' },
    {
        key: 'browser',
        id: 'UI-X-03',
        icon: 'public',
        label: 'Browser',
        blockedReason: 'Bind a browser model on UI-S-02 first',
    },
    { key: 'editor', id: 'UI-X-04', icon: 'code', label: 'Editor' },
    { key: 'debug', id: 'UI-X-05', icon: 'bug_report', label: 'Debug' },
    { key: 'capsule', id: 'UI-X-06', icon: 'medication', label: 'Capsule' },
    { key: 'brain', id: 'UI-X-07', icon: 'neurology', label: 'Brain' },
    {
        key: 'desktop',
        id: 'UI-X-08',
        icon: 'desktop_windows',
        label: 'Desktop',
        blockedReason:
            'Requires a remote-desktop capability in somaAgent01. Not available today.',
    },
];

const SURFACE_KEYS = new Set<string>(SURFACES.map(s => s.key));

function isSurfaceKey(value: string | null): value is SurfaceKey {
    return value !== null && SURFACE_KEYS.has(value);
}

function surfaceDef(key: SurfaceKey): SurfaceDef {
    const def = SURFACES.find(s => s.key === key);
    if (!def) {
        throw new Error(`Unknown surface: ${key}`);
    }
    return def;
}

// ---------------------------------------------------------------------------
// Verified API shapes
// ---------------------------------------------------------------------------

interface FileOut {
    id: string;
    name: string;
    original_name: string;
    mime_type: string;
    size_bytes: number;
    version: number;
    storage_backend: string;
    metadata: Record<string, unknown>;
    tags: string[];
    created_at: string;
    updated_at: string;
}

interface FileListResponse {
    files: FileOut[];
    total: number;
    page: number;
    per_page: number;
}

interface DownloadUrlOut {
    download_url: string;
    expires_in: number;
    filename: string;
}

interface ToolInfo {
    name: string;
    description?: string | null;
    parameters?: Record<string, unknown> | null;
}

interface ToolsListResponse {
    tools: ToolInfo[];
    count: number;
}

interface ToolLogRow {
    id: string;
    name: string;
    status: string;
    ts: number;
}

type LoadStatus = 'idle' | 'loading' | 'ready' | 'empty' | 'error' | 'denied';

// ---------------------------------------------------------------------------
// Honest helpers
// ---------------------------------------------------------------------------

const LANG_BY_EXT: Record<string, string> = {
    ts: 'typescript',
    tsx: 'typescript',
    mts: 'typescript',
    cts: 'typescript',
    js: 'javascript',
    jsx: 'javascript',
    mjs: 'javascript',
    cjs: 'javascript',
    json: 'json',
    py: 'python',
    md: 'markdown',
    markdown: 'markdown',
    css: 'css',
    scss: 'scss',
    html: 'html',
    htm: 'html',
    xml: 'xml',
    yml: 'yaml',
    yaml: 'yaml',
    toml: 'toml',
    sh: 'shell',
    bash: 'shell',
    zsh: 'shell',
    sql: 'sql',
    csv: 'csv',
    txt: 'text',
};

function languageOf(name: string): string {
    const dot = name.lastIndexOf('.');
    if (dot <= 0 || dot === name.length - 1) return 'text';
    const ext = name.slice(dot + 1).toLowerCase();
    return LANG_BY_EXT[ext] ?? 'text';
}

/**
 * UI-X-04 Save stays present-but-disabled (REQ-UIX-020) because
 * `admin/filesv2/api.py` declares no PUT/content route for an existing
 * file — only presigned download (`/{id}/download-url`) and upload
 * (`POST /upload`). The reason travels with the control.
 */
const SAVE_DISABLED_REASON =
    'Save is unavailable: this deployment exposes no write endpoint for an existing file (filesv2 offers presigned download/upload only).';

function isTextishMime(mime: string): boolean {
    const m = (mime || '').toLowerCase().split(';')[0].trim();
    if (!m) return false;
    return (
        m.startsWith('text/') ||
        m === 'application/json' ||
        m === 'application/javascript' ||
        m === 'application/xml' ||
        m === 'application/xhtml+xml' ||
        m === 'application/x-yaml' ||
        m === 'application/yaml' ||
        m === 'application/toml' ||
        m.endsWith('+json') ||
        m.endsWith('+xml')
    );
}

function formatBytes(n: number): string {
    if (!Number.isFinite(n) || n < 0) return '—';
    if (n < 1024) return `${n} B`;
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
    return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

function formatTs(ts: number): string {
    try {
        return new Date(ts).toISOString().slice(11, 23);
    } catch {
        return String(ts);
    }
}

/** Pull the typed body out of a WS envelope ({type, payload}) or a bare body. */
function frameBody(frame: WsFrame): Record<string, unknown> {
    const p = frame.payload;
    if (p && typeof p === 'object') {
        const env = p as Record<string, unknown>;
        if ('payload' in env && env.payload && typeof env.payload === 'object') {
            return env.payload as Record<string, unknown>;
        }
        return env;
    }
    return {};
}

function toolLogFromFrames(): ToolLogRow[] {
    const rows = new Map<string, ToolLogRow>();
    for (const frame of wsFrameLog) {
        if (frame.type !== 'tool.call' && frame.type !== 'tool.done') continue;
        const body = frameBody(frame);
        const name = typeof body.name === 'string' && body.name ? body.name : 'unknown';
        const callId =
            typeof body.tool_call_id === 'string' && body.tool_call_id
                ? body.tool_call_id
                : `frame:${frame.id}`;
        const status =
            frame.type === 'tool.call' ? 'called' : body.ok === false ? 'error' : 'done';
        rows.set(callId, { id: callId, name, status, ts: frame.ts });
    }
    return Array.from(rows.values()).sort((a, b) => b.ts - a.ts);
}

// ---------------------------------------------------------------------------
// Element
// ---------------------------------------------------------------------------

@customElement('soma-right-panel')
export class SomaRightPanel extends LitElement {
    @state() private _activeTab: SurfaceKey = 'files';
    @state() private _workspaceState = workspaceStore.state;

    @state() private _files: FileOut[] = [];
    @state() private _filesTotal = 0;
    @state() private _filesStatus: LoadStatus = 'idle';
    /** Why the last list attempt failed — shown next to the error state. */
    @state() private _filesError = '';

    @state() private _tools: ToolInfo[] = [];
    @state() private _toolsStatus: LoadStatus = 'idle';
    @state() private _openToolSchema: string | null = null;

    @state() private _openFile: FileOut | null = null;
    @state() private _fileContent: string | null = null;
    @state() private _fileStatus: LoadStatus = 'idle';

    @state() private _frameFilter = '';
    @state() private _clearedBefore = 0;

    private _unsubscribeStore: (() => void) | null = null;
    private _unsubscribeFrames: (() => void) | null = null;

    static styles = css`
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
        :host {
            display: flex;
            height: 100%;
            background: var(--aaas-bg-card, #1e1e1e);
        }

        .panel {
            display: flex;
            width: 100%;
            height: 100%;
        }

        .tab-rail {
            width: 44px;
            flex-shrink: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 8px 0;
            gap: 4px;
            border-right: 1px solid var(--aaas-border-light, rgba(255, 255, 255, 0.06));
            background: var(--aaas-bg-sidebar, #ffffff);
            overflow-y: auto;
            overflow-x: hidden;
        }

        .tab-btn {
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: var(--aaas-radius-md, 8px);
            cursor: pointer;
            font-size: 16px;
            background: transparent;
            border: none;
            color: var(--aaas-text-muted, #999999);
            transition: all 150ms ease;
            position: relative;
            flex-shrink: 0;
        }

        .tab-btn:hover {
            background: var(--aaas-bg-hover, #141414);
            color: var(--aaas-text-secondary, #a1a1a1);
        }

        .tab-btn.active {
            background: var(--aaas-bg-active, #1a1a1a);
            color: var(--aaas-accent, #e8e4dc);
        }

        .tab-btn.active::before {
            content: '';
            position: absolute;
            left: -8px;
            top: 50%;
            transform: translateY(-50%);
            width: 3px;
            height: 20px;
            background: var(--aaas-accent, #e8e4dc);
            border-radius: 0 2px 2px 0;
        }

        .tab-btn.gated {
            opacity: 0.55;
            cursor: default;
        }

        .tab-tooltip {
            position: absolute;
            left: 44px;
            top: 50%;
            transform: translateY(-50%);
            background: var(--aaas-bg-hover, #141414);
            color: var(--aaas-text-secondary, #a1a1a1);
            padding: 4px 10px;
            border-radius: var(--aaas-radius-sm, 4px);
            font-size: 12px;
            white-space: nowrap;
            pointer-events: none;
            opacity: 0;
            transition: opacity 150ms ease;
            border: 1px solid var(--aaas-border-light, rgba(255, 255, 255, 0.06));
            z-index: 100;
            max-width: 240px;
        }

        .tab-btn:hover .tab-tooltip {
            opacity: 1;
        }

        .surface-content {
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 16px;
            min-width: 0;
        }

        .surface-header {
            font-size: 14px;
            font-weight: 600;
            color: var(--aaas-text-primary, #ffffff);
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--aaas-border-light, rgba(255, 255, 255, 0.06));
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .surface-id {
            font-size: 11px;
            font-weight: 500;
            color: var(--aaas-text-muted, #999999);
            letter-spacing: 0.04em;
        }

        .empty,
        .error,
        .loading {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 160px;
            color: var(--aaas-text-muted, #999999);
            font-size: 13px;
            text-align: center;
            gap: 8px;
            padding: 16px;
        }

        .error {
            color: var(--aaas-danger, #f87171);
        }

        .disabled-frame {
            border: 1px dashed var(--aaas-border-light, rgba(255, 255, 255, 0.12));
            border-radius: var(--aaas-radius-md, 8px);
            padding: 24px 16px;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            gap: 12px;
            color: var(--aaas-text-secondary, #a1a1a1);
            font-size: 13px;
            line-height: 1.5;
        }

        .disabled-reason {
            color: var(--aaas-text-primary, #ffffff);
            font-weight: 600;
            font-size: 13px;
        }

        .disabled-note {
            color: var(--aaas-text-muted, #999999);
            font-size: 12px;
        }

        .row-list {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .row {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 10px;
            border-radius: var(--aaas-radius-sm, 4px);
            cursor: pointer;
            color: var(--aaas-text-secondary, #a1a1a1);
            font-size: 12px;
            border: 1px solid transparent;
        }

        .row:hover {
            background: var(--aaas-bg-hover, #141414);
            color: var(--aaas-text-primary, #ffffff);
        }

        .row-main {
            flex: 1;
            min-width: 0;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .row-title {
            color: inherit;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .row-sub {
            color: var(--aaas-text-muted, #999999);
            font-size: 11px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .row-meta {
            color: var(--aaas-text-muted, #999999);
            font-size: 11px;
            flex-shrink: 0;
            font-variant-numeric: tabular-nums;
        }

        .chip {
            display: inline-flex;
            align-items: center;
            padding: 1px 8px;
            border-radius: 999px;
            font-size: 11px;
            border: 1px solid var(--aaas-border-light, rgba(255, 255, 255, 0.12));
            color: var(--aaas-text-secondary, #a1a1a1);
            background: var(--aaas-bg-hover, #141414);
            flex-shrink: 0;
        }

        .section-label {
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: var(--aaas-text-muted, #999999);
            margin: 16px 0 8px;
        }

        .toolbar {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
        }

        .toolbar input {
            flex: 1;
            min-width: 0;
            background: var(--aaas-bg-hover, #141414);
            border: 1px solid var(--aaas-border-light, rgba(255, 255, 255, 0.12));
            border-radius: var(--aaas-radius-sm, 4px);
            color: var(--aaas-text-primary, #ffffff);
            font-size: 12px;
            padding: 6px 10px;
        }

        .toolbar input:focus {
            outline: 1px solid var(--aaas-accent, #e8e4dc);
        }

        .btn {
            background: var(--aaas-bg-hover, #141414);
            border: 1px solid var(--aaas-border-light, rgba(255, 255, 255, 0.12));
            border-radius: var(--aaas-radius-sm, 4px);
            color: var(--aaas-text-secondary, #a1a1a1);
            font-size: 12px;
            padding: 6px 10px;
            cursor: pointer;
        }

        .btn:hover {
            color: var(--aaas-text-primary, #ffffff);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .schema {
            margin-top: 6px;
            padding: 8px;
            border-radius: var(--aaas-radius-sm, 4px);
            background: var(--aaas-bg-hover, #141414);
            border: 1px solid var(--aaas-border-light, rgba(255, 255, 255, 0.08));
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 11px;
            color: var(--aaas-text-secondary, #a1a1a1);
            white-space: pre-wrap;
            word-break: break-word;
            max-height: 180px;
            overflow: auto;
        }

        .editor-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }

        .editor-name {
            font-size: 13px;
            font-weight: 600;
            color: var(--aaas-text-primary, #ffffff);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            min-width: 0;
        }

        .readonly-note {
            font-size: 12px;
            color: var(--aaas-text-muted, #999999);
            line-height: 1.5;
            margin-bottom: 12px;
        }

        .editor-save {
            margin-left: auto;
            flex-shrink: 0;
        }

        .code-block {
            margin: 0;
            padding: 12px;
            border-radius: var(--aaas-radius-sm, 4px);
            background: var(--aaas-bg-hover, #141414);
            border: 1px solid var(--aaas-border-light, rgba(255, 255, 255, 0.08));
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 12px;
            line-height: 1.5;
            color: var(--aaas-text-secondary, #a1a1a1);
            white-space: pre-wrap;
            word-break: break-word;
            overflow-x: auto;
        }

        .frame-row {
            display: grid;
            grid-template-columns: 64px 28px 120px 1fr;
            gap: 8px;
            padding: 6px 8px;
            border-radius: var(--aaas-radius-sm, 4px);
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 11px;
            color: var(--aaas-text-secondary, #a1a1a1);
            border-bottom: 1px solid var(--aaas-border-light, rgba(255, 255, 255, 0.04));
            align-items: start;
        }

        .frame-row:hover {
            background: var(--aaas-bg-hover, #141414);
        }

        .frame-dir {
            color: var(--aaas-accent, #e8e4dc);
        }

        .frame-type {
            color: var(--aaas-text-primary, #ffffff);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .frame-payload {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            opacity: 0.85;
        }

        .frame-ts {
            color: var(--aaas-text-muted, #999999);
            font-variant-numeric: tabular-nums;
        }
    `;

    connectedCallback() {
        super.connectedCallback();
        this._unsubscribeStore = workspaceStore.subscribe(() => {
            this._workspaceState = workspaceStore.state;
            const s = this._workspaceState.activeSurface;
            if (isSurfaceKey(s)) {
                this._activeTab = s;
            }
        });
        // Prefer a surface the store already persists among the eight.
        const persisted = this._workspaceState.activeSurface;
        if (isSurfaceKey(persisted)) {
            this._activeTab = persisted;
        }
        this._unsubscribeFrames = onWsFrame(() => this.requestUpdate());
    }

    updated() {
        // Lazy-load the real listings the first time their surface is shown.
        if (this._activeTab === 'files' && this._filesStatus === 'idle') {
            void this._loadFiles();
        }
        if (this._activeTab === 'tools' && this._toolsStatus === 'idle') {
            void this._loadTools();
        }
    }

    disconnectedCallback() {
        this._unsubscribeStore?.();
        this._unsubscribeStore = null;
        this._unsubscribeFrames?.();
        this._unsubscribeFrames = null;
        super.disconnectedCallback();
    }

    private _selectTab(tab: SurfaceKey) {
        this._activeTab = tab;
        workspaceStore.setSurface(tab);
        if (tab === 'files') void this._loadFiles();
        if (tab === 'tools') void this._loadTools();
    }

    // -- Files (UI-X-01) ----------------------------------------------------

    private async _loadFiles(): Promise<void> {
        if (this._filesStatus === 'loading') return;
        this._filesStatus = 'loading';
        this._filesError = '';
        try {
            const res = await apiClient.get<FileListResponse>(
                '/filesv2/?page=1&per_page=50'
            );
            this._files = res.files ?? [];
            this._filesTotal = res.total ?? this._files.length;
            this._filesStatus = this._files.length === 0 ? 'empty' : 'ready';
        } catch (err) {
            if (err instanceof ApiError && err.status === 403) {
                this._filesStatus = 'denied';
            } else {
                this._filesStatus = 'error';
                // A failed load is not an empty workspace — say exactly which
                // request broke instead of a bare "something went wrong".
                this._filesError =
                    err instanceof ApiError
                        ? err.status > 0
                            ? `GET /api/v2/filesv2/ refused (HTTP ${err.status})`
                            : `${err.message || 'network error'} — GET /api/v2/filesv2/`
                        : `GET /api/v2/filesv2/ — ${err instanceof Error ? err.message : 'unknown error'}`;
            }
        }
    }

    private async _openFileInEditor(file: FileOut): Promise<void> {
        this._openFile = file;
        this._fileContent = null;
        this._fileStatus = 'loading';
        this._selectTab('editor');

        if (!isTextishMime(file.mime_type)) {
            this._fileStatus = 'error';
            return;
        }

        try {
            const signed = await apiClient.get<DownloadUrlOut>(
                `/filesv2/${encodeURIComponent(file.id)}/download-url`
            );
            const res = await fetch(signed.download_url);
            if (!res.ok) {
                this._fileStatus = 'error';
                return;
            }
            this._fileContent = await res.text();
            this._fileStatus = 'ready';
        } catch {
            this._fileStatus = 'error';
        }
    }

    // -- Tools (UI-X-02) ----------------------------------------------------

    private async _loadTools(): Promise<void> {
        if (this._toolsStatus === 'loading') return;
        this._toolsStatus = 'loading';
        try {
            const res = await apiClient.get<ToolsListResponse>('/tools');
            this._tools = res.tools ?? [];
            this._toolsStatus = this._tools.length === 0 ? 'empty' : 'ready';
        } catch (err) {
            if (err instanceof ApiError && err.status === 403) {
                this._toolsStatus = 'denied';
            } else {
                this._toolsStatus = 'error';
            }
        }
    }

    // -- Render -------------------------------------------------------------

    render() {
        return html`
            <div class="panel">
                <div class="tab-rail" role="tablist" aria-label="Right-rail surfaces">
                    ${SURFACES.map(s => this._renderRailButton(s))}
                </div>
                <div class="surface-content">
                    ${this._renderSurface()}
                </div>
            </div>
        `;
    }

    private _renderRailButton(s: SurfaceDef) {
        const active = this._activeTab === s.key;
        const gated = s.blockedReason !== undefined;
        // REQ-UIX-020: gated surfaces stay visible and selectable so their
        // disabled frame (with the blocking reason) can be shown. They are
        // never omitted and never presented as working surfaces.
        const title = gated && s.blockedReason ? s.blockedReason : s.label;
        return html`
            <button
                class="tab-btn ${active ? 'active' : ''} ${gated ? 'gated' : ''}"
                role="tab"
                aria-selected=${active ? 'true' : 'false'}
                aria-disabled=${gated ? 'true' : 'false'}
                aria-label=${title}
                title=${title}
                @click=${() => this._selectTab(s.key)}
            >
                <span class="material-symbols-outlined tab-icon">${s.icon}</span>
                <span class="tab-tooltip">${title}</span>
            </button>
        `;
    }

    private _renderSurface(): TemplateResult {
        const def = surfaceDef(this._activeTab);
        const header = html`
            <div class="surface-header">
                <span>${def.label}</span>
                <span class="surface-id">${def.id}</span>
            </div>
        `;

        switch (this._activeTab) {
            case 'files':
                return html`${header}${this._renderFiles()}`;
            case 'tools':
                return html`${header}${this._renderTools()}`;
            case 'browser':
                return html`${header}${this._renderBrowser(def)}`;
            case 'editor':
                return html`${header}${this._renderEditor()}`;
            case 'debug':
                return html`${header}${this._renderDebug()}`;
            case 'capsule':
                return html`${header}<soma-capsule-editor></soma-capsule-editor>`;
            case 'brain':
                return html`${header}<soma-cognitive-panel></soma-cognitive-panel>`;
            case 'desktop':
                return html`${header}${this._renderDesktop(def)}`;
            default:
                return html`${header}`;
        }
    }

    private _renderFiles(): TemplateResult {
        if (this._filesStatus === 'idle' || this._filesStatus === 'loading') {
            return html`<div class="loading">Loading files…</div>`;
        }
        if (this._filesStatus === 'error') {
            return html`<div class="error" role="alert">
                <span>Files could not be listed.</span>
                ${this._filesError
                    ? html`<span class="row-sub">${this._filesError}</span>`
                    : nothing}
                <button
                    class="btn"
                    @click=${() => void this._loadFiles()}
                    aria-label="Retry listing files"
                >
                    Retry
                </button>
            </div>`;
        }
        if (this._filesStatus === 'denied') {
            return html`<div class="error">
                You need <code>files:read</code> to browse files.
            </div>`;
        }
        if (this._filesStatus === 'empty' || this._files.length === 0) {
            return html`<div class="empty">
                <span>No files in the working set.</span>
                <span class="row-sub">
                    filesv2 storage only — agent work-directory files (file_list /
                    file_write tools) have no list API in this deployment.
                </span>
            </div>`;
        }

        return html`
            <div class="row-list" role="list">
                ${this._files.map(
                    f => html`
                        <div
                            class="row"
                            role="listitem"
                            tabindex="0"
                            @click=${() => void this._openFileInEditor(f)}
                            @keydown=${(e: KeyboardEvent) => {
                                if (e.key === 'Enter' || e.key === ' ') {
                                    e.preventDefault();
                                    void this._openFileInEditor(f);
                                }
                            }}
                        >
                            <span class="material-symbols-outlined">description</span>
                            <div class="row-main">
                                <div class="row-title">${f.original_name || f.name}</div>
                                <div class="row-sub">${f.mime_type || '—'} · v${f.version}</div>
                            </div>
                            <div class="row-meta">${formatBytes(f.size_bytes)}</div>
                        </div>
                    `
                )}
            </div>
            ${this._filesTotal > this._files.length
                ? html`<div class="row-sub" style="margin-top:8px">
                      showing ${this._files.length} of ${this._filesTotal}
                  </div>`
                : nothing}
        `;
    }

    private _renderTools(): TemplateResult {
        const log = toolLogFromFrames();
        const listBlock = (() => {
            if (this._toolsStatus === 'idle' || this._toolsStatus === 'loading') {
                return html`<div class="loading">Loading tools…</div>`;
            }
            if (this._toolsStatus === 'error') {
                return html`<div class="error">Tools could not be loaded.</div>`;
            }
            if (this._toolsStatus === 'denied') {
                return html`<div class="error">
                    You need <code>capability:read</code> to view tools.
                </div>`;
            }
            if (this._toolsStatus === 'empty' || this._tools.length === 0) {
                return html`<div class="empty">No tools attached to this capsule.</div>`;
            }
            return html`
                <div class="row-list" role="list">
                    ${this._tools.map(t => {
                        const open = this._openToolSchema === t.name;
                        const hasSchema =
                            t.parameters != null &&
                            typeof t.parameters === 'object' &&
                            Object.keys(t.parameters).length > 0;
                        return html`
                            <div
                                class="row"
                                role="listitem"
                                style="cursor:default; align-items:flex-start;"
                            >
                                <div class="row-main">
                                    <div class="row-title">${t.name}</div>
                                    ${t.description
                                        ? html`<div class="row-sub">${t.description}</div>`
                                        : nothing}
                                    ${hasSchema
                                        ? html`
                                              <button
                                                  class="btn"
                                                  style="margin-top:6px; align-self:flex-start;"
                                                  @click=${() => {
                                                      this._openToolSchema = open ? null : t.name;
                                                  }}
                                                  aria-expanded=${open ? 'true' : 'false'}
                                              >
                                                  ${open ? 'Hide schema' : 'Show schema'}
                                              </button>
                                              ${open
                                                  ? html`<pre class="schema">${JSON.stringify(
                                                        t.parameters,
                                                        null,
                                                        2
                                                    )}</pre>`
                                                  : nothing}
                                          `
                                        : nothing}
                                </div>
                            </div>
                        `;
                    })}
                </div>
            `;
        })();

        const logBlock = html`
            <div class="section-label">Live call log</div>
            ${
                log.length === 0
                    ? html`<div class="empty">No tool calls in this session yet.</div>`
                    : html`
                          <div class="row-list" role="list">
                              ${log.map(
                                  r => html`
                                      <div class="row" role="listitem" style="cursor:default;">
                                          <div class="row-main">
                                              <div class="row-title">${r.name}</div>
                                          </div>
                                          <span class="chip">${r.status}</span>
                                          <div class="row-meta">${formatTs(r.ts)}</div>
                                      </div>
                                  `
                              )}
                          </div>
                      `
            }
        `;

        return html`${listBlock}${logBlock}`;
    }

    private _renderBrowser(def: SurfaceDef): TemplateResult {
        // /llm/slots carries chat/utility/embedding only — there is no browser
        // slot on that surface and no browser viewport backend in this
        // deployment, so binding cannot be verified and the surface stays
        // present-but-disabled (REQ-UIX-020).
        const reason =
            def.blockedReason ?? 'Bind a browser model on UI-S-02 first';
        return html`
            <div class="disabled-frame" aria-disabled="true">
                <div class="disabled-reason">${reason}</div>
                <div class="disabled-note">
                    This deployment exposes no browser slot; binding cannot be verified here.
                </div>
            </div>
        `;
    }

    private _renderEditor(): TemplateResult {
        if (!this._openFile) {
            return html`<div class="empty">No file open.</div>`;
        }

        const file = this._openFile;
        const lang = languageOf(file.original_name || file.name);

        if (this._fileStatus === 'loading') {
            return html`
                <div class="editor-header">
                    <div class="editor-name">${file.original_name || file.name}</div>
                    <span class="chip">${lang}</span>
                </div>
                <div class="loading">Opening file…</div>
            `;
        }

        if (this._fileStatus === 'error' || this._fileContent === null) {
            return html`
                <div class="editor-header">
                    <div class="editor-name">${file.original_name || file.name}</div>
                    <span class="chip">${lang}</span>
                </div>
                <div class="error">File content could not be loaded.</div>
            `;
        }

        return html`
            <div class="editor-header">
                <div class="editor-name">${file.original_name || file.name}</div>
                <span class="chip">${lang}</span>
                <button
                    class="btn editor-save"
                    disabled
                    aria-disabled="true"
                    title=${SAVE_DISABLED_REASON}
                    aria-label=${`Save — disabled. ${SAVE_DISABLED_REASON}`}
                >
                    Save
                </button>
            </div>
            <div class="readonly-note">
                This deployment exposes no file-write endpoint; the buffer is read-only.
                Save stays disabled: filesv2 exposes only presigned download
                (<code>GET /filesv2/{id}/download-url</code>) and upload
                (<code>POST /filesv2/upload</code>) — there is no PUT/content route for
                an existing file, so a save would have nowhere honest to write.
            </div>
            <pre class="code-block">${this._fileContent}</pre>
        `;
    }

    private _renderDebug(): TemplateResult {
        const filter = this._frameFilter.trim().toLowerCase();
        const frames = wsFrameLog
            .filter(f => f.ts > this._clearedBefore)
            .filter(f => {
                if (!filter) return true;
                const type = f.type.toLowerCase();
                if (type.includes(filter)) return true;
                try {
                    return JSON.stringify(f.payload).toLowerCase().includes(filter);
                } catch {
                    return false;
                }
            })
            .slice()
            .reverse();

        return html`
            <div class="toolbar">
                <input
                    type="search"
                    placeholder="Filter frames"
                    aria-label="Filter frames"
                    .value=${this._frameFilter}
                    @input=${(e: Event) => {
                        this._frameFilter = (e.target as HTMLInputElement).value;
                    }}
                />
                <button
                    class="btn"
                    @click=${() => {
                        // UI-A-117: clear local view buffer only.
                        this._clearedBefore = Date.now();
                    }}
                >
                    Clear stream
                </button>
            </div>
            ${
                frames.length === 0
                    ? html`<div class="empty">No events yet.</div>`
                    : html`
                          <div role="log" aria-label="WebSocket frames">
                              ${frames.map(
                                  f => html`
                                      <div class="frame-row">
                                          <span class="frame-ts">${formatTs(f.ts)}</span>
                                          <span class="frame-dir">${f.dir === 'in' ? '←' : '→'}</span>
                                          <span class="frame-type">${f.type}</span>
                                          <span class="frame-payload" title=${this._payloadTitle(f)}
                                              >${this._payloadPreview(f)}</span
                                          >
                                      </div>
                                  `
                              )}
                          </div>
                      `
            }
        `;
    }

    private _payloadPreview(f: WsFrame): string {
        try {
            const s = JSON.stringify(f.payload);
            return s.length > 120 ? `${s.slice(0, 120)}…` : s;
        } catch {
            return String(f.payload);
        }
    }

    private _payloadTitle(f: WsFrame): string {
        try {
            return JSON.stringify(f.payload);
        } catch {
            return String(f.payload);
        }
    }

    private _renderDesktop(def: SurfaceDef): TemplateResult {
        const reason =
            def.blockedReason ??
            'Requires a remote-desktop capability in somaAgent01. Not available today.';
        return html`
            <div class="disabled-frame" aria-disabled="true">
                <div class="disabled-reason">${reason}</div>
                <button class="btn" disabled title=${reason} aria-label=${reason}>
                    Open desktop session
                </button>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-right-panel': SomaRightPanel;
    }
}
