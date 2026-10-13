/**
 * AgentSkin SDK — sanitiser (SOMA-UI-SKINS-001 §8.2 X-1…X-12) + a11y floor.
 * A rejected skin is rejected whole. Findings carry rule ids; never swallowed.
 */

import {
  REQUIRED_TOKEN_NAMES,
  TOKEN_NAME_RE,
  isKnownToken,
  tokenDomain,
  type TokenDomain,
} from './tokens/vocabulary.js';
import { SURFACE_KEYS, isSurfaceKey } from './surfaces.js';
import {
  SKIN_SCHEMA_VERSION,
  type SanitiseFinding,
  type SanitiseResult,
  type SkinDocument,
  type TokenMap,
} from './types.js';

// --- size limits (X-8) ---
const MAX_DOC_BYTES = 32 * 1024;
const MAX_CORE_TOKENS = 128;
const MAX_SURFACES = 8;
const MAX_SURFACE_TOKENS = 64;
const MAX_VALUE_CHARS = 256;
const MAX_CHANGELOG = 50;

// --- denied constructs (X-5/X-6), case-insensitive after unescape ---
const DENIED_SUBSTRINGS = [
  'expression(',
  'javascript:',
  'vbscript:',
  '@import',
  'behavior',
  '-moz-binding',
  '<script',
  '</script',
  'url(',
  'image-set(',
  'attr(',
  'element(',
  '@font-face',
  '@namespace',
  'progid:',
  '://',
  'data:',
  'blob:',
  '`',
];

const COLOR_RE =
  /^(#([0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})|rgba?\(\s*[\d.%\s,/]+\)|hsla?\(\s*[\d.%\s,/deg]+\)|transparent|currentColor|[a-z]+)$/i;
const LENGTH_RE = /^-?\d*\.?\d+(px|rem|em|ch|vh|vw|vmin|vmax|%)$/i;
const NUMBER_RE = /^\d*\.?\d+$/;
const TIME_RE = /^\d*\.?\d+(ms|s)$/i;
const EASING_RE =
  /^(cubic-bezier\(\s*-?\d*\.?\d+\s*,\s*-?\d*\.?\d+\s*,\s*-?\d*\.?\d+\s*,\s*-?\d*\.?\d+\s*\)|linear|ease|ease-in|ease-out|ease-in-out|step-start|step-end)$/i;
const FONT_FAMILY_RE =
  /^[\w\s'",-]+(\s*,\s*[\w\s'",-]+)*$/i;
// One shadow layer: optional inset, 2–4 lengths, one colour.
const SHADOW_LENGTH_RE = /^(-?\d*\.?\d+(px|rem)|0)$/i;
const SHADOW_COLOR_RE =
  /^(#[0-9a-f]{3,8}|rgba?\([^)]*\)|hsla?\([^)]*\)|transparent|currentColor|[a-z]+)$/i;

function splitCssTokens(value: string): string[] {
  // Split on whitespace but keep rgba(0, 0, 0, 0.1) / hsla(...) as one token.
  const tokens: string[] = [];
  let depth = 0;
  let current = '';
  for (const ch of value) {
    if (ch === '(') depth += 1;
    else if (ch === ')') depth -= 1;
    if (/\s/.test(ch) && depth === 0) {
      if (current) tokens.push(current);
      current = '';
    } else {
      current += ch;
    }
  }
  if (current) tokens.push(current);
  return tokens;
}

function validShadowLayer(layer: string): boolean {
  const tokens = splitCssTokens(layer.trim());
  if (tokens.length < 3) return false;
  let lengths = 0;
  let colors = 0;
  let inset = 0;
  for (const t of tokens) {
    if (t === 'inset') {
      inset += 1;
    } else if (SHADOW_LENGTH_RE.test(t)) {
      lengths += 1;
    } else if (SHADOW_COLOR_RE.test(t)) {
      colors += 1;
    } else {
      return false;
    }
  }
  return inset <= 1 && lengths >= 2 && lengths <= 4 && colors === 1;
}

function validShadow(value: string): boolean {
  // comma-separated layers — but rgba(0, 0, 0, 0.1) also has commas, so split
  // only on commas that are not inside parentheses.
  const layers: string[] = [];
  let depth = 0;
  let currentLayer = '';
  for (const ch of value) {
    if (ch === '(') depth += 1;
    else if (ch === ')') depth -= 1;
    if (ch === ',' && depth === 0) {
      layers.push(currentLayer);
      currentLayer = '';
    } else {
      currentLayer += ch;
    }
  }
  layers.push(currentLayer);
  return layers.length > 0 && layers.every((l) => validShadowLayer(l));
}

function unescapeCss(value: string): string {
  return value
    .replace(/\\([0-9a-fA-F]{1,6}\s?)/g, '')
    .replace(/\\(.)/g, '$1');
}

function containsDenied(value: string): string | null {
  const flat = unescapeCss(value).toLowerCase().replace(/\s+/g, '');
  for (const denied of DENIED_SUBSTRINGS) {
    if (flat.includes(denied.toLowerCase().replace(/\s+/g, ''))) {
      return denied;
    }
  }
  // bare ';' outside a single declaration is injection (X-5)
  if (value.includes(';')) return ';';
  return null;
}

function validDomainValue(domain: TokenDomain, value: string): boolean {
  const v = value.trim();
  if (!v || v.length > MAX_VALUE_CHARS) return false;
  switch (domain) {
    case 'color':
      return COLOR_RE.test(v);
    case 'length':
      return LENGTH_RE.test(v);
    case 'number':
      return NUMBER_RE.test(v);
    case 'time':
      return TIME_RE.test(v);
    case 'easing':
      return EASING_RE.test(v);
    case 'font-family':
      return FONT_FAMILY_RE.test(v) && !v.includes('(');
    case 'shadow':
      // lengths + one colour per layer; no url() (X-9)
      return validShadow(v);
    default:
      return false;
  }
}

// --- minimal sRGB relative luminance / contrast (A11Y-1/2/5) ---

function parseColor(value: string): [number, number, number] | null {
  const v = value.trim().toLowerCase();
  const hex = v.match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/);
  if (hex) {
    let h = hex[1];
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    return [
      parseInt(h.slice(0, 2), 16),
      parseInt(h.slice(2, 4), 16),
      parseInt(h.slice(4, 6), 16),
    ];
  }
  const rgb = v.match(/^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/);
  if (rgb) return [Number(rgb[1]), Number(rgb[2]), Number(rgb[3])];
  const named: Record<string, [number, number, number]> = {
    white: [255, 255, 255],
    black: [0, 0, 0],
    transparent: [255, 255, 255],
  };
  return named[v] ?? null;
}

function luminance(rgb: [number, number, number]): number {
  const [r, g, b] = rgb.map((c) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  }) as [number, number, number];
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrastRatio(a: string, b: string): number | null {
  const ca = parseColor(a);
  const cb = parseColor(b);
  if (!ca || !cb) return null;
  const la = luminance(ca);
  const lb = luminance(cb);
  const lighter = Math.max(la, lb);
  const darker = Math.min(la, lb);
  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Contrast pairs (A11Y-1 body text ≥4.5, A11Y-2 UI/badge ≥3).
 * Semantic -text companions are badge/UI labels → 3:1 floor.
 */
const TEXT_PAIRS: readonly [string, string, number][] = [
  ['--skin-color-text-primary', '--skin-color-bg-base', 4.5],
  ['--skin-color-text-primary', '--skin-color-bg-card', 4.5],
  ['--skin-color-text-secondary', '--skin-color-bg-base', 4.5],
  ['--skin-color-text-muted', '--skin-color-bg-base', 4.5],
  ['--skin-color-text-link', '--skin-color-bg-base', 4.5],
  ['--skin-color-accent-text', '--skin-color-accent', 4.5],
  ['--skin-color-success-text', '--skin-color-success', 3],
  ['--skin-color-warning-text', '--skin-color-warning', 3],
  ['--skin-color-danger-text', '--skin-color-danger', 3],
  ['--skin-color-info-text', '--skin-color-info', 3],
  ['--skin-focus-ring', '--skin-color-bg-base', 3],
  ['--skin-focus-ring', '--skin-color-bg-void', 3],
];

function checkContrast(tokens: TokenMap, findings: SanitiseFinding[]): void {
  for (const [fg, bg, min] of TEXT_PAIRS) {
    const a = tokens[fg];
    const b = tokens[bg];
    if (!a || !b) continue;
    const ratio = contrastRatio(a, b);
    if (ratio === null) continue;
    if (ratio < min) {
      findings.push({
        rule: min >= 4.5 ? 'A11Y-1' : 'A11Y-2',
        token: fg,
        message: `contrast(${fg}, ${bg}) = ${ratio.toFixed(2)} < ${min}`,
      });
    }
  }
}

function sanitiseTokenMap(
  map: TokenMap,
  label: string,
  maxTokens: number,
  findings: SanitiseFinding[],
): void {
  const names = Object.keys(map);
  if (names.length > maxTokens) {
    findings.push({
      rule: 'X-8',
      message: `${label}: ${names.length} tokens > ${maxTokens}`,
    });
  }
  for (const name of names) {
    if (!TOKEN_NAME_RE.test(name) || !isKnownToken(name)) {
      findings.push({
        rule: 'X-3',
        token: name,
        message: `${label}: unknown token name`,
      });
      continue;
    }
    const value = map[name];
    if (typeof value !== 'string') {
      findings.push({
        rule: 'X-4',
        token: name,
        message: `${label}: value must be string`,
      });
      continue;
    }
    if (value.length > MAX_VALUE_CHARS) {
      findings.push({
        rule: 'X-8',
        token: name,
        message: `${label}: value length ${value.length} > ${MAX_VALUE_CHARS}`,
      });
      continue;
    }
    const denied = containsDenied(value);
    if (denied !== null) {
      findings.push({
        rule: denied === ';' ? 'X-5' : 'X-6',
        token: name,
        message: `${label}: denied construct ${denied}`,
      });
      continue;
    }
    // X-7: ban var() in values entirely (OPEN-08 recommended)
    if (/var\s*\(/i.test(value)) {
      findings.push({
        rule: 'X-7',
        token: name,
        message: `${label}: var() not allowed in skin values`,
      });
      continue;
    }
    const domain = tokenDomain(name);
    if (!domain || !validDomainValue(domain, value)) {
      findings.push({
        rule: 'X-4',
        token: name,
        message: `${label}: value not parseable as ${domain ?? 'unknown'}`,
      });
    }
  }
}

function topKeysOf(doc: unknown): string[] {
  return doc && typeof doc === 'object' ? Object.keys(doc as object) : [];
}

const ALLOWED_TOP_KEYS = new Set([
  'schema_version',
  'name',
  'description',
  'template',
  'tokens',
  'surfaces',
  'meta',
]);

/**
 * Full sanitiser. Rejects whole on any finding (X-11).
 * Server-side on write and client-side on apply both call this.
 */
export function sanitiseSkin(input: unknown): SanitiseResult {
  const findings: SanitiseFinding[] = [];

  if (!input || typeof input !== 'object' || Array.isArray(input)) {
    return {
      ok: false,
      findings: [{ rule: 'X-2', message: 'skin must be an object' }],
    };
  }

  // X-8 size on the raw document
  let rawBytes = 0;
  try {
    rawBytes = new TextEncoder().encode(JSON.stringify(input)).length;
  } catch {
    return {
      ok: false,
      findings: [{ rule: 'X-8', message: 'document not serialisable' }],
    };
  }
  if (rawBytes > MAX_DOC_BYTES) {
    return {
      ok: false,
      findings: [
        { rule: 'X-8', message: `document ${rawBytes} bytes > ${MAX_DOC_BYTES}` },
      ],
    };
  }

  const doc = input as Record<string, unknown>;

  // X-2 unknown top-level keys
  for (const key of topKeysOf(doc)) {
    if (!ALLOWED_TOP_KEYS.has(key)) {
      findings.push({ rule: 'X-2', message: `unknown top-level key ${key}` });
    }
  }

  // X-1 schema_version
  if (doc.schema_version !== SKIN_SCHEMA_VERSION) {
    findings.push({
      rule: 'X-1',
      message: `schema_version must be "${SKIN_SCHEMA_VERSION}"`,
    });
  }

  // name
  const name = doc.name;
  if (typeof name !== 'string' || name.length < 1 || name.length > 50) {
    findings.push({ rule: 'X-2', message: 'name must be 1–50 chars' });
  }

  if (doc.description !== undefined) {
    const d = doc.description;
    if (typeof d !== 'string' || d.length > 200) {
      findings.push({ rule: 'X-2', message: 'description must be ≤200 chars' });
    }
  }

  // tokens required + complete for templates (T-2 checked on templates separately)
  if (!doc.tokens || typeof doc.tokens !== 'object' || Array.isArray(doc.tokens)) {
    findings.push({ rule: 'X-2', message: 'tokens must be an object' });
  } else {
    sanitiseTokenMap(
      doc.tokens as TokenMap,
      'tokens',
      MAX_CORE_TOKENS,
      findings,
    );
    for (const req of REQUIRED_TOKEN_NAMES) {
      if (!(req in (doc.tokens as TokenMap))) {
        findings.push({
          rule: 'T-2',
          token: req,
          message: 'required core token missing',
        });
      }
    }
  }

  // surfaces
  if (doc.surfaces !== undefined) {
    const surfaces = doc.surfaces;
    if (!surfaces || typeof surfaces !== 'object' || Array.isArray(surfaces)) {
      findings.push({ rule: 'X-2', message: 'surfaces must be an object' });
    } else {
      const keys = Object.keys(surfaces as object);
      if (keys.length > MAX_SURFACES) {
        findings.push({
          rule: 'X-8',
          message: `surfaces ${keys.length} > ${MAX_SURFACES}`,
        });
      }
      for (const key of keys) {
        if (!isSurfaceKey(key)) {
          findings.push({
            rule: 'X-2',
            message: `unknown surface key ${key}`,
          });
          continue;
        }
        const map = (surfaces as Record<string, unknown>)[key];
        if (!map || typeof map !== 'object' || Array.isArray(map)) {
          findings.push({
            rule: 'X-2',
            message: `surfaces.${key} must be an object`,
          });
          continue;
        }
        sanitiseTokenMap(
          map as TokenMap,
          `surfaces.${key}`,
          MAX_SURFACE_TOKENS,
          findings,
        );
      }
    }
  }

  // meta
  if (doc.meta !== undefined && doc.meta !== null) {
    const meta = doc.meta as Record<string, unknown>;
    if (typeof meta !== 'object' || Array.isArray(meta)) {
      findings.push({ rule: 'X-2', message: 'meta must be an object' });
    } else if (Array.isArray(meta.changelog) && meta.changelog.length > MAX_CHANGELOG) {
      findings.push({
        rule: 'X-8',
        message: `meta.changelog ${meta.changelog.length} > ${MAX_CHANGELOG}`,
      });
    }
  }

  // A11Y contrast on the effective core map (surface maps inherit then override;
  // v1 checks the core map — surface pairs land in implementation fixtures).
  if (doc.tokens && typeof doc.tokens === 'object') {
    checkContrast(doc.tokens as TokenMap, findings);
  }

  if (findings.length > 0) {
    return { ok: false, findings };
  }

  return { ok: true, document: input as SkinDocument };
}

/** Template contract T-1…T-6 (SKINS-001 §5.3). */
export function sanitiseTemplate(input: unknown): SanitiseResult {
  const result = sanitiseSkin(input);
  if (!result.ok) return result;
  const doc = result.document;
  if (doc.surfaces && Object.keys(doc.surfaces).length > 0) {
    return {
      ok: false,
      findings: [
        { rule: 'T-2', message: 'templates must not contain surfaces overrides' },
      ],
    };
  }
  return result;
}
