import { test, expect } from '@playwright/test';

// This test requires the Gateway SSE to be enabled. If the runtime config indicates
// SSE is disabled, we skip without mocking or intercepting anything.

test.describe('SSE streaming (happy path, real Gateway)', () => {
  test('connects EventSource and shows assistant response', async ({ page, request }) => {
    const base = process.env.WEB_UI_BASE_URL || process.env.BASE_URL || 'http://localhost:21016/ui';

    // Preflight: use EventSource to detect if SSE is available without blocking on a streaming response
    const sseOk = await page.evaluate(async (base) => {
      const urlBase = base.replace(/\/ui$/, '');
      const sid = Math.random().toString(36).slice(2);
      const url = `${urlBase}/v1/session/${sid}/events`;
      return await new Promise<boolean>((resolve) => {
        const es = new EventSource(url);
        const timer = setTimeout(() => {
          try { es.close(); } catch {}
          resolve(false);
        }, 2500);
        es.onopen = () => {
          clearTimeout(timer);
          try { es.close(); } catch {}
          resolve(true);
        };
        es.onerror = () => {
          clearTimeout(timer);
          try { es.close(); } catch {}
          resolve(false);
        };
      });
    }, base);
    test.skip(!sseOk, 'SSE is not enabled in this environment');

    // Go to UI
    await page.goto(`${base}/index.html`);

    // Watch for SSE GET to /v1/session/{id}/events with 200
    let sawSSE = false;
    page.on('response', async (resp) => {
      const url = resp.url();
      if (/\/v1\/session\/[^/]+\/events$/.test(new URL(url).pathname)) {
        if (resp.status() === 200) {
          sawSSE = true;
        }
      }
    });

    // Type and send a message
    const unique = `sse-ok-${Date.now()}`;
    await page.fill('#chat-input', `hello ${unique}`);
    await page.click('#send-button');

    // Expect either a Thinking bubble or a fast direct final
    const thinking = page.locator('#chat-history .message-agent');
    const finalResp = page.locator('#chat-history .message-agent-response');
    await Promise.race([
      thinking.waitFor({ state: 'visible', timeout: 10000 }),
      page.waitForFunction((sel)=>document.querySelectorAll(sel).length>=1, '#chat-history .message-agent-response', { timeout: 10000 })
    ]);
    // And the final assistant response should appear within 20s
    await page.waitForFunction((sel)=>document.querySelectorAll(sel).length>=1, '#chat-history .message-agent-response', { timeout: 20000 });

    // Expect an SSE connection attempt succeeded
    expect(sawSSE).toBeTruthy();
  });
});
