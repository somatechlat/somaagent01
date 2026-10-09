/**
 * Human walk: casual chat must NEVER claim a name was erased.
 *
 * Pins the bug: after normal remember / ask-name turns the model said
 * "your name has been removed from my memory". Uses the same live-browser
 * helpers as test_memory_human_name (cardinality-gated replies, real WS).
 *
 * Walk:
 *   1. local login
 *   2. "My name is Zoe. Remember it."
 *   3. new chat → "What is my name?" → reply must contain Zoe
 *   4. FAIL if reply matches erasure-lie patterns (no user erase request)
 *   5. "Please delete the memory of my name" → must not claim success
 *      unless memory_forget returned forgotten=true
 *
 * Env: UI_BASE_URL, TEST_USER_EMAIL, TEST_USER_PASSWORD
 */

const { test, expect } = require('@playwright/test');

const UI = process.env.UI_BASE_URL || 'http://localhost:20080';
const EMAIL = process.env.TEST_USER_EMAIL || 'test@soma.dev';
const PASSWORD = process.env.TEST_USER_PASSWORD || 'testpassword123';
const TURN_TIMEOUT_MS = 120000;

const NAME = 'Zoe';

const ERASURE_LIE =
  /removed from my (memory|brain)|deleted (your|the) (name|memory)|no longer (know|remember) your name|forget(ten)? (your|the) name/i;

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
  const attach = (ws) => {
    ws.on('framereceived', ({ payload }) => {
      try {
        frames.push(JSON.parse(typeof payload === 'string' ? payload : String(payload)));
      } catch {
        /* binary */
      }
    });
  };
  page.on('websocket', attach);
  return frames;
}

function silentForgetOk(frames) {
  return frames.find(
    (f) =>
      f.type === 'tool.done' &&
      String(f.payload?.name || '').startsWith('memory_forget') &&
      (f.payload?.ok === true || f.payload?.result?.forgotten === true)
  );
}

test.describe('No wrongful memory erasure claim', () => {
  test('remember then ask name — reply must not claim erasure', async ({ page }) => {
    await loginLocal(page);
    const frames = watchFrames(page);

    const remember = await sendTurn(
      page,
      `My name is ${NAME}. Remember it. Reply with one short sentence.`
    );
    // eslint-disable-next-line no-console
    console.log('REMEMBER_REPLY:', remember.reply);
    expect(
      silentForgetOk(frames),
      'memory_forget must not auto-run on remember'
    ).toBeUndefined();

    await startNewConversation(page);
    const ask = await sendTurn(page, 'What is my name? Answer briefly.');
    // eslint-disable-next-line no-console
    console.log('ASK_REPLY:', ask.reply);

    expect(ask.reply, 'reply must mention the stored name').toMatch(new RegExp(NAME, 'i'));
    expect(
      ask.reply,
      `casual name question must not claim erasure. Reply: ${ask.reply}`
    ).not.toMatch(ERASURE_LIE);
    expect(
      silentForgetOk(frames),
      'memory_forget must not run on "what is my name"'
    ).toBeUndefined();
  });

  test('explicit delete request must not fake success', async ({ page }) => {
    await loginLocal(page);
    const frames = watchFrames(page);

    await sendTurn(page, `My name is ${NAME}. Remember it.`);

    await startNewConversation(page);
    frames.length = 0;
    const del = await sendTurn(
      page,
      'Please delete the memory of my name from long-term memory now.'
    );
    // eslint-disable-next-line no-console
    console.log('DELETE_REPLY:', del.reply);

    const okForget = silentForgetOk(frames);
    const approval = frames.find(
      (f) =>
        f.type === 'tool.approval_request' &&
        String(f.payload?.name || '').startsWith('memory_forget')
    );

    if (okForget && !approval) {
      throw new Error(
        `memory_forget executed without approval_request: ${JSON.stringify(
          okForget.payload
        )}`
      );
    }

    if (!okForget) {
      expect(
        del.reply,
        `must not claim successful erase when forget did not return forgotten=true. Reply: ${del.reply}`
      ).not.toMatch(/has been removed|successfully deleted|is (now )?forgotten/i);
    }
  });
});
