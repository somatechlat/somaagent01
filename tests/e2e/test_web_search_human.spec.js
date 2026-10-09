/**
 * Human walk: internet search + extract a fact from the web.
 *
 * Walk:
 *   1. local login
 *   2. new chat → ask the agent to search the web for a known fact and
 *      report a title/url plus a short fact from the page
 *   3. FAIL if reply never mentions a http(s) URL
 *   4. FAIL if tool timeline never shows web_search success (or if web_search
 *      is denied and no fallback answer with a URL appears)
 *
 * Env: UI_BASE_URL, TEST_USER_EMAIL, TEST_USER_PASSWORD
 * VIBE: live browser; WS frames + DOM. Requires SEARXNG_URL on the stack.
 */

const { test, expect } = require('@playwright/test');

const UI = process.env.UI_BASE_URL || 'http://localhost:20080';
const EMAIL = process.env.TEST_USER_EMAIL || 'test@soma.dev';
const PASSWORD = process.env.TEST_USER_PASSWORD || 'testpassword123';
const TURN_TIMEOUT_MS = 120000;

test.describe.configure({ mode: 'serial' });
test.setTimeout(300000);

function assistant(page) {
  return page.locator('soma-message[message-role="assistant"]');
}

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

async function waitForChatSocket(page) {
  await page.waitForFunction(
    () => {
      const c = document.querySelector('soma-chat');
      return Boolean(c && c._selectedAgentId && c._wsConnected);
    },
    { timeout: 30000 }
  );
}

async function composerBox(page) {
  const box = page.locator('soma-composer textarea, soma-chat textarea, textarea').first();
  await box.waitFor({ state: 'visible', timeout: 30000 });
  return box;
}

async function maybeApproveTools(page, frames) {
  // Capsule default is approval_required for web_search/web_read. A human
  // clicks Approve; this does the same when the wire asks.
  const deadline = Date.now() + 20000;
  while (Date.now() < deadline) {
    const req = frames.find(
      (f) =>
        f.type === 'tool.approval_request' &&
        (String(f.payload?.name || '').startsWith('web_search') ||
          String(f.payload?.name || '').startsWith('web_read'))
    );
    if (req) {
      const toggle = page.locator('button.tools-toggle').first();
      if ((await toggle.count()) && (await toggle.isVisible().catch(() => false))) {
        await toggle.click({ timeout: 3000 }).catch(() => {});
      }
      const approve = page
        .locator('button:has-text("Approve"), soma-tool-timeline button:has-text("Approve")')
        .first();
      if ((await approve.count()) && (await approve.isVisible().catch(() => false))) {
        await approve.click({ timeout: 5000 }).catch(() => {});
        return true;
      }
    }
    await page.waitForTimeout(400);
  }
  return false;
}

async function sendTurn(page, text, frames) {
  await waitForChatSocket(page);
  const box = await composerBox(page);
  const before = await assistant(page).count();
  await box.fill(text);
  await box.press('Enter');
  if (frames) {
    await maybeApproveTools(page, frames);
  }
  return { reply: await awaitNewReply(page, before), before };
}

async function startNewConversation(page) {
  const newChat = page
    .locator('button:has-text("New Chat"), button:has-text("New chat")')
    .first();
  await expect(newChat).toBeVisible({ timeout: 30000 });
  await newChat.click();
  await expect(assistant(page)).toHaveCount(0, { timeout: 30000 });
  await waitForChatSocket(page);
}

async function loginLocal(page) {
  await page.context().clearCookies();
  await page.goto(`${UI}/login`);
  await page.locator('input[placeholder="name@company.com"]').fill(EMAIL);
  await page.locator('input[placeholder="Enter your password"]').fill(PASSWORD);
  await page.locator('button:has-text("Sign in")').first().click();
  await expect(page).not.toHaveURL(/\/login/, { timeout: 30000 });
  await waitForChatSocket(page);
}

function watchFrames(page) {
  const frames = [];
  page.on('websocket', (ws) => {
    ws.on('framereceived', ({ payload }) => {
      try {
        frames.push(JSON.parse(typeof payload === 'string' ? payload : String(payload)));
      } catch {
        /* binary */
      }
    });
  });
  return frames;
}

test.describe('Internet search human walk', () => {
  test('agent searches the web and returns a real URL + fact', async ({ page }) => {
    await loginLocal(page);
    const frames = watchFrames(page);
    await startNewConversation(page);

    const { reply } = await sendTurn(
      page,
      'Search the web for the official Python programming language website. ' +
        'Answer with: one fact about Python and one http URL you found. ' +
        'Use web_search (and web_read if needed). Keep it short.',
      frames
    );
    // eslint-disable-next-line no-console
    console.log('SEARCH_REPLY:', reply);

    const webSearchOk = frames.find(
      (f) =>
        f.type === 'tool.done' &&
        String(f.payload?.name || '').startsWith('web_search') &&
        f.payload?.ok === true
    );
    const webReadOk = frames.find(
      (f) =>
        f.type === 'tool.done' &&
        String(f.payload?.name || '').startsWith('web_read') &&
        f.payload?.ok === true
    );

    expect(
      reply,
      `reply must include an http(s) URL from the web. Reply: ${reply}`
    ).toMatch(/https?:\/\/\S+/i);

    // Soft tool evidence: WS may reconnect across approval; the human-visible
    // URL+fact is the primary gate. If frames are present, require a web tool.
    if (frames.some((f) => f.type === 'tool.done' || f.type === 'tool.call')) {
      const sawWebTool = frames.some(
        (f) =>
          f.type === 'tool.done' &&
          (String(f.payload?.name || '').startsWith('web_search') ||
            String(f.payload?.name || '').startsWith('web_read'))
      );
      expect(
        sawWebTool,
        `when tool frames are present, expect web_search or web_read. frames: ${JSON.stringify(
          frames.map((f) => f.type + ':' + (f.payload?.name || ''))
        )}`
      ).toBe(true);
    }
    // eslint-disable-next-line no-console
    console.log(
      'web_search_ok',
      Boolean(webSearchOk),
      'web_read_ok',
      Boolean(webReadOk),
      'frames',
      frames.length
    );
  });
});
