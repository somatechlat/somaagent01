/**
 * Density scale bindings (AgentSkin L0).
 *
 * Every value is a `var(--skin-*)` reference — no literal colours, lengths,
 * or hosts. Token names match SOMA-UI-SKINS-001 vocabulary / tokens.css
 * structural aliases.
 */

export const SPACE = {
  xs: 'var(--skin-space-xs)',
  sm: 'var(--skin-space-sm)',
  md: 'var(--skin-space-md)',
  lg: 'var(--skin-space-lg)',
  xl: 'var(--skin-space-xl)',
  '2xl': 'var(--skin-space-2xl)',
} as const;

export const RADIUS = {
  sm: 'var(--skin-radius-sm)',
  md: 'var(--skin-radius-md)',
  lg: 'var(--skin-radius-lg)',
  xl: 'var(--skin-radius-xl)',
  full: 'var(--skin-radius-full)',
} as const;

export const TYPE = {
  fontSans: 'var(--skin-font-sans)',
  fontMono: 'var(--skin-font-mono)',
  xs: 'var(--skin-text-xs)',
  sm: 'var(--skin-text-sm)',
  base: 'var(--skin-text-base)',
  lg: 'var(--skin-text-lg)',
  xl: 'var(--skin-text-xl)',
  xxl: 'var(--skin-text-2xl)',
  weightNormal: 'var(--skin-weight-normal)',
  weightMedium: 'var(--skin-weight-medium)',
  weightSemibold: 'var(--skin-weight-semibold)',
  weightBold: 'var(--skin-weight-bold)',
  leadingTight: 'var(--skin-leading-tight)',
  leadingNormal: 'var(--skin-leading-normal)',
  leadingRelaxed: 'var(--skin-leading-relaxed)',
} as const;

export const Z = {
  dropdown: 'var(--skin-z-dropdown)',
  modal: 'var(--skin-z-modal)',
  overlay: 'var(--skin-z-overlay)',
  toast: 'var(--skin-z-toast)',
  tooltip: 'var(--skin-z-tooltip)',
} as const;

export const MOTION = {
  fast: 'var(--skin-motion-fast)',
  normal: 'var(--skin-motion-normal)',
  slow: 'var(--skin-motion-slow)',
  ease: 'var(--skin-motion-ease)',
} as const;

export type SpaceToken = keyof typeof SPACE;
export type RadiusToken = keyof typeof RADIUS;
export type TypeToken = keyof typeof TYPE;
export type ZToken = keyof typeof Z;
export type MotionToken = keyof typeof MOTION;

/** Full density map — handy for spreads and serialisation. */
export const DENSITY = {
  SPACE,
  RADIUS,
  TYPE,
  Z,
  MOTION,
} as const;
