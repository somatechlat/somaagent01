import { test, expect } from '@playwright/test';

// Strict smoke: load a static page that doesn't call backend APIs on load,
// fail on console errors and on any >=400 responses for static assets.
test('login page loads without console errors and static assets succeed', async ({ page }) => {
  const errors: string[] = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });

  const badResponses: string[] = [];
  page.on('response', (resp) => {
    try {
      const url = new URL(resp.url());
      const isLocal = url.hostname === 'localhost' || url.hostname === '127.0.0.1';
      // Only enforce for our static server; external/CDN fonts or images are ignored.
      if (isLocal && resp.status() >= 400) {
        badResponses.push(`${resp.status()} ${resp.url()}`);
      }
    } catch {
      /* ignore */
    }
  });

  await page.goto('/login.html', { waitUntil: 'domcontentloaded' });

  // Basic presence checks
  await expect(page.locator('text=Agent Zero')).toBeVisible();
  await expect(page.locator('form.login-form')).toBeVisible();

  // Ensure CSS and favicon requested are OK
  const linkHrefs = await page.$$eval('link[rel="stylesheet"], link[rel="icon"]', els => els.map(e => (e as HTMLLinkElement).href));
  expect(linkHrefs.length).toBeGreaterThan(0);

  // No console errors
  expect(errors, `Console errors: \n${errors.join('\n')}`).toHaveLength(0);

  // No failed static responses
  expect(badResponses, `Failed responses: \n${badResponses.join('\n')}`).toHaveLength(0);
});
