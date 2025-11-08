// Basic Playwright test for upload UI
// Assumes dev server running at http://localhost:21016 serving webui
import { test, expect } from '@playwright/test';

const BASE = process.env.GATEWAY_BASE || 'http://localhost:21016';

async function attachFile(page, selector, filePath) {
  const input = await page.locator(selector);
  await input.setInputFiles(filePath);
}

test('single small file upload shows progress and completes', async ({ page }) => {
  await page.goto(BASE + '/');
  // Ensure attachments container exists
  const fileInput = page.locator('#chat-file-input');
  await expect(fileInput).toBeVisible();

  // Create a temporary file via evaluate (in-memory) by using input
  // We can't create local disk file easily here; rely on setInputFiles with generated Buffer
  const tmpPath = 'tests/playwright/fixtures/small.txt';
  // The test runner should ensure this file exists; fallback create via fs
  const fs = require('fs');
  if (!fs.existsSync(tmpPath)) {
    fs.mkdirSync('tests/playwright/fixtures', { recursive: true });
    fs.writeFileSync(tmpPath, 'hello world '.repeat(100));
  }

  await fileInput.setInputFiles(tmpPath);
  // Wait for preview item
  const preview = page.locator('.attachment-item');
  await expect(preview).toHaveCount(1);

  // Trigger send (assuming send button id #send-message)
  const sendBtn = page.locator('#send-message');
  await sendBtn.click();

  // Progress bar should appear then disappear when status becomes uploaded
  const progressFill = page.locator('.attachment-item .progress-fill');
  await expect(progressFill).toBeVisible();

  await page.waitForSelector('.attachment-item .attachment-status', { state: 'detached', timeout: 15000 });

  // After completion, item should have uploaded or quarantined status mapped (not directly accessible; check lack of progress bar)
  await expect(progressFill).toBeHidden();
});

test('chunked large file triggers chunked upload path', async ({ page }) => {
  await page.goto(BASE + '/');
  const fileInput = page.locator('#chat-file-input');
  await expect(fileInput).toBeVisible();

  const tmpPath = 'tests/playwright/fixtures/large.bin';
  const fs = require('fs');
  if (!fs.existsSync(tmpPath)) {
    fs.mkdirSync('tests/playwright/fixtures', { recursive: true });
    // ~9MB to exceed 8MB threshold
    fs.writeFileSync(tmpPath, Buffer.alloc(9 * 1024 * 1024, 1));
  }
  await fileInput.setInputFiles(tmpPath);
  const preview = page.locator('.attachment-item');
  await expect(preview).toHaveCount(1);
  const sendBtn = page.locator('#send-message');
  await sendBtn.click();

  // Wait for progress to reach > 50%
  const progressText = page.locator('.attachment-item .progress-text span:first-child');
  await expect(progressText).toBeVisible();
  await page.waitForFunction(() => {
    const el = document.querySelector('.attachment-item .progress-text span:first-child');
    if (!el) return false;
    const val = parseInt(el.textContent.replace('%',''));
    return val >= 50;
  }, { timeout: 20000 });

  // Resume key should exist while uploading
  const resumeKey = await page.evaluate(() => {
    const item = window.Alpine.store('chatAttachments').attachments[0];
    const sid = window.Alpine.store('chatAttachments').sessionId || 'unspecified';
    return sessionStorage.getItem(`chunk-upload:${sid}:${item.name}:${item.file.size}`);
  });
  expect(resumeKey).not.toBeNull();
});
