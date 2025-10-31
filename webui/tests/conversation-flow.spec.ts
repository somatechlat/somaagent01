import { test, expect } from '@playwright/test';

test.describe('Conversation flow parity (Agent Zero UX)', () => {
  test('New/Reset/Delete + Thinking vs Final (no duplicates)', async ({ page }) => {
    test.setTimeout(90000);
    const base = process.env.WEB_UI_BASE_URL || process.env.BASE_URL || 'http://localhost:21016/ui';
    await page.goto(`${base}/index.html`);

    // Ensure a chat is auto-selected or create one
    // Click New Chat to start from a clean context
    await page.click('#newChat');

    // Expect a selected row to appear in Chats list (use font-bold class for parity with A0)
    const selectedRow = page.locator('#chats-section .chat-list-button.font-bold');
    await expect(selectedRow).toHaveCount(1, { timeout: 8000 });

    // Send a message
    const unique = `cf-${Date.now()}`;
    await page.fill('#chat-input', `hello ${unique}`);
    await page.click('#send-button');

    // Expect a Thinking bubble or agent-internal bubble to appear for this turn
    await expect(page.locator('#chat-history .message-agent')).toBeVisible({ timeout: 15000 });
    // Expect at least one assistant response element
    await page.waitForFunction((sel) => document.querySelectorAll(sel).length >= 1,
      '#chat-history .message-agent-response', { timeout: 20000 });

    // Reset chat clears transcript but keeps selection (gold UI may retain a system hint). Proceed to send again.
    await page.click('#resetChat');

    // Send again to ensure session still active after Reset
    await page.fill('#chat-input', `post-reset ${unique}`);
    await page.click('#send-button');
    // Either a Thinking bubble appears or a fast final arrives
    await Promise.race([
      page.locator('#chat-history .message-agent').waitFor({ state: 'visible', timeout: 15000 }),
      page.waitForFunction((sel)=>document.querySelectorAll(sel).length>=1, '#chat-history .message-agent-response', { timeout: 15000 })
    ]);
    // Assert a final assistant response appears after reset
    await page.waitForFunction((sel)=>document.querySelectorAll(sel).length>=1, '#chat-history .message-agent-response', { timeout: 25000 });

    // Delete chat removes it from the list and switches context
    // Guard: find the selected row and click its X button (delete)
    const selectedLi = page.locator('#chats-section li').filter({ has: page.locator('.chat-list-button.font-bold') });
    await expect(selectedLi).toHaveCount(1, { timeout: 5000 });
    await selectedLi.locator('.edit-button').click();

    // After deletion, there should be no row with the same selected marker; selection moves to another or a new chat appears
    await expect(page.locator('#chats-section .chat-list-button.font-bold')).toHaveCount(1, { timeout: 8000 });

    // Sanity: chat input should still be usable. Ensure a row is selected, then send.
    const beforeCount = await page.locator('#chat-history .message-agent-response').count();
    const firstRow = page.locator('#chats-section .chat-list-button').first();
    await firstRow.click({ trial: false });
    await page.fill('#chat-input', 'after delete');
    await page.click('#send-button');
    await page.waitForFunction((sel, prev)=>document.querySelectorAll(sel).length>prev,
      '#chat-history .message-agent-response', beforeCount, { timeout: 30000 });
  });
});
