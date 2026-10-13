/**
 * soma-skin-gallery — Settings › Interface › Skins.
 * Installable skin packs: browse, install, preview, apply, uninstall.
 * Honesty: empty ≠ error; failures render as visible alerts.
 */

import { LitElement, css, html, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import type { InstalledSkinPack } from '../skin-sdk/index.js';
import {
  clearActiveSkin,
  getActiveSkin,
  installSkinPack,
  listInstalledSkins,
  listBundledPacks,
  resolveSkin,
  setActiveSkin,
  uninstallSkinPack,
} from '../skin-sdk/index.js';
import type { SkinDocument } from '../skin-sdk/index.js';
import { SkinApplier } from '../services/skin-applier.js';

@customElement('soma-skin-gallery')
export class SomaSkinGallery extends LitElement {
  static override styles = css`
    :host {
      display: block;
      font-family: var(--soma-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif);
      color: var(--soma-text-primary, #1a1a1a);
    }
    .gallery-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 12px;
    }
    .gallery-title {
      font-size: 14px;
      font-weight: 600;
      margin: 0;
    }
    .gallery-desc {
      font-size: 12px;
      color: var(--soma-text-secondary, #666666);
      margin: 4px 0 0;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 12px;
      margin-top: 12px;
    }
    .card {
      border: 1px solid var(--soma-border-light, #e0e0e0);
      border-radius: 10px;
      padding: 12px;
      background: var(--soma-bg-card, #ffffff);
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .card.active {
      border-color: var(--soma-accent, #FF4D00);
      box-shadow: 0 0 0 1px var(--soma-accent, #FF4D00);
    }
    .card h4 {
      margin: 0;
      font-size: 13px;
      font-weight: 600;
    }
    .card p {
      margin: 0;
      font-size: 11px;
      color: var(--soma-text-secondary, #666666);
      flex: 1;
    }
    .swatches {
      display: flex;
      gap: 4px;
    }
    .swatch {
      width: 18px;
      height: 18px;
      border-radius: 4px;
      border: 1px solid var(--soma-border-light, #e0e0e0);
    }
    .tags {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
    }
    .tag {
      font-size: 10px;
      padding: 1px 6px;
      border-radius: 999px;
      background: var(--soma-bg-hover, #f0f0f0);
      color: var(--soma-text-secondary, #666666);
    }
    .badge {
      font-size: 10px;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 999px;
      background: var(--soma-accent, #FF4D00);
      color: #ffffff;
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    button {
      font-size: 11px;
      padding: 5px 10px;
      border-radius: 6px;
      border: 1px solid var(--soma-border-light, #e0e0e0);
      background: var(--soma-bg-base, #ffffff);
      color: var(--soma-text-primary, #1a1a1a);
      cursor: pointer;
    }
    button:hover:not(:disabled) {
      background: var(--soma-bg-hover, #f5f5f5);
    }
    button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    button.primary {
      background: var(--soma-accent, #FF4D00);
      border-color: var(--soma-accent, #FF4D00);
      color: #ffffff;
    }
    button.danger {
      color: var(--soma-danger, #ef4444);
      border-color: var(--soma-danger, #ef4444);
    }
    .status {
      font-size: 12px;
      margin-top: 10px;
      padding: 8px 10px;
      border-radius: 6px;
    }
    .status.error {
      background: rgba(239, 68, 68, 0.1);
      color: var(--soma-danger, #ef4444);
    }
    .status.ok {
      background: rgba(34, 197, 94, 0.12);
      color: var(--soma-success, #22c55e);
    }
    .status.info {
      background: var(--soma-bg-hover, #f5f5f5);
      color: var(--soma-text-secondary, #666666);
    }
    :focus-visible {
      outline: 2px solid var(--soma-accent, #FF4D00);
      outline-offset: 2px;
    }
  `;

  @state() private _packs: InstalledSkinPack[] = [];
  @state() private _activeId: string | null = null;
  @state() private _status: { kind: 'ok' | 'error' | 'info'; message: string } | null =
    null;
  @state() private _previewing = false;

  override connectedCallback(): void {
    super.connectedCallback();
    this._refresh();
  }

  private _refresh(): void {
    try {
      this._packs = listInstalledSkins();
      this._activeId = getActiveSkin()?.install_id ?? null;
    } catch (err) {
      this._status = {
        kind: 'error',
        message: `Failed to load skins: ${err instanceof Error ? err.message : String(err)}`,
      };
    }
  }

  private _applyPack(pack: InstalledSkinPack): void {
    try {
      const resolved = resolveSkin({ platform: pack.skin });
      SkinApplier.apply(resolved);
      setActiveSkin(pack.install_id);
      this._previewing = false;
      this._status = {
        kind: 'ok',
        message: `Applied skin “${pack.title}”.`,
      };
      this._refresh();
    } catch (err) {
      this._status = {
        kind: 'error',
        message: `Apply failed: ${err instanceof Error ? err.message : String(err)}`,
      };
    }
  }

  private _previewPack(pack: InstalledSkinPack): void {
    try {
      const resolved = resolveSkin({ platform: pack.skin });
      SkinApplier.preview(resolved);
      this._previewing = true;
      this._status = {
        kind: 'info',
        message: `Previewing “${pack.title}”. Revert to restore the previous look.`,
      };
    } catch (err) {
      this._status = {
        kind: 'error',
        message: `Preview failed: ${err instanceof Error ? err.message : String(err)}`,
      };
    }
  }

  private _revert(): void {
    const ok = SkinApplier.revert();
    this._previewing = false;
    this._status = {
      kind: ok ? 'ok' : 'error',
      message: ok
        ? 'Reverted to the previous skin.'
        : 'Nothing to revert — no previous skin in this session.',
    };
    this._refresh();
  }

  private _uninstall(pack: InstalledSkinPack): void {
    const ok = uninstallSkinPack(pack.install_id);
    if (ok) {
      if (this._activeId === pack.install_id) {
        clearActiveSkin();
        SkinApplier.clear();
      }
      this._status = {
        kind: 'ok',
        message: `Uninstalled “${pack.title}”.`,
      };
    } else {
      this._status = {
        kind: 'error',
        message: `Could not uninstall “${pack.title}”.`,
      };
    }
    this._refresh();
  }

  private _installBundled(): void {
    let installed = 0;
    for (const manifest of listBundledPacks()) {
      const result = installSkinPack(manifest, 'bundled');
      if (result.ok) installed += 1;
    }
    this._status = {
      kind: 'ok',
      message: `Installed ${installed} bundled pack(s).`,
    };
    this._refresh();
  }

  private _renderCard(pack: InstalledSkinPack) {
    const isActive = pack.install_id === this._activeId;
    return html`
      <div class="card ${isActive ? 'active' : ''}" data-testid="skin-card">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:8px">
          <h4>${pack.title}</h4>
          ${isActive ? html`<span class="badge" data-testid="skin-active">Active</span>` : nothing}
        </div>
        <div class="swatches" aria-hidden="true">
          ${pack.swatches.map(
            (s) => html`
              <span
                class="swatch"
                style="background: ${pack.skin.tokens[s.token] ?? '#ccc'}"
                title="${s.label}"
              ></span>
            `,
          )}
        </div>
        <p>${pack.description ?? 'No description.'}</p>
        <div class="tags">
          ${pack.tags.map((t) => html`<span class="tag">${t}</span>`)}
        </div>
        <div class="actions">
          ${isActive
            ? nothing
            : html`
                <button
                  class="primary"
                  data-testid="skin-apply"
                  @click=${() => this._applyPack(pack)}
                >
                  Apply
                </button>
              `}
          <button data-testid="skin-preview" @click=${() => this._previewPack(pack)}>
            Preview
          </button>
          <button
            class="danger"
            data-testid="skin-uninstall"
            @click=${() => this._uninstall(pack)}
            ?disabled=${isActive}
            title=${isActive ? 'Unapply this skin before uninstalling' : 'Uninstall'}
          >
            Uninstall
          </button>
        </div>
      </div>
    `;
  }

  override render() {
    return html`
      <div class="gallery-header">
        <div>
          <h3 class="gallery-title">Skins</h3>
          <p class="gallery-desc">
            Installable appearance packs. Apply changes colours, type, spacing — never layout.
          </p>
        </div>
        <div class="actions">
          ${this._previewing
            ? html`<button data-testid="skin-revert" @click=${this._revert}>
                Revert preview
              </button>`
            : nothing}
          <button data-testid="skin-install-bundled" @click=${this._installBundled}>
            Install bundled
          </button>
        </div>
      </div>

      ${this._status
        ? html`
            <div
              class="status ${this._status.kind}"
              role="${this._status.kind === 'error' ? 'alert' : 'status'}"
              data-testid="skin-status"
            >
              ${this._status.message}
            </div>
          `
        : nothing}

      ${this._packs.length === 0
        ? html`
            <div class="status info" role="status">
              No skins installed yet. Click “Install bundled” to load the shipped packs.
            </div>
          `
        : html`
            <div class="grid" data-testid="skin-grid">
              ${this._packs.map((p) => this._renderCard(p))}
            </div>
          `}
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'soma-skin-gallery': SomaSkinGallery;
  }
}
