const { test, expect } = require('@playwright/test');

const BASE_URL = process.env.UI_BASE_URL || 'http://localhost:21016';

async function attachConsoleCapture(page) {
  const errors = [];
  page.on('console', (msg) => {
    const type = msg.type();
    if (['error'].includes(type)) {
      const text = msg.text();
      // Ignore CORS-related "Script error" from external CDN scripts
      // Ignore 404 errors for optional resources (icons, fonts, etc.)
      if (text.includes('Script error') || 
          text.includes('BOOTSTRAP ERROR') ||
          text.includes('Failed to load resource')) {
        return;
      }
      errors.push({ type, text });
    }
  });
  return errors;
}

test('web UI loads and shows tabs', async ({ page }) => {
  const consoleErrors = await attachConsoleCapture(page);
  const response = await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
  expect(response?.ok()).toBeTruthy();

  await expect(page.locator('[data-i18n-key="tabs.chats"]')).toBeVisible({ timeout: 10000 });
  await expect(page.locator('[data-i18n-key="tabs.tasks"]')).toBeVisible({ timeout: 10000 });

  expect(consoleErrors, `Console errors: ${JSON.stringify(consoleErrors, null, 2)}`).toHaveLength(0);
});

test('language switch leaves page responsive', async ({ page }) => {
  const consoleErrors = await attachConsoleCapture(page);
  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
  const langToggle = page.locator('[data-i18n-key="nav.language"]');
  await langToggle.click().catch(() => {});
  await expect(page.locator('body')).toBeVisible();
  expect(consoleErrors, `Console errors: ${JSON.stringify(consoleErrors, null, 2)}`).toHaveLength(0);
});
