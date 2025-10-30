import { test, expect } from '@playwright/test';

// Ensures UI does not make legacy network calls (polling or CSRF)
// Assumes SSE is enabled on the Gateway.

test.describe('No legacy network paths (SSE-only)', () => {
  test('chat flow avoids /v1/ui/poll and /v1/csrf', async ({ page }) => {
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
    test.skip(!sseEnabled, 'SSE must be enabled for the no-legacy test');

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
    const unique = `no-legacy-${Date.now()}`;
    await page.fill('#chat-input', `hello ${unique}`);
    await page.click('#send-button');

    // Expect an assistant response element to appear (transport-level success)
    await expect(page.locator('#chat-history .message-agent-response')).toHaveCount(1, { timeout: 30000 });

    // Assert we did not hit legacy endpoints
    expect(sawPoll).toBeFalsy();
    expect(sawCsrf).toBeFalsy();
  });
});
