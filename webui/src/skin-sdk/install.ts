/**
 * AgentSkin SDK — installable pack lifecycle for Settings › Skins gallery.
 *
 * Storage contract (client mirror of the server store):
 *   localStorage key `soma-installed-skins` → InstalledSkinPack[]
 *   localStorage key `soma-active-skin-id`  → install_id
 *
 * The API client (webui/src/services/api-client.ts) syncs the same records to
 * `GET/POST/DELETE /ui/skins*` when the backend store is live. Local storage is
 * the standalone-mode persistence — not a mock of a missing API.
 */

import {
  isSkinPackManifest,
  type InstalledSkinPack,
  type SkinPackManifest,
  type SkinPackSource,
  type SkinSwatch,
} from './pack.js';
import { sanitiseSkin } from './validate.js';
import type { SkinDocument, SanitiseFinding } from './types.js';
import { BUNDLED_PACKS, getBundledPack } from './templates/index.js';

const INSTALLED_KEY = 'soma-installed-skins';
const ACTIVE_KEY = 'soma-active-skin-id';

export type InstallResult =
  | { ok: true; pack: InstalledSkinPack }
  | { ok: false; findings: SanitiseFinding[]; message: string };

function readInstalled(): InstalledSkinPack[] {
  try {
    const raw = localStorage.getItem(INSTALLED_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as InstalledSkinPack[]) : [];
  } catch {
    return [];
  }
}

function writeInstalled(packs: InstalledSkinPack[]): void {
  localStorage.setItem(INSTALLED_KEY, JSON.stringify(packs));
}

function readActiveId(): string | null {
  return localStorage.getItem(ACTIVE_KEY);
}

function writeActiveId(id: string | null): void {
  if (id === null) localStorage.removeItem(ACTIVE_KEY);
  else localStorage.setItem(ACTIVE_KEY, id);
}

function packSwatches(manifest: SkinPackManifest): SkinSwatch[] {
  return Array.isArray(manifest.swatches) ? manifest.swatches.slice(0, 6) : [];
}

function toInstalled(
  manifest: SkinPackManifest,
  skin: SkinDocument,
  source: SkinPackSource,
): InstalledSkinPack {
  const now = new Date().toISOString();
  return {
    install_id: `${manifest.pack_id}@${manifest.version}`,
    pack_id: manifest.pack_id,
    version: manifest.version,
    title: manifest.title,
    description: manifest.description,
    tags: Array.isArray(manifest.tags) ? manifest.tags : [],
    swatches: packSwatches(manifest),
    source,
    installed_at: now,
    active: false,
    skin,
    meta: skin.meta,
  };
}

/** All installed packs (gallery list). Bundled packs auto-seed on first open. */
export function listInstalledSkins(): InstalledSkinPack[] {
  const existing = readInstalled();
  if (existing.length === 0) {
    // First run: install every bundled pack so the gallery is never empty.
    const seeded: InstalledSkinPack[] = [];
    for (const manifest of BUNDLED_PACKS) {
      const result = installSkinPack(manifest, 'bundled');
      if (result.ok) seeded.push(result.pack);
    }
    return seeded;
  }
  const activeId = readActiveId();
  return existing.map((p) => ({ ...p, active: p.install_id === activeId }));
}

/**
 * Install a pack. Runs the full sanitiser (X-1…X-12) on the inner skin.
 * Rejects whole on any finding — never a partial install.
 */
export function installSkinPack(
  input: unknown,
  source: SkinPackSource = 'file',
): InstallResult {
  if (!isSkinPackManifest(input)) {
    return {
      ok: false,
      findings: [
        { rule: 'X-2', message: 'not a soma-skin-pack manifest' },
      ],
      message: 'Invalid skin pack format',
    };
  }
  const manifest = input;
  const result = sanitiseSkin(manifest.skin);
  if (!result.ok) {
    return {
      ok: false,
      findings: result.findings,
      message: `Skin rejected: ${result.findings.map((f) => f.rule).join(', ')}`,
    };
  }

  const installed = toInstalled(manifest, result.document, source);
  const packs = readInstalled().filter(
    (p) => p.install_id !== installed.install_id,
  );
  packs.push(installed);
  writeInstalled(packs);

  return { ok: true, pack: { ...installed, active: readActiveId() === installed.install_id } };
}

export function uninstallSkinPack(installId: string): boolean {
  const packs = readInstalled();
  const next = packs.filter((p) => p.install_id !== installId);
  if (next.length === packs.length) return false;
  writeInstalled(next);
  if (readActiveId() === installId) writeActiveId(null);
  return true;
}

export function getInstalledSkin(installId: string): InstalledSkinPack | undefined {
  return readInstalled().find((p) => p.install_id === installId);
}

export function getActiveSkin(): InstalledSkinPack | null {
  const id = readActiveId();
  if (!id) return null;
  return readInstalled().find((p) => p.install_id === id) ?? null;
}

/** Mark a pack active (caller then runs SkinApplier). */
export function setActiveSkin(installId: string): boolean {
  const pack = getInstalledSkin(installId);
  if (!pack) return false;
  writeActiveId(installId);
  return true;
}

export function clearActiveSkin(): void {
  writeActiveId(null);
}

/** Ensure the bundled pack set is present (idempotent). */
export function ensureBundledSkins(): void {
  for (const manifest of BUNDLED_PACKS) {
    const id = `${manifest.pack_id}@${manifest.version}`;
    if (!getInstalledSkin(id)) {
      installSkinPack(manifest, 'bundled');
    }
  }
}

export { getBundledPack };
