/**
 * AgentSkin SDK — surface keys (SOMA-UI-SKINS-001 §3.3, OPEN-03 closed set).
 * A surface override may reuse any core token name; it may not invent new ones.
 */

export const SURFACE_KEYS = [
  'chat',
  'sidebar',
  'composer',
  'tool_timeline',
  'login',
  'chrome',
  'right_panel',
] as const;

export type SurfaceKey = (typeof SURFACE_KEYS)[number];

export function isSurfaceKey(key: string): key is SurfaceKey {
  return (SURFACE_KEYS as readonly string[]).includes(key);
}

/** DOM attribute the applier writes surface tokens onto (I-4). */
export const SURFACE_ATTR = 'data-skin-surface';

/** DOM attribute for per-agent isolation hosts (I-1/I-2). */
export const HOST_ATTR = 'data-skin-host';
