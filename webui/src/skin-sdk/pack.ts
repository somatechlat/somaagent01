/**
 * AgentSkin SDK — installable skin package format.
 *
 * A skin is an INSTALLABLE pack (not a loose JSON blob):
 *   - pack manifest (this file's types)
 *   - skin document (SOMA-UI-SKINS-001 §3.1)
 *   - optional preview metadata (label, swatches — no remote assets, SEC-2)
 *
 * Settings shows many installed packs; operator installs/uninstalls/applies
 * from the gallery. Agents/devs ship packs via the same contract.
 */

import type { SkinDocument, SkinMeta } from './types.js';

export const SKIN_PACK_FORMAT = 'soma-skin-pack';
export const SKIN_PACK_FORMAT_VERSION = '1';

export type SkinPackSource =
  | 'bundled'
  | 'registry'
  | 'file'
  | 'agent'
  | 'tenant';

export interface SkinSwatch {
  /** Token name whose value this swatch shows (must be a known --skin-* colour). */
  token: string;
  label: string;
}

export interface SkinPackManifest {
  /** Discriminator — always `soma-skin-pack`. */
  format: typeof SKIN_PACK_FORMAT;
  format_version: string;
  /** Pack id: kebab-case, unique within an install scope. */
  pack_id: string;
  /** Human title shown in the Settings gallery. */
  title: string;
  description?: string;
  /** Semver of the pack content. */
  version: string;
  author?: string;
  /** Tags for gallery filter (e.g. "dark", "high-contrast", "brand"). */
  tags?: string[];
  /** Palette swatches for the gallery card (no images — SEC-2). */
  swatches?: SkinSwatch[];
  /** Where this pack came from (set on install). */
  source?: SkinPackSource;
  /**
   * The skin document this pack installs.
   * For a pure template pack, `tokens` is complete and `surfaces` is empty (T-5).
   */
  skin: SkinDocument;
}

export interface InstalledSkinPack {
  /** Stable install id (uuid or pack_id@version). */
  install_id: string;
  pack_id: string;
  version: string;
  title: string;
  description?: string;
  tags: string[];
  swatches: SkinSwatch[];
  source: SkinPackSource;
  installed_at: string;
  /** True when this pack is the active applied skin for the current scope. */
  active: boolean;
  /** The resolved document stored on install (post-sanitise). */
  skin: SkinDocument;
  meta?: SkinMeta;
}

export function isSkinPackManifest(
  value: unknown,
): value is SkinPackManifest {
  if (!value || typeof value !== 'object') return false;
  const m = value as Record<string, unknown>;
  return (
    m.format === SKIN_PACK_FORMAT &&
    typeof m.pack_id === 'string' &&
    typeof m.title === 'string' &&
    typeof m.version === 'string' &&
    !!m.skin &&
    typeof m.skin === 'object'
  );
}
