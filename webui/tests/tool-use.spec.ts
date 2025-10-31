import { test, expect } from '@playwright/test';

// Validates UI-triggered tool execution via the "/tool" slash command.
// We avoid mocks: the test lists real tools from the Gateway, then triggers one and
// asserts a tool message appears in the chat stream.

test.describe('UI tool use via /tool slash command', () => {
  test('enqueues tool.request and observes a tool result (session events)', async ({ page, request }) => {
    const base = process.env.WEB_UI_BASE_URL || process.env.BASE_URL || 'http://localhost:21016/ui';
    const apiBase = base.replace(/\/?ui\/?$/, '').replace(/\/$/, '');

    // Preflight: verify SSE is enabled; if not, skip (this spec targets live SSE only)
    const sseEnabled = await page.evaluate(async (base) => {
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
    test.skip(!sseEnabled, 'SSE must be enabled for UI tool test');

    // Discover an available tool from the live Gateway
    const toolsResp = await request.get(`${apiBase}/v1/tools`);
    test.skip(!toolsResp.ok(), `Tools endpoint unavailable: HTTP ${toolsResp.status()}`);
    const toolsJson = await toolsResp.json();
    const tools: Array<{ name: string }> = (toolsJson?.tools || []) as any;
    test.skip(!tools || tools.length === 0, 'No tools available in runtime');

    // Prefer a deterministic low-risk tool
    const preferred = ['echo', 'timestamp'];
    let toolName = tools.find(t => preferred.includes(t.name))?.name || tools[0].name;

    // Build a valid slash command
    let args: any = {};
    if (toolName === 'echo') {
      args = { text: `hello-from-tool-${Date.now()}` };
    } else if (toolName === 'timestamp') {
      args = {}; // optional format
    } else {
      // Best-effort empty args; many tools accept object with optional fields
      args = {};
    }

    const cmd = `/tool ${toolName} ${JSON.stringify(args)}`;

    // Track forbidden legacy endpoints to ensure SSE-only transport and capture session id from SSE URL
    let sawPoll = false;
    let sawCsrf = false;
    let sessionIdFromSSE: string | null = null;
    page.on('request', (req) => {
      try {
        const pathname = new URL(req.url()).pathname;
        if (pathname === '/v1/ui/poll') sawPoll = true;
        if (pathname === '/v1/csrf') sawCsrf = true;
        const m = pathname.match(/^\/(?:v1)\/session\/([^/]+)\/events$/);
        if (m) sessionIdFromSSE = m[1];
      } catch {}
    });

    await page.goto(`${base}/index.html`);
    await page.fill('#chat-input', cmd);
    await page.click('#send-button');

    // Expect a success toast indicating enqueue
    const toast = page.locator('.toast-stack-container .toast-item');
    await expect(toast.first()).toContainText(/Tool request/i, { timeout: 10000 });

    // Expect a tool.start lifecycle message in the UI
    const toolHeading = page.locator('#chat-history .message-tool .msg-heading h4');
    await expect(toolHeading).toContainText(new RegExp(`^Tool: ${toolName}$`, 'i'), { timeout: 15000 });
    // The start event may be elided if result arrives immediately; heading is sufficient here.

    // Use the session id observed from SSE to poll server-side session events for a matching tool result
    const sid = sessionIdFromSSE;
    test.skip(!sid, 'No session id captured from SSE');
    const deadline = Date.now() + 25_000;
    let found = false;
    while (Date.now() < deadline && !found) {
      const ev = await request.get(`${apiBase}/v1/sessions/${sid}/events?limit=200`);
      if (ev.ok()) {
        try {
          const body = await ev.json();
          const items: any[] = body?.events || [];
          const hits = items.filter((e: any) => {
            const p = e?.payload || {};
            return p?.tool_name === toolName && (!!p?.status || !!p?.payload);
          });
          if (hits.length > 0) {
            found = true;
            break;
          }
        } catch {}
      }
      await page.waitForTimeout(500);
    }
    expect(found).toBeTruthy();

    // Ensure we did not hit legacy polling or CSRF
    expect(sawPoll).toBeFalsy();
    expect(sawCsrf).toBeFalsy();
  });
});
