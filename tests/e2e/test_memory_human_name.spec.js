/**
 * Mission T — human-like name save + recall through the REAL memory lane.
 *
 * The walk a person takes:
 *   1. log in with the local password identity (no Keycloak, no mock auth)
 *   2. open a new chat -> "My name is Daniel. Remember it."
 *   3. NO approval dialog for memory_save — memory_save is auto_execute, so an
 *      Approve button (DOM) or a tool.approval_request frame (WS) is a failure.
 *      The Approve-button wait is a TIMEOUT wait: absence is the pass.
 *   4. wait for chat.done or memory_hits (chat.turn_meta.memory_hits); if the
 *      brain still 503s on remember, FAIL with the exact message:
 *      'memory remember 503 — brain SFM endpoint'
 *   5. new conversation -> "What is my name?" -> Daniel in the reply
 *   6. GET /memory/ (same-origin page fetch, session cookie) lists a hit
 *      containing Daniel
 *
 * VIBE: real browser against the live stack. Every frame, button and HTTP
 * status observed comes from the running product. No mocks, no stubbed auth.
 *
 * Env: UI_BASE_URL (default http://localhost:20080)
 *      TEST_USER_EMAIL / TEST_USER_PASSWORD (default test@soma.dev /
 *      testpassword123 — the local identity this mission names explicitly).
 */

const { test, expect } = require('@playwright/test');

const UI = process.env.UI_BASE_URL || 'http://localhost:20080';
const EMAIL = process.env.TEST_USER_EMAIL || 'test@soma.dev';
const PASSWORD = process.env.TEST_USER_PASSWORD || 'testpassword123';

/** The exact failure message this mission mandates when brain still 503s. */
const REMEMBER_503 = 'memory remember 503 — brain SFM endpoint';

/** One turn of a real LLM + tool loop may take a while; never the 60s default. */
const TURN_TIMEOUT_MS = 120000;

test.describe.configure({ mode: 'serial' });
test.setTimeout(300000);

// ─── helpers ────────────────────────────────────────────────────────────────

/** Local password login through the real form. No Keycloak, no auth injection. */
async function loginLocal(page) {
  await page.context().clearCookies();
  await page.goto(`${UI}/login`);
  await page.locator('input[placeholder="name@company.com"]').fill(EMAIL);
  await page.locator('input[placeholder="Enter your password"]').fill(PASSWORD);
  await page.locator('button:has-text("Sign in")').first().click();
  await expect(page).not.toHaveURL(/\/login/, { timeout: 30000 });
}

/** Chat shell with a live websocket — the turn channel must actually be up. */
async function waitForChatSocket(page) {
  await page.goto(`${UI}/chat`, { timeout: 30000 });
  await page.waitForFunction(
    () => {
      const c = document.querySelector('soma-chat');
      return Boolean(c && c._selectedAgentId && c._wsConnected);
    },
    { timeout: 30000 }
  );
}

/**
 * Record EVERY WS frame the page receives and EVERY /memory HTTP status >=500.
 * These are the only honest sources for "did an approval fire" and "did the
 * brain 503" — the DOM collapses both.
 */
function watch(page) {
  const frames = [];
  const httpErrors = [];
  page.on('websocket', (ws) => {
    ws.on('framereceived', ({ payload }) => {
      try {
        frames.push(JSON.parse(typeof payload === 'string' ? payload : String(payload)));
      } catch {
        // binary frame — not part of the chat JSON protocol
      }
    });
  });
  page.on('response', (res) => {
    if (/\/memory/.test(res.url()) && res.status() >= 500) {
      httpErrors.push({ url: res.url(), status: res.status() });
    }
  });
  return { frames, httpErrors };
}

function approvalRequested(frames) {
  return (
    frames.find(
      (f) =>
        f.type === 'tool.approval_request' &&
        String(f.payload?.name || '').startsWith('memory_save')
    ) || null
  );
}

/**
 * Failure evidence from the memory_save tool.done frame.
 * Three honest shapes:
 *   - ok:false / error string (tool raised)
 *   - ok:true but result.saved === false (acks all failed)
 *   - acks[] entries carrying an error (partial store failure)
 * Returns null when the save is clean.
 */
function memorySaveFailure(frames) {
  for (const f of frames) {
    if (f.type !== 'tool.done' || f.payload?.name !== 'memory_save') continue;
    const err = String(f.payload.error || '');
    if (f.payload.ok === false || err) {
      return err || 'memory_save ok=false (no error text)';
    }
    const result = f.payload.result || {};
    const ackErrors = (result.acks || [])
      .map((a) => (a && a.ok === false ? String(a.error || 'ack ok=false') : ''))
      .filter(Boolean);
    if (result.saved === false) {
      return `memory_save result.saved=false — acks: ${ackErrors.join('; ') || JSON.stringify(result.acks || [])}`;
    }
    if (ackErrors.length > 0 && (result.acks || []).every((a) => !a || a.ok === false)) {
      return `every memory_save ack failed — ${ackErrors.join('; ')}`;
    }
  }
  return null;
}

function looksLike503(text) {
  return /503|SomaBrain|unavailable|not configured|circuit open|Service Unavailable/i.test(
    text || ''
  );
}

function hasTurnCompleted(frames) {
  return (
    frames.some((f) => f.type === 'chat.done') ||
    frames.some((f) => f.type === 'tool.done' && f.payload?.name === 'memory_save')
  );
}

function hasMemoryHits(frames) {
  return frames.some(
    (f) =>
      f.type === 'chat.turn_meta' &&
      Array.isArray(f.payload?.memory_hits) &&
      f.payload.memory_hits.length > 0
  );
}

/** No new frame for `quietMs` — tool loop settled enough to scan for 503. */
async function settleFrames(frames, quietMs = 2000, deadlineMs = 30000) {
  const end = Date.now() + deadlineMs;
  let last = frames.length;
  let lastChange = Date.now();
  while (Date.now() < end) {
    if (frames.length !== last) {
      last = frames.length;
      lastChange = Date.now();
    } else if (Date.now() - lastChange >= quietMs) {
      return;
    }
    await new Promise((r) => setTimeout(r, 250));
  }
}

function assistant(page) {
  return page.locator('soma-message[message-role="assistant"]');
}

async function composerBox(page) {
  const box = page.locator('soma-composer textarea, soma-chat textarea, textarea').first();
  await box.waitFor({ state: 'visible', timeout: 30000 });
  return box;
}

/** Shadow-DOM aware text of one assistant bubble. */
async function bubbleText(bubble) {
  const raw = await bubble
    .evaluate((el) => {
      const root = el.shadowRoot || el;
      const body = root.querySelector('.text') || root;
      return body.textContent || '';
    })
    .catch(() => '');
  return raw.replace(/\s+/g, ' ').trim();
}

/** Text of THIS bubble, cardinality-gated — never a stale previous turn. */
async function awaitNewReply(page, count) {
  const bubble = assistant(page).nth(count);
  await expect(bubble, 'assistant reply never appeared').toBeVisible({
    timeout: TURN_TIMEOUT_MS,
  });
  await expect
    .poll(async () => (await bubbleText(bubble)).length, {
      timeout: TURN_TIMEOUT_MS,
      message: 'assistant reply never produced text',
    })
    .toBeGreaterThan(0);
  await expect
    .poll(
      async () => {
        const cur = await bubbleText(bubble);
        await page.waitForTimeout(800);
        return cur === (await bubbleText(bubble));
      },
      { timeout: 30000, message: 'assistant reply never stopped streaming' }
    )
    .toBe(true);
  return bubbleText(bubble);
}

/**
 * Send a turn and return the NEW assistant bubble's text.
 * Cardinality gate: count first, read index n — never bare .last().
 */
async function sendTurn(page, text) {
  await waitForChatSocket(page);
  const box = await composerBox(page);
  const before = await assistant(page).count();
  await box.fill(text);
  await box.press('Enter');
  return { reply: await awaitNewReply(page, before), before };
}

async function startNewConversation(page) {
  const newChat = page
    .locator('button:has-text("New Chat"), button:has-text("New chat")')
    .first();
  await expect(newChat).toBeVisible({ timeout: 30000 });
  await newChat.click();
  // A fresh conversation must clear the transcript — otherwise the next
  // ask() reads a stale bubble and the isolation is a lie.
  await expect(assistant(page)).toHaveCount(0, { timeout: 30000 });
  await waitForChatSocket(page);
}

function norm(s) {
  return (s || '')
    .replace(/[‐-―−﹣－]/g, '-')
    .replace(/[‘’]/g, "'")
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Steps 2–4: send the remember turn and babysit it like a person would —
 * watching the tool timeline for an approval dialog the whole time, then
 * waiting for chat.done / memory_hits, then running the 503 gate.
 */
async function rememberName(page, watchHandle) {
  const { frames, httpErrors } = watchHandle;
  const box = await composerBox(page);
  const before = await assistant(page).count();
  await box.fill('My name is Daniel. Remember it.');
  await box.press('Enter');

  // ── Step 3: NO approval dialog for memory_save ────────────────────────────
  // Wait OUT the Approve button: absence over the whole turn is the pass.
  // An approval for memory_save must fail immediately, in DOM or on the wire.
  const deadline = Date.now() + TURN_TIMEOUT_MS;
  let toggleClicked = false;
  let completed = false;
  while (Date.now() < deadline && !completed) {
    const req = approvalRequested(frames);
    if (req) {
      throw new Error(
        `memory_save must auto-execute — tool.approval_request fired on the wire: ` +
          `${JSON.stringify(req.payload)}`
      );
    }

    // Human path: open the tool activity so an approval row would be visible.
    if (!toggleClicked) {
      const toggle = page.locator('button.tools-toggle').first();
      if ((await toggle.count()) > 0 && (await toggle.isVisible().catch(() => false))) {
        await toggle.click({ timeout: 5000 }).catch(() => {});
        toggleClicked = true;
      }
    }
    const approve = page.locator('button:has-text("Approve")').first();
    if ((await approve.count()) > 0 && (await approve.isVisible().catch(() => false))) {
      throw new Error(
        'memory_save must auto-execute — Approve button appeared in the tool timeline'
      );
    }

    // ── Step 4 wait: chat.done or memory_hits ───────────────────────────────
    // Inside the loop only chat.done / memory_save tool.done exit early —
    // memory_hits (chat.turn_meta) is emitted BEFORE the tool loop, so it
    // cannot prove the save finished. memory_hits is accepted as the wait
    // signal only at the deadline (below), followed by a settle + 503 scan.
    if (hasTurnCompleted(frames)) {
      completed = true;
      break;
    }
    await page.waitForTimeout(500);
  }

  if (!completed) {
    if (hasMemoryHits(frames)) {
      // Mission allows memory_hits as the wait signal — settle, then scan.
      await settleFrames(frames);
    } else {
      throw new Error(
        `no chat.done and no memory_hits (chat.turn_meta) within ${TURN_TIMEOUT_MS}ms — ` +
          `the remember turn never completed. frame types seen: ` +
          `${[...new Set(frames.map((f) => f.type))].join(', ') || '(none)'}`
      );
    }
  } else {
    // chat.done is metadata-only and arrives after every tool frame; a short
    // settle catches trailing tool.done if we exited via memory_save earlier.
    await settleFrames(frames, 1500, 15000);
  }

  // The reply must land as visible text — a turn that renders nothing is not done.
  const reply = await awaitNewReply(page, before);
  expect(reply.length, 'remember turn produced no visible reply').toBeGreaterThan(0);

  // ── 503 gate: brain SFM endpoint still down on remember ───────────────────
  const saveErr = memorySaveFailure(frames);
  const http503 = httpErrors.find((e) => e.status === 503);

  // One direct probe with the session cookie — the store itself must answer.
  const probe = await page.evaluate(async () => {
    const r = await fetch('/api/v2/memory/?limit=1', { credentials: 'same-origin' });
    return { status: r.status, body: (await r.text()).slice(0, 500) };
  });

  if (http503 || probe.status === 503 || looksLike503(saveErr)) {
    throw new Error(
      `${REMEMBER_503} — ` +
        `memory_save error: ${saveErr || '(none on wire)'}; ` +
        `memory HTTP: ${http503 ? `${http503.status} ${http503.url}` : probe.status}; ` +
        `list probe body: ${probe.body}`
    );
  }
  if (probe.status >= 500 || (saveErr && looksLike503(probe.body))) {
    throw new Error(
      `${REMEMBER_503} — memory list HTTP ${probe.status}: ${probe.body}` +
        (saveErr ? `; memory_save error: ${saveErr}` : '')
    );
  }
  if (saveErr) {
    // Not a 503, but memory_save itself failed — still a hard failure, and the
    // detail is what the next engineer needs.
    throw new Error(`memory_save failed on the remember turn: ${saveErr}`);
  }

  return { reply, probe };
}

// ─── the walk ───────────────────────────────────────────────────────────────

test.describe('Mission T: name save + recall (human, no mocks)', () => {
  test('remember Daniel with no approval dialog and no brain 503', async ({ page }) => {
    const watchHandle = watch(page);

    // Step 1: local login — real form, real /api/v2/auth/login, no Keycloak.
    await loginLocal(page);
    const user = await page.evaluate(() => localStorage.getItem('soma_user'));
    expect(user, 'login must land an authenticated session').toBeTruthy();
    expect(JSON.parse(user).email).toBe(EMAIL);

    // Step 2: new chat, then the remember line.
    await waitForChatSocket(page);
    await startNewConversation(page);

    const { reply } = await rememberName(page, watchHandle);

    // Positive wire evidence is logged, never asserted as the only proof —
    // the 503 gate above already scanned every tool.done frame.
    const saved = watchHandle.frames.find(
      (f) => f.type === 'tool.done' && f.payload?.name === 'memory_save'
    );
    console.log(
      `[Mission T] memory_save tool.done: ${saved ? JSON.stringify(saved.payload).slice(0, 1500) : '(model did not call memory_save this turn)'}`
    );
    console.log(`[Mission T] remember reply: ${reply.slice(0, 200)}`);
  });

  test('new conversation recalls: What is my name -> Daniel', async ({ page }) => {
    await loginLocal(page);
    await waitForChatSocket(page);
    await startNewConversation(page);

    // Fresh transcript: the answer must come back through memory, not history.
    const { reply } = await sendTurn(page, 'What is my name?');
    expect(
      norm(reply).toLowerCase(),
      `recall failed — reply was: "${reply.slice(0, 300)}"`
    ).toContain('daniel');
  });

  test('GET /memory/ lists a hit containing Daniel (page fetch, session cookie)', async ({
    page,
  }) => {
    await loginLocal(page);

    const list = await page.evaluate(async () => {
      const r = await fetch('/api/v2/memory/?limit=20', { credentials: 'same-origin' });
      return { status: r.status, body: await r.text() };
    });

    if (list.status === 503 || looksLike503(list.body.slice(0, 300))) {
      throw new Error(`${REMEMBER_503} — GET /api/v2/memory/ returned ${list.status}: ${list.body.slice(0, 300)}`);
    }
    expect(
      list.status,
      `GET /api/v2/memory/ returned HTTP ${list.status} — an outage must not read as "no memories". body=${list.body.slice(0, 300)}`
    ).toBe(200);
    expect(
      list.body,
      `GET /api/v2/memory/ 200 but no hit containing Daniel. body=${list.body.slice(0, 500)}`
    ).toContain('Daniel');
  });
});
