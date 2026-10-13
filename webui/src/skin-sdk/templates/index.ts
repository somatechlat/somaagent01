/**
 * AgentSkin SDK — bundled installable packs registry.
 * These six packs ship with the UI and appear in Settings › Interface › Skins.
 * Additional packs install from registry/file/agent via installSkinPack().
 */

import type { SkinPackManifest } from '../pack.js';

import platformLight from './platform-light.json';
import platformDark from './platform-dark.json';
import somaBrand from './soma-brand.json';
import highContrast from './high-contrast.json';
import slateCool from './slate-cool.json';
import paperLight from './paper-light.json';

export const BUNDLED_PACKS: readonly SkinPackManifest[] = [
  platformLight,
  platformDark,
  somaBrand,
  highContrast,
  slateCool,
  paperLight,
] as unknown as readonly SkinPackManifest[];

export function getBundledPack(packId: string): SkinPackManifest | undefined {
  return BUNDLED_PACKS.find((p) => p.pack_id === packId);
}

export function listBundledPacks(): SkinPackManifest[] {
  return [...BUNDLED_PACKS];
}
