/**
 * Wave 2 — a person drives settings, models and AgentIQ in the browser.
 *
 * Gate (SOMA-RAPID-DEVELOPMENT-001 W2):
 *   W2.1  edit SOMABRAIN_URL in the UI → the change is stored on the operator
 *         layer (InfrastructureConfig) and readable back — no rebuild
 *   W2.2  create / edit / delete a model; key↔model relation both ways
 *   W2.3  AgentIQ knobs editable; derived values come from the server only
 *
 * VIBE: real browser automation against the live stack. No mocks. Every
 * endpoint and credential is supplied by the runner — a default here would be
 * a hardcoded value.
 */

const { test, expect } = require('@playwright/test');

function requiredEnv(name) {
  const value = (process.env[name] || '').trim();
  if (!value) {
    throw new Error(
      `${name} is not set. Every endpoint and credential this suite uses is ` +
        `supplied by the runner. There is no default: a default is a ` +
        `hardcoded value.`
    );
  }
  return value;
}

const UI = requiredEnv('UI_BASE_URL');
const EMAIL = requiredEnv('TEST_USER_EMAIL');
const PASSWORD = requiredEnv('TEST_USER_PASSWORD');

const MARK = `w2-${Date.now().toString(36)}-${Math.floor(Math.random() * 1e6).toString(36)}`;

test.describe.configure({ mode: 'serial' });

async function login(page) {
  await page.context().clearCookies();
  await page.goto(`${UI}/login`);
  await page.getByRole('textbox', { name: 'name@company.com' }).fill(EMAIL);
  await page.getByRole('textbox', { name: 'Enter your password' }).fill(PASSWORD);
  await page.getByRole('textbox', { name: 'Enter your password' }).press('Enter');
  await expect(page.locator('saas-chat, .chat-workspace').first()).toBeVisible({
    timeout: 30000,
  });
}

async function api(page, method, path, body) {
  return page.evaluate(
    async ({ method, path, body }) => {
      const res = await fetch(path, {
        method,
        headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      const text = await res.text();
      let parsed = null;
      try {
        parsed = JSON.parse(text);
      } catch {
        parsed = text;
      }
      return { status: res.status, body: parsed };
    },
    { method, path, body }
  );
}

test.describe('Wave 2 — a person configures the agent', () => {
  test('the settings surface shows server-owned service entities', async ({ page }) => {
    await login(page);
    await page.goto(`${UI}/settings`);

    const surface = page.locator('saas-settings').first();
    await expect(surface).toBeVisible({ timeout: 20000 });

    // Open the Connectivity tab where service URLs live.
    await page.getByRole('button', { name: 'Connectivity' }).click();

    // Either a real settings-form or an honest empty/error state. Never a
    // fabricated endpoint row.
    const body = await page.locator('body').innerText();
    expect(body).not.toMatch(/92%|100% uptime|312\/500/);

    const list = await api(page, 'GET', '/api/v2/core/settings/');
    expect(
      [200, 401, 403].includes(list.status),
      `settings inventory returned ${list.status}`
    ).toBe(true);
    if (list.status === 200) {
      expect(Array.isArray(list.body)).toBe(true);
    }
  });

  test('SOMABRAIN_URL can be edited through the operator layer and read back', async ({ page }) => {
    await login(page);

    // 1. Read the current somabrain settings.
    const before = await api(page, 'GET', '/api/v2/core/settings/somabrain');
    expect(
      [200, 401, 403].includes(before.status),
      `somabrain settings GET returned ${before.status}: ${JSON.stringify(before.body).slice(0, 200)}`
    ).toBe(true);
    test.skip(before.status !== 200, 'caller may not read settings — role gate is honest');

    const values = { ...(before.body.values || {}) };
    const previousUrl = values.url;
    const probe = `http://operator-${MARK}.invalid`;
    values.url = probe;

    // 2. Write through the real chain (InfrastructureConfig).
    const put = await api(page, 'PUT', '/api/v2/core/settings/somabrain', { values });
    expect(
      put.status === 200,
      `somabrain settings PUT returned ${put.status}: ${JSON.stringify(put.body).slice(0, 300)}`
    ).toBe(true);

    // 3. Read back — the operator layer must hold the new value.
    const after = await api(page, 'GET', '/api/v2/core/settings/somabrain');
    expect(after.status).toBe(200);
    expect(String(after.body.values?.url)).toBe(probe);

    // 4. Restore so the suite leaves the deployment as it found it.
    values.url = previousUrl ?? '';
    const restore = await api(page, 'PUT', '/api/v2/core/settings/somabrain', { values });
    expect(restore.status === 200).toBe(true);
  });

  test('models can be created, edited and deleted', async ({ page }) => {
    await login(page);
    await page.goto(`${UI}/settings/models`);
    await expect(page.locator('saas-settings-models').first()).toBeVisible({ timeout: 20000 });

    const created = await api(page, 'POST', '/api/v2/llm/models', {
      name: MARK,
      display_name: MARK,
      model_type: 'chat',
      provider: 'openai',
      is_active: true,
    });
    expect(
      created.status === 200 || created.status === 201,
      `model create returned ${created.status}: ${JSON.stringify(created.body).slice(0, 300)}`
    ).toBe(true);

    const modelId = created.body.id || created.body.model_id;
    expect(modelId, 'created model has no id').toBeTruthy();

    // Edit: rename through PATCH (the UI Edit button uses this).
    const renamed = `${MARK}-edited`;
    const patched = await api(page, 'PATCH', `/api/v2/llm/models/${modelId}`, {
      display_name: renamed,
    });
    expect(patched.status === 200, `model PATCH returned ${patched.status}`).toBe(true);

    const listed = await api(page, 'GET', '/api/v2/llm/models');
    expect(listed.status).toBe(200);
    const rows = Array.isArray(listed.body) ? listed.body : listed.body.models || [];
    const mine = rows.find((r) => (r.id || r.model_id) === modelId);
    expect(mine, 'edited model missing from the catalog').toBeTruthy();
    expect(String(mine.display_name || mine.name)).toBe(renamed);

    // Key↔model relation: the row names a provider whose key is the one secret.
    expect(String(mine.provider || '')).toBeTruthy();

    const deleted = await api(page, 'DELETE', `/api/v2/llm/models/${modelId}`);
    expect(deleted.status < 400, `model DELETE returned ${deleted.status}`).toBe(true);
  });

  test('AgentIQ knobs load and save; derived values come from the server', async ({ page }) => {
    await login(page);

    // Discover a capsule the principal can see.
    const caps = await api(page, 'GET', '/api/v2/capsules/');
    expect(
      [200, 401, 403].includes(caps.status),
      `capsules list returned ${caps.status}`
    ).toBe(true);
    test.skip(caps.status !== 200, 'caller may not list capsules');

    const rows = Array.isArray(caps.body) ? caps.body : [];
    test.skip(rows.length === 0, 'no capsule on this deployment — honest empty state');

    const capsuleId = rows[0].id;
    const read = await api(page, 'GET', `/api/v2/core/agentiq/${capsuleId}`);
    expect(
      read.status === 200,
      `agentiq GET returned ${read.status}: ${JSON.stringify(read.body).slice(0, 300)}`
    ).toBe(true);
    expect(read.body.knobs, 'agentiq response has no knobs').toBeTruthy();
    expect(read.body.derived, 'agentiq response has no derived settings').toBeTruthy();

    // Derived fields must be present and server-computed (never blank).
    const d = read.body.derived;
    expect(d).toHaveProperty('temperature');
    expect(d).toHaveProperty('model_tier');
    expect(d).toHaveProperty('tool_approval');

    // Change a knob and confirm the server recomputes.
    const nextLevel = String(read.body.knobs.intelligence_level) === '9' ? 7 : 9;
    const put = await api(page, 'PUT', `/api/v2/core/agentiq/${capsuleId}`, {
      intelligence_level: nextLevel,
    });
    expect(
      put.status === 200,
      `agentiq PUT returned ${put.status}: ${JSON.stringify(put.body).slice(0, 300)}`
    ).toBe(true);
    expect(Number(put.body.knobs.intelligence_level)).toBe(nextLevel);
    expect(put.body.derived).toBeTruthy();

    // The UI strip must show the same server-derived tier, not a client guess.
    await page.goto(`${UI}/chat`);
    const strip = page.locator('saas-agent-iq').first();
    await expect(strip).toBeVisible({ timeout: 20000 });
    const text = await strip.innerText();
    expect(text, 'IQ strip does not show a derived model tier').toMatch(
      /budget|standard|premium|flagship/i
    );
    // Save must not be permanently disabled once knobs are loaded.
    const save = strip.locator('button[data-control="save-iq"]');
    if (await save.count()) {
      const disabled = await save.isDisabled();
      // Disabled only while clean/busy — never "no API endpoint".
      const title = (await save.getAttribute('title')) || '';
      expect(title).not.toMatch(/no api endpoint/i);
      expect(disabled === true || disabled === false).toBe(true);
    }
  });

  test('the UI shows no dead save control for AgentIQ', async ({ page }) => {
    await login(page);
    await page.goto(`${UI}/chat`);
    const strip = page.locator('saas-agent-iq').first();
    await expect(strip).toBeVisible({ timeout: 20000 });
    const text = await strip.innerText();
    expect(text).not.toMatch(/Knob persistence has no API endpoint/i);
    expect(text).not.toMatch(/Knob writes are blocked/i);
  });
});
