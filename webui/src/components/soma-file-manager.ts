/**
 * soma-file-manager — M-024 File Manager (CM-02 control map).
 *
 * Real bindings (no mocks):
 *   GET    /api/v2/filesv2/?page=&per_page=   list (LIVE)
 *   GET    /api/v2/filesv2/{id}/download-url  signed GET (S3-backed)
 *   POST   /api/v2/filesv2/upload             presigned PUT or upload-local (LIVE)
 *   DELETE /api/v2/filesv2/{id}               soft delete (LIVE)
 *
 * Honest gates (present-but-disabled with reason — never a fake control):
 *   GET    /api/v2/workroot/tree              tree + breadcrumb  (absent → gate)
 *   PATCH  /api/v2/filesv2/{id}               rename             (absent → gate)
 *   POST   /api/v2/workroot/mkdir             new folder         (absent → gate)
 *   POST   /api/v2/workroot/move               move               (absent → gate)
 *   PUT    /api/v2/filesv2/{id}/content       editor save        (absent → gate)
 *
 * Standard locations: workroot / inbox (tree chrome; list stays filesv2).
 * Modes: browse | select (composer attach) | manage.
 */

import { LitElement, css, html, nothing, TemplateResult } from 'lit';
import { customElement, property, query, state } from 'lit/decorators.js';
import { apiClient, ApiError } from '../services/api-client.js';
import { uploadAttachment, type AttachmentMeta } from '../services/file-upload.js';
import { formatBytes } from '../utils/markdown.js';
import { attachmentIcon } from '../utils/file-icons.js';
import './soma-file-preview.js';
import './soma-glass-modal.js';
import type { SomaGlassModal } from './soma-glass-modal.js';

// ---------------------------------------------------------------------------
// Verified API shapes (admin/filesv2/api.py)
// ---------------------------------------------------------------------------

export interface FileOut {
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

export interface FileListResponse {
    files: FileOut[];
    total: number;
    page: number;
    per_page: number;
}

export type FileListResponseEnvelope =
    | FileListResponse
    | { items: FileOut[]; total?: number; page?: number; pageSize?: number };

interface DownloadUrlOut {
    download_url: string;
    expires_in: number;
    filename: string;
}

type LoadStatus = 'idle' | 'loading' | 'ready' | 'empty' | 'error' | 'denied';

export type FileManagerMode = 'browse' | 'select' | 'manage';

interface UploadTrayItem {
    key: string;
    name: string;
    size: number;
    state: 'uploading' | 'complete' | 'failed';
    fileId?: string;
    error?: string;
}

// ---------------------------------------------------------------------------
// Gates — target endpoints named in CM-02 that are not mounted in this API
// ---------------------------------------------------------------------------

const RENAME_DISABLED_REASON =
    'Rename needs the filesv2 write API (PATCH /api/v2/filesv2/{id}).';

const NEW_FOLDER_DISABLED_REASON =
    'New folder needs the workroot write API (POST /api/v2/workroot/mkdir).';

const TREE_ABSENT_REASON =
    'Workroot tree is not available on this deployment. GET /api/v2/workroot/tree is not mounted.';

const EDITOR_SAVE_DISABLED_REASON =
    'Editor Save needs the filesv2 content write API (PUT /api/v2/filesv2/{id}/content).';

const MOVE_DISABLED_REASON =
    'Move needs the workroot write API (POST /api/v2/workroot/move).';

const INBOX_PATH = 'inbox';
const WORKROOT_ROOT = 'workroot';

function reasonOf(err: unknown): string {
    if (err instanceof ApiError) {
        if (!err.status) return err.message || 'network error — request never reached the API';
        return `${err.message || 'request failed'} (HTTP ${err.status})`;
    }
    if (err instanceof Error && err.message) return err.message;
    return 'request failed';
}

function fileName(f: FileOut): string {
    return f.original_name || f.name || f.id;
}

/** Normalize paginated or raw FileListResponse shapes from api-client. */
function normalizeFileList(res: FileListResponseEnvelope): {
    files: FileOut[];
    total: number;
} {
    if (res && Array.isArray((res as FileListResponse).files)) {
        const r = res as FileListResponse;
        return { files: r.files, total: r.total ?? r.files.length };
    }
    const r = res as { items?: FileOut[]; total?: number };
    const files = Array.isArray(r?.items) ? r.items : [];
    return { files, total: r?.total ?? files.length };
}

@customElement('soma-file-manager')
export class SomaFileManager extends LitElement {
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
            flex-direction: column;
            min-height: 0;
            height: 100%;
            color: var(--skin-color-text-primary, #1a1a1a);
            font-family: var(--skin-font-sans, system-ui, sans-serif);
            background: var(--skin-color-bg-card, rgba(255, 255, 255, 0.72));
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
            border-radius: var(--skin-radius-lg, 12px);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            overflow: hidden;
        }

        .top {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: var(--skin-space-sm, 8px);
            padding: var(--skin-space-sm, 10px) var(--skin-space-md, 14px);
            border-bottom: 1px solid var(--skin-color-border-subtle, rgba(0, 0, 0, 0.05));
        }

        .crumb {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            min-width: 0;
            font-size: var(--skin-text-sm, 12px);
            color: var(--skin-color-text-secondary, #555555);
        }

        .crumb .sep {
            opacity: 0.55;
        }

        .crumb .current {
            color: var(--skin-color-text-primary, #1a1a1a);
            font-weight: var(--skin-weight-medium, 500);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            max-width: 220px;
        }

        .search {
            flex: 1;
            min-width: 140px;
            max-width: 280px;
            height: 32px;
            padding: 0 10px;
            border-radius: var(--skin-radius-md, 8px);
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.1));
            background: var(--skin-color-bg-base, transparent);
            color: var(--skin-color-text-primary, #1a1a1a);
            font-size: var(--skin-text-sm, 12px);
            font-family: inherit;
        }

        .search:focus {
            outline: none;
            border-color: var(--skin-focus-ring, var(--skin-color-accent, #3b82f6));
            box-shadow: 0 0 0 var(--skin-focus-ring-width, 2px)
                color-mix(in srgb, var(--skin-focus-ring, #3b82f6) 35%, transparent);
        }

        .spacer {
            flex: 1;
        }

        .btn,
        .icon-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            height: 32px;
            padding: 0 12px;
            border-radius: var(--skin-radius-md, 8px);
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.1));
            background: var(--skin-color-bg-base, transparent);
            color: var(--skin-color-text-secondary, #444444);
            font-size: var(--skin-text-sm, 12px);
            font-family: inherit;
            cursor: pointer;
            white-space: nowrap;
        }

        .icon-btn {
            width: 32px;
            padding: 0;
        }

        .btn:hover:not(:disabled),
        .icon-btn:hover:not(:disabled) {
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.04));
            color: var(--skin-color-text-primary, #1a1a1a);
        }

        .btn.primary {
            background: var(--skin-color-accent, #3b82f6);
            border-color: transparent;
            color: var(--skin-color-accent-text, #ffffff);
        }

        .btn.primary:hover:not(:disabled) {
            background: var(--skin-color-accent-hover, #2563eb);
            color: var(--skin-color-accent-text, #ffffff);
        }

        .btn.danger {
            background: var(--skin-color-danger, #ef4444);
            border-color: transparent;
            color: var(--skin-color-danger-text, #ffffff);
        }

        .btn:disabled,
        .icon-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .mode-pill {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 2px 8px;
            border-radius: var(--skin-radius-full, 999px);
            font-size: var(--skin-text-xs, 11px);
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.05));
            color: var(--skin-color-text-secondary, #555555);
            border: 1px solid var(--skin-color-border-subtle, rgba(0, 0, 0, 0.06));
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .layout {
            display: grid;
            grid-template-columns: minmax(180px, 220px) minmax(0, 1.2fr) minmax(220px, 1fr);
            flex: 1;
            min-height: 0;
        }

        .layout.no-tree {
            grid-template-columns: minmax(0, 1.2fr) minmax(220px, 1fr);
        }

        .layout.no-preview {
            grid-template-columns: minmax(180px, 220px) minmax(0, 1fr);
        }

        .layout.no-tree.no-preview {
            grid-template-columns: minmax(0, 1fr);
        }

        .col {
            min-width: 0;
            min-height: 0;
            overflow: auto;
            border-right: 1px solid var(--skin-color-border-subtle, rgba(0, 0, 0, 0.05));
        }

        .col:last-child {
            border-right: none;
        }

        .tree-panel {
            padding: var(--skin-space-sm, 10px);
            background: var(--skin-color-bg-sidebar, rgba(0, 0, 0, 0.02));
        }

        .tree-std {
            display: flex;
            flex-direction: column;
            gap: 2px;
            margin-bottom: var(--skin-space-sm, 10px);
        }

        .tree-node {
            display: flex;
            align-items: center;
            gap: 6px;
            width: 100%;
            padding: 6px 8px;
            border: none;
            border-radius: var(--skin-radius-sm, 4px);
            background: transparent;
            color: var(--skin-color-text-secondary, #555555);
            font-size: var(--skin-text-sm, 12px);
            font-family: inherit;
            cursor: pointer;
            text-align: left;
        }

        .tree-node.child {
            padding-left: 24px;
        }

        .tree-node:hover {
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.04));
            color: var(--skin-color-text-primary, #1a1a1a);
        }

        .tree-node.selected {
            background: var(--skin-color-bg-active, rgba(59, 130, 246, 0.12));
            color: var(--skin-color-text-primary, #1a1a1a);
            font-weight: var(--skin-weight-medium, 500);
        }

        .tree-node:focus-visible {
            outline: var(--skin-focus-ring-width, 2px) solid
                var(--skin-focus-ring, var(--skin-color-accent, #3b82f6));
            outline-offset: -2px;
        }

        .gate {
            margin: 0;
            padding: var(--skin-space-md, 12px);
            border-radius: var(--skin-radius-md, 8px);
            border: 1px dashed var(--skin-color-border, rgba(0, 0, 0, 0.14));
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.03));
            color: var(--skin-color-text-secondary, #555555);
            font-size: var(--skin-text-xs, 12px);
            line-height: var(--skin-leading-normal, 1.5);
        }

        .gate strong {
            display: block;
            color: var(--skin-color-warning, #a16207);
            margin-bottom: 4px;
            font-size: var(--skin-text-xs, 11px);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .banner {
            margin: var(--skin-space-sm, 8px);
            padding: var(--skin-space-sm, 8px) var(--skin-space-md, 12px);
            border-radius: var(--skin-radius-md, 8px);
            border: 1px solid var(--skin-color-border-subtle, rgba(0, 0, 0, 0.06));
            background: color-mix(in srgb, var(--skin-color-warning, #eab308) 18%, transparent);
            color: var(--skin-color-text-primary, #1a1a1a);
            font-size: var(--skin-text-xs, 12px);
        }

        .list-panel {
            display: flex;
            flex-direction: column;
            min-height: 0;
        }

        .list-head {
            display: grid;
            grid-template-columns: 28px 28px minmax(0, 1fr) 80px 110px 160px;
            gap: var(--skin-space-xs, 6px);
            padding: 8px var(--skin-space-md, 12px);
            font-size: var(--skin-text-xs, 11px);
            color: var(--skin-color-text-muted, #666666);
            text-transform: uppercase;
            letter-spacing: 0.04em;
            border-bottom: 1px solid var(--skin-color-border-subtle, rgba(0, 0, 0, 0.05));
            position: sticky;
            top: 0;
            background: inherit;
            z-index: 1;
        }

        .row {
            display: grid;
            grid-template-columns: 28px 28px minmax(0, 1fr) 80px 110px 160px;
            gap: var(--skin-space-xs, 6px);
            align-items: center;
            padding: 8px var(--skin-space-md, 12px);
            border-bottom: 1px solid var(--skin-color-border-subtle, rgba(0, 0, 0, 0.04));
            cursor: pointer;
            font-size: var(--skin-text-sm, 12px);
        }

        .row:hover,
        .row.selected {
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.035));
        }

        .row.selected {
            background: var(--skin-color-bg-active, rgba(59, 130, 246, 0.12));
        }

        .row:focus-visible {
            outline: var(--skin-focus-ring-width, 2px) solid
                var(--skin-focus-ring, var(--skin-color-accent, #3b82f6));
            outline-offset: -2px;
        }

        .row .file-type {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: var(--skin-color-text-secondary, #555555);
        }

        .row .file-type .material-symbols-outlined {
            font-size: 18px;
        }

        .row .name {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-weight: var(--skin-weight-medium, 500);
        }

        .row .sub {
            display: block;
            font-size: var(--skin-text-xs, 11px);
            color: var(--skin-color-text-muted, #666666);
        }

        .row .muted {
            color: var(--skin-color-text-muted, #666666);
            font-variant-numeric: tabular-nums;
        }

        .row-actions {
            display: inline-flex;
            gap: 2px;
            justify-content: flex-end;
        }

        .status-block {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: var(--skin-space-sm, 8px);
            min-height: 180px;
            padding: var(--skin-space-lg, 24px);
            text-align: center;
            color: var(--skin-color-text-muted, #666666);
            font-size: var(--skin-text-sm, 13px);
        }

        .status-block.error {
            color: var(--skin-color-danger, #b91c1c);
        }

        .status-block .detail {
            font-family: var(--skin-font-mono, ui-monospace, monospace);
            font-size: var(--skin-text-xs, 11px);
            color: var(--skin-color-text-secondary, #555555);
            word-break: break-word;
            max-width: 420px;
        }

        .foot {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: var(--skin-space-sm, 8px);
            padding: var(--skin-space-sm, 8px) var(--skin-space-md, 14px);
            border-top: 1px solid var(--skin-color-border-subtle, rgba(0, 0, 0, 0.05));
            font-size: var(--skin-text-xs, 11px);
            color: var(--skin-color-text-muted, #666666);
        }

        .tray {
            display: flex;
            flex-direction: column;
            gap: 4px;
            width: 100%;
        }

        .tray-item {
            display: flex;
            align-items: center;
            gap: var(--skin-space-sm, 8px);
            padding: 4px 0;
            font-size: var(--skin-text-xs, 11px);
        }

        .tray-item .bar {
            flex: 1;
            height: 4px;
            border-radius: 2px;
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.08));
            overflow: hidden;
            position: relative;
        }

        .tray-item .bar > i {
            display: block;
            height: 100%;
            width: 40%;
            background: var(--skin-color-accent, #3b82f6);
            animation: tray-slide 1.1s ease-in-out infinite;
        }

        .tray-item.complete .bar > i {
            width: 100%;
            background: var(--skin-color-success, #22c55e);
            animation: none;
        }

        .tray-item.failed .bar > i {
            width: 100%;
            background: var(--skin-color-danger, #ef4444);
            animation: none;
        }

        @keyframes tray-slide {
            0% {
                transform: translateX(-100%);
            }
            100% {
                transform: translateX(280%);
            }
        }

        @media (prefers-reduced-motion: reduce) {
            .tray-item .bar > i {
                animation: none;
                width: 100%;
                opacity: 0.55;
            }
        }

        .modal-field {
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin-bottom: 12px;
        }

        .modal-field label {
            font-size: var(--skin-text-xs, 11px);
            color: var(--skin-color-text-secondary, #555555);
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .modal-field input {
            height: 36px;
            padding: 0 10px;
            border-radius: var(--skin-radius-md, 8px);
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.12));
            background: var(--skin-color-bg-base, transparent);
            color: var(--skin-color-text-primary, #1a1a1a);
            font-family: var(--skin-font-mono, ui-monospace, monospace);
            font-size: var(--skin-text-sm, 12px);
        }

        .modal-note {
            font-size: var(--skin-text-xs, 12px);
            color: var(--skin-color-text-secondary, #555555);
            line-height: var(--skin-leading-normal, 1.5);
        }

        .modal-error {
            margin-top: 8px;
            padding: 8px 10px;
            border-radius: var(--skin-radius-sm, 4px);
            background: color-mix(in srgb, var(--skin-color-danger, #ef4444) 14%, transparent);
            color: var(--skin-color-danger, #b91c1c);
            font-size: var(--skin-text-xs, 12px);
            font-family: var(--skin-font-mono, ui-monospace, monospace);
            word-break: break-word;
        }

        .preview-host {
            display: flex;
            flex-direction: column;
            min-height: 0;
            height: 100%;
            padding: var(--skin-space-sm, 8px);
        }

        .preview-host soma-file-preview {
            flex: 1;
            min-height: 0;
        }

        input[type='checkbox'] {
            accent-color: var(--skin-color-accent, #3b82f6);
            width: 15px;
            height: 15px;
            cursor: pointer;
        }
    `;

    @property({ type: String, reflect: true }) mode: FileManagerMode = 'browse';
    @property({ type: String, reflect: true }) path = '';
    @property({ type: Array, attribute: false }) selection: string[] = [];
    @property({ type: Boolean, attribute: 'show-preview' }) showPreview = true;
    @property({ type: Boolean, attribute: 'show-upload' }) showUpload = true;
    @property({ type: Boolean, attribute: 'show-toolbar' }) showToolbar = true;
    @property({ type: Number, attribute: 'page-size' }) pageSize = 50;

    @state() private _files: FileOut[] = [];
    @state() private _filesTotal = 0;
    @state() private _filesStatus: LoadStatus = 'idle';
    @state() private _filesError = '';
    @state() private _query = '';

    /** Tree gate: never a fabricated tree when GET /api/v2/workroot/tree is absent. */
    @state() private _treeStatus: LoadStatus = 'idle';
    @state() private _treeGateReason = '';
    @state() private _treePartial = '';

    @state() private _previewFile: FileOut | null = null;
    @state() private _uploads: UploadTrayItem[] = [];

    @state() private _renameTarget: FileOut | null = null;
    @state() private _renameValue = '';
    @state() private _renameError = '';
    @state() private _renameBusy = false;

    @state() private _deleteTarget: FileOut | null = null;
    @state() private _deleteError = '';
    @state() private _deleteBusy = false;

    @state() private _moveTarget: FileOut | null = null;
    @state() private _moveDest = INBOX_PATH;
    @state() private _moveError = '';
    @state() private _moveBusy = false;

    private _fileInput: HTMLInputElement | null = null;

    @query('soma-glass-modal#rename-modal')
    private _renameModal!: SomaGlassModal | null;

    @query('soma-glass-modal#delete-modal')
    private _deleteModal!: SomaGlassModal | null;

    @query('soma-glass-modal#move-modal')
    private _moveModal!: SomaGlassModal | null;

    override connectedCallback(): void {
        super.connectedCallback();
        void this.refresh();
    }

    /** Reload list + re-probe the workroot tree. */
    async refresh(): Promise<void> {
        void this._loadFiles();
        void this._probeTree();
        this.dispatchEvent(
            new CustomEvent('soma-refresh', { bubbles: true, composed: true }),
        );
    }

    private get _filtered(): FileOut[] {
        const q = this._query.trim().toLowerCase();
        if (!q) return this._files;
        return this._files.filter(f => {
            const hay = `${fileName(f)} ${f.mime_type} ${f.name}`.toLowerCase();
            return hay.includes(q);
        });
    }

    private get _selectionSet(): Set<string> {
        return new Set(this.selection);
    }

    // -- Files (LIVE) -------------------------------------------------------

    private async _loadFiles(): Promise<void> {
        if (this._filesStatus === 'loading') return;
        this._filesStatus = 'loading';
        this._filesError = '';
        try {
            const raw = await apiClient.get<FileListResponseEnvelope>(
                `/filesv2/?page=1&per_page=${Math.max(1, this.pageSize)}`,
            );
            const { files, total } = normalizeFileList(raw);
            this._files = files;
            this._filesTotal = total;
            this._filesStatus = files.length === 0 ? 'empty' : 'ready';
        } catch (err) {
            if (err instanceof ApiError && err.status === 403) {
                this._filesStatus = 'denied';
            } else {
                this._filesStatus = 'error';
                this._filesError =
                    err instanceof ApiError
                        ? err.status > 0
                            ? `GET /api/v2/filesv2/ refused (HTTP ${err.status})`
                            : `${err.message || 'network error'} — GET /api/v2/filesv2/`
                        : `GET /api/v2/filesv2/ — ${err instanceof Error ? err.message : 'unknown error'}`;
            }
        }
    }

    // -- Tree (GATED when absent) ------------------------------------------

    private async _probeTree(): Promise<void> {
        if (this._treeStatus === 'loading') return;
        this._treeStatus = 'loading';
        this._treeGateReason = '';
        this._treePartial = '';
        try {
            await apiClient.get<unknown>('/workroot/tree');
            // Endpoint answered: do not invent a tree shape. Surface a partial
            // note that the list remains filesv2 until a typed tree lands.
            this._treeStatus = 'ready';
            this._treePartial =
                'GET /api/v2/workroot/tree answered. Typed tree rendering is not bound yet — the file list stays filesv2.';
        } catch (err) {
            const status = err instanceof ApiError ? err.status : 0;
            if (status === 403) {
                this._treeStatus = 'denied';
                this._treeGateReason =
                    'You need permission to read the workroot tree (GET /api/v2/workroot/tree).';
            } else if (status === 404 || status === 405 || status === 501) {
                this._treeStatus = 'empty';
                this._treeGateReason = TREE_ABSENT_REASON;
            } else if (status > 0) {
                this._treeStatus = 'error';
                this._treeGateReason = `${TREE_ABSENT_REASON} Last attempt: GET /api/v2/workroot/tree refused (HTTP ${status}).`;
                this._treePartial = this._treeGateReason;
            } else {
                this._treeStatus = 'error';
                this._treeGateReason = `${TREE_ABSENT_REASON} Last attempt: ${reasonOf(err)}`;
                this._treePartial = this._treeGateReason;
            }
        }
    }

    private get _treeVisible(): boolean {
        return this._treeStatus === 'ready' || this._treeStatus === 'loading';
    }

    // -- Upload (LIVE via file-upload.ts) ----------------------------------

    private _openUploadPicker(): void {
        if (!this._fileInput) {
            this._fileInput = document.createElement('input');
            this._fileInput.type = 'file';
            this._fileInput.multiple = true;
            this._fileInput.addEventListener('change', () => {
                const files = this._fileInput?.files ? Array.from(this._fileInput.files) : [];
                if (this._fileInput) this._fileInput.value = '';
                void this._uploadFiles(files);
            });
            // Detached picker — fired once per user gesture.
            this._fileInput.hidden = true;
            document.body.appendChild(this._fileInput);
        }
        this._fileInput.click();
    }

    private async _uploadFiles(files: File[]): Promise<void> {
        if (files.length === 0) return;

        const started = files.map((f, i) => ({
            key: `${Date.now()}-${i}-${f.name}`,
            name: f.name,
            size: f.size,
            state: 'uploading' as const,
        }));
        this._uploads = [...started, ...this._uploads].slice(0, 20);

        this.dispatchEvent(
            new CustomEvent<{ files: { name: string; type: string; size: number }[] }>(
                'soma-upload-start',
                {
                    detail: {
                        files: files.map(f => ({
                            name: f.name,
                            type: f.type || 'application/octet-stream',
                            size: f.size,
                        })),
                    },
                    bubbles: true,
                    composed: true,
                },
            ),
        );

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const key = started[i].key;
            try {
                const meta: AttachmentMeta = await uploadAttachment(file);
                if (!meta.file_id) {
                    throw new Error('upload completed without a file_id');
                }
                this._uploads = this._uploads.map(u =>
                    u.key === key ? { ...u, state: 'complete', fileId: meta.file_id } : u,
                );
                this.dispatchEvent(
                    new CustomEvent<{ fileId: string; name: string }>('soma-upload-complete', {
                        detail: { fileId: meta.file_id, name: file.name },
                        bubbles: true,
                        composed: true,
                    }),
                );
            } catch (err) {
                const message = reasonOf(err);
                this._uploads = this._uploads.map(u =>
                    u.key === key ? { ...u, state: 'failed', error: message } : u,
                );
                this.dispatchEvent(
                    new CustomEvent<{ name: string; error: string }>('soma-upload-error', {
                        detail: { name: file.name, error: message },
                        bubbles: true,
                        composed: true,
                    }),
                );
            }
        }

        void this._loadFiles();
    }

    // -- Download / open ---------------------------------------------------

    private async _download(file: FileOut): Promise<void> {
        this.dispatchEvent(
            new CustomEvent<{ fileId: string; name: string }>('soma-file-download', {
                detail: { fileId: file.id, name: fileName(file) },
                bubbles: true,
                composed: true,
            }),
        );
        try {
            const signed = await apiClient.get<DownloadUrlOut>(
                `/filesv2/${encodeURIComponent(file.id)}/download-url`,
            );
            if (!signed?.download_url) {
                throw new Error('download-url response had no download_url');
            }
            const a = document.createElement('a');
            a.href = signed.download_url;
            a.rel = 'noopener';
            a.download = fileName(file);
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (err) {
            this._filesError = `Download unavailable — ${reasonOf(err)}`;
        }
    }

    private _openPreview(file: FileOut): void {
        this._previewFile = file;
        this.dispatchEvent(
            new CustomEvent<{ fileId: string; name: string; mime: string; path: string }>(
                'soma-file-open',
                {
                    detail: {
                        fileId: file.id,
                        name: fileName(file),
                        mime: file.mime_type,
                        path: this.path,
                    },
                    bubbles: true,
                    composed: true,
                },
            ),
        );
    }

    // -- Selection / composer attach ---------------------------------------

    private _toggleSelect(file: FileOut, on?: boolean): void {
        const next = new Set(this.selection);
        const want = on ?? !next.has(file.id);
        if (want) next.add(file.id);
        else next.delete(file.id);
        this.selection = Array.from(next);
        this.dispatchEvent(
            new CustomEvent<{ fileIds: string[]; files: FileOut[] }>('soma-file-select', {
                detail: {
                    fileIds: this.selection,
                    files: this._files.filter(f => next.has(f.id)),
                },
                bubbles: true,
                composed: true,
            }),
        );
    }

    private _emitAttach(): void {
        const files = this._files.filter(f => this._selectionSet.has(f.id));
        this.dispatchEvent(
            new CustomEvent<{ fileIds: string[]; files: FileOut[] }>('soma-file-select', {
                detail: { fileIds: files.map(f => f.id), files },
                bubbles: true,
                composed: true,
            }),
        );
    }

    // -- Rename modal (gated target API) -----------------------------------

    private _openRename(file: FileOut): void {
        this._renameTarget = file;
        this._renameValue = fileName(file);
        this._renameError = RENAME_DISABLED_REASON;
        this._renameBusy = false;
        this._renameModal?.show();
    }

    private async _confirmRename(): Promise<void> {
        if (!this._renameTarget) return;
        const newName = this._renameValue.trim();
        if (!newName) {
            this._renameError = 'A name is required.';
            return;
        }
        this._renameBusy = true;
        this._renameError = '';
        try {
            await apiClient.patch(`/filesv2/${encodeURIComponent(this._renameTarget.id)}`, {
                original_name: newName,
                name: newName,
            });
            this.dispatchEvent(
                new CustomEvent<{ fileId: string; name: string; newName: string }>(
                    'soma-file-rename',
                    {
                        detail: {
                            fileId: this._renameTarget.id,
                            name: fileName(this._renameTarget),
                            newName,
                        },
                        bubbles: true,
                        composed: true,
                    },
                ),
            );
            this._renameModal?.close();
            this._renameTarget = null;
            void this._loadFiles();
        } catch (err) {
            // Honest failure: the PATCH route is not in admin/filesv2/api.py.
            const targetId = this._renameTarget?.id ?? '';
            this._renameError = `${RENAME_DISABLED_REASON} Attempted PATCH /api/v2/filesv2/${targetId} — ${reasonOf(err)}`;
        } finally {
            this._renameBusy = false;
        }
    }

    // -- Delete modal (LIVE soft-delete) -----------------------------------

    private _openDelete(file: FileOut): void {
        this._deleteTarget = file;
        this._deleteError = '';
        this._deleteBusy = false;
        this._deleteModal?.show();
    }

    private async _confirmDelete(): Promise<void> {
        if (!this._deleteTarget) return;
        this._deleteBusy = true;
        this._deleteError = '';
        const target = this._deleteTarget;
        try {
            await apiClient.delete<{ success?: boolean }>(
                `/filesv2/${encodeURIComponent(target.id)}`,
            );
            this.dispatchEvent(
                new CustomEvent<{ fileId: string; name: string }>('soma-file-delete', {
                    detail: { fileId: target.id, name: fileName(target) },
                    bubbles: true,
                    composed: true,
                }),
            );
            if (this._previewFile?.id === target.id) this._previewFile = null;
            this.selection = this.selection.filter(id => id !== target.id);
            this._deleteModal?.close();
            this._deleteTarget = null;
            void this._loadFiles();
        } catch (err) {
            this._deleteError = `DELETE /api/v2/filesv2/${target.id} — ${reasonOf(err)}`;
        } finally {
            this._deleteBusy = false;
        }
    }

    // -- Move modal (gated target API) --------------------------------------

    private _openMove(file: FileOut): void {
        this._moveTarget = file;
        this._moveDest = INBOX_PATH;
        this._moveError = MOVE_DISABLED_REASON;
        this._moveBusy = false;
        this._moveModal?.show();
    }

    private async _confirmMove(): Promise<void> {
        if (!this._moveTarget) return;
        const dest = this._moveDest.trim();
        if (!dest) {
            this._moveError = 'A destination path is required.';
            return;
        }
        this._moveBusy = true;
        this._moveError = '';
        const target = this._moveTarget;
        try {
            await apiClient.post(`/workroot/move`, {
                file_id: target.id,
                dest,
            });
            this.dispatchEvent(
                new CustomEvent<{ fileId: string; name: string; dest: string }>('soma-file-move', {
                    detail: { fileId: target.id, name: fileName(target), dest },
                    bubbles: true,
                    composed: true,
                }),
            );
            this._moveModal?.close();
            this._moveTarget = null;
            void this._loadFiles();
        } catch (err) {
            this._moveError = `${MOVE_DISABLED_REASON} Attempted POST /api/v2/workroot/move for ${target.id} — ${reasonOf(err)}`;
        } finally {
            this._moveBusy = false;
        }
    }

    // -- Render -------------------------------------------------------------

    override render(): TemplateResult {
        const treeClass = this._treeVisible ? '' : 'no-tree';
        const previewClass = this.showPreview ? '' : 'no-preview';
        return html`
            <div class="top">
                ${this._renderBreadcrumb()}
                <input
                    class="search"
                    type="search"
                    role="searchbox"
                    aria-label="Search files"
                    placeholder="Search files…"
                    .value=${this._query}
                    @input=${(e: Event) => {
                        this._query = (e.target as HTMLInputElement).value;
                    }}
                />
                <span class="spacer"></span>
                <span class="mode-pill" title="Active mode">${this.mode}</span>
                ${this.showToolbar
                    ? html`
                          <button
                              class="icon-btn"
                              aria-label="Refresh"
                              title="Refresh"
                              @click=${() => void this.refresh()}
                          >
                              <span class="material-symbols-outlined">refresh</span>
                          </button>
                          ${this.showUpload
                              ? html`
                                    <button
                                        class="btn"
                                        aria-label="Upload files"
                                        @click=${this._openUploadPicker}
                                    >
                                        <span class="material-symbols-outlined">upload</span>
                                        Upload
                                    </button>
                                `
                              : nothing}
                          <button
                              class="btn"
                              disabled
                              title=${NEW_FOLDER_DISABLED_REASON}
                              aria-disabled="true"
                              aria-label="New folder (disabled)"
                          >
                              <span class="material-symbols-outlined">create_new_folder</span>
                              New folder
                          </button>
                      `
                    : nothing}
                ${this.mode === 'select'
                    ? html`
                          <button
                              class="btn primary"
                              ?disabled=${this.selection.length === 0}
                              title=${this.selection.length === 0
                                  ? 'Select one or more files to attach.'
                                  : 'Attach selected files to the composer'}
                              @click=${this._emitAttach}
                          >
                              Attach (${this.selection.length})
                          </button>
                      `
                    : nothing}
            </div>

            ${this._treePartial
                ? html`<div class="banner" role="alert">${this._treePartial}</div>`
                : nothing}

            <div class="layout ${treeClass} ${previewClass}">
                ${this._treeVisible ? this._renderTree() : nothing}
                <div class="col list-panel">${this._renderList()}</div>
                ${this.showPreview
                    ? html`
                          <div class="col">
                              <div class="preview-host">
                                  <soma-file-preview
                                      file-id=${this._previewFile?.id ?? ''}
                                      name=${this._previewFile ? fileName(this._previewFile) : ''}
                                      mime=${this._previewFile?.mime_type ?? ''}
                                      size-bytes=${this._previewFile?.size_bytes ?? 0}
                                      show-edit
                                      @soma-download=${(e: CustomEvent<{ fileId: string; name: string }>) => {
                                          const f =
                                              this._previewFile &&
                                              this._previewFile.id === e.detail.fileId
                                                  ? this._previewFile
                                                  : null;
                                          if (f) void this._download(f);
                                      }}
                                  ></soma-file-preview>
                              </div>
                          </div>
                      `
                    : nothing}
            </div>

            <div class="foot">
                <span>
                    ${this._filtered.length} shown${this._filesTotal > this._files.length
                        ? ` · ${this._filesTotal} total`
                        : nothing}
                    ${this._files.length > 0
                        ? ` · ${formatBytes(this._files.reduce((n, f) => n + (f.size_bytes || 0), 0))}`
                        : nothing}
                </span>
                ${this.mode === 'manage'
                    ? html`<span title=${NEW_FOLDER_DISABLED_REASON}>
                          Manage mode — rename/delete enabled where the API exists.
                      </span>`
                    : nothing}
                <span title=${EDITOR_SAVE_DISABLED_REASON}>${EDITOR_SAVE_DISABLED_REASON}</span>
                ${this._uploads.length > 0
                    ? html`
                          <div class="tray" aria-label="Upload tray">
                              ${this._uploads.slice(0, 6).map(
                                  u => html`
                                      <div class="tray-item ${u.state}">
                                          <span>${u.name}</span>
                                          <span class="bar" aria-hidden="true"><i></i></span>
                                          <span>${u.state}${u.error ? ` — ${u.error}` : ''}</span>
                                      </div>
                                  `,
                              )}
                              <button
                                  class="btn"
                                  @click=${() => (this._uploads = [])}
                                  aria-label="Clear upload tray"
                              >
                                  Clear tray
                              </button>
                          </div>
                      `
                    : nothing}
            </div>

            ${this._renderRenameModal()} ${this._renderDeleteModal()} ${this._renderMoveModal()}
        `;
    }

    private _renderBreadcrumb(): TemplateResult {
        if (this._treeStatus !== 'ready' && this._treeStatus !== 'loading') {
            // FM-00: breadcrumb hidden when the tree API is not mounted.
            return html`<span class="crumb" title=${TREE_ABSENT_REASON} aria-hidden="true"></span>`;
        }
        const segments = (this.path || '/').split('/').filter(Boolean);
        return html`
            <nav class="crumb" aria-label="Breadcrumb">
                <span class="material-symbols-outlined" aria-hidden="true">home</span>
                <button
                    class="btn"
                    style="height:24px;padding:0 6px;border:none;background:transparent"
                    @click=${() => {
                        this.path = '';
                        this.dispatchEvent(
                            new CustomEvent<{ path: string }>('soma-path-change', {
                                detail: { path: '' },
                                bubbles: true,
                                composed: true,
                            }),
                        );
                    }}
                >
                    workroot
                </button>
                ${segments.map(
                    (seg, i) => html`
                        <span class="sep">/</span>
                        ${i === segments.length - 1
                            ? html`<span class="current">${seg}</span>`
                            : html`<button
                                  class="btn"
                                  style="height:24px;padding:0 6px;border:none;background:transparent"
                                  @click=${() => {
                                      const next = segments.slice(0, i + 1).join('/');
                                      this.path = next;
                                      this.dispatchEvent(
                                          new CustomEvent<{ path: string }>('soma-path-change', {
                                              detail: { path: next },
                                              bubbles: true,
                                              composed: true,
                                          }),
                                      );
                                  }}
                              >
                                  ${seg}
                              </button>`}
                    `,
                )}
            </nav>
        `;
    }

    private _renderTree(): TemplateResult {
        if (this._treeStatus === 'loading') {
            return html`
                <aside class="col tree-panel" aria-label="Workroot tree">
                    <div class="status-block" aria-hidden="true">Loading tree…</div>
                </aside>
            `;
        }
        // Standardized locations: workroot root + inbox. Selecting a node only
        // changes the path chrome — the list stays filesv2 until a typed tree
        // schema is bound. Never invent children.
        const onRoot = this.path === '' || this.path === WORKROOT_ROOT;
        const onInbox = this.path === INBOX_PATH || this.path === `${WORKROOT_ROOT}/${INBOX_PATH}`;
        return html`
            <aside class="col tree-panel" aria-label="Workroot tree">
                <div class="tree-std" role="tree" aria-label="Workroot locations">
                    <button
                        class="tree-node ${onRoot ? 'selected' : ''}"
                        role="treeitem"
                        aria-selected=${onRoot ? 'true' : 'false'}
                        @click=${() => this._setPath('')}
                    >
                        <span class="material-symbols-outlined" aria-hidden="true">folder</span>
                        ${WORKROOT_ROOT}
                    </button>
                    <button
                        class="tree-node child ${onInbox ? 'selected' : ''}"
                        role="treeitem"
                        aria-selected=${onInbox ? 'true' : 'false'}
                        @click=${() => this._setPath(INBOX_PATH)}
                    >
                        <span class="material-symbols-outlined" aria-hidden="true">inbox</span>
                        ${INBOX_PATH}
                    </button>
                </div>
                <p class="gate" role="status">
                    <strong>${this._treeStatus === 'ready' ? 'Tree bound' : 'Tree gated'}</strong>
                    ${this._treeGateReason ||
                    'Typed node rendering is not wired to a verified tree schema yet. The file list remains the live filesv2 source.'}
                </p>
            </aside>
        `;
    }

    private _setPath(path: string): void {
        this.path = path;
        this.dispatchEvent(
            new CustomEvent<{ path: string }>('soma-path-change', {
                detail: { path },
                bubbles: true,
                composed: true,
            }),
        );
    }

    private _renderList(): TemplateResult {
        if (this._filesStatus === 'idle' || this._filesStatus === 'loading') {
            return html`<div class="status-block" aria-live="polite">Loading files…</div>`;
        }
        if (this._filesStatus === 'error') {
            return html`
                <div class="status-block error" role="alert">
                    <span>Files could not be listed.</span>
                    ${this._filesError ? html`<div class="detail">${this._filesError}</div>` : nothing}
                    <button class="btn" aria-label="Retry listing files" @click=${() => void this._loadFiles()}>
                        Retry
                    </button>
                </div>
            `;
        }
        if (this._filesStatus === 'denied') {
            return html`<div class="status-block error">
                You need <code>files:read</code> to browse files.
            </div>`;
        }

        const rows = this._filtered;
        if (rows.length === 0) {
            return html`
                <div class="status-block">
                    <span>No files in the working set.</span>
                    <span class="detail">
                        filesv2 storage only — agent work-directory files have no list API in
                        this deployment.
                    </span>
                </div>
            `;
        }

        return html`
            <div class="list-head" role="row">
                <span></span>
                <span></span>
                <span>Name</span>
                <span>Size</span>
                <span>Modified</span>
                <span></span>
            </div>
            <div role="list" aria-label="Files">
                ${rows.map(f => this._renderRow(f))}
            </div>
            ${this._filesTotal > rows.length
                ? html`<div class="status-block" style="min-height:0;padding:8px">
                      showing ${rows.length} of ${this._filesTotal}
                  </div>`
                : nothing}
        `;
    }

    private _renderRow(file: FileOut): TemplateResult {
        const selected = this._selectionSet.has(file.id);
        const canMutate = this.mode === 'manage';
        return html`
            <div
                class="row ${selected ? 'selected' : ''}"
                role="listitem"
                tabindex="0"
                @click=${() => this._openPreview(file)}
                @keydown=${(e: KeyboardEvent) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        this._openPreview(file);
                    }
                }}
            >
                <span @click=${(e: Event) => e.stopPropagation()}>
                    <input
                        type="checkbox"
                        aria-label=${`Select ${fileName(file)}`}
                        .checked=${selected}
                        @change=${(e: Event) =>
                            this._toggleSelect(file, (e.target as HTMLInputElement).checked)}
                    />
                </span>
                <span class="file-type" aria-hidden="true">
                    <span class="material-symbols-outlined">${attachmentIcon(fileName(file), file.mime_type)}</span>
                </span>
                <span>
                    <span class="name" title=${fileName(file)}>${fileName(file)}</span>
                    <span class="sub">${file.mime_type || '—'} · v${file.version}</span>
                </span>
                <span class="muted">${formatBytes(file.size_bytes)}</span>
                <span class="muted">${file.updated_at ? file.updated_at.slice(0, 10) : '—'}</span>
                <span class="row-actions" @click=${(e: Event) => e.stopPropagation()}>
                    <button
                        class="icon-btn"
                        aria-label="Download"
                        title="Download"
                        @click=${() => void this._download(file)}
                    >
                        <span class="material-symbols-outlined">download</span>
                    </button>
                    <button
                        class="icon-btn"
                        aria-label="Preview"
                        title="Preview"
                        @click=${() => this._openPreview(file)}
                    >
                        <span class="material-symbols-outlined">visibility</span>
                    </button>
                    <button
                        class="icon-btn"
                        aria-label="Rename"
                        title=${canMutate ? 'Rename' : RENAME_DISABLED_REASON}
                        ?disabled=${!canMutate}
                        aria-disabled=${!canMutate ? 'true' : 'false'}
                        @click=${() => this._openRename(file)}
                    >
                        <span class="material-symbols-outlined">edit</span>
                    </button>
                    <button
                        class="icon-btn"
                        aria-label="Move"
                        title=${canMutate ? 'Move' : MOVE_DISABLED_REASON}
                        ?disabled=${!canMutate}
                        aria-disabled=${!canMutate ? 'true' : 'false'}
                        @click=${() => this._openMove(file)}
                    >
                        <span class="material-symbols-outlined">drive_file_move</span>
                    </button>
                    <button
                        class="icon-btn"
                        aria-label="Delete"
                        title=${canMutate ? 'Delete' : 'Switch to manage mode to delete'}
                        ?disabled=${!canMutate}
                        aria-disabled=${!canMutate ? 'true' : 'false'}
                        @click=${() => this._openDelete(file)}
                    >
                        <span class="material-symbols-outlined">delete</span>
                    </button>
                    ${this.mode === 'select'
                        ? html`
                              <button
                                  class="icon-btn"
                                  aria-label="Attach to chat"
                                  title="Attach to chat"
                                  @click=${() => {
                                      this._toggleSelect(file, true);
                                      this._emitAttach();
                                  }}
                              >
                                  <span class="material-symbols-outlined">attach_file</span>
                              </button>
                          `
                        : nothing}
                </span>
            </div>
        `;
    }

    private _renderRenameModal(): TemplateResult {
        return html`
            <soma-glass-modal
                id="rename-modal"
                size="sm"
                title="Rename file"
                subtitle=${this._renameTarget ? fileName(this._renameTarget) : ''}
                @soma-modal-close=${() => {
                    this._renameTarget = null;
                    this._renameError = '';
                }}
            >
                <div class="modal-field">
                    <label for="rename-input">New name</label>
                    <input
                        id="rename-input"
                        .value=${this._renameValue}
                        @input=${(e: Event) => {
                            this._renameValue = (e.target as HTMLInputElement).value;
                        }}
                    />
                </div>
                <p class="modal-note">
                    Target API:
                    <code>PATCH /api/v2/filesv2/${this._renameTarget?.id ?? '{id}'}</code>.
                    This deployment does not declare a rename route
                    (<code>admin/filesv2/api.py</code> has list/upload/get/delete/download-url
                    only).
                </p>
                ${this._renameError
                    ? html`<div class="modal-error" role="alert">${this._renameError}</div>`
                    : nothing}
                <div slot="actions">
                    <button
                        class="btn"
                        @click=${() => this._renameModal?.close()}
                        ?disabled=${this._renameBusy}
                    >
                        Cancel
                    </button>
                    <button
                        class="btn primary"
                        ?disabled=${this._renameBusy || !this._renameValue.trim()}
                        @click=${() => void this._confirmRename()}
                    >
                        ${this._renameBusy ? 'Renaming…' : 'Rename'}
                    </button>
                </div>
            </soma-glass-modal>
        `;
    }

    private _renderMoveModal(): TemplateResult {
        return html`
            <soma-glass-modal
                id="move-modal"
                size="sm"
                title="Move file"
                subtitle=${this._moveTarget ? fileName(this._moveTarget) : ''}
                @soma-modal-close=${() => {
                    this._moveTarget = null;
                    this._moveError = '';
                }}
            >
                <div class="modal-field">
                    <label for="move-dest">Destination</label>
                    <input
                        id="move-dest"
                        .value=${this._moveDest}
                        placeholder=${INBOX_PATH}
                        @input=${(e: Event) => {
                            this._moveDest = (e.target as HTMLInputElement).value;
                        }}
                    />
                </div>
                <p class="modal-note">
                    Standard locations:
                    <code>${WORKROOT_ROOT}</code>
                    /
                    <code>${INBOX_PATH}</code>.
                    Target API:
                    <code>POST /api/v2/workroot/move</code>
                    (not mounted in this deployment).
                </p>
                ${this._moveError
                    ? html`<div class="modal-error" role="alert">${this._moveError}</div>`
                    : nothing}
                <div slot="actions">
                    <button
                        class="btn"
                        @click=${() => this._moveModal?.close()}
                        ?disabled=${this._moveBusy}
                    >
                        Cancel
                    </button>
                    <button
                        class="btn primary"
                        ?disabled=${this._moveBusy || !this._moveDest.trim()}
                        @click=${() => void this._confirmMove()}
                    >
                        ${this._moveBusy ? 'Moving…' : 'Move'}
                    </button>
                </div>
            </soma-glass-modal>
        `;
    }

    private _renderDeleteModal(): TemplateResult {
        return html`
            <soma-glass-modal
                id="delete-modal"
                size="sm"
                title="Delete file"
                subtitle=${this._deleteTarget ? fileName(this._deleteTarget) : ''}
                @soma-modal-close=${() => {
                    this._deleteTarget = null;
                    this._deleteError = '';
                }}
            >
                <p class="modal-note">
                    Soft-delete
                    <code>${this._deleteTarget ? fileName(this._deleteTarget) : ''}</code>
                    via
                    <code>DELETE /api/v2/filesv2/${this._deleteTarget?.id ?? '{id}'}</code>.
                    The row is marked <code>deleted_at</code> and disappears from the list.
                </p>
                ${this._deleteError
                    ? html`<div class="modal-error" role="alert">${this._deleteError}</div>`
                    : nothing}
                <div slot="actions">
                    <button
                        class="btn"
                        @click=${() => this._deleteModal?.close()}
                        ?disabled=${this._deleteBusy}
                    >
                        Cancel
                    </button>
                    <button
                        class="btn danger"
                        ?disabled=${this._deleteBusy}
                        @click=${() => void this._confirmDelete()}
                    >
                        ${this._deleteBusy ? 'Deleting…' : 'Delete'}
                    </button>
                </div>
            </soma-glass-modal>
        `;
    }

}

declare global {
    interface HTMLElementTagNameMap {
        'soma-file-manager': SomaFileManager;
    }
}
