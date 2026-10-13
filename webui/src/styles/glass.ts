/**
 * Glass surface primitives (SOMA-UI-MODULE-CATALOG-001 M-005 / M-012).
 *
 * Values bind only to `--skin-*` custom properties (AgentSkin vocabulary +
 * structural glass/z aliases declared in tokens.css). No literal colours,
 * lengths, or hosts.
 */

import { css, type CSSResult } from 'lit';

/** Elevated translucent surface — cards, panels, stat tiles. */
export const glassCard: CSSResult = css`
  .glass-card {
    box-sizing: border-box;
    background: var(--skin-glass-bg);
    border: var(--skin-border-width) solid var(--skin-color-border);
    border-radius: var(--skin-radius-lg);
    box-shadow: var(--skin-shadow-md);
    padding: var(--skin-space-md);
    color: var(--skin-color-text-primary);
    font-family: var(--skin-font-sans);
    font-size: var(--skin-text-base);
    line-height: var(--skin-leading-normal);
    backdrop-filter: var(--skin-glass-backdrop);
    -webkit-backdrop-filter: var(--skin-glass-backdrop);
    transition:
      background var(--skin-motion-fast) var(--skin-motion-ease),
      border-color var(--skin-motion-fast) var(--skin-motion-ease),
      box-shadow var(--skin-motion-fast) var(--skin-motion-ease);
  }

  .glass-card:hover {
    border-color: var(--skin-color-border-strong);
    box-shadow: var(--skin-shadow-lg);
  }

  .glass-card[data-selected],
  .glass-card.is-selected {
    background: var(--skin-color-bg-active);
    border-color: var(--skin-color-border-strong);
    box-shadow: var(--skin-shadow-lg);
  }
`;

/** Focused dialog shell — elevated glass panel on the modal stack. */
export const glassModal: CSSResult = css`
  .glass-modal {
    box-sizing: border-box;
    background: var(--skin-glass-bg);
    border: var(--skin-border-width) solid var(--skin-glass-border);
    border-radius: var(--skin-radius-xl);
    box-shadow: var(--skin-shadow-overlay);
    z-index: var(--skin-z-modal);
    padding: var(--skin-space-lg);
    color: var(--skin-color-text-primary);
    font-family: var(--skin-font-sans);
    font-size: var(--skin-text-base);
    line-height: var(--skin-leading-normal);
    backdrop-filter: var(--skin-glass-backdrop);
    -webkit-backdrop-filter: var(--skin-glass-backdrop);
    transition:
      background var(--skin-motion-normal) var(--skin-motion-ease),
      border-color var(--skin-motion-normal) var(--skin-motion-ease),
      box-shadow var(--skin-motion-normal) var(--skin-motion-ease);
  }
`;

/** Dense interactive row — lists, table body, nav items. */
export const glassRow: CSSResult = css`
  .glass-row {
    box-sizing: border-box;
    display: flex;
    align-items: center;
    gap: var(--skin-space-sm);
    padding: var(--skin-space-sm) var(--skin-space-md);
    border: var(--skin-border-width) solid transparent;
    border-radius: var(--skin-radius-md);
    background: transparent;
    color: var(--skin-color-text-primary);
    font-family: var(--skin-font-sans);
    font-size: var(--skin-text-sm);
    line-height: var(--skin-leading-normal);
    transition:
      background var(--skin-motion-fast) var(--skin-motion-ease),
      border-color var(--skin-motion-fast) var(--skin-motion-ease);
  }

  .glass-row:hover {
    background: var(--skin-color-bg-hover);
    border-color: var(--skin-color-border);
  }

  .glass-row[data-active],
  .glass-row.is-active {
    background: var(--skin-color-bg-active);
    border-color: var(--skin-color-border-strong);
    color: var(--skin-color-text-primary);
    font-weight: var(--skin-weight-medium);
  }
`;

/** Compact pill — status, counts, model/confidence chips. */
export const glassChip: CSSResult = css`
  .glass-chip {
    box-sizing: border-box;
    display: inline-flex;
    align-items: center;
    gap: var(--skin-space-xs);
    padding: var(--skin-space-xs) var(--skin-space-sm);
    border: var(--skin-border-width) solid var(--skin-color-border);
    border-radius: var(--skin-radius-full);
    background: var(--skin-glass-bg);
    color: var(--skin-color-text-secondary);
    font-family: var(--skin-font-sans);
    font-size: var(--skin-text-xs);
    font-weight: var(--skin-weight-medium);
    line-height: var(--skin-leading-tight);
    white-space: nowrap;
    transition:
      background var(--skin-motion-fast) var(--skin-motion-ease),
      border-color var(--skin-motion-fast) var(--skin-motion-ease),
      color var(--skin-motion-fast) var(--skin-motion-ease);
  }

  .glass-chip:hover {
    border-color: var(--skin-color-border-strong);
    color: var(--skin-color-text-primary);
  }

  .glass-chip[data-accent],
  .glass-chip.is-accent {
    border-color: var(--skin-color-accent);
    background: var(--skin-color-accent);
    color: var(--skin-color-accent-text);
  }
`;

/** All four glass primitives in one stylesheet. */
export const glassStyles: CSSResult = css`
  ${glassCard}
  ${glassModal}
  ${glassRow}
  ${glassChip}
`;
