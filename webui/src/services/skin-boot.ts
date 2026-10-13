/**
 * skin-boot — re-apply the active installable skin on every page load.
 *
 * SkinApplier.setProperty only lasts for the current document. A full
 * navigation (or reload) must restore the saved pack so the whole UI — chat,
 * sidebar, chrome, settings — comes back skinned. Standalone authority is the
 * install registry (localStorage); API sync is wired when the store is live.
 */

import {
  getActiveSkin,
  resolveSkin,
} from '../skin-sdk/index.js';
import { SkinApplier } from './skin-applier.js';

export function bootActiveSkin(): boolean {
  try {
    const pack = getActiveSkin();
    if (!pack) return false;
    const resolved = resolveSkin({ platform: pack.skin });
    // remember:false — this is the baseline, not a preview
    SkinApplier.apply(resolved, { remember: false });
    return true;
  } catch {
    // Fail visible is the applier's job on user action; boot must not blank the UI.
    return false;
  }
}

// Run at module load (imported from main.ts beside theme-boot).
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => bootActiveSkin(), {
      once: true,
    });
  } else {
    bootActiveSkin();
  }
}
