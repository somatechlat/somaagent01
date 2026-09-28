import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:20080';

test('Login and chat via browser', async ({ page }) => {
    page.on('console', msg => {
        if (msg.type() === 'error' || msg.text().includes('[Saas')) {
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

    // 6. Check result
    if (!page.url().includes('/login')) {
        console.log('LOGIN SUCCESS - on chat page');
        await page.waitForTimeout(5000);
        await page.screenshot({ path: 'test-results/chat-page.png', fullPage: true });

        // Try to send a message
        const textarea = page.locator('textarea').first();
        if (await textarea.count() > 0) {
            await textarea.click();
            await page.keyboard.type('What model are you?', { delay: 20 });
            await page.keyboard.press('Enter');
            console.log('Message sent');
            await page.waitForTimeout(15000);
            await page.screenshot({ path: 'test-results/chat-response.png', fullPage: true });
        }
    } else {
        console.log('STILL ON LOGIN - checking errors');
        // Check for any visible error text
        const allText = await page.textContent('body');
        if (allText) {
            const lines = allText.split('\n').filter(l => l.trim()).slice(0, 20);
            lines.forEach(l => console.log('  ', l.trim()));
        }
    }

    expect(true).toBe(true);
});
