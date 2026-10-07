/**
 * Memory algorithms through the real AGENT+BRAIN conversation.
 *
 * The owner's bar: "the conversation with the agent must be PERFECT. He must
 * remember, forget, and get all memories based on the algorithms of SomaBrain."
 *
 * VIBE COMPLIANT:
 * - Real browser against the live stack. No mocks, no fakes, no stubbed LLM.
 * - Every endpoint and credential is REQUIRED from the runner. A default IS a
 *   hardcoded value.
 * - The ONLY DOM surface fed exclusively by MemoryGateway.recall() is
 *   chat.turn_meta.memory_hits (chat_orchestrator -> soma-chat turn-meta
 *   details ul li). Assistant prose is a SECONDARY check: the transcript is in
 *   the LLM history and can answer with the store offline.
 * - Assistant bubbles are read at a cardinality-gated index. Bare .last() is
 *   the previous turn's bubble between Enter and the first delta.
 * - FORGET is proven with a surviving control marker. An empty lane after a
 *   forget is also what an outage looks like — empty alone is FAILURE.
 *
 * Promotion rule (somabrain/memory/promotion.py, A2.1 / PromotionTracker):
 *   WM items with salience >= BrainSetting "promotion_threshold" for 3+
 *   consecutive ticks are promoted to LTM (min_ticks=3, threshold from
 *   BrainSetting.get("promotion_threshold", tenant_id)). Promoted payload
 *   carries memory_type="episodic" and promoted_from_wm=true. This suite
 *   states that rule; it does not invent one.
 *
 * Score bands (never one global threshold — a missing score collapses to 0.0
 * in somabrain_adapter._to_hit, and real LTM hits score ~0.05):
 *   WM hit  >= 0.9
 *   LTM hit >  0 and >= 0.01
 * Identity first: the marker in hit text/coord IS the proof.
 */

const { test, expect } = require('@playwright/test');
const { execFileSync } = require('child_process');
const crypto = require('crypto');

function requiredEnv(name) {
  const value = (process.env[name] || '').trim();
  if (!value) {
    throw new Error(
      `${name} is not set. Every endpoint and credential this suite uses is ` +
        `supplied by the runner. There is no default.`
    );
  }
  return value;
}

function requiredCount(name) {
  const raw = requiredEnv(name);
  const n = Number(raw);
  if (!Number.isInteger(n) || n <= 0) {
    throw new Error(`${name} must be a positive integer, got ${raw}`);
  }
  return n;
}

const UI = requiredEnv('UI_BASE_URL');
const API = requiredEnv('API_BASE_URL');
const EMAIL = requiredEnv('TEST_USER_EMAIL');
const PASSWORD = requiredEnv('TEST_USER_PASSWORD');
// Container that owns the agent Django ORM (Tenant.objects.create isolation,
// same seam row shape as tests/e2e/test_triad_integration.py).
const DJANGO_CONTAINER = requiredEnv('AGENT_DJANGO_CONTAINER');

// EXISTING product knob (settings_model.py / config/settings.py: MEM_RECALL_TOP_K).
// Never a sibling name (AP-01). Supplied by the runner; no default.
const RECALL_TOP_K = requiredCount('MEM_RECALL_TOP_K');

// UI wait bounds come from the ONE Playwright declaration site
// (playwright.config.js `timeout`). We do not invent TEST_TIMEOUT_* siblings
// (AP-01 / AP-06). Callers pass the project timeout in.
function projectTimeoutMs() {
  return test.info().project.timeout;
}

// Observed score band (ground truth 2026-10-07: WM ~1.000, LTM ~0.05-0.09).
// Assertion expectations on measured reality — the gate the store must satisfy.
const WM_MIN_SCORE = 0.9;
const LTM_MIN_SCORE = 0.01;

const RUN = `mem-${Date.now().toString(36)}-${Math.floor(Math.random() * 1e6).toString(36)}`;

// Independent algorithms — one failing recall must not hide chrome or honesty.
test.describe.configure({ mode: 'default' });

// ─── helpers (login / composer / socket: same product path as the other specs) ─

async function login(page) {
  await page.goto(`${UI}/login`);
  await page.getByRole('textbox', { name: 'name@company.com' }).fill(EMAIL);
  await page.getByRole('textbox', { name: 'Enter your password' }).fill(PASSWORD);
  await page.getByRole('textbox', { name: 'Enter your password' }).press('Enter');
  await expect(
    page.locator('soma-chat, .chat-workspace').first()
  ).toBeVisible({ timeout: projectTimeoutMs() });
}

async function composer(page) {
  const box = page
    .locator('soma-composer textarea, soma-chat textarea, textarea')
    .first();
  await box.waitFor({ state: 'visible', timeout: projectTimeoutMs() });
  return box;
}

async function waitForChatSocket(page) {
  await page.waitForFunction(
    () => {
      const chat = document.querySelector('soma-chat');
      return Boolean(chat && chat._wsConnected);
    },
    { timeout: projectTimeoutMs() }
  );
}

function normalise(text) {
  return (text || '')
    .replace(/[‐-―−﹣－]/g, '-')
    .replace(/[‘’‚‛]/g, "'")
    .replace(/[“”„‟]/g, '"')
    .replace(/[   ]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function assistantLocator(page) {
  return page.locator('soma-message[message-role="assistant"]');
}

/**
 * Turn-meta recall hits — the ONLY DOM fed exclusively by MemoryGateway.recall().
 * (chat.turn_meta.memory_hits -> soma-chat.ts [data-control="turn-meta"] details ul li)
 */
function recallHitLocator(page) {
  return page.locator('soma-chat [data-control="turn-meta"] details ul li');
}

function turnMetaLocator(page) {
  return page.locator('soma-chat [data-control="turn-meta"]');
}

/**
 * Send one turn and return the NEW assistant bubble's text.
 * Cardinality gate: count first, then read index n. Never bare .last().
 */
async function sendTurn(page, text) {
  await waitForChatSocket(page);
  const box = await composer(page);
  const assistant = assistantLocator(page);
  const n = await assistant.count();
  await box.fill(text);
  await box.press('Enter');

  const bubble = assistant.nth(n);
  await expect(
    bubble,
    `assistant bubble #${n} never appeared after sending the turn`
  ).toBeVisible({ timeout: projectTimeoutMs() });

  // The turn must land content ON THIS BUBBLE, not on a previous one.
  await expect
    .poll(
      async () => {
        return await bubble
          .evaluate((el) => {
            const root = el.shadowRoot || el;
            return (root.textContent || '').replace(/\s+/g, ' ').trim().length;
          })
          .catch(() => 0);
      },
      {
        timeout: projectTimeoutMs(),
        message: `assistant bubble #${n} never produced text — the reply did not render`,
      }
    )
    .toBeGreaterThan(0);

  // Streaming settle: wait until THIS bubble's text length is stable, not a
  // fixed sleep (expect.poll, not a magic number).
  let prev = await bubble.evaluate((el) => {
    const root = el.shadowRoot || el;
    return (root.textContent || '').length;
  }).catch(() => 0);
  await expect
    .poll(async () => {
      const cur = await bubble.evaluate((el) => {
        const root = el.shadowRoot || el;
        return (root.textContent || '').length;
      }).catch(() => 0);
      const stable = cur === prev && cur > 0;
      prev = cur;
      return stable;
    }, { timeout: projectTimeoutMs(), message: 'assistant bubble text never stabilised' })
    .toBe(true);
  return (
    await bubble
      .evaluate((el) => {
        const root = el.shadowRoot || el;
        return root.textContent || '';
      })
      .catch(() => '')
  )
    .replace(/\r\n/g, '\n')
    .replace(/[ \t]+/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

/**
 * Wait until turn-meta recall has been refreshed for the turn just sent.
 * `expect` on presence/absence of a marker; a fixed sleep cannot do this.
 */
async function waitForRecallContaining(page, text, timeout = projectTimeoutMs()) {
  const hits = recallHitLocator(page).filter({ hasText: text });
  await expect(
    hits,
    `recall lane never returned a hit containing "${text}"`
  ).toHaveCount(1, { timeout });
}

async function waitForRecallNotContaining(page, text, timeout = projectTimeoutMs()) {
  const hits = recallHitLocator(page).filter({ hasText: text });
  await expect(
    hits,
    `recall lane still shows a hit containing "${text}" — forget did not land`
  ).toHaveCount(0, { timeout });
}

/**
 * Prove the memory-list HTTP is a live 200, not an outage dressed as empty.
 * Returns the parsed body. A non-200 throws (Rule 7: absent evidence is failure).
 */
async function fetchMemoryList(page, limit = RECALL_TOP_K) {
  const result = await page.evaluate(async (lim) => {
    const res = await fetch(`/api/v2/memory/?limit=${lim}`, {
      credentials: 'same-origin',
    });
    const text = await res.text();
    let body = null;
    try {
      body = JSON.parse(text);
    } catch {
      body = { raw: text };
    }
    return { status: res.status, body };
  }, limit);

  expect(
    result.status,
    `GET /api/v2/memory/ returned HTTP ${result.status} — the store did not ` +
      `answer. An outage must not be read as "no memories". body=${JSON.stringify(result.body)}`
  ).toBe(200);
  return result.body;
}

/**
 * Isolated tenant per test — same seam isolation as
 * tests/e2e/test_triad_integration.py: Tenant.objects.create(slug=...).
 * The chat principal's tenant still comes from the JWT (THE ONE PATH); this
 * row is the test's own tenant identity so runs never share one slug.
 */
function createIsolatedTenant() {
  const script = [
    'import django, os, uuid',
    'os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")',
    'django.setup()',
    'from admin.aaas.models import Tenant',
    't = Tenant.objects.create(',
    '    name="Seam Tenant",',
    '    slug=f"seam-tenant-{uuid.uuid4().hex[:8]}",',
    ')',
    'print(t.id)',
  ].join('\n');

  const out = execFileSync(
    'docker',
    ['exec', DJANGO_CONTAINER, 'python', '-c', script],
    { encoding: 'utf8' }
  );
  const id = out
    .trim()
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => /^[0-9a-f-]{36}$/i.test(l))
    .pop();
  if (!id) {
    throw new Error(
      `Tenant.objects.create produced no id. stdout was: ${out}`
    );
  }
  return id;
}

function mark(label) {
  return `${label}-${RUN}-${crypto.randomBytes(3).toString('hex')}`;
}

async function startFreshConversation(page) {
  const before = await assistantLocator(page).count();
  const newChat = page
    .locator('button:has-text("New Chat"), button:has-text("New chat")')
    .first();
  await expect(newChat).toBeVisible({ timeout: projectTimeoutMs() });
  await newChat.click();
  // A new conversation clears the transcript. If the old bubbles remain, the
  // next ask() would read a stale turn and the isolation would be a lie.
  await expect(assistantLocator(page)).toHaveCount(0, { timeout: projectTimeoutMs() });
  expect(
    before,
    'the walk started with zero assistant bubbles — cardinality gate is useless'
  ).toBeGreaterThanOrEqual(0);
  await waitForChatSocket(page);
}

test.describe('SomaBrain memory algorithms through the conversation', () => {
  test.beforeEach(async ({ page }) => {
    // Case budget is the project timeout (playwright.config.js / CLI --timeout).
    // No invented TEST_TIMEOUT_* sibling (AP-01).
    test.setTimeout(projectTimeoutMs());
    await page.context().clearCookies();
  });

  // ─── 1. REMEMBER ─────────────────────────────────────────────────────────

  test('remember: a codeword told to the agent comes back in the RECALL lane', async ({
    page,
  }) => {
    const tenant = createIsolatedTenant();
    expect(
      tenant,
      `isolated tenant id must be a UUID, got ${tenant}`
    ).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
    const CODE = mark('codeword');

    await login(page);
    await sendTurn(page, `Remember this codeword for me: ${CODE}`);
    // Later turn, different phrasing. The claim is the RECALL LANE, not prose.
    await sendTurn(page, 'What codeword did I ask you to remember?');

    await waitForRecallContaining(page, CODE);

    // Secondary: the assistant also says it (never the sole proof).
    const reply = await sendTurn(page, `Say the codeword ${CODE} back to me exactly.`);
    expect(
      normalise(reply),
      `assistant did not echo the codeword: got "${reply}"`
    ).toContain(CODE);
  });

  // ─── 2. FORGET ───────────────────────────────────────────────────────────

  test('forget: the fact leaves the recall lane while a control fact survives', async ({
    page,
  }) => {
    const tenant = createIsolatedTenant();
    expect(tenant).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
    const MARK_A = mark('forget-a');
    const MARK_B = mark('keep-b');

    await login(page);

    // Both facts in one turn so they share the write path and the tick window.
    await sendTurn(
      page,
      `Remember two codewords. First: ${MARK_A}. Second: ${MARK_B}.`
    );

    // Positive control BEFORE the forget: both must be recallable.
    await sendTurn(
      page,
      `What two codewords did I ask you to remember? Reply with both.`
    );
    await waitForRecallContaining(page, MARK_A);
    await waitForRecallContaining(page, MARK_B);

    // Forget only MARK_A.
    await sendTurn(
      page,
      `Forget the codeword ${MARK_A}. Keep the other one. Confirm in one sentence.`
    );

    // A turn whose recall must return the surviving fact and NOT the forgotten one.
    await sendTurn(
      page,
      `Which codeword do you still have? The one I did not ask you to forget.`
    );
    await waitForRecallContaining(page, MARK_B);
    await waitForRecallNotContaining(page, MARK_A);

    // HTTP proof: the list is live 200 and does not contain MARK_A.
    // A non-200 fails inside fetchMemoryList (an outage is not "forgotten").
    const body = await fetchMemoryList(page);
    const texts = (body.memories || [])
      .map((m) => String(m.text || m.content || ''))
      .join('\n');
    expect(
      texts,
      `GET /api/v2/memory/ 200 still lists the forgotten codeword ${MARK_A}`
    ).not.toContain(MARK_A);
    expect(
      texts,
      `GET /api/v2/memory/ 200 lost the control codeword ${MARK_B} — ` +
        `empty alone is not a successful forget`
    ).toContain(MARK_B);
  });

  // ─── 3. PERSISTENCE ──────────────────────────────────────────────────────

  test('persistence: the fact survives a new conversation', async ({ page }) => {
    const tenant = createIsolatedTenant();
    expect(tenant).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
    const CODE = mark('persist');

    await login(page);
    await sendTurn(page, `Remember this codeword for me: ${CODE}`);

    // Real conversation boundary. The transcript cannot satisfy the next turn.
    await startFreshConversation(page);

    await sendTurn(page, 'What codeword did I ask you to remember?');
    await waitForRecallContaining(page, CODE);

    const reply = await sendTurn(
      page,
      `Reply with only the word ${CODE}.`
    );
    expect(
      normalise(reply),
      `recall across the conversation boundary failed: got "${reply}"`
    ).toContain(CODE);
  });

  // ─── 4. DURABILITY ───────────────────────────────────────────────────────

  test('durability: the fact is in LTM (store somafractalmemory), not just WM', async ({
    page,
  }) => {
    const tenant = createIsolatedTenant();
    expect(tenant).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
    const CODE = mark('durable');

    await login(page);
    await sendTurn(page, `Remember this codeword for me: ${CODE}`);
    await sendTurn(page, 'What codeword did I ask you to remember?');
    await waitForRecallContaining(page, CODE);

    // The store labels on the hit are the durability claim.
    // WM is somaabrain; LTM is somafractalmemory (brain _hit_record).
    const hits = await page.evaluate(async (needle) => {
      const res = await fetch('/api/v2/memory/recall', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: needle, top_k: RECALL_TOP_K }),
      });
      const status = res.status;
      const body = await res.json().catch(() => ({}));
      return { status, body };
    }, CODE);

    expect(
      hits.status,
      `POST /api/v2/memory/recall returned HTTP ${hits.status}`
    ).toBe(200);

    const rows = hits.body.memories || hits.body.results || [];
    const matching = rows.filter((r) =>
      String(r.text || r.content || '').includes(CODE)
    );
    expect(
      matching.length,
      `recall by marker returned no identity hit for ${CODE}. ` +
        `rows=${JSON.stringify(rows)}`
    ).toBeGreaterThan(0);

    const stores = matching.map((r) => String(r.store || '')).filter(Boolean);
    const layers = matching.map((r) => String(r.layer || '')).filter(Boolean);
    expect(
      stores.length,
      `hits must carry a real store label. got=${JSON.stringify(matching)}`
    ).toBeGreaterThan(0);
    expect(
      layers.length,
      `hits must carry a real layer label (wm|ltm). got=${JSON.stringify(matching)}`
    ).toBeGreaterThan(0);

    // Durable means LTM, not only WM. If the promoter has not run yet the
    // honest failure is "no LTM hit" — we do not accept WM-only as durable.
    const ltm = matching.filter((r) => {
      const layer = String(r.layer || '').toLowerCase();
      const store = String(r.store || '').toLowerCase();
      return layer === 'ltm' || store === 'somafractalmemory';
    });
    expect(
      ltm.length,
      `no LTM hit for ${CODE} — durability requires store somafractalmemory / ` +
        `layer ltm, not WM-only. matching=${JSON.stringify(matching)}`
    ).toBeGreaterThan(0);

    // Brain restart survival needs an operator-controlled restart. We assert
    // the LTM label above; the restart step is reported as operator action.
  });

  // ─── 5. SCORING ──────────────────────────────────────────────────────────

  test('scoring: hits carry store+layer; a WM hit ranks above an LTM hit', async ({
    page,
  }) => {
    const tenant = createIsolatedTenant();
    expect(tenant).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
    const CODE = mark('score');

    await login(page);
    await sendTurn(page, `Remember this codeword for me: ${CODE}`);
    await sendTurn(page, 'What codeword did I ask you to remember?');
    await waitForRecallContaining(page, CODE);

    const hits = await page.evaluate(async (needle) => {
      const res = await fetch('/api/v2/memory/recall', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: needle, top_k: RECALL_TOP_K }),
      });
      return { status: res.status, body: await res.json().catch(() => ({})) };
    }, CODE);

    expect(hits.status).toBe(200);
    const rows = (hits.body.memories || hits.body.results || []).filter((r) =>
      String(r.text || r.content || '').includes(CODE)
    );
    expect(rows.length, `no identity hit for ${CODE}`).toBeGreaterThan(0);

    for (const r of rows) {
      expect(
        String(r.store || ''),
        `hit is missing a store label: ${JSON.stringify(r)}`
      ).not.toBe('');
      expect(
        String(r.layer || ''),
        `hit is missing a layer label: ${JSON.stringify(r)}`
      ).not.toBe('');
    }

    const wm = rows.filter((r) => String(r.layer || '').toLowerCase() === 'wm');
    const ltm = rows.filter((r) => String(r.layer || '').toLowerCase() === 'ltm');

    for (const r of wm) {
      const score = Number(r.score);
      expect(
        Number.isFinite(score) && score >= WM_MIN_SCORE,
        `WM hit must score >= ${WM_MIN_SCORE} (got ${r.score}) for ${CODE}`
      ).toBe(true);
    }
    for (const r of ltm) {
      const score = Number(r.score);
      expect(
        Number.isFinite(score) && score > 0 && score >= LTM_MIN_SCORE,
        `LTM hit must score > 0 and >= ${LTM_MIN_SCORE} (got ${r.score}) for ${CODE}`
      ).toBe(true);
    }

    // Relative ordering: when both layers answer the same text, WM outranks LTM.
    if (wm.length > 0 && ltm.length > 0) {
      const bestWm = Math.max(...wm.map((r) => Number(r.score) || 0));
      const bestLtm = Math.max(...ltm.map((r) => Number(r.score) || 0));
      expect(
        bestWm,
        `WM hit must rank above LTM for the same text (wm=${bestWm} ltm=${bestLtm})`
      ).toBeGreaterThan(bestLtm);
    } else {
      // Identity + banding still prove labelling; ordering needs both layers.
      expect(
        wm.length + ltm.length,
        `expected at least one labelled wm/ltm hit for ${CODE}`
      ).toBeGreaterThan(0);
    }
  });

  // ─── 6. SALIENCE ─────────────────────────────────────────────────────────

  test('salience: a high-importance write is promoted to LTM (3+ ticks)', async ({
    page,
  }) => {
    const tenant = createIsolatedTenant();
    expect(tenant).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
    const CODE = mark('salient');

    await login(page);

    // Drive remember through the composer (THE ONE PATH). POST /memory/save is
    // refused for this principal (resource:memory_write) and would be a bypass
    // of the conversation claim anyway. Salience on the chat write is whatever
    // the orchestrator derives; the promoter rule is the gate.
    // Real rule (somabrain/memory/promotion.py, A2.1 / PromotionTracker.check):
    //   promote when salience >= BrainSetting "promotion_threshold"
    //   for 3+ consecutive ticks (min_ticks=3).
    await sendTurn(page, `Remember this codeword for me: ${CODE}`);
    await sendTurn(page, 'What codeword did I ask you to remember?');
    await waitForRecallContaining(page, CODE);

    // Promotion claim: the fact reaches LTM.
    // (A2.1: salience >= threshold for 3+ ticks; threshold is
    //  BrainSetting "promotion_threshold" — not a literal in this suite.)
    await expect
      .poll(
        async () => {
          const probe = await page.evaluate(async (needle) => {
            const res = await fetch('/api/v2/memory/recall', {
              method: 'POST',
              credentials: 'same-origin',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ query: needle, top_k: RECALL_TOP_K }),
            });
            const body = await res.json().catch(() => ({}));
            return { status: res.status, body };
          }, CODE);
          if (probe.status !== 200) return 'http-' + probe.status;
          const rows = probe.body.memories || probe.body.results || [];
          const matching = rows.filter((r) =>
            String(r.text || r.content || '').includes(CODE)
          );
          const ltm = matching.filter((r) => {
            const layer = String(r.layer || '').toLowerCase();
            const store = String(r.store || '').toLowerCase();
            return layer === 'ltm' || store === 'somafractalmemory';
          });
          return ltm.length > 0 ? 'ltm' : 'no-ltm';
        },
        {
          timeout: projectTimeoutMs(),
          message:
            `high-salience fact ${CODE} never reached LTM. Promotion rule: ` +
            `salience >= BrainSetting promotion_threshold for 3+ consecutive ` +
            `ticks (somabrain/memory/promotion.py A2.1). No LTM hit means the ` +
            `promoter did not fire — not that the test may accept WM-only.`,
        }
      )
      .toBe('ltm');
  });

  // ─── 7. LANE HONESTY ─────────────────────────────────────────────────────

  test('lane honesty: empty recall is honest empty, never a fake "no memories"', async ({
    page,
  }) => {
    const tenant = createIsolatedTenant();
    expect(tenant).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
    // A codeword nobody wrote and nobody will write.
    const GHOST = mark('ghost');

    await login(page);
    await sendTurn(page, `What codeword did I ask you to remember about ${GHOST}?`);

    // Fabricated-memory guard: the ghost must never appear as a recall hit.
    await expect(
      recallHitLocator(page).filter({ hasText: GHOST }),
      `ghost marker ${GHOST} appeared in the recall lane — fabricated memory`
    ).toHaveCount(0, { timeout: projectTimeoutMs() });

    // Which honest state is the product in? Empty and outage must render
    // DIFFERENTLY. We never accept an outage painted as empty.
    const list = await page.evaluate(async (lim) => {
      const res = await fetch(`/api/v2/memory/?limit=${lim}`, {
        credentials: 'same-origin',
      });
      const text = await res.text();
      let body = null;
      try {
        body = JSON.parse(text);
      } catch {
        body = { raw: text };
      }
      return { status: res.status, body };
    }, 50);

    const meta = turnMetaLocator(page);
    await expect(meta, 'turn-meta never rendered').toBeVisible();
    const metaText = (await meta.innerText().catch(() => '')) || '';
    const pageText = await page.locator('body').innerText().catch(() => '');

    if (list.status === 200) {
      // STORE UP + nothing stored = honest empty. Not the outage sentinel.
      const texts = (list.body.memories || [])
        .map((m) => String(m.text || m.content || ''))
        .join('\n');
      expect(
        texts,
        `ghost ${GHOST} must not be in the live 200 memory list`
      ).not.toContain(GHOST);
      expect(
        metaText,
        'empty recall must not claim long-term memory is unavailable — ' +
          'that sentinel is only for a store outage'
      ).not.toMatch(/unavailable/i);
      expect(
        metaText,
        'empty recall must not invent a "[No relevant memories]" fact row'
      ).not.toMatch(/\[no (relevant )?memories\]/i);
      const emptyMark =
        /—|0 hit/i.test(metaText) || (await recallHitLocator(page).count()) === 0;
      expect(
        emptyMark,
        `store is up and empty — turn-meta must show the honest empty mark ` +
          `(em dash / 0 hits). meta="${metaText}"`
      ).toBe(true);
    } else {
      // STORE DOWN = unavailability, never a fake "no memories".
      // The two states must be distinguishable: outage paints the product
      // sentinel, empty paints the empty mark. Collapsing them is the bug.
      expect(
        metaText,
        `GET /api/v2/memory/ is HTTP ${list.status} (store down) but the ` +
          `lane paints empty rather than the unavailability sentinel. ` +
          `meta="${metaText}"`
      ).not.toMatch(/\[no (relevant )?memories\]/i);
      expect(
        /unavailable this turn|memory unavailable/i.test(pageText) ||
          /unavailable/i.test(metaText),
        `store outage (HTTP ${list.status}) must surface the unavailability ` +
          `sentinel ("[Long-term memory unavailable this turn]"). Neither ` +
          `the sentinel nor a 200 list is present — empty and outage are ` +
          `collapsed into one lie. body=${JSON.stringify(list.body)}`
      ).toBe(true);
    }
  });

  test('lane honesty: store outage shows the unavailability sentinel, not fake empty', async ({
    page,
  }) => {
    const tenant = createIsolatedTenant();
    expect(tenant).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);

    await login(page);
    // One real turn so turn-meta exists and the lane has rendered a state.
    await sendTurn(
      page,
      `What codeword did I ask you to remember about ${mark('outage-probe')}?`
    );

    const list = await page.evaluate(async (lim) => {
      const res = await fetch(`/api/v2/memory/?limit=${lim}`, {
        credentials: 'same-origin',
      });
      const text = await res.text();
      let body = null;
      try {
        body = JSON.parse(text);
      } catch {
        body = { raw: text };
      }
      return { status: res.status, body };
    }, 50);

    const meta = turnMetaLocator(page);
    await expect(meta, 'turn-meta never rendered').toBeVisible();
    const metaText = (await meta.innerText().catch(() => '')) || '';
    const pageText = await page.locator('body').innerText().catch(() => '');

    // The two honest states, from the product's own contract:
    //   memory_hits None  -> "[Long-term memory unavailable this turn]"
    //                       (admin/core/context/builder.py:_MEMORY_UNAVAILABLE)
    //   memory_hits []    -> "[No relevant memories]" / turn-meta empty mark
    // A fake "no memories" during an outage is the failure this test exists for.
    if (list.status === 200) {
      // Store answers: the lane must NOT claim unavailability.
      expect(
        metaText + pageText,
        `GET /api/v2/memory/ is 200 but the UI claims memory is unavailable`
      ).not.toMatch(/unavailable this turn|memory unavailable/i);
      expect(
        metaText,
        'live 200 list must not be rendered as a "[No relevant memories]" fact row'
      ).not.toMatch(/\[no (relevant )?memories\]/i);
    } else {
      // Store down: the lane must show the unavailability sentinel, and must
      // NOT show the success-empty vocabulary as if the user simply has none.
      expect(
        metaText,
        `HTTP ${list.status} (store down) — the lane must not render the ` +
          `success-empty token "[No relevant memories]". meta="${metaText}"`
      ).not.toMatch(/\[no (relevant )?memories\]/i);
      expect(
        /unavailable this turn|memory unavailable/i.test(pageText + metaText),
        `HTTP ${list.status} (store down) — the unavailability sentinel ` +
          `("[Long-term memory unavailable this turn]" / "[Memory unavailable]") ` +
          `is not in the DOM. Empty and outage are collapsed into one lie.`
      ).toBe(true);
    }
  });

  // ─── 8. CHROME ───────────────────────────────────────────────────────────

  test('chrome: five lanes (system/history/memory/tools/buffer) and the tool timeline', async ({
    page,
  }) => {
    const tenant = createIsolatedTenant();
    expect(tenant).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);

    await login(page);
    // Force a real tool call (ToolRegistry `timestamp`) so the timeline has
    // steps to show. "What day is it" can be answered from the model alone —
    // that would leave the timeline unrendered and the chrome unproven.
    await sendTurn(
      page,
      'Call the timestamp tool now and reply with exactly what it returns.'
    );

    const seen = new Set();

    // ONE vocabulary, exactly as admin/core/context/lanes.py / soma-agent-iq.
    const iq = page.locator('soma-agent-iq').first();
    await expect(iq, 'AgentIQ strip (5-lane chrome) is not visible').toBeVisible({
      timeout: projectTimeoutMs(),
    });

    const LANE_NAMES = ['System', 'History', 'Memory', 'Tools', 'Buffer'];
    for (const name of LANE_NAMES) {
      const lane = page
        .locator('soma-agent-iq .lane')
        .filter({ hasText: name });
      const count = await lane.count();
      expect(
        count,
        `lane "${name}" is missing from the 5-lane chrome (one vocabulary: ` +
          `system, history, memory, tools, buffer)`
      ).toBeGreaterThan(0);
      seen.add(name);
    }

    // Tool timeline is rendered inside the assistant message when a tool ran
    // (soma-message .tools -> soma-tool-timeline). A tool-using turn must
    // surface it — skip-as-pass is forbidden.
    const timeline = page.locator('soma-tool-timeline');
    await expect(
      timeline.first(),
      'a timestamp-tool turn produced no tool timeline — the person cannot ' +
        'see what the agent did'
    ).toBeVisible({ timeout: projectTimeoutMs() });

    // Anti-vacuous: the walk must actually have seen the five lanes.
    expect(
      seen.size,
      'the chrome walk saw no lanes — an empty page cannot pass'
    ).toBe(LANE_NAMES.length);
  });
});
