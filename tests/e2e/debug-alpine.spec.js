const { test, expect } = require('@playwright/test');

test('Debug Alpine.js and Settings Modal', async ({ page }) => {
    await page.goto('http://localhost:21016', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);

    // Check if Alpine is loaded
    const alpineLoaded = await page.evaluate(() => {
        return typeof window.Alpine !== 'undefined';
    });
    console.log('Alpine.js loaded:', alpineLoaded);

    // Check if settingsModalProxy exists
    const proxyExists = await page.evaluate(() => {
        return typeof window.settingsModalProxy !== 'undefined';
    });
    console.log('settingsModalProxy exists:', proxyExists);

    // Get settingsModalProxy state
    const proxyState = await page.evaluate(() => {
        if (typeof window.settingsModalProxy !== 'undefined') {
            return {
                isOpen: window.settingsModalProxy.isOpen,
                hasSettings: !!window.settingsModalProxy.settings,
                activeTab: window.settingsModalProxy.activeTab
            };
        }
        return null;
    });
    console.log('settingsModalProxy state:', JSON.stringify(proxyState, null, 2));

    // Click settings button
    await page.click('button:has-text("Settings")');
    await page.waitForTimeout(1000);

    // Check state after click
    const stateAfterClick = await page.evaluate(() => {
        return {
            proxyIsOpen: window.settingsModalProxy?.isOpen,
            modalElement: !!document.getElementById('settingsModal'),
            modalData: window.Alpine?.$data(document.getElementById('settingsModal')),
            modalDisplay: window.getComputedStyle(document.querySelector('#settingsModal .modal-overlay')).display
        };
    });
    console.log('State after click:', JSON.stringify(stateAfterClick, null, 2));

    // Check for console errors
    const errors = [];
    page.on('console', msg => {
        if (msg.type() === 'error') {
            errors.push(msg.text());
        }
    });

    await page.waitForTimeout(500);
    console.log('Console errors:', errors);
});
