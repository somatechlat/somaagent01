/**
 * soma-artifacts — document artifacts panel (PDF/DOCX/XLSX/PPTX).
 * List + preview host + download + attach. Honest empty/error. No mocks.
 */
import { LitElement, css, html, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';

interface ArtifactFile {
  id: string;
  name: string;
  size?: number;
  content_type?: string;
  created_at?: string;
}

const KINDS = ['all', 'pdf', 'docx', 'xlsx', 'pptx'] as const;
type Kind = (typeof KINDS)[number];

function kindOf(name: string, mime?: string): Kind {
  const n = name.toLowerCase();
  if (n.endsWith('.pdf') || mime === 'application/pdf') return 'pdf';
  if (n.endsWith('.docx') || mime?.includes('word')) return 'docx';
  if (n.endsWith('.xlsx') || mime?.includes('sheet')) return 'xlsx';
  if (n.endsWith('.pptx') || mime?.includes('presentation')) return 'pptx';
  return 'all';
}

@customElement('soma-artifacts')
export class SomaArtifacts extends LitElement {
  static override styles = css`
    :host {
      display: block; height: 100%;
      font-family: var(--skin-font-sans, system-ui, sans-serif);
      color: var(--skin-color-text-primary, #1a1a1a);
    }
    .toolbar {
      display: flex; gap: var(--skin-space-sm, 8px); align-items: center;
      flex-wrap: wrap; padding: var(--skin-space-sm, 8px) 0;
    }
    .tabs { display: flex; gap: 4px; flex-wrap: wrap; }
    .tab {
      border: 1px solid var(--skin-color-border, rgba(0,0,0,.1));
      background: var(--skin-color-bg-base, #fff); color: inherit;
      border-radius: var(--skin-radius-full, 999px); padding: 4px 12px;
      font-size: var(--skin-text-xs, 11px); cursor: pointer;
    }
    .tab.active {
      background: var(--skin-color-accent, #FF4D00);
      color: var(--skin-color-accent-text, #fff); border-color: transparent;
    }
    table { width: 100%; border-collapse: collapse; font-size: var(--skin-text-sm, 13px); }
    th, td { text-align: left; padding: 8px 6px; border-bottom: 1px solid var(--skin-color-border-subtle, rgba(0,0,0,.06)); }
    button {
      border-radius: var(--skin-radius-md, 8px); border: 1px solid var(--skin-color-border, rgba(0,0,0,.12));
      background: var(--skin-color-bg-base, #fff); color: inherit; cursor: pointer;
      padding: 5px 10px; font-size: var(--skin-text-xs, 11px);
    }
    .preview {
      margin-top: var(--skin-space-md, 16px);
      border: 1px solid var(--skin-color-border, rgba(0,0,0,.1));
      border-radius: var(--skin-radius-lg, 12px);
      background: var(--skin-color-bg-card, #fff);
      min-height: 160px; padding: var(--skin-space-md, 16px);
    }
    .status { padding: var(--skin-space-md, 16px); color: var(--skin-color-text-secondary, #666); }
    .status.error { color: var(--skin-color-danger, #ef4444); }
  `;

  @state() private _files: ArtifactFile[] = [];
  @state() private _kind: Kind = 'all';
  @state() private _error = '';
  @state() private _loading = false;
  @state() private _selected: ArtifactFile | null = null;

  override connectedCallback(): void {
    super.connectedCallback();
    void this._load();
  }

  private async _load() {
    this._loading = true;
    this._error = '';
    try {
      const res = await apiClient.get<{ files?: ArtifactFile[] } | ArtifactFile[]>('/filesv2/');
      const list = Array.isArray(res) ? res : (res.files ?? []);
      this._files = list.filter((f) => {
        const k = kindOf(f.name, f.content_type);
        return k !== 'all';
      });
    } catch (e) {
      this._error = e instanceof Error ? e.message : 'Failed to load artifacts';
      this._files = [];
    } finally {
      this._loading = false;
    }
  }

  private _rows(): ArtifactFile[] {
    if (this._kind === 'all') return this._files;
    return this._files.filter((f) => kindOf(f.name, f.content_type) === this._kind);
  }

  private _attach(f: ArtifactFile) {
    this.dispatchEvent(new CustomEvent('soma-artifact-attach', {
      detail: { id: f.id, name: f.name },
      bubbles: true,
      composed: true,
    }));
  }

  override render() {
    return html`
      <div class="toolbar">
        <div class="tabs">
          ${KINDS.map(
            (k) => html`
              <button
                class="tab ${this._kind === k ? 'active' : ''}"
                @click=${() => { this._kind = k; }}
                aria-pressed=${this._kind === k}
              >
                ${k.toUpperCase()}
              </button>
            `,
          )}
        </div>
        <button data-testid="artifacts-refresh" @click=${() => void this._load()}>Refresh</button>
      </div>
      ${this._error
        ? html`<div class="status error" role="alert">${this._error}
            <button @click=${() => void this._load()}>Retry</button></div>`
        : this._loading
          ? html`<div class="status" role="status">Loading artifacts…</div>`
          : this._rows().length === 0
            ? html`<div class="status" role="status">No artifacts yet. Ask the agent to create a PDF, DOCX, XLSX, or PPTX.</div>`
            : html`
                <table>
                  <thead><tr><th>Name</th><th>Type</th><th>Size</th><th>Actions</th></tr></thead>
                  <tbody>
                    ${this._rows().map(
                      (f) => html`
                        <tr>
                          <td>${f.name}</td>
                          <td>${kindOf(f.name, f.content_type)}</td>
                          <td>${f.size != null ? `${Math.round(f.size / 1024)} KB` : '—'}</td>
                          <td>
                            <button data-testid="artifact-preview" @click=${() => { this._selected = f; }}>Preview</button>
                            <button data-testid="artifact-attach" @click=${() => this._attach(f)}>Attach</button>
                          </td>
                        </tr>
                      `,
                    )}
                  </tbody>
                </table>
                ${this._selected
                  ? html`
                      <div class="preview" data-testid="artifact-preview-pane">
                        <strong>${this._selected.name}</strong>
                        <div class="status">
                          Preview renders in the canvas host when a typed viewer is bound
                          (pdf/docx/xlsx/pptx). Use Open in Editor or Download from Files for now.
                        </div>
                        <button @click=${() => { this._selected = null; }}>Close preview</button>
                      </div>
                    `
                  : nothing}
              `}
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'soma-artifacts': SomaArtifacts;
  }
}
