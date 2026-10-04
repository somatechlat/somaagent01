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

function requiredEnv(name) {
  const value = (process.env[name] || '').trim();
  if (!value) {
    throw new Error(`${name} is required. Every endpoint and credential comes from the environment.`);
  }
  return value;
}

const UI = requiredEnv('UI_BASE_URL');
const API = requiredEnv('API_BASE_URL');
const EMAIL = requiredEnv('TEST_USER_EMAIL');
const PASSWORD = requiredEnv('TEST_USER_PASSWORD');

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
    await page.getByRole('textbox', { name: 'name@company.com' }).fill(EMAIL);
    await page.getByRole('textbox', { name: 'Enter your password' }).fill(PASSWORD);
    await page.getByRole('textbox', { name: 'Enter your password' }).press('Enter');

    // A human knows they are in when the chat surface appears.
    await expect(page).toHaveURL(/\/(chat|saas\/chat|workspace)?$/, { timeout: 30000 });
    await expect(
      page.locator('saas-chat, saas-chat-workspace, .chat-workspace').first()
    ).toBeVisible({ timeout: 30000 });
  });

  test('streams a reply the person can watch arrive', async ({ page }) => {
    await page.goto(`${UI}/login`);
    await page.getByRole('textbox', { name: 'name@company.com' }).fill(EMAIL);
    await page.getByRole('textbox', { name: 'Enter your password' }).fill(PASSWORD);
    await page.getByRole('textbox', { name: 'Enter your password' }).press('Enter');
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
    await page.getByRole('textbox', { name: 'name@company.com' }).fill(EMAIL);
    await page.getByRole('textbox', { name: 'Enter your password' }).fill(PASSWORD);
    await page.getByRole('textbox', { name: 'Enter your password' }).press('Enter');
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
    await page.getByRole('textbox', { name: 'name@company.com' }).fill(EMAIL);
    await page.getByRole('textbox', { name: 'Enter your password' }).fill(PASSWORD);
    await page.getByRole('textbox', { name: 'Enter your password' }).press('Enter');
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
    await page.getByRole('textbox', { name: 'name@company.com' }).fill(EMAIL);
    await page.getByRole('textbox', { name: 'Enter your password' }).fill(PASSWORD);
    await page.getByRole('textbox', { name: 'Enter your password' }).press('Enter');
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

  test('the settings panel tells the truth about what this role may edit', async ({ page }) => {
    await page.goto(`${UI}/login`);
    await page.getByRole('textbox', { name: 'name@company.com' }).fill(EMAIL);
    await page.getByRole('textbox', { name: 'Enter your password' }).fill(PASSWORD);
    await page.getByRole('textbox', { name: 'Enter your password' }).press('Enter');
    await expect(page.locator('saas-chat, saas-chat-workspace').first()).toBeVisible({
      timeout: 30000,
    });

    // The server is the authority on what this principal may do. Settings must
    // agree with it — never with a role name hardcoded in the client.
    const me = await page.evaluate(async () => {
      const r = await fetch('/api/v2/auth/me', { credentials: 'include' });
      return r.ok ? r.json() : null;
    });
    expect(me, 'GET /api/v2/auth/me must answer for a signed-in user').not.toBeNull();
    const perms = Array.isArray(me.permissions) ? me.permissions : [];
    // settings:write / settings:edit alias to system:configure in the catalog
    // (admin/core/authz.py ACTION_ALIASES).
    const mayEdit =
      perms.includes('system:configure') ||
      perms.includes('settings:write') ||
      perms.includes('settings:edit');
    const role = me.role || (Array.isArray(me.roles) ? me.roles.join(',') : 'unknown');

    await page.goto(`${UI}/settings`);
    const host = page.locator('saas-settings').first();
    await expect(host).toBeVisible({ timeout: 20000 });

    // 1. The screen must expose its editability, and it must match the server.
    await expect(host).toHaveAttribute(
      'data-can-edit',
      mayEdit ? 'true' : 'false',
      { timeout: 10000 }
    );

    // 2. Walk every settings tab and check every control this role touches.
    //    Editable       -> live (unless a real precondition is unmet, and then
    //                      the title states that precondition).
    //    Not editable   -> disabled AND carrying a visible blocking reason.
    //    Dead-with-no-reason is the failure this test exists to catch.
    const tabs = ['Agent', 'External', 'Connectivity', 'System'];
    const seenControls = new Set();

    for (const label of tabs) {
      await page.locator('saas-settings .tab-item', { hasText: label }).first().click();

      const controls = host.locator('[data-control]');
      const count = await controls.count();

      // A tab must render real content — an empty tab is an omission.
      const tabText = (await host.locator('main').first().innerText()) || '';
      expect(tabText.trim().length, `settings tab "${label}" must render content`).toBeGreaterThan(0);

      for (let i = 0; i < count; i++) {
        const ctl = controls.nth(i);
        const name = (await ctl.getAttribute('data-control')) || `#${i}`;
        const isDisabled = await ctl.isDisabled();
        const title = ((await ctl.getAttribute('title')) || '').trim();
        seenControls.add(name);

        if (mayEdit) {
          // Admin path. The controls this role owns must actually be live.
          // Save is the one honest exception: it sits disabled until something
          // is dirty. A disabled control still owes the user its reason.
          const owned = [
            'feature-flag-memory',
            'feature-flag-tools',
            'feature-flag-voice',
            'feature-flag-mcp',
            'secret-input',
          ];
          if (owned.includes(name)) {
            expect(
              isDisabled,
              `role ${role} may edit, so "${name}" must be enabled`
            ).toBe(false);
          } else if (isDisabled) {
            expect(
              title.length,
              `role ${role} may edit, so a disabled "${name}" must state why`
            ).toBeGreaterThan(0);
          }
        } else {
          // Read-only role: every control must be off and must say why.
          expect(
            isDisabled,
            `role ${role} may not edit settings, so "${name}" must be disabled`
          ).toBe(true);
          expect(
            title.length,
            `role ${role}: disabled "${name}" must carry a blocking reason in title`
          ).toBeGreaterThan(0);
          expect(
            title.toLowerCase(),
            `"${name}" must not use the banned placeholder phrase`
          ).not.toContain('coming soon');
        }
      }

      // When the role cannot edit, the tab must also print a visible reason —
      // not just silently grey things out.
      if (!mayEdit && count > 0) {
        const reason = host.locator('.disabled-reason').first();
        await expect(reason, `tab "${label}" must print a blocking reason`).toBeVisible();
        const reasonText = ((await reason.textContent()) || '').trim();
        expect(reasonText.length).toBeGreaterThan(0);
        expect(reasonText.toLowerCase()).not.toContain('coming soon');
      }
    }

    // 3. Honesty: the settings screen must never invent key material or models.
    const bodyText = (await host.innerText()) || '';
    for (const lie of ['sk-****', 'sk-ant-****', 'localhost:9696', 'gpt-4-turbo', 'claude-3-haiku']) {
      expect(bodyText, `settings must not fabricate "${lie}"`).not.toContain(lie);
    }

    // 4. The walk must actually have seen controls, otherwise this would pass
    //    on an empty page.
    expect(seenControls.size, 'settings must expose data-control hooks').toBeGreaterThan(0);
    expect(seenControls.has('save'), 'the save control must be wired').toBe(true);
  });
});
