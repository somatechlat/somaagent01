/**
 * AgentSkin SDK — public surface.
 *
 * Installable skin packs for the Settings gallery.
 * Contract: SOMA-UI-SKINS-001 · Architecture: SOMA-ARCH-SKINS-001.
 */

export {
  TOKEN_SPECS,
  TOKEN_NAMES,
  REQUIRED_TOKEN_NAMES,
  TOKEN_NAME_RE,
  tokenDomain,
  isKnownToken,
  type TokenSpec,
  type TokenDomain,
} from './tokens/vocabulary.js';

export {
  SURFACE_KEYS,
  SURFACE_ATTR,
  HOST_ATTR,
  isSurfaceKey,
  type SurfaceKey,
} from './surfaces.js';

export {
  SKIN_SCHEMA_VERSION,
  type SkinDocument,
  type SkinMeta,
  type TokenMap,
  type SanitiseFinding,
  type SanitiseResult,
  type SanitiseRuleId,
} from './types.js';

export {
  SKIN_PACK_FORMAT,
  SKIN_PACK_FORMAT_VERSION,
  isSkinPackManifest,
  type SkinPackManifest,
  type InstalledSkinPack,
  type SkinPackSource,
  type SkinSwatch,
} from './pack.js';

export { sanitiseSkin, sanitiseTemplate } from './validate.js';

export {
  resolveSkin,
  effectiveToken,
  RESOLUTION_ORDER,
  type SkinSources,
  type SkinSourceLayer,
  type ResolvedSkin,
} from './resolve.js';

export {
  listInstalledSkins,
  installSkinPack,
  uninstallSkinPack,
  getInstalledSkin,
  getActiveSkin,
  setActiveSkin,
  clearActiveSkin,
  ensureBundledSkins,
  getBundledPack,
  type InstallResult,
} from './install.js';

export {
  BUNDLED_PACKS,
  listBundledPacks,
} from './templates/index.js';
