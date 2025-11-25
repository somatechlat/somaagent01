const { test, expect } = require('@playwright/test');

test('Settings Modal After Fix', async ({ page, context }) => {
    // Clear cache
    await context.clearCookies();

    // Navigate with cache bypass
    await page.goto('http://localhost:21016', {
        waitUntil: 'networkidle'
    });

    // Force reload to get fresh JS
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Check proxy state before click
    const beforeClick = await page.evaluate(() => {
        return {
            isOpen: window.settingsModalProxy?.isOpen,
            hasSettings: !!window.settingsModalProxy?.settings
        };
    });
    console.log('Before click:', beforeClick);

    // Click settings
    await page.click('button:has-text("Settings")');
    await page.waitForTimeout(1000);

    // Check after click
    const afterClick = await page.evaluate(() => {
        return {
            proxyIsOpen: window.settingsModalProxy?.isOpen,
            modalVisible: document.querySelector('#settingsModal .modal-overlay')?.style.display !== 'none'
        };
    });
    console.log('After click:', afterClick);

    // Take screenshot
    await page.screenshot({ path: 'settings-fixed.png', fullPage: true });

    // Check if modal is visible
    const modal = page.locator('#settingsModal .modal-overlay');
    const isVisible = await modal.isVisible();
    console.log('Modal visible:', isVisible);

    // Count form elements
    const formElements = await page.locator('#settingsModal input, #settingsModal select, #settingsModal textarea').count();
    console.log('Form elements:', formElements);

    expect(isVisible).toBe(true);
    expect(formElements).toBeGreaterThan(0);
});
