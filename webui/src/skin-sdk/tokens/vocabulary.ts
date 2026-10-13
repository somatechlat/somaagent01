/**
 * AgentSkin SDK — closed token vocabulary (SOMA-UI-SKINS-001 §3.2).
 * Names are stable; values are skin data. Unknown names are rejected (X-2/X-3).
 */

export type TokenDomain =
  | 'color'
  | 'font-family'
  | 'length'
  | 'number'
  | 'time'
  | 'easing'
  | 'shadow';

export interface TokenSpec {
  readonly name: string;
  readonly domain: TokenDomain;
  readonly required: boolean;
}

/** Closed vocabulary. Additions require schema_version bump. */
export const TOKEN_SPECS: readonly TokenSpec[] = [
  // Colour — base
  { name: '--skin-color-bg-void', domain: 'color', required: true },
  { name: '--skin-color-bg-base', domain: 'color', required: true },
  { name: '--skin-color-bg-card', domain: 'color', required: true },
  { name: '--skin-color-bg-sidebar', domain: 'color', required: true },
  { name: '--skin-color-bg-hover', domain: 'color', required: true },
  { name: '--skin-color-bg-active', domain: 'color', required: true },
  // Colour — text
  { name: '--skin-color-text-primary', domain: 'color', required: true },
  { name: '--skin-color-text-secondary', domain: 'color', required: true },
  { name: '--skin-color-text-muted', domain: 'color', required: true },
  { name: '--skin-color-text-inverse', domain: 'color', required: true },
  { name: '--skin-color-text-link', domain: 'color', required: true },
  // Colour — accent
  { name: '--skin-color-accent', domain: 'color', required: true },
  { name: '--skin-color-accent-hover', domain: 'color', required: true },
  { name: '--skin-color-accent-text', domain: 'color', required: true },
  // Colour — semantic
  { name: '--skin-color-success', domain: 'color', required: true },
  { name: '--skin-color-success-text', domain: 'color', required: true },
  { name: '--skin-color-warning', domain: 'color', required: true },
  { name: '--skin-color-warning-text', domain: 'color', required: true },
  { name: '--skin-color-danger', domain: 'color', required: true },
  { name: '--skin-color-danger-text', domain: 'color', required: true },
  { name: '--skin-color-info', domain: 'color', required: true },
  { name: '--skin-color-info-text', domain: 'color', required: true },
  // Colour — border
  { name: '--skin-color-border', domain: 'color', required: true },
  { name: '--skin-color-border-strong', domain: 'color', required: true },
  { name: '--skin-color-border-subtle', domain: 'color', required: true },
  // Focus (OPEN-12 resolved — A11Y-3 needs a colourable ring)
  { name: '--skin-focus-ring', domain: 'color', required: true },
  { name: '--skin-focus-ring-width', domain: 'length', required: true },
  { name: '--skin-focus-ring-offset', domain: 'length', required: true },
  // Type — family
  { name: '--skin-font-sans', domain: 'font-family', required: true },
  { name: '--skin-font-mono', domain: 'font-family', required: true },
  // Type — scale
  { name: '--skin-text-xs', domain: 'length', required: true },
  { name: '--skin-text-sm', domain: 'length', required: true },
  { name: '--skin-text-base', domain: 'length', required: true },
  { name: '--skin-text-lg', domain: 'length', required: true },
  { name: '--skin-text-xl', domain: 'length', required: true },
  { name: '--skin-text-2xl', domain: 'length', required: true },
  // Type — weight
  { name: '--skin-weight-normal', domain: 'number', required: true },
  { name: '--skin-weight-medium', domain: 'number', required: true },
  { name: '--skin-weight-semibold', domain: 'number', required: true },
  { name: '--skin-weight-bold', domain: 'number', required: true },
  // Type — leading
  { name: '--skin-leading-tight', domain: 'number', required: true },
  { name: '--skin-leading-normal', domain: 'number', required: true },
  { name: '--skin-leading-relaxed', domain: 'number', required: true },
  // Spacing
  { name: '--skin-space-xs', domain: 'length', required: true },
  { name: '--skin-space-sm', domain: 'length', required: true },
  { name: '--skin-space-md', domain: 'length', required: true },
  { name: '--skin-space-lg', domain: 'length', required: true },
  { name: '--skin-space-xl', domain: 'length', required: true },
  { name: '--skin-space-2xl', domain: 'length', required: true },
  // Radius
  { name: '--skin-radius-sm', domain: 'length', required: true },
  { name: '--skin-radius-md', domain: 'length', required: true },
  { name: '--skin-radius-lg', domain: 'length', required: true },
  { name: '--skin-radius-xl', domain: 'length', required: true },
  { name: '--skin-radius-full', domain: 'length', required: true },
  // Elevation
  { name: '--skin-shadow-sm', domain: 'shadow', required: true },
  { name: '--skin-shadow-md', domain: 'shadow', required: true },
  { name: '--skin-shadow-lg', domain: 'shadow', required: true },
  { name: '--skin-shadow-overlay', domain: 'shadow', required: true },
  // Motion
  { name: '--skin-motion-fast', domain: 'time', required: true },
  { name: '--skin-motion-normal', domain: 'time', required: true },
  { name: '--skin-motion-slow', domain: 'time', required: true },
  { name: '--skin-motion-ease', domain: 'easing', required: true },
] as const;

export const TOKEN_NAMES: ReadonlySet<string> = new Set(
  TOKEN_SPECS.map((s) => s.name),
);

export const REQUIRED_TOKEN_NAMES: readonly string[] = TOKEN_SPECS.filter(
  (s) => s.required,
).map((s) => s.name);

export const TOKEN_NAME_RE = /^--skin-[a-z0-9-]+$/;

export function tokenDomain(name: string): TokenDomain | null {
  return TOKEN_SPECS.find((s) => s.name === name)?.domain ?? null;
}

export function isKnownToken(name: string): boolean {
  return TOKEN_NAMES.has(name);
}
