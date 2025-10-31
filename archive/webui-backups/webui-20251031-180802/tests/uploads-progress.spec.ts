import { test, expect } from '@playwright/test';

// Validates that uploading a file produces an uploads progress UI block.
// This test relies on the live Gateway /v1/uploads emitting uploads.progress over SSE.

test.describe('Uploads progress UI', () => {
  test('shows progress bar during file upload', async ({ page }) => {
    const base = process.env.WEB_UI_BASE_URL || process.env.BASE_URL || 'http://localhost:21016/ui';

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
    test.skip(!sseEnabled, 'SSE must be enabled for uploads progress test');

    await page.goto(`${base}/index.html`);

    // Prepare a small in-memory file
    const payload = {
      name: `large-${Date.now()}.bin`,
      mimeType: 'application/octet-stream',
      // ~2MB buffer to increase the chance of progress events
      buffer: Buffer.alloc(2 * 1024 * 1024, 97),
    };

    // Attach file to the hidden file input
    await page.setInputFiles('#file-input', payload);

    // Send a short message
    await page.fill('#chat-input', 'file test');
    await page.click('#send-button');

    // Expect an uploads UI block to appear (either Uploading or Uploaded)
    const heading = page.locator('#chat-history .message-upload .msg-heading h4');
    await expect(heading).toContainText(/Uploading:|Uploaded:/i, { timeout: 25000 });

    // Expect a progress bar element
    const bar = page.locator('#chat-history .message-upload .upload-progress-bar');
    await expect(bar).toHaveCount(1);
  });
});
