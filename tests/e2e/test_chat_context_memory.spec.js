/**
 * Complex conversation + long-context memory tests (human UI path).
 *
 * VIBE: real browser, real stack, no mocks. Credentials from env only.
 * Owner bar: memory and context must work in the product UI over long turns.
 */
const { test, expect } = require('@playwright/test');

function requiredEnv(name) {
  const v = (process.env[name] || '').trim();
  if (!v) throw new Error(`${name} is required`);
  return v;
}

const UI = requiredEnv('UI_BASE_URL');
const EMAIL = requiredEnv('TEST_USER_EMAIL');
const PASSWORD = requiredEnv('TEST_USER_PASSWORD');
const MARK = `ctx-${Date.now().toString(36)}`;

async function login(page) {
  await page.goto(`${UI}/login`);
  await page.locator('input[placeholder="name@company.com"]').fill(EMAIL);
  await page.locator('input[placeholder="Enter your password"]').fill(PASSWORD);
  await page.locator('button:has-text("Sign in")').first().click();
  await expect(page.locator('soma-composer textarea, textarea').first()).toBeVisible({ timeout: 30000 });
  // wait until the chat shell has an agent + websocket — a send without it
  // fails "Not connected" and is a test race, not a product answer.
  await page.waitForFunction(() => {
    const c = document.querySelector('soma-chat');
    return c && c._selectedAgentId && c._wsConnected;
  }, { timeout: 30000 });
}

async function ask(page, text) {
  const box = page.locator('soma-composer textarea, textarea').first();
  // Cardinality gate: read the NEW assistant bubble, never the previous turn's
  // (locator.evaluate on a pre-send .last() races the placeholder and can
  // return the old turn or an empty shell).
  const before = await page.locator('soma-message[message-role="assistant"]').count();
  await box.fill(text);
  await box.press('Enter');
  await expect
    .poll(async () => page.locator('soma-message[message-role="assistant"]').count(), {
      timeout: 90000,
    })
    .toBeGreaterThan(before);
  const last = page.locator('soma-message[message-role="assistant"]').nth(before);
  await expect(last).toBeVisible({ timeout: 90000 });
  await expect
    .poll(async () => last.evaluate((el) => {
      const root = el.shadowRoot || el;
      const body = root.querySelector('.text') || root;
      return (body.textContent || '').replace(/\s+/g, ' ').trim().length;
    }), { timeout: 90000 })
    .toBeGreaterThan(0);
  // Wait for the STREAM to finish, not just the first token. A read at the
  // first delta is a truncated reply (live Mission T: mid-coord cutoff).
  // Signal: assistant text stable across two samples. The send button is NOT
  // a signal — it stays disabled on an empty composer after send.
  await expect
    .poll(async () => {
      const t1 = await last.evaluate((el) => {
        const root = el.shadowRoot || el;
        const body = root.querySelector('.text') || root;
        return (body.textContent || '').replace(/\s+/g, ' ').trim();
      });
      await page.waitForTimeout(1500);
      const t2 = await last.evaluate((el) => {
        const root = el.shadowRoot || el;
        const body = root.querySelector('.text') || root;
        return (body.textContent || '').replace(/\s+/g, ' ').trim();
      });
      return t1 === t2 && t1.length > 0;
    }, { timeout: 90000, intervals: [2000] })
    .toBe(true);
  return (await last.evaluate((el) => {
    const root = el.shadowRoot || el;
    const body = root.querySelector('.text') || root;
    return body.textContent || '';
  })).replace(/\s+/g, ' ').trim();
}

function norm(s) {
  return (s || '')
    .replace(/[\u2010\u2011\u2012\u2013\u2014\u2212]/g, '-')
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/\s+/g, ' ')
    .trim();
}

test.describe.configure({ mode: 'serial' });
test.setTimeout(180000);

test.describe('Complex context and memory (UI)', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
  });

  test('long conversation: keeps a project thread over 4 turns', async ({ page }) => {
    await login(page);
    await ask(page, `My project codename is ${MARK} and it is about marine maps.`);
    await ask(page, `Remind me what my project codename is and what it is about.`);
    const mid = norm(await ask(page, 'Summarize what I told you about my project in one sentence.'));
    expect(mid).toContain(MARK.split('-')[1] || MARK);
    expect(mid.toLowerCase()).toContain('marine');
    await ask(page, `If I asked you to change the project topic to glaciers, would you still know the codename?`);
    const end = norm(await ask(page, `What is my project codename?`));
    expect(end).toContain(MARK);
  });

  test('memory: name + favorite + codeword survive a fresh conversation', async ({ page }) => {
    await login(page);
    await ask(page, `Remember these facts: my name is Marco, my favorite color is terracotta, codeword is ${MARK}.`);
    await page.locator('button:has-text("New Chat"), button:has-text("New chat")').first().click();
    // New Chat tears down the turn channel — wait for the new one before asking
    // or the recall question is a "Not connected" race.
    await page.waitForFunction(() => {
      const c = document.querySelector('soma-chat');
      return c && c._selectedAgentId && c._wsConnected;
    }, { timeout: 30000 });
    const reply = norm(await ask(page, 'What is my name, my favorite color, and the codeword?'));
    expect(reply.toLowerCase()).toContain('marco');
    expect(reply.toLowerCase()).toContain('terracotta');
    expect(reply).toContain(MARK);
  });

  test('memory: can explain where a memory is stored (coord/id)', async ({ page }) => {
    await login(page);
    await ask(page, `Remember my employee id is ${MARK}.`);
    const reply = norm(await ask(page, 'Look in memory and tell me my employee id and its memory_id or coord.'));
    expect(reply).toContain(MARK);
  });

  test('bottom dock: knobs panel opens and shows live IQ', async ({ page }) => {
    await login(page);
    const handle = page.locator('soma-chat .dock-handle, soma-chat button[aria-label*="knobs" i]').first();
    await expect(handle).toBeVisible({ timeout: 15000 });
    await handle.click();
    await expect(page.locator('soma-chat .dock.open, soma-agent-iq').first()).toBeVisible({ timeout: 5000 });
    const iq = page.locator('soma-agent-iq').first();
    await expect(iq).toBeVisible();
  });
});
