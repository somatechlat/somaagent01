/**
 * AgentSkin SDK — four-source resolution (SOMA-UI-SKINS-001 §4.1).
 * Merge is per TOKEN, not per document. Highest source wins; lower fill gaps.
 */

import type { SurfaceKey } from './surfaces.js';
import type { SkinDocument, TokenMap } from './types.js';

export type SkinSourceLayer =
  | 'capsule'
  | 'agent_setting'
  | 'tenant'
  | 'platform';

/** Highest precedence first. */
export const RESOLUTION_ORDER: readonly SkinSourceLayer[] = [
  'capsule',
  'agent_setting',
  'tenant',
  'platform',
] as const;

export interface SkinSources {
  capsule?: SkinDocument | null;
  agent_setting?: SkinDocument | null;
  tenant?: SkinDocument | null;
  platform: SkinDocument;
}

export interface ResolvedSkin {
  /** Effective core token map (complete — every required token present). */
  tokens: TokenMap;
  /** Effective per-surface maps (surface overrides merged per token). */
  surfaces: Partial<Record<SurfaceKey, TokenMap>>;
  /** Which layer supplied each core token (debug / honesty UI). */
  provenance: Record<string, SkinSourceLayer>;
  /** Layer that supplied the display name. */
  name: string;
}

function layerOf(
  sources: SkinSources,
  layer: SkinSourceLayer,
): SkinDocument | null | undefined {
  switch (layer) {
    case 'capsule':
      return sources.capsule;
    case 'agent_setting':
      return sources.agent_setting;
    case 'tenant':
      return sources.tenant;
    case 'platform':
      return sources.platform;
  }
}

/**
 * Resolve the effective skin. Per-token: first source that defines a value wins.
 * Absent / non-object / failed-sanitise sources are skipped by the caller
 * (this function assumes already-valid documents; sanitise before resolve).
 */
export function resolveSkin(sources: SkinSources): ResolvedSkin {
  const tokens: TokenMap = {};
  const provenance: Record<string, SkinSourceLayer> = {};
  let name = sources.platform.name;

  for (const layer of RESOLUTION_ORDER) {
    const doc = layerOf(sources, layer);
    if (!doc || typeof doc !== 'object') continue;
    if (layer === 'capsule' || layer === 'agent_setting' || layer === 'tenant') {
      name = doc.name || name;
    }
    for (const [key, value] of Object.entries(doc.tokens ?? {})) {
      if (tokens[key] === undefined) {
        tokens[key] = value;
        provenance[key] = layer;
      }
    }
  }

  // Platform fills any remaining required gaps (platform is complete by T-2).
  for (const [key, value] of Object.entries(sources.platform.tokens ?? {})) {
    if (tokens[key] === undefined) {
      tokens[key] = value;
      provenance[key] = 'platform';
    }
  }

  // Surfaces: same per-token merge across layers, then surface key.
  const surfaces: Partial<Record<SurfaceKey, TokenMap>> = {};
  const surfaceKeys = new Set<string>();
  for (const layer of RESOLUTION_ORDER) {
    const doc = layerOf(sources, layer);
    if (!doc?.surfaces) continue;
    for (const k of Object.keys(doc.surfaces)) surfaceKeys.add(k);
  }
  for (const sk of surfaceKeys) {
    const merged: TokenMap = {};
    for (const layer of RESOLUTION_ORDER) {
      const doc = layerOf(sources, layer);
      const map = doc?.surfaces?.[sk as SurfaceKey];
      if (!map) continue;
      for (const [key, value] of Object.entries(map)) {
        if (merged[key] === undefined) merged[key] = value;
      }
    }
    if (Object.keys(merged).length > 0) {
      surfaces[sk as SurfaceKey] = merged;
    }
  }

  return { tokens, surfaces, provenance, name };
}

/**
 * Effective value of one token after resolution (including surface override).
 */
export function effectiveToken(
  resolved: ResolvedSkin,
  token: string,
  surface?: SurfaceKey,
): string | undefined {
  if (surface) {
    const override = resolved.surfaces[surface]?.[token];
    if (override !== undefined) return override;
  }
  return resolved.tokens[token];
}
