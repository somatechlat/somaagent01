import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:20080';

test('Login and chat via browser', async ({ page }) => {
    page.on('console', msg => {
        if (msg.type() === 'error' || msg.text().includes('[Soma')) {
            console.log(`[${msg.type()}] ${msg.text()}`);
        }
    });

    // 1. Go to app
    await page.goto(BASE_URL);
    await page.waitForTimeout(3000);
    console.log('URL:', page.url());

    // 2. Fill email - click first, then type character by character
    const emailInput = page.locator('input[type="email"]').first();
    await emailInput.click();
    await page.keyboard.type('test@soma.dev', { delay: 30 });
    await page.waitForTimeout(300);

    // 3. Fill password
    const passwordInput = page.locator('input[type="password"]').first();
    await passwordInput.click();
    await page.keyboard.type('testpass123', { delay: 30 });
    await page.waitForTimeout(300);

    // 4. Submit form
    const signIn = page.locator('button[type="submit"]').first();
    await signIn.click();

    // 5. Wait for redirect
    await page.waitForTimeout(8000);
    console.log('After login:', page.url());
    await page.screenshot({ path: 'test-results/login-result.png', fullPage: true });

    // 6. Real assertions — these can fail. `expect(true).toBe(true)` was a
    // placeholder that could never fail, which is a lie dressed as a test.
    await expect(page).not.toHaveURL(/\/login/, { timeout: 15000 });

    const chatSurface = page.locator('soma-chat, soma-chat-workspace, .chat-workspace').first();
    await expect(chatSurface).toBeVisible({ timeout: 20000 });

    await page.screenshot({ path: 'test-results/chat-page.png', fullPage: true });

    // Send a message and require a visible reply, not just a screenshot.
    const textarea = page.locator('textarea').first();
    await expect(textarea).toBeVisible({ timeout: 15000 });
    await textarea.click();
    await textarea.fill('Reply with exactly: BROWSER-OK');
    await textarea.press('Enter');

    await expect(
        page.locator('soma-message, .message, .assistant').last()
    ).toContainText(/BROWSER-OK/i, { timeout: 45000 });

    await page.screenshot({ path: 'test-results/chat-response.png', fullPage: true });
});
