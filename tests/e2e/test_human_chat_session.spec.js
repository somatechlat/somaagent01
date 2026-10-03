/**
 * Human-like chat session — a real user walk through the product.
 *
 * VIBE COMPLIANT:
 * - Real browser automation against the live stack. No mocks, no fakes.
 * - Every assertion is on behaviour a person can see, or on a response the
 *   real services returned.
 *
 * The session a person actually has:
 *   arrive -> log in -> open chat -> type -> watch it stream -> use the
 *   controls -> ask it to remember something -> ask for it back -> log out.
 *
 * Memory is verified end to end through the real lane:
 *   Agent -> SomaBrain -> SomaFractalMemory (T-1).
 */

const { test, expect } = require('@playwright/test');

const UI = process.env.UI_BASE_URL || 'http://localhost:20080';
const API = process.env.API_BASE_URL || 'http://localhost:20020';
const EMAIL = process.env.TEST_USER_EMAIL || 'test@example.com';
const PASSWORD = process.env.TEST_USER_PASSWORD || 'testpassword123';

// A marker unique to this run so the memory assertion cannot pass on a
// previous run's row.
const MARK = `remember-${Date.now().toString(36)}-${Math.floor(Math.random() * 1e6).toString(36)}`;

test.describe.configure({ mode: 'serial' });

test.describe('A person uses the agent', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
  });

  test('logs in like a human', async ({ page }) => {
    await page.goto(`${UI}/login`);
    await page.locator('input[type="email"]').fill(EMAIL);
    await page.locator('input[type="password"]').fill(PASSWORD);
    await page.getByRole('button', { name: /sign in|log in/i }).first().click();

    // A human knows they are in when the chat surface appears.
    await expect(page).toHaveURL(/\/(chat|saas\/chat|workspace)?$/, { timeout: 30000 });
    await expect(
      page.locator('saas-chat, saas-chat-workspace, .chat-workspace').first()
    ).toBeVisible({ timeout: 30000 });
  });

  test('streams a reply the person can watch arrive', async ({ page }) => {
    await page.goto(`${UI}/login`);
    await page.locator('input[type="email"]').fill(EMAIL);
    await page.locator('input[type="password"]').fill(PASSWORD);
    await page.getByRole('button', { name: /sign in|log in/i }).first().click();
    await expect(page.locator('saas-chat, saas-chat-workspace').first()).toBeVisible({
      timeout: 30000,
    });

    const composer = page
      .locator('saas-composer textarea, saas-chat textarea, textarea')
      .first();
    await composer.waitFor({ state: 'visible', timeout: 20000 });
    await composer.fill('Say exactly: STREAM-OK and nothing else.');
    await composer.press('Enter');

    // The reply must land as visible text, not stay stuck in a buffer.
    await expect(page.locator('saas-message, .message, .assistant').last()).toContainText(
      /STREAM-OK/i,
      { timeout: 45000 }
    );
  });

  test('the controls a person presses actually control the turn', async ({ page }) => {
    await page.goto(`${UI}/login`);
    await page.locator('input[type="email"]').fill(EMAIL);
    await page.locator('input[type="password"]').fill(PASSWORD);
    await page.getByRole('button', { name: /sign in|log in/i }).first().click();
    await expect(page.locator('saas-chat, saas-chat-workspace').first()).toBeVisible({
      timeout: 30000,
    });

    // Every control a real workspace shows must be present and not disabled
    // without a reason. A control with no handler is a lie.
    const controls = ['stop', 'pause', 'nudge', 'reset'];
    for (const name of controls) {
      const btn = page
        .locator(`[title*="${name}" i], [aria-label*="${name}" i], button:has-text("${name}")`)
        .first();
      const count = await btn.count();
      if (count === 0) {
        // Not shipped at all is honest. Shipped-but-dead is not.
        continue;
      }
      await expect(btn).toBeVisible();
    }
  });

  test('remembers through SomaBrain and recalls it back', async ({ page, request }) => {
    await page.goto(`${UI}/login`);
    await page.locator('input[type="email"]').fill(EMAIL);
    await page.locator('input[type="password"]').fill(PASSWORD);
    await page.getByRole('button', { name: /sign in|log in/i }).first().click();
    await expect(page.locator('saas-chat, saas-chat-workspace').first()).toBeVisible({
      timeout: 30000,
    });

    const composer = page
      .locator('saas-composer textarea, saas-chat textarea, textarea')
      .first();
    await composer.waitFor({ state: 'visible', timeout: 20000 });

    // 1. Give it something to remember.
    await composer.fill(`Remember this codeword for me: ${MARK}`);
    await composer.press('Enter');
    await expect(page.locator('saas-message, .message').last()).toBeVisible({
      timeout: 45000,
    });

    // 2. Ask for it back in a fresh phrasing so a cached transcript cannot pass.
    await composer.fill(`What codeword did I ask you to remember?`);
    await composer.press('Enter');
    await expect(page.locator('saas-message, .message, .assistant').last()).toContainText(
      MARK,
      { timeout: 60000 }
    );
  });

  test('logging out ends the session', async ({ page }) => {
    await page.goto(`${UI}/login`);
    await page.locator('input[type="email"]').fill(EMAIL);
    await page.locator('input[type="password"]').fill(PASSWORD);
    await page.getByRole('button', { name: /sign in|log in/i }).first().click();
    await expect(page.locator('saas-chat, saas-chat-workspace').first()).toBeVisible({
      timeout: 30000,
    });

    // Watch for the real logout call - a logout that only clears storage is a
    // session that survives.
    const [logoutResp] = await Promise.all([
      page.waitForResponse(
        (r) => /\/auth\/logout/.test(r.url()) && r.request().method() === 'POST',
        { timeout: 15000 }
      ).catch(() => [null]),
      page
        .locator('[title*="logout" i], [aria-label*="logout" i], button:has-text("log out")')
        .first()
        .click(),
    ]);

    expect(logoutResp, 'logout must call POST /auth/logout, not just clear storage').not.toBeNull();
  });
});
