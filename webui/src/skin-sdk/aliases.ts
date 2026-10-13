/**
 * Skin token alias table — migration bridge (SOMA-ARCH-SKINS-001 Workstream A).
 *
 * Components today read `--platform-*` and `--soma-*` (often with hex fallbacks).
 * The applier writes `--skin-*` values AND the legacy names below so a skin
 * actually restyles the live UI before the mechanical rename lands.
 *
 * One-way: skin value → legacy alias. Deleted when alias-use count hits zero.
 */

export type AliasTable = ReadonlyArray<readonly [skinName: string, legacyName: string]>;

export const ALIAS_TABLE: AliasTable = [
  // Colour — base
  ['--skin-color-bg-void', '--platform-bg-void'],
  ['--skin-color-bg-void', '--soma-bg-void'],
  ['--skin-color-bg-base', '--platform-bg-base'],
  ['--skin-color-bg-base', '--platform-bg-page'],
  ['--skin-color-bg-base', '--soma-bg-page'],
  ['--skin-color-bg-base', '--soma-bg-base'],
  ['--skin-color-bg-card', '--platform-surface'],
  ['--skin-color-bg-card', '--platform-bg-card'],
  ['--skin-color-bg-card', '--soma-bg-card'],
  ['--skin-color-bg-card', '--soma-surface'],
  ['--skin-color-bg-sidebar', '--platform-bg-sidebar'],
  ['--skin-color-bg-sidebar', '--soma-bg-sidebar'],
  ['--skin-color-bg-hover', '--platform-surface-hover'],
  ['--skin-color-bg-hover', '--soma-bg-hover'],
  ['--skin-color-bg-active', '--soma-bg-active'],
  // Colour — text
  ['--skin-color-text-primary', '--platform-text-main'],
  ['--skin-color-text-primary', '--platform-text-primary'],
  ['--skin-color-text-primary', '--soma-text-primary'],
  ['--skin-color-text-primary', '--soma-text-main'],
  ['--skin-color-text-primary', '--soma-text'],
  ['--skin-color-text-secondary', '--platform-text-dim'],
  ['--skin-color-text-secondary', '--platform-text-secondary'],
  ['--skin-color-text-secondary', '--soma-text-secondary'],
  ['--skin-color-text-secondary', '--soma-text-dim'],
  ['--skin-color-text-muted', '--soma-text-muted'],
  ['--skin-color-text-muted', '--soma-text-dim'],
  ['--skin-color-text-inverse', '--soma-text-inverse'],
  ['--skin-color-text-link', '--soma-text-link'],
  // Colour — accent
  ['--skin-color-accent', '--platform-accent'],
  ['--skin-color-accent', '--soma-accent'],
  ['--skin-color-accent', '--soma-primary'],
  ['--skin-color-accent-hover', '--platform-accent-hover'],
  ['--skin-color-accent-hover', '--soma-accent-hover'],
  ['--skin-color-accent-hover', '--soma-primary-hover'],
  ['--skin-color-accent-text', '--soma-accent-text'],
  ['--skin-color-accent-text', '--soma-on-primary'],
  // Colour — semantic
  ['--skin-color-success', '--platform-success'],
  ['--skin-color-success', '--soma-success'],
  ['--skin-color-success', '--soma-status-success'],
  ['--skin-color-success-text', '--soma-success-text'],
  ['--skin-color-warning', '--platform-warning'],
  ['--skin-color-warning', '--soma-warning'],
  ['--skin-color-warning', '--soma-status-warning'],
  ['--skin-color-warning-text', '--soma-warning-text'],
  ['--skin-color-danger', '--platform-danger'],
  ['--skin-color-danger', '--soma-danger'],
  ['--skin-color-danger', '--soma-status-danger'],
  ['--skin-color-danger-text', '--soma-danger-text'],
  ['--skin-color-info', '--platform-info'],
  ['--skin-color-info', '--soma-info'],
  ['--skin-color-info', '--soma-status-info'],
  ['--skin-color-info-text', '--soma-info-text'],
  // Colour — border
  ['--skin-color-border', '--platform-border-color'],
  ['--skin-color-border', '--soma-border'],
  ['--skin-color-border', '--soma-border-light'],
  ['--skin-color-border-strong', '--platform-border-hover'],
  ['--skin-color-border-strong', '--soma-border-medium'],
  ['--skin-color-border-strong', '--soma-border-strong'],
  ['--skin-color-border-subtle', '--platform-glass-border'],
  ['--skin-color-border-subtle', '--soma-border-subtle'],
  // Type
  ['--skin-font-sans', '--platform-font-sans'],
  ['--skin-font-sans', '--soma-font-sans'],
  ['--skin-font-sans', '--soma-font'],
  ['--skin-font-mono', '--platform-font-mono'],
  ['--skin-font-mono', '--soma-font-mono'],
  ['--skin-text-xs', '--platform-text-xs'],
  ['--skin-text-xs', '--soma-text-xs'],
  ['--skin-text-sm', '--platform-text-sm'],
  ['--skin-text-sm', '--soma-text-sm'],
  ['--skin-text-base', '--platform-text-base'],
  ['--skin-text-base', '--soma-text-base'],
  ['--skin-text-lg', '--platform-text-lg'],
  ['--skin-text-lg', '--soma-text-lg'],
  ['--skin-text-xl', '--platform-text-xl'],
  ['--skin-text-xl', '--soma-text-xl'],
  ['--skin-text-2xl', '--platform-text-2xl'],
  ['--skin-text-2xl', '--soma-text-2xl'],
  // Spacing
  ['--skin-space-xs', '--platform-spacing-xs'],
  ['--skin-space-xs', '--platform-space-xs'],
  ['--skin-space-xs', '--soma-space-xs'],
  ['--skin-space-xs', '--soma-spacing-xs'],
  ['--skin-space-sm', '--platform-spacing-sm'],
  ['--skin-space-sm', '--platform-space-sm'],
  ['--skin-space-sm', '--soma-space-sm'],
  ['--skin-space-sm', '--soma-spacing-sm'],
  ['--skin-space-md', '--platform-spacing-md'],
  ['--skin-space-md', '--platform-space-md'],
  ['--skin-space-md', '--soma-space-md'],
  ['--skin-space-md', '--soma-spacing-md'],
  ['--skin-space-lg', '--platform-spacing-lg'],
  ['--skin-space-lg', '--platform-space-lg'],
  ['--skin-space-lg', '--soma-space-lg'],
  ['--skin-space-lg', '--soma-spacing-lg'],
  ['--skin-space-xl', '--platform-spacing-xl'],
  ['--skin-space-xl', '--platform-space-xl'],
  ['--skin-space-xl', '--soma-space-xl'],
  ['--skin-space-2xl', '--platform-spacing-2xl'],
  ['--skin-space-2xl', '--platform-space-2xl'],
  ['--skin-space-2xl', '--soma-space-2xl'],
  // Radius
  ['--skin-radius-sm', '--platform-radius-sm'],
  ['--skin-radius-sm', '--soma-radius-sm'],
  ['--skin-radius-md', '--platform-radius-md'],
  ['--skin-radius-md', '--soma-radius-md'],
  ['--skin-radius-lg', '--platform-radius-lg'],
  ['--skin-radius-lg', '--soma-radius-lg'],
  ['--skin-radius-xl', '--platform-radius-xl'],
  ['--skin-radius-xl', '--soma-radius-xl'],
  ['--skin-radius-full', '--platform-radius-full'],
  ['--skin-radius-full', '--soma-radius-full'],
  // Shadow
  ['--skin-shadow-sm', '--platform-shadow-sm'],
  ['--skin-shadow-sm', '--soma-shadow-sm'],
  ['--skin-shadow-md', '--platform-shadow-md'],
  ['--skin-shadow-md', '--soma-shadow-md'],
  ['--skin-shadow-lg', '--platform-shadow-lg'],
  ['--skin-shadow-lg', '--soma-shadow-lg'],
  ['--skin-shadow-overlay', '--platform-shadow-glow'],
  ['--skin-shadow-overlay', '--soma-shadow-overlay'],
  // Motion (platform uses transition shorthand — approximate with duration)
  ['--skin-motion-fast', '--platform-transition-fast'],
  ['--skin-motion-normal', '--platform-transition-normal'],
  ['--skin-motion-slow', '--platform-transition-slow'],
  ['--skin-motion-ease', '--soma-motion-ease'],
] as const;

/** Legacy names that must never be written (reserved / unsafe). */
export function aliasesFor(skinName: string): string[] {
  return ALIAS_TABLE.filter(([s]) => s === skinName).map(([, legacy]) => legacy);
}

export function expandTokenMap(tokens: Record<string, string>): Record<string, string> {
  const out: Record<string, string> = { ...tokens };
  for (const [skinName, legacyName] of ALIAS_TABLE) {
    const value = tokens[skinName];
    if (value !== undefined && out[legacyName] === undefined) {
      out[legacyName] = value;
    }
  }
  return out;
}
