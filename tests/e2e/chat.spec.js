const { test, expect } = require('@playwright/test');

test('Chat Flow Test', async ({ page }) => {
    // 1. Navigate to home
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    // 2. Send a message
    const message = 'Hello E2E Test';
    await page.fill('#chat-input', message);
    await page.click('#send-button');

    // 3. Verify message appears in history
    // Based on index.html: <div id="chat-history">
    // We expect the user message to appear.
    await expect(page.locator('#chat-history')).toContainText(message);

    // 4. Verify Agent Response
    // We expect a response. In dev mode (no API key), it might echo.
    // We'll wait for a new message bubble that is NOT the user message.
    // Usually agent messages have a specific class.
    // Let's wait for a new message bubble that is NOT the user message.
    // Assuming agent messages have a class like 'agent-message' or similar (inferred from css/messages.css).
    // Or we can look for the text "Echo: Hello E2E Test" since we saw that logic in chat.py.
    // We increase timeout to 30s to account for potential delays.
    await expect(page.locator('#chat-history')).toContainText('Echo: ' + message, { timeout: 30000 });
});
