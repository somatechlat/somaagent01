/**
 * soma-file-preview — honest mime-scoped preview host (CM-02 FM-30…FM-36).
 *
 * Real bindings only:
 *   GET /api/v2/filesv2/{id}/download-url  → signed body URL (S3-backed)
 *   fetch(signed)                          → text / image / pdf bytes
 *
 * Preview policy (normative CM-02 §5):
 *   markdown                  → rendered doc body
 *   text/* · json · source    → readonly code/text body
 *   image/*                   → <img> from authorized URL
 *   application/pdf           → iframe from authorized URL
 *   binary / unknown          → metadata card + Download only (never a fake renderer)
 *
 * When the signed-URL endpoint is missing or the bytes cannot be fetched,
 * the pane says so — it never invents content.
 */

import { LitElement, css, html, nothing, TemplateResult } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { unsafeHTML } from 'lit/directives/unsafe-html.js';
import { apiClient, ApiError } from '../services/api-client.js';
import { renderMarkdown, renderCodeBlock, formatBytes } from '../utils/markdown.js';

export type FilePreviewKind = 'markdown' | 'code' | 'image' | 'pdf' | 'metadata';

export type FilePreviewStatus = 'idle' | 'loading' | 'ready' | 'error';

interface DownloadUrlOut {
    download_url: string;
    expires_in: number;
    filename: string;
}

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

function extOf(name: string): string {
    const dot = name.lastIndexOf('.');
    if (dot <= 0 || dot === name.length - 1) return '';
    return name.slice(dot + 1).toLowerCase();
}

function languageOf(name: string): string {
    return LANG_BY_EXT[extOf(name)] ?? 'text';
}

/** Decide the preview control from mime + extension. Never guesses a renderer. */
export function previewKindOf(mime: string, name: string): FilePreviewKind {
    const m = (mime || '').toLowerCase().split(';')[0].trim();
    const ext = extOf(name);

    if (m === 'text/markdown' || ext === 'md' || ext === 'markdown') return 'markdown';
    if (m.startsWith('image/')) return 'image';
    if (m === 'application/pdf' || ext === 'pdf') return 'pdf';

    const textish =
        m.startsWith('text/') ||
        m === 'application/json' ||
        m === 'application/javascript' ||
        m === 'application/xml' ||
        m === 'application/xhtml+xml' ||
        m === 'application/x-yaml' ||
        m === 'application/yaml' ||
        m === 'application/toml' ||
        m.endsWith('+json') ||
        m.endsWith('+xml');

    if (textish) return 'code';
    // Source-looking extensions even when the server sent a generic mime.
    if (
        !m ||
        m === 'application/octet-stream' ||
        [
            'ts',
            'tsx',
            'js',
            'jsx',
            'json',
            'py',
            'css',
            'html',
            'yml',
            'yaml',
            'toml',
            'sh',
            'sql',
            'csv',
            'txt',
        ].includes(ext)
    ) {
        if (['md', 'markdown'].includes(ext)) return 'markdown';
        if (
            textish ||
            [
                'ts',
                'tsx',
                'js',
                'jsx',
                'json',
                'py',
                'css',
                'html',
                'yml',
                'yaml',
                'toml',
                'sh',
                'sql',
                'csv',
                'txt',
            ].includes(ext)
        ) {
            return 'code';
        }
    }

    return 'metadata';
}

function reasonOf(err: unknown): string {
    if (err instanceof ApiError) {
        if (!err.status) return err.message || 'network error — request never reached the API';
        return `${err.message || 'request failed'} (HTTP ${err.status})`;
    }
    if (err instanceof Error && err.message) return err.message;
    return 'request failed';
}

@customElement('soma-file-preview')
export class SomaFilePreview extends LitElement {
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
            -webkit-smoothing: antialiased;
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
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            overflow: hidden;
        }

        .bar {
            display: flex;
            align-items: center;
            gap: var(--skin-space-sm, 8px);
            padding: var(--skin-space-sm, 8px) var(--skin-space-md, 16px);
            border-bottom: 1px solid var(--skin-color-border-subtle, rgba(0, 0, 0, 0.05));
            flex-shrink: 0;
        }

        .name {
            flex: 1;
            min-width: 0;
            font-size: var(--skin-text-sm, 13px);
            font-weight: var(--skin-weight-medium, 500);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .meta {
            font-size: var(--skin-text-xs, 11px);
            color: var(--skin-color-text-muted, #666666);
            white-space: nowrap;
        }

        .kind-chip {
            font-size: var(--skin-text-xs, 11px);
            padding: 2px 8px;
            border-radius: var(--skin-radius-full, 999px);
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.04));
            color: var(--skin-color-text-secondary, #555555);
            border: 1px solid var(--skin-color-border-subtle, rgba(0, 0, 0, 0.05));
        }

        .body {
            flex: 1;
            min-height: 0;
            overflow: auto;
            padding: var(--skin-space-md, 16px);
        }

        .icon-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
            height: 30px;
            padding: 0 10px;
            border-radius: var(--skin-radius-sm, 4px);
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
            background: var(--skin-color-bg-base, transparent);
            color: var(--skin-color-text-secondary, #555555);
            font-size: var(--skin-text-xs, 11px);
            cursor: pointer;
        }

        .icon-btn:hover:not(:disabled) {
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.04));
            color: var(--skin-color-text-primary, #1a1a1a);
        }

        .icon-btn:disabled {
            opacity: 0.55;
            cursor: not-allowed;
        }

        .status {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: var(--skin-space-sm, 8px);
            min-height: 180px;
            text-align: center;
            color: var(--skin-color-text-muted, #666666);
            font-size: var(--skin-text-sm, 13px);
            padding: var(--skin-space-lg, 24px);
        }

        .status .material-symbols-outlined {
            font-size: 36px;
            opacity: 0.7;
        }

        .status.error {
            color: var(--skin-color-danger, #b91c1c);
        }

        .code {
            margin: 0;
            font-family: var(--skin-font-mono, ui-monospace, monospace);
            font-size: var(--skin-text-xs, 12px);
            line-height: var(--skin-leading-relaxed, 1.6);
            white-space: pre-wrap;
            word-break: break-word;
            color: var(--skin-color-text-primary, #1a1a1a);
        }

        .md {
            font-size: var(--skin-text-base, 14px);
            line-height: var(--skin-leading-relaxed, 1.65);
        }

        .md :is(h1, h2, h3, h4) {
            margin: 0.8em 0 0.35em;
            line-height: var(--skin-leading-tight, 1.25);
        }

        .md p {
            margin: 0.55em 0;
        }

        .md pre {
            overflow: auto;
            padding: var(--skin-space-sm, 8px);
            border-radius: var(--skin-radius-sm, 4px);
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.04));
            font-family: var(--skin-font-mono, ui-monospace, monospace);
            font-size: var(--skin-text-xs, 12px);
        }

        .md code {
            font-family: var(--skin-font-mono, ui-monospace, monospace);
            font-size: 0.92em;
        }

        .md a {
            color: var(--skin-color-text-link, #2563eb);
        }

        img.view {
            display: block;
            max-width: 100%;
            max-height: 60vh;
            margin: 0 auto;
            border-radius: var(--skin-radius-sm, 4px);
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.03));
        }

        iframe.pdf {
            width: 100%;
            height: min(60vh, 640px);
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
            border-radius: var(--skin-radius-sm, 4px);
            background: var(--skin-color-bg-base, #ffffff);
        }

        .meta-card {
            display: grid;
            grid-template-columns: minmax(96px, 140px) 1fr;
            gap: var(--skin-space-xs, 4px) var(--skin-space-sm, 8px);
            font-size: var(--skin-text-sm, 13px);
            max-width: 520px;
        }

        .meta-card dt {
            color: var(--skin-color-text-muted, #666666);
        }

        .meta-card dd {
            margin: 0;
            font-family: var(--skin-font-mono, ui-monospace, monospace);
            word-break: break-all;
        }

        .note {
            margin-top: var(--skin-space-md, 16px);
            padding: var(--skin-space-sm, 8px) var(--skin-space-md, 12px);
            border-radius: var(--skin-radius-md, 8px);
            border: 1px solid var(--skin-color-border-subtle, rgba(0, 0, 0, 0.05));
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.03));
            color: var(--skin-color-text-secondary, #555555);
            font-size: var(--skin-text-xs, 12px);
            line-height: var(--skin-leading-normal, 1.5);
        }
    `;

    /** filesv2 id — required for any authorized fetch. */
    @property({ attribute: 'file-id' }) fileId = '';
    @property() name = '';
    @property() mime = '';
    @property({ type: Number, attribute: 'size-bytes' }) sizeBytes = 0;
    /** Present-but-disabled Edit affordance until PUT content exists (CM-02 FM-37). */
    @property({ type: Boolean, attribute: 'show-edit' }) showEdit = false;

    @state() private _status: FilePreviewStatus = 'idle';
    @state() private _kind: FilePreviewKind = 'metadata';
    @state() private _signedUrl = '';
    @state() private _textBody: string | null = null;
    @state() private _error = '';

    private _loadToken = 0;

    override willUpdate(changed: Map<string, unknown>): void {
        if (
            changed.has('fileId') ||
            changed.has('mime') ||
            changed.has('name')
        ) {
            this._kind = previewKindOf(this.mime, this.name);
            void this._load();
        }
    }

    /** Public reload — hosts call after a replace/upload of the same id. */
    reload(): void {
        void this._load();
    }

    private async _load(): Promise<void> {
        const token = ++this._loadToken;
        const kindAtStart: FilePreviewKind = this._kind;
        this._error = '';
        this._signedUrl = '';
        this._textBody = null;

        if (!this.fileId) {
            this._status = 'idle';
            return;
        }

        // Binary/unknown never fetches a renderer body — metadata only.
        if (this._kind === 'metadata') {
            this._status = 'ready';
            return;
        }

        this._status = 'loading';
        try {
            const signed = await apiClient.get<DownloadUrlOut>(
                `/filesv2/${encodeURIComponent(this.fileId)}/download-url`,
            );
            if (token !== this._loadToken) return;
            if (!signed?.download_url) {
                this._status = 'error';
                this._error =
                    'GET /api/v2/filesv2/{id}/download-url returned no download_url — Preview unavailable.';
                return;
            }
            this._signedUrl = signed.download_url;

            if (this._kind === 'image' || this._kind === 'pdf') {
                // Authorized URL is the renderer source; browser fetches bytes.
                this._status = 'ready';
                return;
            }

            const res = await fetch(signed.download_url);
            if (token !== this._loadToken) return;
            if (!res.ok) {
                this._status = 'error';
                this._error = `Preview body fetch refused (HTTP ${res.status}) — Preview unavailable.`;
                return;
            }
            this._textBody = await res.text();
            this._status = 'ready';
        } catch (err) {
            if (token !== this._loadToken) return;
            this._status = 'error';
            this._error =
                kindAtStart === 'metadata'
                    ? reasonOf(err)
                    : `Preview unavailable — ${reasonOf(err)}`;
        }
    }

    private _onDownloadClick(): void {
        this.dispatchEvent(
            new CustomEvent<{ fileId: string; name: string }>('soma-download', {
                detail: { fileId: this.fileId, name: this.name },
                bubbles: true,
                composed: true,
            }),
        );
    }

    private _onEditRequest(): void {
        this.dispatchEvent(
            new CustomEvent<{ fileId: string; name: string }>('soma-edit-request', {
                detail: { fileId: this.fileId, name: this.name },
                bubbles: true,
                composed: true,
            }),
        );
    }

    private get _editDisabledReason(): string {
        return 'Editor Save needs the filesv2 content write API (PUT /api/v2/filesv2/{id}/content).';
    }

    private _renderBody(): TemplateResult {
        if (this._status === 'idle') {
            return html`
                <div class="status">
                    <span class="material-symbols-outlined">visibility</span>
                    <span>Select a file to preview.</span>
                </div>
            `;
        }

        if (this._status === 'loading') {
            return html`
                <div class="status" aria-live="polite">
                    <span class="material-symbols-outlined">hourglass_top</span>
                    <span>Loading preview…</span>
                </div>
            `;
        }

        if (this._status === 'error') {
            return html`
                <div class="status error" role="alert">
                    <span class="material-symbols-outlined">error</span>
                    <span>Preview unavailable.</span>
                    ${this._error ? html`<span class="note">${this._error}</span>` : nothing}
                </div>
            `;
        }

        switch (this._kind) {
            case 'metadata':
                return html`
                    <dl class="meta-card">
                        <dt>Name</dt>
                        <dd>${this.name || '—'}</dd>
                        <dt>MIME</dt>
                        <dd>${this.mime || '—'}</dd>
                        <dt>Size</dt>
                        <dd>${this.sizeBytes > 0 ? formatBytes(this.sizeBytes) : '—'}</dd>
                        <dt>Preview</dt>
                        <dd>metadata only — no renderer for this type</dd>
                    </dl>
                    <div class="note">
                        Binary or unknown mime. This pane never fabricates a document view —
                        use Download for the real bytes.
                    </div>
                `;

            case 'image':
                return this._signedUrl
                    ? html`<img
                          class="view"
                          src=${this._signedUrl}
                          alt=${this.name || 'file preview'}
                      />`
                    : html`<div class="status error" role="alert">
                          <span>No authorized URL for image preview.</span>
                      </div>`;

            case 'pdf':
                return this._signedUrl
                    ? html`<iframe
                          class="pdf"
                          src=${this._signedUrl}
                          title=${`PDF preview — ${this.name || this.fileId}`}
                      ></iframe>`
                    : html`<div class="status error" role="alert">
                          <span>No authorized URL for PDF preview.</span>
                      </div>`;

            case 'markdown':
                return this._textBody !== null
                    ? html`<div class="md">
                          ${unsafeHTML(
                              renderMarkdown(this._textBody, { onCodeBlock: renderCodeBlock }),
                          )}
                      </div>`
                    : html`<div class="status error" role="alert">
                          <span>No markdown body loaded.</span>
                      </div>`;

            case 'code':
            default:
                return this._textBody !== null
                    ? html`<pre
                          class="code"
                          data-language=${languageOf(this.name)}
                      ><code>${this._textBody}</code></pre>`
                    : html`<div class="status error" role="alert">
                          <span>No text body loaded.</span>
                      </div>`;
        }
    }

    override render(): TemplateResult {
        return html`
            <div class="bar">
                <span class="name" title=${this.name || this.fileId}>${this.name || '—'}</span>
                <span class="kind-chip">${this._kind}</span>
                ${this.sizeBytes > 0
                    ? html`<span class="meta">${formatBytes(this.sizeBytes)}</span>`
                    : nothing}
                ${this.showEdit
                    ? html`<button
                          class="icon-btn"
                          disabled
                          title=${this._editDisabledReason}
                          aria-disabled="true"
                          aria-label="Request edit (disabled: no content write API)"
                          @click=${this._onEditRequest}
                      >
                          <span class="material-symbols-outlined" aria-hidden="true">edit</span>
                          Edit
                      </button>`
                    : nothing}
                <button
                    class="icon-btn"
                    aria-label="Download"
                    title="Download"
                    ?disabled=${!this.fileId}
                    @click=${this._onDownloadClick}
                >
                    <span class="material-symbols-outlined" aria-hidden="true">download</span>
                    Download
                </button>
            </div>
            <div class="body">${this._renderBody()}</div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-file-preview': SomaFilePreview;
    }
}
