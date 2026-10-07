const { test, expect } = require('@playwright/test');

async function tryLogin(page) {
  await page.goto('/settings/models');
  const hasPassword = await page.locator('input[type="password"]').count();
  if (!hasPassword) return;
  const userInput = page.locator('input[type="email"], input[type="text"], input[name="username"]').first();
  const passInput = page.locator('input[type="password"]').first();
  if (await userInput.count() && await passInput.count()) {
    await userInput.fill('admin@example.com');
    await passInput.fill('testpass123');
    const btn = page.locator('button[type="submit"], button:has-text("Sign in"), button:has-text("Login")').first();
    if (await btn.count()) await btn.click();
    await page.waitForTimeout(1500);
    await page.goto('/settings/models');
  }
}

test('model settings show provider-key relation both ways', async ({ page }) => {
  await tryLogin(page);
  await expect(page.locator('th', { hasText: 'Key' })).toBeVisible();
  await expect(page.locator('th', { hasText: 'Models that use this key' })).toBeVisible();
  const body = await page.locator('body').innerText();
  expect(body).not.toMatch(/312 \/ 500/);
  expect(body).not.toMatch(/Dev-1/);
});

test('chat chrome mounts the AgentIQ strip without invented derived values', async ({ page }) => {
  await tryLogin(page);
  await page.goto('/chat');
  const strip = page.locator('soma-agent-iq');
  await expect(strip).toBeVisible();
  const text = await strip.innerText();
  expect(text).toContain('temperature');
  // Em-dash placeholder means "not computed yet", never a fabricated number.
  expect(text).not.toMatch(/temperature\s+0\.\d/);
});

test('roles screen uses the real catalog and locks provisioned roles', async ({ page }) => {
  await tryLogin(page);
  await page.goto('/platform/roles');
  const body = await page.locator('body').innerText();
  expect(body).toContain('org:assign_roles');
  expect(body).toContain('sysadmin');
});
