import { test, expect } from '@playwright/test';

// Validates the UI chat transport is SSE-only and avoids polling/CSRF endpoints.
// Assumes the Gateway has SSE enabled.

test.describe('UI chat transport: SSE-only', () => {
  test('does not use /v1/ui/poll or /v1/csrf while sending a message', async ({ page }) => {
    const base = process.env.WEB_UI_BASE_URL || process.env.BASE_URL || 'http://localhost:21016/ui';

    // Quickly check SSE appears to be enabled; if not, skip this spec
    const sseEnabled = await page.evaluate(async (base) => {
      const urlBase = base.replace(/\/ui$/, '');
      const sid = Math.random().toString(36).slice(2);
      const url = `${urlBase}/v1/session/${sid}/events`;
      return await new Promise<boolean>((resolve) => {
        const es = new EventSource(url);
        const timer = setTimeout(() => {
          try { es.close(); } catch {}
          // No onopen within 2.5s suggests disabled; consider not enabled
          resolve(false);
        }, 2500);
        es.onopen = () => {
          clearTimeout(timer);
          try { es.close(); } catch {}
          resolve(true); // SSE enabled
        };
        es.onerror = () => {
          clearTimeout(timer);
          try { es.close(); } catch {}
          resolve(false); // SSE disabled or failing
        };
      });
    }, base);
    test.skip(!sseEnabled, 'SSE must be enabled for this test');

    // Track forbidden endpoints
    let sawPoll = false;
    let sawCsrf = false;
    page.on('request', (req) => {
      try {
        const pathname = new URL(req.url()).pathname;
        if (pathname === '/v1/ui/poll') {
          sawPoll = true;
        }
        if (pathname === '/v1/csrf') {
          sawCsrf = true;
        }
      } catch {}
    });

    // Load the UI and perform a minimal chat send
    await page.goto(`${base}/index.html`);
    const unique = `sse-only-${Date.now()}`;
    await page.fill('#chat-input', `hello ${unique}`);
    await page.click('#send-button');

    // Expect an assistant response element to appear (transport-level success)
    await expect(page.locator('#chat-history .message-agent-response')).toHaveCount(1, { timeout: 30000 });

    // Assert we did not hit legacy endpoints
    expect(sawPoll).toBeFalsy();
    expect(sawCsrf).toBeFalsy();
  });
});
