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

  // Wait for modal to appear and render sections
  await expect(page.locator('#settingsModal .modal-container')).toHaveCount(1);

  // Look for any input of type password or text with id containing 'api_key'
  const input = page.locator('#settingsModal input[id*="api_key_"], #settingsModal input[type="password"], #settingsModal input[type="text"]');
  await expect(input.first()).toBeVisible();
});
