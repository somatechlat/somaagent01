/**
 * SkinApplier — runtime application of a resolved skin (SOMA-UI-SKINS-001 §6).
 *
 * Writes ONLY `--skin-*` custom property declarations via element.style.setProperty.
 * Never injects <style> text, never uses unsafeCSS, never writes selectors.
 * Shadow DOM custom properties inherit from the host — no re-render, no rebuild.
 */

import { HOST_ATTR, SURFACE_ATTR, type SurfaceKey } from '../skin-sdk/surfaces.js';
import type { ResolvedSkin } from '../skin-sdk/resolve.js';
import type { TokenMap } from '../skin-sdk/types.js';

type Listener = (resolved: ResolvedSkin | null) => void;

const listeners = new Set<Listener>();

let current: ResolvedSkin | null = null;
let previous: ResolvedSkin | null = null;

function writeTokens(el: HTMLElement, tokens: TokenMap): void {
  for (const [name, value] of Object.entries(tokens)) {
    if (!name.startsWith('--skin-')) continue;
    el.style.setProperty(name, value);
  }
}

function clearTokens(el: HTMLElement, tokens: TokenMap): void {
  for (const name of Object.keys(tokens)) {
    if (!name.startsWith('--skin-')) continue;
    el.style.removeProperty(name);
  }
}

function applyReducedMotion(tokens: TokenMap): TokenMap {
  if (
    typeof matchMedia === 'function' &&
    matchMedia('(prefers-reduced-motion: reduce)').matches
  ) {
    return {
      ...tokens,
      '--skin-motion-fast': '0ms',
      '--skin-motion-normal': '0ms',
      '--skin-motion-slow': '0ms',
    };
  }
  return tokens;
}

function surfaceHosts(root: ParentNode, surface: SurfaceKey): HTMLElement[] {
  return Array.from(
    root.querySelectorAll<HTMLElement>(`[${SURFACE_ATTR}="${surface}"]`),
  );
}

function agentHosts(root: ParentNode): HTMLElement[] {
  return Array.from(root.querySelectorAll<HTMLElement>(`[${HOST_ATTR}]`));
}

function applyToTree(resolved: ResolvedSkin, root: ParentNode = document): void {
  const core = applyReducedMotion(resolved.tokens);
  const docEl = document.documentElement;

  // Workspace / chrome host — full resolved map (prevents :root leak of agent maps).
  writeTokens(docEl, core);

  // Per-agent isolation hosts get their own full map (I-1…I-6).
  for (const host of agentHosts(root)) {
    writeTokens(host, core);
  }

  // Surface overrides — write only under [data-skin-surface="…"] (I-4).
  for (const [surface, map] of Object.entries(resolved.surfaces)) {
    if (!map) continue;
    const scoped = applyReducedMotion(map);
    for (const el of surfaceHosts(root, surface as SurfaceKey)) {
      writeTokens(el, scoped);
    }
  }
}

function notify(): void {
  for (const fn of listeners) fn(current);
}

export const SkinApplier = {
  /** Currently applied skin (null = platform tokens.css only). */
  get current(): ResolvedSkin | null {
    return current;
  },

  /**
   * Apply a resolved skin. Hot-swap: property writes only, zero Lit re-render.
   * Saves the prior map so revert() works (AC-10).
   */
  apply(resolved: ResolvedSkin, options?: { remember?: boolean }): void {
    if (options?.remember !== false && current) {
      previous = current;
    }
    current = resolved;
    applyToTree(resolved);
    notify();
  },

  /**
   * Preview without replacing the saved baseline (apply-without-save).
   * preview() then revert() restores the pre-preview map (AC-10).
   */
  preview(resolved: ResolvedSkin): void {
    if (!previous && current) previous = current;
    current = resolved;
    applyToTree(resolved);
    notify();
  },

  /** Restore the previously applied map. No reload. */
  revert(): boolean {
    if (!previous) return false;
    const prior = previous;
    previous = current;
    current = prior;
    applyToTree(prior);
    notify();
    return true;
  },

  /** Re-apply after polarity toggle without dropping the skin (§6.3). */
  reapply(): void {
    if (current) applyToTree(current);
  },

  /** Clear all applied skin properties (back to tokens.css defaults). */
  clear(): void {
    if (current) {
      clearTokens(document.documentElement, current.tokens);
      for (const host of agentHosts(document)) {
        clearTokens(host, current.tokens);
      }
      for (const [surface, map] of Object.entries(current.surfaces)) {
        if (!map) continue;
        for (const el of surfaceHosts(document, surface as SurfaceKey)) {
          clearTokens(el, map);
        }
      }
    }
    previous = current;
    current = null;
    notify();
  },

  onChange(fn: Listener): () => void {
    listeners.add(fn);
    return () => listeners.delete(fn);
  },
};

// Polarity interaction: re-apply skin when data-theme flips (§6.3).
if (typeof window !== 'undefined') {
  window.addEventListener('soma-theme-change', () => {
    SkinApplier.reapply();
  });
}
