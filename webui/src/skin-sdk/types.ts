/**
 * AgentSkin SDK — skin document types (SOMA-UI-SKINS-001 §3.1).
 */

import type { SurfaceKey } from './surfaces.js';

export const SKIN_SCHEMA_VERSION = '1';

export interface SkinChangelogEntry {
  version: string;
  date: string;
  note: string;
}

export interface SkinMeta {
  author?: string;
  version?: string;
  changelog?: SkinChangelogEntry[];
}

/** Token map: closed --skin-* names → CSS values. */
export type TokenMap = Record<string, string>;

export interface SkinDocument {
  schema_version: string;
  name: string;
  description?: string;
  template?: string;
  tokens: TokenMap;
  surfaces?: Partial<Record<SurfaceKey, TokenMap>>;
  meta?: SkinMeta;
}

export type SanitiseRuleId =
  | 'X-1'
  | 'X-2'
  | 'X-3'
  | 'X-4'
  | 'X-5'
  | 'X-6'
  | 'X-7'
  | 'X-8'
  | 'X-9'
  | 'X-10'
  | 'X-11'
  | 'X-12'
  | 'A11Y-1'
  | 'A11Y-2'
  | 'A11Y-5'
  | 'T-2';

export interface SanitiseFinding {
  rule: SanitiseRuleId;
  token?: string;
  message: string;
}

export type SanitiseResult =
  | { ok: true; document: SkinDocument }
  | { ok: false; findings: SanitiseFinding[] };
