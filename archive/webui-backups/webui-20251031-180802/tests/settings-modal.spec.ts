import { test, expect } from '@playwright/test';

// Opens Settings modal and verifies provider input field exists (shape-only; does not save).

test('Settings modal shows API provider fields', async ({ page }) => {
  const base = process.env.WEB_UI_BASE_URL || process.env.BASE_URL || 'http://localhost:21016/ui';
  await page.goto(`${base}/index.html`);

  // Try opening via button; if not found, call the proxy directly
  const btn = page.locator('#settings');
  if (await btn.count()) {
    await btn.click();
  } else {
    await page.evaluate(() => (window as any).settingsModalProxy?.openModal?.());
  }

  // Wait for modal to appear and render sections (teleported to <body>)
  await expect(page.locator('.modal-container:visible').first()).toBeVisible();

  // Look for any input of type password or text with id containing 'api_key'
  const input = page.locator('.modal-container:visible input[id*="api_key_"], .modal-container:visible input[type="password"], .modal-container:visible input[type="text"]');
  await expect(input.first()).toBeVisible();
});
