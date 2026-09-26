import { test, expect } from '@playwright/test';

test('Debug login', async ({ page }) => {
    // Capture ALL console messages
    const consoleMessages: string[] = [];
    page.on('console', msg => {
        consoleMessages.push(`[${msg.type()}] ${msg.text()}`);
    });

    // Capture network requests
    const requests: string[] = [];
    page.on('request', req => {
        if (req.url().includes('/api/')) {
            requests.push(`${req.method()} ${req.url()}`);
        }
    });

    const responses: string[] = [];
    page.on('response', res => {
        if (res.url().includes('/api/')) {
            responses.push(`${res.status()} ${res.url()}`);
        }
    });

    await page.goto('http://localhost:20080');
    await page.waitForTimeout(3000);

    // Check the page structure
    const inputs = await page.locator('input').count();
    const buttons = await page.locator('button').count();
    console.log(`Inputs: ${inputs}, Buttons: ${buttons}`);

    // Get all input types
    const inputTypes = await page.locator('input').evaluateAll(els => 
        els.map(el => ({ type: el.type, name: el.name, placeholder: el.placeholder, value: el.value }))
    );
    console.log('Inputs:', JSON.stringify(inputTypes, null, 2));

    // Type in the email field
    const emailInput = page.locator('input[type="email"]').first();
    await emailInput.click();
    await emailInput.pressSequentially('test@soma.dev', { delay: 50 });
    await page.waitForTimeout(500);

    // Check value
    const emailValue = await emailInput.evaluate((el: HTMLInputElement) => el.value);
    console.log('Email value:', emailValue);

    // Type in password
    const passwordInput = page.locator('input[type="password"]').first();
    await passwordInput.click();
    await passwordInput.pressSequentially('testpass123', { delay: 50 });
    await page.waitForTimeout(500);

    const passValue = await passwordInput.evaluate((el: HTMLInputElement) => el.value);
    console.log('Password value:', passValue);

    // Click submit
    const submitBtn = page.locator('button[type="submit"]').first();
    console.log('Submit button text:', await submitBtn.textContent());
    await submitBtn.click();

    // Wait for network
    await page.waitForTimeout(8000);

    console.log('Network requests:', requests);
    console.log('Network responses:', responses);
    console.log('Console messages:', consoleMessages.filter(m => !m.includes('401')));

    console.log('Final URL:', page.url());
    await page.screenshot({ path: 'test-results/debug-login.png', fullPage: true });
});
