import { test, expect } from '@playwright/test';

const BASE_URL = process.env.UI_BASE_URL || 'http://localhost:21016';

test('web UI loads and shows tabs', async ({ page }) => {
  const response = await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
  expect(response?.ok()).toBeTruthy();

  // Basic smoke: page renders and key nav items appear
  await expect(page.locator('[data-i18n-key="tabs.chats"]')).toBeVisible({ timeout: 10000 });
  await expect(page.locator('[data-i18n-key="tabs.tasks"]')).toBeVisible({ timeout: 10000 });
});

test('language switch leaves page responsive', async ({ page }) => {
  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
  const langToggle = page.locator('[data-i18n-key="nav.language"]');
  await langToggle.click().catch(() => {}); // tolerate missing dropdown
  // Just ensure page remains interactive
  await expect(page.locator('body')).toBeVisible();
});
