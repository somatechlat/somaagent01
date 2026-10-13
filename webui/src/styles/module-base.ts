/**
 * module-base — shared modular styles for every Soma UI module.
 * ALL values come from AgentSkin tokens (`--skin-*`). No literals.
 * Import with glassCard/density for a complete skin-aware surface.
 */

import { css, type CSSResult } from 'lit';

/** Form controls · buttons · chips · rows · status — one look everywhere. */
export const moduleBase: CSSResult = css`
    .mb-btn {
        box-sizing: border-box;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: var(--skin-space-xs);
        min-height: var(--skin-space-xl);
        padding: var(--skin-space-sm) var(--skin-space-md);
        border-radius: var(--skin-radius-md);
        border: var(--skin-border-width) solid var(--skin-color-border);
        background: var(--skin-color-bg-base);
        color: var(--skin-color-text-primary);
        font-family: var(--skin-font-sans);
        font-size: var(--skin-text-sm);
        font-weight: var(--skin-weight-medium);
        line-height: var(--skin-leading-normal);
        cursor: pointer;
        transition:
            background var(--skin-motion-fast) var(--skin-motion-ease),
            border-color var(--skin-motion-fast) var(--skin-motion-ease);
    }

    .mb-btn:hover:not(:disabled) {
        background: var(--skin-color-bg-hover);
        border-color: var(--skin-color-border-strong);
    }

    .mb-btn:focus-visible {
        outline: var(--skin-focus-ring-width) solid var(--skin-focus-ring);
        outline-offset: var(--skin-focus-ring-offset);
    }

    .mb-btn:disabled {
        opacity: 0.55;
        cursor: not-allowed;
    }

    .mb-btn.primary {
        background: var(--skin-color-accent);
        border-color: transparent;
        color: var(--skin-color-accent-text);
    }

    .mb-btn.primary:hover:not(:disabled) {
        background: var(--skin-color-accent-hover);
    }

    .mb-btn.danger {
        color: var(--skin-color-danger);
        border-color: var(--skin-color-danger);
    }

    .mb-btn.ghost {
        border-color: transparent;
        background: transparent;
    }

    .mb-input {
        box-sizing: border-box;
        width: 100%;
        min-height: var(--skin-space-xl);
        padding: var(--skin-space-sm) var(--skin-space-md);
        border-radius: var(--skin-radius-md);
        border: var(--skin-border-width) solid var(--skin-color-border);
        background: var(--skin-color-bg-base);
        color: var(--skin-color-text-primary);
        font-family: var(--skin-font-sans);
        font-size: var(--skin-text-sm);
    }

    .mb-input:focus-visible {
        outline: var(--skin-focus-ring-width) solid var(--skin-focus-ring);
        outline-offset: var(--skin-focus-ring-offset);
    }

    .mb-label {
        display: block;
        margin: var(--skin-space-sm) 0 var(--skin-space-xs);
        font-family: var(--skin-font-sans);
        font-size: var(--skin-text-xs);
        font-weight: var(--skin-weight-medium);
        color: var(--skin-color-text-secondary);
    }

    .mb-hint {
        margin-top: var(--skin-space-xs);
        font-family: var(--skin-font-sans);
        font-size: var(--skin-text-xs);
        color: var(--skin-color-text-muted);
    }

    .mb-chip {
        display: inline-flex;
        align-items: center;
        gap: var(--skin-space-xs);
        padding: var(--skin-space-xs) var(--skin-space-sm);
        border-radius: var(--skin-radius-full);
        background: var(--skin-color-bg-hover);
        color: var(--skin-color-text-secondary);
        font-family: var(--skin-font-sans);
        font-size: var(--skin-text-xs);
    }

    .mb-row {
        display: flex;
        align-items: center;
        gap: var(--skin-space-sm);
        padding: var(--skin-space-sm) var(--skin-space-md);
        border: var(--skin-border-width) solid var(--skin-color-border);
        border-radius: var(--skin-radius-md);
        background: var(--skin-color-bg-base);
        color: var(--skin-color-text-primary);
        font-family: var(--skin-font-sans);
        font-size: var(--skin-text-sm);
    }

    .mb-status {
        padding: var(--skin-space-sm) var(--skin-space-md);
        border-radius: var(--skin-radius-md);
        background: var(--skin-color-bg-hover);
        color: var(--skin-color-text-secondary);
        font-family: var(--skin-font-sans);
        font-size: var(--skin-text-sm);
    }

    .mb-status.ok {
        color: var(--skin-color-success-text);
        background: color-mix(in srgb, var(--skin-color-success) 14%, transparent);
    }

    .mb-status.error {
        color: var(--skin-color-danger-text);
        background: color-mix(in srgb, var(--skin-color-danger) 14%, transparent);
    }

    .mb-status.warn {
        color: var(--skin-color-warning-text);
        background: color-mix(in srgb, var(--skin-color-warning) 16%, transparent);
    }

    .mb-title {
        margin: 0;
        font-family: var(--skin-font-sans);
        font-size: var(--skin-text-base);
        font-weight: var(--skin-weight-semibold);
        color: var(--skin-color-text-primary);
    }

    .mb-body {
        margin: var(--skin-space-xs) 0 var(--skin-space-md);
        font-family: var(--skin-font-sans);
        font-size: var(--skin-text-sm);
        color: var(--skin-color-text-secondary);
        line-height: var(--skin-leading-normal);
    }
`;
