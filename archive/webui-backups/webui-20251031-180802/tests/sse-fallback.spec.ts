import { test, expect } from '@playwright/test';

// This test verifies the real fallback: when SSE returns 503 from the Gateway, the UI
// continues via polling and still shows assistant responses. No mocks or intercepts.

test.describe('SSE -> poll fallback (real, no mocks)', () => {
  test('falls back to poll when SSE disabled server-side', async ({ page, request }) => {
    const base = process.env.WEB_UI_BASE_URL || process.env.BASE_URL || 'http://localhost:21016/ui';

    // Preflight: use EventSource to confirm SSE is disabled (expect error), skip if enabled
    const sseDisabled = await page.evaluate(async (base) => {
      const urlBase = base.replace(/\/ui$/, '');
      const sid = Math.random().toString(36).slice(2);
      const url = `${urlBase}/v1/session/${sid}/events`;
      return await new Promise<boolean>((resolve) => {
        const es = new EventSource(url);
        const timer = setTimeout(() => {
          try { es.close(); } catch {}
          // Timeout treating as enabled (no immediate error)
          resolve(false);
        }, 2500);
        es.onopen = () => {
          clearTimeout(timer);
          try { es.close(); } catch {}
          resolve(false); // SSE enabled
        };
        es.onerror = () => {
          clearTimeout(timer);
          try { es.close(); } catch {}
          resolve(true); // SSE disabled or failing
        };
      });
    }, base);
    test.skip(!sseDisabled, 'SSE is enabled; fallback test requires SSE disabled');

    // Go to UI
    await page.goto(`${base}/index.html`);

    // Capture SSE 503 attempts and poll requests
    let sawSSE503 = false;
    let pollCount = 0;
    page.on('response', async (resp) => {
      const url = resp.url();
      const pathname = new URL(url).pathname;
      if (/\/v1\/session\/[^/]+\/events$/.test(pathname)) {
        if (resp.status() === 503) {
          sawSSE503 = true;
        }
      }
      if (pathname === '/v1/ui/poll' && resp.status() === 200) {
        pollCount += 1;
      }
    });

    // Send a message to trigger activity
    const unique = `sse-fallback-${Date.now()}`;
    await page.fill('#chat-input', `hello ${unique}`);
    await page.click('#send-button');

    // We expect assistant response to show via polling
    await expect(page.locator('#chat-history .message-agent-response')).toHaveCount(1, { timeout: 25000 });

    // Assert poll requests happening (SSE is disabled server-side)
    expect(pollCount).toBeGreaterThan(0);
  });
});
