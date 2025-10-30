import { test, expect } from '@playwright/test';

test('offline chat shows error toast when sending a message', async ({ page, request, baseURL }) => {
  // If the Gateway is online, skip this offline-only test.
  try {
    const probeUrl = new URL(baseURL || 'http://localhost:21016/ui');
    probeUrl.pathname = '/v1/health';
    const res = await request.get(probeUrl.toString());
    if (res.status() === 200) {
      // Gateway online; this test targets offline behavior only.
      return;
    }
  } catch {
    // proceed with offline assertions
  }
  // Don’t fail the test on console errors; we expect network-related errors when backend is offline
  const consoleMessages: string[] = [];
  page.on('console', (msg) => {
    consoleMessages.push(`[${msg.type()}] ${msg.text()}`);
  });

  // Only gate failed responses for our local static server assets
  const badStaticResponses: string[] = [];
  page.on('response', (resp) => {
    try {
      const url = new URL(resp.url());
      const isLocal = url.hostname === 'localhost' || url.hostname === '127.0.0.1';
      const isStatic = isLocal && (url.pathname.endsWith('.css') || url.pathname.endsWith('.js') || url.pathname.endsWith('.svg') || url.pathname.endsWith('.html'));
      if (isStatic && resp.status() >= 400) {
        badStaticResponses.push(`${resp.status()} ${resp.url()}`);
      }
    } catch {}
  });

  await page.goto('/index.html', { waitUntil: 'domcontentloaded' });

  // Basic UI elements should exist
  await expect(page.locator('#chat-input')).toBeVisible();
  await expect(page.locator('#send-button')).toBeVisible();

  // Type a message and click send
  await page.fill('#chat-input', 'hello world');
  await page.click('#send-button');

  // Expect an error toast from the frontend notifications due to offline backend
  const toast = page.locator('.toast-stack-container .toast-item.notification-error');
  await expect(toast).toBeVisible({ timeout: 10_000 });
  // Title often defaults to "Connection Error"
  const title = toast.locator('.toast-title');
  await expect(title).toBeVisible();

  // No failed local static responses
  expect(badStaticResponses, `Failed static responses: \n${badStaticResponses.join('\n')}`).toHaveLength(0);
});
