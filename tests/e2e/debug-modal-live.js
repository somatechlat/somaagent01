const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();

    // Capture console messages
    page.on('console', msg => {
        const type = msg.type();
        if (type === 'error' || type === 'warning') {
            console.log(`[${type}] ${msg.text()}`);
        }
    });

    // Capture page errors
    page.on('pageerror', error => {
        console.log(`[PAGE ERROR] ${error.message}`);
    });

    // Navigate
    await page.goto('http://localhost:21016');
    await page.waitForTimeout(3000);

    console.log('\n=== BEFORE CLICK ===');
    const before = await page.evaluate(() => {
        return {
            proxyExists: typeof window.settingsModalProxy !== 'undefined',
            proxyIsOpen: window.settingsModalProxy?.isOpen,
            alpineLoaded: typeof window.Alpine !== 'undefined'
        };
    });
    console.log(JSON.stringify(before, null, 2));

    // Click settings button
    console.log('\n=== CLICKING SETTINGS BUTTON ===');
    try {
        await page.click('button:has-text("Settings")');
    } catch (e) {
        console.log('Click failed:', e.message);
    }

    await page.waitForTimeout(2000);

    console.log('\n=== AFTER CLICK ===');
    const after = await page.evaluate(() => {
        return {
            proxyIsOpen: window.settingsModalProxy?.isOpen,
            modalElement: !!document.getElementById('settingsModal'),
            modalOverlay: !!document.querySelector('#settingsModal .modal-overlay'),
            overlayDisplay: document.querySelector('#settingsModal .modal-overlay')?.style.display,
            overlayComputed: window.getComputedStyle(document.querySelector('#settingsModal .modal-overlay') || document.body).display
        };
    });
    console.log(JSON.stringify(after, null, 2));

    // Take screenshot
    await page.screenshot({ path: 'modal-debug.png', fullPage: true });
    console.log('\n=== Screenshot saved to modal-debug.png ===');

    // Keep browser open
    console.log('\n=== Browser will stay open for 30 seconds ===');
    await page.waitForTimeout(30000);

    await browser.close();
})();
