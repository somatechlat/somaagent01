/**
 * AgentSkin SDK tests — sanitiser, resolution, install lifecycle.
 * Run: bun test src/skin-sdk/skin-sdk.test.ts
 */

import { describe, expect, test } from 'bun:test';
import { sanitiseSkin, sanitiseTemplate } from './validate.js';
import { resolveSkin } from './resolve.js';
import { BUNDLED_PACKS } from './templates/index.js';
import { isSkinPackManifest } from './pack.js';
import { REQUIRED_TOKEN_NAMES } from './tokens/vocabulary.js';
import { SURFACE_KEYS } from './surfaces.js';
import { expandTokenMap } from './aliases.js';
import type { SkinDocument } from './types.js';

function fullTokens(overrides: Record<string, string> = {}): Record<string, string> {
  const base: Record<string, string> = {};
  for (const name of REQUIRED_TOKEN_NAMES) {
    if (name.includes('color') || name === '--skin-focus-ring') {
      base[name] = '#1a1a1a';
    } else if (name.includes('space') || name.includes('radius') || name.includes('text-') || name.includes('ring-')) {
      base[name] = '8px';
    } else if (name.includes('weight') || name.includes('leading')) {
      base[name] = name.includes('weight') ? '400' : '1.5';
    } else if (name.includes('motion-fast') || name.includes('motion-normal') || name.includes('motion-slow')) {
      base[name] = '200ms';
    } else if (name.includes('motion-ease')) {
      base[name] = 'linear';
    } else if (name.includes('shadow')) {
      base[name] = '0 1px 2px rgba(0, 0, 0, 0.1)';
    } else if (name.includes('font')) {
      base[name] = 'system-ui, sans-serif';
    } else {
      base[name] = '8px';
    }
  }
  // AA-safe contrast pairs
  base['--skin-color-bg-void'] = '#f5f5f5';
  base['--skin-color-bg-base'] = '#ffffff';
  base['--skin-color-bg-card'] = '#ffffff';
  base['--skin-color-text-primary'] = '#1a1a1a';
  base['--skin-color-text-secondary'] = '#666666';
  base['--skin-color-text-muted'] = '#666666';
  base['--skin-color-text-inverse'] = '#ffffff';
  base['--skin-color-text-link'] = '#1a1a1a';
  base['--skin-color-accent'] = '#1a1a1a';
  base['--skin-color-accent-hover'] = '#333333';
  base['--skin-color-accent-text'] = '#ffffff';
  base['--skin-color-success'] = '#22c55e';
  base['--skin-color-success-text'] = '#052e16';
  base['--skin-color-warning'] = '#eab308';
  base['--skin-color-warning-text'] = '#422006';
  base['--skin-color-danger'] = '#ef4444';
  base['--skin-color-danger-text'] = '#ffffff';
  base['--skin-color-info'] = '#3b82f6';
  base['--skin-color-info-text'] = '#ffffff';
  base['--skin-color-border'] = 'rgba(0, 0, 0, 0.08)';
  base['--skin-color-border-strong'] = 'rgba(0, 0, 0, 0.14)';
  base['--skin-color-border-subtle'] = 'rgba(0, 0, 0, 0.05)';
  base['--skin-focus-ring'] = '#1a1a1a';
  return { ...base, ...overrides };
}

function doc(overrides: Partial<SkinDocument> = {}): unknown {
  return {
    schema_version: '1',
    name: 'test-skin',
    tokens: fullTokens(),
    ...overrides,
  };
}

describe('sanitiseSkin', () => {
  test('accepts a complete valid document', () => {
    const result = sanitiseSkin(doc());
    expect(result.ok).toBe(true);
  });

  test('rejects wrong schema_version (X-1)', () => {
    const result = sanitiseSkin(doc({ schema_version: '2' }));
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.findings.some((f) => f.rule === 'X-1')).toBe(true);
    }
  });

  test('rejects unknown top-level keys (X-2)', () => {
    const result = sanitiseSkin({ ...doc(), evil: true });
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.findings.some((f) => f.rule === 'X-2')).toBe(true);
    }
  });

  test('rejects unknown token names (X-3)', () => {
    const result = sanitiseSkin(
      doc({ tokens: fullTokens({ '--skin-color-evil': 'red' }) }),
    );
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.findings.some((f) => f.rule === 'X-3')).toBe(true);
    }
  });

  test('rejects url() (X-6) — no network I/O', () => {
    const result = sanitiseSkin(
      doc({
        tokens: fullTokens({
          '--skin-color-bg-void': 'url(https://evil.example/x)',
        }),
      }),
    );
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.findings.some((f) => f.rule === 'X-6' || f.rule === 'X-5')).toBe(true);
    }
  });

  test('rejects expression() (X-5) — no script', () => {
    const result = sanitiseSkin(
      doc({
        tokens: fullTokens({
          '--skin-color-bg-void': 'expression(alert(1))',
        }),
      }),
    );
    expect(result.ok).toBe(false);
  });

  test('rejects var() in values (X-7)', () => {
    const result = sanitiseSkin(
      doc({
        tokens: fullTokens({
          '--skin-color-bg-void': 'var(--skin-color-bg-base)',
        }),
      }),
    );
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.findings.some((f) => f.rule === 'X-7')).toBe(true);
    }
  });

  test('rejects missing required tokens (T-2)', () => {
    const tokens = fullTokens();
    delete tokens['--skin-color-accent'];
    const result = sanitiseSkin(doc({ tokens }));
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.findings.some((f) => f.rule === 'T-2')).toBe(true);
    }
  });

  test('rejects unknown surface keys (X-2)', () => {
    const result = sanitiseSkin(
      doc({
        surfaces: { nope: { '--skin-color-accent': '#ff0000' } },
      } as Partial<SkinDocument>),
    );
    expect(result.ok).toBe(false);
  });

  test('rejects low-contrast text pair (A11Y-1)', () => {
    const result = sanitiseSkin(
      doc({
        tokens: fullTokens({
          '--skin-color-text-primary': '#777777',
          '--skin-color-bg-base': '#777777',
        }),
      }),
    );
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.findings.some((f) => f.rule === 'A11Y-1' || f.rule === 'A11Y-2')).toBe(true);
    }
  });

  test('rejects semicolon injection (X-5)', () => {
    const result = sanitiseSkin(
      doc({
        tokens: fullTokens({
          '--skin-color-bg-void': '#fff; background: url(//evil)',
        }),
      }),
    );
    expect(result.ok).toBe(false);
  });
});

describe('bundled installable packs', () => {
  test('ships at least 6 packs', () => {
    expect(BUNDLED_PACKS.length).toBeGreaterThanOrEqual(6);
  });

  test('every bundled pack is a valid pack manifest', () => {
    for (const pack of BUNDLED_PACKS) {
      expect(isSkinPackManifest(pack)).toBe(true);
    }
  });

  test('every bundled pack sanitises clean', () => {
    for (const pack of BUNDLED_PACKS) {
      const result = sanitiseSkin(pack.skin);
      if (!result.ok) {
        throw new Error(
          `${pack.pack_id} failed: ${JSON.stringify(result.findings)}`,
        );
      }
      expect(result.ok).toBe(true);
    }
  });

  test('every bundled pack uses only known surface keys', () => {
    for (const pack of BUNDLED_PACKS) {
      const surfaces = pack.skin.surfaces ?? {};
      for (const key of Object.keys(surfaces)) {
        expect(SURFACE_KEYS as readonly string[]).toContain(key);
      }
    }
  });
});

describe('sanitiseTemplate', () => {
  test('rejects templates with surfaces (T-5)', () => {
    const result = sanitiseTemplate(
      doc({
        surfaces: {
          chat: { '--skin-color-accent': '#1a1a1a' },
        },
      } as Partial<SkinDocument>),
    );
    expect(result.ok).toBe(false);
  });
});

describe('resolveSkin', () => {
  test('capsule wins over lower layers per token', () => {
    const platform = doc({ name: 'platform' }) as SkinDocument;
    const capsule = doc({
      name: 'capsule',
      tokens: fullTokens({ '--skin-color-accent': '#ff0000' }),
    }) as SkinDocument;

    const resolved = resolveSkin({
      capsule,
      agent_setting: doc({
        name: 'setting',
        tokens: fullTokens({ '--skin-color-accent': '#00ff00' }),
      }) as SkinDocument,
      platform,
    });

    expect(resolved.tokens['--skin-color-accent']).toBe('#ff0000');
    expect(resolved.provenance['--skin-color-accent']).toBe('capsule');
  });

  test('falls through per token when capsule is partial', () => {
    const platform = doc({ name: 'platform' }) as SkinDocument;
    const capsule = {
      schema_version: '1',
      name: 'partial',
      tokens: { '--skin-color-accent': '#ff0000' },
    } as unknown as SkinDocument;

    const resolved = resolveSkin({ capsule, platform });
    expect(resolved.tokens['--skin-color-accent']).toBe('#ff0000');
    expect(resolved.tokens['--skin-color-bg-void']).toBe('#f5f5f5');
    expect(resolved.provenance['--skin-color-bg-void']).toBe('platform');
  });

  test('surface overrides merge across layers', () => {
    const platform = doc({ name: 'platform' }) as SkinDocument;
    const capsule = {
      schema_version: '1',
      name: 'c',
      tokens: {},
      surfaces: {
        chat: { '--skin-color-bg-card': '#111111' },
      },
    } as unknown as SkinDocument;

    const resolved = resolveSkin({ capsule, platform });
    expect(resolved.surfaces.chat?.['--skin-color-bg-card']).toBe('#111111');
  });
});

describe('alias bridge', () => {
  test('expandTokenMap emits legacy --platform-* / --soma-* reads', () => {
    const expanded = expandTokenMap({
      '--skin-color-accent': '#FF4D00',
      '--skin-color-bg-void': '#050505',
    });
    expect(expanded['--platform-accent']).toBe('#FF4D00');
    expect(expanded['--soma-accent']).toBe('#FF4D00');
    expect(expanded['--soma-primary']).toBe('#FF4D00');
    expect(expanded['--platform-bg-void']).toBe('#050505');
    expect(expanded['--soma-bg-void']).toBe('#050505');
  });

  test('alias values never override an explicit legacy key', () => {
    const expanded = expandTokenMap({
      '--skin-color-accent': '#FF4D00',
      '--platform-accent': '#000000',
    });
    expect(expanded['--platform-accent']).toBe('#000000');
    expect(expanded['--soma-accent']).toBe('#FF4D00');
  });
});
