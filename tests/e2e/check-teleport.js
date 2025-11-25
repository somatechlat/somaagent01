const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();

    await page.goto('http://localhost:21016');
    await page.waitForTimeout(3000);

    console.log('=== CLICKING SETTINGS ===');
    await page.click('button:has-text("Settings")');
    await page.waitForTimeout(1000);

    const result = await page.evaluate(() => {
        return {
            proxyIsOpen: window.settingsModalProxy?.isOpen,
            // Check for modal-overlay ANYWHERE in body (teleported)
            overlayInBody: !!document.querySelector('body > .modal-overlay'),
            overlayVisible: document.querySelector('body > .modal-overlay')?.style.display !== 'none',
            overlayCount: document.querySelectorAll('.modal-overlay').length,
            // Check if it has x-show attribute
            hasXShow: document.querySelector('.modal-overlay')?.hasAttribute('x-show')
        };
    });

    console.log(JSON.stringify(result, null, 2));

    // Take screenshot
    await page.screenshot({ path: 'modal-teleport-check.png', fullPage: true });
    console.log('Screenshot: modal-teleport-check.png');

    await page.waitForTimeout(5000);
    await browser.close();
})();
