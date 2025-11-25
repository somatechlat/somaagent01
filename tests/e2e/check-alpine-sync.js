const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();

    await page.goto('http://localhost:21016');
    await page.waitForTimeout(3000);

    console.log('=== BEFORE CLICK ===');
    const before = await page.evaluate(() => {
        const modalEl = document.getElementById('settingsModal');
        const alpineData = window.Alpine?.$data(modalEl);
        return {
            globalProxyIsOpen: window.settingsModalProxy?.isOpen,
            alpineDataIsOpen: alpineData?.isOpen,
            areSame: window.settingsModalProxy === alpineData
        };
    });
    console.log(JSON.stringify(before, null, 2));

    console.log('\n=== CLICKING SETTINGS ===');
    await page.click('button:has-text("Settings")');
    await page.waitForTimeout(1000);

    console.log('\n=== AFTER CLICK ===');
    const after = await page.evaluate(() => {
        const modalEl = document.getElementById('settingsModal');
        const alpineData = window.Alpine?.$data(modalEl);
        const overlay = document.querySelector('body > .modal-overlay');
        return {
            globalProxyIsOpen: window.settingsModalProxy?.isOpen,
            alpineDataIsOpen: alpineData?.isOpen,
            areSame: window.settingsModalProxy === alpineData,
            overlayHidden: overlay?.hasAttribute('hidden'),
            overlayStyle: overlay?.getAttribute('style')
        };
    });
    console.log(JSON.stringify(after, null, 2));

    await page.screenshot({ path: 'alpine-sync-check.png', fullPage: true });
    await page.waitForTimeout(5000);
    await browser.close();
})();
